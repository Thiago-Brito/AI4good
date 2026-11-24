"""LoRA no Qwen3 0.6B com o dataset de destilação (mobile/app/bench/lora_dataset.mjs).

Cada amostra vira: prompt no formato de chat do Qwen3 com raciocínio desligado e "/no_think" no fim da mensagem do
usuário (como o app monta no llama.rn) + saída do professor + <|im_end|>. A perda só conta nos tokens da saída.
Separação treino/validação por apresentação (todas as chamadas de um deck ficam do mesmo lado).
No fim, funde o adaptador no modelo e salva em formato Hugging Face, pronto para converter em GGUF.

Roda no venv de treino (D:\\lora\\venv), na GPU:
  D:\\lora\\venv\\Scripts\\python scripts\\lora_treino.py --dados outputs/lora/dataset/amostras.jsonl --out D:/lora/run1
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup


def load(path: Path, tok, max_len: int):
    rows = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]
    out = []
    for r in rows:
        prompt = tok.apply_chat_template([{"role": "system", "content": r["system"]},
                                          {"role": "user", "content": r["user"] + "\n/no_think"}],
                                         tokenize=False, add_generation_prompt=True, enable_thinking=False)
        p = tok(prompt, add_special_tokens=False)["input_ids"]
        a = tok(r["output"] + "<|im_end|>", add_special_tokens=False)["input_ids"]
        if len(p) + len(a) > max_len:
            continue
        out.append({"deck": r["id"], "stage": r["stage"], "input_ids": p + a, "labels": [-100] * len(p) + a})
    return out


def batches(items, size, shuffle, rng):
    idx = list(range(len(items)))
    if shuffle:
        rng.shuffle(idx)
    # Agrupa por tamanho parecido para desperdiçar menos padding.
    idx = sorted(idx, key=lambda i: len(items[i]["input_ids"])) if not shuffle else idx
    for i in range(0, len(idx), size):
        yield [items[j] for j in idx[i:i + size]]


def collate(group, pad_id, device):
    n = max(len(x["input_ids"]) for x in group)
    ids = torch.full((len(group), n), pad_id)
    lab = torch.full((len(group), n), -100)
    att = torch.zeros((len(group), n), dtype=torch.long)
    for i, x in enumerate(group):
        k = len(x["input_ids"])
        ids[i, :k] = torch.tensor(x["input_ids"])
        lab[i, :k] = torch.tensor(x["labels"])
        att[i, :k] = 1
    return ids.to(device), lab.to(device), att.to(device)


def answer_loss(model, ids, lab, att):
    """Perda só nos tokens da resposta, aplicando a cabeça de saída apenas neles.

    O vocabulário do Qwen3 tem 151 mil tokens: logits de 4096 posições ocupam ~5 GB e estouram os 12 GB da GPU.
    Retorna (soma das perdas, nº de tokens)."""
    inner = model.get_base_model()
    # Com 1 amostra por lote não há padding: sem máscara explícita o SDPA usa o kernel causal eficiente
    # (com máscara cai no caminho que materializa a matriz de atenção e a memória cresce com n²).
    hidden = inner.model(input_ids=ids, attention_mask=None if ids.shape[0] == 1 else att).last_hidden_state
    target = lab[:, 1:]
    mask = target != -100
    h = hidden[:, :-1][mask]
    logits = inner.lm_head(h).float()
    loss = torch.nn.functional.cross_entropy(logits, target[mask], reduction="sum")
    return loss, int(mask.sum())


@torch.no_grad()
def evaluate(model, items, pad_id, device):
    model.eval()
    tot = n = 0.0
    for group in batches(items, 1, False, None):
        ids, lab, att = collate(group, pad_id, device)
        loss, k = answer_loss(model, ids, lab, att)
        tot += loss.item()
        n += k
    model.train()
    return tot / max(n, 1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--epocas", type=float, default=2)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--acum", type=int, default=16)
    ap.add_argument("--max-len", type=int, default=4096)
    ap.add_argument("--val", type=float, default=0.06)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    rng = random.Random(0)
    device = "cuda"
    # No Windows, passar da VRAM não dá erro: o driver transborda para a RAM e o treino fica ~10x mais lento.
    # Com um teto, o alocador do PyTorch recicla o próprio cache antes de chegar lá.
    torch.cuda.set_per_process_memory_fraction(0.8)
    tok = AutoTokenizer.from_pretrained(args.base)
    data = load(Path(args.dados), tok, args.max_len)
    decks = sorted({x["deck"].split("__")[0] for x in data})
    rng.shuffle(decks)
    val_decks = set(decks[:max(1, int(len(decks) * args.val))])
    train = [x for x in data if x["deck"].split("__")[0] not in val_decks]
    val = [x for x in data if x["deck"].split("__")[0] in val_decks]
    stages = {s: sum(x["stage"] == s for x in train) for s in {x["stage"] for x in train}}
    print(f"amostras: treino {len(train)} {stages}, validação {len(val)} ({len(val_decks)} pedidos)", flush=True)

    model = AutoModelForCausalLM.from_pretrained(args.base, dtype=torch.bfloat16).to(device)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model.config.use_cache = False
    cfg = LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, task_type="CAUSAL_LM",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.0)
    steps = math.ceil(len(train) / (args.batch * args.acum) * args.epocas)
    sched = get_cosine_schedule_with_warmup(opt, max(1, steps // 20), steps)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    log = {"args": vars(args), "treino": len(train), "validacao": len(val), "etapas": stages, "historico": []}
    v0 = evaluate(model, val, pad, device)
    print(f"perda de validação antes do treino: {v0:.4f}", flush=True)
    log["historico"].append({"passo": 0, "val": v0})
    step, micro, t0, running = 0, 0, time.time(), []
    model.train()
    epoch = 0
    while step < steps:
        for group in batches(train, args.batch, True, rng):
            ids, lab, att = collate(group, pad, device)
            total, k = answer_loss(model, ids, lab, att)
            loss = total / max(k, 1)
            (loss / args.acum).backward()
            running.append(loss.item())
            micro += 1
            if micro % args.acum:
                continue
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if step % 10 == 0 or step == steps or step <= 3:
                print(f"passo {step}/{steps} perda {sum(running) / len(running):.4f} "
                      f"lr {sched.get_last_lr()[0]:.2e} {time.time() - t0:.0f}s "
                      f"pico {torch.cuda.max_memory_reserved() / 2**30:.1f} GB", flush=True)
                running = []
            if step % max(1, steps // 4) == 0 or step == steps:
                v = evaluate(model, val, pad, device)
                print(f"  validação passo {step}: {v:.4f}", flush=True)
                log["historico"].append({"passo": step, "val": v})
            if step >= steps:
                break
        epoch += 1
    model.save_pretrained(out / "adaptador")
    merged = model.merge_and_unload()
    merged.config.use_cache = True
    merged.save_pretrained(out / "fundido", safe_serialization=True)
    tok.save_pretrained(out / "fundido")
    log["segundos"] = round(time.time() - t0)
    (out / "treino.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), "utf-8")
    print("salvo em", out / "fundido", flush=True)


if __name__ == "__main__":
    main()

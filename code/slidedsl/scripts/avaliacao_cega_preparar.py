"""Prepara a avaliação cega de qualidade (P6 do PLANO_TCC): 12 apresentações = 4 temas × 3 modelos.

Mesmo pedido (nível detalhado), mesmo documento, semente 11 e pipeline do app (gramática com limites + frases):
- 1.7B: outputs/teste6_17b_dica; 0.6B: outputs/teste7_06b_dica; 0.6B LoRA: outputs/teste8_lora.
Os slides são renderizados pelo compilador atual (o mesmo para todos), então só o conteúdo difere.

Saídas em outputs/avaliacao_cega/ (fora do git):
- publicar/: o que vai na página (imagens com códigos aleatórios e avaliacao.json, sem o modelo);
- gabarito.json: código -> modelo e execução. PRIVADO: não publicar nem mostrar aos avaliadores.

Uso: .venv/Scripts/python scripts/avaliacao_cega_preparar.py
"""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

from slidedsl.alto import AltoDeck
from slidedsl.alto_compile import build_alto
from slidedsl.ir_preview import render_deck
from slidedsl.motor_celular import _dossie

ROOT = Path(__file__).resolve().parents[1]
CONDICOES = {"1.7B": "teste6_17b_dica", "0.6B": "teste7_06b_dica", "0.6B LoRA": "teste8_lora"}
TEMAS = {"agua": "Ciclo da água", "sono": "Sono e estudos", "git": "Git", "solar": "Energia solar em casa"}
SEED = 20261124  # sorteio dos códigos, registrado para reprodução


def main():
    out = ROOT / "outputs/avaliacao_cega"
    if out.exists():
        shutil.rmtree(out)
    pub = out / "publicar"
    pub.mkdir(parents=True)
    reqs = {r["id"]: r for r in json.loads((ROOT / "benchmark/format_requests.json").read_text("utf-8"))["requests"]}
    rng = random.Random(SEED)
    codes = rng.sample(range(100, 1000), len(TEMAS) * len(CONDICOES))
    itens, gabarito, k = [], {}, 0
    for tema, nome in TEMAS.items():
        for cond, pasta in CONDICOES.items():
            run = f"{tema}_detalhado__gramatica_limites+frases__s11"
            base = ROOT / "outputs" / pasta / run
            deck = AltoDeck.model_validate(json.loads(Path(f"{base}.deck.json").read_text("utf-8")))
            facts = json.loads(Path(f"{base}.facts.json").read_text("utf-8")).get("facts", {})
            built = build_alto(deck, _dossie(nome, facts).fact_map() if facts else {})
            if not built.success():
                raise SystemExit(f"{run} ({cond}) não compila: {[d.code for d in built.errors]}")
            code = f"A{codes[k]}"
            k += 1
            paths = render_deck(built.validation.ir, pub / code, 0.75)
            itens.append({"codigo": code, "tema": tema, "slides": [f"{code}/{p.name}" for p in paths]})
            gabarito[code] = {"condicao": cond, "pasta": pasta, "execucao": run}
    docs = {t: (ROOT / "outputs/teste4/documentos" / f"{t}.txt").read_text("utf-8") for t in TEMAS}
    publico = {"temas": {t: {"nome": n, "pedido": reqs[f"{t}_detalhado"]["prompt"], "documento": docs[t]}
                         for t, n in TEMAS.items()},
               "apresentacoes": itens}
    (pub / "avaliacao.json").write_text(json.dumps(publico, ensure_ascii=False), "utf-8")
    (out / "gabarito.json").write_text(json.dumps({"seed": SEED, "codigos": gabarito}, ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(itens)} apresentações; {sum(len(i['slides']) for i in itens)} imagens em {pub}")


if __name__ == "__main__":
    main()

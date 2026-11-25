"""Prepara a avaliação cega v2 (comparação de versões): 23 apresentações = 4 temas × 6 condições, sem água × PC 4B.

Diferença para a v1 (scripts/avaliacao_cega_preparar.py, intacta): cada modelo do celular entra em duas versões, a
da v1 (app 0.5/0.6) e a congelada para o artigo (app 0.7.7, tag artigo-v2). PC 4B e externo são os mesmos da v1.
Protocolo: docs/AVALIACAO_CEGA_V2_PROTOCOLO.md.

Mesmo pedido (nível detalhado), mesmo documento-fonte e 5 slides em todas:
- celular 0.6B LoRA e celular 1.7B: bancada do app (gramática com limites + frases, semente 11),
  outputs/teste8_lora e outputs/teste6_17b_dica;
- PC 4B: fluxo completo do PC com o documento (scripts/avaliacao_pc_4b.py), outputs/avaliacao_cega/pc4b;
- externo: GPT-4.1-mini escreve o PowerPoint direto (scripts/avaliacao_externo_gpt.py), mostrado como sai
  (LibreOffice), outputs/avaliacao_cega/externo.
As três condições SlideDSL são renderizadas pelo compilador atual; a externa tem o visual que o modelo fez.

Saídas em outputs/avaliacao_cega_v2/ (fora do git; PC 4B e externo são lidos de outputs/avaliacao_cega/):
- publicar/: o que vai na página (imagens com códigos aleatórios e avaliacao.json, sem o modelo);
- gabarito.json: código -> modelo e execução. PRIVADO: não publicar nem mostrar aos avaliadores.

Uso: .venv/Scripts/python scripts/avaliacao_cega_v2_preparar.py
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
CONDICOES = {"celular 0.6B LoRA (app 0.6)": "teste8_lora", "celular 0.6B LoRA (app 0.7.7)": "teste9_v077_lora06",
             "celular 1.7B (app 0.5)": "teste6_17b_dica", "celular 1.7B (app 0.7.7)": "teste9_v077_q17",
             "PC 4B": "pc4b", "externo GPT-4.1-mini": "externo"}
TEMAS = {"agua": "Ciclo da água", "sono": "Sono e estudos", "git": "Git", "solar": "Energia solar em casa"}
SEED = 20261125  # sorteio dos códigos, registrado para reprodução


def main():
    out = ROOT / "outputs/avaliacao_cega_v2"
    pub = out / "publicar"
    if pub.exists():  # só a pasta publicada; externo/, pc4b/ e a página ficam
        shutil.rmtree(pub)
    pub.mkdir(parents=True)
    reqs = {r["id"]: r for r in json.loads((ROOT / "benchmark/format_requests.json").read_text("utf-8"))["requests"]}
    rng = random.Random(SEED)
    codes = rng.sample(range(100, 1000), len(TEMAS) * len(CONDICOES))  # B### na v2, para não confundir com a v1
    itens, gabarito, k = [], {}, 0
    for tema, nome in TEMAS.items():
        for cond, pasta in CONDICOES.items():
            code = f"B{codes[k]}"
            k += 1
            if pasta == "pc4b":
                rel = ROOT / "outputs/avaliacao_cega/pc4b" / tema / "relatorio.json"
                if not rel.is_file() or not json.loads(rel.read_text("utf-8")).get("valid"):
                    # Regra do protocolo: até 3 sementes; sem versão válida, a combinação fica fora e é registrada.
                    gabarito[f"ausente-{tema}-pc4b"] = {"condicao": cond, "pasta": pasta, "execucao": f"pc4b/{tema}",
                                                       "motivo": "nenhuma das sementes 11, 12 e 13 gerou apresentação válida"}
                    continue
            if pasta == "externo":
                src = ROOT / "outputs/avaliacao_cega/externo" / tema
                (pub / code).mkdir(parents=True)
                paths = []
                for png in sorted(src.glob("slide_*.png")):
                    shutil.copy(png, pub / code / png.name)
                    paths.append(pub / code / png.name)
                run = f"externo/{tema}"
            else:
                if pasta == "pc4b":
                    from slidedsl.alto import parse_alto
                    from slidedsl.research import Dossier

                    folder = ROOT / "outputs/avaliacao_cega/pc4b" / tema
                    deck = parse_alto((folder / "apresentacao.slda").read_text("utf-8"))
                    fact_map = Dossier.load(folder / "dossie.json").fact_map() if (folder / "dossie.json").exists() else {}
                    run = f"pc4b/{tema}"
                else:
                    run = f"{tema}_detalhado__gramatica_limites+frases__s11"
                    base = ROOT / "outputs" / pasta / run
                    deck = AltoDeck.model_validate(json.loads(Path(f"{base}.deck.json").read_text("utf-8")))
                    facts = json.loads(Path(f"{base}.facts.json").read_text("utf-8")).get("facts", {})
                    fact_map = _dossie(nome, facts).fact_map() if facts else {}
                built = build_alto(deck, fact_map, ROOT)
                if not built.success():
                    raise SystemExit(f"{run} ({cond}) não compila: {[d.code for d in built.errors]}")
                paths = render_deck(built.validation.ir, pub / code, 0.75, ROOT)
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

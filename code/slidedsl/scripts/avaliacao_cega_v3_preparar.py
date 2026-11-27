"""Prepara a avaliação cega v3 (assuntos novos): 24 apresentações = 4 assuntos × 6 condições.

Diferença para a v2 (scripts/avaliacao_cega_v2_preparar.py, intacta): os 4 assuntos não são os do banco de pedidos
padrão (água, sono, Git, solar), e sim vacinas, reciclagem, polinização e Sistema Solar, com documentos montados de
trechos da Wikipédia (scripts/avaliacao_cega_v3_documentos.py). Os modelos do celular entram na versão congelada
(app 0.7.7, tag artigo-v2) e na nova (branch exp/celular-documento). Protocolo: docs/AVALIACAO_CEGA_V3_PROTOCOLO.md.

Mesmo pedido, mesmo documento e 5 slides em todas:
- celular 0.6B LoRA e 1.7B, nas duas versões: bancada do app, semente 11 (scripts/bancada_v3.sh);
- PC 4B: fluxo completo do PC (scripts/avaliacao_pc_4b.py --documentos/--pedidos/--saida da v3);
- externo: GPT-4.1-mini escreve o PowerPoint direto (scripts/avaliacao_externo_gpt.py --documento).

Saídas em outputs/avaliacao_cega_v3/ (fora do git): publicar/ (página) e gabarito.json (PRIVADO).
Uso: .venv/Scripts/python scripts/avaliacao_cega_v3_preparar.py
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
CONDICOES = {"celular 0.6B LoRA (app 0.7.7)": "celular_077_lora06", "celular 0.6B LoRA (app novo)": "celular_novo_lora06",
             "celular 1.7B (app 0.7.7)": "celular_077_q17", "celular 1.7B (app novo)": "celular_novo_q17",
             "PC 4B": "pc4b", "externo GPT-4.1-mini": "externo"}
TEMAS = {"vacinas": "Vacinas", "reciclagem": "Reciclagem", "polinizacao": "Polinização", "sistemasolar": "Sistema Solar"}
SEED = 20261127  # sorteio dos códigos, registrado para reprodução
V3 = ROOT / "outputs/avaliacao_cega_v3"


def main():
    out = V3
    pub = out / "publicar"
    if pub.exists():  # só a pasta publicada; externo/, pc4b/ e a página ficam
        shutil.rmtree(pub)
    pub.mkdir(parents=True)
    reqs = {r["id"]: r for r in json.loads((V3 / "pedidos.json").read_text("utf-8"))["requests"]}
    rng = random.Random(SEED)
    codes = rng.sample(range(100, 1000), len(TEMAS) * len(CONDICOES))  # C### na v3, para não confundir com a v1/v2
    itens, gabarito, k = [], {}, 0
    for tema, nome in TEMAS.items():
        for cond, pasta in CONDICOES.items():
            code = f"C{codes[k]}"
            k += 1
            if pasta == "pc4b":
                rel = V3 / "pc4b" / tema / "relatorio.json"
                if not rel.is_file() or not json.loads(rel.read_text("utf-8")).get("valid"):
                    # Regra do protocolo: até 3 sementes; sem versão válida, a combinação fica fora e é registrada.
                    gabarito[f"ausente-{tema}-pc4b"] = {"condicao": cond, "pasta": pasta, "execucao": f"pc4b/{tema}",
                                                       "motivo": "nenhuma das sementes 11, 12 e 13 gerou apresentação válida"}
                    continue
            if pasta == "externo":
                src = V3 / "externo" / tema
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

                    folder = V3 / "pc4b" / tema
                    deck = parse_alto((folder / "apresentacao.slda").read_text("utf-8"))
                    fact_map = Dossier.load(folder / "dossie.json").fact_map() if (folder / "dossie.json").exists() else {}
                    run = f"pc4b/{tema}"
                else:
                    run = f"{tema}_detalhado__gramatica_limites+frases__s11"
                    base = V3 / pasta / run
                    deck = AltoDeck.model_validate(json.loads(Path(f"{base}.deck.json").read_text("utf-8")))
                    facts = json.loads(Path(f"{base}.facts.json").read_text("utf-8")).get("facts", {})
                    fact_map = _dossie(nome, facts).fact_map() if facts else {}
                built = build_alto(deck, fact_map, ROOT)
                if not built.success():
                    raise SystemExit(f"{run} ({cond}) não compila: {[d.code for d in built.errors]}")
                paths = render_deck(built.validation.ir, pub / code, 0.75, ROOT)
            itens.append({"codigo": code, "tema": tema, "slides": [f"{code}/{p.name}" for p in paths]})
            gabarito[code] = {"condicao": cond, "pasta": pasta, "execucao": run}
    docs = {t: (V3 / "documentos" / f"{t}.txt").read_text("utf-8") for t in TEMAS}
    publico = {"temas": {t: {"nome": n, "pedido": reqs[f"{t}_detalhado"]["prompt"], "documento": docs[t]}
                         for t, n in TEMAS.items()},
               "apresentacoes": itens}
    (pub / "avaliacao.json").write_text(json.dumps(publico, ensure_ascii=False), "utf-8")
    (out / "gabarito.json").write_text(json.dumps({"seed": SEED, "codigos": gabarito}, ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(itens)} apresentações; {sum(len(i['slides']) for i in itens)} imagens em {pub}")


if __name__ == "__main__":
    main()

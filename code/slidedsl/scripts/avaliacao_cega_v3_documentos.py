"""Avaliação cega v3: documentos e pedidos de 4 assuntos fora do banco de pedidos padrão (água, sono, Git, solar).

Documentos: trechos literais da Wikipédia em português (CC BY-SA 4.0), introdução e uma ou duas seções de cada artigo,
até cerca de 5.500 caracteres, no mesmo formato dos documentos da v2 (outputs/teste4/documentos). Os artigos baixados
(API da Wikipédia, extrato em texto) ficam em outputs/avaliacao_cega_v3/fontes/*.json.

Saída: outputs/avaliacao_cega_v3/documentos/<tema>.txt e outputs/avaliacao_cega_v3/pedidos.json (formato de
benchmark/format_requests.json; o tema é o prefixo do id, como a bancada do app espera).
Uso: .venv/Scripts/python scripts/avaliacao_cega_v3_documentos.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/avaliacao_cega_v3"
MAX = 5500
# tema -> (arquivo baixado, nome, seções usadas depois da introdução, pedido no nível detalhado)
TEMAS = {
    "vacinas": ("Vacina.json", "Vacinas", ["Eficácia"],
                "Apresente para alunos do ensino médio como as vacinas funcionam: o que é uma vacina, por que a vacinação "
                "previne doenças e quão eficazes elas são, com os dados do documento."),
    "reciclagem": ("Reciclagem.json", "Reciclagem", ["Conceito", "Benefícios da reciclagem", "Cores dos cestos de separação para reciclagem"],
                   "Apresente reciclagem para moradores de um condomínio que vão começar a separar o lixo: o que é "
                   "reciclar, que benefícios traz e como separar os materiais pelas cores dos cestos."),
    "polinizacao": ("Polinização.json", "Polinização", ["Polinização biótica"],
                    "Explique a polinização para estudantes do ensino fundamental: o que é, quais animais e outros agentes "
                    "levam o pólen e por que ela importa para as plantas e a agricultura."),
    "sistemasolar": ("SistemaSolar.json", "Sistema Solar", ["Sol"],
                     "Apresente o Sistema Solar para uma turma do ensino fundamental: como ele se formou, quais são os "
                     "planetas e por que o Sol é tão importante, com os números do documento."),
}


def sections(text: str) -> dict[str, str]:
    """Texto de cada seção (qualquer nível), sem as subseções; a introdução fica em ''."""
    parts = re.split(r"^(=+) (.+?) =+$", text, flags=re.M)
    out = {"": parts[0]}
    for k in range(1, len(parts), 3):
        out[parts[k + 1].strip()] = parts[k + 2]
    return out


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n+", text) if len(p.strip()) > 40]


def main():
    docs = OUT / "documentos"
    docs.mkdir(parents=True, exist_ok=True)
    requests = []
    for tema, (arquivo, nome, usadas, pedido) in TEMAS.items():
        page = next(iter(json.loads((OUT / "fontes" / arquivo).read_text("utf-8"))["query"]["pages"].values()))
        secs = sections(page["extract"])
        head = (f"{nome}\n\nDocumento de referência montado com trechos literais de fontes públicas.\n\n"
                f"Fonte: Wikipédia, artigo \"{page['title']}\" (CC BY-SA 4.0)\n{page['fullurl']}\n")
        body, size = [], len(head)
        for titulo in ["", *usadas]:
            bloco = [f"## {titulo}"] if titulo else []
            for p in paragraphs(secs[titulo]):
                if size + len(p) > MAX:
                    break
                bloco.append(p)
                size += len(p) + 2
            if len(bloco) > (1 if titulo else 0):
                body.append("\n\n".join(bloco))
        text = head + "\n" + "\n\n".join(body) + "\n"
        (docs / f"{tema}.txt").write_text(text, "utf-8")
        requests.append({"id": f"{tema}_detalhado", "theme": tema, "level": "detalhado", "prompt": pedido, "obligations": []})
        print(tema, len(text))
    (OUT / "pedidos.json").write_text(json.dumps({"order_seed": 20261127, "requests": requests}, ensure_ascii=False, indent=1), "utf-8")


if __name__ == "__main__":
    main()

"""Documentos e pedidos para o dataset de destilação (LoRA no Qwen3 0.6B).

Temas DIFERENTES dos quatro temas da bancada (água, sono, git, solar), para que o treino não veja o teste.
Cada documento é o texto do artigo da Wikipedia em português (API pública, texto puro), com as seções
convertidas em títulos Markdown, que o app usa como metadados. Três pedidos por tema, nos níveis da bancada
(tema, detalhado, obrigatório); o pedido obrigatório usa títulos de seção do próprio artigo.

Uso: .venv\\Scripts\\python scripts\\lora_documentos.py --out outputs/lora/documentos
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Nenhum tema da bancada nem vizinho direto deles (ciclo da água, sono, controle de versão, energia solar).
TOPICS = [
    "Fotossíntese", "Revolução Industrial", "Vacina", "Reciclagem", "Inteligência artificial", "Sistema imunitário",
    "Revolução Francesa", "Internet", "Teorema de Pitágoras", "Nutrição", "Dengue", "Célula", "Independência do Brasil",
    "Algoritmo", "Biodiversidade", "Vulcão", "Tectónica de placas", "Energia eólica", "Diabetes mellitus",
    "Primeira Guerra Mundial", "Sistema circulatório", "Banco de dados", "Criptografia", "Desmatamento",
    "Floresta Amazónica", "Segunda Guerra Mundial", "Python", "Efeito estufa", "Sistema nervoso", "Antibiótico",
    "Computação em nuvem", "Democracia", "Fração", "Terremoto", "Abelha", "Mercado de ações",
]
AUDIENCES = ["alunos do ensino fundamental", "alunos do ensino médio", "estudantes universitários iniciantes",
             "professores que vão apresentar o tema em sala", "o público geral, sem conhecimento prévio",
             "uma equipe de trabalho que precisa de uma visão rápida do assunto"]
SKIP = {"ver também", "referências", "ligações externas", "bibliografia", "notas", "leitura adicional", "galeria",
        "notas e referências", "fontes", "etimologia"}
UA = "SlideDSL-research/0.1 (educational; research prototype)"


def fetch(title: str) -> tuple[str, str]:
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1,
                                "format": "json", "titles": title})
    req = urllib.request.Request(f"https://pt.wikipedia.org/w/api.php?{q}", headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                page = next(iter(json.load(r)["query"]["pages"].values()))
            return page.get("title", title), page.get("extract", "")
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(10 * (attempt + 1))  # limite de requisições da API: espera crescente
    raise RuntimeError("inalcançável")


def to_document(title: str, text: str, limit: int) -> tuple[str, list[str]]:
    lines, sections, skipping = [title, ""], [], False
    for raw in text.splitlines():
        m = re.match(r"^(=+)\s*(.+?)\s*=+$", raw.strip())
        if m:
            name = m.group(2)
            skipping = name.lower() in SKIP
            if not skipping:
                lines += ["", "#" * min(len(m.group(1)), 3) + " " + name]
                if len(m.group(1)) == 2:
                    sections.append(name)
            continue
        if not skipping and raw.strip():
            lines.append(raw.strip())
    doc = "\n".join(lines)
    return doc[:limit].rsplit("\n", 1)[0], sections


def requests_for(topic: str, sections: list[str], rng: random.Random) -> list[dict]:
    t = topic.lower() if topic not in {"Python", "Internet"} else topic
    aud = rng.choice(AUDIENCES)
    secs = [s.lower() for s in sections if len(s) < 50][:6]
    rng.shuffle(secs)
    out = [{"level": "tema", "prompt": f"{topic}."},
           {"level": "detalhado", "prompt": f"Apresente {t} para {aud}: o que é, por que importa e exemplos concretos."}]
    if len(secs) >= 2:
        items = ", ".join(secs[:3][:-1]) + " e " + secs[:3][-1]
        out.append({"level": "obrigatorio", "prompt": f"Apresente {t} para {aud}. Inclua obrigatoriamente: {items}."})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "outputs" / "lora" / "documentos"))
    ap.add_argument("--limit", type=int, default=14000)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261124)
    reqs = []
    for topic in TOPICS:
        title, text = fetch(topic)
        time.sleep(3)
        if len(text) < 3000:
            print("curto demais, pulado:", topic, len(text))
            continue
        doc, sections = to_document(title, text, args.limit)
        slug = re.sub(r"[^a-z0-9]+", "_", topic.lower().encode("ascii", "ignore").decode()).strip("_")
        (out / f"{slug}.txt").write_text(doc, "utf-8")
        for i, r in enumerate(requests_for(topic, sections, rng)):
            reqs.append({"id": f"{slug}_{r['level']}", "doc": f"{slug}.txt", **r})
        print(f"{topic}: {len(doc)} caracteres, {len(sections)} seções")
    (out.parent / "pedidos.json").write_text(json.dumps({"requests": reqs}, ensure_ascii=False, indent=1), "utf-8")
    print(len(reqs), "pedidos")


if __name__ == "__main__":
    main()

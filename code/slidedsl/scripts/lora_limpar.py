"""Limpa o dataset de destilação antes do treino (saída: amostras_limpas.jsonl ao lado da entrada).

- Texto de slide cortado no limite do compilador (tamanho exato de um limite A005, sem pontuação final e com a
  última palavra fora do vocabulário do dataset, isto é, palavra partida) é
  aparado na última frase completa ou, se não houver, na última palavra inteira: treinar com texto cortado
  ensinaria o 0.6B a cortar; aparado, ele aprende a terminar dentro do limite.
- Roteiro (JSON) é reserializado compacto e sem fatos repetidos: menos tokens para o modelo aprender a gerar.
- Amostras repetidas (mesma entrada) ficam uma vez.

Uso: .venv\\Scripts\\python scripts\\lora_limpar.py outputs/lora/dataset/amostras.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

# Limites de texto do compilador (A005), os mesmos da gramática em gramatica_limites (altoText.ts COMPILER_LIMITS).
LIMITS = {80, 140, 260, 40, 48, 170, 14, 16, 36, 90, 24, 1500}
STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')


DANGLING = {"a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "com", "para",
            "por", "pela", "pelo", "um", "uma", "que", "ao", "à", "sem", "ou", "como"}
WORD = re.compile(r"\w+$")
VOCAB: set[str] = set()


def is_cut(s: str) -> bool:
    """No tamanho exato de um limite e terminando numa palavra que não existe em nenhum documento/saída."""
    if len(s) not in LIMITS or re.search(r'[.!?…)"»%\d]$', s.strip()):
        return False
    m = WORD.search(s)
    return m is None or m.group(0).lower() not in VOCAB


def trim(s: str) -> str:
    ends = [m.end() for m in re.finditer(r'[.!?…](?=\s|$)', s)]
    if ends and ends[-1] >= len(s) * 0.4:
        return s[:ends[-1]]
    if " " not in s:
        return s
    words = s[:s.rfind(" ")].rstrip(" ,;:—-").split(" ")
    while len(words) > 2 and words[-1].lower() in DANGLING:  # não termina em "de", "o", "com"...
        words.pop()
    return " ".join(words).rstrip(" ,;:—-")


def repair(alto: str) -> tuple[str, int]:
    n = 0

    def fix(m):
        nonlocal n
        s = json.loads(f'"{m.group(1)}"')
        if not is_cut(s):
            return m.group(0)
        n += 1
        return json.dumps(trim(s), ensure_ascii=False)
    return STRING.sub(fix, alto), n


def main(path: str):
    src = Path(path)
    out, seen, why = [], set(), Counter()
    rows = [json.loads(line) for line in src.read_text("utf-8").splitlines()]
    for r in rows:  # vocabulário: palavras dos prompts (documentos) e das saídas
        VOCAB.update(w.lower() for w in re.findall(r"\w+", r["user"]))
        for m in STRING.finditer(r["output"]):
            t = m.group(1)
            if len(t) not in LIMITS:
                VOCAB.update(w.lower() for w in re.findall(r"\w+", t))
    for r in rows:
        key = (r["system"], r["user"])
        if key in seen:
            why["repetida"] += 1
            continue
        seen.add(key)
        if r["stage"] == "slide":
            r["output"], n = repair(r["output"])
            why["textos aparados"] += n
        if r["stage"] == "roteiro":
            try:
                data = json.loads(r["output"])
            except json.JSONDecodeError:
                why["roteiro inválido"] += 1
                continue
            for s in data.get("slides", []):
                if isinstance(s.get("fatos"), list):
                    s["fatos"] = list(dict.fromkeys(s["fatos"]))
            r["output"] = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        out.append(r)
    dst = src.with_name("amostras_limpas.jsonl")
    dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), "utf-8")
    print(f"{len(out)} amostras mantidas {dict(Counter(r['stage'] for r in out))}; descartadas {dict(why)} -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1])

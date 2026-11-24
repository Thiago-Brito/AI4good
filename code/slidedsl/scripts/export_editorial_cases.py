"""Gera mobile/app/test/fixtures/editorial_cases.json com as saídas do PC (strip_fact_ids, sentence_case,
capitalize_first). O teste editorial.test.mjs exige que o celular produza exatamente o mesmo texto.

  Uso: .venv/Scripts/python scripts/export_editorial_cases.py
"""

import json
from pathlib import Path

from slidedsl.alto_generation import fallback_queries, strip_fact_ids
from slidedsl.editorial import capitalize_first, proper_words, sentence_case

IDS = ["F1", "F2", "F3", "F12"]
STRIP = [
    "A agricultura consome 70% da água, conforme F2.",
    "As plantas liberam água por transpiração, como em F1.",
    "Segundo F3 e F12, o uso cresceu.",
    "Dados (F1, F2) mostram queda",
    "A F1 é uma categoria do automobilismo",
    "F9 não existe no dossiê",
    "Fonte: F12",
    "Texto sem referência",
]
REQUEST = "Explique o Git e o GitHub para a equipe da Petrobras"
CASE = [
    "Como Funciona O Controle De Versões",
    "Como o Git guarda versões",
    "Por Que Usar GitHub Na Petrobras",
    "O SQL E A API REST",
    "Ciclo Da Água",
    "Programação Em C Para Iniciantes",
    "Estatística Com R E Python",
]
QUERIES = ["painel solar casa iluminação natural", "solar panels roof diagram", "ciclo da água", "git version control"]
CAP = ["avaliar fase atual", "Já maiúscula", "", "1º passo", "érica"]

out = {
    "ids": IDS,
    "strip": [[t, strip_fact_ids(t, IDS)] for t in STRIP],
    "request": REQUEST,
    "keep": sorted(proper_words(REQUEST)),
    "case": [[t, sentence_case(t, proper_words(REQUEST))] for t in CASE],
    "capitalize": [[t, capitalize_first(t)] for t in CAP],
    "fallback_queries": [[q, fallback_queries(q)] for q in QUERIES],
}
path = Path(__file__).resolve().parents[1] / "mobile/app/test/fixtures/editorial_cases.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", "utf-8")
print(path)

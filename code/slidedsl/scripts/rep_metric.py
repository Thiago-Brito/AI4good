"""Repetição entre slides (Jaccard de palavras de conteúdo, pares acima de 0,3) e cobertura das fases do ciclo."""
import json, re, sys, itertools, pathlib
STOP = set("a o as os um uma de do da dos das em no na nos nas para por com sem e ou que se ao à é como mais seu sua".split())
FASES = {"evapora": "evapora", "condensa": "condensa", "precipita": "precipita|chuva", "infiltra": "infiltra", "escoa": "escoa|rios|oceano", "transpira": "transpira|plantas"}
def words(s): return {w for w in re.findall(r"[a-zà-ú]{4,}", s.lower()) if w not in STOP}
for d in sorted(pathlib.Path(sys.argv[1]).glob(sys.argv[2] + "_s*")):
    if not (d / "deck.json").exists(): continue
    deck = json.loads((d / "deck.json").read_text("utf-8"))
    texts = []
    for s in deck["slides"][1:]:
        parts = [s.get("title") or ""] + [f"{i['label']} {i.get('detail') or ''}" for i in s.get("items") or []]
        parts += [f"{i['label']} {i.get('detail') or ''}" for side in s.get("sides") or [] for i in side["items"]]
        parts += [f"{m['label']} {m.get('detail') or ''}" for m in s.get("milestones") or []]
        texts.append(" ".join(parts))
    ws = [words(t) for t in texts]
    pairs = [(a + 2, b + 2, round(len(ws[a] & ws[b]) / max(1, len(ws[a] | ws[b])), 2)) for a, b in itertools.combinations(range(len(ws)), 2)]
    rep = [p for p in pairs if p[2] >= 0.3]
    alltext = " ".join(texts).lower()
    cob = [f for f, pat in FASES.items() if re.search(pat, alltext)]
    used = sorted({f for s in deck["slides"] for f in s.get("sources") or []}, key=lambda x: int(x[1:]))
    print(f"{d.name}: pares repetidos {len(rep)} {rep} | fases {len(cob)}/6 {cob} | fatos usados {len(used)}")

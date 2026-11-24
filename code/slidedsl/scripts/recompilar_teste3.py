"""Recompila os decks do Teste 3 com o código atual, sem chamar o modelo.

O texto Alto escrito pelo modelo (apresentacao.slda) e os fatos (dossie.json) ficam iguais; só o
compilador muda. Serve para medir o efeito de uma correção do compilador sobre as mesmas saídas.
Os originais não são tocados: a saída vai para outra pasta.

Uso: .venv\\Scripts\\python scripts\\recompilar_teste3.py [--src outputs/teste3] [--out outputs/teste3_recompilado]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def main(argv=None):
    from pptx_checks import check_pptx
    from slidedsl.alto_compile import build_alto
    from slidedsl.compiler import compile_ir
    from slidedsl.research import Dossier
    from teste3_restricao import commit

    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "outputs" / "teste3"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "teste3_recompilado"))
    ap.add_argument("--slides", type=int, default=6)
    args = ap.parse_args(argv)
    src, out = Path(args.src), Path(args.out)
    rows = []
    for deck in sorted(src.glob("runs/*/deck")):
        run_id = deck.parent.name
        slda = deck / "apresentacao.slda"
        if not slda.exists():
            continue
        before = json.loads((deck / "relatorio.json").read_text("utf-8")).get("valid", False)
        facts = Dossier.load(deck / "dossie.json").fact_map() if (deck / "dossie.json").exists() else {}
        built = build_alto(slda.read_text("utf-8"), facts)
        row = {"run_id": run_id, "valido_antes": bool(before), "valido_depois": built.success(False),
               "erros_depois": sorted({d.code for d in built.errors})}
        if built.success(False):
            target = out / run_id / "apresentacao.pptx"
            target.parent.mkdir(parents=True, exist_ok=True)
            compile_ir(built.validation.ir, target)
            check = check_pptx(target, args.slides)
            row.update(verificador=check["valido"], estrito=check["valido_estrito"],
                       bloqueios=check["bloqueios"])
        rows.append(row)
    out.mkdir(parents=True, exist_ok=True)
    (out / "recompilacao.json").write_text(json.dumps({"commit": commit(), "decks": rows},
                                                      ensure_ascii=False, indent=2), "utf-8")
    for mode in ("json", "gramatica", "direto"):
        sel = [r for r in rows if f"__{mode}__" in r["run_id"]]
        print(mode, "decks:", len(sel), "válidos antes:", sum(r["valido_antes"] for r in sel),
              "depois:", sum(r["valido_depois"] for r in sel),
              "verificador ok:", sum(bool(r.get("verificador")) for r in sel))
    changed = [r for r in rows if r["valido_antes"] != r["valido_depois"]]
    print("mudaram:", json.dumps(changed, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

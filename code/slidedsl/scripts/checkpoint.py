"""Registrar etapa após executar os comandos indicados, sem inventar validação."""

import argparse
from pathlib import Path

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", type=int)
    p.add_argument("text")
    a = p.parse_args()
    roadmap = Path("ROADMAP.md")
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            f"- [ ] Fase {a.phase}", f"- [x] Fase {a.phase}"
        ),
        encoding="utf-8",
    )
    with Path("docs/PROGRESSO.md").open("a", encoding="utf-8") as f:
        f.write(f"\n## 2026-10-08 — Fase {a.phase}\n{a.text}\n")

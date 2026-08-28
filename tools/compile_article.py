import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "academy" / "papers" / "artigo-disciplina"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=PAPER_DIR, check=True)


def main() -> int:
    if shutil.which("pdflatex") is None:
        print("pdflatex nao encontrado no PATH.")
        print("Instale MiKTeX ou TeX Live e rode este comando novamente.")
        return 1

    run(["pdflatex", "paper.tex"])
    if shutil.which("bibtex") is not None:
        run(["bibtex", "paper"])
        run(["pdflatex", "paper.tex"])
        run(["pdflatex", "paper.tex"])

    print(f"PDF gerado em: {PAPER_DIR / 'paper.pdf'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


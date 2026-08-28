from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "AGENTS.md",
    "CONTEXT.md",
    "code/CONTEXT.md",
    "code/rede-neural-do-zero/CONTEXT.md",
    "code/rede-neural-do-zero/README.md",
    "code/rede-neural-do-zero/requirements.txt",
    "academy/CONTEXT.md",
    "academy/papers/CONTEXT.md",
    "academy/papers/artigo-disciplina/CONTEXT.md",
    "academy/papers/artigo-disciplina/PROJECT.md",
    "academy/papers/artigo-disciplina/ROADMAP.md",
    "academy/papers/artigo-disciplina/paper.tex",
    "academy/papers/artigo-disciplina/refs/references.bib",
    "core/flows/research/literature.md",
    "core/flows/research/draft.md",
]


def main() -> int:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        print("Workspace incompleto. Arquivos faltando:")
        for path in missing:
            print(f"- {path}")
        return 1

    print("Workspace OK.")
    print("Codigo: code/rede-neural-do-zero/")
    print("Artigo: academy/papers/artigo-disciplina/paper.tex")
    print("Proximo passo: responder PROJECT.md e instalar LaTeX se precisar gerar PDF.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


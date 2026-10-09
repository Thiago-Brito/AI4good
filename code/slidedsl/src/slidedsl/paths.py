import os
from pathlib import Path, PureWindowsPath


def project_root() -> Path:
    return Path(os.environ.get("SLIDEDSL_ROOT", Path(__file__).resolve().parents[2])).resolve()


def asset_path(file: str, root: Path) -> Path:
    # Verificação também para caminhos Windows em execução Linux.
    win = PureWindowsPath(file)
    if win.is_absolute() or win.drive or Path(file).is_absolute() or ":" in file:
        raise ValueError(f"Asset deve ser relativo e local: {file}")
    p = (root / file.replace("\\", "/")).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError(f"Asset fora da raiz do projeto: {file}")
    if p.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise ValueError(f"Formato de asset não suportado: {file}")
    if not p.is_file():
        raise ValueError(f"Arquivo de imagem não existe: {file}")
    header = p.read_bytes()[:12]
    if (p.suffix.lower() == ".png" and not header.startswith(b"\x89PNG\r\n\x1a\n")) or (
        p.suffix.lower() in {".jpg", ".jpeg"} and not header.startswith(b"\xff\xd8\xff")
    ):
        raise ValueError(f"Conteúdo não corresponde ao formato de imagem: {file}")
    return p


def node_executable(root: Path | None = None) -> str:
    import shutil

    custom = os.environ.get("SLIDEDSL_NODE")
    if custom:
        return custom
    portable = (root or project_root()) / "outputs/runtime/node.exe"
    return str(portable) if portable.is_file() else shutil.which("node") or "node"

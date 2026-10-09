import os
from pathlib import Path
import subprocess

from .paths import project_root


def render_preview(pptx: Path, out: Path):
    if os.name != "nt":
        raise RuntimeError("Preview COM requer Windows e PowerPoint instalado.")
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(project_root() / "scripts/preview_powerpoint.ps1"),
            "-Pptx",
            str(pptx.resolve()),
            "-OutDir",
            str(out.resolve()),
        ],
        shell=False,
        check=True,
        timeout=120,
    )

import os
from pathlib import Path
import subprocess

from .paths import project_root


def rendering_available():
    import shutil

    office = False
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application\CLSID"):
                office = True
        except OSError:
            pass
    candidates = [
        shutil.which("soffice"),
        "C:/Program Files/LibreOffice/program/soffice.com",
        "C:/Program Files/LibreOffice/program/soffice.exe",
    ]
    libreoffice = next((p for p in candidates if p and Path(p).is_file()), None)
    return {"powerpoint_com": office, "libreoffice": libreoffice}


def render_optional(pptx: Path, out: Path):
    from .incremental import save_json

    out.mkdir(parents=True, exist_ok=False)
    available = rendering_available()
    report = {"available": available, "engine": "geometric", "rendered": False, "errors": []}
    if available["powerpoint_com"]:
        try:
            render_preview(pptx, out / "png")
            report.update(engine="powerpoint_com", rendered=True)
        except (subprocess.SubprocessError, OSError) as exc:
            report["errors"].append(str(exc))
    if not report["rendered"] and available["libreoffice"]:
        try:
            profile = (out / "lo_profile").resolve().as_uri()
            result = subprocess.run(
                [
                    available["libreoffice"],
                    "-env:UserInstallation=" + profile,
                    "--headless",
                    "--convert-to",
                    "pdf:impress_pdf_Export",
                    "--outdir",
                    str(out.resolve()),
                    str(pptx.resolve()),
                ],
                shell=False,
                capture_output=True,
                timeout=120,
            )
            pdf = out / (pptx.stem + ".pdf")
            if result.returncode or not pdf.is_file():
                raise RuntimeError("LibreOffice não produziu PDF.")
            from pypdf import PdfReader

            report.update(
                engine="libreoffice_pdf",
                rendered=True,
                pages=len(PdfReader(pdf).pages),
                artifact=pdf.name,
            )
        except (subprocess.SubprocessError, OSError, RuntimeError) as exc:
            report["errors"].append(str(exc))
    report["note"] = "Inspeção humana não realizada; fallback geométrico não renderiza glifos."
    save_json(out / "rendering.json", report)
    return report


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

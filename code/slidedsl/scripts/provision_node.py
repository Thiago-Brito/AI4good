"""Node 24 portátil, oficial, com SHA-256, sem alterar instalação global."""

import hashlib
from pathlib import Path
import subprocess
import urllib.request

VERSION = "24.14.0"


def provision():
    folder = Path(__file__).resolve().parents[1] / "outputs/runtime"
    target = folder / "node.exe"
    if (
        target.exists()
        and subprocess.check_output([str(target), "--version"], text=True).strip() == "v" + VERSION
    ):
        print("Node portátil já disponível: " + VERSION)
        return
    folder.mkdir(parents=True, exist_ok=True)
    base = "https://nodejs.org/dist/v" + VERSION + "/"
    manifest = urllib.request.urlopen(base + "SHASUMS256.txt", timeout=30).read().decode()
    expected = next(
        line.split()[0] for line in manifest.splitlines() if line.split()[-1] == "win-x64/node.exe"
    )
    with urllib.request.urlopen(base + "win-x64/node.exe", timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError("SHA-256 do Node não corresponde ao manifesto oficial.")
    target.write_bytes(data)
    (folder / "SHASUMS256.txt").write_text(manifest, encoding="utf-8")
    print("Node portátil instalado e verificado: " + VERSION)


if __name__ == "__main__":
    provision()

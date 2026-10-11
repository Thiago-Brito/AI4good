"""Fallback Windows: baixar wheels via urllib quando pip HTTPS não responde."""

import concurrent.futures
import json
from pathlib import Path
import urllib.request

VERSIONS = {
    "setuptools": "80.9.0",
    "wheel": "0.45.1",
    "lark": "1.2.2",
    "pydantic": "2.11.7",
    "pydantic-core": "2.33.2",
    "annotated-types": "0.7.0",
    "typing-extensions": "4.14.0",
    "typing-inspection": "0.4.1",
    "PyYAML": "6.0.2",
    "fastapi": "0.115.12",
    "starlette": "0.46.2",
    "anyio": "4.9.0",
    "sniffio": "1.3.1",
    "idna": "3.10",
    "uvicorn": "0.34.3",
    "click": "8.2.1",
    "h11": "0.16.0",
    "httpx": "0.28.1",
    "httpcore": "1.0.9",
    "certifi": "2025.6.15",
    "jsonschema": "4.24.0",
    "attrs": "25.3.0",
    "jsonschema-specifications": "2025.4.1",
    "referencing": "0.36.2",
    "rpds-py": "0.25.1",
    "pytest": "8.4.1",
    "iniconfig": "2.1.0",
    "packaging": "25.0",
    "pluggy": "1.6.0",
    "Pygments": "2.19.2",
    "colorama": "0.4.6",
    "ruff": "0.12.0",
    "Pillow": "12.3.0",
    "pypdf": "6.20.0",
    "psutil": "7.1.0",
}


def fetch(item):
    name, version = item
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as r:
        metadata = json.load(r)
    choices = [
        u
        for u in metadata["urls"]
        if u["filename"].endswith(".whl")
        and (
            "py3-none-any" in u["filename"]
            or "py2.py3-none-any" in u["filename"]
            or "cp312-cp312-win_amd64" in u["filename"]
            or "py3-none-win_amd64" in u["filename"]
            or (
                "abi3-win_amd64" in u["filename"]
                and any(f"cp{v}-" in u["filename"] for v in [37, 38, 39, 310, 311, 312])
            )
        )
    ]
    if not choices:
        raise RuntimeError(f"Sem wheel compatível: {name}")
    u = choices[0]
    dest = Path("outputs/wheels") / u["filename"]
    urllib.request.urlretrieve(u["url"], dest)
    import hashlib

    if hashlib.sha256(dest.read_bytes()).hexdigest() != u["digests"]["sha256"]:
        raise RuntimeError(f"Hash inválido: {name}")
    return f"{name}=={version}"


if __name__ == "__main__":
    Path("outputs/wheels").mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        versions = list(pool.map(fetch, VERSIONS.items()))
    Path("requirements-lock.txt").write_text("\n".join(sorted(versions)) + "\n", encoding="utf-8")
    print(f"{len(versions)} wheels verificadas por SHA-256.")

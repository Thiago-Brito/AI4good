"""Republish binary artifacts with destination inheritance, preserving exact bytes."""

import argparse
import hashlib
import os
from pathlib import Path
from uuid import uuid4

from slidedsl.incremental import save_json
from slidedsl.paths import project_root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="+", type=Path)
    args = parser.parse_args()
    allowed = (project_root() / "outputs").resolve()
    records = []
    for folder in args.folders:
        folder = folder.resolve()
        if not folder.is_relative_to(allowed) or folder == allowed:
            raise ValueError("Informe uma subpasta explícita de outputs.")
        for target in folder.rglob("*.pptx"):
            target = target.resolve()
            if not target.is_relative_to(folder):
                raise ValueError("PPTX fora da subpasta explicitamente informada.")
            original = target.read_bytes()
            digest = hashlib.sha256(original).hexdigest()
            staging = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
            try:
                staging.write_bytes(original)
                assert hashlib.sha256(staging.read_bytes()).hexdigest() == digest
                os.replace(staging, target)
            finally:
                staging.unlink(missing_ok=True)
            assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
            records.append(
                {
                    "file": str(target.relative_to(project_root())),
                    "before_sha256": digest,
                    "after_sha256": digest,
                    "bytes_preserved": True,
                }
            )
    save_json(allowed / f"artifact_access_{uuid4().hex}.json", records)
    print(f"{len(records)} PPTX republicados com os mesmos bytes e herança da pasta de entrega.")


if __name__ == "__main__":
    main()

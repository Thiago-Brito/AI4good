from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

from .models.factory import create_model
from .paths import project_root
from .pipeline import validate_source


def repair_prompt(user: str, previous: str, diagnostics: list[dict]) -> str:
    return (
        user
        + "\n\nCorrija o programa completo abaixo usando os diagnósticos. Retorne somente SlideDSL.\n"
        + previous
        + "\n\nDiagnósticos:\n"
        + json.dumps(diagnostics, ensure_ascii=False)
    )


def generate_file(
    provider: str,
    model: str,
    prompt_file: Path,
    out: Path,
    *,
    repair_max=0,
    temperature=0,
    seed=None,
    adapter=None,
) -> dict:
    if repair_max not in (0, 1, 2):
        raise ValueError("Reparo permite no máximo duas rodadas adicionais.")
    if out.suffix != ".sld":
        raise ValueError("A saída do gerador deve ter extensão .sld.")
    sidecars = [out, out.with_suffix(".raw.txt"), out.with_suffix(".meta.json")]
    if any(p.exists() for p in sidecars):
        raise FileExistsError(
            "Saída já existe; use outro caminho. Geração não sobrescreve silenciosamente."
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    system_bytes = (project_root() / "prompts/system_dsl.txt").read_bytes()
    user_bytes = prompt_file.read_bytes()
    system, user = system_bytes.decode("utf-8"), user_bytes.decode("utf-8-sig")
    adapter = adapter or create_model(provider, model)
    records = []
    current = user
    for round in range(repair_max + 1):
        started = time.perf_counter()
        raw = adapter.generate(system, current, temperature=temperature, seed=seed)
        duration = (time.perf_counter() - started) * 1000
        raw_path = (
            out.with_suffix(".raw.txt") if round == 0 else out.with_suffix(f".round{round}.raw.txt")
        )
        raw_path.write_bytes(raw.encode("utf-8"))
        validation = validate_source(raw)
        record = {
            "round": round,
            "duration_ms": duration,
            **validation.report(),
            "metadata": dict(adapter.metadata),
        }
        records.append(record)
        out.with_suffix(f".round{round}.validation.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if validation.success() and not any(
            d.severity in {"ERRO", "AVISO"} for d in validation.diagnostics
        ):
            break
        current = repair_prompt(user, raw, [d.model_dump() for d in validation.diagnostics])
    out.write_bytes(raw.encode("utf-8"))
    metadata = {
        "provider": provider,
        "model": model,
        "is_mock": provider == "mock",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": platform.python_version(), "os": platform.system()},
        "temperature": temperature,
        "seed": seed,
        "system_prompt_sha256": hashlib.sha256(system_bytes).hexdigest(),
        "user_prompt_sha256": hashlib.sha256(user_bytes).hexdigest(),
        "system_prompt": system,
        "user_prompt": user,
        "rounds": records,
        "repair_rounds": len(records) - 1,
        "valid": validation.success(),
    }
    out.with_suffix(".meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metadata

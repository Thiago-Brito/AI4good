"""Mede tempo total e pico de memória de um comando (ex.: slidedsl criar).

Uso:
    .venv\\Scripts\\python.exe scripts\\medir_execucao.py --out medicao.json -- <comando> [args...]

Amostra a cada 0,5 s:
  * RAM (RSS) do processo e de todos os filhos;
  * RAM (RSS) dos processos do Ollama (o modelo roda no servidor do Ollama, fora do Python);
  * VRAM usada na GPU NVIDIA (nvidia-smi), se existir.
Registra também a máquina, o commit e o comando, para a execução ficar identificada.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

MB = 1024 * 1024


def tree_rss(proc: psutil.Process) -> int:
    total = 0
    try:
        for p in [proc, *proc.children(recursive=True)]:
            try:
                total += p.memory_info().rss
            except psutil.Error:
                pass
    except psutil.Error:
        pass
    return total


def ollama_rss() -> int:
    total = 0
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info["name"] or "").lower().startswith("ollama"):
                total += p.memory_info().rss
        except psutil.Error:
            pass
    return total


def vram_mib() -> int | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        return sum(int(x) for x in out.split())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def machine() -> dict:
    info = {
        "sistema": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor(),
        "ram_total_gb": round(psutil.virtual_memory().total / 1024**3, 1),
    }
    if sys.platform == "win32":
        try:
            info["cpu"] = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Processor).Name"],
                capture_output=True, text=True, timeout=15,
            ).stdout.strip() or info["cpu"]
        except (OSError, subprocess.SubprocessError):
            pass
    if shutil.which("nvidia-smi"):
        try:
            info["gpu"] = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return info


def commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "."],
                               capture_output=True, text=True).stdout.strip()
        return sha + ("+alterações locais" if dirty else "")
    except OSError:
        return "desconhecido"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--intervalo", type=float, default=0.5)
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        parser.error("informe o comando depois de --")
    cmd[0] = shutil.which(cmd[0]) or str(Path(cmd[0]).resolve())

    base_vram = vram_mib()
    base_ollama = ollama_rss()
    start_utc = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd)
    ps = psutil.Process(proc.pid)
    peak = {"slidedsl_rss": 0, "ollama_rss": base_ollama, "soma_rss": 0, "vram": base_vram or 0}
    while proc.poll() is None:
        a, o, v = tree_rss(ps), ollama_rss(), vram_mib()
        peak["slidedsl_rss"] = max(peak["slidedsl_rss"], a)
        peak["ollama_rss"] = max(peak["ollama_rss"], o)
        peak["soma_rss"] = max(peak["soma_rss"], a + o)
        if v is not None:
            peak["vram"] = max(peak["vram"], v)
        time.sleep(args.intervalo)
    seconds = time.perf_counter() - t0

    report = {
        "inicio_utc": start_utc,
        "comando": cmd,
        "codigo_saida": proc.returncode,
        "commit": commit(),
        "maquina": machine(),
        "tempo_total_s": round(seconds, 1),
        "pico_ram_slidedsl_mb": round(peak["slidedsl_rss"] / MB),
        "pico_ram_ollama_mb": round(peak["ollama_rss"] / MB),
        "pico_ram_soma_mb": round(peak["soma_rss"] / MB),
        "vram_antes_mib": base_vram,
        "pico_vram_mib": peak["vram"] if base_vram is not None else None,
        "ram_ollama_antes_mb": round(base_ollama / MB),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

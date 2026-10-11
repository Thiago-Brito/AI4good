"""Sample process RAM/CPU during a run; GPU utilisation is explicitly unavailable."""

from functools import wraps
from pathlib import Path
from threading import Event, Thread
import time

import psutil

from .incremental import save_json


class ResourceMonitor:
    def __init__(self):
        self.done = Event()
        self.samples = []
        self.started = time.perf_counter()
        self.thread = Thread(target=self._run, daemon=True)

    def _run(self):
        own = psutil.Process()
        while not self.done.is_set():
            sample = {
                "elapsed_s": time.perf_counter() - self.started,
                "python_rss": own.memory_info().rss,
                "ollama_rss": 0,
                "ollama_cpu_s": 0,
                "system_cpu_percent": psutil.cpu_percent(),
            }
            for process in psutil.process_iter(["name", "memory_info", "cpu_times"]):
                try:
                    if "ollama" in (process.info["name"] or "").lower():
                        sample["ollama_rss"] += process.info["memory_info"].rss
                        cpu = process.info["cpu_times"]
                        sample["ollama_cpu_s"] += cpu.user + cpu.system
                except (psutil.Error, AttributeError):
                    pass
            self.samples.append(sample)
            self.done.wait(0.5)

    def start(self):
        self.thread.start()

    def finish(self):
        self.done.set()
        self.thread.join(timeout=3)
        return {
            "sampling_interval_s": 0.5,
            "samples": self.samples,
            "python_peak_rss": max((s["python_rss"] for s in self.samples), default=None),
            "ollama_peak_rss": max((s["ollama_rss"] for s in self.samples), default=None),
            "gpu_utilisation": None,
            "gpu_note": "Não mensurada; RAM não representa VRAM.",
            "scope": "Processo Python e processos com nome Ollama; cache e outras cargas podem interferir.",
        }


def measured(function):
    @wraps(function)
    def run(*args, **kwargs):
        monitor = ResourceMonitor()
        monitor.start()
        report = None
        try:
            report = function(*args, **kwargs)
            return report
        finally:
            data = monitor.finish()
            out = Path(args[3] if len(args) > 3 else kwargs["out"])
            if out.exists():
                save_json(out / "resources.json", data)
                if report is not None:
                    report["resources"] = data
                    save_json(out / "report.json", report)

    return run

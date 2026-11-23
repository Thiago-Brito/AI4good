"""Base comum dos testes do TCC (docs/PLANO_TCC.md, F1).

- Plano pareado: todo pedido passa por todas as condições e sementes, em ordem
  sorteada com semente registrada.
- Execução retomável: cada execução tem um id estável; o CSV recebe uma linha por
  execução concluída (ok ou erro) e execuções já registradas são puladas.
- O executor de cada teste é injetado (função), então o mesmo laço serve para T2, T3
  e T7, e os testes automáticos usam um executor simulado.
"""

from __future__ import annotations

import csv
import json
import random
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BASE_FIELDS = ["run_id", "order", "request_id", "condition", "seed", "status", "error"]


@dataclass(frozen=True)
class Run:
    order: int
    request: dict
    condition: str
    seed: int

    @property
    def run_id(self) -> str:
        return f"{self.request['id']}__{self.condition}__s{self.seed}"


def load_requests(path: Path) -> dict:
    data = json.loads(path.read_text("utf-8"))
    ids = [r["id"] for r in data["requests"]]
    if len(ids) != len(set(ids)):
        raise ValueError("IDs de pedido repetidos em " + str(path))
    return data


def plan_runs(requests: list[dict], conditions: list[str], seeds: list[int], order_seed: int):
    """Ordem sorteada, reproduzível pela semente de ordem."""
    if not requests or not conditions or not seeds:
        raise ValueError("Pedidos, condições e sementes não podem ser vazios.")
    if len(set(conditions)) != len(conditions):
        raise ValueError("Condições repetidas.")
    combos = [(r, c, s) for r in requests for c in conditions for s in seeds]
    random.Random(order_seed).shuffle(combos)
    return [Run(i, r, c, s) for i, (r, c, s) in enumerate(combos)]


def completed_ids(csv_path: Path) -> set[str]:
    if not csv_path.exists():
        return set()
    with csv_path.open(encoding="utf-8", newline="") as f:
        return {row["run_id"] for row in csv.DictReader(f) if row.get("run_id")}


def run_matrix(
    runs: list[Run],
    executor: Callable[[Run, Path], dict],
    out_dir: Path,
    *,
    metric_fields: list[str],
    retry_errors: bool = False,
    progress: Callable[[str], None] | None = None,
) -> dict:
    """Executa o que falta e devolve contagens. `executor(run, pasta)` devolve as métricas.

    Uma exceção do executor vira linha com status=error (não interrompe a matriz).
    Com retry_errors=True, linhas com erro são refeitas e a nova linha é acrescentada
    (a análise usa a última linha de cada run_id).
    """
    say = progress or (lambda message: None)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "results.csv"
    fields = BASE_FIELDS + [f for f in metric_fields if f not in BASE_FIELDS]
    if csv_path.exists():
        with csv_path.open(encoding="utf-8", newline="") as f:
            header = next(csv.reader(f), [])
        if header != fields:
            raise ValueError(f"Cabeçalho de {csv_path} difere do esperado; use outra pasta.")
        with csv_path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        # retry_errors: só conta como feita a execução que já tem alguma linha ok.
        done = {r["run_id"] for r in rows if not retry_errors or r["status"] == "ok"}
    else:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(fields)
        done = set()
    (out_dir / "plano.json").write_text(
        json.dumps(
            [
                {"order": r.order, "run_id": r.run_id, "condition": r.condition, "seed": r.seed}
                for r in runs
            ],
            ensure_ascii=False,
            indent=2,
        ),
        "utf-8",
    )
    counts = {"skipped": 0, "ok": 0, "error": 0}
    for run in runs:
        if run.run_id in done:
            counts["skipped"] += 1
            continue
        folder = out_dir / "runs" / run.run_id
        folder.mkdir(parents=True, exist_ok=True)
        say(f"[{run.order + 1}/{len(runs)}] {run.run_id}")
        row = {
            "run_id": run.run_id,
            "order": run.order,
            "request_id": run.request["id"],
            "condition": run.condition,
            "seed": run.seed,
        }
        try:
            metrics = executor(run, folder) or {}
            unknown = set(metrics) - set(fields)
            if unknown:
                raise ValueError(f"Métricas fora do cabeçalho: {sorted(unknown)}")
            row.update(metrics, status="ok", error="")
            counts["ok"] += 1
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # registrada e a matriz segue
            (folder / "erro.txt").write_text(traceback.format_exc(), "utf-8")
            row.update(status="error", error=f"{type(exc).__name__}: {exc}"[:300])
            counts["error"] += 1
        # Grava linha a linha: se o processo cair, o que terminou já está salvo.
        with csv_path.open("a", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=fields).writerow(row)
    return counts

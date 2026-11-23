"""Auditoria imediata de inferência, independente da pesquisa e da geração Alto."""

from datetime import date
import json
import math
import os
from pathlib import Path
from time import perf_counter

from .models.base import GenerationLimitError, generate_text
from .paths import replace_file


def _count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def pricing_for(model: str) -> dict | None:
    """Tarifa explícita por modelo; sem configuração não inferir preço ou custo zero."""
    try:
        price = json.loads(os.environ.get("SLIDEDSL_OPENAI_PRICING", "{}"))[model]
        date.fromisoformat(price["date"])
        values = [price[k] for k in ("input", "cached_input", "output")]
        if not all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in values):
            return None
        return {
            "model": model,
            "currency": "USD",
            "date": price["date"],
            **dict(zip(("input", "cached_input", "output"), values, strict=True)),
        }
    except (KeyError, ValueError, TypeError):
        return None


def _ms(value, scale=1.0):
    """Duração não negativa em ms (Ollama informa ns: scale=1e-6)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return round(value * scale, 3)


# Campos de tempo informados pelo servidor; ausentes = None (nunca zero inventado).
TIMING_KEYS = ("prefill_ms", "decode_ms", "load_ms", "server_total_ms")


def normalized_usage(metadata: dict, provider: str) -> dict:
    raw = metadata.get("usage") or {}
    timing = dict.fromkeys(TIMING_KEYS)
    reasoning = None
    if provider == "ollama":
        incoming = _count(metadata.get("prompt_eval_count"))
        outgoing = _count(metadata.get("eval_count"))
        cached = None
        timing.update(
            prefill_ms=_ms(metadata.get("prompt_eval_duration"), 1e-6),
            decode_ms=_ms(metadata.get("eval_duration"), 1e-6),
            load_ms=_ms(metadata.get("load_duration"), 1e-6),
            server_total_ms=_ms(metadata.get("total_duration"), 1e-6),
        )
    else:
        incoming = _count(raw.get("prompt_tokens", raw.get("input_tokens")))
        outgoing = _count(raw.get("completion_tokens", raw.get("output_tokens")))
        details = raw.get("prompt_tokens_details", raw.get("input_tokens_details")) or {}
        cached = _count(details.get("cached_tokens"))
        out_details = raw.get("completion_tokens_details", raw.get("output_tokens_details")) or {}
        reasoning = _count(out_details.get("reasoning_tokens"))
        timings = metadata.get("timings") or {}
        if provider == "llamacpp" and isinstance(timings, dict):
            prefill, decode = _ms(timings.get("prompt_ms")), _ms(timings.get("predicted_ms"))
            timing.update(
                prefill_ms=prefill,
                decode_ms=decode,
                server_total_ms=round(prefill + decode, 3)
                if prefill is not None and decode is not None
                else None,
            )
            # llama-server sem `usage` (versões antigas): usar contagens de timings.
            incoming = incoming if incoming is not None else _count(timings.get("prompt_n"))
            outgoing = outgoing if outgoing is not None else _count(timings.get("predicted_n"))
    if cached is not None and (incoming is None or cached > incoming):
        cached = None
    return {
        "input_tokens": incoming,
        "cached_input_tokens": cached,
        "output_tokens": outgoing,
        "reasoning_tokens": reasoning,
        **timing,
    }


def stage_group(record: dict) -> str:
    """Etapa para o resumo de custo: tentativa >0 de um slide conta como reparo."""
    stage = record.get("stage") or "generation"
    if stage == "slide" and (record.get("attempt") or 0) > 0:
        return "reparo"
    return stage


def cost_breakdown(records: list[dict]) -> dict:
    """Totais por deck e por etapa (custo.json). Só soma valores conhecidos e
    informa quantas chamadas não tinham o campo, para não esconder lacunas."""

    def totals(rows):
        out = {"calls": len(rows), "failed_calls": sum(r["status"] == "failed" for r in rows)}
        for key in (
            "input_tokens",
            "output_tokens",
            "reasoning_tokens",
            "wall_ms",
            *TIMING_KEYS,
        ):
            known = [r[key] for r in rows if r.get(key) is not None]
            out[key] = round(sum(known), 3) if known else None
            out[key + "_unknown_calls"] = len(rows) - len(known)
        return out

    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(stage_group(record), []).append(record)
    return {
        "schema": "slidedsl.custo.v1",
        "total": totals(records),
        "by_stage": {name: totals(rows) for name, rows in groups.items()},
    }


class RecordedModel:
    """Uma instância por execução; delega capacidades e registra sucesso e falha."""

    def __init__(self, model, folder: Path, *, max_calls: int = 60, on_usage=None):
        if not 1 <= max_calls <= 200:
            raise ValueError("Limite de chamadas deve estar entre 1 e 200.")
        self.model = model
        self.folder = folder
        self.max_calls = max_calls
        self.on_usage = on_usage
        self.records: list[dict] = []
        self.images: list[dict] = []
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / "uso_chamadas.jsonl"
        if self.path.exists() or (self.folder / "uso.json").exists():
            raise FileExistsError(
                "A pasta já contém auditoria; use uma pasta nova para não sobrescrever."
            )
        self.price = pricing_for(model.metadata.get("model_requested", ""))
        self._persist()

    def __getattr__(self, name):
        return getattr(self.model, name)

    def generate(self, system, user, **kwargs):
        return self.generate_recorded(system, user, **kwargs)

    def generate_recorded(self, system, user, *, context=None, **kwargs):
        if len(self.records) >= self.max_calls:
            raise GenerationLimitError(
                "Limite de chamadas atingido; nenhuma nova inferência foi iniciada."
            )
        # Cada adaptador mantém metadados mutáveis: limpar antes da tentativa.
        for key in (
            "usage",
            "prompt_eval_count",
            "eval_count",
            "model_returned",
            "finish_reason",
            "done_reason",
            "timings",
            "prompt_eval_duration",
            "eval_duration",
            "load_duration",
            "total_duration",
        ):
            self.model.metadata.pop(key, None)
        started = perf_counter()
        record = {
            "call": len(self.records) + 1,
            "provider": self.model.metadata.get("provider", "unknown"),
            "model_requested": self.model.metadata.get("model_requested"),
            "stage": (context or {}).get("stage", "generation"),
            "slide": (context or {}).get("slide"),
            "candidate": (context or {}).get("candidate"),
            "attempt": (context or {}).get("attempt"),
            "constraint": "grammar"
            if kwargs.get("grammar")
            else "json_schema"
            if kwargs.get("response_schema")
            else "none",
            "status": "running",
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "reasoning_tokens": None,
            "wall_ms": None,
            **dict.fromkeys(TIMING_KEYS),
            "cost_usd": None,
        }
        self.records.append(record)
        pending = self.folder / "uso_em_andamento.json"
        pending.write_text(json.dumps(record, ensure_ascii=False, indent=2), "utf-8")
        self._persist()
        if self.on_usage:
            self.on_usage(self.summary())
        try:
            result = generate_text(self.model, system, user, **kwargs)
            record["status"] = "completed"
            return result
        except Exception as exc:
            # Mensagem detalhada fica no diagnóstico do fluxo; não copiar respostas,
            # cabeçalhos, credenciais ou exceções HTTP para o registro de consumo.
            record["error_type"] = type(exc).__name__
            record["status"] = "failed"
            raise
        finally:
            elapsed = perf_counter() - started
            record.update(
                seconds=round(elapsed, 4),
                wall_ms=round(elapsed * 1000, 3),
                model_returned=self.model.metadata.get("model_returned"),
                finish_reason=self.model.metadata.get("finish_reason"),
                **normalized_usage(self.model.metadata, record["provider"]),
            )
            record["cost_usd"] = self._cost(record)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._persist()
            pending.unlink(missing_ok=True)
            if self.on_usage:
                self.on_usage(self.summary())

    def _cost(self, record):
        p = self.price
        incoming, outgoing, cached = (
            record[k]
            for k in (
                "input_tokens",
                "output_tokens",
                "cached_input_tokens",
            )
        )
        if record["provider"] != "openai" or p is None or incoming is None or outgoing is None:
            return None
        if cached is None:
            if p["input"] != p["cached_input"]:
                return None
            cached = 0
        return round(
            ((incoming - cached) * p["input"] + cached * p["cached_input"] + outgoing * p["output"])
            / 1_000_000,
            10,
        )

    def record_image(self, record: dict):
        """Imagem gerada por IA: registrada à parte das inferências de texto, somada ao total."""
        record = {"image": len(self.images) + 1, **record}
        self.images.append(record)
        with (self.folder / "uso_imagens.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._persist()
        if self.on_usage:
            self.on_usage(self.summary())

    def summary(self):
        known = [
            r
            for r in self.records
            if r["input_tokens"] is not None and r["output_tokens"] is not None
        ]
        priced = [r for r in self.records if r["cost_usd"] is not None]
        text_cost = round(sum(r["cost_usd"] for r in priced), 10)
        images_priced = [i for i in self.images if i.get("cost_usd") is not None]
        image_cost = round(sum(i["cost_usd"] for i in images_priced), 10)
        text_complete = bool(self.records) and len(priced) == len(self.records)
        return {
            "calls": len(self.records),
            "max_calls": self.max_calls,
            "failed_calls": sum(r["status"] == "failed" for r in self.records),
            "known_usage_calls": len(known),
            "unknown_usage_calls": len(self.records) - len(known),
            "known_input_tokens": sum(r["input_tokens"] or 0 for r in self.records),
            "known_output_tokens": sum(r["output_tokens"] or 0 for r in self.records),
            "known_cached_input_tokens": sum(r["cached_input_tokens"] or 0 for r in known),
            "text_cost_usd": text_cost,
            "image_calls": len(self.images),
            "image_cost_usd": image_cost,
            "unknown_image_cost": len(self.images) - len(images_priced),
            "known_cost_usd": round(text_cost + image_cost, 10),
            "cost_usd": round(text_cost + image_cost, 10)
            if text_complete and len(images_priced) == len(self.images)
            else None,
            "pricing": self.price,
        }

    def _persist(self):
        target = self.folder / "uso.json"
        temp = target.with_suffix(".tmp.json")
        temp.write_text(json.dumps(self.summary(), ensure_ascii=False, indent=2), "utf-8")
        replace_file(temp, target)
        target = self.folder / "custo.json"
        temp = target.with_suffix(".tmp.json")
        temp.write_text(
            json.dumps(cost_breakdown(self.records), ensure_ascii=False, indent=2), "utf-8"
        )
        replace_file(temp, target)

    def last_usage(self) -> dict | None:
        """Formato único da última chamada (copiado para Call em alto_generation)."""
        if not self.records:
            return None
        r = self.records[-1]
        keys = (
            "provider",
            "model_requested",
            "model_returned",
            "status",
            "finish_reason",
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "reasoning_tokens",
            "wall_ms",
            *TIMING_KEYS,
            "cost_usd",
        )
        return {k: r.get(k) for k in keys} | {"thinking": self.model.metadata.get("thinking")}

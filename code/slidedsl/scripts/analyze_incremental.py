"""Audit final evaluation evidence and measure diagnostics without inventing missing phases."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from slidedsl.benchmarking import instruction_coverage
from slidedsl.incremental import save_json, sha
from slidedsl.pipeline import validate_source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    folder = args.folder
    data = json.loads((folder / "evaluation.json").read_text(encoding="utf-8"))
    groups = []
    rubric = []
    audited = 0
    for summary in data["summary"]:
        rows = [
            r
            for r in data["runs"]
            if r["model"] == summary["model"] and r["mode"] == summary["mode"]
        ]
        rounds, finals, initial, digests = [], [], [], set()
        for row in rows:
            location = folder / row["path"]
            report = json.loads((location / "report.json").read_text(encoding="utf-8"))
            assert not report["is_mock"] and report["status"] == "EXECUTADO"
            assert len(report["slides"]) == 5 and "finished_utc" in report
            digests.add(report["model_metadata"]["model_digest"])
            for s in report["slides"]:
                initial.append(s["rounds"][0])
                finals.append(s["rounds"][-1])
                for r in s["rounds"]:
                    rounds.append(r)
                    if "transport_error" in r:
                        continue
                    rd = location / f"slides/slide_{s['number']:02d}/round_{r['round']}"
                    payload = json.loads((rd / "request.json").read_text(encoding="utf-8"))
                    response = json.loads((rd / "response.json").read_text(encoding="utf-8"))
                    raw = (rd / "raw.txt").read_bytes().decode("utf-8")
                    assert raw == response["message"]["content"] and sha(raw) == r["raw_sha256"]
                    assert (
                        sha(payload["messages"][0]["content"])
                        == report["configuration"]["system_sha256"]
                    )
                    assert sha(payload["messages"][1]["content"]) == r["user_sha256"]
                    assert payload["options"]["temperature"] == 0.1
                    assert payload["options"]["seed"] == 41 + row["repeat"]
                    assert payload["options"]["num_ctx"] == 8192
                    assert payload["options"]["num_predict"] == 4096
                    assert ("format" in payload) == (row["mode"] == "json")
                    assert payload["messages"][1]["content"].startswith(
                        "Pedido integral do usuário:\n" + data["configuration"]["request"]
                    )
                    audited += 1
            if report["compile_success"]:
                source = (location / "presentation.sld").read_text(encoding="utf-8")
                result = validate_source(source)
                assert result.success() and len(result.ir.slides) == 5
                rubric.append(
                    {
                        "model": row["model"],
                        "mode": row["mode"],
                        "repeat": row["repeat"],
                        "instruction_coverage": instruction_coverage(result),
                    }
                )
        group = {
            **summary,
            "model_digests": sorted(digests),
            "responses": len(rounds),
            "empty_content": sum(
                r.get("metadata", {}).get("eval_count") is not None
                and r.get("diagnostics", [{}])[0].get("code") == "G002"
                and r.get("diagnostics", [{}])[0].get("evidence", {}).get("content_chars") == 0
                for r in rounds
                if r.get("diagnostics")
            ),
            "length_responses": sum(
                r.get("metadata", {}).get("done_reason") == "length" for r in rounds
            ),
            "transport_errors": sum("transport_error" in r for r in rounds),
            "final_design_slides_reached": sum(r["semantic_success"] for r in finals),
            "final_design_errors": sum(r.get("design_errors") or 0 for r in finals),
            "final_design_warnings": sum(r.get("design_warnings") or 0 for r in finals),
            "all_diagnostics": dict(
                Counter(d["code"] + ":" + d["severity"] for r in rounds for d in r["diagnostics"])
            ),
            "final_diagnostics": dict(
                Counter(d["code"] + ":" + d["severity"] for r in finals for d in r["diagnostics"])
            ),
            "initial_slide_parse": sum(r["parse_success"] for r in initial),
            "final_slide_parse": sum(r["parse_success"] for r in finals),
            "initial_slide_semantics": sum(r["semantic_success"] for r in initial),
            "final_slide_semantics": sum(r["semantic_success"] for r in finals),
        }
        assert len(digests) == 1
        groups.append(group)
    result = {
        "audited_real_responses": audited,
        "groups": groups,
        "rubric_of_compiled_decks": rubric,
        "limits": "complete is API completion, not factual correctness; raw output unmodified; generation parameters fixed within each mode; modes have different schema/prompt/wrapping; latency includes model loading and concurrent demonstrations/tests",
    }
    save_json(folder / "audit_analysis.json", result)
    fields = [k for k, v in groups[0].items() if not isinstance(v, (dict, list))]
    with (folder / "analysis.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: g[k] for k in fields} for g in groups)
    lines = [
        "# Evidência auditada da avaliação incremental",
        "",
        f"{audited} respostas reais: conteúdo HTTP, hashes, pedido integral, seeds e parâmetros conferidos.",
        "",
        "| Modelo | Modo | PPTX/5 | Respostas | Length | Erros transporte | Design alcançado (slides/25) | Erros design final | Avisos design final | Correções |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for g in groups:
        lines.append(
            f"| {g['model']} | {g['mode']} | {g['compile_success']} | {g['responses']} | {g['length_responses']} | {g['transport_errors']} | {g['final_design_slides_reached']} | {g['final_design_errors']} | {g['final_design_warnings']} | {g['corrections']} |"
        )
    lines += [
        "",
        "Os erros/avisos são somados somente nos slides cuja semântica foi alcançada; fases não alcançadas não contam como aprovação.",
        "",
        "## Rubrica do pedido original (proxies geométricos/lexicais)",
        "",
    ]
    for r in rubric:
        c = r["instruction_coverage"]
        failed = ", ".join(k for k, v in c["items"].items() if not v)
        lines.append(
            f"- {r['model']} {r['mode']} rep {r['repeat']}: {c['numerator']}/{c['denominator']}; não atendidos pelo proxy: {failed}."
        )
    lines += [
        "",
        result["limits"],
        "",
        "JSON schema é um auxílio de decodificação; validação Pydantic e semântica continuam necessárias. PPTX válido não equivale a atender o pedido completo.",
        "",
    ]
    (folder / "ANALISE_AUDITADA.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps({"audited_responses": audited, "groups": groups}, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    main()

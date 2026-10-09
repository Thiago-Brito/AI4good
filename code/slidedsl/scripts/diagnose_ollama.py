"""Replay every original physical answer, preserving legacy evidence unchanged."""

from collections import Counter
import hashlib
import json

from slidedsl.incremental import save_json
from slidedsl.paths import project_root
from slidedsl.pipeline import validate_source


def main():
    root = project_root()
    original = root / "outputs/reports_ollama_20261008"
    out = root / "outputs/diagnostico_ollama"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for attempt in sorted((original / "attempts").glob("*/rep_*/C/attempt.json")):
        data = json.loads(attempt.read_text(encoding="utf-8"))
        for old_round in data["rounds"]:
            folder = attempt.parent / f"round_{old_round['round']}"
            raw_bytes = (folder / "raw.txt").read_bytes()
            raw = raw_bytes.decode("utf-8")
            replay = validate_source(raw)
            md = old_round["metadata"]
            ds = [d.model_dump() for d in replay.diagnostics]
            first = ds[0] if ds else {}
            line = first.get("line")
            offending = raw.splitlines()[line - 1] if line and line <= len(raw.splitlines()) else ""
            if not raw.strip():
                cause = "content vazio; parser encontra EOF sem apresentacao"
            elif "adicionar_imagem" in offending:
                cause = "nome com underscore; produção exige adicionar imagem"
            elif "ARQUIVO" in first.get("evidence", {}).get("expected", []):
                cause = "falta palavra arquivo antes do caminho da imagem"
            elif "trazer" in offending:
                cause = "ordem/nome inválido; produção exige trazer ID para frente"
            elif line == len(raw.splitlines()) and md.get("done_reason") == "length":
                cause = "EOF em comando incompleto após limite de tokens"
            else:
                cause = "sintaxe rejeitada; verificar contexto e tokens esperados registrados"
            record = {
                "model": data["model"],
                "repeat": data["repeat"],
                "round": old_round["round"],
                "raw_path": str((folder / "raw.txt").relative_to(root)),
                "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "content_chars": len(raw),
                "done_reason": md.get("done_reason"),
                "eval_count": md.get("eval_count"),
                "num_predict": md.get("num_predict"),
                "thinking": md.get("thinking"),
                "thinking_output_chars": md.get("thinking_output_chars"),
                "cause": cause,
                "offending_line": offending,
                "tail": raw[-240:],
                "diagnostics": ds,
                "replay_matches_original_diagnostics": ds == old_round["diagnostics"],
            }
            records.append(record)
    result = {
        "p001_definition": "parser.py: UnexpectedInput de Lark -> P001, primeira falha sintática; semântica/design não alcançados",
        "content_extraction": "adaptador retorna message.content textual sem strip, fences ou extração de thinking; corpos HTTP originais não foram preservados no experimento antigo, somente content e metadados",
        "limitations": "length confirma limite de geração, mas uma falha anterior ao EOF não é causada apenas pelo truncamento; thinking pode consumir orçamento, sem prova causal para cada content vazio",
        "legacy_metric_issue": "metrics.json usa null para design não alcançado; attempt.json antigo pode contar 0. A nova avaliação conserva null, não aprovação",
        "counts": dict(Counter((r["model"] + ":" + str(r["done_reason"])) for r in records)),
        "responses": records,
    }
    save_json(out / "evidence.json", result)
    lines = [
        "# Diagnóstico das 30 respostas físicas originais",
        "",
        result["p001_definition"],
        "",
        result["content_extraction"],
        "",
        result["limitations"],
        "",
        result["legacy_metric_issue"],
        "",
        "| Modelo | Rep | Rodada | Finalização | Tokens | Content chars | Thinking chars | Linha:coluna | Causa |",
        "|---|---:|---:|---|---:|---:|---:|---|---|",
    ]
    for r in records:
        d = r["diagnostics"][0]
        lines.append(
            f"| {r['model']} | {r['repeat']} | {r['round']} | {r['done_reason']} | {r['eval_count']} | {r['content_chars']} | {r['thinking_output_chars']} | {d['line']}:{d['column']} | {r['cause']} |"
        )
    (out / "DIAGNOSTICO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"{len(records)} respostas auditadas; replay idêntico: {sum(r['replay_matches_original_diagnostics'] for r in records)}"
    )


if __name__ == "__main__":
    main()

from slidedsl.benchmarking import instruction_coverage, run_benchmark
from slidedsl.models.mock_model import MockTextModel
from slidedsl.pipeline import validate_source
import pytest


def test_rubric_reference_is_complete(root):
    result = validate_source((root / "examples/cinco_slides.sld").read_text(encoding="utf-8"))
    rubric = instruction_coverage(result)
    assert rubric["numerator"] == rubric["denominator"] == 17


def test_mock_counts_success_and_failure(root, tmp_path):
    valid = (root / "examples/cinco_slides.sld").read_text(encoding="utf-8")
    adapter = MockTextModel([valid, "texto inválido"])
    report = run_benchmark(
        ["mock:controlado"],
        2,
        tmp_path,
        conditions=["A", "B"],
        adapters={"mock:controlado": adapter},
    )
    assert adapter.calls == 2
    assert len(report["attempts"]) == 4
    assert all(s["parse_rate_first"] == 0.5 for s in report["summary"])
    assert all(s["compile_rate_first"] == 0.5 for s in report["summary"])
    assert report["attempts"][0]["raw_sha256"] == report["attempts"][1]["raw_sha256"]
    assert report["attempts"][0]["first_attempt"]["design_warnings"] is None
    assert report["attempts"][1]["first_attempt"]["design_warnings"] == 1
    assert all(r["is_mock"] for r in report["attempts"])
    assert (tmp_path / "benchmark.csv").is_file()


def test_repair_counts_and_original_separate(root, tmp_path):
    good = (
        (root / "examples/cinco_slides.sld")
        .read_text(encoding="utf-8")
        .replace("#DDE8F9\n    adicionar texto id corpo", "#14233D\n    adicionar texto id corpo")
    )
    adapter = MockTextModel(["invalido", good])
    r = run_benchmark(
        ["mock:repair"], 1, tmp_path, conditions=["C"], adapters={"mock:repair": adapter}
    )["attempts"][0]
    assert not r["first_attempt"]["parse_success"]
    assert r["final_attempt"]["parse_success"]
    assert r["repair_rounds"] == 1
    assert r["success_after_repair"]


def test_unavailable_has_no_fake_metrics(tmp_path):
    class Missing(MockTextModel):
        def available(self):
            return False, "Indisponível no teste."

    report = run_benchmark(["mock:missing"], 5, tmp_path, adapters={"mock:missing": Missing(["x"])})
    assert report["models"]["mock:missing"]["status"] == "NAO_EXECUTADO"
    assert report["attempts"] == [] and report["summary"] == []
    assert (tmp_path / "RESULTADOS_PENDENTES.md").is_file()


def test_resume_keeps_real_attempt_bytes_and_only_generates_missing_repetitions(root, tmp_path):
    good = (root / "examples/cinco_slides.sld").read_text(encoding="utf-8")

    class Interrupted(MockTextModel):
        def generate(self, *args, **kwargs):
            if self.calls:
                raise KeyboardInterrupt()
            return super().generate(*args, **kwargs)

    with pytest.raises(KeyboardInterrupt):
        run_benchmark(
            ["mock:resume"],
            2,
            tmp_path,
            conditions=["A", "B"],
            adapters={"mock:resume": Interrupted([good])},
        )
    first_raw = tmp_path / "attempts/mock_resume/rep_01/A/round_0/raw.txt"
    original_bytes = first_raw.read_bytes()
    with pytest.raises(FileExistsError):
        run_benchmark(["mock:resume"], 2, tmp_path, conditions=["A", "B"])
    adapter = MockTextModel(["inválido"])
    report = run_benchmark(
        ["mock:resume"],
        2,
        tmp_path,
        conditions=["A", "B"],
        adapters={"mock:resume": adapter},
        resume=True,
    )
    assert adapter.calls == 1
    assert first_raw.read_bytes() == original_bytes
    assert report["models"]["mock:resume"]["reused_completed_repetitions"] == 1
    assert all(s["parse_rate_first"] == 0.5 for s in report["summary"])


def test_resume_rejects_changed_prompt_snapshot(root, tmp_path):
    class Interrupted(MockTextModel):
        def generate(self, *args, **kwargs):
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_benchmark(["mock:resume"], 2, tmp_path, adapters={"mock:resume": Interrupted()})
    (tmp_path / "system_prompt.txt").write_text("alterado", encoding="utf-8")
    with pytest.raises(ValueError, match="mesmos bytes"):
        run_benchmark(["mock:resume"], 2, tmp_path, resume=True)

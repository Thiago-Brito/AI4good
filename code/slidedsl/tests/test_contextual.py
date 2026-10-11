from copy import deepcopy
from io import BytesIO
import json
import socket
import zipfile

import httpx
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from slidedsl import documents, media
from slidedsl.contextual import contextual_schema, generate_contextual, source_audit
from slidedsl.edits import merge_manual
from slidedsl.evolution import _validate_plan
from slidedsl.layouts import VISUAL_LAYOUTS, compile_plan, plan_to_dsl
from slidedsl.planning import DeckPlan
from slidedsl.preview import render_optional
from slidedsl.serializer import to_dsl
from slidedsl.server import app
from test_evolution import Answers, plan_data


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org/image.png",
        "https://user:pass@example.org/i.png",
        "https://127.0.0.1/i.png",
        "https://[::1]/i.png",
        "https://10.0.0.1/i.png",
        "https://169.254.169.254/i.png",
        "https://192.168.1.1/i.png",
        "https://example.org:8443/i.png",
        "file:///etc/passwd",
        "https://example.org/i.png#x",
    ],
)
def test_ssrf_blocks_private_and_non_https(url):
    with pytest.raises(ValueError):
        media.public_target(url)


def test_dns_with_any_private_address_is_blocked():
    def resolve(*args, **kwargs):
        return [(socket.AF_INET, 1, 6, "", (a, 443)) for a in ["8.8.8.8", "10.0.0.2"]]

    with pytest.raises(ValueError, match="interno"):
        media.public_target("https://example.org/image.png", resolve)


def simulated_network(monkeypatch, handler):
    original = media.public_target

    def check(url):
        def resolver(host, *args, **kwargs):
            address = "127.0.0.1" if host == "localhost" else "8.8.8.8"
            return [(socket.AF_INET, 1, 6, "", (address, 443))]

        return original(url, resolver)

    monkeypatch.setattr(media, "public_target", check)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(media.httpx, "Client", lambda **kwargs: client)


def test_downloader_pins_checked_ip_and_preserves_tls_name(monkeypatch):
    observed = []

    def handler(request):
        observed.append(request)
        return httpx.Response(200, content=b"abc", headers={"content-type": "image/png"})

    simulated_network(monkeypatch, handler)
    assert media.fetch_public("https://example.org/i.png")[0] == b"abc"
    assert observed[0].url.host == "8.8.8.8"
    assert observed[0].headers["host"] == "example.org"
    assert observed[0].extensions["sni_hostname"] == "example.org"


def test_redirect_to_localhost_is_rejected(monkeypatch):
    simulated_network(
        monkeypatch,
        lambda request: httpx.Response(302, headers={"location": "https://localhost/secret"}),
    )
    with pytest.raises(ValueError, match="interno"):
        media.fetch_public("https://example.org/i.png")


@pytest.mark.parametrize(
    "headers,data",
    [
        ({"content-type": "image/svg+xml"}, b"<svg/>"),
        ({"content-type": "image/png", "content-length": "100"}, b"a"),
        ({"content-type": "image/png"}, b"123456789"),
    ],
)
def test_download_mime_and_size_limits(monkeypatch, headers, data):
    simulated_network(
        monkeypatch, lambda request: httpx.Response(200, headers=headers, content=data)
    )
    with pytest.raises(ValueError):
        media.fetch_public("https://example.org/i.png", limit=4)


def test_verified_image_cache_reencodes_and_works_without_network(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "project_root", lambda: tmp_path)
    id = "a" * 64
    folder = media.store_root() / "candidates"
    folder.mkdir(parents=True)
    item = {
        "id": id,
        "provider": "openverse",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "url": "https://example.org/a.png",
    }
    (folder / f"{id}.json").write_text(json.dumps(item))
    data = BytesIO()
    Image.new("RGB", (640, 360)).save(data, "PNG")
    monkeypatch.setattr(
        media, "fetch_public", lambda *args, **kwargs: (data.getvalue(), "image/png")
    )
    asset = media.cache_image(id)
    assert asset["width"] == 640 and (tmp_path / asset["asset"]).is_file()
    monkeypatch.setattr(
        media, "fetch_public", lambda *args, **kwargs: pytest.fail("Cache deve funcionar offline")
    )
    assert media.cache_image(id) == asset


def test_image_without_license_and_malicious_header_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "project_root", lambda: tmp_path)
    id = "b" * 64
    folder = media.store_root() / "candidates"
    folder.mkdir(parents=True)
    path = folder / f"{id}.json"
    item = {
        "id": id,
        "provider": "openverse",
        "license_url": "",
        "url": "https://example.org/a.png",
    }
    path.write_text(json.dumps(item))
    with pytest.raises(ValueError, match="Licença"):
        media.cache_image(id)
    item["license_url"] = "https://creativecommons.org/publicdomain/zero/1.0/"
    path.write_text(json.dumps(item))
    monkeypatch.setattr(
        media, "fetch_public", lambda *args, **kwargs: (b"<script>bad</script>", "image/png")
    )
    with pytest.raises(ValueError, match="Assinatura"):
        media.cache_image(id)


def test_documents_retrieval_pages_and_deletion(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "project_root", lambda: tmp_path)
    a = documents.add_document(
        "business.md", b"Revenue means sales income.\n\nCosts describe expenses."
    )
    b = documents.add_document("unrelated.txt", b"An apple is a fruit.")
    selected = documents.retrieve([a["id"], b["id"]], "sales revenue")
    assert selected and all(c["document_id"] == a["id"] for c in selected)
    assert selected[0]["page"] is None and selected[0]["document_name"] == "business.md"
    documents.delete_document(a["id"])
    assert not documents.document_path(a["id"]).exists()
    with pytest.raises(ValueError):
        documents.document_path("../outside")


def test_pdf_text_extracted_in_bounded_process(tmp_path, monkeypatch):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    monkeypatch.setattr(documents, "project_root", lambda: tmp_path)
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 100 Td (Water freezes at low temperatures.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    doc = documents.add_document("science.pdf", output.getvalue())
    selected = documents.retrieve([doc["id"]], "Water")
    assert selected[0]["page"] == 1 and "Water freezes" in selected[0]["text"]


@pytest.mark.parametrize(
    "name,data",
    [("script.exe", b"bad"), ("x.txt", b"\x00bad"), ("x.pdf", b"notpdf"), ("empty.txt", b"")],
)
def test_document_integrity_limits(tmp_path, monkeypatch, name, data):
    monkeypatch.setattr(documents, "project_root", lambda: tmp_path)
    with pytest.raises(ValueError):
        documents.add_document(name, data)


@pytest.mark.parametrize("layout", sorted(VISUAL_LAYOUTS))
def test_visual_layouts_compile_real_pptx_without_image_distortion(tmp_path, layout):
    data = plan_data()
    slide = data["slides"][0]
    slide.update(
        layout=layout,
        columns=[{"heading": "", "items": ["Texto curto."], "group": False}],
        decorations=[],
        relations=[],
        footer="",
    )
    if layout == "image_comparison":
        slide["columns"] *= 2
    count = 2 if layout == "image_comparison" else 1
    slide["media"] = [
        {"asset": "assets/imagem_demo.png", "query": "demo", "caption": "Imagem local"}
        for _ in range(count)
    ]
    plan = DeckPlan.model_validate(data)
    result = compile_plan(plan, tmp_path / f"{layout}.pptx", strict=True)
    assert result["inspection"]["image_objects"] == count
    _, validation, _, ds = _validate_plan(data, 1)
    assert not [d for d in ds if d["severity"] == "ERRO"]
    images = [e for e in validation.ir.slides[0].elements if e.type == "image"]
    from slidedsl.media import resolve_asset

    asset = resolve_asset("assets/imagem_demo.png")
    assert all(
        e.width / e.height == pytest.approx(asset["width"] / asset["height"]) for e in images
    )


def test_missing_media_and_overflow_remain_observable():
    data = plan_data()
    slide = data["slides"][0]
    slide.update(
        layout="text_image",
        media=[{"query": "water", "asset": "", "caption": ""}],
        columns=[{"heading": "", "items": ["Long content " * 90], "group": False}],
    )
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert {"M001", "L004"} <= {d.code for d in ds}
    assert "Long content " * 90 in source and "imagem_demo.png" not in source


def test_vector_flow_roundtrip_and_native_editable_arrow(tmp_path):
    data = plan_data()
    slide = data["slides"][0]
    slide.update(
        layout="flow",
        vector_flow=True,
        columns=[{"heading": "", "items": ["Collect", "Validate"], "group": False}],
        relations=[{"kind": "next", "reference": "c1_i1", "target": "c1_i2"}],
    )
    result = compile_plan(DeckPlan.model_validate(data), tmp_path / "flow.pptx", strict=True)
    with zipfile.ZipFile(tmp_path / "flow.pptx") as archive:
        assert b'prst="downArrow"' in archive.read("ppt/slides/slide1.xml")
    _, validation, _, _ = _validate_plan(data, 1)
    assert "adicionar seta" in to_dsl(validation.ir)
    assert result["inspection"]["shape_objects"] == 3


def test_manual_merge_preserves_text_geometry_removal_addition_and_ids():
    _, validation, _, _ = _validate_plan(plan_data(), 1)
    base = validation.ir.model_dump()
    current, candidate = deepcopy(base), deepcopy(base)
    title = current["slides"][0]["elements"][0]
    title["text"] = "Edited title"
    title["x"] += 8
    removed = current["slides"][0]["elements"].pop()["id"]
    extra = deepcopy(title)
    extra.update(
        id="manual_note",
        text="User note",
        x=64,
        y=600,
        width=800,
        height=40,
        font_size=20,
        role="corpo",
        z=20,
    )
    current["slides"][0]["elements"].append(extra)
    merged, edits = merge_manual(base, current, candidate)
    objects = {e["id"]: e for e in merged["slides"][0]["elements"]}
    assert (
        objects[title["id"]]["text"] == "Edited title" and objects[title["id"]]["x"] == title["x"]
    )
    assert removed not in objects and "manual_note" in objects and edits


def test_simultaneous_field_conflict_is_reported_and_manual_wins():
    _, validation, _, _ = _validate_plan(plan_data(), 1)
    base = validation.ir.model_dump()
    current, candidate = deepcopy(base), deepcopy(base)
    current["slides"][0]["elements"][0]["text"] = "User"
    candidate["slides"][0]["elements"][0]["text"] = "Model"
    merged, edits = merge_manual(base, current, candidate)
    assert merged["slides"][0]["elements"][0]["text"] == "User"
    assert any(e.get("conflict") for e in edits)


def test_restricted_sources_reject_fake_ids_and_unsupported_claims():
    data = plan_data()
    data["slides"][0]["sources"] = ["known", "invented"]
    data["slides"][0]["columns"][0]["items"] = ["Unsupported fact"]
    audit = source_audit(data, [{"id": "known", "text": "A grounded quotation."}], True)
    assert {i["code"] for i in audit["issues"]} == {"F001", "F002"}
    data["slides"][0]["sources"] = ["known"]
    data["slides"][0]["footer"] = ""
    data["title"] = data["slides"][0]["title"] = "Fontes fornecidas"
    data["slides"][0]["columns"][0]["heading"] = ""
    data["slides"][0]["columns"][0]["items"] = ["A grounded quotation."]
    assert not source_audit(data, [{"id": "known", "text": "A grounded quotation."}], True)[
        "issues"
    ]


def test_context_integration_logs_actual_prompt_and_freezes_sources(tmp_path):
    adapter = Answers([json.dumps(DeckPlan.model_validate(plan_data()).model_dump())])
    result = generate_contextual(
        "test",
        "C",
        "Crie um slide",
        tmp_path / "run",
        context={"audience": "Clients", "objective": "Compare"},
        adapter=adapter,
    )
    assert result["compile_success"] and result["is_mock"]
    assert "Clients" in adapter.calls[0]["user"] and "Compare" in adapter.calls[0]["user"]
    assert (tmp_path / "run/source_hashes.json").is_file()
    assert result["resources"]["python_peak_rss"] > 0


def test_api_upload_limits_origin_and_offline_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "project_root", lambda: tmp_path)
    monkeypatch.setattr(media, "project_root", lambda: tmp_path)
    client = TestClient(app)
    assert (
        client.post(
            "/api/documents",
            json={"name": "a.txt", "data_base64": "aGk="},
            headers={"Origin": "http://127.0.0.1:5173", "Host": "127.0.0.1:8000"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/documents", json={"name": "a.txt", "data_base64": "notbase64"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/documents",
            json={"name": "a.txt", "data_base64": "aGk="},
            headers={"Origin": "https://attacker.example"},
        ).status_code
        == 403
    )
    assert client.post("/api/documents", content=b"x" * (4 * 1024 * 1024 + 1)).status_code == 413
    data = client.post(
        "/api/images/search", json={"provider": "openverse", "query": "water", "offline": True}
    ).json()
    assert data["results"] == [] and data["offline"]


def test_rendering_fallback_explicitly_does_not_claim_actual_rendering(tmp_path, monkeypatch):
    import slidedsl.preview as preview

    monkeypatch.setattr(
        preview, "rendering_available", lambda: {"powerpoint_com": False, "libreoffice": None}
    )
    report = render_optional(tmp_path / "fake.pptx", tmp_path / "render")
    assert report["engine"] == "geometric" and not report["rendered"]


def test_contextual_schema_requires_selected_image_reference_and_matching_layout():
    from jsonschema import Draft202012Validator

    data = DeckPlan.model_validate(plan_data()).model_dump()
    slide = data["slides"][0]
    slide.update(
        layout="text_image", media=[{"query": "Moon", "asset": "image1", "caption": "Lua"}]
    )
    schema = contextual_schema(1, ["image1"], [], ["text_image"])
    validator = Draft202012Validator(schema)
    validator.validate(data)
    del slide["media"][0]["asset"]
    assert list(validator.iter_errors(data))
    slide["media"][0]["asset"] = "invented"
    assert list(validator.iter_errors(data))


def test_invalid_contextual_decoder_response_remains_failed_without_manual_fallback(tmp_path):
    adapter = Answers([json.dumps(plan_data())])
    result = generate_contextual(
        "test", "C", "Crie um slide", tmp_path / "invalid", adapter=adapter
    )
    assert not result["compile_success"] and not (tmp_path / "invalid/presentation.pptx").exists()
    assert any(d["code"] == "J001" for d in result["diagnostics"])
    assert (tmp_path / "invalid/initial/round_0/raw.txt").exists()


def test_documents_cannot_be_sent_to_remote_ollama(tmp_path):
    adapter = Answers([])
    adapter.base_url = "https://remote.example"
    with pytest.raises(ValueError, match="própria máquina"):
        generate_contextual(
            "test",
            "C",
            "Crie um slide",
            tmp_path / "remote",
            context={"documents": ["a" * 32]},
            adapter=adapter,
        )
    assert not adapter.calls


def test_nasa_requires_individual_rights_review(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "project_root", lambda: tmp_path)
    folder = media.store_root() / "candidates"
    folder.mkdir(parents=True)
    id = "c" * 64
    (folder / f"{id}.json").write_text(json.dumps({"provider": "nasa"}))
    with pytest.raises(ValueError, match="revisar"):
        media.cache_image(id)


def test_failed_repair_keeps_current_manual_scene(tmp_path, monkeypatch):
    from slidedsl import generation_jobs, reliability

    _, validation, _, _ = _validate_plan(plan_data(), 1)
    base = validation.ir.model_dump()
    current = deepcopy(base)
    current["slides"][0]["elements"][0]["text"] = "Manual title must survive"
    current["slides"][0]["elements"][0]["x"] = 1300

    def invalid(data, request, out, **kwargs):
        out.mkdir(parents=True)
        return {
            "valid": False,
            "compile_success": False,
            "diagnostics": [],
            "requirements": {"numerator": 0, "denominator": 2},
        }

    monkeypatch.setattr(reliability, "run_reliability", invalid)
    monkeypatch.setattr(generation_jobs, "project_root", lambda: tmp_path)
    id = "d" * 32
    generation_jobs.jobs[id] = {
        "id": id,
        "state": "queued",
        "events": [],
        "result": None,
        "error": None,
    }
    generation_jobs._work(
        id,
        {
            "model": "test",
            "strategy": "D",
            "prompt": "Crie um slide",
            "plan": plan_data(),
            "requirements": [],
            "repair_max": 2,
            "strict": True,
            "seed": 42,
            "base_ir": base,
            "current_ir": current,
        },
    )
    job = generation_jobs.read_job(id)
    assert job["state"] == "completed"
    assert "Manual title must survive" in job["result"]["source"]
    assert not job["result"]["report"]["compile_success"]
    assert job["result"]["report"]["geometry"] is False
    assert any(d["code"] == "D001" for d in job["result"]["report"]["diagnostics"])
    generation_jobs.jobs.pop(id)


def test_manual_text_edit_keeps_layer_instructions_and_final_order():
    from slidedsl.edits import merged_source
    from slidedsl.ir import Presentation
    from slidedsl.pipeline import validate_source

    data = plan_data()
    data["slides"][0]["decorations"] = [
        {"kind": "rectangle", "slot": "left", "color": "primaria"},
        {"kind": "image", "slot": "overlay", "color": "primaria"},
    ]
    data["slides"][0]["relations"] = [
        {"kind": "back", "target": "d2", "reference": ""},
        {"kind": "front", "target": "d2", "reference": ""},
    ]
    original, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    result = validate_source(original)
    deck = result.ir.model_copy(deep=True)
    next(e for e in deck.slides[0].elements if e.role == "titulo").text = "Título manual"
    source = merged_source(Presentation.model_validate(deck.model_dump()), original)
    updated = validate_source(source)
    assert updated.semantic_success
    assert "enviar s1_d2 para tras" in source and "trazer s1_d2 para frente" in source
    assert [(e.id, e.z) for e in updated.ir.slides[0].elements] == [
        (e.id, e.z) for e in deck.slides[0].elements
    ]


def test_local_image_import_is_offline_sanitized_and_metadata_preserved(tmp_path, monkeypatch):
    import base64

    monkeypatch.setattr(media, "project_root", lambda: tmp_path)
    monkeypatch.setattr(media, "fetch_public", lambda *a, **kw: pytest.fail("Upload é offline"))
    image = BytesIO()
    Image.new("RGB", (640, 360)).save(image, "PNG")
    payload = {
        "name": "../../local.png",
        "data_base64": base64.b64encode(image.getvalue()).decode(),
        "author": "Autor de teste",
        "license_note": "Criação própria",
        "rights_confirmed": True,
    }
    with TestClient(app) as client:
        response = client.post("/api/images/local", json=payload)
    assert response.status_code == 201
    asset = response.json()
    assert asset["provider"] == "local" and asset["title"] == "local.png"
    assert asset["author"] == "Autor de teste" and asset["reviewed"]
    assert (tmp_path / asset["asset"]).is_file()
    assert asset in media.cached_assets()
    assert media.resolve_asset(asset["asset"])["width"] == 640


@pytest.mark.parametrize("fault", ["rights", "size", "magic", "format"])
def test_local_image_import_rejects_unauthorized_or_invalid_files(tmp_path, monkeypatch, fault):
    monkeypatch.setattr(media, "project_root", lambda: tmp_path)
    image = BytesIO()
    Image.new("RGB", (640, 360)).save(image, "PNG")
    args = {
        "name": "image.png",
        "data": image.getvalue(),
        "license_note": "Autorização",
        "rights_confirmed": True,
    }
    if fault == "rights":
        args["rights_confirmed"] = False
    if fault == "size":
        args["data"] = b"x" * (2 * 1024 * 1024 + 1)
    if fault == "magic":
        args["data"] = b"<script/>"
    if fault == "format":
        args["name"] = "image.svg"
    with pytest.raises(ValueError):
        media.local_image(**args)
    assert not media.cached_assets()

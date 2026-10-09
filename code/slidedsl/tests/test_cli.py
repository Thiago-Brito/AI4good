from slidedsl.cli import main


def test_cli_validate_and_json(root, tmp_path):
    out = tmp_path / "diagnostics.json"
    assert main(["validate", str(root / "examples/cinco_slides.sld"), "--json", str(out)]) == 0
    assert out.is_file()
    # O exemplo intencionalmente fraco de contraste deve falhar no modo estrito.
    assert main(["validate", str(root / "examples/cinco_slides.sld"), "--strict"]) == 1


def test_cli_negative(root, tmp_path):
    assert main(["validate", str(root / "examples/negativo_id_duplicado.sld")]) == 1
    assert (
        main(
            [
                "compile",
                str(root / "examples/negativo_id_duplicado.sld"),
                "--out",
                str(tmp_path / "x.pptx"),
            ]
        )
        == 1
    )
    assert not (tmp_path / "x.pptx").exists()


def test_cli_ast_ir(root, tmp_path):
    for cmd in ["ast", "ir"]:
        assert (
            main(
                [
                    cmd,
                    str(root / "examples/cinco_slides.sld"),
                    "--out",
                    str(tmp_path / f"{cmd}.json"),
                ]
            )
            == 0
        )

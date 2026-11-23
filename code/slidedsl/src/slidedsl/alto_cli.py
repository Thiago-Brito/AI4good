"""Comandos da SlideDSL Alto, da pesquisa e da geração com SLM."""

import json
import sys
from pathlib import Path

COMMANDS = {"alto-validate", "alto-compile", "alto-dsl", "previa", "pesquisar", "criar", "gbnf",
            "alto-refazer", "alto-ajustar", "google-slides", "alto-svg"}


def add_parsers(sub):
    for command in ("alto-refazer", "alto-ajustar"):
        p = sub.add_parser(command, help="Editar Alto preservando os demais slides")
        p.add_argument("file")
        p.add_argument("--slide", type=int, default=1)
        p.add_argument("--out", required=True, help="Pasta nova ou arquivo .slda")
        p.add_argument("--dossie")
        if command == "alto-refazer":
            p.add_argument("--instrucao", required=True)
            p.add_argument("--provider", default="ollama", choices=["ollama", "llamacpp", "openai"])
            p.add_argument("--model", default="qwen3:4b-instruct")
        else:
            group = p.add_mutually_exclusive_group(required=True)
            group.add_argument("--foto-buscar")
            group.add_argument("--foto-arquivo", help="Asset local importado pelo catálogo de imagens")
            group.add_argument("--sem-foto", action="store_true")
            group.add_argument("--tema", choices=["auto", "claro", "escuro", "editorial", "vibrante", "natural", "noturno"])
            group.add_argument("--mover-para", type=int)
            group.add_argument("--excluir", action="store_true")
    p = sub.add_parser("alto-validate", help="Validar SlideDSL Alto (.slda)")
    p.add_argument("file")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--dossie", help="Dossiê de pesquisa para conferir fontes F1..Fn")
    p.add_argument("--json", help="Salvar relatório JSON")
    p = sub.add_parser("alto-compile", help="Compilar SlideDSL Alto para PowerPoint editável")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--strict", action="store_true")
    p.add_argument("--dossie")
    p = sub.add_parser("alto-dsl", help="Mostrar a SlideDSL 1.1 gerada a partir da Alto")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--dossie")
    p = sub.add_parser("alto-svg", help="Desenhar em SVG os slides etapas/grafico de um .slda")
    p.add_argument("file")
    p.add_argument("--out", required=True, help="Pasta de saída")
    p = sub.add_parser("previa", help="Prévia PNG aproximada de .slda ou .sld (sem Office)")
    p.add_argument("file")
    p.add_argument("--out", required=True, help="Pasta de saída")
    p.add_argument("--dossie")
    p = sub.add_parser("pesquisar", help="Pesquisar na internet e montar dossiê de fatos")
    p.add_argument("tema")
    p.add_argument("--out", required=True)
    p.add_argument(
        "--buscador", default="searxng", choices=["searxng", "wikipedia", "brave", "tavily"]
    )
    p.add_argument("--idiomas", default="pt,en", help="Wikipédias consultadas")
    p.add_argument(
        "--provider",
        choices=["ollama", "llamacpp", "openai"],
        help="Modelo para consultas/extração; sem ele, extração heurística",
    )
    p.add_argument("--model", default="qwen3:4b-instruct")
    p.add_argument("--offline", action="store_true", help="Usar somente o cache local")
    p.add_argument("--contato", help="E-mail ou site para o User-Agent (política Wikimedia)")
    p = sub.add_parser("criar", help="Pesquisar, planejar e gerar slides com SLM + GLC")
    p.add_argument("pedido", help="Pedido em linguagem natural ou @arquivo.txt")
    p.add_argument("--out", required=True, help="Pasta da execução")
    p.add_argument("--provider", default="ollama", choices=["ollama", "llamacpp", "openai"])
    p.add_argument("--model", default="qwen3:4b-instruct")
    p.add_argument("--slides", type=int, default=6)
    p.add_argument(
        "--modo",
        default=None,
        choices=["json", "gramatica", "direto"],
        help="Padrão: gramatica no llamacpp, json nos demais",
    )
    p.add_argument("--candidatos", type=int, default=1, help="Versões por slide (best-of-N)")
    p.add_argument("--max-chamadas", type=int, default=60, help="Limite local de inferências")
    p.add_argument("--reparos", type=int, default=2)
    p.add_argument(
        "--buscador",
        default="searxng",
        choices=["searxng", "nenhum", "wikipedia", "brave", "tavily"],
        help="Padrão: SearXNG local. Os demais existem só para comparação experimental.",
    )
    p.add_argument("--idiomas", default="pt,en")
    p.add_argument("--dossie", help="Reusar dossiê existente em vez de pesquisar")
    p.add_argument("--documento", action="append", default=[], help="Arquivo TXT/MD/PDF/DOCX (até oito)")
    p.add_argument("--fontes", choices=["documentos", "documentos+internet"])
    p.add_argument("--imagens", action="store_true", help="Buscar imagens licenciadas")
    p.add_argument(
        "--lote", action="store_true",
        help="Escrever todos os slides numa só chamada (menos tokens)",
    )
    p.add_argument(
        "--imagens-fonte", choices=["livres", "livres_ia", "ia"], default="livres",
        help="livres: Wikimedia; livres_ia: IA quando faltar foto; ia: só IA (pago)",
    )
    p.add_argument(
        "--imagens-ia-qualidade", choices=["economica", "media"], default="economica",
        help="economica: gpt-image-2 baixa (~US$ 0,005); media: gpt-image-1-mini média (~US$ 0,015)",
    )
    p.add_argument("--tema", default="auto", choices=["auto", "claro", "escuro", "editorial", "vibrante", "natural", "noturno"])
    p.add_argument("--temperatura", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--contexto", type=int, default=8192, help="num_ctx do Ollama")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--contato", help="E-mail ou site para o User-Agent (política Wikimedia)")
    p.add_argument(
        "--sem-fatos", action="store_true", help="Continuar mesmo se a pesquisa não encontrar fatos"
    )
    p.add_argument(
        "--sem-verificacao",
        action="store_true",
        help="Não conferir se as frases são sustentadas pelos fatos",
    )
    p.add_argument(
        "--fallback-wikipedia",
        action="store_true",
        help="Se o SearXNG não trouxer fontes, tentar a Wikipedia",
    )
    p.add_argument(
        "--sem-cobertura",
        action="store_true",
        help="Não extrair/conferir os tópicos exigidos pelo pedido",
    )
    p = sub.add_parser("google-slides", help="Enviar um PPTX ao Google Slides (login do Google)")
    p.add_argument("file", help="Arquivo .pptx")
    p.add_argument("--titulo", help="Nome da apresentação no Drive (padrão: nome do arquivo)")
    p = sub.add_parser("gbnf", help="Exportar a GLC como gramática GBNF (llama.cpp)")
    p.add_argument("--out", required=True)
    p.add_argument("--regra", default="start", help="Regra inicial (ex.: topicos)")
    p.add_argument("--baixo-nivel", action="store_true", help="Usar a SlideDSL 1.1")


def _facts(path):
    if not path:
        return None
    from .research import Dossier

    return Dossier.load(Path(path)).fact_map()


def _model(provider, name, context=8192):
    from .local_settings import load_local_settings
    from .models.factory import create_model

    if provider == "openai":
        load_local_settings()
    model = create_model(provider, name)
    if provider == "ollama":
        model.context_length = context
        model.output_tokens = 2048
        model.metadata.update(num_ctx=context, num_predict=2048)
    return model


def _print_diagnostics(diagnostics):
    for d in diagnostics:
        if d.severity == "INFORMAÇÃO":
            continue
        path = (d.evidence or {}).get("path") or d.element or "cena"
        print(f"{d.severity} {d.code} slide {d.slide} / {path}: {d.message}")


def run(args) -> int:
    from .alto_compile import build_alto, compile_alto

    if args.command in {"alto-refazer", "alto-ajustar"}:
        from .alto_edit import ajustar_alto, export_edit, refazer_slide
        from .model_usage import RecordedModel

        source = Path(args.file).read_bytes().decode("utf-8-sig")
        dossier_path = args.dossie or (str(Path(args.file).parent / "dossie.json")
                                      if (Path(args.file).parent / "dossie.json").exists() else None)
        facts = _facts(dossier_path)
        target = Path(args.out)
        folder = target.with_suffix("") if target.suffix == ".slda" else target
        if folder.exists() or target.exists():
            raise ValueError("A saída já existe; escolha uma pasta nova.")
        if args.command == "alto-refazer":
            model = RecordedModel(_model(args.provider, args.model), folder, max_calls=2)
            source = refazer_slide(source, args.slide, args.instrucao, facts, model)
        else:
            source = ajustar_alto(source, numero=args.slide, tema=args.tema,
                foto_buscar=args.foto_buscar, foto_arquivo=args.foto_arquivo,
                sem_foto=args.sem_foto, mover_para=args.mover_para, excluir=args.excluir)
        export_edit(source, folder, facts)
        if dossier_path:
            (folder / "dossie.json").write_bytes(Path(dossier_path).read_bytes())
        if target.suffix == ".slda":
            target.write_bytes(source.encode("utf-8"))
        print(f"Edição salva em {folder}")
        return 0
    if args.command == "alto-svg":
        from .alto import parse_alto
        from .svg_diagrams import deck_svgs

        deck = parse_alto(Path(args.file).read_text(encoding="utf-8-sig"))
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        diagrams = deck_svgs(deck)
        for number, result in diagrams:
            target = out / f"slide{number:02d}_{result.kind}.svg"
            target.write_text(result.svg, "utf-8")
            for warning in result.warnings:
                print(f"AVISO {target.name}: {warning}", file=sys.stderr)
        print(f"{len(diagrams)} diagrama(s) SVG em {out}")
        return 0
    if args.command in {"alto-validate", "alto-compile", "alto-dsl", "previa"}:
        source = Path(args.file).read_text(encoding="utf-8-sig")
        facts = _facts(getattr(args, "dossie", None))
        if args.command == "previa":
            from .ir_preview import contact_sheet, render_deck

            if Path(args.file).suffix.lower() == ".sld":
                from .pipeline import validate_source

                ir = validate_source(source).ir
            else:
                ir = build_alto(source, facts).validation.ir
            if ir is None:
                print("Não foi possível gerar a cena; rode a validação.", file=sys.stderr)
                return 1
            paths = render_deck(ir, Path(args.out))
            print(f"Prévia: {contact_sheet(paths, Path(args.out) / 'previa.png')}")
            return 0
        if args.command == "alto-compile":
            result, info = compile_alto(source, Path(args.out), facts, strict=args.strict)
            _print_diagnostics(result.all_diagnostics)
            print(
                f"PPTX gerado em {args.out}: {info['inspection']['slide_count']} slides editáveis."
            )
            return 0
        result = build_alto(source, facts)
        if args.command == "alto-dsl":
            if not result.dsl:
                _print_diagnostics(result.all_diagnostics)
                return 1
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(result.dsl, "utf-8")
            print(f"SlideDSL 1.1 salva em {args.out}")
            return 0
        _print_diagnostics(result.all_diagnostics)
        if args.json:
            Path(args.json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json).write_text(
                json.dumps(result.report(args.strict), ensure_ascii=False, indent=2), "utf-8"
            )
        ok = result.success(args.strict)
        print("Validação concluída: " + ("válido" if ok else "falhou"))
        return 0 if ok else 1
    if args.command == "google-slides":
        import time
        import webbrowser

        from . import google_slides as g

        pptx = Path(args.file)
        if pptx.suffix.casefold() != ".pptx" or not pptx.is_file():
            raise ValueError("Informe um arquivo .pptx existente.")
        if not g.load_token():
            flow = g.LoginFlow()
            url = flow.start()
            print("Abrindo o navegador para você confirmar o acesso ao Google…")
            print("Se não abrir, copie este endereço:")
            print(url)
            webbrowser.open(url)
            limit = time.time() + 300
            while flow.state == "pending" and time.time() < limit:
                time.sleep(0.5)
            if flow.state != "authorized":
                flow._shutdown()
                raise ValueError(flow.error or "Login do Google não concluído em 5 minutos.")
        result = g.upload_pptx(pptx, args.titulo or pptx.stem)
        print(f"Google Slides: {result['url']}")
        return 0
    if args.command == "gbnf":
        from .gbnf import alto_gbnf, low_level_gbnf

        text = low_level_gbnf() if args.baixo_nivel else alto_gbnf(args.regra)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, "utf-8")
        print(f"GBNF salva em {args.out} ({len(text.splitlines())} regras)")
        return 0
    if args.command == "pesquisar":
        from .research import research

        model = _model(args.provider, args.model) if args.provider else None
        dossier = research(
            args.tema,
            contact=args.contato,
            model=model,
            provider=args.buscador,
            langs=tuple(args.idiomas.split(",")),
            offline=args.offline,
            progress=print,
        )
        dossier.save(Path(args.out))
        print(
            f"Dossiê salvo em {args.out}: {len(dossier.facts)} fatos de "
            f"{len(dossier.sources)} fontes ({len(dossier.rejected)} descartados)."
        )
        return 0 if dossier.facts else 1
    if args.command == "criar":
        from .alto_generation import create_presentation

        request = args.pedido
        if request.startswith("@"):
            request = Path(request[1:]).read_text(encoding="utf-8-sig").strip()
        model = _model(args.provider, args.model, args.contexto)
        ok, message = model.available()
        if not ok:
            print(f"Modelo indisponível: {message}", file=sys.stderr)
            return 1
        mode = args.modo or ("gramatica" if args.provider == "llamacpp" else "json")
        dossier = None
        if len(args.documento) > 8:
            raise ValueError("Selecione até oito documentos.")
        from .documents import add_document

        document_ids = [add_document(Path(p).name, Path(p).read_bytes())["id"] for p in args.documento]
        if args.dossie:
            from .research import Dossier

            dossier = Dossier.load(Path(args.dossie))
        report = create_presentation(
            request,
            Path(args.out),
            model,
            research_provider=None if args.buscador == "nenhum" else args.buscador,
            langs=tuple(args.idiomas.split(",")),
            dossier=dossier,
            document_ids=document_ids,
            sources_mode=args.fontes,
            n_slides=args.slides,
            theme=args.tema,
            mode=mode,
            candidates=args.candidatos,
            max_calls=args.max_chamadas,
            repair_max=args.reparos,
            images=args.imagens,
            batch=args.lote,
            image_source=args.imagens_fonte,
            ai_profile=args.imagens_ia_qualidade,
            seed=args.seed,
            temperature=args.temperatura,
            strict=args.strict,
            progress=print,
            contact=args.contato,
            allow_without_facts=args.sem_fatos,
            verify_support=not args.sem_verificacao,
            coverage=not args.sem_cobertura,
            fallback_wikipedia=args.fallback_wikipedia,
        )
        if report.get("pptx"):
            print(f"PPTX: {report['pptx']}  |  prévia: {report.get('preview')}")
            print(
                f"{report.get('facts', 0)} fatos, {report['calls']} chamadas, "
                f"{report['seconds']} s. Detalhes em {Path(args.out) / 'relatorio.json'}"
            )
            return 0
        print("Geração terminou com erros; veja validacao.json.", file=sys.stderr)
        return 1
    return 2

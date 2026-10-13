"""Comandos da SlideDSL Alto, da pesquisa e da geração com SLM."""

import json
import sys
from pathlib import Path

COMMANDS = {"alto-validate", "alto-compile", "alto-dsl", "previa", "pesquisar", "criar", "gbnf"}


def add_parsers(sub):
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
    p.add_argument("--candidatos", type=int, default=2, help="Versões por slide (best-of-N)")
    p.add_argument("--reparos", type=int, default=2)
    p.add_argument(
        "--buscador",
        default="searxng",
        choices=["searxng", "nenhum", "wikipedia", "brave", "tavily"],
        help="Padrão: SearXNG local. Os demais existem só para comparação experimental.",
    )
    p.add_argument("--idiomas", default="pt,en")
    p.add_argument("--dossie", help="Reusar dossiê existente em vez de pesquisar")
    p.add_argument("--imagens", action="store_true", help="Buscar imagens licenciadas")
    p.add_argument("--tema", default="claro", choices=["claro", "escuro"])
    p.add_argument("--temperatura", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--contexto", type=int, default=8192, help="num_ctx do Ollama")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--contato", help="E-mail ou site para o User-Agent (política Wikimedia)")
    p.add_argument("--sem-fatos", action="store_true",
                   help="Continuar mesmo se a pesquisa não encontrar fatos")
    p.add_argument("--sem-verificacao", action="store_true",
                   help="Não conferir se as frases são sustentadas pelos fatos")
    p.add_argument("--fallback-wikipedia", action="store_true",
                   help="Se o SearXNG não trouxer fontes, tentar a Wikipedia")
    p.add_argument("--sem-cobertura", action="store_true",
                   help="Não extrair/conferir os tópicos exigidos pelo pedido")
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
    from .models.factory import create_model

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
            n_slides=args.slides,
            theme=args.tema,
            mode=mode,
            candidates=args.candidatos,
            repair_max=args.reparos,
            images=args.imagens,
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

import argparse
import json
import sys
from pathlib import Path

from .diagnostics import DSLException
from .parser import parse


def write_json(path: str | Path, value) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="slidedsl", description="SlideDSL — apresentações editáveis"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command, help in [
        ("ast", "Inspecionar AST tipada"),
        ("ir", "Materializar IR JSON"),
        ("compile", "Gerar PowerPoint editável"),
        ("validate", "Validar sintaxe, semântica e design"),
    ]:
        p = sub.add_parser(command, help=help)
        p.add_argument("file", help="Programa .sld em UTF-8")
        if command != "validate":
            p.add_argument("--out", required=True, help="Caminho de saída")
        if command in {"validate", "compile"}:
            p.add_argument(
                "--strict", action="store_true", help="Tratar avisos selecionados como falha"
            )
        if command == "validate":
            p.add_argument("--json", help="Salvar relatório JSON")
    p = sub.add_parser("generate", help="Gerar SlideDSL por modelo (mock só para testes)")
    p.add_argument("--provider", required=True, choices=["ollama", "openai", "mock"])
    p.add_argument("--model", required=True)
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--repair-max", type=int, default=0, choices=[0, 1, 2])
    p.add_argument("--temperature", type=float, default=0)
    p.add_argument("--seed", type=int)
    p = sub.add_parser("benchmark", help="Experimento fixo com logs e relatório de disponibilidade")
    p.add_argument("--models", default="qwen3:0.6b,qwen3:4b,gpt-4.1-mini,gpt-4.1")
    p.add_argument("--repetitions", type=int, default=5)
    p.add_argument("--conditions", default="A,B,C")
    p.add_argument(
        "--resume",
        action="store_true",
        help="Retomar repetições completas sem sobrescrever respostas",
    )
    p.add_argument("--out", default="outputs/reports")
    for name in ("demo-local", "evaluate-local"):
        p = sub.add_parser(name, help="Geração incremental real por Ollama")
        p.add_argument("--prompt-file", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--repair-max", type=int, default=2, choices=[0, 1, 2])
        p.add_argument("--temperature", type=float, default=0.1)
        p.add_argument("--context-length", type=int, default=8192)
        p.add_argument("--output-tokens", type=int, default=4096)
        p.add_argument(
            "--strict", action="store_true", help="Também bloquear avisos D002/D008/D010"
        )
        if name == "demo-local":
            p.add_argument("--model", default="qwen3:4b-instruct")
            p.add_argument("--mode", default="json", choices=["direct", "json"])
            p.add_argument("--seed", type=int, default=42)
        else:
            p.add_argument("--models", default="qwen3:4b-instruct,qwen3:0.6b,qwen2.5:3b-instruct")
            p.add_argument("--modes", default="direct,json")
            p.add_argument("--repetitions", type=int, default=5)
            p.add_argument("--resume", action="store_true")
    for name in ("generate-planned", "evaluate-strategies"):
        p = sub.add_parser(name, help="Planejamento local e comparação A/B/C/D")
        p.add_argument("--model", default="qwen3:4b-instruct")
        p.add_argument("--out", required=True)
        p.add_argument("--temperature", type=float, default=0.1)
        p.add_argument("--context-length", type=int, default=8192)
        p.add_argument("--output-tokens", type=int, default=4096)
        p.add_argument(
            "--allow-warnings", action="store_true", help="Não bloquear avisos selecionados"
        )
        if name == "generate-planned":
            p.add_argument("--prompt-file", required=True)
            p.add_argument("--strategy", choices=["A", "B", "C", "D"], default="D")
            p.add_argument("--slides", type=int)
            p.add_argument("--seed", type=int, default=42)
            p.add_argument(
                "--reliability",
                action="store_true",
                help="Validador de requisitos e D com controle de progresso",
            )
            p.add_argument("--repair-max", type=int, default=2, choices=range(11))
        else:
            p.add_argument("--requests-file", default="benchmark/evolution_requests.json")
            p.add_argument("--strategies", default="A,B,C,D")
            p.add_argument("--repetitions", type=int, default=5)
            p.add_argument("--resume", action="store_true")
    p = sub.add_parser("compile-plan", help="Compilar plano JSON com layouts automáticos, sem IA")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p.add_argument("--strict", action="store_true")
    p = sub.add_parser(
        "evaluate-reliability", help="Ablação sobre o mesmo plano inicial e critérios congelados"
    )
    p.add_argument("--requests-file", default="benchmark/reliability_requests.json")
    p.add_argument("--model", default="qwen3:4b-instruct")
    p.add_argument("--repetitions", type=int, default=2)
    p.add_argument("--repair-max", type=int, default=2, choices=range(11))
    p.add_argument("--out", required=True)
    p = sub.add_parser("serve", help="Abrir API/editor local")
    contextual_parser = sub.add_parser(
        "generate-contextual", help="Plano visual com configurações e documentos locais opcionais"
    )
    contextual_parser.add_argument("--model", default="qwen3:4b-instruct")
    contextual_parser.add_argument("--strategy", default="D", choices=["C", "D"])
    contextual_parser.add_argument("--prompt-file", required=True)
    contextual_parser.add_argument(
        "--visual-planning",
        action="store_true",
        help="SLM escolhe intenção e representação antes do conteúdo",
    )
    contextual_parser.add_argument(
        "--context-file", help="JSON GenerationContext; padrão offline/livre"
    )
    contextual_parser.add_argument("--out", required=True)
    contextual_parser.add_argument("--repair-max", type=int, default=2, choices=range(11))
    contextual_parser.add_argument("--seed", type=int, default=42)
    experiment_parser = sub.add_parser(
        "evaluate-contextual", help="Experimentos separados de estrutura, imagens e fontes"
    )
    experiment_parser.add_argument("--requests-file", default="benchmark/contextual_requests.json")
    experiment_parser.add_argument("--model", default="qwen3:4b-instruct")
    experiment_parser.add_argument("--out", required=True)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p = sub.add_parser("inspect", help="Inspecionar conteúdo de PPTX ou relatório JSON")
    p.add_argument("file")
    p = sub.add_parser("render-preview", help="Exportar PNG via PowerPoint COM opcional")
    p.add_argument("file")
    p.add_argument("--out", required=True)
    p = sub.add_parser(
        "render-optional",
        help="PowerPoint/LibreOffice opcionais, disponibilidade e fallback explícito",
    )
    p.add_argument("file")
    p.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "evaluate-contextual":
            from .contextual_experiment import evaluate_contextual

            report = evaluate_contextual(
                Path(args.out),
                json.loads(Path(args.requests_file).read_text("utf-8-sig")),
                model=args.model,
            )
            print(
                f"{len(report['rows'])} avaliações estruturais; {report['actual_http_calls']} chamadas reais; avaliação humana não aplicada."
            )
            return 0
        if args.command == "render-optional":
            from .preview import render_optional

            report = render_optional(Path(args.file), Path(args.out))
            print(f"Mecanismo: {report['engine']}; renderização real: {report['rendered']}")
            return 0
        if args.command == "generate-contextual":
            from .contextual import generate_contextual

            context_data = (
                json.loads(Path(args.context_file).read_text("utf-8-sig"))
                if args.context_file
                else {}
            )
            if args.visual_planning:
                context_data = {
                    "provider": "auto",
                    "selection": "auto",
                    **context_data,
                    "visual_planning": True,
                }
            report = generate_contextual(
                args.model,
                args.strategy,
                Path(args.prompt_file).read_text("utf-8-sig"),
                Path(args.out),
                context=context_data,
                repair_max=args.repair_max,
                seed=args.seed,
            )
            print(f"Geração contextual em {args.out}; PPTX: {report.get('compile_success', False)}")
            return 0 if report.get("compile_success") else 1
        if args.command == "evaluate-reliability":
            from .reliability_experiment import evaluate_reliability

            report = evaluate_reliability(
                json.loads(Path(args.requests_file).read_text(encoding="utf-8-sig")),
                Path(args.out),
                model=args.model,
                repetitions=args.repetitions,
                repair_max=args.repair_max,
            )
            print(
                f"{len(report['runs'])} avaliações; {report['actual_calls']} chamadas reais; {report['status']}"
            )
            return 0 if report["status"] == "EXECUTADO" else 1
        if args.command == "compile-plan":
            from .layouts import compile_plan
            from .planning import DeckPlan

            report = compile_plan(
                DeckPlan.model_validate_json(Path(args.file).read_text(encoding="utf-8-sig")),
                Path(args.out),
                strict=args.strict,
            )
            print(f"Plano compilado: {report['inspection']['slide_count']} slides editáveis.")
            return 0
        if args.command in {"generate-planned", "evaluate-strategies"}:
            options = dict(
                temperature=args.temperature,
                context_length=args.context_length,
                output_tokens=args.output_tokens,
                strict=not args.allow_warnings,
            )
            if args.command == "generate-planned":
                from .evolution import generate_strategy

                report = generate_strategy(
                    args.model,
                    args.strategy,
                    Path(args.prompt_file).read_text(encoding="utf-8-sig"),
                    Path(args.out),
                    slide_count=args.slides,
                    seed=args.seed,
                    reliability=args.reliability,
                    repair_max=args.repair_max,
                    **options,
                )
                print(
                    f"Resultado em {args.out}; PPTX: {report['compile_success']}; "
                    f"requisitos: {report['requirements']['numerator']}/{report['requirements']['denominator']}"
                )
                return 0 if report["compile_success"] else 1
            from .evolution_experiment import evaluate_strategies

            result = evaluate_strategies(
                args.model,
                json.loads(Path(args.requests_file).read_text(encoding="utf-8-sig")),
                Path(args.out),
                repetitions=args.repetitions,
                strategies=args.strategies.split(","),
                resume=args.resume,
                **options,
            )
            print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
            return 0 if all(r["status"] == "EXECUTADO" for r in result["runs"]) else 1
        if args.command in {"demo-local", "evaluate-local"}:
            from .incremental import evaluate_incremental, generate_deck, publish_demo

            request = Path(args.prompt_file).read_text(encoding="utf-8-sig")
            options = dict(
                repair_max=args.repair_max,
                temperature=args.temperature,
                context_length=args.context_length,
                output_tokens=args.output_tokens,
                strict=args.strict,
            )
            if args.command == "demo-local":
                report = generate_deck(
                    args.model, args.mode, request, Path(args.out), seed=args.seed, **options
                )
                if report["compile_success"]:
                    publish_demo(Path(args.out), report)
                print(f"Demo salva em {args.out}; PPTX real: {report['compile_success']}")
                return 0 if report["compile_success"] else 1
            report = evaluate_incremental(
                args.models.split(","),
                args.modes.split(","),
                request,
                Path(args.out),
                repetitions=args.repetitions,
                resume=args.resume,
                **options,
            )
            print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
            return 0
        if args.command == "serve":
            import uvicorn

            uvicorn.run("slidedsl.server:app", host=args.host, port=args.port)
            return 0
        if args.command == "generate":
            from .generation import generate_file

            report = generate_file(
                args.provider,
                args.model,
                Path(args.prompt_file),
                Path(args.out),
                repair_max=args.repair_max,
                temperature=args.temperature,
                seed=args.seed,
            )
            print(f"Programa e saída original salvos em {args.out}; válido: {report['valid']}")
            return 0 if report["valid"] else 1
        if args.command == "benchmark":
            from .benchmarking import run_benchmark

            report = run_benchmark(
                args.models.split(","),
                args.repetitions,
                Path(args.out),
                conditions=args.conditions.split(","),
                resume=args.resume,
            )
            print(
                f"Benchmark salvo em {args.out}; estados: "
                + ", ".join(f"{m}: {s['status']}" for m, s in report["models"].items())
            )
            return 0
        if args.command == "inspect":
            from .compiler import inspect_pptx

            data = (
                inspect_pptx(Path(args.file))
                if Path(args.file).suffix.lower() == ".pptx"
                else json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
            )
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "render-preview":
            from .preview import render_preview

            render_preview(Path(args.file), Path(args.out))
            print(f"Preview PowerPoint exportado em {args.out}")
            return 0
        source = Path(args.file).read_text(encoding="utf-8-sig")
        if args.command == "ast":
            write_json(args.out, parse(source).model_dump())
            print(f"AST salva em {args.out}")
            return 0
        from .pipeline import validate_source

        result = validate_source(source)
        if args.command == "validate":
            if args.json:
                write_json(args.json, result.report(args.strict))
            for d in result.diagnostics:
                print(
                    f"{d.severity} {d.code} slide {d.slide} / {d.element or 'cena'} linha {d.line}:{d.column}: {d.message}"
                )
            print("Validação concluída: " + ("válido" if result.success(args.strict) else "falhou"))
            return 0 if result.success(args.strict) else 1
        if not result.semantic_success:
            raise DSLException(result.diagnostics)
        if args.command == "ir":
            from .serializer import save_ir

            save_ir(result.ir, args.out)
            print(f"IR salva em {args.out}")
        elif args.command == "compile":
            from .compiler import compile_source

            report = compile_source(source, Path(args.out), strict=args.strict)
            print(
                f"PPTX gerado em {args.out}: {report['inspection']['slide_count']} slides editáveis."
            )
        return 0
    except DSLException as exc:
        for d in exc.diagnostics:
            print(f"{d.severity} {d.code} linha {d.line}:{d.column}: {d.message}", file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

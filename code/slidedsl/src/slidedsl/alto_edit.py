"""Edit a single parsed block, preserving all other source bytes and whitespace."""

import json
from pathlib import Path

from lark import Tree

from .alto import SLIDE_KINDS, AltoDeck, alto_parser, parse_alto, print_slide
from .alto_generation import (CONTENT_SYSTEM, KIND_RULES, check_slide, clean_visible,
                              diagnostics_feedback, facts_block, json_to_slide, slide_schema)
from .diagnostics import DSLException
from .models.base import generate_text


def slide_spans(source):
    tree = alto_parser().parse(source).children[0]
    return [(c.meta.start_pos, c.meta.end_pos) for c in tree.children
            if isinstance(c, Tree) and str(c.data) in (*SLIDE_KINDS, "ciclo")]  # ciclo = etapas com cycle


def replace_slide(source, number, slide):
    spans = slide_spans(source)
    if not 1 <= number <= len(spans):
        raise ValueError("Número de slide fora do deck.")
    start, end = spans[number - 1]
    line_start = source.rfind("\n", 0, start) + 1
    indent = source[line_start:start]
    indent = indent if not indent.strip() else ""
    replacement = print_slide(slide, indent=indent)[len(indent):]
    if "\r\n" in source:
        replacement = replacement.replace("\n", "\r\n")
    return source[:start] + replacement + source[end:]


# Palavras que pedem um tipo de slide. Medido em 23/11/2026 (scripts/teste_edicao.py): com todos os
# tipos liberados, o Qwen3 4B trocou 8 de 9 slides editados por `secao` (só título), perdendo itens e
# fontes, inclusive quando a instrução pedia comparação. Por isso o tipo só muda quando é pedido.
KIND_WORDS = {
    "comparacao": ("comparacao", "comparar", "compare", "comparativo", "versus"),
    "etapas": ("etapas", "passo a passo", "passos"),
    "ciclo": ("ciclo", "circulo", "que se repete"),
    "linha_do_tempo": ("linha do tempo", "cronologia", "cronologico"),
    "numeros": ("numeros", "estatisticas", "indicadores"),
    "citacao": ("citacao", "frase de destaque"),
    "grafico": ("grafico",),
    "imagem": ("imagem", "foto"),
    "topicos": ("topicos",),
    "secao": ("secao", "divisoria"),
    "capa": ("capa",),
    "conclusao": ("conclusao",),
}
CHANGE_VERBS = ("transform", "vire", "virar", "mude", "mudar", "converta", "converter", "troque",
                "trocar", "refaca como", "faca como", "em forma de", "use o tipo", "como um slide de")


def _plain(text):
    import unicodedata

    return "".join(c for c in unicodedata.normalize("NFD", text.casefold())
                   if unicodedata.category(c) != "Mn")


def allowed_kinds(instrucao: str, current: str) -> list[str]:
    """Tipos que a edição pode produzir: o atual, salvo pedido explícito de outro tipo."""
    text = _plain(instrucao)
    wants_change = any(v in text for v in CHANGE_VERBS)
    requested = [kind for kind, words in KIND_WORDS.items()
                 if kind in (*SLIDE_KINDS, "ciclo") and any(w in text for w in words)
                 and (wants_change or kind == "comparacao")]
    return requested or [current]


def refazer_slide(deck_slda, numero, instrucao, fatos, modelo, *, roteiro=None, repair_max=1):
    if not instrucao.strip() or len(instrucao) > 2000:
        raise ValueError("Escreva uma instrução de 1 a 2000 caracteres.")
    deck = parse_alto(deck_slda)
    if not 1 <= numero <= len(deck.slides):
        raise ValueError("Número de slide fora do deck.")
    facts = fatos or {}
    current = deck.slides[numero - 1]
    # Ciclo é etapas com cycle: refazer mantém o ciclo (antes voltava a etapas comuns).
    current_kind = "ciclo" if current.cycle else current.kind
    kinds = allowed_kinds(instrucao, current_kind)
    variants = []
    for kind in kinds:
        variants.append({"type": "object", "properties": {
            "tipo": {"type": "string", "enum": [kind]},
            "conteudo": slide_schema(kind, list(facts))}, "required": ["tipo", "conteudo"]})
    schema = {"type": "object", "properties": {"slide": variants[0] if len(variants) == 1
                                                else {"anyOf": variants}}, "required": ["slide"]}
    neighbors = [print_slide(s) for i, s in enumerate(deck.slides)
                 if abs(i - (numero - 1)) == 1]
    outline = roteiro or [{"numero": i + 1, "tipo": s.kind, "titulo": s.title}
                           for i, s in enumerate(deck.slides)]
    user = (f"Deck: {deck.title}\nRoteiro: {json.dumps(outline, ensure_ascii=False)}\n"
            f"Slide atual {numero}:\n{print_slide(current)}\nVizinhos (não repetir):\n"
            + "\n".join(neighbors) + f"\nInstrução: {instrucao}\n"
            + (f"Mantenha o tipo atual ({current_kind}) e todo o conteúdo que a instrução não "
               "mandar remover.\n" if kinds == [current_kind]
               else f"Mude o tipo do slide para: {', '.join(kinds)}.\n")
            + "Regras por tipo: " + json.dumps(KIND_RULES, ensure_ascii=False)
            + "\nFatos: " + facts_block(list(facts), facts, all_facts=True))
    for attempt in range(min(1, max(0, repair_max)) + 1):
        raw = generate_text(modelo, CONTENT_SYSTEM, user, response_schema=schema,
                            temperature=.2, seed=42 + attempt,
                            context={"stage": "refazer_slide", "slide": numero, "attempt": attempt})
        try:
            data = json.loads(raw)["slide"]
            slide = clean_visible(json_to_slide(data["tipo"], data["conteudo"]), facts)
            # A request to change text keeps the selected photo unless its type changes.
            if slide.kind == current.kind and slide.kind in {"capa", "imagem"}:
                slide.image_file = current.image_file
            if slide.kind == "capa":
                slide.author = current.author
            parsed = parse_alto('deck "edição" {\n' + print_slide(slide) + '\n}')
            ds = check_slide(parsed.slides[0], facts, deck.theme)
            errors = [d for d in ds if d.severity == "ERRO"]
            repair = [d for d in ds if d.severity == "ERRO" or d.code in {"A007", "A012", "A018"}]
            if not repair or attempt == min(1, max(0, repair_max)):
                if errors:
                    raise DSLException(ds)
                return replace_slide(deck_slda, numero, slide)
            feedback = diagnostics_feedback(repair)
        except (ValueError, KeyError, TypeError, DSLException) as exc:
            if attempt == min(1, max(0, repair_max)):
                raise
            feedback = str(exc)
        user += f"\nResposta anterior:\n{raw}\nRepare somente os problemas:\n{feedback}"
    raise ValueError("Slide não produzido.")


def ajustar_alto(source, *, numero=1, tema=None, foto_buscar=None, foto_arquivo=None,
                  sem_foto=False, mover_para=None, excluir=False):
    deck = parse_alto(source)
    spans = slide_spans(source)
    if not 1 <= numero <= len(spans):
        raise ValueError("Número de slide fora do deck.")
    operations = sum(bool(x) for x in (tema, foto_buscar, foto_arquivo, sem_foto, mover_para, excluir))
    if operations != 1:
        raise ValueError("Escolha exatamente um ajuste.")
    if tema:
        from .auto_theme import choose_theme

        tema = choose_theme(deck.title) if tema == "auto" else tema
        AltoDeck(title=deck.title, theme=tema, slides=deck.slides)
        tree = alto_parser().parse(source).children[0]
        theme_node = next((c for c in tree.children if isinstance(c, Tree) and c.data == "tema"), None)
        if theme_node:
            return source[:theme_node.meta.start_pos] + f"tema {tema}" + source[theme_node.meta.end_pos:]
        position = source.index("{") + 1
        return source[:position] + f"\n  tema {tema}" + source[position:]
    if excluir or mover_para is not None:
        if excluir and len(spans) == 1:
            raise ValueError("O deck deve conservar pelo menos um slide.")
        blocks = [source[a:b] for a, b in spans]
        block = blocks.pop(numero - 1)
        if not excluir:
            if not 1 <= mover_para <= len(spans):
                raise ValueError("Destino fora do deck.")
            blocks.insert(mover_para - 1, block)
        # Preserve every block verbatim, including comments inside it.
        result, cursor = [], 0
        for i, (a, b) in enumerate(spans):
            result.append(source[cursor:a])
            result.append(blocks[i] if i < len(blocks) else "")
            cursor = b
        return "".join(result) + source[cursor:]
    slide = deck.slides[numero - 1]
    if slide.kind not in {"capa", "imagem"}:
        raise ValueError("Este tipo de slide não possui foto; refaça como imagem primeiro.")
    slide.image_file = None
    if foto_arquivo:
        from .media import local_image, resolve_asset

        try:
            slide.image_file = resolve_asset(foto_arquivo)["asset"]
        except ValueError:
            path = Path(foto_arquivo)
            slide.image_file = local_image(path.name, path.read_bytes(),
                license_note="Arquivo fornecido para esta apresentação pelo usuário",
                rights_confirmed=True)["asset"]
    elif foto_buscar:
        from .alto_generation import resolve_images

        slide.image_query = foto_buscar
        resolve_images(AltoDeck(title=deck.title, theme=deck.theme, slides=[slide]), source="livres")
    if slide.kind == "imagem" and not slide.image_file:
        slide.image_query = slide.image_query or slide.title or "foto"
    return replace_slide(source, numero, slide)


def export_edit(source, out, facts=None):
    """Save editable sources, PowerPoint and IR previews for a fresh revision."""
    from .alto_compile import build_alto
    from .compiler import compile_ir
    from .ir_preview import contact_sheet, render_deck

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    built = build_alto(source, facts)
    if not built.success():
        raise DSLException(built.all_diagnostics)
    (out / "apresentacao.slda").write_bytes(source.encode("utf-8"))
    (out / "apresentacao.sld").write_text(built.dsl, "utf-8")
    ir = built.validation.ir
    (out / "ir.json").write_text(ir.model_dump_json(indent=2), "utf-8")
    compile_ir(ir, out / "apresentacao.pptx")
    contact_sheet(render_deck(ir, out / "pngs", .6), out / "contato.png")
    (out / "validacao.json").write_text(json.dumps(built.report(), ensure_ascii=False, indent=2), "utf-8")
    return built

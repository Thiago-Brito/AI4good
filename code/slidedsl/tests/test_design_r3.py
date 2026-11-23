"""Contratos offline de legibilidade, composição e revisão editorial da rodada 3."""

from pathlib import Path
import runpy

from slidedsl.alto import AltoDeck, AltoSlide, Item, Side
from slidedsl.alto_compile import build_alto
from slidedsl.alto_generation import check_slide, resolve_images
from slidedsl.editorial import sentence_case
from slidedsl.layout_metrics import content_occupancy
from slidedsl.repetition import sibling_repetitions


def items():
    return [Item(label="Histórico do projeto", detail="Cada commit registra uma versão escolhida dos arquivos."),
            Item(label="Trabalho em equipe", detail="Uma branch permite experimentar sem alterar a linha principal.")]


def test_dense_slide_does_not_shrink_neighbors_and_ir_respects_minimum():
    from slidedsl.text_metrics import optical_size
    slides = [AltoSlide(kind="topicos", title="Git organiza o projeto", items=items()),
              AltoSlide(kind="comparacao", title="Duas formas de guardar", sides=[
                  Side(name=name, items=items() + [Item(label="Cópias locais", detail="O disco guarda arquivos.")])
                  for name in ["Manual", "Versionada"]])]
    result = build_alto(AltoDeck(title="Git", slides=slides))
    assert result.validation.ir
    assert {e.font_size for e in result.validation.ir.slides[0].elements if "_detalhe_" in e.id} == {
        optical_size(20, "Calibri", 16, effective_minimum=18)}
    for slide in result.validation.ir.slides:
        for e in slide.elements:
            if "_detalhe_" in e.id:
                assert e.font_size >= 16
            if "_rotulo_" in e.id:
                assert e.font_size >= 20
            if e.role == "titulo":
                assert e.font_size >= 32


def test_two_items_use_large_columns_with_centered_text():
    result = build_alto(AltoDeck(title="Git", slides=[
        AltoSlide(kind="conclusao", title="Pratique com um projeto", items=items())]))
    assert result.success(), result.report()
    slide = result.validation.ir.slides[0]
    cards = [e for e in slide.elements if "_card_" in e.id]
    assert len(cards) == 2 and cards[0].x < cards[1].x
    assert min(e.height for e in cards) >= 220  # inclui o número dentro do cartão
    # Texto alinhado ao topo do cartão: sem vazio grande acima do rótulo.
    labels = [e for e in slide.elements if "_rotulo_" in e.id]
    numbers = [e for e in slide.elements if "_acao_" in e.id]
    assert all(card.y < num.y < lab.y for card, num, lab in zip(cards, numbers, labels))
    assert content_occupancy(slide) >= .3


def test_overflow_reports_error_without_shrinking_below_floor():
    result = build_alto(AltoDeck(title="Git", slides=[AltoSlide(kind="topicos", title="Git organiza o projeto",
        items=[Item(label="Uma explicação", detail="palavra " * 21) for _ in range(5)])]))
    assert not result.success()
    assert any(d.code == "A010" for d in result.all_diagnostics)
    assert all(e.font_size >= 16 for e in result.validation.ir.slides[0].elements if "_detalhe_" in e.id)


def test_sibling_prefix_and_label_echo_are_detected():
    repeated = [Item(label="Cópias manuais", detail="Cópias manuais exigem nomes diferentes para cada versão."),
                Item(label="Disco local", detail="Salvar cópias manuais exige espaço no computador."),
                Item(label="Muitos arquivos", detail="Salvar cópias manuais exige organização das pastas.")]
    assert len(sibling_repetitions(repeated)) == 2
    ds = check_slide(AltoSlide(kind="topicos", title="Organize seus arquivos", items=repeated), {})
    assert any(d.code == "A020" and d.evidence['path'].endswith('.detail') for d in ds)
    assert not sibling_repetitions(items())


def test_telegraphic_label_has_targeted_warning():
    ds = check_slide(AltoSlide(kind="topicos", title="Problema das cópias manuais", items=[
        Item(label="Problema cópias manuais", detail="O nome do arquivo não identifica o conteúdo alterado."), items()[1]]), {})
    assert any(d.code == "A022" for d in ds)


def test_cover_case_preserves_names_and_acronyms():
    from slidedsl.editorial import proper_words
    assert sentence_case("Energia Solar Residencial Descomplicada") == "Energia solar residencial descomplicada"
    keep = proper_words("Crie slides sobre Git para calouros.")
    assert sentence_case("Comece Com Git e GitHub Usando API", keep) == "Comece com Git e GitHub usando API"
    # Caixa de frase já correta não é alterada (nomes sem evidência permanecem).
    assert sentence_case("Comece a usar Git hoje") == "Comece a usar Git hoje"


def test_cover_reuses_photo_search_and_shows_credit(monkeypatch):
    from slidedsl import media
    searches, downloads = [], []
    monkeypatch.setattr(media, 'automatic_search', lambda q, **kw: (
        searches.append(q) or {'results': [{'id': 'photo', 'title': 'solar panel'}]}))
    monkeypatch.setattr(media, 'automatic_candidate', lambda i: True)
    monkeypatch.setattr(media, 'cache_image', lambda i: (
        downloads.append(i) or {'asset': 'assets/imagem_demo.png'}))
    monkeypatch.setattr(media, 'resolve_asset', lambda f: {'author': 'Autora', 'license': 'CC BY 4.0'})
    deck = AltoDeck(title="Energia solar", slides=[
        AltoSlide(kind="capa", title="Energia Solar Residencial", subtitle="Entenda seu telhado", image_query="solar panel"),
        AltoSlide(kind="imagem", title="O painel recebe luz", image_query="solar panel", items=items())])
    resolve_images(deck)
    assert searches == ['solar panel'] and downloads == ['photo']
    from slidedsl.alto import print_alto, parse_alto
    frozen = print_alto(deck)
    assert parse_alto(frozen).slides[0].image_file == deck.slides[0].image_file
    result = build_alto(frozen)
    slide = result.validation.ir.slides[0]
    assert any(e.type == 'image' for e in slide.elements)
    assert any('CC BY' in (e.text or '') for e in slide.elements)
    assert all(e.font_size >= 18 for e in slide.elements if '_subtitulo_' in e.id)


def test_telegraphic_label_from_extracted_topic_is_not_exempt():
    ds = check_slide(AltoSlide(kind="topicos", title="Git ajuda a organizar", items=[
        Item(label="Problema cópias manuais", detail="Arquivos com nomes parecidos confundem as versões."), items()[1]]), {})
    assert any(d.code == "A022" for d in ds)


def test_dense_comparison_recomposes_before_reducing_body():
    from slidedsl.alto import parse_alto
    # Conteúdo congelado mínimo reproduz o overflow do primeiro ciclo, sem depender de outputs/.
    slide = AltoSlide(kind='comparacao', title='Internet é rede; Web é conteúdo acessado', sides=[
        Side(name='Internet', items=[Item(label='Rede de computadores', detail='A internet conecta computadores e dispositivos no mundo para trocar dados.'),
            Item(label='Exemplo de rede', detail='Redes permitem que celulares e computadores se comuniquem entre si.')]),
        Side(name='Web', items=items())])
    from slidedsl.alto import print_alto
    deck = parse_alto(print_alto(AltoDeck(title='Internet', slides=[slide])))
    result = build_alto(deck)
    assert result.success(), result.report()
    assert not any(d.code == 'A010' for d in result.all_diagnostics)


def test_repetition_statistics_includes_cost_of_failure():
    harness = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/comparar_alto_vs_sld.py'))
    rows = [dict(condition='A', seed=seed, cost_usd=cost, valid=valid, pptx_generated=valid,
                 pptx_slides=5 if valid else 0, input_tokens=100, output_tokens=20, cached_input_tokens=0)
            for seed, cost, valid in [(42, .01, True), (42, .02, False), (43, .02, True), (44, .04, True)]]
    stats = harness['repetition_statistics'](rows)['A']['statistics']
    assert stats['cost_usd']['min'] == .02 and stats['cost_usd']['max'] == .04
    assert stats['valid_rate']['min'] == .5
    assert stats['cost_per_valid_slide']['max'] == .008


def test_photo_filter_rejects_icon_but_keeps_real_photo():
    from slidedsl.media import photographic_candidate
    base = dict(query='git logo', lexical_score=1, width=1200, height=800,
                license_url='https://creativecommons.org/publicdomain/zero/1.0/')
    assert not photographic_candidate(dict(base, title='Git format.png', description='icon that symbolizes git format'))
    # R7: a photograph must match the requested subject; a workshop is not a logo.
    assert not photographic_candidate(dict(base, title='Git workshop', description='Participants at a computer workshop.'))
    assert photographic_candidate(dict(base, query='git workshop', title='Git workshop',
                                       description='Participants at a computer workshop.'))


def test_automatic_flow_waits_for_provider_instead_of_losing_search(monkeypatch, tmp_path):
    from slidedsl import media
    (tmp_path / 'commons.stamp').touch()
    delays = []
    monkeypatch.setattr(media, 'store_root', lambda: tmp_path)
    monkeypatch.setattr(media.time, 'sleep', delays.append)
    monkeypatch.setattr(media, 'search_images', lambda *a, **kw: {'results': []})
    media.automatic_search('solar inverter', providers=['commons'], wait_for_provider=True)
    # Folga para arredondamento do relógio entre gravar o carimbo e calcular a espera.
    assert len(delays) == 1 and 0 < delays[0] <= 2.1


def test_structural_topics_from_request_are_not_subjects():
    from slidedsl.alto_quality import structural_topic
    assert structural_topic("Conclusão") and structural_topic("Exemplos Concretos")
    assert not structural_topic("Hábitos seguros") and not structural_topic("Diferença entre internet e Web")


def test_redundant_label_is_never_suppressed_alone():
    from slidedsl.editorial import visible_labels
    group = [Item(label="Origem acadêmica", detail="Universidades ligaram computadores para pesquisa."),
             Item(label="Comunicação entre computadores", detail="Mensagens passavam de uma rede para outra.")]
    assert visible_labels(group, "Internet começou com comunicação entre computadores") == [
        "Origem acadêmica", "Comunicação entre computadores"]
    same = [Item(label="Comunicação entre computadores", detail="Mensagens passavam de uma rede a outra.")]
    assert visible_labels(same, "Internet começou com comunicação entre computadores") == [None]
    result = build_alto(AltoDeck(title="Internet", slides=[AltoSlide(
        kind="topicos", title="Internet começou com comunicação entre computadores",
        items=group + [Item(label="Redes locais", detail="Escritórios ligavam máquinas próximas por cabo.")])]))
    ids = [e.id for e in result.validation.ir.slides[0].elements]
    assert sum("_rotulo_" in i for i in ids) == 3


def test_cover_without_photo_has_no_loose_decoration():
    result = build_alto(AltoDeck(title="Git", slides=[AltoSlide(kind="capa", title="Comece a usar Git hoje",
                                                                subtitle="Controle de versões para calouros")]))
    ids = [e.id for e in result.validation.ir.slides[0].elements]
    assert not any("_motivo_" in i or "_painel_" in i for i in ids)


def test_comparison_sides_share_one_composition():
    three = items() + [Item(label="Cópias locais", detail="O disco guarda arquivos.")]
    slide = AltoSlide(kind="comparacao", title="Duas formas de guardar", sides=[
        Side(name="Manual", items=three), Side(name="Versionada", items=items())])
    ir = build_alto(AltoDeck(title="Git", slides=[slide])).validation.ir.slides[0]
    labels = sorted((e for e in ir.elements if "_rotulo_" in e.id), key=lambda e: e.x)
    details = [e for e in ir.elements if "_detalhe_" in e.id]
    # Em linhas, o detalhe fica à direita do rótulo nas duas colunas.
    left, right = labels[0].x, labels[-1].x
    assert any(d.x > left + 150 and d.x < right for d in details)
    assert any(d.x > right + 150 for d in details)

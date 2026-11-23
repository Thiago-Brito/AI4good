"""Auditoria offline dos artefatos finais da rodada 3, sem chamadas de modelo."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from slidedsl.alto_compile import build_alto


def read(path):
    return json.loads(path.read_text('utf-8'))


def audit(final, cycles):
    data = read(final / 'resultados.json')
    annotations = read(final / 'AVALIACAO_MIDIA.json') if (final / 'AVALIACAO_MIDIA.json').exists() else {}
    non_photographs = {entry['file'] for entry in annotations.get('non_photographs', [])}
    errors, fonts, photos, briefs, totals = [], [], [], {}, []
    runs = data['runs']
    expected = {(theme, condition, seed) for theme in (
        'fotossintese', 'git', 'energia_solar', 'historia_internet')
        for condition in ('A', 'B', 'B+img') for seed in (42, 43, 44)}
    if {(r['theme'], r['condition'], r['seed']) for r in runs} != expected or len(runs) != 36:
        errors.append('Lote final incompleto ou duplicado.')
    for row in runs:
        folder = final / row['folder']
        digest = hashlib.sha256((folder / 'brief.txt').read_bytes()).hexdigest()
        briefs.setdefault(row['theme'], set()).add(digest)
        if digest != row['brief_sha256']:
            errors.append(f"Hash divergente: {folder.name}")
        records = [json.loads(line) for line in (folder / 'uso_chamadas.jsonl').read_text('utf-8').splitlines()]
        usage = read(folder / 'uso.json')
        if len(records) != usage['calls'] or abs(sum(r['cost_usd'] or 0 for r in records) - usage['known_cost_usd']) > 1e-9:
            errors.append(f"Uso divergente: {folder.name}")
        ir_path = folder / 'ir.json'
        if not ir_path.exists():
            continue
        ir = read(ir_path)
        if row['condition'] != 'A':
            rebuilt = build_alto((folder / 'apresentacao.slda').read_text('utf-8'))
            if rebuilt.validation is None or rebuilt.validation.ir.model_dump() != ir:
                errors.append(f"IR não reproduz a fonte: {folder.name}")
        for slide in ir['slides']:
            for element in slide['elements']:
                if element['type'] != 'text':
                    continue
                minimum = (32 if element['role'] == 'titulo' else
                           16 if element['role'] == 'corpo' or '_detalhe_' in element['id'] else
                           20 if '_rotulo_' in element['id'] else
                           18 if row['condition'] != 'A' and '_subtitulo_' in element['id'] else 0)
                if element['font_size'] < minimum:
                    fonts.append({'folder': folder.name, 'slide': slide['number'],
                                  'id': element['id'], 'actual': element['font_size'], 'minimum': minimum})
        if not row['pptx_generated']:
            continue
        ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
              'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        with zipfile.ZipFile(folder / 'apresentacao.pptx') as archive:
            for slide in ir['slides']:
                tree = ET.fromstring(archive.read(f"ppt/slides/slide{slide['number']}.xml"))
                shapes = {node.find('.//p:cNvPr', ns).get('name'): node
                          for node in tree.findall('.//p:sp', ns)}
                for element in slide['elements']:
                    if element['type'] == 'text':
                        node = shapes.get(element['id'])
                        sizes = {int(p.get('sz')) for p in node.findall('.//a:rPr', ns) if p.get('sz')} if node is not None else set()
                        if sizes != {element['font_size'] * 100}:
                            errors.append(f"Fonte IR/PPTX diverge: {folder.name}/{element['id']}: {sizes}")
                    if element['type'] == 'image':
                        photos.append({'folder': folder.name, 'slide': slide['number'], 'file': element['file']})
    for theme, hashes in briefs.items():
        if len(hashes) != 1:
            errors.append(f'Brief desigual entre condições/seeds: {theme}')
    for batch in [*(cycles / f'ciclo_{n}' for n in (1, 2, 3)), final]:
        for usage_path in batch.glob('*/uso.json'):
            totals.append(read(usage_path))
    known = round(sum(u['known_cost_usd'] for u in totals), 10)
    ledger = read(final / 'orcamento.json')
    if abs(known - ledger['known_cost_usd']) > 1e-9:
        errors.append('Ledger não coincide com soma dos ciclos e lote final.')
    if ledger['cost_upper_bound_usd'] > .60:
        errors.append('Teto da rodada excedido.')
    manifest = read(cycles / 'codigo_final_sha256.json')
    changed = [name for name, digest in manifest.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest]
    result = {'runs': len(runs), 'valid': sum(r['valid'] for r in runs),
              'known_cost_usd': known, 'upper_bound_usd': ledger['cost_upper_bound_usd'],
              'calls': sum(u['calls'] for u in totals),
              'unknown_usage_calls': sum(u['unknown_usage_calls'] for u in totals),
              'brief_hashes_equal': all(len(v) == 1 for v in briefs.values()),
              'code_changed_after_snapshot': changed, 'font_violations': fonts,
              'images_in_pptx': photos,
              'photos_in_pptx': [p for p in photos if p['file'].startswith('assets/media/') and p['file'] not in non_photographs],
              'errors': errors}
    (final / 'auditoria_final_r3.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in {'photos_in_pptx', 'images_in_pptx'}}, ensure_ascii=False, indent=2))
    return int(bool(errors or fonts or changed))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('final', type=Path)
    parser.add_argument('cycles', type=Path)
    args = parser.parse_args()
    raise SystemExit(audit(args.final, args.cycles))

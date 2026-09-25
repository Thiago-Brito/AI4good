"""Verifica os nomes das classes; não muda os dados nem os modelos treinados.

O Planetoid fornece categorias numéricas. O arquivo original do Cora fornece
nomes. Ligamos os dois comparando os mesmos 1.433 indicadores de palavras.
Não usamos a ordem alfabética nem uma tabela de códigos encontrada na internet.
"""
import hashlib
import json
import tarfile
import numpy as np
import torch
from data import OUTPUTS


def main():
    folder = OUTPUTS / 'dataset'
    archive = folder / 'cora-original.tgz'
    # Somente leitura de um membro; não extraímos caminhos de dentro do arquivo.
    with tarfile.open(archive) as source:
        content = source.extractfile('cora/cora.content').read()
    lookup = {}
    for line in content.decode().splitlines():
        fields = line.split()
        features = np.array(fields[1:-1], dtype=np.uint8).tobytes()
        lookup.setdefault(features, set()).add(fields[-1])
    data = torch.load(folder / 'data.pt', weights_only=True)
    observations = {code: set() for code in range(7)}
    for vector, code in zip(data['x'].numpy(), data['y'].numpy()):
        # As features foram normalizadas por documento no treino. A comparação
        # binária recupera quais palavras estavam presentes antes da normalização.
        matches = lookup[(vector > 0).astype(np.uint8).tobytes()]
        assert len(matches) == 1, 'Atributos não identificam uma categoria única.'
        observations[int(code)].update(matches)
    assert all(len(names) == 1 for names in observations.values())
    mapping = {code: next(iter(names)) for code, names in observations.items()}
    assert len(set(mapping.values())) == 7
    result = {'source_url': 'https://linqs-data.soe.ucsc.edu/public/lbc/cora.tgz',
              'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'content_sha256': hashlib.sha256(content).hexdigest(),
              'verified_nodes': len(data['y']), 'ambiguous_feature_rows': 0,
              'matching': 'Exact binary feature equality; all 2708 rows identify a unique source category; all seven numeric classes have a unique name.',
              'class_names': mapping}
    (folder / 'class-label-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

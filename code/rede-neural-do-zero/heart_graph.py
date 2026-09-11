"""Snapshots reais do grafo para a animacao Canvas no navegador."""
import json
from pathlib import Path

from heart_mlp import FEATURES


def snapshot(model, sample, epoch):
    activations, _ = model.forward(sample.reshape(1, -1))
    return {'epoch': int(epoch), 'values': [float(activations[i][0]) for i in range(len(model.nodes))],
            'weights': [e.weight for e in model.edges], 'changes': [e.change for e in model.edges]}


def graph_html(model, frames, training=True, seconds=.65, hide_inactive=True, animate=True):
    if not frames:
        raise ValueError('A animacao precisa de ao menos um snapshot.')
    payload = {'layers': model.layers, 'edges': [[e.source, e.target] for e in model.edges],
               'features': FEATURES, 'frames': frames, 'training': training,
               'seconds': seconds, 'hideInactive': hide_inactive, 'animate': animate}
    template = Path(__file__).with_name('heart_graph.html').read_text(encoding='utf-8')
    return template.replace('__GRAPH_DATA__', json.dumps(payload, allow_nan=False).replace('<', '\\u003c'))

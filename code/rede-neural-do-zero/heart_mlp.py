"""MLP cujo estado e calculos pertencem aos nos e arestas de um DAG."""
from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import hashlib
import json

import numpy as np

ROOT = Path(__file__).resolve().parent
FEATURES = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg',
            'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal']


@dataclass
class Node:
    layer: int
    index: int
    bias: float = 0.0
    grad: float = 0.0


@dataclass
class Edge:
    source: int
    target: int
    weight: float
    grad: float = 0.0
    change: float = 0.0


class GraphMLP:
    def __init__(self, sizes, seed=42):
        if len(sizes) < 3 or sizes[-1] != 1 or any(n < 1 for n in sizes):
            raise ValueError('Use entrada, ao menos uma camada oculta e uma saida.')
        self.nodes, self.edges, self.layers = [], [], []
        self.incoming, self.outgoing = {}, {}
        self._adam_m, self._adam_v, self._step = None, None, 0
        rng = np.random.default_rng(seed)
        for layer, size in enumerate(sizes):
            ids = []
            for index in range(size):
                node_id = len(self.nodes)
                ids.append(node_id)
                self.nodes.append(Node(layer, index))
                self.incoming[node_id], self.outgoing[node_id] = [], []
            self.layers.append(ids)
        for sources, targets in zip(self.layers[:-1], self.layers[1:]):
            limit = np.sqrt(6 / (len(sources) + len(targets)))
            for source in sources:
                for target in targets:
                    edge = Edge(source, target, float(rng.uniform(-limit, limit)))
                    self.edges.append(edge)
                    self.incoming[target].append(edge)
                    self.outgoing[source].append(edge)

    def forward(self, x):
        x = np.asarray(x, dtype=float)
        if x.ndim != 2 or x.shape[1] != len(self.layers[0]):
            raise ValueError('Formato de entrada incompativel com o grafo.')
        activations = {i: x[:, j] for j, i in enumerate(self.layers[0])}
        logits = None
        # As camadas constituem uma ordenacao topologica do grafo.
        for layer in self.layers[1:]:
            for i in layer:
                z = np.full(len(x), self.nodes[i].bias)
                for edge in self.incoming[i]:
                    z += activations[edge.source] * edge.weight
                if i in self.layers[-1]:
                    logits = z
                    activations[i] = np.exp(-np.logaddexp(0, -z))
                else:
                    activations[i] = np.tanh(z)
        return activations, logits

    def predict(self, x):
        return self.forward(x)[0][self.layers[-1][0]].reshape(-1, 1)

    def metrics(self, x, y):
        activations, logits = self.forward(x)
        p = activations[self.layers[-1][0]]
        y = np.asarray(y).ravel()
        return {'loss': float(np.mean(np.logaddexp(0, logits) - y * logits)),
                'accuracy': float(np.mean((p >= .5) == y))}

    def backward(self, x, y):
        activations, _ = self.forward(x)
        output = self.layers[-1][0]
        delta = {output: (activations[output] - np.asarray(y).ravel()) / len(x)}
        # Percurso topologico reverso; nenhum parametro muda durante o calculo.
        for layer in reversed(self.layers[1:]):
            for i in layer:
                if i != output:
                    propagated = sum(e.weight * delta[e.target] for e in self.outgoing[i])
                    delta[i] = propagated * (1 - activations[i] ** 2)
                self.nodes[i].grad = float(delta[i].sum())
                for edge in self.incoming[i]:
                    edge.grad = float(np.sum(activations[edge.source] * delta[i]))

    def train_step(self, x, y, rate, optimizer='sgd', l2=0.0):
        if optimizer not in ('sgd', 'adam') or rate <= 0 or l2 < 0:
            raise ValueError('Otimizador, taxa ou regularizacao invalidos.')
        self.backward(x, y)
        # Objetivo: BCE + (l2 / 2) * soma(w**2); biases nao sao penalizados.
        for edge in self.edges:
            edge.grad += l2 * edge.weight
        bias_nodes = [self.nodes[i] for layer in self.layers[1:] for i in layer]
        gradients = np.array([e.grad for e in self.edges] + [n.grad for n in bias_nodes])
        if optimizer == 'adam':
            if self._adam_m is None:
                self._adam_m = np.zeros_like(gradients)
                self._adam_v = np.zeros_like(gradients)
            self._step += 1
            self._adam_m = .9 * self._adam_m + .1 * gradients
            self._adam_v = .999 * self._adam_v + .001 * gradients ** 2
            m = self._adam_m / (1 - .9 ** self._step)
            v = self._adam_v / (1 - .999 ** self._step)
            changes = -rate * m / (np.sqrt(v) + 1e-8)
        else:
            changes = -rate * gradients
        for edge, change in zip(self.edges, changes):
            edge.change = float(change)
            edge.weight += edge.change
        for node, change in zip(bias_nodes, changes[len(self.edges):]):
            node.bias += float(change)


def download_dataset():
    destination = ROOT / 'outputs' / 'dataset'
    if (destination / 'heart.csv').is_file():
        return destination / 'heart.csv'
    import kagglehub
    path = Path(kagglehub.dataset_download(
        'johnsmith88/heart-disease-dataset', output_dir=str(destination)))
    matches = list(path.rglob('heart.csv'))
    if not matches:
        raise ValueError('O download nao contem heart.csv.')
    return matches[0]


def prepare_data(path, seed=42):
    with open(path, encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not set(FEATURES + ['target']).issubset(reader.fieldnames or []):
            raise ValueError('CSV deve conter as 13 caracteristicas e target.')
        rows = np.array([[float(row[k]) for k in FEATURES + ['target']] for row in reader])
    if rows.ndim != 2 or len(rows) < 10 or not np.isfinite(rows).all():
        raise ValueError('CSV vazio, pequeno demais ou com valores ausentes/invalidos.')
    if set(rows[:, -1]) != {0., 1.}:
        raise ValueError('target deve conter as classes 0 e 1.')
    original_count = len(rows)
    # Duplicatas exatas nao podem reaparecer como exemplos de teste.
    _, unique_indices = np.unique(rows, axis=0, return_index=True)
    rows = rows[np.sort(unique_indices)]
    rng = np.random.default_rng(seed)
    total_test = int(np.ceil(.2 * len(rows)))
    counts = np.bincount(rows[:, -1].astype(int), minlength=2)
    if min(counts) < 2:
        raise ValueError('Cada classe precisa de pelo menos duas amostras unicas.')
    first_test = int(np.clip(round(total_test * counts[0] / len(rows)),
                             max(1, total_test - counts[1] + 1), min(counts[0] - 1, total_test - 1)))
    train_ids, test_ids = [], []
    for cls, n_test in enumerate([first_test, total_test - first_test]):
        ids = rng.permutation(np.flatnonzero(rows[:, -1] == cls))
        test_ids.extend(ids[:n_test])
        train_ids.extend(ids[n_test:])
    train_ids, test_ids = rng.permutation(train_ids), rng.permutation(test_ids)
    train, test = rows[train_ids], rows[test_ids]
    mean, scale = train[:, :-1].mean(axis=0), train[:, :-1].std(axis=0)
    scale[scale == 0] = 1
    return {'x_train': (train[:, :-1] - mean) / scale, 'y_train': train[:, -1:],
            'x_test': (test[:, :-1] - mean) / scale, 'y_test': test[:, -1:],
            'raw_train': train[:, :-1], 'raw_test': test[:, :-1], 'mean': mean, 'scale': scale,
            'train_ids': train_ids, 'test_ids': test_ids,
            'original_count': original_count, 'unique_count': len(rows),
            'duplicates_removed': original_count - len(rows),
            'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def validation_split(raw_train, y_train, seed):
    """Reserva interna; ajuste da escala exclui validacao e teste externo."""
    rng = np.random.default_rng(seed)
    fit, validation = [], []
    for cls in (0, 1):
        ids = rng.permutation(np.flatnonzero(y_train.ravel() == cls))
        if len(ids) < 2:
            raise ValueError('A busca precisa de ao menos duas amostras de treino por classe.')
        count = min(len(ids) - 1, max(1, int(np.ceil(.2 * len(ids)))))
        validation.extend(ids[:count])
        fit.extend(ids[count:])
    fit, validation = np.array(fit), np.array(validation)
    mean, scale = raw_train[fit].mean(axis=0), raw_train[fit].std(axis=0)
    scale[scale == 0] = 1
    return fit, validation, (raw_train - mean) / scale


def select_config(raw_train, y_train, seed=42, max_epochs=500, callback=None):
    """Escolhe configuracao e epoca pela menor BCE de validacao, sem receber teste."""
    if max_epochs < 1:
        raise ValueError('max_epochs deve ser positivo.')
    fit, validation, x = validation_split(raw_train, y_train, seed)
    candidates = [
        {'sizes': [13, 8, 4, 1], 'optimizer': 'sgd', 'rate': .1, 'l2': 0.0},
        {'sizes': [13, 8, 4, 1], 'optimizer': 'adam', 'rate': .01, 'l2': .001},
        {'sizes': [13, 8, 4, 1], 'optimizer': 'adam', 'rate': .003, 'l2': .01},
        {'sizes': [13, 16, 8, 1], 'optimizer': 'adam', 'rate': .003, 'l2': .01},
    ]
    results = []
    for number, config in enumerate(candidates, 1):
        model = GraphMLP(config['sizes'], seed)
        best, stale = None, 0
        for epoch in range(1, max_epochs + 1):
            model.train_step(x[fit], y_train[fit], config['rate'], config['optimizer'], config['l2'])
            metrics = model.metrics(x[validation], y_train[validation])
            if best is None or metrics['loss'] < best['validation_loss'] - 1e-6:
                best = dict(config, epochs=epoch, validation_loss=metrics['loss'],
                            validation_accuracy=metrics['accuracy'])
                stale = 0
            else:
                stale += 1
            if callback and (epoch == 1 or epoch % 25 == 0):
                callback(number, len(candidates), epoch)
            if stale >= 60:
                break
        results.append(best)
    selected = min(results, key=lambda item: item['validation_loss'])
    audit = {'criterion': 'minimum validation BCE; patience=60', 'candidates': results,
             'fit_indices_within_train': fit.tolist(), 'validation_indices_within_train': validation.tolist()}
    return dict(selected), audit


def export_run(model, data, history, config):
    from dataclasses import asdict
    from datetime import datetime, timezone
    directory = ROOT / 'outputs' / datetime.now(timezone.utc).strftime('heart-%Y%m%d-%H%M%S-%f')
    directory.mkdir(parents=True)
    predictions = model.predict(data['x_test']).ravel()
    truth = data['y_test'].astype(int).ravel()
    confusion = np.zeros((2, 2), dtype=int)
    np.add.at(confusion, (truth, (predictions >= .5).astype(int)), 1)
    report = {'config': config, 'source': 'johnsmith88/heart-disease-dataset',
              'sha256': data['sha256'], 'original_count': data['original_count'],
              'duplicates_removed': data['duplicates_removed'],
              'train_count': len(data['x_train']), 'test_count': len(truth),
              'test': model.metrics(data['x_test'], data['y_test']),
              'confusion_true_rows_predicted_columns': confusion.tolist(),
              'history': history, 'train_ids': data['train_ids'].tolist(),
              'test_ids': data['test_ids'].tolist()}
    (directory / 'metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    state = {'features': FEATURES, 'layers': model.layers,
             'nodes': [asdict(n) for n in model.nodes], 'edges': [asdict(e) for e in model.edges],
             'mean': data['mean'].tolist(), 'scale': data['scale'].tolist()}
    (directory / 'model.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
    np.savetxt(directory / 'predictions.csv', np.c_[data['test_ids'], truth, predictions, predictions >= .5],
               delimiter=',', header='row_id,target,probability,prediction', comments='')
    return directory, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', type=Path)
    parser.add_argument('--epochs', type=int, default=500)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--tune', action='store_true', help='Selecionar parametros pela validacao interna')
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error('--epochs deve ser positivo')
    data = prepare_data(args.csv or download_dataset(), args.seed)
    config = {'sizes': [13, 8, 4, 1], 'rate': .1, 'optimizer': 'sgd', 'l2': 0., 'epochs': args.epochs}
    audit = None
    if args.tune:
        config, audit = select_config(data['raw_train'], data['y_train'], args.seed, args.epochs)
    model = GraphMLP(config['sizes'], args.seed)
    history = []
    for epoch in range(1, config['epochs'] + 1):
        model.train_step(data['x_train'], data['y_train'], config['rate'], config['optimizer'], config['l2'])
        history.append({'epoch': epoch, **model.metrics(data['x_train'], data['y_train'])})
    directory, report = export_run(model, data, history,
                                   dict(config, seed=args.seed, selection=audit))
    print(json.dumps({k: v for k, v in report.items() if k not in ('history', 'train_ids', 'test_ids')}, indent=2))
    print(directory)

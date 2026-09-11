"""Gera figuras e tabelas do artigo a partir dos artefatos reais registrados."""
from pathlib import Path
import json
import subprocess
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

from heart_mlp import FEATURES, GraphMLP, ROOT, prepare_data

PAPER = ROOT.parents[1] / 'academy' / 'papers' / 'artigo-overleaf'
OUT = PAPER / 'outputs' / 'heart-report'
RUNS = ['heart-20260911-204447-117664', 'heart-20260911-204939-879247']


def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=220, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)


def restore(run):
    state = json.loads((ROOT / 'outputs' / run / 'model.json').read_text())
    model = GraphMLP([len(layer) for layer in state['layers']], 42)
    for node, saved in zip(model.nodes, state['nodes']):
        node.bias = saved['bias']
    for edge, saved in zip(model.edges, state['edges']):
        edge.weight = saved['weight']
    return model


def classification_metrics(run):
    a = np.loadtxt(ROOT / 'outputs' / run / 'predictions.csv', delimiter=',', skiprows=1)
    y, p = a[:, 1].astype(int), a[:, 2]
    predicted = p >= .5
    tn = int(np.sum((y == 0) & ~predicted)); fp = int(np.sum((y == 0) & predicted))
    fn = int(np.sum((y == 1) & ~predicted)); tp = int(np.sum((y == 1) & predicted))
    pos, neg = p[y == 1], p[y == 0]
    # AUC = probabilidade de ordenar um positivo acima de um negativo; empate vale 1/2.
    auc = np.mean((pos[:, None] > neg).astype(float) + .5 * (pos[:, None] == neg))
    return {'accuracy': (tp + tn) / len(y), 'precision': tp / (tp + fp),
            'recall': tp / (tp + fn), 'specificity': tn / (tn + fp),
            'f1': 2 * tp / (2 * tp + fp + fn), 'auc': float(auc),
            'confusion': [[tn, fp], [fn, tp]]}


def network(ax, model, sample, scale, title):
    values, _ = model.forward(sample.reshape(1, -1))
    positions = {i: (layer, (j + .5) / len(ids))
                 for layer, ids in enumerate(model.layers) for j, i in enumerate(ids)}
    for edge in model.edges:
        a, b = positions[edge.source], positions[edge.target]
        ax.plot([a[0], b[0]], [a[1], b[1]], color='#237ace' if edge.weight >= 0 else '#dc5264',
                lw=.2 + 1.8 * abs(edge.weight) / scale, alpha=.45, zorder=1)
    for i, (x, y) in positions.items():
        value = float(values[i][0])
        ax.scatter(x, y, s=280, c=[value], cmap='coolwarm', vmin=-1, vmax=1,
                   edgecolors='#34435b', linewidths=.8, zorder=3)
        ax.text(x, y, f'{value:.2f}', ha='center', va='center', fontsize=5.7, zorder=4)
        if x == 0:
            ax.text(x - .14, y, FEATURES[model.nodes[i].index], ha='right', va='center', fontsize=6.5)
    ax.set_title(title, fontsize=11, loc='left', pad=18, fontweight='bold')
    ax.set_xlim(-.6, len(model.layers) - .7); ax.set_ylim(-.08, 1.08)
    ax.set_xticks(range(len(model.layers)), ['Entrada', 'Oculta 1', 'Oculta 2', 'Saída'], fontsize=8)
    ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)


def architecture_figure():
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis('off')
    def box(x, y, width, height, text, color='#eef5ff'):
        ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle='round,pad=0.08',
                                   facecolor=color, edgecolor='#6f88a7', linewidth=1.2))
        ax.text(x + width / 2, y + height / 2, text, ha='center', va='center', fontsize=10)
    def arrow(a, b, label=None):
        ax.annotate('', xy=b, xytext=a, arrowprops={'arrowstyle': '-|>', 'color': '#385779', 'lw': 1.5})
        if label: ax.text((a[0]+b[0])/2, (a[1]+b[1])/2+.16, label, ha='center', fontsize=8)
    box(.2, 4.55, 2.5, 1, 'Kaggle / heart.csv\n13 atributos + target')
    box(3.6, 4.55, 4.4, 1, 'heart_mlp.py\nLimpeza → divisão → padronização')
    box(8.8, 4.55, 2.8, 1, 'Treino 80%\nTeste 20% reservado')
    box(3.6, 2.45, 4.4, 1.2, 'GraphMLP · heart_mlp.py\nNós + arestas + listas de adjacência\nForward → backward → SGD / Adam')
    box(.2, 2.45, 2.5, 1.2, 'app_heart.py\nControles Streamlit\nSeleção por validação')
    box(8.8, 2.45, 2.8, 1.2, 'outputs/\nmodel.json / metrics.json\npredictions.csv', '#ecf8f0')
    box(3.6, .25, 4.4, 1.2, 'heart_graph.py → heart_graph.html\nSnapshots → Canvas / JavaScript\nAnimação e inferência no navegador', '#ecf8f0')
    box(.2, .25, 2.5, 1.2, 'test_heart_mlp.py\nGradientes, Adam\nDivisão e aprendizado', '#fff5e5')
    arrow((2.8, 5.05), (3.5, 5.05)); arrow((8.1, 5.05), (8.7, 5.05))
    arrow((5.8, 4.45), (5.8, 3.75)); arrow((2.8, 3.05), (3.5, 3.05))
    arrow((8.1, 3.05), (8.7, 3.05)); arrow((5.8, 2.35), (5.8, 1.55), 'pesos e ativações')
    arrow((1.45, 1.55), (1.45, 2.35)); arrow((10.2, 4.45), (10.2, 3.75))
    save(fig, 'arquitetura_modulos')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = prepare_data(ROOT / 'outputs' / 'dataset' / 'heart.csv')
    before, after = GraphMLP([13, 8, 4, 1], 42), restore(RUNS[0])
    np.testing.assert_allclose(after.predict(data['x_test']).ravel(),
                              np.loadtxt(ROOT / 'outputs' / RUNS[0] / 'predictions.csv', delimiter=',', skiprows=1)[:, 2])
    reports = [json.loads((ROOT / 'outputs' / r / 'metrics.json').read_text()) for r in RUNS]
    metrics = [dict(classification_metrics(run), loss=report['test']['loss']) for run, report in zip(RUNS, reports)]
    (OUT / 'metricas_derivadas.json').write_text(json.dumps(dict(zip(['base', 'selecionado'], metrics)), indent=2))
    lines = []
    for name, m in zip(['Base (SGD)', 'Selecionado (Adam)'], metrics):
        values = [100*m[k] for k in ('accuracy', 'precision', 'recall', 'specificity', 'f1')]
        cells = [f'{v:.2f}'.replace('.', ',') for v in values]
        cells += [f"{m['auc']:.3f}".replace('.', ','), f"{m['loss']:.4f}".replace('.', ',')]
        lines.append(name + ' & ' + ' & '.join(cells) + r' \\')
    table = [r'\begin{tabular}{lrrrrrrr}', r'\toprule',
             r'Modelo & Ac. & Pr. & Se. & Es. & F1 & AUC & BCE\\', r'\midrule',
             *lines, r'\bottomrule', r'\end{tabular}']
    (OUT / 'metricas_tabela.tex').write_text('\n'.join(table) + '\n', encoding='utf-8')
    sample = data['x_test'][0]
    scale = max(abs(e.weight) for m in (before, after) for e in m.edges)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
    for ax, model, label in zip(axes, [before, after], ['(a) Antes · época 0', '(b) Depois · época 500']):
        network(ax, model, sample, scale, label)
    fig.text(.5, .01, 'Mesma amostra de teste e mesma escala de pesos. Azul: peso positivo; vermelho: negativo.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0,.03,1,1)); save(fig, 'rede_antes_depois')
    fig = plt.figure(figsize=(12, 6.3))
    ax = fig.add_axes([.5, .08, .48, .82]); network(ax, after, sample, scale, 'Rede treinada · 13 → 8 → 4 → 1')
    fig.text(.035,.89,'THIAGO BARBOSA',fontsize=26,fontweight='bold',color='#153c63')
    fig.text(.04,.82,'Heart Disease · acurácia 0,869',fontsize=13,color='#475569')
    rows = [('accuracy (teste)', '0,8689 · 53/61 acertos'), ('learning rate', '0,1 · SGD · 500 épocas'),
            ('activation', 'tanh (ocultas) / sigmoid (saída)'), ('architecture', '13 | 8 | 4 | 1'),
            ('pre-processing', 'standardize, ajustado no treino')]
    for j, (label,value) in enumerate(rows):
        fig.text(.04,.73-j*.095,label,fontsize=12,fontweight='bold')
        fig.text(.04,.692-j*.095,value,fontsize=11)
    comment = ('MLP codificada do zero como grafo dirigido, com feed forward e\n'
               'backpropagation manuais. A corretude do backward foi verificada\n'
               'por gradient checking. Redes maiores e treinos mais longos\n'
               'aumentaram o ajuste ao treino, mas pioraram a validação; a\n'
               'configuração base obteve 86,89% no teste reservado.')
    fig.text(.04,.045,comment,fontsize=9.5,color='#475569',va='bottom')
    save(fig, 'resumo_experimento')
    architecture_figure()
    fig, axes = plt.subplots(1,2,figsize=(10,3.3))
    h = reports[0]['history']
    axes[0].plot([p['epoch'] for p in h],[p['loss'] for p in h],color='#dd5365')
    axes[1].plot([p['epoch'] for p in h],[100*p['accuracy'] for p in h],color='#237ace')
    axes[0].set_ylabel('BCE de treino'); axes[1].set_ylabel('Acurácia de treino (%)')
    for ax in axes: ax.set_xlabel('Época'); ax.grid(alpha=.2)
    fig.tight_layout(); save(fig,'curvas_treino')
    commands = [['codex', '--version'], [sys.executable, '--version'],
                [sys.executable, '-m', 'unittest', 'discover', '-p', 'test_heart_mlp.py']]
    logs = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        display = 'codex --version' if command[0] == 'codex' else ('python --version' if '--version' in command else 'python -m unittest discover -p test_heart_mlp.py')
        logs.append('$ ' + display + '\n' + result.stdout.strip() + '\n' + result.stderr.strip())
    transcript = '\n\n'.join(logs)
    (OUT / 'harness_verificacao.txt').write_text(transcript, encoding='utf-8')
    fig = plt.figure(figsize=(11,4.7),facecolor='#111c2d')
    fig.text(.04,.89,'HARNESS INSTALADO · VERIFICAÇÃO LOCAL',fontsize=17,color='#8bcfff',fontweight='bold')
    fig.text(.04,.79,transcript,fontsize=11,color='#e8f0fa',family='monospace',va='top')
    fig.text(.04,.045,'Transcrição dos comandos executados no workspace pelo agente · 11/09/2026',fontsize=10,color='#a7b6ca')
    save(fig,'harness_funcional')
    (OUT / 'proveniencia.json').write_text(json.dumps({'runs': RUNS, 'csv_sha256': data['sha256'],
        'sample_test_index': 0, 'sample_unique_row_id': int(data['test_ids'][0]),
        'sample_target': int(data['y_test'][0,0]), 'before_probability': float(before.predict(sample.reshape(1,-1))[0,0]),
        'after_probability': float(after.predict(sample.reshape(1,-1))[0,0])},indent=2), encoding='utf-8')
    print(json.dumps(metrics,indent=2)); print(OUT)


if __name__ == '__main__':
    main()

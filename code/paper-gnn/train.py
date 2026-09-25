"""Predeclared, paired experiment with evidence and checkpoint reload checks."""
import argparse
import copy
import csv
import json
import platform
import random
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from data import ROOT, OUTPUTS, load_data, record_data, sha256
from models import parameters, make_model


def scores(logits, y, mask):
    truth, pred = y[mask], logits[mask].argmax(-1)
    k = logits.shape[1]
    cm = torch.bincount(truth*k+pred, minlength=k*k).reshape(k,k)
    tp = cm.diag().float()
    f1 = (2*tp / (cm.sum(0)+cm.sum(1)).clamp_min(1)).mean()
    return {'accuracy': float((truth == pred).float().mean()), 'macro_f1': float(f1),
            'loss': float(F.cross_entropy(logits[mask], truth)), 'confusion': cm.tolist()}


def train_one(kind, seed, data, adjacency, protocol, destination):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    params = parameters(data.num_features, int(data.y.max())+1, protocol['hidden'])
    model = make_model(kind, params)
    initial = copy.deepcopy(model.state_dict())
    folder = destination / f'{kind}-seed{seed}'
    folder.mkdir(parents=True, exist_ok=False)
    torch.save({'state_dict': initial, 'params': params, 'kind': kind}, folder/'initial.pt')
    # All parameters train, including input LayerNorm omitted from the authors'
    # two-group optimizer. Common Adam/decay for both models is a declared change.
    optimizer = torch.optim.Adam(model.parameters(), lr=protocol['lr'], weight_decay=protocol['weight_decay'])
    best_loss, best_epoch, best_state, stale = float('inf'), 0, None, 0
    history = []
    started = time.perf_counter()
    for epoch in range(1, protocol['epochs']+1):
        model.train(); optimizer.zero_grad(set_to_none=True)
        logits = model(data.x, adjacency)['x']
        loss = F.cross_entropy(logits[data.train_mask], data.y[data.train_mask])
        loss.backward()
        grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), float('inf')))
        optimizer.step()
        model.eval()
        with torch.no_grad():
            logits = model(data.x, adjacency)['x']
            train = scores(logits, data.y, data.train_mask)
            val = scores(logits, data.y, data.val_mask)
        history.append({'epoch': epoch, 'train_loss': train['loss'], 'train_accuracy': train['accuracy'],
                        'val_loss': val['loss'], 'val_accuracy': val['accuracy'], 'gradient_norm': grad_norm})
        if val['loss'] < best_loss - 1e-6:
            best_loss, best_epoch, best_state, stale = val['loss'], epoch, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
        if epoch == 1 or epoch % 25 == 0:
            print(f'{kind} seed={seed} epoch={epoch} train={train["accuracy"]:.4f} val={val["accuracy"]:.4f}', flush=True)
        if stale >= protocol['patience']:
            break
    elapsed = time.perf_counter()-started
    model.load_state_dict(best_state); model.eval()
    checkpoint = {'state_dict': best_state, 'params': params, 'kind': kind, 'seed': seed,
                  'best_epoch': best_epoch, 'protocol': protocol}
    torch.save(checkpoint, folder/'model.pt')
    with torch.no_grad():
        logits = model(data.x, adjacency)['x']
        final_scores = {name: scores(logits, data.y, getattr(data, name+'_mask')) for name in ['train','val','test']}
        probabilities = logits.softmax(-1)
    restored = make_model(kind, params)
    restored.load_state_dict(torch.load(folder/'model.pt', weights_only=True)['state_dict']); restored.eval()
    before = copy.deepcopy(restored.state_dict())
    with torch.no_grad():
        reloaded = restored(data.x, adjacency)['x']
    torch.testing.assert_close(logits, reloaded, rtol=0, atol=0)
    assert all(torch.equal(v, restored.state_dict()[k]) for k,v in before.items())
    timings = []
    with torch.no_grad():
        for _ in range(12):
            start = time.perf_counter(); restored(data.x, adjacency)
            timings.append(time.perf_counter()-start)
    changes = {k: float((best_state[k]-v).norm()) for k,v in initial.items() if v.is_floating_point()}
    assert max(changes.values()) > 0
    result = {'kind': kind, 'seed': seed, 'params': params, 'best_epoch': best_epoch, 'epochs_run': epoch,
              'parameter_count': sum(p.numel() for p in model.parameters()),
              'training_seconds': elapsed, 'full_graph_inference_ms_median': float(np.median(timings[2:])*1000),
              'scores': final_scores, 'parameter_l2_changes': changes,
              'reload_max_abs_error': float((logits-reloaded).abs().max()), 'inference_preserved_parameters': True,
              'checkpoint_sha256': sha256(folder/'model.pt')}
    (folder/'metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    with (folder/'history.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=history[0]); writer.writeheader(); writer.writerows(history)
    with (folder/'predictions.csv').open('w', newline='') as f:
        writer = csv.writer(f); writer.writerow(['node_id','split','target','prediction']+[f'p_{i}' for i in range(logits.shape[1])])
        for i in range(data.num_nodes):
            split = 'train' if data.train_mask[i] else 'val' if data.val_mask[i] else 'test'
            writer.writerow([i, split, int(data.y[i]), int(logits[i].argmax()), *probabilities[i].tolist()])
    print(f'FINISHED {kind} seed={seed} test={final_scores["test"]["accuracy"]:.4f} best_epoch={best_epoch} seconds={elapsed:.1f}', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=400)
    parser.add_argument('--patience', type=int, default=70)
    parser.add_argument('--hidden', type=int, default=64)
    parser.add_argument('--seeds', type=int, nargs='+', default=[42,43,44])
    parser.add_argument('--name', default='main')
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    destination = OUTPUTS/args.name
    destination.mkdir(parents=True, exist_ok=False)
    data, adjacency = load_data()
    manifest = record_data(data)
    protocol = dict(epochs=args.epochs, patience=args.patience, hidden=args.hidden,
                    seeds=args.seeds, lr=.001, weight_decay=5e-6, threads=args.threads,
                    selection='minimum validation cross entropy; test after selection only',
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    python=platform.python_version(), torch=str(torch.__version__), numpy=np.__version__,
                    dataset_manifest_sha256=sha256(OUTPUTS/'dataset/manifest.json'),
                    code_sha256={p.name: sha256(p) for p in ROOT.glob('*.py')})
    (destination/'protocol.json').write_text(json.dumps(protocol, indent=2), encoding='utf-8')
    print(json.dumps(manifest), flush=True)
    results = []
    for seed in args.seeds:
        for kind in ['original','modified']:
            results.append(train_one(kind, seed, data, adjacency, protocol, destination))
            (destination/'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    summary = {}
    for kind in ['original','modified']:
        runs = [r for r in results if r['kind']==kind]
        summary[kind] = {metric: {'mean': float(np.mean([r['scores']['test'][metric] for r in runs])),
                                 'std_sample': float(np.std([r['scores']['test'][metric] for r in runs], ddof=1)) if len(runs)>1 else None}
                         for metric in ['accuracy','macro_f1','loss']}
    (destination/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()

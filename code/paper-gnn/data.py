"""Cora from the same Planetoid/full loader configuration as the authors."""
from pathlib import Path
import hashlib
import json
import torch
from torch_geometric.datasets import Planetoid
from torch_geometric.transforms import NormalizeFeatures
from ordered_layer import mean_adjacency

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / 'outputs'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_data():
    dataset = Planetoid(str(OUTPUTS / 'dataset'), 'Cora', split='full', transform=NormalizeFeatures())
    data = dataset[0]
    adjacency = mean_adjacency(data.edge_index, data.num_nodes)
    masks = [data.train_mask, data.val_mask, data.test_mask]
    assert torch.stack(masks).sum(0).eq(1).all()
    return data, adjacency


def record_data(data):
    folder = OUTPUTS / 'dataset'
    manifest = {'name': 'Cora', 'loader': 'torch_geometric.datasets.Planetoid', 'split': 'full',
                'nodes': data.num_nodes, 'features': data.num_features,
                'directed_edges': data.num_edges, 'undirected_edges': data.num_edges // 2,
                'classes': int(data.y.max())+1,
                'train': int(data.train_mask.sum()), 'validation': int(data.val_mask.sum()),
                'test': int(data.test_mask.sum()),
                'raw_sha256': {str(p.relative_to(folder)): sha256(p) for p in sorted(folder.rglob('raw/*')) if p.is_file()},
                'protocol': 'Transductive: all features/edges visible; only train labels used in gradients.'}
    masks = {name: getattr(data, name+'_mask').nonzero().flatten().tolist() for name in ['train', 'val', 'test']}
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (folder/'split.json').write_text(json.dumps(masks, indent=2), encoding='utf-8')
    torch.save({'x': data.x, 'y': data.y, 'edge_index': data.edge_index, **{k+'_mask': getattr(data,k+'_mask') for k in masks}}, folder/'data.pt')
    return manifest

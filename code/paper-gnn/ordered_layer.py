"""CPU port of OrderedGNN/layer.py (MIT, Yunchong Song, 2023).

Only aggregation infrastructure changes: precomputed sparse mean instead of
torch_sparse and the old PyG MessagePassing. Gates and LayerNorm follow the
released implementation, including its left-to-right cumulative sum.
"""
import torch
from torch import nn
from torch.nn import functional as F


def mean_adjacency(edge_index, n, self_loops=False):
    src, dst = edge_index
    keep = src != dst
    src, dst = src[keep], dst[keep]
    if self_loops:
        nodes = torch.arange(n, device=src.device)
        src, dst = torch.cat([src, nodes]), torch.cat([dst, nodes])
    degree = torch.bincount(dst, minlength=n).clamp_min(1).float()
    return torch.sparse_coo_tensor(torch.stack([dst, src]), 1 / degree[dst],
                                   (n, n)).coalesce()


class ONGNNConv(nn.Module):
    def __init__(self, tm_net, tm_norm, params):
        super().__init__()
        self.params, self.tm_net, self.tm_norm = params, tm_net, tm_norm

    def forward(self, x, adjacency, last_tm_signal):
        m = torch.sparse.mm(adjacency, x)
        if self.params['tm']:
            if self.params['simple_gating']:
                gate = torch.sigmoid(self.tm_net(torch.cat((x, m), dim=1)))
            else:
                gate = F.softmax(self.tm_net(torch.cat((x, m), dim=1)), dim=-1)
                gate = torch.cumsum(gate, dim=-1)
                if self.params['diff_or']:
                    gate = last_tm_signal + (1 - last_tm_signal) * gate
            expanded = gate.repeat_interleave(self.params['hidden_channel'] // self.params['chunk_size'], dim=1)
            out = x * expanded + m * (1 - expanded)
        else:
            out, gate = m, last_tm_signal
        return self.tm_norm(out), gate

"""Released Ordered GNN model and a locally proposed architectural variant."""
import torch
from torch import nn
from torch.nn import functional as F
from original_model import GONN


def parameters(in_features=1433, classes=7, hidden=64):
    return dict(in_channel=in_features, out_channel=classes, hidden_channel=hidden,
                chunk_size=hidden // 4, num_layers=4, num_layers_input=2,
                global_gating=True, model='ONGNN', dropout_rate=.4,
                dropout_rate2=.2, tm=True, simple_gating=False, diff_or=True,
                add_self_loops=False)


class MultiScaleOrderedGNN(GONN):
    """Independent gates + residual feed-forward blocks + node-wise depth fusion.

    This is a local extension, not an architecture attributed to Song et al.
    """
    def __init__(self, params):
        params = dict(params, global_gating=False)
        super().__init__(params)
        h = params['hidden_channel']
        self.feedforward = nn.ModuleList([
            nn.Sequential(nn.Linear(h, 2*h), nn.GELU(), nn.Linear(2*h, h))
            for _ in self.convs])
        self.residual_norm = nn.ModuleList([nn.LayerNorm(h) for _ in self.convs])
        self.depth_score = nn.Sequential(nn.Linear(h, h//2), nn.Tanh(), nn.Linear(h//2, 1))

    def forward(self, x, adjacency):
        p = self.params
        for linear, norm in zip(self.linear_trans_in, self.norm_input):
            x = norm(F.relu(linear(F.dropout(x, p=p['dropout_rate'], training=self.training))))
        states = [x]
        gate = x.new_zeros(p['chunk_size'])
        signals = []
        for conv, ffn, norm in zip(self.convs, self.feedforward, self.residual_norm):
            x, gate = conv(F.dropout(x, p=p['dropout_rate2'], training=self.training), adjacency, gate)
            x = norm(x + F.dropout(ffn(x), p=p['dropout_rate2'], training=self.training))
            states.append(x)
            signals.append({'tm_signal': gate})
        stack = torch.stack(states, dim=1)
        attention = self.depth_score(stack).softmax(dim=1)
        combined = (stack * attention).sum(dim=1)
        logits = self.linear_trans_out(F.dropout(combined, p=p['dropout_rate'], training=self.training))
        return {'x': logits, 'check_signal': signals, 'depth_attention': attention.squeeze(-1)}


def make_model(kind, params):
    return GONN(params) if kind == 'original' else MultiScaleOrderedGNN(params)

import copy
import unittest
import torch
from torch import nn
from torch_geometric.utils import remove_self_loops, add_self_loops
from data import ROOT
from ordered_layer import ONGNNConv, mean_adjacency
from models import parameters, make_model


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)
        torch.manual_seed(3)
        self.params = parameters(5, 3, 8)
        self.edges = torch.tensor([[0,1,2,3,0,4,1],[1,2,1,0,0,3,1]])

    def test_released_layer_forward_and_gradients(self):
        # Execute the actual official forward, replacing only old dependency
        # plumbing with an independent index_add mean on a tiny directed graph.
        class ReferenceMessagePassing(nn.Module):
            def __init__(self, aggr):
                super().__init__()
                assert aggr == 'mean'
            def propagate(self, edge_index, x):
                src, dst = edge_index
                sums = torch.zeros_like(x).index_add(0, dst, x[src])
                degree = torch.bincount(dst, minlength=len(x)).clamp_min(1)
                return sums / degree[:, None]
        source = (ROOT/'vendor/OrderedGNN/layer.py').read_text()
        source = '\n'.join(line for line in source.splitlines() if not line.startswith(('from mp_deterministic', 'from torch_sparse')))
        namespace = {'MessagePassing': ReferenceMessagePassing, 'SparseTensor': type('UnusedSparseTensor', (), {})}
        exec(compile(source, 'official_layer.py', 'exec'), namespace)
        for loops in [False, True]:
            p = dict(self.params, add_self_loops=loops)
            reference = namespace['ONGNNConv'](nn.Linear(16,2), nn.LayerNorm(8), p)
            port = ONGNNConv(copy.deepcopy(reference.tm_net), copy.deepcopy(reference.tm_norm), p)
            x = torch.randn(6,8, requires_grad=True)
            xp = x.detach().clone().requires_grad_()
            previous = torch.rand(6,2)
            expected, eg = reference(x, self.edges, previous)
            actual, ag = port(xp, mean_adjacency(self.edges,6,loops), previous)
            torch.testing.assert_close(actual, expected, atol=1e-6, rtol=1e-5)
            torch.testing.assert_close(ag, eg, atol=1e-6, rtol=1e-5)
            weights = torch.randn_like(expected)
            (expected*weights).sum().backward(); (actual*weights).sum().backward()
            torch.testing.assert_close(x.grad, xp.grad, atol=2e-6, rtol=1e-4)
            for a,b in zip(reference.parameters(), port.parameters()):
                torch.testing.assert_close(a.grad,b.grad,atol=2e-6,rtol=1e-4)

    def test_official_model_only_import_changed(self):
        official = (ROOT/'vendor/OrderedGNN/model.py').read_text(encoding='utf-8-sig')
        local = (ROOT/'original_model.py').read_text(encoding='utf-8-sig')
        self.assertEqual(official.replace('from layer import ONGNNConv','from ordered_layer import ONGNNConv').strip(), local.strip())

    def test_variant_shape_gates_and_train_gradients(self):
        model = make_model('modified', self.params)
        x = torch.randn(6,5)
        out = model(x,mean_adjacency(self.edges,6))
        self.assertEqual(out['x'].shape,(6,3))
        torch.testing.assert_close(out['depth_attention'].sum(1),torch.ones(6))
        gates = [s['tm_signal'] for s in out['check_signal']]
        for prev,current in zip(gates,gates[1:]):
            self.assertTrue(torch.all(current >= prev-1e-6))
        out['x'].square().mean().backward()
        self.assertGreater(float(model.depth_score[0].weight.grad.norm()),0)
        self.assertGreater(float(model.feedforward[0][0].weight.grad.norm()),0)
        self.assertIsNot(model.tm_net[0],model.tm_net[1])

    def test_masked_loss_ignores_other_labels(self):
        model = make_model('original', self.params).eval()
        logits = model(torch.randn(6,5),mean_adjacency(self.edges,6))['x']
        y = torch.tensor([0,1,2,0,1,2]); mask=torch.tensor([True,True,False,False,False,False])
        changed=y.clone(); changed[~mask]=(changed[~mask]+1)%3
        loss=torch.nn.functional.cross_entropy(logits[mask],y[mask])
        other=torch.nn.functional.cross_entropy(logits[mask],changed[mask])
        self.assertEqual(float(loss.detach()),float(other.detach()))


if __name__ == '__main__':
    unittest.main()

import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from heart_mlp import FEATURES, GraphMLP, prepare_data, validation_split, select_config


class GraphTests(unittest.TestCase):
    def test_adam_updates_match_reference_and_l2_excludes_biases(self):
        model = GraphMLP([2, 2, 1], 3)
        x, y = np.array([[.2, -.4], [.7, .3]]), np.array([[0], [1]])
        bias_nodes = [model.nodes[i] for layer in model.layers[1:] for i in layer]
        m = np.zeros(len(model.edges) + len(bias_nodes))
        v = np.zeros_like(m)
        for step in range(1, 4):
            model.backward(x, y)
            old = np.array([e.weight for e in model.edges] + [n.bias for n in bias_nodes])
            gradients = np.array([e.grad + .01 * e.weight for e in model.edges] + [n.grad for n in bias_nodes])
            m = .9 * m + .1 * gradients
            v = .999 * v + .001 * gradients ** 2
            expected = old - .003 * (m / (1 - .9 ** step)) / (np.sqrt(v / (1 - .999 ** step)) + 1e-8)
            model.train_step(x, y, .003, 'adam', .01)
            actual = [e.weight for e in model.edges] + [n.bias for n in bias_nodes]
            np.testing.assert_allclose(actual, expected, atol=1e-12)

    def test_validation_is_excluded_from_scaler_and_selection_is_reproducible(self):
        rng = np.random.default_rng(7)
        raw = rng.normal(size=(40, 13))
        y = (np.arange(40) % 2).reshape(-1, 1)
        fit, validation, scaled = validation_split(raw, y, 42)
        self.assertFalse(set(fit) & set(validation))
        self.assertEqual(set(fit) | set(validation), set(range(40)))
        modified = raw.copy()
        modified[validation] += 1000
        new_fit, _, new_scaled = validation_split(modified, y, 42)
        np.testing.assert_allclose(scaled[fit], new_scaled[new_fit])
        config, audit = select_config(raw, y, 42, max_epochs=3)
        self.assertEqual(config, min(audit['candidates'], key=lambda c: c['validation_loss']))
        self.assertEqual((config, audit), select_config(raw, y, 42, max_epochs=3))

    def test_all_gradients_against_finite_differences(self):
        model = GraphMLP([2, 3, 2, 1], 7)
        x = np.array([[.1, -.4], [.5, .2], [-.3, .8]])
        y = np.array([[1], [0], [1]])
        model.backward(x, y)
        params = [(e, 'weight') for e in model.edges]
        params += [(model.nodes[i], 'bias') for layer in model.layers[1:] for i in layer]
        for parameter, attribute in params:
            original = getattr(parameter, attribute)
            setattr(parameter, attribute, original + 1e-5)
            plus = model.metrics(x, y)['loss']
            setattr(parameter, attribute, original - 1e-5)
            minus = model.metrics(x, y)['loss']
            setattr(parameter, attribute, original)
            self.assertAlmostEqual(parameter.grad, (plus - minus) / 2e-5, places=7)

    def test_xor_learning_and_inference_does_not_change_weights(self):
        model = GraphMLP([2, 4, 3, 1], 42)
        x = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]])
        y = np.array([[0], [1], [1], [0]])
        for _ in range(1000):
            model.train_step(x, y, .3)
        self.assertEqual(model.metrics(x, y)['accuracy'], 1.)
        weights = [e.weight for e in model.edges]
        model.predict(x)
        self.assertEqual(weights, [e.weight for e in model.edges])

    def test_split_deduplication_and_train_only_standardization(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'heart.csv'
            rows = [[float(i + j) for j in range(13)] + [i % 2] for i in range(30)]
            with path.open('w', newline='') as output:
                writer = csv.writer(output)
                writer.writerow(FEATURES + ['target'])
                writer.writerows(rows + rows[:5])
            data = prepare_data(path)
            self.assertEqual(data['duplicates_removed'], 5)
            self.assertEqual(len(data['x_train']), 24)
            self.assertEqual(len(data['x_test']), 6)
            self.assertFalse(set(data['train_ids']) & set(data['test_ids']))
            np.testing.assert_allclose(data['x_train'].mean(axis=0), 0, atol=1e-14)
            np.testing.assert_allclose(data['x_train'].std(axis=0), 1)
            expected_mean = np.array(rows)[data['train_ids'], :-1].mean(axis=0)
            np.testing.assert_allclose(data['mean'], expected_mean)
            np.testing.assert_array_equal(data['test_ids'], prepare_data(path)['test_ids'])


if __name__ == '__main__':
    unittest.main()

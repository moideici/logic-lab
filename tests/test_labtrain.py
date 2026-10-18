import unittest

import numpy as np
import torch

from logic_arena.labtrain import TorchMLP, build_dataset, evaluate, neuron_importance, strength, train


class LabTrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train = build_dataset("tictactoe", "train", 120, cache=False)
        cls.val = build_dataset("tictactoe", "val", 40, cache=False)

    def test_dataset_is_deterministic_and_masks_contain_the_teacher_move(self):
        a = build_dataset("nim", "train", 20, cache=False)
        b = build_dataset("nim", "train", 20, cache=False)
        for u, v in zip(a, b):
            np.testing.assert_array_equal(u, v)
        x, y, mask = a
        self.assertTrue(mask[np.arange(len(y)), y].all())
        self.assertEqual(x.shape[1], 48)

    def test_core_export_matches_torch_forward(self):
        m = TorchMLP(18, 9, 6, 5, seed=3)
        x = torch.as_tensor(self.train[0][:16])
        with torch.no_grad():
            expected = m(x).numpy()
        got = m.to_core().forward(x.numpy())
        np.testing.assert_allclose(got, expected, atol=1e-5)

    def test_grow_keeps_the_function_and_prune_equals_mute(self):
        m = TorchMLP(18, 9, 6, 6, seed=1)
        x = torch.as_tensor(self.train[0][:32])
        with torch.no_grad():
            before = m(x).clone()
        m.grow("coeur", 3)
        m.grow("encodeur", 2)
        self.assertEqual(m.sizes, (8, 9))
        with torch.no_grad():
            np.testing.assert_allclose(m(x).numpy(), before.numpy(), atol=1e-6)
            muted = m(x, mute={"encodeur": [0, 4], "coeur": [1]}).clone()
        m.prune("encodeur", [0, 4])
        m.prune("coeur", [1])
        self.assertEqual(m.sizes, (6, 8))
        with torch.no_grad():
            np.testing.assert_allclose(m(x).numpy(), muted.numpy(), atol=1e-5)
        with self.assertRaises(ValueError):
            m.prune("coeur", list(range(8)))

    def test_training_reduces_validation_loss(self):
        m = TorchMLP(18, 9, 8, 8, seed=0)
        before, _ = evaluate(m, self.val)
        r = train(m, self.train, self.val, steps=300, eval_every=100)
        after = r["historique"][-1]["val_loss"]
        self.assertLess(after, before * 0.7)
        self.assertEqual([p["step"] for p in r["historique"]], [100, 200, 300])

    def test_graine_grows_on_plateau_and_prunes_useless_neurons(self):
        m = TorchMLP(18, 9, 2, 2, seed=0)
        graine = {"grow_by": 2, "plateau": 1.0, "patience": 1, "prune_every": 200, "prune_tol": 1.0, "max": 12, "min": 2}
        r = train(m, self.train, self.val, steps=400, eval_every=100, graine=graine)
        kinds = [e["type"] for e in r["evenements"]]
        self.assertIn("croissance", kinds)
        self.assertIn("elagage", kinds)
        self.assertGreaterEqual(min(m.sizes), 2)
        self.assertLessEqual(max(m.sizes), 12 + 2)

    def test_importance_and_strength_are_well_formed(self):
        m = TorchMLP(18, 9, 4, 4)
        imp = neuron_importance(m, self.val)
        self.assertEqual((len(imp["encodeur"]), len(imp["coeur"])), (4, 4))
        s = strength(m, "tictactoe", level=2, games=4)
        self.assertTrue(0.0 <= s <= 1.0)


if __name__ == "__main__":
    unittest.main()

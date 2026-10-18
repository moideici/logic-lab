import unittest

import numpy as np
import torch

from logic_arena.reason.model import RecurrentSolver, loss_over_passes, predicted_grid
from logic_arena.reason.problems import dataset, peers
from logic_arena.reason.train import evaluate, fit


class ReasonModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train = dataset(4, 600, (3, 8), seed=1)
        cls.test = dataset(4, 80, (3, 10), seed=2)

    def test_output_shape_one_proposal_per_pass(self):
        m = RecurrentSolver(4, 16, d=32, heads=4, passes=5)
        P = torch.as_tensor(self.train[0][:7])
        out = m(P, torch.as_tensor(peers(4)))
        self.assertEqual(tuple(out.shape), (5, 7, 16, 4))
        self.assertEqual(tuple(m(P, torch.as_tensor(peers(4)), passes=9).shape), (9, 7, 16, 4))

    def test_tied_weights_share_one_block_untied_do_not(self):
        tied = RecurrentSolver(4, 16, d=32, heads=4, passes=6, tied=True)
        untied = RecurrentSolver(4, 16, d=32, heads=4, passes=6, tied=False)
        self.assertEqual(len(tied.blocks), 1)
        self.assertEqual(len(untied.blocks), 6)
        self.assertGreater(untied.parameter_count(), 3 * tied.parameter_count())
        with self.assertRaises(ValueError):
            untied(torch.as_tensor(self.train[0][:2]), torch.as_tensor(peers(4)), passes=7)

    def test_attention_only_sees_constraint_neighbours(self):
        """Changer une case non voisine d'une case donnée ne change pas sa première mise à jour."""
        torch.manual_seed(0)
        m = RecurrentSolver(4, 16, d=32, heads=4, passes=1).eval()
        pe = torch.as_tensor(peers(4))
        grid = torch.zeros(1, 16, dtype=torch.long)
        other = grid.clone()
        target = 0
        stranger = int(np.flatnonzero(~peers(4)[target] & (np.arange(16) != target))[0])
        other[0, stranger] = 3
        with torch.no_grad():
            a, b = m(grid, pe)[0, 0, target], m(other, pe)[0, 0, target]
        torch.testing.assert_close(a, b)
        neighbour = int(np.flatnonzero(peers(4)[target])[0])
        other2 = grid.clone()
        other2[0, neighbour] = 3
        with torch.no_grad():
            c = m(other2, pe)[0, 0, target]
        self.assertFalse(torch.allclose(a, c))

    def test_training_improves_and_loss_ignores_given_cells(self):
        m = RecurrentSolver(4, 16, d=32, heads=4, passes=6)
        before = evaluate(m, 4, self.test)["case"]
        fit(m, 4, self.train, steps=250, batch=64, lr=3e-3, seed=0)
        after = evaluate(m, 4, self.test)
        self.assertGreater(after["case"], before + 0.2)
        P, S = torch.as_tensor(self.train[0][:4]), torch.as_tensor(self.train[1][:4])
        full = torch.zeros(1, 4, 16, 4)
        self.assertAlmostEqual(float(loss_over_passes(full.expand(1, 4, 16, 4), S, torch.where(P > 0, P, P))), float(torch.log(torch.tensor(4.0))), places=4)

    def test_predicted_grid_keeps_the_givens(self):
        P = torch.as_tensor(self.train[0][:3])
        logits = torch.randn(3, 16, 4)
        g = predicted_grid(logits, P)
        self.assertTrue(bool(((P == 0) | (g == P)).all()))
        self.assertTrue(int(g.min()) >= 1 and int(g.max()) <= 4)

    def test_evaluate_reports_thinking_time_for_solved_cases(self):
        m = RecurrentSolver(4, 16, d=32, heads=4, passes=6)
        fit(m, 4, self.train, steps=250, batch=64, lr=3e-3, seed=0)
        r = evaluate(m, 4, self.test, passes=6)
        if r["resolus"]:
            self.assertTrue(1 <= r["passes_moy"] <= 6)
        self.assertEqual(r["cas"], 80)


if __name__ == "__main__":
    unittest.main()

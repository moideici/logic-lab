import unittest

import numpy as np
import torch

from logic_arena.zero import c4
from logic_arena.zero.mcts import BatchedMCTS
from logic_arena.zero.net import PolicyValueNet
from logic_arena.zero.rules import Connect4Rules
from logic_arena.zero.selfplay import Replay, self_play, train_steps

RULES = Connect4Rules()


def position(moves):
    pos, mask = c4.new_games(1)
    for m in moves:
        pos, mask, _ = c4.play(pos, mask, [m])
    return np.stack([pos, mask], axis=1)


def fresh_net(seed=0):
    torch.manual_seed(seed)
    return PolicyValueNet(RULES.planes_shape, RULES.n_actions, channels=16, blocks=1)


class ZeroTests(unittest.TestCase):
    def test_search_takes_an_immediate_win(self):
        s = position([0, 6, 1, 6, 2, 5])   # le joueur 1 aligne 0,1,2 en bas : la colonne 3 gagne
        visits, q = BatchedMCTS(RULES, fresh_net(), sims=60, seed=1).search(s, noise=False)
        self.assertEqual(int(visits[0].argmax()), 3)
        self.assertGreater(float(q[0, 3]), 0.9)

    def test_search_blocks_an_immediate_loss(self):
        s = position([0, 6, 1, 6, 2])      # le joueur 2 doit bloquer en 3
        visits, _ = BatchedMCTS(RULES, fresh_net(), sims=200, seed=1).search(s, noise=False)
        self.assertEqual(int(visits[0].argmax()), 3)

    def test_visit_counts_equal_the_number_of_simulations_and_respect_legality(self):
        s = position([0] * 6)              # colonne 0 pleine
        visits, _ = BatchedMCTS(RULES, fresh_net(), sims=40, seed=2).search(s, noise=True)
        self.assertEqual(int(visits[0].sum()), 40)
        self.assertEqual(int(visits[0, 0]), 0)

    def test_batched_search_matches_games_independently(self):
        a, b = position([0, 6, 1, 6, 2, 5]), position([0, 6, 1, 6, 2])
        visits, _ = BatchedMCTS(RULES, fresh_net(), sims=120, seed=3).search(np.concatenate([a, b]), noise=False)
        self.assertEqual(int(visits[0].argmax()), 3)
        self.assertEqual(int(visits[1].argmax()), 3)

    def test_self_play_produces_consistent_training_targets(self):
        X, PI, Z, stats = self_play(RULES, fresh_net(), "cpu", games=6, sims=12, seed=4)
        self.assertEqual(X.shape[1:], RULES.planes_shape)
        self.assertEqual(len(X), len(PI), len(Z))
        self.assertTrue(np.allclose(PI.sum(1), 1.0, atol=1e-5))
        self.assertTrue(set(np.unique(Z)) <= {-1.0, 0.0, 1.0})
        self.assertEqual(stats["parties"], 6)

    def test_training_reduces_the_loss_on_a_small_buffer(self):
        net = fresh_net()
        X, PI, Z, _ = self_play(RULES, net, "cpu", games=8, sims=12, seed=5)
        replay = Replay(10000)
        replay.add(list(X), list(PI), list(Z))
        opt = torch.optim.Adam(net.parameters(), lr=3e-3)
        rng = np.random.default_rng(0)
        first = train_steps(net, opt, replay, RULES, "cpu", 5, 32, rng)
        later = train_steps(net, opt, replay, RULES, "cpu", 60, 32, rng)
        self.assertLess(later.sum(), first.sum())


if __name__ == "__main__":
    unittest.main()

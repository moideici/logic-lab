import unittest

import numpy as np

from logic_arena.core import Dense, Net, from_garry, encode_observation
from logic_arena.games import make_game
from logic_arena.general import GarryPolicy, GAMES, OUTPUT_OFFSETS
from logic_arena.neural import SPECS, MODEL_DIR


def sample_observations(per_game=6, seed=7):
    """Positions réelles : quelques coups aléatoires légaux dans chacun des jeux."""
    rng = np.random.default_rng(seed)
    out = []
    for name in GAMES:
        env = make_game(name, 12)
        for step in range(per_game):
            obs = env.observation()
            if obs["done"]:
                break
            out.append(obs)
            legal = env.legal_actions()
            env.step(legal[int(rng.integers(len(legal)))])
    return out


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = GarryPolicy.load(MODEL_DIR / "garry.json")
        cls.net = from_garry(cls.policy)
        cls.obs = sample_observations()

    def test_shape_matches_garry_0_6_0(self):
        self.assertEqual(self.net.shape, [4872, 48, 48, 4259])
        # 444 979 paramètres annoncés = 444 947 du réseau + 32 de la tête de position (Puissance 4), hors Core.
        self.assertEqual(self.net.parameter_count() + 32, 444979)
        self.assertEqual(self.net.parameter_count(), 4872 * 48 + 48 + 48 * 48 + 48 + 48 * 4259 + 4259)

    def test_parity_with_garry_policy_on_all_14_games(self):
        seen = set()
        for obs in self.obs:
            expected = self.policy.logits(obs)
            got = self.net.forward(encode_observation(obs))
            np.testing.assert_array_equal(got, expected, err_msg=obs["game"])
            seen.add(obs["game"])
        self.assertEqual(seen, set(GAMES))

    def test_trace_exposes_every_layer_without_changing_the_output(self):
        obs = self.obs[0]
        x = encode_observation(obs)
        trace = {}
        out = self.net.forward(x, trace)
        self.assertEqual(set(trace), {"encodeur", "coeur", "sortie"})
        self.assertEqual(trace["encodeur"].shape, (48,))
        np.testing.assert_array_equal(out, self.net.forward(x))
        self.assertTrue(np.all(np.abs(trace["encodeur"]) <= 1))

    def test_muting_changes_output_and_is_reversible(self):
        net = self.net.copy()
        x = encode_observation(self.obs[3])
        base = net.forward(x)
        trace = {}
        net.forward(x, trace)
        strongest = int(np.argmax(np.abs(trace["coeur"])))
        net.mute("coeur", [strongest])
        self.assertFalse(np.array_equal(net.forward(x), base))
        net.unmute_all()
        np.testing.assert_array_equal(net.forward(x), base)
        with self.assertRaises(ValueError):
            net.mute("sortie", [0])
        with self.assertRaises(ValueError):
            net.mute("coeur", [48])

    def test_pruning_equals_muting_but_makes_the_network_smaller(self):
        muted, pruned = self.net.copy(), self.net.copy()
        for layer, drop in (("encodeur", [0, 5, 17]), ("coeur", [2, 40])):
            muted.mute(layer, drop)
            pruned.prune(layer, drop)
        self.assertEqual(pruned.shape, [4872, 45, 46, 4259])
        self.assertLess(pruned.parameter_count(), self.net.parameter_count())
        for obs in self.obs[::3]:
            x = encode_observation(obs)
            np.testing.assert_allclose(pruned.forward(x), muted.forward(x), atol=1e-5)

    def test_growing_adds_neurons_without_changing_the_output(self):
        net = self.net.copy()
        new = net.grow("coeur", 4)
        self.assertEqual(new, [48, 49, 50, 51])
        self.assertEqual(net.shape, [4872, 48, 52, 4259])
        x = encode_observation(self.obs[10])
        np.testing.assert_allclose(net.forward(x), self.net.forward(x), atol=1e-6)

    def test_pruning_cannot_empty_or_touch_the_output_layer(self):
        net = self.net.copy()
        with self.assertRaises(ValueError):
            net.prune("encodeur", list(range(48)))
        with self.assertRaises(ValueError):
            net.prune("sortie", [0])

    def test_weight_change_between_versions(self):
        other = self.net.copy()
        other.layer("coeur").w[:, 7] += 0.5
        change = self.net.weight_change(other)
        self.assertGreater(change["coeur"][7], 0.5 * np.sqrt(48) - 1e-3)
        self.assertEqual(int(np.count_nonzero(change["coeur"])), 1)
        self.assertEqual(float(change["encodeur"].sum()), 0.0)
        with self.assertRaises(ValueError):
            self.net.weight_change(Net([Dense('a', np.zeros((3, 2), np.float32), np.zeros(2, np.float32))]))

    def test_each_game_reads_only_its_own_output_zone(self):
        obs = next(o for o in self.obs if o["game"] == "go")
        out = self.net.forward(encode_observation(obs))
        start = OUTPUT_OFFSETS["go"]
        self.assertEqual(out.shape[0], 4259)
        self.assertEqual(SPECS["go"][1] > 0, True)
        self.assertTrue(np.isfinite(out[start:start + SPECS["go"][1]]).all())


if __name__ == "__main__":
    unittest.main()

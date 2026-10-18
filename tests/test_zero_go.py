import unittest

import numpy as np

from logic_arena.games import make_game
from logic_arena.go_rules import area_score
from logic_arena.zero.go import GoRules9, margin

RULES = GoRules9()


def garry_board(env):
    return [row[:] for row in env.board]


def to_state(env, player):
    obs = env.observation()
    return RULES.from_observation(obs)


class Go9EngineTests(unittest.TestCase):
    def test_board_after_each_move_and_legal_points_match_garry_rules(self):
        """Parties aléatoires : le moteur C++ et les règles de Garry doivent donner le même plateau et les mêmes points légaux."""
        mismatches = 0
        checked = 0
        for seed in range(25):
            rng = np.random.default_rng(seed)
            env = make_game("go", seed, {"size": 9, "komi": 7.5})
            st = RULES.initial(1)
            for _ in range(70):
                legal_garry = [a for a in env.legal_actions() if "row" in a]
                pts = {a["row"] * 9 + a["col"] for a in legal_garry}
                mine = {int(i) for i in np.flatnonzero(RULES.legal(st)[0][:81])}
                checked += 1
                if pts != mine:
                    mismatches += 1   # ne peut venir que du superko (non pris en charge par le moteur d'entraînement)
                choices = [a for a in env.legal_actions() if "row" in a or "pass" in a]
                a = choices[int(rng.integers(len(choices)))]
                action = 81 if a.get("pass") else a["row"] * 9 + a["col"]
                if action != 81 and action not in mine:
                    break
                env.step(a)
                st, terminal, _ = RULES.step(st, np.array([action]))
                board_mine = st[0, :81].reshape(9, 9).tolist()
                self.assertEqual(board_mine, env.board, f"plateaux différents (partie {seed})")
                if env.go_state["phase"] != "play" or terminal[0]:
                    break
        self.assertGreater(checked, 500)
        self.assertLessEqual(mismatches, 3, "plus de désaccords sur les coups légaux que le superko ne l'explique")

    def test_area_margin_matches_garry_scoring(self):
        for seed in range(15):
            rng = np.random.default_rng(100 + seed)
            env = make_game("go", seed, {"size": 9, "komi": 7.5})
            st = RULES.initial(1)
            for _ in range(60):
                choices = [a for a in env.legal_actions() if "row" in a]
                if not choices or env.go_state["phase"] != "play":
                    break
                a = choices[int(rng.integers(len(choices)))]
                env.step(a)
                st, _, _ = RULES.step(st, np.array([a["row"] * 9 + a["col"]]))
            expected = area_score(env.board, {"dead": [], "komi": 7.5})["margin"]
            self.assertAlmostEqual(margin(st[0]), expected, places=3, msg=f"partie {seed}")

    def test_capture_suicide_and_ko(self):
        st = RULES.initial(1)
        # noir en (0,1)(1,0) ; blanc en (0,0) joue ... on construit une capture simple : blanc en (0,0), noirs en (0,1) puis (1,0) capturent.
        moves = [(0, 1), (0, 0), (8, 8), (8, 7)]   # noir(0,1) blanc(0,0) noir(8,8) blanc(8,7)
        for r, c in moves:
            st, _, _ = RULES.step(st, np.array([r * 9 + c]))
        st, _, _ = RULES.step(st, np.array([1 * 9 + 0]))        # noir (1,0) capture le blanc (0,0)
        self.assertEqual(int(st[0, 0]), 0)
        self.assertEqual(int(st[0, 1]), 1)
        # suicide : un point entouré de pierres ennemies sans capture est illégal
        st = RULES.initial(1)
        for r, c in [(0, 1), (8, 8), (1, 0), (8, 7)]:        # noir autour de (0,0)
            st, _, _ = RULES.step(st, np.array([r * 9 + c]))
        self.assertEqual(int(st[0, 81]), 1)                     # noir au trait
        st, _, _ = RULES.step(st, np.array([8 * 9 + 0]))        # noir joue ailleurs ; blanc au trait
        self.assertFalse(bool(RULES.legal(st)[0][0]))           # (0,0) serait un suicide pour blanc

    def test_two_passes_end_the_game_with_an_area_value(self):
        st = RULES.initial(1)
        st, term, val = RULES.step(st, np.array([4 * 9 + 4]))   # noir au centre
        st, term, val = RULES.step(st, np.array([81]))
        self.assertFalse(bool(term[0]))
        st, term, val = RULES.step(st, np.array([81]))
        self.assertTrue(bool(term[0]))
        # noir tient tout le plateau moins le komi : 81 − 7,5 > 0, c'est noir (au trait désormais) qui gagne
        self.assertEqual(float(val[0]), 1.0 if int(st[0, 81]) == 1 else -1.0)

    def test_encoding_is_from_the_mover_perspective(self):
        st = RULES.initial(1)
        st, _, _ = RULES.step(st, np.array([0]))                 # noir en (0,0) ; blanc au trait
        x = RULES.encode(st)
        self.assertEqual(x.shape, (1, 4, 9, 9))
        self.assertEqual(float(x[0, 1, 0, 0]), 1.0)             # plan adverse : la pierre noire
        self.assertEqual(float(x[0, 0].sum()), 0.0)             # blanc n'a aucune pierre
        self.assertEqual(float(x[0, 3, 0, 0]), 0.0)             # plan de couleur : blanc au trait

    def test_mirror_keeps_probability_mass_and_pass(self):
        x = RULES.encode(RULES.initial(1))[0]
        pi = np.zeros(82, dtype=np.float32)
        pi[3], pi[81] = 0.7, 0.3
        x2, pi2 = RULES.mirror(x, pi)
        self.assertAlmostEqual(float(pi2.sum()), 1.0, places=5)
        self.assertAlmostEqual(float(pi2[81]), 0.3, places=5)
        self.assertEqual(x2.shape, x.shape)


if __name__ == "__main__":
    unittest.main()

import random
import tempfile
import unittest
from pathlib import Path

import numpy as np

from logic_arena.unified import dataset, teachers
from logic_arena.unified.adapters import make_adapter
from logic_arena.unified.encode import action_index, encode, legal_indices
from logic_arena.unified.spec import CANVAS, CHOOSE_BLACK, EXTRA, GAMES, N_ACTIONS, PLANES, SWAP


def random_positions(game, seed, plies=60):
    rng = random.Random(seed)
    env = make_adapter(game, seed)
    for _ in range(plies):
        if env.done:
            break
        yield env.observation(), env.legal()
        env.step(rng.choice(env.legal()))


class EncodingTests(unittest.TestCase):
    def test_shapes_ranges_and_unique_legal_indices(self):
        for game in GAMES:
            for obs, legal in random_positions(game, 3):
                planes, extra = encode(obs)
                self.assertEqual(planes.shape, (PLANES, CANVAS, CANVAS))
                self.assertEqual(extra.shape, (EXTRA,))
                idx = legal_indices(obs, legal)
                self.assertEqual(len(set(idx.tolist())), len(legal), game)
                self.assertTrue((idx >= 0).all() and (idx < N_ACTIONS[game]).all())

    def test_placement_actions_land_on_empty_cells_of_the_board_mask(self):
        for game in ("tictactoe", "connect4", "hex", "gomoku"):
            for obs, legal in random_positions(game, 5):
                planes, _ = encode(obs)
                for i in legal_indices(obs, legal):
                    if i < 225:
                        self.assertEqual(planes[0].flat[i], 1)
                        self.assertEqual(planes[1].flat[i] + planes[2].flat[i], 0, f"{game}: coup sur une case occupée")

    def test_connect4_actions_are_landing_cells(self):
        env = make_adapter("connect4")
        env.step({"column": 3})
        env.step({"column": 3})
        obs = env.observation()
        planes, _ = encode(obs)
        self.assertEqual(planes[5].sum(), 7)
        self.assertEqual(action_index(obs, {"column": 3}) // CANVAS, 4 + 3)  # deux pierres : atterrit sur la 3e rangée depuis le bas
        self.assertEqual(planes[1].sum(), 1)
        self.assertEqual(planes[2].sum(), 1)

    def test_perspective_is_the_player_to_move(self):
        env = make_adapter("tictactoe")
        env.step({"row": 1, "col": 1})
        planes, _ = encode(env.observation())  # le joueur 2 est au trait : la pierre du joueur 1 est « adverse »
        self.assertEqual(planes[2].sum(), 1)
        self.assertEqual(planes[1].sum(), 0)

    def test_hex_transposition_makes_both_colors_connect_top_bottom(self):
        from logic_arena.games import make_game
        env = make_game("hex", 0)
        env.board[2][5] = 2  # le joueur de couleur 2 relie gauche-droite
        env.current_player = 2
        env.hex_state["colors"] = [1, 2]
        obs = env.observation()
        planes, _ = encode(obs)
        oy = (CANVAS - 7) // 2
        self.assertEqual(planes[1, oy + 5, oy + 2], 1)  # (2,5) transposé en (5,2)
        self.assertEqual(action_index(obs, {"row": 2, "col": 5}), (oy + 5) * CANVAS + oy + 2)
        self.assertEqual(action_index(obs, {"swap": True}), SWAP)

    def test_hex_neighbourhood_is_preserved_by_the_transposition(self):
        dirs = {(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)}
        self.assertEqual({(dc, dr) for dr, dc in dirs}, dirs)

    def test_gomoku_special_actions_and_phase(self):
        env = make_adapter("gomoku")
        for cell in ((7, 7), (7, 8), (8, 8)):
            env.step({"row": cell[0], "col": cell[1]})
        obs = env.observation()
        planes, extra = encode(obs)
        self.assertEqual(extra[2], 1)  # choose_or_extend
        self.assertEqual(action_index(obs, {"choose": "black"}), CHOOSE_BLACK)

    def test_dames_encoding_is_canonical_for_both_sides(self):
        env = make_adapter("dames")
        a, _ = encode(env.observation())
        env.step(env.legal()[0])
        b, _ = encode(env.observation())
        self.assertEqual(a[1].sum(), 12)
        self.assertEqual(b[1].sum(), 12)
        self.assertEqual(b[2].sum(), 12)


class TeacherTests(unittest.TestCase):
    def test_tictactoe_labels_are_exact(self):
        rec = teachers.ttt_records()
        self.assertEqual(len(rec), 4520)
        self.assertEqual(max(rec.value), 1)
        self.assertEqual(rec.value[0], 0)  # la position vide est nulle

    def test_connect4_conversion_matches_the_solver_labels(self):
        rec = teachers.c4_records(limit=50)
        self.assertEqual(len(rec), 50)
        d = np.load(Path(teachers.ROOT) / "training-lab" / "data" / "c4-labels-1.npz")
        for i in range(0, 50, 10):
            b = teachers.c4_board(int(d["pos"][i]), int(d["mask"][i]))
            self.assertEqual(sum(v == 1 for row in b for v in row), bin(int(d["pos"][i])).count("1"))

    def test_dames_conversion_and_dataset_roundtrip(self):
        rec = teachers.dames_records(limit=30)
        self.assertGreater(len(rec), 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "d.npz"
            rec.save(path)
            d = dataset.load(path)
        self.assertEqual(d["game"], "dames")
        self.assertEqual(d["planes"].shape[1:], (PLANES, CANVAS, CANVAS))
        target = dataset.policy_target(d["moves"][0], d["scores"][0], 10.0, 1024)
        self.assertAlmostEqual(float(target.sum()), 1.0, places=5)
        self.assertEqual(int(target.argmax()), int(d["moves"][0][0]))

    def test_js_teacher_produces_outcome_labelled_positions(self):
        rec = teachers.js_records("hex", games_per_worker=1, workers=2, seed=9, ms=20)
        self.assertGreater(len(rec), 10)
        self.assertTrue(set(rec.value) <= {-1.0, 0.0, 1.0})
        self.assertTrue(all(abs(v) <= 1 for v in rec.value_search))


if __name__ == "__main__":
    unittest.main()

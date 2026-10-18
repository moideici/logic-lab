import unittest

import numpy as np

from logic_arena.games import make_game
from logic_arena.zero import c4


def play_reference(seed):
    """Partie aléatoire jouée avec les règles de Garry ; retourne la liste des colonnes jouées, le gagnant et les plateaux."""
    rng = np.random.default_rng(seed)
    env = make_game("connect4", seed)
    cols, boards = [], []
    while not env.done:
        legal = env.legal_actions()
        a = legal[int(rng.integers(len(legal)))]
        boards.append((env.observation()["board"], env.observation()["current_player"]))
        env.step(a)
        cols.append(a["column"])
    return cols, env.winner, boards


class Connect4VectorTests(unittest.TestCase):
    def test_vectorised_engine_matches_garry_rules_on_random_games(self):
        for seed in range(60):
            cols, winner, boards = play_reference(seed)
            pos, mask = c4.new_games(1)
            for i, col in enumerate(cols):
                # positions et coups légaux identiques à ceux de Garry avant chaque coup
                board, player = boards[i]
                p2, m2 = c4.from_board(board, player)
                self.assertEqual((int(pos[0]), int(mask[0])), (int(p2), int(m2)))
                legal_ref = [c for c in range(7) if not board[0][c]]
                self.assertEqual(list(np.flatnonzero(c4.legal(mask)[0])), legal_ref)
                pos, mask, won = c4.play(pos, mask, [col])
                last = i == len(cols) - 1
                self.assertEqual(bool(won[0]), last and winner in (1, 2), (seed, i))
            if winner in (1, 2):
                self.assertTrue(c4.has_won(np.array([int(mask[0] ^ pos[0])], dtype=np.uint64))[0])

    def test_all_four_directions_and_no_wrap_around(self):
        def bits(cells):
            return np.array([sum(1 << (c * 7 + r) for c, r in cells)], dtype=np.uint64)
        self.assertTrue(c4.has_won(bits([(0, 0), (1, 0), (2, 0), (3, 0)]))[0])          # horizontale
        self.assertTrue(c4.has_won(bits([(2, 1), (2, 2), (2, 3), (2, 4)]))[0])          # verticale
        self.assertTrue(c4.has_won(bits([(0, 0), (1, 1), (2, 2), (3, 3)]))[0])          # diagonale montante
        self.assertTrue(c4.has_won(bits([(3, 0), (2, 1), (1, 2), (0, 3)]))[0])          # diagonale descendante
        self.assertFalse(c4.has_won(bits([(0, 3), (0, 4), (0, 5), (1, 0)]))[0])         # haut d'une colonne + bas de la suivante
        self.assertFalse(c4.has_won(bits([(0, 0), (1, 0), (2, 0), (4, 0)]))[0])

    def test_planes_orientation_and_perspective(self):
        pos, mask = c4.new_games(1)
        pos, mask, _ = c4.play(pos, mask, [3])      # le joueur 1 joue au centre
        x = c4.planes(pos, mask)
        self.assertEqual(x.shape, (1, 2, 6, 7))
        self.assertEqual(float(x[0, 0].sum()), 0.0)   # le joueur au trait (joueur 2) n'a rien
        self.assertEqual(float(x[0, 1, 5, 3]), 1.0)   # pierre adverse en bas (rangée 5 = bas), colonne 3

    def test_full_column_becomes_illegal(self):
        pos, mask = c4.new_games(1)
        for _ in range(6):
            pos, mask, _ = c4.play(pos, mask, [0])
        self.assertFalse(c4.legal(mask)[0, 0])
        self.assertTrue(c4.legal(mask)[0, 1:].all())


if __name__ == "__main__":
    unittest.main()

import random
import unittest

from logic_arena import t2048
from logic_arena.games import slide_2048


class T2048(unittest.TestCase):
    def test_moves_match_garry_rules(self):
        rng = random.Random(3)
        for _ in range(200):
            n = rng.randint(2, 12)
            cells = [0] * 16
            for k in rng.sample(range(16), n):
                cells[k] = rng.choice([2, 4, 8, 16, 32, 64])
            board = [cells[r * 4:r * 4 + 4] for r in range(4)]
            b = t2048.pack(board)
            for d, name in enumerate(t2048.DIRECTIONS):
                ref, _ = slide_2048(board, name)
                want = [[v.bit_length() - 1 if v else 0 for v in row] for row in ref]
                self.assertEqual(t2048.exponents([t2048.move(b, d)])[0].tolist(), want, (name, board))

    def test_teacher_plays_past_2048_without_stopping(self):
        # une grille avec une tuile 2048 reste jouable : le professeur propose un coup légal
        board = [[2048, 1024, 512, 256], [0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0]]
        b = t2048.pack(board)
        v = t2048.values([b], 2)[0]
        self.assertTrue((v > -1e29).any())
        mask = t2048.legal_masks([b])[0]
        self.assertEqual(mask & 0b1111 != 0, True)


if __name__ == "__main__":
    unittest.main()

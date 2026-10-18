import time
import unittest

import numpy as np

from logic_arena.reason.problems import count_solutions, dataset, is_valid_solution, make_puzzle, peers, random_solution, respects_givens


class ProblemTests(unittest.TestCase):
    def test_constraint_graph_sizes(self):
        self.assertTrue((peers(4).sum(1) == 7).all())
        self.assertTrue((peers(6).sum(1) == 12).all())
        self.assertTrue((peers(6) == peers(6).T).all())

    def test_random_solutions_are_valid_and_wrong_ones_rejected(self):
        rng = np.random.default_rng(1)
        for n in (4, 6):
            for _ in range(10):
                s = random_solution(n, rng)
                self.assertTrue(is_valid_solution(n, s))
        s = random_solution(4, rng)
        bad = s.copy()
        bad[0], bad[1] = bad[1], bad[0]
        self.assertFalse(is_valid_solution(4, bad) and (bad == s).all())
        self.assertFalse(is_valid_solution(4, np.zeros(16, dtype=int)))
        self.assertFalse(is_valid_solution(4, np.full(16, 5)))

    def test_generated_puzzles_have_a_unique_solution_consistent_with_the_answer(self):
        rng = np.random.default_rng(2)
        for n, empties in ((4, 8), (6, 18)):
            for _ in range(5):
                puzzle, solution, removed = make_puzzle(n, empties, rng)
                self.assertEqual(int((puzzle == 0).sum()), removed)
                self.assertEqual(count_solutions(n, puzzle), 1)
                self.assertTrue(respects_givens(puzzle, solution))
                self.assertTrue(is_valid_solution(n, solution))

    def test_solver_counts_several_solutions_on_an_empty_grid(self):
        self.assertEqual(count_solutions(4, np.zeros(16, dtype=int), limit=2), 2)

    def test_dataset_is_deterministic_and_respects_the_empty_range(self):
        a = dataset(4, 20, (4, 9), seed=5)
        b = dataset(4, 20, (4, 9), seed=5)
        for u, v in zip(a, b):
            np.testing.assert_array_equal(u, v)
        P, S, E = a
        self.assertTrue((E >= 4).all() and (E <= 9).all())
        self.assertTrue(all(respects_givens(p, s) for p, s in zip(P, S)))

    def test_generation_is_fast_enough_for_training(self):
        t = time.time()
        dataset(6, 30, (10, 22), seed=3)
        self.assertLess(time.time() - t, 20)


if __name__ == "__main__":
    unittest.main()

"""Le solveur exact de Puissance 4 doit s'accorder avec une recherche exhaustive naïve sur des positions avancées."""
import random
import unittest

from logic_arena.zero import c4solver

COL = (1 << 6) - 1


def drop(mask, c):
    return (mask + (1 << (c * 7))) & (COL << (c * 7))


def wins(p):
    for sh in (1, 7, 6, 8):
        m = p & (p >> sh)
        if m & (m >> (2 * sh)):
            return True
    return False


def brute(pos, mask, moves):
    if moves == 42:
        return 0
    best = -2
    for c in range(7):
        m = drop(mask, c)
        if not m:
            continue
        if wins(pos | m):
            return 1
        best = max(best, -brute(pos ^ mask, mask | m, moves + 1))
        if best == 1:
            break
    return best


class C4SolverTest(unittest.TestCase):
  def test_solver_matches_bruteforce_on_late_positions(self):
      rng = random.Random(1)
      checked = 0
      while checked < 40:
          pos = mask = n = 0
          ok = True
          for _ in range(rng.randint(30, 34)):
              cols = [c for c in range(7) if drop(mask, c)]
              c = rng.choice(cols)
              m = drop(mask, c)
              if wins(pos | m):
                  ok = False
                  break
              pos ^= mask
              mask |= m
              n += 1
          if not ok or wins(pos ^ mask):
              continue
          e = c4solver.solve(pos, mask, True)
          self.assertEqual((e > 0) - (e < 0), brute(pos, mask, n))
          checked += 1


  def test_scores_flag_full_columns_and_immediate_wins(self):
      pos = mask = 0
      for c in (0, 1, 0, 1, 0, 1):  # le joueur 1 a trois pierres en colonne 0
          m = drop(mask, c)
          pos ^= mask
          mask |= m
      s = c4solver.scores(pos, mask, True)
      self.assertTrue(s[0] > 0 and all(x != -1000 for x in s))


if __name__ == "__main__":
    unittest.main()

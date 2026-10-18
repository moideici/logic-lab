import unittest

from logic_arena.lab import handle
from logic_arena.reason import service
from logic_arena.reason.problems import is_valid_solution


@unittest.skipUnless(service.PATH.exists(), "modèle Loop absent : lancer training-lab/entrainer_loop.py")
class ReasonServiceTests(unittest.TestCase):
    def test_new_puzzle_is_deterministic_and_consistent(self):
        a, b = service.new_puzzle(20, 3), service.new_puzzle(20, 3)
        self.assertEqual(a, b)
        self.assertEqual(sum(v == 0 for v in a["puzzle"]), a["vides"])
        self.assertTrue(is_valid_solution(6, a["solution"]))
        self.assertTrue(all(p in (0, s) for p, s in zip(a["puzzle"], a["solution"])))

    def test_solving_reports_each_pass_and_the_first_valid_grid(self):
        p = service.new_puzzle(14, 1)
        r = service.solve(p["puzzle"], 16, p["solution"])
        self.assertEqual(len(r["etapes"]), 16)
        self.assertEqual(r["etapes"][0]["passe"], 1)
        self.assertIsNotNone(r["premiere_valide"])
        step = r["etapes"][r["premiere_valide"] - 1]
        self.assertTrue(step["valide"])
        self.assertEqual(step["fausses"], 0)
        self.assertTrue(all(0 <= c <= 1 for c in step["confiance"]))
        # les cases données restent inchangées à chaque passe
        for e in r["etapes"]:
            self.assertTrue(all(g == s for g, s in zip(e["grille"], p["puzzle"]) if s))

    def test_invalid_requests_are_refused(self):
        for body in ({"puzzle": [0] * 5, "passes": 8}, {"puzzle": [9] * 36, "passes": 8}, {"puzzle": [0] * 36, "passes": 8}, {"puzzle": [1] * 36, "passes": 999}):
            status, payload = handle("POST", "/api/lab/reason/solve", {}, body)
            self.assertEqual(status, 400, body)
        status, _ = handle("POST", "/api/lab/reason/new", {}, {"empties": 99, "seed": 1})
        self.assertEqual(status, 400)
        status, payload = handle("GET", "/api/lab/reason/info", {}, {})
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"]["n"], 6)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest import mock

from logic_arena.maths import evaluate
from logic_arena.maths.arith import next_state
from logic_arena.maths.data import LEVELS, make_starts, make_steps


def oracle(model, prompts, device="cpu", **kw):
    return [next_state(p) for p in prompts]


def always_wrong(model, prompts, device="cpu", **kw):
    return ["0" for _ in prompts]


class EvaluateTests(unittest.TestCase):
    def test_oracle_scores_one_on_every_level(self):
        with mock.patch.object(evaluate, "generate", oracle):
            for lv in LEVELS:
                r = evaluate.evaluate_level(None, lv, "test", 60, 40, 0)
                self.assertEqual(r["etape"]["exacte"], 1.0, lv)
                self.assertEqual(r["etape"]["valide"], 1.0, lv)
                self.assertEqual(r["probleme"]["resolu"], 1.0, lv)
                self.assertEqual(r["probleme"]["echecs"], {}, lv)

    def test_oracle_also_solves_out_of_distribution(self):
        with mock.patch.object(evaluate, "generate", oracle):
            r = evaluate.evaluate_level(None, "N5", "test", 40, 30, 1, ood=True)
        self.assertEqual(r["probleme"]["resolu"], 1.0)
        self.assertGreater(r["probleme"]["etapes_moy"], 3)

    def test_wrong_outputs_are_counted_as_failures(self):
        with mock.patch.object(evaluate, "generate", always_wrong):
            r = evaluate.evaluate_level(None, "N4", "test", 40, 30, 0)
        self.assertEqual(r["etape"]["exacte"], 0.0)
        self.assertEqual(r["etape"]["valide"], 0.0)
        self.assertEqual(r["probleme"]["resolu"], 0.0)
        self.assertEqual(r["probleme"]["echecs"], {"étape invalide": 30})

    def test_valid_but_different_order_counts_valid_not_exact(self):
        pairs = [("(2+3)*(4+1)", "5*(4+1)")]  # la référence prend le premier groupe

        def second_group_first(model, prompts, device="cpu", **kw):
            return ["(2+3)*5" for _ in prompts]

        with mock.patch.object(evaluate, "generate", second_group_first):
            r = evaluate.step_metrics(None, pairs)
        self.assertEqual((r["exacte"], r["valide"]), (0.0, 1.0))

    def test_stalling_model_runs_out_of_steps(self):
        # une étape qui ne progresse pas est invalide dès la première fois
        def stall(model, prompts, device="cpu", **kw):
            return list(prompts)

        with mock.patch.object(evaluate, "generate", stall):
            r = evaluate.solve_metrics(None, make_starts("N4", 10, 0))
        self.assertEqual(r["resolu"], 0.0)
        self.assertEqual(r["echecs"], {"étape invalide": 10})


if __name__ == "__main__":
    unittest.main()

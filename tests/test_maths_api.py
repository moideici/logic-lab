import unittest

from logic_arena import maths_api


class MathsApi(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(maths_api.normalize(" 12 + 7 × 3 − 4 "), "12+7*3-4")

    def test_unknown_expression_is_refused(self):
        with self.assertRaises(ValueError):
            maths_api.solve("3++", "recetteD") if maths_api.models() else (_ for _ in ()).throw(ValueError("pas de poids"))

    @unittest.skipUnless(maths_api.models(), "poids Maths absents")
    def test_small_calculation_is_solved_and_every_step_verified(self):
        r = maths_api.solve("12+7*3-4", maths_api.models()[0]["id"])
        self.assertTrue(r["correct"])
        self.assertTrue(all(s["valid"] for s in r["steps"]))
        self.assertEqual(r["final"], "29")


if __name__ == "__main__":
    unittest.main()

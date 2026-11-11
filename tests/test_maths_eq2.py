import unittest
from fractions import Fraction

from logic_arena.maths.arith import (ArithError, chain, final_state, is_canonical, next_state, solset, solve_eq, verify_step, _progress,
                                     _remaining)
from logic_arena.maths.data import make_steps


def rat(s):
    return chain(s, rational=True)


class ReferenceChainTests(unittest.TestCase):
    def test_powers(self):
        self.assertEqual(rat("x^2=49"), ["x^2=49", "x=7 ou x=-7"])
        self.assertEqual(rat("3x^2+5=53"), ["3x^2+5=53", "3x^2=53-5", "3x^2=48", "x^2=48/3", "x^2=16", "x=4 ou x=-4"])
        self.assertEqual(rat("5+2x^2=55"), ["5+2x^2=55", "2x^2=55-5", "2x^2=50", "x^2=50/2", "x^2=25", "x=5 ou x=-5"])
        self.assertEqual(rat("x^2=0"), ["x^2=0", "x=0"])
        self.assertEqual(rat("x^2=-4"), ["x^2=-4", "aucune solution"])
        self.assertEqual(rat("x^3=-27"), ["x^3=-27", "x=-3"])
        self.assertEqual(rat("4x^2=9"), ["4x^2=9", "x^2=9/4", "x^2=(9/4)", "x=(3/2) ou x=(-3/2)"])

    def test_fractions(self):
        self.assertEqual(rat("x/3+2=5"), ["x/3+2=5", "x/3=5-2", "x/3=3", "x=3*3", "x=9"])
        self.assertEqual(rat("(2/3)x=4"), ["(2/3)x=4", "x=4/(2/3)", "x=(4*3/2)", "x=(12/2)", "x=6"])
        self.assertEqual(rat("(3/4)x-1=2"), ["(3/4)x-1=2", "(3/4)x=2+1", "(3/4)x=3", "x=3/(3/4)", "x=(3*4/3)", "x=(12/3)", "x=4"])
        self.assertEqual(rat("(2/3)x=1")[-1], "x=(3/2)")
        self.assertEqual(rat("x/4=-2")[-1], "x=-8")

    def test_roots(self):
        self.assertEqual(rat("√x=7"), ["√x=7", "x=7^2", "x=49"])
        self.assertEqual(rat("2√x+1=9"), ["2√x+1=9", "2√x=9-1", "2√x=8", "√x=8/2", "√x=4", "x=4^2", "x=16"])
        self.assertEqual(rat("√(x+3)=5"), ["√(x+3)=5", "x+3=5^2", "x+3=25", "x=25-3", "x=22"])
        self.assertEqual(rat("√(x-4)=3")[-1], "x=13")
        self.assertEqual(rat("√x=-2"), ["√x=-2", "aucune solution"])
        self.assertEqual(rat("√x=(1/2)")[-1], "x=(1/4)")

    def test_terminals_and_errors(self):
        for t in ("x=7 ou x=-7", "aucune solution", "x=5", "x=(3/2)"):
            self.assertIsNone(next_state(t, True))
        with self.assertRaises(ArithError):
            rat("x^2=5")                 # solution irrationnelle : hors vague
        with self.assertRaises(ArithError):
            rat("x/1=3")                 # diviseur trivial


class SolutionSetTests(unittest.TestCase):
    def test_sets(self):
        S = lambda *v: frozenset(Fraction(x) for x in v)
        self.assertEqual(solset("x^2=49"), S(7, -7))
        self.assertEqual(solset("3x^2+5=53"), S(4, -4))
        self.assertEqual(solset("x^2=-4"), S())
        self.assertEqual(solset("√x=-2"), S())
        self.assertEqual(solset("√(x+3)=5"), S(22))
        self.assertEqual(solset("x/3+2=5"), S(9))
        self.assertEqual(solset("(2/3)x=4"), S(6))
        self.assertEqual(solset("2√x+1=9"), S(16))
        self.assertEqual(solset("x^3=-27"), S(-3))
        self.assertEqual(solset("x=7 ou x=-7"), S(7, -7))
        self.assertEqual(solset("aucune solution"), S())
        self.assertEqual(solset("x^2-20=5"), S(5, -5))
        self.assertEqual(solset("20=x^2+4"), S(4, -4))        # inconnue à droite ou à gauche
        self.assertEqual(solset("x^2=(9/4)"), frozenset({Fraction(3, 2), Fraction(-3, 2)}))

    def test_errors(self):
        for bad in ("x^2=5", "2x+x=3", "3=4", "x^x=4"):
            with self.assertRaises(ArithError, msg=bad):
                solset(bad)

    def test_solver_agrees_with_the_wave_one_solver_and_progress(self):
        for inp, out in make_steps("N6", 400, 21, "train"):
            for s in (inp, out):
                self.assertEqual(solset(s), frozenset({solve_eq(s)}), s)
            self.assertEqual(_remaining(inp), _progress(inp))


class VerifyAndCanonicalTests(unittest.TestCase):
    def test_valid_steps(self):
        for a, b in (("x^2=49", "x=7 ou x=-7"), ("3x^2=48", "x^2=48/3"), ("x^2=-4", "aucune solution"), ("√x=7", "x=7^2"),
                     ("x/3=3", "x=3*3"), ("(2/3)x=4", "x=4/(2/3)"), ("√(x+3)=5", "x+3=5^2")):
            self.assertTrue(verify_step(a, b), (a, b))

    def test_wrong_steps(self):
        for a, b in (("x^2=49", "x=7"),                       # solution perdue
                     ("x^2=-4", "x=2 ou x=-2"),
                     ("3x^2=48", "x^2=48-3"),
                     ("3x^2=48", "x^2=48/3 "),
                     ("√x=7", "x=7"),
                     ("x/3+2=5", "x/3=5+2"),
                     ("x^2=49", "x=-7 ou x=7"),                # ordre non canonique
                     ("x^2=49", "x=7 ou x=7"),
                     ("√x=-2", "x=(-2)^2")):
            self.assertFalse(verify_step(a, b), (a, b))

    def test_canonical_equations(self):
        for good in ("x^2=49", "3x^2+5=53", "5+2x^2=55", "x/3+2=5", "(2/3)x-1=4", "2√x+1=9", "√(x+3)=5", "x=7 ou x=-7", "aucune solution",
                     "x=(3/2) ou x=(-3/2)"):
            self.assertTrue(is_canonical(good), good)
        for bad in ("1x^2=4", "x^2=+4", "x^2=(4)", "x/1=3", "(4/2)x=1", "2√x+1+2=9", "x=7 ou x=-7 ou x=1", "x =7"):
            self.assertFalse(is_canonical(bad), bad)

    def test_final_state(self):
        self.assertEqual(final_state("3x+5=20"), "x=5")
        self.assertEqual(final_state("3x^2+5=53"), "x=4 ou x=-4")
        self.assertEqual(final_state("x^2=-4"), "aucune solution")
        self.assertEqual(final_state("(2/3)x=1"), "x=(3/2)")
        self.assertEqual(final_state("2+3*4"), "14")
        self.assertEqual(final_state("1/2+1/3"), "(5/6)")


if __name__ == "__main__":
    unittest.main()

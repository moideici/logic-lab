import unittest
from fractions import Fraction

from logic_arena.maths.arith import ArithError, answer, chain, final_text, is_canonical, next_state, render, tokenize, value, verify_step


def rat(s):
    return chain(s, rational=True)


class PowerTests(unittest.TestCase):
    def test_power_chains(self):
        self.assertEqual(chain("2^3"), ["2^3", "8"])
        self.assertEqual(chain("2^0"), ["2^0", "1"])
        self.assertEqual(chain("2+3*2^2"), ["2+3*2^2", "2+3*4", "2+12", "14"])

    def test_right_associativity_and_leftmost_independent_power(self):
        self.assertEqual(chain("2^3^2"), ["2^3^2", "2^9", "512"])
        self.assertEqual(chain("2^3*4^2"), ["2^3*4^2", "8*4^2", "8*16", "128"])

    def test_negative_base_is_always_parenthesised(self):
        self.assertEqual(chain("(-2)^3"), ["(-2)^3", "-8"])
        self.assertEqual(chain("3+(-2)^2"), ["3+(-2)^2", "3+4", "7"])
        self.assertEqual(chain("((-2)^2)"), ["((-2)^2)", "(4)", "4"][0:1] + ["4"])
        self.assertFalse(is_canonical("-2^2"))
        self.assertTrue(is_canonical("(-2)^2"))
        self.assertEqual(render(tokenize("(-2)^2")), "(-2)^2")

    def test_group_that_becomes_a_negative_base_keeps_the_marking(self):
        self.assertEqual(chain("(1-3)^2"), ["(1-3)^2", "(-2)^2", "4"])

    def test_errors(self):
        for bad in ("0^0", "2^13", "2^(-1)", "2^-1", "2^(1/2)"):
            with self.assertRaises(ArithError, msg=bad):
                chain(bad, rational=True)


class RootTests(unittest.TestCase):
    def test_roots(self):
        self.assertEqual(chain("√16"), ["√16", "4"])
        self.assertEqual(chain("√(9+16)"), ["√(9+16)", "√25", "5"])
        self.assertEqual(chain("∛(-27)"), ["∛(-27)", "-3"])
        self.assertEqual(chain("∛1000"), ["∛1000", "10"])
        self.assertEqual(chain("√0"), ["√0", "0"])

    def test_root_priority(self):
        self.assertEqual(chain("√16+∛8*2"), ["√16+∛8*2", "4+∛8*2", "4+2*2", "4+4", "8"])
        self.assertEqual(chain("2^√16"), ["2^√16", "2^4", "16"])
        self.assertEqual(chain("√16^2"), ["√16^2", "4^2", "16"])   # (√16)^2
        self.assertEqual(chain("√√16"), ["√√16", "√4", "2"])

    def test_inexact_or_invalid_roots_are_errors(self):
        for bad in ("√2", "√(-4)", "∛9", "√(1/3)"):
            with self.assertRaises(ArithError, msg=bad):
                chain(bad, rational=True)


class FractionTests(unittest.TestCase):
    def test_inexact_division_gives_a_fraction_atom(self):
        self.assertEqual(rat("3/4"), ["3/4", "(3/4)"])
        self.assertEqual(rat("6/4"), ["6/4", "(3/2)"])
        self.assertEqual(rat("6/3"), ["6/3", "2"])
        self.assertEqual(rat("(6/4)+1"), ["(6/4)+1", "(3/2)+1", "((3+1*2)/2)", "((3+2)/2)", "(5/2)"])

    def test_operations_between_atoms(self):
        # amendement : une opération sur une fraction est d'abord réécrite en un groupe d'opérations sur des entiers (gabarit), puis réduite
        self.assertEqual(rat("1/2+1/3"), ["1/2+1/3", "(1/2)+1/3", "(1/2)+(1/3)", "((1*3+1*2)/(2*3))", "((3+1*2)/(2*3))", "((3+2)/(2*3))",
                                          "(5/(2*3))", "(5/6)"])
        self.assertEqual(rat("(1/2)*(2/3)"), ["(1/2)*(2/3)", "(1*2/(2*3))", "(1*2/6)", "(2/6)", "(1/3)"])
        self.assertEqual(rat("(3/4)/(3/8)"), ["(3/4)/(3/8)", "(3*8/(4*3))", "(3*8/12)", "(24/12)", "2"])
        self.assertEqual(rat("1-(3/4)"), ["1-(3/4)", "((1*4-3)/4)", "((4-3)/4)", "(1/4)"])
        self.assertEqual(rat("(-1/2)*4"), ["(-1/2)*4", "(-1*4/2)", "(-4/2)", "-2"])
        self.assertEqual(rat("(1/2)^3"), ["(1/2)^3", "(1^3/2^3)", "(1/2^3)", "(1/8)"])
        self.assertEqual(rat("√(1/4)"), ["√(1/4)", "(√1/√4)", "(1/√4)", "(1/2)"])
        self.assertEqual(rat("(1/2)+(1/2)"), ["(1/2)+(1/2)", "((1*2+1*2)/(2*2))", "((2+1*2)/(2*2))", "((2+2)/(2*2))", "(4/(2*2))",
                                              "(4/4)", "1"])

    def test_group_reducing_to_a_fraction_loses_its_parentheses(self):
        self.assertEqual(rat("2*(1/2+1/3)"), ["2*(1/2+1/3)", "2*((1/2)+1/3)", "2*((1/2)+(1/3))", "2*((1*3+1*2)/(2*3))", "2*((3+1*2)/(2*3))",
                                              "2*((3+2)/(2*3))", "2*(5/(2*3))", "2*(5/6)", "(2*5/6)", "(10/6)", "(5/3)"])

    def test_negative_fraction_results(self):
        self.assertEqual(rat("1/4-1/2"), ["1/4-1/2", "(1/4)-1/2", "(1/4)-(1/2)", "((1*2-1*4)/(4*2))", "((2-1*4)/(4*2))", "((2-4)/(4*2))",
                                          "(-2/(4*2))", "(-2/8)", "(-1/4)"])

    def test_wave_one_mode_still_refuses_inexact_division(self):
        for s in ("7/2", "(1/2)+1", "((11+16)/11)+14"):
            with self.assertRaises(ArithError, msg=s):
                chain(s)
        self.assertEqual(chain("(4/2)"), ["(4/2)", "2"])  # groupe avec division exacte : inchangé

    def test_zero_denominator_and_non_atoms(self):
        with self.assertRaises(ArithError):
            rat("1/0")
        self.assertEqual(tokenize("(2/4)"), ["(", 2, "/", 4, ")"])   # non irréductible : groupe, pas atome
        self.assertEqual(tokenize("(1/2)"), [Fraction(1, 2)])
        self.assertEqual(tokenize("(1/1)"), ["(", 1, "/", 1, ")"])
        self.assertEqual(tokenize("(0/5)"), ["(", 0, "/", 5, ")"])


class IndependentEvaluatorTests(unittest.TestCase):
    def test_values_and_operation_counts(self):
        self.assertEqual(value("2+3*2^2"), (14, 3))
        self.assertEqual(value("√(9+16)"), (5, 2))
        self.assertEqual(value("(1/2)+(1/3)"), (Fraction(5, 6), 5))   # réécriture + 4 opérations du gabarit, la division finale disparaît
        self.assertEqual(value("(1/2)+(1/2)"), (1, 6))                # ici la division finale 4/4 est un pas à part
        self.assertEqual(value("(1/2)+1"), (Fraction(3, 2), 3))
        self.assertEqual(value("(1/2)^2"), (Fraction(1, 4), 3))
        self.assertEqual(value("√(1/4)"), (Fraction(1, 2), 3))
        self.assertEqual(value("(6/4)"), (Fraction(3, 2), 1))      # groupe avec division : une opération
        self.assertEqual(value("(1/2)"), (Fraction(1, 2), 0))       # atome : aucune
        self.assertEqual(value("2^3^2"), (512, 2))
        self.assertEqual(value("∛(-27)"), (-3, 1))

    def test_reference_and_evaluator_agree_on_a_grid_of_expressions(self):
        exprs = ["2^3+√16*3", "(2+3)^2-√(9+16)", "1/2+3/4", "(1/2)^2+(1/4)", "2*(3/4)", "√(1/4)+1/2", "(1/3)/(2/3)", "3^2^2-70",
                 "(-3)^3+∛27*2", "1-√(1/9)", "4/6*3/2", "((1/2)+(1/3))*6"]
        for s in exprs:
            ch = rat(s)
            self.assertEqual(final_text(answer(s), False), ch[-1], s)
            for a, b in zip(ch, ch[1:]):
                self.assertTrue(verify_step(a, b), (a, b))

    def test_verify_rejects_wrong_steps(self):
        self.assertTrue(verify_step("1/2+1/3", "(1/2)+1/3"))
        self.assertFalse(verify_step("1/2+1/3", "(1/2)+(1/4)"))
        self.assertFalse(verify_step("2^3^2", "8^2"))            # change la valeur : (2^3)^2
        self.assertFalse(verify_step("√16^2", "4^3"))
        self.assertTrue(verify_step("√16^2", "√256"))             # même valeur et une opération de moins : valide même si la forme change
        self.assertFalse(verify_step("3/4", "0.75"))
        self.assertFalse(verify_step("6/4", "(6/4)"))            # pas de progression et non réduit

    def test_canonical_forms(self):
        for good in ("(1/2)", "(-1/2)", "2*(3/4)", "√(1/4)", "∛(-27)", "(-2)^3", "2^√16"):
            self.assertTrue(is_canonical(good), good)
        for bad in ("((1/2))", "2*-3", "√-4", "-2^2", "2+(12)", "(1/2"):
            self.assertFalse(is_canonical(bad) and next_state_ok(bad), bad)
        self.assertEqual(next_state("(2/4)", True), "(1/2)")      # état valide, non terminal : groupe avec division


def next_state_ok(s):
    try:
        next_state(s, True)
        return True
    except ArithError:
        return False


if __name__ == "__main__":
    unittest.main()

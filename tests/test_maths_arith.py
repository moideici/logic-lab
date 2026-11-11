import unittest
from fractions import Fraction

from logic_arena.maths.arith import (ArithError, answer, chain, final_text, is_canonical, next_state, parse_eq, render, tokenize,
                                     value, verify_step)


class ChainTests(unittest.TestCase):
    def test_priority_multiplication_before_addition(self):
        self.assertEqual(chain("2+3*4"), ["2+3*4", "2+12", "14"])

    def test_parentheses_first_and_dropped_when_reduced(self):
        self.assertEqual(chain("(2+3)*4"), ["(2+3)*4", "5*4", "20"])
        self.assertEqual(chain("20/(2+3)"), ["20/(2+3)", "20/5", "4"])

    def test_left_to_right_for_same_priority(self):
        self.assertEqual(chain("12/4/3"), ["12/4/3", "3/3", "1"])
        self.assertEqual(chain("10-2-3"), ["10-2-3", "8-3", "5"])

    def test_negative_numbers_are_parenthesised_after_an_operator(self):
        self.assertEqual(chain("10-2*7+3"), ["10-2*7+3", "10-14+3", "-4+3", "-1"])
        self.assertEqual(chain("8-(2-5)"), ["8-(2-5)", "8-(-3)", "11"])
        self.assertEqual(chain("3*(2-5)"), ["3*(2-5)", "3*(-3)", "-9"])
        self.assertEqual(chain("(-3)*2"), ["(-3)*2", "-3*2", "-6"])

    def test_nested_groups_take_the_first_innermost_group(self):
        self.assertEqual(chain("((1+2)*3+4)*2"), ["((1+2)*3+4)*2", "(3*3+4)*2", "(9+4)*2", "13*2", "26"])

    def test_inexact_division_and_garbage_are_errors(self):
        for bad in ("7/2", "5/0", "2+", "(2+3", "2*-3", "a+1", "", "()", "2 +3"):
            with self.assertRaises(ArithError, msg=bad):
                next_state(bad)

    def test_terminal_states(self):
        self.assertIsNone(next_state("14"))
        self.assertIsNone(next_state("-3"))
        self.assertIsNone(next_state("x=5"))

    def test_roundtrip(self):
        for s in ("2+3*4", "(2+3)*4", "8-(-3)", "-4+3", "3*(-3)", "((1+2)*3+4)*2"):
            self.assertEqual(render(tokenize(s)), s)


class EquationTests(unittest.TestCase):
    def test_chains(self):
        self.assertEqual(chain("3x+5=20"), ["3x+5=20", "3x=20-5", "3x=15", "x=15/3", "x=5"])
        self.assertEqual(chain("x-5=20"), ["x-5=20", "x=20+5", "x=25"])
        self.assertEqual(chain("5+2x=-3"), ["5+2x=-3", "2x=-3-5", "2x=-8", "x=-8/2", "x=-4"])
        self.assertEqual(chain("2x=-6"), ["2x=-6", "x=-6/2", "x=-3"])
        self.assertEqual(chain("x+7=7"), ["x+7=7", "x=7-7", "x=0"])

    def test_parse(self):
        self.assertEqual(parse_eq("3x-5=1")[:3], (3, -5, False))
        self.assertEqual(parse_eq("5+x=1")[:3], (1, 5, True))
        with self.assertRaises(ArithError):
            parse_eq("3x+5+2=1")

    def test_independent_solver_agrees_with_the_chain(self):
        for s in ("3x+5=20", "x-5=20", "5+2x=-3", "12x-9=-33", "7x=-21"):
            self.assertEqual(final_text(answer(s), True), chain(s)[-1])


class EvaluatorTests(unittest.TestCase):
    def test_values_and_operation_counts(self):
        self.assertEqual(value("2+3*4"), (14, 2))
        self.assertEqual(value("-6-9"), (-15, 1))
        self.assertEqual(value("8-(-3)"), (11, 1))
        self.assertEqual(value("7/2")[0], Fraction(7, 2))

    def test_reference_chain_and_evaluator_agree_on_random_expressions(self):
        import numpy as np
        rng = np.random.default_rng(0)
        done = 0
        while done < 400:
            n = int(rng.integers(2, 6))
            parts = [str(int(rng.integers(0, 30)))]
            for _ in range(n - 1):
                parts += [str(rng.choice(list("+-*"))), str(int(rng.integers(0, 30)))]
            s = "".join(parts)
            if rng.random() < 0.5 and n >= 3:
                s = "(" + "".join(parts[:3]) + ")" + "".join(parts[3:])
            ch = chain(s)
            self.assertEqual(final_text(answer(s), False), ch[-1], s)
            for a, b in zip(ch, ch[1:]):
                self.assertTrue(verify_step(a, b), (a, b))
            done += 1


class VerifyStepTests(unittest.TestCase):
    def test_accepts_other_valid_orders_but_not_wrong_values(self):
        self.assertTrue(verify_step("2+3*4", "2+12"))
        self.assertFalse(verify_step("2+3*4", "5*4"))          # mauvaise priorité : la valeur change
        self.assertTrue(verify_step("(2+3)*(4+1)", "5*(4+1)"))
        self.assertTrue(verify_step("(2+3)*(4+1)", "(2+3)*5"))  # valide même si ce n'est pas le choix de la référence

    def test_rejects_malformed_or_stalled_outputs(self):
        for out in ("2+3*4", "2+012", "2+(12)", "2+12$", "", "14"):
            self.assertFalse(verify_step("2+3*4", out), out)
        self.assertFalse(verify_step("3x+5=20", "3x=20-6"))
        self.assertTrue(verify_step("3x+5=20", "3x=20-5"))
        self.assertFalse(verify_step("3x=15", "x=15/3+0"))
        self.assertFalse(verify_step("2+3", "x=5"))

    def test_canonical_form(self):
        self.assertTrue(is_canonical("8-(-3)"))
        self.assertFalse(is_canonical("8--3"))
        self.assertFalse(is_canonical("3x+05=1"))


if __name__ == "__main__":
    unittest.main()

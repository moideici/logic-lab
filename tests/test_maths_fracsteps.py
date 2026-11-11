"""Amendement du protocole de la vague 2 : une opération sur fraction est réécrite en gabarit d'entiers avant d'être calculée."""
import unittest
from fractions import Fraction

import numpy as np

from logic_arena.maths.arith import ArithError, answer, chain, final_text, is_canonical, value, verify_step
from logic_arena.maths.data import gen_problem


def rat(s):
    return chain(s, rational=True)


class TemplateTests(unittest.TestCase):
    def test_every_template_keeps_the_value_and_costs_exactly_one_step(self):
        cases = ["(1/2)+(1/3)", "(1/2)-(1/3)", "(1/2)+3", "3-(1/2)", "(1/2)*(2/3)", "(1/2)*3", "3*(1/2)", "(3/4)/(3/8)", "(3/4)/3", "3/(3/4)",
                 "(1/2)^0", "(1/2)^3", "(-2/3)^3", "√(1/4)", "∛(-8/27)", "(5/7)/(-2/3)", "(-5/7)/(-2/3)", "6/(-2/3)", "(-2/3)/(-4)",
                 "(11/12)-(-45/7)", "(-103/21)+(10/9)", "(1/2)-(1/2)", "(1/2)+(-1/2)"]
        for s in cases:
            first = rat(s)[1]
            self.assertEqual(value(first)[0], value(s)[0], s)
            self.assertEqual(value(first)[1], value(s)[1] - 1, s)
            self.assertTrue(verify_step(s, first), (s, first))

    def test_template_is_one_unit_in_any_context(self):
        # sans le groupe extérieur, `3/1^2/2^2` vaudrait 3/4 au lieu de 12
        self.assertEqual(rat("3/(1/2)^2")[-1], "12")
        self.assertEqual(rat("2/(1/3)^2")[-1], "18")
        self.assertEqual(rat("5-(1/2)*(1/3)")[-1], "(29/6)")
        self.assertEqual(rat("(1/2)/(1/3)*6")[-1], "9")

    def test_sign_goes_to_the_numerator(self):
        self.assertEqual(rat("(3/4)/(-3/5)")[1], "(-3*5/(4*3))")
        self.assertEqual(rat("6/(-2/3)")[1], "(-6*3/2)")
        self.assertEqual(rat("(-2/3)/(-4)")[1], "(2/(3*4))")
        self.assertEqual(rat("(11/12)-(-45/7)")[1], "((11*7-(-45)*12)/(12*7))")

    def test_template_filling_a_group_does_not_double_the_parentheses(self):
        ch = rat("(10/11)*((7/4)*6)")
        self.assertEqual(ch[:4], ["(10/11)*((7/4)*6)", "(10/11)*(7*6/4)", "(10/11)*(42/4)", "(10/11)*(21/2)"])
        self.assertTrue(all(is_canonical(s) for s in ch))
        for a, b in zip(ch, ch[1:]):
            self.assertTrue(verify_step(a, b), (a, b))

    def test_irreducible_result_needs_no_final_division_step(self):
        self.assertEqual(rat("(31/7)+(4/9)")[-2:], ["(307/(7*9))", "(307/63)"])
        self.assertEqual(rat("(1/2)+(1/2)")[-3:], ["(4/(2*2))", "(4/4)", "1"])     # exacte : la division est un pas
        self.assertEqual(rat("(-103/21)+(10/9)")[-3:], ["(-717/(21*9))", "(-717/189)", "(-239/63)"])  # réductible : un pas de réduction

    def test_group_division_is_absorbed_only_when_the_atom_is_already_irreducible(self):
        self.assertEqual(value("(7/(2+3))"), (Fraction(7, 5), 1))
        self.assertEqual(value("(10/(2+3))"), (2, 2))
        self.assertEqual(value("(7/(0-5))"), (Fraction(-7, 5), 2))             # dénominateur négatif : pas un atome, la division est un pas
        self.assertEqual(rat("(7/(0-5))"), ["(7/(0-5))", "(7/(-5))", "(-7/5)"])
        self.assertEqual(value("(-7/(2+3))"), (Fraction(-7, 5), 1))
        self.assertEqual(value("(2/(2+2))"), (Fraction(1, 2), 2))
        self.assertEqual(value("1+7/5"), (Fraction(12, 5), 4))                 # pas de groupe : la division reste un pas

    def test_independent_evaluator_and_reference_agree_on_random_problems(self):
        for level in ("N8", "N9", "N10"):
            for ood in (False, True):
                rng = np.random.default_rng(31)
                for _ in range(150):
                    start, ch = gen_problem(rng, level, ood)
                    if "=" not in start:
                        self.assertEqual(ch[-1], final_text(answer(start), False), start)
                    for a, b in zip(ch, ch[1:]):
                        self.assertTrue(verify_step(a, b), (level, a, b))
                    self.assertLessEqual(max(map(len, ch)), 60)

    def test_reduction_goes_one_prime_factor_at_a_time(self):
        # amendement 2 : le pgcd d'un groupe (N/D) non entier se retire facteur premier par facteur premier, le plus petit d'abord
        self.assertEqual(rat("(405/324)"), ["(405/324)", "(135/108)", "(45/36)", "(15/12)", "(5/4)"])
        self.assertEqual(rat("(-480/176)"), ["(-480/176)", "(-240/88)", "(-120/44)", "(-60/22)", "(-30/11)"])
        self.assertEqual(rat("(471/396)"), ["(471/396)", "(157/132)"])
        self.assertEqual(rat("(24/84)")[:3], ["(24/84)", "(12/42)", "(6/21)"])
        self.assertEqual(value("(405/324)"), (Fraction(5, 4), 4))
        self.assertEqual(value("(135/108)"), (Fraction(5, 4), 3))
        self.assertEqual(value("(2*7/4)"), (Fraction(7, 2), 2))
        self.assertEqual(value("(5/10)"), (Fraction(1, 2), 1))

    def test_exact_and_bare_divisions_stay_one_step(self):
        self.assertEqual(rat("(12/4)"), ["(12/4)", "3"])
        self.assertEqual(rat("(4/4)"), ["(4/4)", "1"])
        self.assertEqual(rat("(0/12)"), ["(0/12)", "0"])
        self.assertEqual(rat("48/36"), ["48/36", "(4/3)"])
        self.assertEqual(rat("(10/(0-4))"), ["(10/(0-4))", "(10/(-4))", "(-5/2)"])
        self.assertEqual(value("48/36"), (Fraction(4, 3), 1))

    def test_prime_steps_are_verified_and_wrong_ones_rejected(self):
        self.assertTrue(verify_step("(405/324)", "(135/108)"))
        self.assertTrue(verify_step("(135/108)", "(45/36)"))
        self.assertFalse(verify_step("(405/324)", "(5/4)"))        # tout d'un coup : quatre pas
        self.assertFalse(verify_step("(405/324)", "(45/36)"))      # par 9 : deux pas
        self.assertFalse(verify_step("(405/324)", "(135/107)"))    # valeur fausse

    def test_wave_one_is_untouched(self):
        for s in ("7/2", "(1/2)+1", "((11+16)/11)+14"):
            with self.assertRaises(ArithError, msg=s):
                chain(s)

    def test_wrong_alternatives_are_still_rejected(self):
        self.assertFalse(verify_step("(1/2)+(1/3)", "(5/6)"))                  # deux pas d'un coup : plus une seule opération
        self.assertFalse(verify_step("(1/2)+(1/3)", "((1*3+1*3)/(2*3))"))       # valeur fausse
        self.assertFalse(verify_step("(1/2)+(1/3)", "(1*3+1*2)/(2*3)"))         # sans le groupe, la forme n'est pas celle du gabarit : coût différent
        self.assertTrue(verify_step("((1*3+1*2)/(2*3))", "((3+1*2)/(2*3))"))


if __name__ == "__main__":
    unittest.main()

import re
import unittest

import numpy as np

from logic_arena.maths.arith import answer, chain, final_text, is_canonical, verify_step
from logic_arena.maths.data import (CH2ID, EOS, LEVELS, LEVELS2, SEP, VOCAB, encode_pair, gen_problem, make_starts, make_steps, split_of)


class Wave2GeneratorTests(unittest.TestCase):
    def test_every_new_level_gives_canonical_valid_chains(self):
        rng = np.random.default_rng(0)
        for lv in ("N7", "N8", "N9"):
            for ood in (False, True):
                for _ in range(120):
                    start, traj = gen_problem(rng, lv, ood)
                    self.assertTrue(is_canonical(start), start)
                    self.assertEqual(traj, chain(start, rational=lv in ("N8", "N9")))
                    self.assertEqual(final_text(answer(start), False), traj[-1], start)
                    for a, b in zip(traj, traj[1:]):
                        self.assertTrue(verify_step(a, b), (a, b))

    def test_levels_exercise_what_they_are_named_for(self):
        rng = np.random.default_rng(1)
        n7 = [gen_problem(rng, "N7")[0] for _ in range(300)]
        self.assertTrue(all("^" in s for s in n7))
        self.assertTrue(any("(-" in s for s in n7))                       # bases négatives
        n8 = [gen_problem(rng, "N8")[0] for _ in range(300)]
        self.assertTrue(all("/" in s for s in n8))
        self.assertTrue(any(re.search(r"\(-?\d+/\d+\)", s) for s in n8))   # atomes fractions en entrée
        n9 = [gen_problem(rng, "N9")[0] for _ in range(300)]
        self.assertTrue(all(("√" in s or "∛" in s) for s in n9))
        self.assertTrue(any("∛(-" in s for s in n9))                      # cube négatif
        self.assertTrue(any(re.search(r"√\(\d+\+\d+\)", s) for s in n9))   # racine d'un groupe
        self.assertTrue(any(re.search(r"√\(\d+/\d+\)", s) for s in n9))    # racine d'une fraction

    def test_ood_goes_beyond_training(self):
        rng = np.random.default_rng(2)
        big7 = max(int(t) for _ in range(150) for t in re.findall(r"\d+", gen_problem(rng, "N7", True)[0]))
        small7 = max(int(t) for _ in range(150) for t in re.findall(r"\d+", gen_problem(rng, "N7", False)[0]))
        self.assertGreater(big7, small7)
        sq = [max(int(t) for t in re.findall(r"\d+", gen_problem(rng, "N9", True)[0])) for _ in range(150)]
        self.assertGreater(max(sq), 441)  # au-delà de 21² : carrés parfaits jusqu'à 900

    def test_training_bounds_hold_over_the_whole_chain(self):
        rng = np.random.default_rng(3)
        for lv, bound in (("N7", 9999), ("N8", 999), ("N9", 999)):
            for _ in range(150):
                _, traj = gen_problem(rng, lv)
                self.assertLessEqual(max(int(t) for s in traj for t in re.findall(r"\d+", s)), bound, (lv, traj))

    def test_no_split_leak_and_reproducible(self):
        for lv in ("N7", "N8", "N9"):
            sets = {sp: {i for i, _ in make_steps(lv, 120, 3, sp)} for sp in ("train", "val", "test")}
            self.assertFalse(sets["train"] & sets["val"])
            self.assertFalse(sets["train"] & sets["test"])
            self.assertFalse(sets["val"] & sets["test"])
            self.assertEqual(make_steps(lv, 20, 7), make_steps(lv, 20, 7))
            self.assertEqual(make_starts(lv, 10, 5), make_starts(lv, 10, 5))


class Wave2EquationGeneratorTests(unittest.TestCase):
    def test_n10_chains_are_valid_and_end_in_the_independent_final_state(self):
        from logic_arena.maths.arith import final_state
        rng = np.random.default_rng(5)
        for ood in (False, True):
            for _ in range(150):
                start, traj = gen_problem(rng, "N10", ood)
                self.assertTrue(is_canonical(start), start)
                self.assertEqual(traj[-1], final_state(start), start)
                for a, b in zip(traj, traj[1:]):
                    self.assertTrue(verify_step(a, b), (a, b))

    def test_n10_covers_every_family_and_every_kind_of_answer(self):
        rng = np.random.default_rng(6)
        starts, ends = [], []
        for _ in range(400):
            s, tr = gen_problem(rng, "N10")
            starts.append(s)
            ends.append(tr[-1])
        self.assertTrue(any("x^2" in s for s in starts) and any("x^3" in s for s in starts))
        self.assertTrue(any("x/" in s for s in starts) and any(re.search(r"\(-?\d+/\d+\)x", s) for s in starts))
        self.assertTrue(any("√x" in s for s in starts) and any("√(x" in s for s in starts))
        self.assertTrue(any(e == "aucune solution" for e in ends))
        self.assertTrue(any(" ou " in e for e in ends))
        self.assertTrue(any(re.fullmatch(r"x=-?\d+", e) for e in ends))

    def test_n10_no_split_leak_and_levels3(self):
        from logic_arena.maths.data import LEVELS3
        self.assertEqual(LEVELS3[-1], "N10")
        sets = {sp: {i for i, _ in make_steps("N10", 120, 3, sp)} for sp in ("train", "val", "test")}
        self.assertFalse(sets["train"] & sets["val"] or sets["train"] & sets["test"] or sets["val"] & sets["test"])
        for text in ("x=7 ou x=-7", "aucune solution", "√(x+3)=5", "(2/3)x+5=1"):
            for ch in text:
                self.assertIn(ch, CH2ID)


class VocabularyTests(unittest.TestCase):
    def test_new_characters_are_appended_so_old_ids_do_not_move(self):
        self.assertEqual(VOCAB[:21], ["<pad>"] + list("0123456789+-*/()x=") + [">", "$"])
        self.assertEqual((CH2ID[">"], CH2ID["$"]), (SEP, EOS))
        self.assertEqual(len(set(VOCAB)), len(VOCAB))

    def test_every_state_of_every_level_encodes(self):
        rng = np.random.default_rng(4)
        for lv in LEVELS2:
            for ood in (False, True):
                for _ in range(40):
                    _, traj = gen_problem(rng, lv, ood)
                    for a, b in zip(traj, traj[1:]):
                        encode_pair(a, b)
        for text in ("x=7 ou x=-7", "aucune solution"):
            for ch in text:
                self.assertIn(ch, CH2ID)

    def test_wave_one_levels_unchanged(self):
        self.assertEqual(LEVELS, ("N1", "N2", "N3", "N4", "N5", "N6"))
        self.assertEqual(split_of("12+34"), "train")


if __name__ == "__main__":
    unittest.main()

import re
import unittest

import numpy as np
import torch

from logic_arena.maths.arith import chain, final_text, answer, verify_step
from logic_arena.maths.data import (CH2ID, EOS, LEVELS, MAX_LEN, PAD, SEP, decode, encode_pair, encode_pairs, gen_problem, make_starts,
                                    make_steps, rand_num, split_of)
from logic_arena.maths.model import MathLM, generate, loss_on_outputs


EXPECTED_V1_HASH = "8d77842ba33d"


class SplitTests(unittest.TestCase):
    def test_split_is_stable_and_roughly_90_5_5(self):
        states = [f"{a}+{b}" for a in range(100) for b in range(100)]
        counts = {"train": 0, "val": 0, "test": 0}
        for s in states:
            self.assertEqual(split_of(s), split_of(s))
            counts[split_of(s)] += 1
        n = len(states)
        self.assertAlmostEqual(counts["train"] / n, 0.9, delta=0.02)
        self.assertAlmostEqual(counts["test"] / n, 0.05, delta=0.015)
        self.assertAlmostEqual(counts["val"] / n, 0.05, delta=0.015)
        self.assertEqual(split_of("12+34"), "train")  # valeur figée : change si le hachage change

    def test_train_val_test_share_no_state(self):
        for lv in LEVELS:
            sets = {sp: {i for i, _ in make_steps(lv, 150, 3, sp)} for sp in ("train", "val", "test")}
            self.assertFalse(sets["train"] & sets["val"], lv)
            self.assertFalse(sets["train"] & sets["test"], lv)
            self.assertFalse(sets["val"] & sets["test"], lv)


class GeneratorTests(unittest.TestCase):
    def test_every_level_gives_valid_chains_that_match_the_evaluator(self):
        rng = np.random.default_rng(0)
        for lv in LEVELS:
            for ood in (False, True):
                for _ in range(60):
                    start, traj = gen_problem(rng, lv, ood)
                    self.assertEqual(traj, chain(start))
                    self.assertEqual(final_text(answer(start), "=" in start), traj[-1], start)
                    for a, b in zip(traj, traj[1:]):
                        self.assertTrue(verify_step(a, b), (a, b))

    def test_training_levels_respect_their_bounds(self):
        rng = np.random.default_rng(1)
        for _ in range(200):
            traj = gen_problem(rng, "N4")[1]
            self.assertLessEqual(max(int(t) for state in traj for t in re.findall(r"\d+", state)), 999)
        for lv in ("N1", "N2", "N3"):
            for _ in range(100):
                start, _ = gen_problem(rng, lv, False)
                self.assertLessEqual(len(start), 7)

    def test_ood_goes_beyond_training(self):
        rng = np.random.default_rng(2)
        big = [max(int(t) for t in re.findall(r"\d+", gen_problem(rng, "N1", True)[0])) for _ in range(100)]
        self.assertGreaterEqual(min(big), 1000)
        longer = [len(gen_problem(rng, "N4", True)[0]) for _ in range(100)]
        shorter = [len(gen_problem(rng, "N4", False)[0]) for _ in range(100)]
        self.assertGreater(np.mean(longer), np.mean(shorter) * 1.5)

    def test_reproducible(self):
        self.assertEqual(make_steps("N5", 30, 7), make_steps("N5", 30, 7))
        self.assertNotEqual(make_steps("N5", 30, 7), make_steps("N5", 30, 8))
        self.assertEqual(make_starts("N6", 20, 5), make_starts("N6", 20, 5))

    def test_rand_num_covers_short_numbers(self):
        rng = np.random.default_rng(0)
        digits = {len(str(rand_num(rng, 0, 99))) for _ in range(300)}
        self.assertEqual(digits, {1, 2})

    def test_wide_training_range_never_leaks_into_validation_or_test(self):
        wide = make_steps("N2", 3000, 1, "train", wide=True)
        self.assertGreater(max(int(re.findall(r"\d+", i)[0]) for i, _ in wide), 99)   # plage élargie : facteurs à 3 chiffres
        held = {i for sp in ("val", "test") for i, _ in make_steps("N2", 400, 2, sp, distinct=True)}
        self.assertTrue(held)
        self.assertFalse({i for i, _ in wide} & held)
        n1 = make_steps("N1", 2000, 4, "train", wide=True)
        self.assertGreater(max(int(t) for i, _ in n1 for t in re.findall(r"\d+", i)), 99)
        held1 = {i for sp in ("val", "test") for i, _ in make_steps("N1", 300, 5, sp, distinct=True)}
        self.assertFalse({i for i, _ in n1} & held1)
        # sans `wide`, la plage reste celle du protocole
        plain = make_steps("N3", 500, 3, "train")
        self.assertLessEqual(max(int(i.split("/")[0]) // int(i.split("/")[1]) for i, _ in plain), 99)

    def test_non_wide_streams_are_unchanged_by_the_wide_options(self):
        # états de validation et de test de la v1 : mêmes graines, mêmes états (empreinte figée)
        import hashlib
        h = hashlib.blake2b("|".join(i for lv in ("N1", "N2", "N3") for i, _ in make_steps(lv, 40, 7, "test", distinct=True)).encode(), digest_size=6).hexdigest()
        self.assertEqual(h, EXPECTED_V1_HASH)

    def test_wide_training_covers_negatives_two_digit_factors_and_larger_divisors(self):
        from logic_arena.maths.arith import chain as ch, verify_step as vs
        n1 = [i for i, _ in make_steps("N1", 1500, 11, "train", wide=True)]
        self.assertTrue(any("(-" in i for i in n1) and any(i.startswith("-") for i in n1))
        n2 = [i for i, _ in make_steps("N2", 1500, 12, "train", wide=True)]
        self.assertTrue(any(min(int(t) for t in re.findall(r"\d+", i)) >= 13 for i in n2))   # deux facteurs d'au moins 13
        n3 = [i for i, _ in make_steps("N3", 1500, 13, "train", wide=True)]
        self.assertTrue(any(int(re.findall(r"\d+", i)[1]) > 12 for i in n3))                  # diviseur supérieur à 12
        for i in n1[:200] + n2[:200] + n3[:200]:
            a = ch(i)
            self.assertTrue(all(vs(x, y) for x, y in zip(a, a[1:])), i)

    def test_distinct_evaluation_sets_have_no_repeats(self):
        steps = make_steps("N1", 300, 0, "test", distinct=True)
        self.assertEqual(len({i for i, _ in steps}), len(steps))


class EncodingTests(unittest.TestCase):
    def test_roundtrip_and_layout(self):
        ids = encode_pair("2+3*4", "2+12")
        self.assertEqual(ids[5], SEP)
        self.assertEqual(ids[-1], EOS)
        self.assertEqual(decode(ids[6:]), "2+12")
        X, plen = encode_pairs([("2+3*4", "2+12"), ("(2+3)*4", "5*4")])
        self.assertEqual(X.shape, (2, MAX_LEN))
        self.assertEqual(list(plen), [6, 8])
        self.assertEqual(X[0, plen[0] - 1], SEP)
        self.assertEqual(X[0, -1], PAD)
        self.assertEqual(CH2ID["x"], CH2ID["x"])


class ModelTests(unittest.TestCase):
    def test_size_under_one_million_parameters(self):
        self.assertLess(MathLM().parameter_count(), 1_000_000)

    def test_causal(self):
        torch.manual_seed(0)
        m = MathLM(d=32, layers=2, heads=2, ff=64).eval()
        a = torch.randint(1, 20, (1, 12))
        b = a.clone()
        b[0, 8:] = (b[0, 8:] + 3) % 19 + 1
        with torch.no_grad():
            la, lb = m(a), m(b)
        self.assertTrue(torch.allclose(la[:, :8], lb[:, :8], atol=1e-5))

    def test_loss_counts_exactly_the_output_tokens_and_the_end_marker(self):
        torch.manual_seed(0)
        m = MathLM(d=32, layers=2, heads=2, ff=64).eval()
        X, plen = encode_pairs([("2+3*4", "2+12")])
        X, p = torch.as_tensor(X.astype(np.int64)), torch.as_tensor(plen.astype(np.int64))
        with torch.no_grad():
            logits = m(X[:, :-1])
            lp = torch.log_softmax(logits[0], -1)
            # sortie « 2+12$ » : indices 6 à 10 de la séquence, prédits depuis les positions 5 à 9
            expected = -sum(float(lp[t - 1, X[0, t]]) for t in range(6, 11)) / 5
            self.assertAlmostEqual(float(loss_on_outputs(m, X, p)), expected, places=4)

    def test_can_overfit_a_few_examples_and_generate_them(self):
        torch.manual_seed(0)
        pairs = [("2+3*4", "2+12"), ("(2+3)*4", "5*4"), ("3x+5=20", "3x=20-5"), ("10-14+3", "-4+3"), ("-4+3", "-1"), ("x=15/3", "x=5")]
        m = MathLM(d=64, layers=2, heads=4, ff=128)
        X, plen = encode_pairs(pairs, 32)
        X, plen = torch.as_tensor(X.astype(np.int64)), torch.as_tensor(plen.astype(np.int64))
        opt = torch.optim.AdamW(m.parameters(), lr=3e-3)
        for _ in range(250):
            opt.zero_grad()
            loss = loss_on_outputs(m, X, plen)
            loss.backward()
            opt.step()
        self.assertLess(float(loss), 0.05)
        self.assertEqual(generate(m, [i for i, _ in pairs]), [o for _, o in pairs])


if __name__ == "__main__":
    unittest.main()

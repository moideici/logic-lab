import unittest

import numpy as np
import torch

from logic_arena.maths.data import VOCAB_SIZE, encode_pairs
from logic_arena.maths.model import MathLM, beam_generate, generate, load_compatible, loss_on_outputs


class GrowthTests(unittest.TestCase):
    def test_deeper_model_starts_as_the_same_function(self):
        torch.manual_seed(0)
        base = MathLM(d=32, layers=2, heads=2, ff=64).eval()
        grown = MathLM(d=32, layers=5, heads=2, ff=64).eval()
        added = load_compatible(grown, base.state_dict())
        self.assertEqual(added, 3)
        ids = torch.randint(1, VOCAB_SIZE, (3, 20))
        with torch.no_grad():
            self.assertTrue(torch.allclose(base(ids), grown(ids), atol=1e-5))

    def test_added_layers_do_learn(self):
        torch.manual_seed(1)
        base = MathLM(d=32, layers=1, heads=2, ff=64)
        grown = MathLM(d=32, layers=3, heads=2, ff=64)
        load_compatible(grown, base.state_dict())
        ids = torch.randint(1, VOCAB_SIZE, (4, 12))
        grown(ids).sum().backward()
        new = grown.blocks.layers[2]
        self.assertGreater(float(new.linear2.weight.grad.abs().sum()), 0)
        self.assertGreater(float(new.self_attn.out_proj.weight.grad.abs().sum()), 0)

    def test_older_smaller_vocabulary_checkpoint_loads(self):
        torch.manual_seed(2)
        m = MathLM(d=32, layers=1, heads=2, ff=64)
        old = {k: (v[:21].clone() if k in ("tok.weight", "head.weight") else v.clone()) for k, v in m.state_dict().items()}
        fresh = MathLM(d=32, layers=1, heads=2, ff=64)
        self.assertEqual(load_compatible(fresh, old), 0)
        self.assertTrue(torch.equal(fresh.tok.weight[:21], m.tok.weight[:21]))


class CheckpointingTests(unittest.TestCase):
    def test_recomputation_gives_the_same_loss_and_gradients(self):
        torch.manual_seed(0)
        X, plen = encode_pairs([("2+3*4", "2+12"), ("(2+3)*4", "5*4"), ("3x+5=20", "3x=20-5")], 32)
        X, plen = torch.as_tensor(X.astype(np.int64)), torch.as_tensor(plen.astype(np.int64))
        a = MathLM(d=32, layers=3, heads=2, ff=64)
        b = MathLM(d=32, layers=3, heads=2, ff=64)
        b.load_state_dict(a.state_dict())
        b.grad_ckpt = True
        la, lb = loss_on_outputs(a, X, plen), loss_on_outputs(b, X, plen)
        la.backward()
        lb.backward()
        self.assertAlmostEqual(float(la), float(lb), places=5)
        for (n, pa), (_, pb) in zip(a.named_parameters(), b.named_parameters()):
            self.assertTrue(torch.allclose(pa.grad, pb.grad, atol=1e-5), n)


class PerRowLossTests(unittest.TestCase):
    def test_worst_token_loss_per_example(self):
        torch.manual_seed(0)
        m = MathLM(d=32, layers=1, heads=2, ff=64).eval()
        X, plen = encode_pairs([("2+3*4", "2+12"), ("10-14+3", "-4+3")])
        X, plen = torch.as_tensor(X.astype(np.int64)), torch.as_tensor(plen.astype(np.int64))
        loss, worst = loss_on_outputs(m, X, plen, per_row=True)
        self.assertEqual(worst.shape, (2,))
        self.assertTrue(torch.isfinite(loss) and bool((worst > 0).all()))
        self.assertAlmostEqual(float(loss_on_outputs(m, X, plen)), float(loss), places=6)
        with torch.no_grad():
            lp = torch.log_softmax(m(X[:, :-1]), -1)
        row0 = max(-float(lp[0, t - 1, X[0, t]]) for t in range(6, 11))  # sortie « 2+12$ » : indices 6 à 10
        self.assertAlmostEqual(float(worst[0]), row0, places=4)


class BeamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.manual_seed(0)
        cls.pairs = [("2+3*4", "2+12"), ("(2+3)*4", "5*4"), ("3x+5=20", "3x=20-5"), ("10-14+3", "-4+3"), ("-4+3", "-1"), ("x=15/3", "x=5")]
        m = MathLM(d=64, layers=2, heads=4, ff=128)
        X, plen = encode_pairs(cls.pairs, 32)
        X, plen = torch.as_tensor(X.astype(np.int64)), torch.as_tensor(plen.astype(np.int64))
        opt = torch.optim.AdamW(m.parameters(), lr=3e-3)
        for _ in range(250):
            opt.zero_grad()
            loss_on_outputs(m, X, plen).backward()
            opt.step()
        cls.model = m

    def test_best_beam_equals_greedy_and_candidates_are_distinct(self):
        prompts = [i for i, _ in self.pairs]
        cands = beam_generate(self.model, prompts, beam=4)
        greedy = generate(self.model, prompts)
        for c, g, (_, target) in zip(cands, greedy, self.pairs):
            self.assertEqual(len(c), 4)
            self.assertEqual(c[0], g)
            self.assertEqual(c[0], target)
            self.assertEqual(len(set(c)), 4)

    def test_beam_one_is_greedy(self):
        prompts = [i for i, _ in self.pairs]
        self.assertEqual([c[0] for c in beam_generate(self.model, prompts, beam=1)], generate(self.model, prompts))

    def test_verified_solving_never_returns_a_wrong_answer(self):
        from logic_arena.maths import evaluate
        r = evaluate.solve_verified(self.model, ["2+3*4", "(2+3)*4", "10-14+3"], beam=4)
        self.assertEqual(r["n"], 3)
        self.assertTrue(all(k != "résultat faux" for k in r["echecs"]))   # une réponse finale fausse est impossible : chaque pas est vérifié
        # un modèle qui se trompe toujours ne produit aucune réponse fausse : il échoue
        bad = MathLM(d=16, layers=1, heads=2, ff=32)
        r2 = evaluate.solve_verified(bad, ["2+3*4", "(2+3)*4"], beam=2)
        self.assertEqual(r2["resolu"] + sum(r2["echecs"].values()) / 2 >= 1.0, True)
        self.assertNotIn("résultat faux", r2["echecs"])


if __name__ == "__main__":
    unittest.main()

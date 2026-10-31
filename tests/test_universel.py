"""Garry Universel : l'encodeur est déterministe et le modèle note les coups sans dépendre de leur ordre, ni du remplissage du lot."""
import unittest

import numpy as np
import torch

from universel import tokens as tk
from universel.bridge import Bridge
from universel.model import UniversalPlayer


class UniversalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = Bridge()
        cls.samples = []
        for game in ("morpion", "puissance-4", "dames", "othello"):
            s = cls.bridge.init(game, seed=2)
            cls.samples.append((game, s["view"], s["legal"], s["active"][0]))

    @classmethod
    def tearDownClass(cls):
        cls.bridge.close()

    def test_encoding_is_deterministic_and_nonempty(self):
        for _, view, legal, seat in self.samples:
            a, b = tk.encode(view, legal, seat, 2), tk.encode(view, legal, seat, 2)
            np.testing.assert_array_equal(a["ints"], b["ints"])
            self.assertGreater(a["n_view"], 2)
            self.assertEqual(a["n_actions"], len(legal))

    def test_action_numbers_share_embedding_with_indices(self):
        view = {"cells": [None, None, "X"]}
        enc = tk.encode(view, [{"type": "play", "cell": 2}], 0, 2)
        ints = enc["ints"]
        cell_token = [r for r in ints if r[5] == tk.SEG_VIEW and r[1] == 2][0]
        action_cell = [r for r in ints if r[5] == tk.SEG_ACTION and r[3] == tk.T_INT][0]
        self.assertEqual(cell_token[1], action_cell[4])  # indice 2 de la vue == valeur 2 du coup

    def test_permutation_chunking_and_padding_invariance(self):
        torch.manual_seed(0)
        model = UniversalPlayer(d=32, layers=2, heads=4, ff=64).eval()
        game, view, legal, seat = self.samples[2]  # dames
        enc = tk.encode(view, legal, seat, 2)
        with torch.no_grad():
            s_all, _ = model(tk.collate([enc]))
            perm = list(reversed(range(len(legal))))
            enc_p = tk.encode(view, [legal[i] for i in perm], seat, 2)
            s_perm, _ = model(tk.collate([enc_p]))
            n = len(legal)
            np.testing.assert_allclose(s_perm[0, :n].numpy(), s_all[0, :n].numpy()[perm], atol=1e-4)
            # lot avec un échantillon plus long : même score pour le premier
            long_enc = tk.encode(self.samples[3][1], self.samples[3][2], self.samples[3][3], 2)
            s_batch, _ = model(tk.collate([enc, long_enc]))
            np.testing.assert_allclose(s_batch[0, :n].numpy(), s_all[0, :n].numpy(), atol=1e-4)
            # découpage des coups en deux paquets
            half = n // 2
            if half:
                first = model(tk.collate([tk.encode(view, legal[:half], seat, 2)]))[0][0, :half].numpy()
                np.testing.assert_allclose(first, s_all[0, :half].numpy(), atol=1e-4)


if __name__ == "__main__":
    unittest.main()

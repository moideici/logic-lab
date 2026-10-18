import unittest

from logic_arena.lab import Lab, handle


class LabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = Lab()

    def test_describe_matches_the_active_network(self):
        d = self.lab.describe()
        self.assertEqual(d["forme"], [4872, 48, 48, 4259])
        self.assertEqual(len(d["jeux"]), 14)
        self.assertEqual([c["name"] for c in d["couches"]], ["encodeur", "coeur", "sortie"])

    def test_new_game_exposes_activations_and_ranked_actions(self):
        s = self.lab.new_game("tictactoe", 3)
        self.assertEqual(len(s["activations"]["encodeur"]), 48)
        self.assertEqual(len(s["activations"]["coeur"]), 48)
        self.assertTrue(s["actions"][0]["choisie"])
        self.assertEqual([a["score"] for a in s["actions"]], sorted((a["score"] for a in s["actions"]), reverse=True))
        self.assertFalse(s["choix_change"])

    def test_muting_changes_activations_and_resetting_restores_them(self):
        base = self.lab.new_game("connect4", 1)
        strongest = max(range(48), key=lambda i: abs(base["activations"]["coeur"][i]))
        muted = self.lab.mute("coeur", strongest, True)
        self.assertEqual(muted["activations"]["coeur"][strongest], 0.0)
        self.assertIn(strongest, muted["eteints"]["coeur"])
        back = self.lab.reset_mutes()
        self.assertEqual(back["activations"], base["activations"])
        self.assertEqual(back["eteints"], {})

    def test_steps_advance_and_finish_without_error(self):
        self.lab.new_game("nim", 5)
        for _ in range(60):
            s = self.lab.step("hasard" if _ % 2 else "reseau")
            if s["termine"]:
                break
        self.assertTrue(s["termine"] or s["coups"] > 0)

    def test_importance_covers_all_96_hidden_neurons(self):
        data = self.lab.importance("tictactoe")
        self.assertEqual(len(data["neurones"]), 96)
        self.assertTrue(all(0 <= n["sensibilite"] <= 1 for n in data["neurones"]))
        self.assertEqual({n["couche"] for n in data["neurones"]}, {"encodeur", "coeur"})

    def test_prune_curve_starts_from_the_full_network(self):
        c = self.lab.prune_curve("tictactoe")
        self.assertEqual(c["courbe"][0]["eteints"], 0)
        self.assertEqual(c["courbe"][0]["accord"], 1.0)
        self.assertEqual(c["courbe"][0]["parametres"], c["pleine"])
        params = [p["parametres"] for p in c["courbe"]]
        self.assertEqual(params, sorted(params, reverse=True))

    def test_invalid_requests_are_refused_with_400(self):
        for method, path, query, body in (("POST", "/api/lab/new", {}, {"game": "echecs"}), ("POST", "/api/lab/new", {}, {"game": "nim", "seed": -1}),
                                          ("POST", "/api/lab/mute", {}, {"layer": "sortie", "index": 0}), ("POST", "/api/lab/mute", {}, {"layer": "coeur", "index": 99}),
                                          ("GET", "/api/lab/importance", {"game": ["xx"]}, {}), ("POST", "/api/lab/step", {}, {"mode": "triche"})):
            status, payload = handle(method, path, query, body)
            self.assertEqual(status, 400, (path, body))
            self.assertFalse(payload["ok"])
        self.assertEqual(handle("GET", "/api/lab/inconnu", {}, {})[0], 404)


if __name__ == "__main__":
    unittest.main()

"""Le moteur de dames C++/Python doit reproduire exactement le moteur TypeScript de multi sur 40 parties aléatoires
(fixture générée par un export de `packages/engines/src/games/dames`) : mêmes coups légaux à chaque demi-coup, même issue."""
import json
import unittest
from pathlib import Path

from logic_arena.zero import dames

FIXTURE = Path(__file__).parent / "fixtures" / "dames-playouts.json"


class DamesParityTest(unittest.TestCase):
    def test_same_moves_and_outcomes_as_typescript(self):
        games = json.loads(FIXTURE.read_text(encoding="utf-8"))
        plies = 0
        for gi, game in enumerate(games):
            state = dames.State.new()
            for pi, ply in enumerate(game["plies"]):
                self.assertEqual(state.cells, ply["cells"], f"partie {gi} coup {pi}: plateau")
                self.assertEqual(state.next, ply["next"])
                mine = sorted(state.moves())
                theirs = sorted(tuple(p) for p in ply["moves"])
                self.assertEqual([m[0] for m in mine], theirs, f"partie {gi} coup {pi}: coups légaux")
                chosen = tuple(ply["chosen"])
                path, caps = next(m for m in state.moves() if m[0] == chosen)
                self.assertEqual(sorted(caps), sorted(ply["captures"]), f"partie {gi} coup {pi}: prises")
                state = state.advance(path, caps)
                plies += 1
            self.assertEqual(state.status, game["status"], f"partie {gi}")
            self.assertEqual(state.winner, game["winner"], f"partie {gi}")
            self.assertEqual(state.cells, game["cells"], f"partie {gi}")
        self.assertGreater(plies, 1000)



class DamesBotPortTest(unittest.TestCase):
    """La recherche C++ en mode 0 doit choisir le même coup que le bot TypeScript de multi (niveaux normal et difficile)."""

    def test_mode0_matches_typescript_bot(self):
        rows = json.loads((Path(__file__).parent / "fixtures" / "dames-bot-choices.json").read_text(encoding="utf-8"))
        same = 0
        for r in rows:
            depth, budget = (4, 2000) if r["difficulty"] == "normal" else (7, 20000)
            move, _ = dames.search(r["cells"], r["next"], 0, depth, budget, 0)
            if move is not None and r["path"] is not None and list(move[0]) == r["path"]:
                same += 1
        self.assertGreaterEqual(same / len(rows), 0.97, f"{same}/{len(rows)} coups identiques")


if __name__ == "__main__":
    unittest.main()

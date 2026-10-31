"""L'extension de Garry aux dames ne doit changer aucune sortie des autres jeux (même avec des unités cachées ajoutées)."""
import unittest
from pathlib import Path

import numpy as np

from logic_arena.games import make_game
from logic_arena.garry_dames import GarryDames, dames_features, dames_features_batch
from logic_arena.general import GAMES, OUTPUT_OFFSETS, SPECS, GarryPolicy
from logic_arena.zero import dames

MODEL = Path(__file__).resolve().parents[1] / "web" / "models" / "garry.json"


class GarryDamesTest(unittest.TestCase):
    def test_old_games_unchanged(self):
        base = GarryPolicy.load(MODEL)
        for extra in (0, 32):
            ext = GarryDames(base, extra_hidden=extra, seed=3)
            for game in GAMES:
                env = make_game(game, 5, None)
                for _ in range(6):
                    obs, legal = env.observation(), env.legal_actions()
                    if env.done or not legal:
                        break
                    start = OUTPUT_OFFSETS[game]
                    expected = base.logits(obs)[start:start + SPECS[game][1]]
                    np.testing.assert_allclose(ext.old_game_logits(obs), expected, atol=1e-5, err_msg=f"{game} extra={extra}")
                    env.step(legal[0])

    def test_dames_features_batch_matches_single(self):
        state = dames.State.new()
        rng = np.random.default_rng(0)
        for _ in range(30):
            moves = state.moves()
            if not moves:
                break
            np.testing.assert_array_equal(dames_features(state.cells, state.next, state.quiet),
                                          dames_features_batch([state.cells], [state.next], [state.quiet])[0])
            state = state.advance(*moves[int(rng.integers(len(moves)))])


if __name__ == "__main__":
    unittest.main()

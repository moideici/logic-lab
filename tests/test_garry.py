import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

from logic_arena.general import GarryPolicy, INPUT, OUTPUT, general_encode
from logic_arena.games import make_game
from logic_arena.migration import LEGACY_GAMES
from logic_arena.neural import NeuralPolicy, NeuralSuite, SPECS, action_index, encode

ROOT=Path(__file__).resolve().parents[1]


class GarryTests(unittest.TestCase):
    def test_one_model_preserves_six_old_policies_and_legal_actions(self):
        originals={g:NeuralPolicy.load(ROOT/'versions/1.0.0/web/models'/f'{g}.json') for g in LEGACY_GAMES}
        general=GarryPolicy.fuse(originals)
        self.assertEqual((INPUT,OUTPUT),(4872,4259))
        for g in LEGACY_GAMES:
            old=originals[g]
            env=make_game(g,42)
            for _ in range(12):
                if env.done:break
                obs=env.observation();legal=env.legal_actions();view=general.for_game(g)
                np.testing.assert_allclose(view.logits(obs),old.logits(obs),atol=3e-5,rtol=1e-5)
                self.assertIn(view.choose(obs,legal),legal)
                self.assertIn(general.choose(obs,legal),legal)
                self.assertEqual(general_encode(obs).shape,(INPUT,))
                env.step(env.rng.choice(legal))

    def test_training_changes_one_shared_encoder_and_exports_one_file(self):
        suite=NeuralSuite.load();general=suite.general
        self.assertTrue(all(v.model is general for v in suite.models.values()))
        env=make_game('tictactoe');env.step({'row':0,'col':0});obs=env.observation()
        other=make_game('connect4');other.step({'column':3})
        before=suite.models['connect4'].logits(other.observation()).copy()
        targets=np.array([4]);mask=np.zeros((1,9),dtype=bool)
        mask[0,[action_index('tictactoe',a) for a in env.legal_actions()]]=True
        losses=suite.models['tictactoe'].fit(encode(obs)[None,:],targets,mask,epochs=20)
        self.assertLess(losses[-1],losses[0])
        self.assertFalse(np.array_equal(before,suite.models['connect4'].logits(other.observation())))
        with tempfile.TemporaryDirectory() as d:
            suite.save(d)
            self.assertEqual([p.name for p in Path(d).iterdir()],['garry.json'])
            restored=NeuralSuite.load(d)
            np.testing.assert_array_equal(restored.general.w1,general.w1)
            np.testing.assert_array_equal(restored.general.w2,general.w2)

    def test_rejects_incompatible_or_corrupted_unified_artifacts(self):
        data=json.loads((ROOT/'web/models/garry.json').read_text())
        for key,bad in [('input',897),('output',730),('hidden',0),('games',[])]:
            with self.assertRaises(ValueError):GarryPolicy.from_dict({**data,key:bad})
        data['w1'][0]=float('nan')
        with self.assertRaises(ValueError):GarryPolicy.from_dict(data)

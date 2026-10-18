import copy
import unittest
from pathlib import Path
import numpy as np
from logic_arena.general import GarryPolicy
from logic_arena.games import make_game
from logic_arena.identity import AGENT_VERSION

ROOT=Path(__file__).resolve().parents[1]

class VersionAliasTests(unittest.TestCase):
 def test_previous_version_alias_preserves_weights_and_public_predictions(self):
  model=GarryPolicy.load(ROOT/'web/models/garry.json')
  data=model.export();data['version']='6.0.0';before=copy.deepcopy(data)
  restored=GarryPolicy.from_dict(data)
  self.assertEqual(AGENT_VERSION,'0.6.0')
  self.assertEqual(restored.export()['version'],'0.6.0')
  self.assertEqual(data,before)
  for key in ('w1','w2','b1','b2'):np.testing.assert_array_equal(getattr(model,key),getattr(restored,key))
  for game in ('go','sudoku','sliding_puzzle'):
   obs=make_game(game,42).observation()
   np.testing.assert_array_equal(model.logits(obs),restored.logits(obs))
  with self.assertRaises(ValueError):GarryPolicy.from_dict({**data,'version':'0.7.0'})
  with self.assertRaises(ValueError):GarryPolicy.from_dict({**data,'input':data['input']-1,'version':'0.6.0'})

if __name__=='__main__':unittest.main()

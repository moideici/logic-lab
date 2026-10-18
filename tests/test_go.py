import unittest,random,json
from copy import deepcopy
from pathlib import Path
import numpy as np
from logic_arena.games import make_game
from logic_arena.go_rules import group,board_key,play_candidate,area_score,encode_go,go_action_index
from logic_arena.go_planner import go_values
from logic_arena.agents import Budget
from logic_arena.general import GarryPolicy,FEATURES
ROOT=Path(__file__).resolve().parents[1]
def fixture(stones,player=1):
 e=make_game('go',0,{'size':9})
 for r,c,v in stones:e.board[r][c]=v
 e.current_player=player;e.go_state['seen']=[board_key(e.board)];return e
class GoTests(unittest.TestCase):
 def test_sizes_options_and_default_real_board(self):
  self.assertEqual(len(make_game('go').board),19)
  for n in (9,13,19):
   e=make_game('go',0,{'size':n});self.assertEqual(len(e.legal_actions()),n*n+2);self.assertEqual(len(encode_go(e.observation())),1816);self.assertEqual(len(set(go_action_index(a) for a in e.legal_actions())),n*n+2)
  for options in ({'size':8},{'size':True},{'komi':float('nan')},{'komi':True}):
   with self.assertRaises(ValueError):make_game('go',0,options)
 def test_capture_multistone_group_and_suicide(self):
  e=fixture([(1,1,2),(1,2,2),(0,1,1),(0,2,1),(1,0,1),(1,3,1),(2,1,1)]);e.step({'row':2,'col':2});self.assertEqual(e.board[1][1:3],[0,0]);self.assertEqual(e.go_state['captures'],[2,0])
  e=fixture([(0,1,2),(1,0,2),(1,2,2),(2,1,2)]);self.assertNotIn({'row':1,'col':1},e.legal_actions());before=e.observation()
  with self.assertRaises(ValueError):e.step({'row':1,'col':1})
  self.assertEqual(before,e.observation())
 def test_capture_inside_surrounded_point_is_not_suicide(self):
  e=fixture([(0,1,2),(1,0,2),(1,2,2),(2,1,2),(0,0,1),(0,2,1),(2,0,1),(2,2,1),(1,3,1),(3,1,1)]);self.assertIn({'row':1,'col':1},e.legal_actions());e.step({'row':1,'col':1});self.assertGreater(e.go_state['captures'][0],0)
 def test_ko_and_older_superko_positions_are_forbidden(self):
  e=fixture([(1,1,2),(0,1,1),(1,0,1),(2,1,1),(0,2,2),(2,2,2),(1,3,2)]);e.step({'row':1,'col':2});self.assertNotIn({'row':1,'col':1},e.legal_actions());self.assertIn({'pass':True},e.legal_actions())
  e=make_game('go',0,{'size':9});candidate=play_candidate(e.board,1,4,4,set())[2];e.go_state['seen']=[candidate,board_key(e.board)];self.assertNotIn({'row':4,'col':4},e.legal_actions())
 def test_two_passes_require_agreement_not_premature_end(self):
  e=make_game('go',0,{'size':9});e.step({'pass':True});e.step({'pass':True});self.assertFalse(e.done);self.assertEqual(e.go_state['phase'],'scoring');e.step({'accept':True});self.assertFalse(e.done);e.step({'accept':True});self.assertTrue(e.done);self.assertEqual(e.winner,2);self.assertEqual(e.go_state['final_score']['white'],7.5)
 def test_dead_group_changes_entire_group_resets_agreement_and_resumes(self):
  e=fixture([(1,1,1),(1,2,1),(5,5,2)]);e.step({'pass':True});e.step({'pass':True});e.step({'accept':True});e.step({'dead':[1,1]});self.assertEqual(e.go_state['dead'],[10,11]);self.assertEqual(e.go_state['accepted'],[]);e.step({'dead':[1,2]});self.assertEqual(e.go_state['dead'],[]);e.step({'resume':True});self.assertEqual(e.go_state['phase'],'play');self.assertEqual(e.current_player,1);self.assertEqual(e.go_state['passes'],0)
 def test_area_score_neutral_regions_and_marked_stones(self):
  e=fixture([(r,c,1) for r in range(9) for c in range(9) if (r,c)!=(4,4)]);s=area_score(e.board,e.go_state);self.assertEqual(s['black'],81);self.assertEqual(s['white'],7.5)
  e=fixture([(0,0,1),(8,8,2)]);s=area_score(e.board,e.go_state);self.assertEqual(s['black'],1);self.assertEqual(s['white'],8.5)
 def test_no_live_group_in_random_legal_games_has_zero_liberties(self):
  rng=random.Random(42)
  for _ in range(3):
   e=make_game('go',0,{'size':9})
   for step in range(100):
    legal=[a for a in e.legal_actions() if 'row'in a]
    if not legal:break
    e.step(rng.choice(legal));checked=set()
    for r,row in enumerate(e.board):
     for c,v in enumerate(row):
      if v and (r,c) not in checked:stones,libs=group(e.board,r,c);checked|=stones;self.assertTrue(libs)
 def test_tactical_capture_survives_zero_search_budget(self):
  e=fixture([(1,1,2),(0,1,1),(1,0,1),(2,1,1)]);o=e.observation();v,info=go_values(o,e.legal_actions(),Budget(0,0));a=max(v,key=lambda v:v['quality'])['action'];self.assertEqual(a,{'row':1,'col':2});self.assertEqual(o,e.observation());self.assertFalse(info['analysis_exact'])
 def test_resign_and_final_legal_actions(self):
  e=make_game('go');e.step({'resign':True});self.assertTrue(e.done);self.assertEqual(e.winner,2);self.assertEqual(e.legal_actions(),[])
 def test_import_previous_thirteen_games_preserves_weights(self):
  old=json.loads((ROOT/'versions/5.0.0/garry.json').read_text());m=GarryPolicy.from_dict(old);h=old['hidden'];w=np.asarray(old['w1'],np.float32).reshape(3055,h);np.testing.assert_array_equal(m.w1[:3042],w[:3042]);np.testing.assert_array_equal(m.w1[FEATURES:FEATURES+13],w[3042:]);np.testing.assert_array_equal(m.w2[:,:3894],np.asarray(old['w2'],np.float32).reshape(h,3894));self.assertEqual(m.search_memory,old['search_memory'])
if __name__=='__main__':unittest.main()

import json,random,tempfile,unittest
from pathlib import Path
import numpy as np
from logic_arena.games import make_game
from logic_arena.puzzle_levels import LEVELS,sudoku_bank
from logic_arena.diversity import sudoku_solutions
from logic_arena.planner import sliding_distance
from logic_arena.large_sliding import large_sliding_values
from logic_arena.agents import Budget,ReferenceAgent
from logic_arena.neural import encode
from logic_arena.general import GarryPolicy,FEATURES
from logic_arena.hex_rules import connection_path
from logic_arena.gomoku_rules import exact_five
from logic_arena.external import ExternalArena
ROOT=Path(__file__).resolve().parents[1]
class ExpansionTests(unittest.TestCase):
 def test_hex_swap_changes_ownership_and_next_player(self):
  e=make_game('hex');e.step({'row':3,'col':3});self.assertIn({'swap':True},e.legal_actions());before=[r[:] for r in e.board];e.step({'swap':True});self.assertEqual(e.board,before);self.assertEqual(e.hex_state['colors'],[2,1]);self.assertEqual(e.current_player,1);self.assertNotIn({'swap':True},e.legal_actions());e.step({'row':0,'col':0});self.assertEqual(e.board[0][0],2)
 def test_hex_path_and_full_boards_have_one_winner(self):
  rng=random.Random(123)
  for _ in range(100):
   b=[[rng.choice((1,2)) for _ in range(7)] for _ in range(7)];self.assertEqual(sum(bool(connection_path(b,c)) for c in (1,2)),1)
  e=make_game('hex');e.board=[[0]*7 for _ in range(7)]
  for r in range(6):e.board[r][2]=1
  e.step({'row':6,'col':2});self.assertEqual(e.winner,1);self.assertEqual(len(e.hex_state['winning_path']),7);self.assertEqual(e.legal_actions(),[])
 def test_swap2_direct_choice_and_extension(self):
  for extend in (False,True):
   e=make_game('gomoku')
   for i in range(3):self.assertEqual(e.current_player,1);e.step({'row':7,'col':i})
   self.assertEqual(e.current_player,2);self.assertEqual(e.gomoku_state['phase'],'choose_or_extend')
   if extend:
    for i in (3,4):self.assertEqual(e.current_player,2);e.step({'row':7,'col':i})
    self.assertEqual(e.current_player,1);self.assertEqual(e.gomoku_state['phase'],'choose_color');self.assertEqual(len(e.legal_actions()),2)
   chooser=e.current_player;e.step({'choose':'black'});self.assertEqual(e.gomoku_state['colors'][chooser-1],1);self.assertEqual(e.current_player,3-chooser)
 def test_gomoku_exact_five_and_overline(self):
  for length in (5,6):
   b=[[0]*15 for _ in range(15)];b[7][2:2+length]=[1]*length;self.assertEqual(bool(exact_five(b,7,4,1)),length==5)
 def test_sudoku_catalog_has_unique_solutions_and_expert_is_record(self):
  bank=sudoku_bank();entries=[x for group in bank['levels'].values() for x in group]
  for entry in entries:
   b=[[int(v) for v in entry['puzzle'][r*9:(r+1)*9]] for r in range(9)];answers,_=sudoku_solutions(b,2,200000);self.assertEqual(len(answers),1)
  self.assertTrue(all(x['grade']['score']==max(e['grade']['score'] for e in entries) for x in bank['levels']['expert']))
 def test_sliding_all_sizes_difficulties_are_solvable_permutations(self):
  for n in (3,4,5):
   for difficulty in LEVELS:
    e=make_game('sliding_puzzle',171,{'size':n,'difficulty':difficulty});f=sum(e.board,[]);self.assertEqual(sorted(f),list(range(n*n)));v=[x for x in f if x];inv=sum(a>b for i,a in enumerate(v) for b in v[i+1:]);self.assertEqual(inv%2 if n%2 else (inv+n-f.index(0)//n)%2,0 if n%2 else 1);self.assertEqual(len(encode(e.observation())),81);self.assertTrue(np.isfinite(encode(e.observation())).all())
    if n==3 and difficulty=='expert':self.assertEqual(sliding_distance(e.board),31)
 def test_large_easy_solves_from_public_board_alone(self):
  for n in (4,5):
   e=make_game('sliding_puzzle',171,{'size':n,'difficulty':'easy'});before=e.observation();values,info=large_sliding_values(before,e.legal_actions(),Budget(100000,10000));self.assertTrue(info['solution_found']);self.assertTrue(info['optimal']);self.assertFalse(info['analysis_exact']);self.assertEqual(e.observation(),before)
   length=info['remaining_moves']
   for _ in range(length):
    values,info=large_sliding_values(e.observation(),e.legal_actions(),Budget(100000,10000));e.step(max(values,key=lambda x:x['quality'])['action'])
   self.assertTrue(e.done);self.assertEqual(e.moves,length)
 def test_large_teacher_returns_action_even_without_budget(self):
  e=make_game('sliding_puzzle',3,{'size':5,'difficulty':'expert'});a=ReferenceAgent(10).sliding(e.observation(),e.legal_actions(),Budget(0,0),e.legal_actions()[0]);self.assertIn(a,e.legal_actions())
 def test_options_reject_unsupported_sizes_and_difficulties(self):
  for name,options in [('sliding_puzzle',{'size':6}),('sliding_puzzle',{'size':True}),('sudoku',{'difficulty':'impossible'}),('sliding_puzzle',{'size':4,'scramble':10})]:
   with self.assertRaises(ValueError):make_game(name,0,options)
 def test_migration_preserves_all_eleven_previous_modes(self):
  old=json.loads((ROOT/'versions/4.0.0/garry.json').read_text());new=GarryPolicy.from_dict(old);h=old['hidden'];w=np.asarray(old['w1'],dtype=np.float32).reshape(2494,h);np.testing.assert_array_equal(new.w1[:2483],w[:2483]);np.testing.assert_array_equal(new.w1[FEATURES:FEATURES+11],w[2483:]);np.testing.assert_array_equal(new.w2[:,:3617],np.asarray(old['w2'],dtype=np.float32).reshape(h,3617));self.assertEqual(new.search_memory,old['search_memory'])
 def test_external_config_and_path_validation(self):
  with tempfile.TemporaryDirectory() as d:
   arena=ExternalArena(d)
   for identifier in ('../outside','',None):
    with self.assertRaises(ValueError):arena.get(identifier)
   for config in ({'game':'chess'},{'mode':'shell'},{'max_steps':True},{'url':'https://example.com'}):
    with self.assertRaises(ValueError):arena.start(config)
if __name__=='__main__':unittest.main()

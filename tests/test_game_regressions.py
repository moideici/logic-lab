import unittest,random
import numpy as np
from logic_arena.games import make_game
from logic_arena.sudoku_rules import solve_sudoku
from logic_arena.planner import plan,sliding_distance
from logic_arena.go_ai_policy import go_ai_actions
class GameRegressions(unittest.TestCase):
 def test_sudoku_three_lives_and_hidden_judge(self):
  e=make_game('sudoku',42,{'error_limit':3});answer=solve_sudoku(e.board,limit=1)[0][0]
  for i in range(3):
   a=next(a for a in e.legal_actions() if a['value']!=answer[a['row']][a['col']]);before=[r[:] for r in e.board];e.step(a);self.assertEqual(e.board,before);self.assertEqual(e.sudoku_state['errors'],i+1);self.assertNotIn(a,e.legal_actions());self.assertEqual(e.done,i==2)
  self.assertEqual(e.winner,0);self.assertNotIn('_answer',e.observation())
 def test_sudoku_levels_end_and_ten_solves(self):
  for difficulty in ('easy','medium','hard','expert'):
   for level in (0,5,10):
    e=make_game('sudoku',42,{'difficulty':difficulty,'error_limit':3});rng=random.Random(42)
    while not e.done and e.moves<100:
     legal=e.legal_actions();a,_=plan(e.observation(),legal,None,level,legal[0],logits=np.zeros(730),rng=rng);e.step(a)
    self.assertTrue(e.done,(difficulty,level))
    if level==10:self.assertEqual(e.winner,1,difficulty);self.assertEqual(e.sudoku_state['errors'],0)
 def test_go_automatic_end_and_human_pass(self):
  for level in (0,5,10):
   e=make_game('go',0,{'size':9});self.assertIn({'pass':True},e.legal_actions())
   while not e.done and e.moves<167:
    legal=go_ai_actions(e.observation(),e.legal_actions());e.step(legal[round(level*(len(legal)-1)/10)])
   self.assertTrue(e.done);self.assertLessEqual(e.moves,166)
 def test_taquin_trajectories_progress(self):
  means=[]
  for level in (1,5,9,10):
   moves=[]
   for seed in range(10):
    e=make_game('sliding_puzzle',seed,{'size':3,'difficulty':'expert'});rng=random.Random(seed)
    while not e.done and e.moves<2000:
     legal=e.legal_actions();a,_=plan(e.observation(),legal,None,level,legal[0],logits=np.zeros(4),rng=rng);e.step(a)
    self.assertTrue(e.done)
    if level==10:self.assertEqual(e.moves,31)
    moves.append(e.moves)
   means.append(sum(moves)/len(moves))
  self.assertEqual(means,sorted(means,reverse=True));self.assertEqual(len(set(means)),4)

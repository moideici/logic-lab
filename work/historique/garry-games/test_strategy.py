import unittest,random,json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import numpy as np
from logic_arena.games import make_game
from logic_arena.strategy_rules import owner,new_state,legal_strategy,position_key
from logic_arena.strategy_planner import strategy_values
from logic_arena.agents import Budget
from logic_arena.general import GarryPolicy,FEATURES
from logic_arena.neural import encode,action_index

def fixture(pieces,player=1):
    env=make_game('draughts');env.board=[[0]*10 for _ in range(10)]
    for r,c,v in pieces:env.board[r][c]=v
    env.current_player=player;env.draughts_state=new_state(env.board,player);return env

@lru_cache(None)
def race_oracle(flat,p):
    # Independent two-piece/pawn race game tree; no production rules called.
    n=8;dr=-1 if p==1 else 1;options=[]
    for i,v in enumerate(flat):
        if v!=p:continue
        r,c=divmod(i,8)
        for dc in (-1,0,1):
            y,x=r+dr,c+dc
            if not 0<=y<8 or not 0<=x<8:continue
            target=flat[y*8+x]
            if target and (not dc or target==p):continue
            b=list(flat);b[i]=0;b[y*8+x]=p
            value=1 if y==(0 if p==1 else 7) or 3-p not in b else -race_oracle(tuple(b),3-p)
            options.append(value)
    return max(options) if options else -1

class StrategyTests(unittest.TestCase):
    def test_initial_positions_and_action_indices_are_unique(self):
        for name,total in (('draughts',40),('breakthrough',32)):
            e=make_game(name);self.assertEqual(sum(bool(v) for row in e.board for v in row),total);legal=e.legal_actions();self.assertEqual(len({action_index(name,a) for a in legal}),len(legal));self.assertEqual(len(encode(e.observation())),304 if name=='draughts' else 128)
        e=make_game('draughts');self.assertEqual(len(e.legal_actions()),9);self.assertTrue(all((r+c)%2==1 for r,row in enumerate(e.board) for c,v in enumerate(row) if v))
    def test_maximum_capture_is_mandatory_and_keeps_turn_until_the_end(self):
        e=fixture([(6,1,1),(5,2,2),(3,4,2),(6,7,1),(5,8,2)])
        self.assertEqual(e.legal_actions(),[{'from':[6,1],'to':[4,3]}]);before=e.observation()
        with self.assertRaises(ValueError):e.step({'from':[6,7],'to':[4,9]})
        self.assertEqual(e.observation(),before);e.step(e.legal_actions()[0]);self.assertEqual(e.current_player,1);self.assertEqual(e.board[5][2],2);self.assertEqual(e.draughts_state['pending_captures'],[[5,2]])
        self.assertEqual(e.legal_actions(),[{'from':[4,3],'to':[2,5]}]);e.step(e.legal_actions()[0]);self.assertEqual(e.current_player,2);self.assertEqual(e.board[5][2],0);self.assertEqual(e.board[3][4],0);self.assertIsNone(e.draughts_state['forced_piece'])
    def test_backward_capture_flying_kings_and_captured_pieces_block(self):
        e=fixture([(4,3,1),(5,4,2)]);self.assertEqual(e.legal_actions(),[{'from':[4,3],'to':[6,5]}])
        e=fixture([(7,0,3),(4,3,2)]);self.assertEqual({tuple(a['to']) for a in e.legal_actions()},{(3,4),(2,5),(1,6),(0,7)})
        e=fixture([(4,3,3),(3,4,2),(5,2,2)]);self.assertIn({'from':[4,3],'to':[2,5]},e.legal_actions());e.step({'from':[4,3],'to':[2,5]});self.assertEqual(e.current_player,2);self.assertIsNone(e.draughts_state['forced_piece']);self.assertEqual(e.board[5][2],2)
    def test_promotion_occurs_only_after_the_entire_capture(self):
        e=fixture([(2,1,1),(1,2,2),(1,4,2)]);e.step({'from':[2,1],'to':[0,3]});self.assertEqual(e.board[0][3],1);self.assertEqual(e.current_player,1);e.step({'from':[0,3],'to':[2,5]});self.assertEqual(e.board[2][5],1)
        e=fixture([(2,1,1),(1,2,2)]);e.step({'from':[2,1],'to':[0,3]});self.assertEqual(e.board[0][3],3);self.assertTrue(e.done);self.assertEqual(e.winner,1)
    def test_threefold_and_move_limits_draw_but_a_win_takes_precedence(self):
        e=fixture([(9,0,3),(0,1,4)]);cycle=[([9,0],[8,1]),([0,1],[1,0]),([8,1],[9,0]),([1,0],[0,1])]
        for start,end in cycle*2:e.step({'from':start,'to':end})
        self.assertTrue(e.done);self.assertEqual(e.winner,0)
        e=fixture([(9,0,3),(9,4,3),(9,8,3),(0,1,4),(0,5,4),(0,9,4)]);e.draughts_state['quiet_plies']=49;e.step({'from':[9,4],'to':[8,3]});self.assertTrue(e.done);self.assertEqual(e.winner,0)
        e=fixture([(9,0,3),(0,1,4)]);e.draughts_state['endgame_5']=9;e.step({'from':[9,0],'to':[8,1]});self.assertTrue(e.done);self.assertEqual(e.winner,0)
        e=fixture([(4,3,3),(3,4,4)]);e.draughts_state['endgame_5']=9;e.step({'from':[4,3],'to':[2,5]});self.assertTrue(e.done);self.assertEqual(e.winner,1)
    def test_breakthrough_cannot_capture_straight_and_wins_on_the_back_rank(self):
        e=make_game('breakthrough');e.board=[[0]*8 for _ in range(8)];e.board[3][3]=1;e.board[2][3]=2;e.board[2][4]=2
        self.assertNotIn({'from':[3,3],'to':[2,3]},e.legal_actions());self.assertIn({'from':[3,3],'to':[2,4]},e.legal_actions());self.assertIn({'from':[3,3],'to':[2,2]},e.legal_actions())
        e.board=[[0]*8 for _ in range(8)];e.board[1][2]=1;e.board[5][5]=2;e.step({'from':[1,2],'to':[0,2]});self.assertTrue(e.done);self.assertEqual(e.winner,1)
    def test_pawn_race_search_matches_an_independent_exact_oracle(self):
        rng=random.Random(1710711)
        for sample in range(16):
            e=make_game('breakthrough');e.board=[[0]*8 for _ in range(8)];e.board[rng.randrange(1,4)][rng.randrange(8)]=1;e.board[rng.randrange(4,7)][rng.randrange(8)]=2;e.current_player=1+sample%2
            expected=race_oracle(tuple(v for row in e.board for v in row),e.current_player);values,info=strategy_values(e.observation(),e.legal_actions(),Budget(2000000,10000),max_depth=12)
            self.assertTrue(info['analysis_exact']);self.assertEqual(max(v['quality'][0] for v in values),expected*100000)
    def test_search_does_not_modify_capture_state_and_respects_the_budget(self):
        e=fixture([(6,1,1),(5,2,2),(3,4,2),(6,7,1),(5,8,2)]);e.step(e.legal_actions()[0]);before=e.observation();values,info=strategy_values(before,e.legal_actions(),Budget(0,1000));self.assertEqual(info['depth'],0);self.assertEqual(e.observation(),before);self.assertEqual(values[0]['action'],e.legal_actions()[0])
    def test_all_nine_prior_modes_are_preserved_after_strategy_training(self):
        root=Path(__file__).resolve().parents[1];nine=GarryPolicy.load(root/'training/new-games-4.0.0/nine-game-bootstrap.json');now=GarryPolicy.load(root/'web/models/garry.json')
        np.testing.assert_array_equal(now.w1[:2051],nine.w1[:2051]);np.testing.assert_array_equal(now.w1[FEATURES:FEATURES+9],nine.w1[FEATURES:FEATURES+9]);np.testing.assert_array_equal(now.w2[:,:925],nine.w2[:,:925]);np.testing.assert_array_equal(now.b1,nine.b1)
        for name in ('draughts','breakthrough'):self.assertGreater(now.game_steps[name],0)

if __name__=='__main__':unittest.main()

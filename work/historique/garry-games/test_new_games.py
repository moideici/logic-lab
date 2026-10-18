import json,random,unittest
from pathlib import Path
from copy import deepcopy
import numpy as np
from logic_arena.games import make_game
from logic_arena.general import GarryPolicy,FEATURES
from logic_arena.neural import action_index,encode
from logic_arena.extra_rules import flip_lights,reversi_flips
from logic_arena.extra_planner import nim_value,light_solutions,extra_values
from logic_arena.agents import Budget
from logic_arena.planner import plan
ROOT=Path(__file__).resolve().parents[1]

def chase_lights(board):
    # Independent row-chasing oracle: only 32 possible first rows.
    solutions=[]
    for mask in range(32):
        b=deepcopy(board);presses=[]
        def press(r,c):
            presses.append((r,c))
            for y,x in ((r,c),(r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if 0<=y<5 and 0<=x<5:b[y][x]^=1
        for c in range(5):
            if mask>>c&1:press(0,c)
        for r in range(1,5):
            for c in range(5):
                if b[r-1][c]:press(r,c)
        if not any(b[-1]):solutions.append(presses)
    return min(map(len,solutions))

class NewGamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.model=GarryPolicy.load(ROOT/'web/models/garry.json')
    def test_nim_every_heap_configuration_matches_independent_xor_theorem(self):
        for a in range(16):
            for b in range(16):
                for c in range(16):self.assertEqual(nim_value((a,b,c))[0],1 if a^b^c else -1)
    def test_nim_legal_actions_turns_terminal_and_invalid_types(self):
        env=make_game('nim');env.board=[[1]+[0]*14,[0]*15,[0]*15]
        self.assertEqual(env.legal_actions(),[{'pile':0,'take':1}])
        for bad in ({'pile':0,'take':True},{'pile':-1,'take':1},{'pile':1,'take':1}):
            with self.assertRaises(ValueError):env.step(bad)
        self.assertEqual(env.moves,0);env.step({'pile':0,'take':1});self.assertEqual(env.winner,1);self.assertEqual(env.legal_actions(),[])
    def test_lights_out_is_solvable_and_shortest_against_row_chasing(self):
        for seed in range(60):
            env=make_game('lightsout',seed);distance=chase_lights(env.board)
            self.assertEqual(light_solutions(env.board)[0].bit_count(),distance)
            for _ in range(distance):
                legal=env.legal_actions();a,info=plan(env.observation(),legal,self.model.for_game('lightsout'),10,legal[0]);env.step(a)
            self.assertTrue(env.done);self.assertEqual(env.winner,1);self.assertEqual(env.moves,distance);self.assertEqual(env.score,25)
    def test_reversi_captures_eight_rays_passes_and_counts_final_discs(self):
        board=[[0]*6 for _ in range(6)]
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr or dc:board[2+dr][2+dc]=2;board[2+2*dr][2+2*dc]=1
        env=make_game('reversi');env.board=board;self.assertEqual(len(reversi_flips(board,1,2,2)),8);env.step({'row':2,'col':2})
        self.assertEqual(sum(v==2 for row in env.board for v in row),0);self.assertTrue(env.done);self.assertEqual(env.winner,1)
        env=make_game('reversi');env.board=[[1]*6 for _ in range(6)];env.board[0][0]=0;env.board[0][1]=2;env.current_player=2
        self.assertEqual(env.legal_actions(),[{'pass':True}]);env.step({'pass':True});self.assertFalse(env.done);self.assertEqual(env.current_player,1)
        env.step({'row':0,'col':0});self.assertTrue(env.done);self.assertEqual(env.winner,1);self.assertEqual(env.score,36)
    def test_extra_levels_are_monotone_legal_and_leave_the_state_unchanged(self):
        for name in ('nim','lightsout','reversi'):
            env=make_game(name,42);obs=env.observation();legal=env.legal_actions();last=None
            # Fixed-depth public values avoid comparisons between different time cutoffs.
            values,info=extra_values(obs,legal,Budget(1000000,10000),max_depth=3)
            from logic_arena.quality import select_quality
            for level in range(11):
                v,meta=select_quality(values,level,np.zeros(925),name);q=tuple(v['quality']);self.assertIn(v['action'],legal)
                if last is not None:self.assertGreaterEqual(q,last)
                last=q
            self.assertEqual(obs,env.observation())
    def test_migration_preserves_all_six_game_parameters_and_knowledge(self):
        raw=json.loads((ROOT/'versions/3.2.0/garry.json').read_text());m=GarryPolicy.from_dict(raw);h=m.hidden
        np.testing.assert_array_equal(m.w1[:1906],np.asarray(raw['w1'],dtype=np.float32).reshape(1912,h)[:1906])
        np.testing.assert_array_equal(m.w1[FEATURES:FEATURES+6],np.asarray(raw['w1'],dtype=np.float32).reshape(1912,h)[1906:])
        np.testing.assert_array_equal(m.w2[:,:818],np.asarray(raw['w2'],dtype=np.float32).reshape(h,818))
        np.testing.assert_array_equal(self.model.w1[:1906],m.w1[:1906]);np.testing.assert_array_equal(self.model.w2[:,:818],m.w2[:,:818]);np.testing.assert_array_equal(self.model.b1,m.b1)
        for k in ('w','b'):np.testing.assert_array_equal(self.model.core[k],m.core[k])
        self.assertEqual(self.model.position_head,raw['position_head']);self.assertEqual(self.model.search_memory,raw['search_memory'])
        for name in ('reversi','nim','lightsout'):
            env=make_game(name,42);self.assertEqual(len(encode(env.observation())),{'reversi':72,'nim':48,'lightsout':25}[name]);self.assertGreater(self.model.game_steps[name],0)

if __name__=='__main__':unittest.main()

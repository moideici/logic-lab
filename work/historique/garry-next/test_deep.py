import json,random,unittest
from functools import lru_cache
from pathlib import Path
import numpy as np
from logic_arena.agents import Budget
from logic_arena.games import make_game
from logic_arena.connect4_wasm import search
from logic_arena.general import GarryPolicy

LINES=tuple(tuple((r+i*dr)*7+c+i*dc for i in range(4)) for r in range(6) for c in range(7) for dr,dc in ((0,1),(1,0),(1,1),(1,-1)) if r+3*dr<6 and 0<=c+3*dc<7)
def winner(b,p):return any(all(b[i]==p for i in line) for line in LINES)
@lru_cache(None)
def oracle(b,p):
    if winner(b,3-p):return -1
    moves=[c for c in range(7) if not b[c]]
    if not moves:return 0
    best=-1
    for c in moves:
        r=max(r for r in range(6) if not b[r*7+c]);child=b[:r*7+c]+(p,)+b[r*7+c+1:]
        best=max(best,-oracle(child,3-p))
        if best==1:break
    return best

class DeepSearchTests(unittest.TestCase):
    def test_wasm_endgames_and_reported_forecast_match_independent_rules(self):
        model=GarryPolicy.load(Path(__file__).resolve().parents[1]/'web/models/garry.json');rng=random.Random(108017)
        checked=0
        for seed in range(200):
            env=make_game('connect4',seed)
            # Seek varied long games without terminating them in the generator.
            for ply in range(32):
                b=tuple(v for r in env.board for v in r);options=[]
                for a in env.legal_actions():
                    c=a['column'];r=max(r for r in range(6) if not b[r*7+c]);child=b[:r*7+c]+(env.current_player,)+b[r*7+c+1:]
                    if not winner(child,env.current_player):options.append(a)
                if not options:break
                env.step(rng.choice(options))
            if env.moves<32:continue
            o=env.observation();b=tuple(v for row in env.board for v in row);p=env.current_player
            expected=oracle(b,p)
            a,info=search(o,env.legal_actions(),Budget(2000000,10000),logits=np.arange(7)*1e12,position_head=model.position_head,max_depth=20)
            env.step(a);child_value=0 if env.winner==0 else 1 if env.winner==p else -oracle(tuple(v for row in env.board for v in row),env.current_player)
            self.assertEqual(child_value,expected)
            replay=make_game('connect4');replay.board=[r[:] for r in o['board']];replay.current_player=p;replay.moves=o['moves']
            for column in info['principal_variation']:
                self.assertFalse(replay.done);self.assertIn({'column':column},replay.legal_actions());replay.step({'column':column})
            self.assertEqual(info['principal_variation'][0],a['column'])
            if info['proof']=='win':self.assertEqual(expected,1)
            elif info['proof']=='loss':self.assertEqual(expected,-1)
            elif info['proof']=='draw':self.assertEqual(expected,0)
            checked+=1
            if checked==20:break
        self.assertEqual(checked,20);oracle.cache_clear()

    def test_level_ten_reports_completed_depth_separately_from_target(self):
        from logic_arena.neural import NeuralAgent
        env=make_game('connect4');d=NeuralAgent(10,time_ms=10).choose(env.observation(),env.legal_actions())
        self.assertEqual(d.info['target_depth'],20);self.assertLessEqual(d.info['depth'],20)
        self.assertEqual(d.info['depth_target_reached'],d.info['depth']>=20)
        self.assertEqual(d.info['level_semantics'],'strongest_completed_search')

if __name__=='__main__':unittest.main()

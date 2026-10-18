import json
import random
import unittest
from functools import lru_cache
from pathlib import Path
import numpy as np
from logic_arena.agents import ReferenceAgent,Budget
from logic_arena.general import GarryPolicy
from logic_arena.neural import NeuralAgent,SPECS,action_index
from logic_arena.games import make_game
from logic_arena.planner import plan,sliding_distance
from logic_arena.quality import select_quality
from logic_arena.value import features,default_head
from logic_arena.connect4_wasm import search,_runtime

ROOT=Path(__file__).resolve().parents[1]
LINES=((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))
@lru_cache(None)
def oracle(b,p):
    if any(all(b[i]==3-p for i in line) for line in LINES):return -1,0
    free=[i for i in range(9) if not b[i]]
    if not free:return 0,0
    options=[]
    for i in free:
        v,n=oracle(b[:i]+(p,)+b[i+1:],3-p);options.append((-v,n+1))
    return max(options,key=lambda v:(v[0],v[1] if v[0]==-1 else -v[1]))

class LevelsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.model=GarryPolicy.load(ROOT/'web/models/garry.json')

    def test_every_playable_tictactoe_state_worst_and_best_match_independent_oracle(self):
        seen=set();stack=[((0,)*9,1)]
        while stack:
            board,p=stack.pop()
            if board in seen:continue
            seen.add(board)
            if any(all(board[i] and board[i]==board[line[0]] for i in line) for line in LINES) or all(board):continue
            obs={'game':'tictactoe','board':[list(board[r:r+3]) for r in (0,3,6)],'current_player':p,'done':False}
            legal=[{'row':i//3,'col':i%3} for i in range(9) if not board[i]];logits=np.arange(9,dtype=float)*1e12
            qs={}
            for a in legal:
                i=a['row']*3+a['col'];child=board[:i]+(p,)+board[i+1:];v,n=oracle(child,3-p);v=-v;n+=1
                qs[i]=(v,n if v==-1 else -n);stack.append((child,3-p))
            for level,expected in ((0,min(qs.values())),(10,max(qs.values()))):
                action,info=plan(obs,legal,None,level,legal[0],logits=logits)
                self.assertEqual(qs[action_index('tictactoe',action)],expected)
                self.assertEqual(tuple(info['quality']),expected)

    def test_all_eleven_quantiles_are_monotone_and_endpoints_cannot_explore(self):
        values=[{'action':{'column':i},'quality':[v]} for i,v in enumerate((4,-100,20,1,900,-900,5))]
        scores=[]
        for level in range(11):
            selected,info=select_quality(values,level,np.zeros(7),'connect4');scores.append(selected['quality'][0]);self.assertEqual(info['quality_rank'],int(level*6/10+.5))
        self.assertEqual(scores,sorted(scores));self.assertEqual((scores[0],scores[-1]),(-900,900))
        env=make_game('connect4');o=env.observation();legal=env.legal_actions();view=self.model.for_game('connect4')
        for style in ('balanced','exploratory','aggressive'):
            for level,index in ((0,0),(10,6)):
                self.assertEqual(view.choose(o,legal,level,style,logits=np.arange(7)),{'column':index})

    def test_public_api_accepts_zero_and_rejects_invalid_levels(self):
        from logic_arena.harness import catalog,Arena
        self.assertEqual([x['level'] for x in catalog()['levels']],list(range(11)))
        env=make_game('tictactoe')
        for agent in (NeuralAgent(0),ReferenceAgent(0)):
            d=agent.choose(env.observation(),env.legal_actions());self.assertTrue(d.info['selected_is_worst'])
        for v in (-1,11,.5,True):
            with self.assertRaises(ValueError):NeuralAgent(v)

    def test_connect4_zero_ignores_a_forced_block_but_ten_defends_even_without_nodes(self):
        env=make_game('connect4')
        for c in [6,0,6,1,5,2]:env.step({'column':c})
        _,info=search(env.observation(),env.legal_actions(),Budget(0,10000),logits=np.arange(7)*1e12,analyze=True,position_head=self.model.position_head)
        values=info['action_values'];best,_=select_quality(values,10,np.arange(7),'connect4');worst,_=select_quality(values,0,np.arange(7),'connect4')
        self.assertEqual(best['action'],{'column':3});self.assertNotEqual(worst['action'],{'column':3});self.assertEqual(worst['quality'],[-999998])
        self.assertEqual(len(values),len(env.legal_actions()))

    def test_taquin_levels_use_exact_distance_and_sudoku_worst_is_proven_bad(self):
        env=make_game('sliding_puzzle',91);obs=env.observation();d=sliding_distance(obs['board']);view=self.model.for_game(env.name)
        best,_=plan(obs,env.legal_actions(),view,10,env.legal_actions()[0]);worst,_=plan(obs,env.legal_actions(),view,0,env.legal_actions()[0])
        env.step(best);self.assertEqual(sliding_distance(env.board),d-1)
        env=make_game('sliding_puzzle',91);env.step(worst);self.assertEqual(sliding_distance(env.board),d+1)
        env=make_game('sudoku',42);view=self.model.for_game('sudoku');legal=env.legal_actions()
        _,good=plan(env.observation(),legal,view,10,legal[0],10000)
        _,bad=plan(env.observation(),legal,view,0,legal[0],10000)
        self.assertEqual(good['quality'],[1]);self.assertEqual(bad['quality'],[-2]);self.assertTrue(bad['proved']);self.assertFalse(bad['optimal'])

    def test_value_is_antisymmetric_python_wasm_and_policy_weights_are_preserved(self):
        old=GarryPolicy.load(ROOT/'versions/2.0.0/garry.json')
        for key in ('w1','b1','w2','b2'):np.testing.assert_array_equal(getattr(old,key),getattr(self.model,key))
        for key in ('w','b'):np.testing.assert_array_equal(old.core[key],self.model.core[key])
        head=self.model.position_head;head={**head,'enabled':True};store,rt=_runtime();rt['enableValue'](store,1)
        for i,v in enumerate(head['weights']):rt['setValueWeight'](store,i,float(v))
        rng=random.Random(217)
        for n in range(40):
            env=make_game('connect4',n)
            for _ in range(n%25):
                if env.done:break
                env.step(rng.choice(env.legal_actions()))
            obs=env.observation();x=features(obs);np.testing.assert_array_equal(features({**obs,'current_player':3-obs['current_player']}),-x)
            bits=[0,0,0]
            for r,row in enumerate(obs['board']):
                for c,p in enumerate(row):
                    if p:bits[p]|=1<<(c*7+5-r)
            self.assertAlmostEqual(rt['evaluateBoard'](store,bits[1],bits[2],obs['current_player']),float(x@head['weights']),delta=.501)
        # Strict validation and lossless 2.0 migration, new branch survives JSON.
        data=self.model.export();self.assertEqual(GarryPolicy.from_dict(data).position_head,head|{'enabled':self.model.position_head['enabled']})
        for value in (None,{'weights':[]}):
            with self.assertRaises(ValueError):GarryPolicy.from_dict({**data,'position_head':value})

if __name__=='__main__':unittest.main()

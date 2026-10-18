import copy,json,random,unittest
from pathlib import Path
from logic_arena.games import make_game
from logic_arena.agents import Budget
from logic_arena.general import GarryPolicy
from logic_arena.connect4_wasm import _runtime,search
from logic_arena.search_memory import validate_memory,memory_key,lookup_memory,empty_memory
from tests.test_deep import oracle,winner

ROOT=Path(__file__).resolve().parents[1]
def bits(obs):
    out=[0,0,0]
    for r,row in enumerate(obs['board']):
        for c,p in enumerate(row):
            if p:out[p]|=1<<(c*7+5-r)
    return out

class CertifiedSearchTests(unittest.TestCase):
    def test_exact_outcomes_and_selected_moves_match_200_independent_endgames(self):
        store,rt=_runtime();rng=random.Random(170017);checked=0;outcomes=set()
        for seed in range(1000):
            env=make_game('connect4',seed)
            for ply in range(28+seed%7):
                b=tuple(v for row in env.board for v in row);options=[]
                for a in env.legal_actions():
                    c=a['column'];r=max(r for r in range(6) if not b[r*7+c]);child=b[:r*7+c]+(env.current_player,)+b[r*7+c+1:]
                    if not winner(child,env.current_player):options.append(a)
                if not options:break
                env.step(rng.choice(options))
            if env.moves<28:continue
            o=env.observation();b=tuple(v for row in env.board for v in row);p=env.current_player;expected=oracle(b,p);bb=bits(o)
            c=rt['certify'](store,bb[1],bb[2],p,10000000,5000.);state=rt['getProofState'](store)
            self.assertEqual({2:1,3:0,4:-1}.get(state),expected);outcomes.add(expected)
            env.step({'column':c});actual=1 if env.winner==p else 0 if env.winner==0 else -oracle(tuple(v for row in env.board for v in row),env.current_player)
            self.assertEqual(actual,expected)
            checked+=1
            if checked==200:break
        self.assertEqual(checked,200);self.assertEqual(outcomes,{-1,0,1});oracle.cache_clear()

    def test_exhausted_probe_does_not_reuse_a_previous_certificate(self):
        store,rt=_runtime();env=make_game('connect4')
        for c in [0,1,4,1,1,0,5,1,6,5,2,3,5,6]:env.step({'column':c})
        bb=bits(env.observation());rt['certify'](store,bb[1],bb[2],env.current_player,0,1000.)
        self.assertEqual(rt['getProofState'](store),0);self.assertEqual(rt['getProofNodes'](store),0)
        _,info=search(env.observation(),env.legal_actions(),Budget(0,1000))
        self.assertIsNone(info['proof']);self.assertFalse(info['outcome_proven']);self.assertFalse(info['search_complete'])

    def test_memory_roundtrip_mirror_and_experience_is_not_a_proof(self):
        model=GarryPolicy.load(ROOT/'web/models/garry.json');restored=GarryPolicy.from_dict(model.export())
        self.assertEqual(model.search_memory,restored.search_memory)
        env=make_game('connect4');env.step({'column':3})
        action,info=search(env.observation(),env.legal_actions(),Budget(0,1000),search_memory=model.search_memory)
        self.assertEqual(action,{'column':2});self.assertIsNone(info['proof']);self.assertFalse(info['certified_non_loss'])
        env.step(action);env.step({'column':3});obs=env.observation();entry=lookup_memory(obs,env.legal_actions(),model.search_memory)
        self.assertIsNotNone(entry);self.assertEqual(entry['guarantee'],'non_loss')
        mirror={**obs,'board':[row[::-1] for row in obs['board']]}
        other=lookup_memory(mirror,env.legal_actions(),model.search_memory)
        self.assertEqual(entry['column'],6-other['column']);self.assertEqual(memory_key(obs)[0],memory_key(mirror)[0])
        _,info=search(obs,env.legal_actions(),Budget(0,1000),search_memory=model.search_memory)
        self.assertEqual(info['proof'],'non_loss');self.assertFalse(info['search_complete']);self.assertTrue(info['certified_non_loss'])

    def test_memory_validation_rejects_illegal_columns_duplicates_and_false_tags(self):
        self.assertEqual(validate_memory(empty_memory()),empty_memory())
        e={'key':'0000000200000','column':2,'guarantee':'experience'}
        for entries in ([e,e],[{**e,'column':7}],[{**e,'column':True}],[{**e,'guarantee':'perfect'}],[{**e,'key':'fffffffffffff'}],[{**e,'key':'000000000003f','column':0}]):
            with self.assertRaises(ValueError):validate_memory({**empty_memory(),'entries':entries})
        old=json.loads((ROOT/'versions/3.1.0/garry.json').read_text());self.assertEqual(GarryPolicy.from_dict(old).search_memory,empty_memory())
        self.assertEqual(GarryPolicy.from_dict(old).export()['w1'],old['w1'])

if __name__=='__main__':unittest.main()

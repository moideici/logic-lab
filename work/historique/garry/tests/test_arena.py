import http.client
import json
from functools import partial
from http.server import ThreadingHTTPServer
import tempfile
import threading
import unittest

import numpy as np

from logic_arena.agents import ReferenceAgent
from logic_arena.games import GAMES, make_game, slide_2048
from logic_arena.harness import Arena
from logic_arena.neural import NeuralPolicy, NeuralSuite, SPECS, action_index, encode
from logic_arena.server import Handler


class RulesTests(unittest.TestCase):
    def test_all_environments_are_seeded_and_actions_safe(self):
        for name in GAMES:
            a,b=make_game(name,123),make_game(name,123)
            self.assertEqual(a.observation(),b.observation())
            before=a.observation()
            with self.assertRaises(ValueError):
                a.step({"invalid":True})
            self.assertEqual(before,a.observation())
            for _ in range(20):
                if a.done:break
                action=a.legal_actions()[0]
                self.assertEqual(a.step(action),b.step(action))
                self.assertEqual(a.observation(),b.observation())

    def test_tictactoe_win_draw_and_terminal(self):
        env=make_game('tictactoe')
        for r,c in ((0,0),(1,0),(0,1),(1,1),(0,2)):
            reward=env.step({'row':r,'col':c})
        self.assertEqual((env.done,env.winner,reward),(True,1,1))
        self.assertEqual(env.legal_actions(),[])
        with self.assertRaises(ValueError):env.step({'row':2,'col':2})
        env=make_game('tictactoe')
        for r,c in ((0,0),(0,1),(0,2),(1,1),(1,0),(1,2),(2,1),(2,0),(2,2)):
            env.step({'row':r,'col':c})
        self.assertEqual((env.done,env.winner),(True,0))

    def test_connect4_gravity_win_and_full_column(self):
        env=make_game('connect4')
        for c in (0,1,0,1,0,1,0):env.step({'column':c})
        self.assertEqual(env.winner,1)
        env=make_game('connect4')
        for _ in range(6):env.step({'column':0})
        self.assertNotIn({'column':0},env.legal_actions())

    def test_2048_merges_once_and_conserves_mass(self):
        b=[[2,2,2,2],[4,4,8,0],[0]*4,[0]*4]
        child,gain=slide_2048(b,'left')
        self.assertEqual(child[:2],[[4,4,0,0],[8,8,0,0]])
        self.assertEqual(gain,16)
        self.assertEqual(sum(map(sum,b)),sum(map(sum,child)))
        self.assertEqual(b[0],[2,2,2,2])

    def test_sudoku_solver_and_undo_preserve_givens(self):
        env=make_game('sudoku',7)
        initial=env.observation()
        action=env.legal_actions()[0]
        env.step(action);env.step({'undo':True})
        self.assertEqual(env.board,initial['board'])
        agent=ReferenceAgent(10,seed=7)
        for _ in range(60):
            if env.done:break
            env.step(agent.choose(env.observation(),env.legal_actions()).action)
        self.assertTrue(env.done)
        self.assertEqual(env.winner,1)
        for row in env.board:self.assertEqual(set(row),set(range(1,10)))

    def test_mines_hidden_first_click_safe_and_terminal(self):
        env=make_game('minesweeper',4)
        self.assertNotIn('mines',env.observation())
        env.step({'row':3,'col':3})
        self.assertEqual(env.board[3][3],0)
        self.assertFalse(env.done)
        r,c=next(iter(env.mines))
        env.step({'row':r,'col':c})
        self.assertEqual((env.done,env.winner),(True,0))
        self.assertNotIn('mines',env.observation())

    def test_sliding_puzzle_is_solvable_and_solved(self):
        env=make_game('sliding_puzzle',12,{'scramble':14})
        agent=ReferenceAgent(10,seed=12)
        for _ in range(40):
            if env.done:break
            env.step(agent.choose(env.observation(),env.legal_actions()).action)
        self.assertTrue(env.done)


class NeuralTests(unittest.TestCase):
    def test_express_planning_proves_minimal_puzzle_paths(self):
        from logic_arena.neural import NeuralAgent
        from logic_arena.planner import sliding_distance
        agent=NeuralAgent()
        self.assertEqual(agent.level,10)
        env=make_game('sliding_puzzle')
        env.board=[[8,6,7],[2,5,4],[3,0,1]]
        self.assertEqual(sliding_distance(env.board),31)
        for left in range(31,0,-1):
            d=agent.choose(env.observation(),env.legal_actions())
            self.assertEqual(d.info['remaining_moves'],left)
            self.assertTrue(d.info['optimal'])
            env.step(d.action)
        self.assertEqual((env.moves,env.winner),(31,1))
        for seed in (17,42,91):
            env=make_game('sudoku',seed)
            holes=sum(v==0 for row in env.board for v in row)
            while not env.done and env.moves<100:
                d=agent.choose(env.observation(),env.legal_actions())
                self.assertNotIn('undo',d.action)
                env.step(d.action)
            self.assertEqual((env.winner,env.moves),(1,holes))

    def test_morpion_takes_the_shortest_forced_win(self):
        from logic_arena.neural import NeuralAgent
        env=make_game('tictactoe')
        env.board=[[1,1,0],[2,2,0],[0,0,0]]
        d=NeuralAgent().choose(env.observation(),env.legal_actions())
        self.assertEqual(d.action,{'row':0,'col':2})
        self.assertEqual(d.info['remaining_moves'],1)
        self.assertTrue(d.info['optimal'])

    def test_express_2048_takes_a_winning_merge(self):
        from logic_arena.neural import NeuralAgent
        env=make_game('2048',42)
        env.board=[[1024,1024,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
        d=NeuralAgent().choose(env.observation(),env.legal_actions())
        env.step(d.action)
        self.assertEqual((env.winner,env.moves),(1,1))

    def test_saved_models_mask_actions_and_share_core(self):
        suite=NeuralSuite.load()
        for name,m in suite.models.items():
            env=make_game(name,12)
            self.assertIs(m.core,suite.core)
            self.assertGreater(m.steps,0)
            self.assertEqual(encode(env.observation()).shape,(SPECS[name][0],))
            for level in range(1,11):
                a=m.choose(env.observation(),env.legal_actions(),level)
                self.assertIn(a,env.legal_actions())
        with tempfile.TemporaryDirectory() as d:
            suite.save(d)
            restored=NeuralSuite.load(d)
            for name,m in suite.models.items():
                obs=make_game(name).observation()
                np.testing.assert_allclose(m.logits(obs),restored.models[name].logits(obs))

    def test_learning_updates_shared_parameters_and_other_game(self):
        a=NeuralPolicy('tictactoe',seed=4)
        b=NeuralPolicy('connect4',seed=8,core=a.core)
        # Nonempty board: a blank board has a zero hidden activation at initialization.
        other=make_game('connect4');other.step({'column':3})
        before=b.logits(other.observation()).copy()
        env=make_game('tictactoe');env.step({'row':0,'col':0})
        obs=env.observation();x=encode(obs)[None,:];target=np.array([4]);mask=np.zeros((1,9),dtype=bool)
        mask[0,[action_index('tictactoe',a) for a in env.legal_actions()]]=True
        losses=a.fit(x,target,mask,epochs=40)
        self.assertLess(losses[-1],losses[0]*.1)
        self.assertFalse(np.allclose(before,b.logits(other.observation())))
        self.assertEqual(a.core['steps'],40)


class ProtocolTests(unittest.TestCase):
    def setUp(self):self.arena=Arena()
    def tearDown(self):self.arena.close()

    def create(self):
        return self.arena.dispatch({'op':'create','game':'tictactoe','seed':42})['result']['session_id']

    def test_protocol_error_recovery_revision_and_neural_default(self):
        sid=self.create()
        self.assertFalse(self.arena.dispatch([])['ok'])
        self.assertFalse(self.arena.dispatch({'op':'step','session_id':sid,'action':{'row':True,'col':0}})['ok'])
        result=self.arena.dispatch({'op':'play','session_id':sid,'expected_revision':0})
        self.assertTrue(result['ok']);self.assertEqual(result['result']['info']['agent'],'neural+planner')
        self.assertEqual(result['result']['revision'],1)
        self.assertFalse(self.arena.dispatch({'op':'play','session_id':sid,'expected_revision':0})['ok'])

    def test_background_run_truncation_and_delete(self):
        sid=self.create()
        r=self.arena.dispatch({'op':'run','session_id':sid,'max_steps':2,'interval_ms':0})
        self.assertTrue(r['ok'])
        session=self.arena.session(sid);session.thread.join(5)
        self.assertFalse(session.running)
        self.assertEqual(session.revision,2)
        self.assertEqual(session.events[-1]['type'],'stopped')
        self.assertTrue(session.events[-1]['truncated'])
        seq=[e['seq'] for e in session.events]
        self.assertEqual(seq,sorted(set(seq)))
        self.assertTrue(self.arena.dispatch({'op':'delete','session_id':sid})['ok'])
        self.assertFalse(self.arena.dispatch({'op':'observe','session_id':sid})['ok'])

    def test_http_json_and_sse(self):
        class Quiet(Handler):
            def log_message(self,*a):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,arena=self.arena))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            conn.request('GET','/');resp=conn.getresponse();self.assertEqual(resp.status,200);self.assertIn(b'Logic Lab',resp.read())
            conn.request('POST','/api',json.dumps({'op':'create'}),{'Content-Type':'application/json'})
            resp=conn.getresponse();created=json.loads(resp.read());sid=created['result']['session_id']
            conn.request('POST','/api','{broken',{'Content-Type':'application/json'})
            resp=conn.getresponse();self.assertEqual(resp.status,400);resp.read()
            conn.request('GET',f'/sessions/{sid}/events');resp=conn.getresponse()
            self.assertEqual(resp.getheader('Content-Type'),'text/event-stream; charset=utf-8')
            self.assertTrue(resp.readline().startswith(b'id: 1'))
            self.assertEqual(resp.readline(),b'event: created\n')
            self.assertIn(b'"session_id"',resp.readline())
            conn.close()
        finally:
            server.shutdown();server.server_close();thread.join(2)


if __name__=='__main__':unittest.main()

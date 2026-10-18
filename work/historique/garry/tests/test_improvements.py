"""Régressions : espérances exactes, indépendance des agents et arrêt réactif."""
import http.client
import json
import random
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import numpy as np

from logic_arena.agents import Decision
from logic_arena.games import make_game, slide_2048
from logic_arena.harness import Arena
from logic_arena.neural import NeuralAgent, NeuralPolicy
from logic_arena.general import GarryView
from logic_arena.server import Handler
from logic_arena import tiles


class TilesTests(unittest.TestCase):
    def test_packed_transitions_match_independent_game_rules(self):
        rng = random.Random(2701)
        for _ in range(100):
            board = [[rng.choice([0,0,2,4,8,16,32,64,128,256,512,1024]) for _ in range(4)] for _ in range(4)]
            original = tiles.pack(board)
            for direction in tiles.DIRECTIONS:
                expected, gain = slide_2048(board, direction)
                self.assertEqual(tiles.move(original, direction), (tiles.pack(expected), gain))

    def test_analytical_expectation_matches_all_spawn_outcomes(self):
        rng = random.Random(8901)
        for _ in range(60):
            board = [[rng.choice([0,0,2,4,8,16,64,512]) for _ in range(4)] for _ in range(4)]
            empty = [(r,c) for r in range(4) for c in range(4) if not board[r][c]]
            if not empty:
                continue
            expected = 0.
            for r,c in empty:
                for value, probability in ((2,.9),(4,.1)):
                    child = [row[:] for row in board]
                    child[r][c] = value
                    expected += probability*tiles.heuristic(tiles.pack(child))/len(empty)
            self.assertAlmostEqual(tiles.spawn_expectation(tiles.pack(board)), expected, delta=1e-7)


class AgentIsolationTests(unittest.TestCase):
    def test_agent_rng_advances_reproducibly_without_changing_cached_model_rng(self):
        obs = make_game('tictactoe').observation()
        legal = make_game('tictactoe').legal_actions()
        # Des logits égaux isolent le comportement du générateur de l'agent.
        with patch.object(GarryView, 'logits', return_value=np.zeros(9)):
            a = NeuralAgent(level=1, seed=17, planning=False)
            b = NeuralAgent(level=1, seed=17, planning=False)
            sequence_a = [a.choose(obs,legal).action for _ in range(30)]
            sequence_b = [b.choose(obs,legal).action for _ in range(30)]
            self.assertEqual(sequence_a,sequence_b)
            self.assertGreater(len({json.dumps(x,sort_keys=True) for x in sequence_a}),1)
            # Les appels concurrents d'autres agents n'intercalent pas leurs tirages.
            c = NeuralAgent(level=1,seed=17,planning=False)
            noise = NeuralAgent(level=1,seed=99,planning=False)
            mixed = []
            with ThreadPoolExecutor(max_workers=2) as pool:
                for _ in range(30):
                    noise_job = pool.submit(noise.choose,obs,legal)
                    mixed.append(c.choose(obs,legal).action)
                    noise_job.result()
            self.assertEqual(sequence_a,mixed)

    def test_one_neural_forward_per_current_board(self):
        agent = NeuralAgent(planning=True)
        env = make_game('tictactoe')
        with patch.object(GarryView,'logits',return_value=np.zeros(9)) as forward:
            agent.choose(env.observation(),env.legal_actions())
        self.assertEqual(forward.call_count,1)

    def test_failed_save_keeps_previous_model_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'model.json'
            model = NeuralPolicy('tictactoe')
            model.save(path)
            old = path.read_bytes()
            with patch('logic_arena.neural.os.replace',side_effect=OSError('simulated failure')):
                with self.assertRaises(OSError):
                    model.save(path)
            self.assertEqual(path.read_bytes(),old)
            self.assertEqual(list(Path(directory).iterdir()),[path])
            NeuralPolicy.load(path)


class RealtimeTests(unittest.TestCase):
    def test_stop_returns_during_inference_and_discards_late_move(self):
        arena = Arena()
        sid = arena.dispatch({'op':'create'})['result']['session_id']
        entered,release,stopped = threading.Event(),threading.Event(),threading.Event()
        result = []

        class SlowAgent:
            def choose(self,obs,legal):
                entered.set()
                release.wait(5)
                return Decision(legal[0],{})

        def stop():
            result.append(arena.dispatch({'op':'stop','session_id':sid}))
            stopped.set()

        try:
            with patch('logic_arena.harness.agent_config',return_value=SlowAgent()):
                arena.dispatch({'op':'run','session_id':sid})
            self.assertTrue(entered.wait(2))
            thread = threading.Thread(target=stop,daemon=True)
            thread.start()
            self.assertTrue(stopped.wait(2),'stop is blocked by inference')
            self.assertTrue(result[0]['ok'])
        finally:
            release.set()
            arena.close()
        session = arena.session(sid)
        self.assertEqual(session.revision,0)
        self.assertEqual(session.events[-1]['reason'],'cancelled')

    def test_sse_resync_of_finished_run_closes_instead_of_waiting_forever(self):
        arena = Arena()
        sid = arena.dispatch({'op':'create'})['result']['session_id']
        session = arena.session(sid)
        for _ in range(260):
            session.emit('step',{})
        session.emit('stopped',{'reason':'max_steps'})

        class Quiet(Handler):
            def log_message(self,*args):pass

        server = ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,arena=arena))
        worker = threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        connection = http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2)
        try:
            connection.request('GET',f'/sessions/{sid}/events?after=0')
            response = connection.getresponse()
            data = response.read().decode()
            self.assertIn('event: resync',data)
            self.assertIn('"running": false',data)
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            worker.join(2)
            arena.close()


if __name__=='__main__':
    unittest.main()

import copy
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from logic_arena.agents import Budget
from logic_arena.connect4_wasm import search
from logic_arena.games import make_game
from logic_arena.harness import catalog
from logic_arena.identity import agent_identity
from logic_arena.neural import NeuralAgent, NeuralPolicy, SPECS

ROOT=Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def test_identity_in_catalog_decisions_and_exports_with_unified_model(self):
        games=catalog()['games']
        self.assertEqual({game['ai']['codename'] for game in games},{'garry'})
        for game in games:
            name=game['id']
            identity=agent_identity(name)
            self.assertEqual(identity['version'],'3.1.0')
            env=make_game(name,42)
            d=NeuralAgent(planning=False).choose(env.observation(),env.legal_actions())
            self.assertEqual(d.info['identity'],identity)
            model=NeuralPolicy(name)
            data=model.export()
            self.assertEqual(data['identity'],identity)
            self.assertEqual((data['input'],data['output']),SPECS[name])
            self.assertEqual(data['hidden'],48)
            np.testing.assert_array_equal(NeuralPolicy.from_dict(data).logits(env.observation()),model.logits(env.observation()))

    def test_previous_version_files_match_frozen_hashes(self):
        base=ROOT/'versions'/'1.0.0'
        manifest=json.loads((base/'manifest.json').read_text())
        for name,expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256((base/name).read_bytes()).hexdigest(),expected,name)

    def test_wasm_safe_actions_and_proven_forks_with_zero_budget(self):
        positions=json.loads((ROOT/'tests'/'fixtures'/'connect4-positions.json').read_text())
        for p in positions:
            env=make_game('connect4')
            for c in p['history']:
                env.step({'column':c})
            before=env.observation()
            action,info=search(before,env.legal_actions(),Budget(0,10000),np.arange(7)*1e12)
            self.assertEqual(info['runtime'],'wasm')
            if p['immediate']:
                self.assertIn(action['column'],p['immediate'])
            elif p['forks']:
                self.assertIn(action['column'],p['forks'])
                self.assertTrue(info['optimal'])
                self.assertEqual(info['remaining_moves'],3)
            elif p['safe']:
                self.assertIn(action['column'],p['safe'])
            self.assertEqual(env.observation(),before)

    def test_separate_wasm_instances_do_not_share_board_or_search_state(self):
        from concurrent.futures import ThreadPoolExecutor
        positions=json.loads((ROOT/'tests'/'fixtures'/'connect4-positions.json').read_text())
        def run(p):
            env=make_game('connect4')
            for c in p['history']:env.step({'column':c})
            return search(env.observation(),env.legal_actions(),Budget(3000,10000),np.arange(7))[0]
        expected=list(map(run,positions))
        with ThreadPoolExecutor(max_workers=3) as pool:
            self.assertEqual(list(pool.map(run,positions)),expected)


if __name__=='__main__':unittest.main()

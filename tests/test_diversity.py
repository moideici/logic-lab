from copy import deepcopy
from pathlib import Path
import unittest
import numpy as np
from logic_arena.general import GarryPolicy
from logic_arena.games import make_game,slide_2048
from logic_arena.diversity import canonical_key,new_sudoku,sudoku_solutions,sudoku_family,soft_targets,example,augment,arrays,SoftImitation,assess,family_split
from examples.train_garry_guarded import protected_weights_equal
ROOT=Path(__file__).resolve().parents[1]

class DiversityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=GarryPolicy.load(ROOT/'versions/3.0.0/garry.json')

    def test_new_sudoku_families_are_deterministic_unique_and_structurally_varied(self):
        families=set()
        for seed in (151,251,351,451):
            env,solution=new_sudoku(seed,40);answers,_=sudoku_solutions(env.board)
            self.assertEqual(answers,[solution]);self.assertEqual(env.board,new_sudoku(seed,40)[0].board)
            families.add(sudoku_family(env.givens));self.assertLess(sum(v==0 for row in env.board for v in row),81)
            self.assertTrue(all(v==0 or v==solution[r][c] for r,row in enumerate(env.givens) for c,v in enumerate(row)))
        self.assertEqual(len(families),4)

    def test_equivalent_orientations_are_one_identity_and_cannot_cross_splits(self):
        env=make_game('connect4')
        for c in (0,3,1,2,0):env.step({'column':c})
        obs=env.observation();mirror={**obs,'board':[r[::-1] for r in obs['board']]}
        self.assertEqual(canonical_key(obs),canonical_key(mirror))
        grid=make_game('tictactoe');grid.step({'row':0,'col':1});obs=grid.observation();rot={**obs,'board':[list(r) for r in zip(*obs['board'][::-1])]}
        self.assertEqual(canonical_key(obs),canonical_key(rot));self.assertEqual(family_split('fixed:151'),family_split('fixed:151'))

    def test_soft_targets_cover_multiple_good_moves_and_forbid_proven_losses(self):
        legal=[{'column':c} for c in range(7)];values=[{'action':a,'quality':[v]} for a,v in zip(legal,(10,10,-999998,8,-500,5,0))]
        p=soft_targets('connect4',legal,values);self.assertAlmostEqual(float(p.sum()),1);self.assertEqual(p[2],0);self.assertGreater(p[0],0);self.assertEqual(p[0],p[1])
        values[4]['quality']=[999999];p=soft_targets('connect4',legal,values);self.assertEqual(p[4],1);self.assertEqual(np.count_nonzero(p),1)

    def test_augmentations_preserve_rules_targets_and_family(self):
        env=make_game('2048',51);case=example(env,self.base,'fixture','oracle')
        for c in augment(case):
            self.assertEqual(c['family'],case['family']);self.assertAlmostEqual(sum(c['target']),1)
            for old,new in zip(case['legal'],c['legal']):
                self.assertEqual(slide_2048(case['observation']['board'],old['direction'])[1],slide_2048(c['observation']['board'],new['direction'])[1])
        t=make_game('tictactoe');t.board=[[1,1,0],[2,2,0],[0,0,0]];case=example(t,self.base,'fixture','oracle')
        for c in augment(case):
            target,info=assess(c['observation'],c['legal'],self.base)
            np.testing.assert_array_equal(c['target'],target);self.assertEqual(set(c['optimal']),set(info['optimal']))

    def test_guarded_soft_training_reduces_loss_and_preserves_every_other_mode(self):
        candidate=GarryPolicy.from_dict(self.base.export());env=make_game('connect4',13)
        for col in (3,2,1):env.step({'column':col})
        c=example(env,self.base,'train:1','oracle');cases=[c]*8;_,x,y,mask,w=arrays(cases,'connect4');trainer=SoftImitation(candidate,'connect4',.002)
        first=trainer.batch(x,y,mask,w)
        for _ in range(30):last=trainer.batch(x,y,mask,w)
        self.assertLess(last,first);self.assertTrue(protected_weights_equal(self.base,candidate,'connect4'));self.assertEqual(self.base.position_head,candidate.position_head)
        before=candidate.w1.copy();bad=y.copy();bad[0]*=0
        with self.assertRaises(ValueError):trainer.batch(x,bad,mask,w)
        np.testing.assert_array_equal(before,candidate.w1)

    def test_labels_are_public_and_never_replace_optimal_ids_with_a_boolean(self):
        for game in ('connect4','2048','minesweeper'):
            env=make_game(game,9);case=example(env,self.base,'train:public','oracle')
            self.assertIsInstance(case['optimal'],list);self.assertNotIn('mines',case['observation']);self.assertNotIn('solution',case['observation']);self.assertTrue(case['optimal'])
            self.assertEqual(len(case['target']),{'connect4':7,'2048':4,'minesweeper':64}[game])

    def test_test_gate_rejects_loss_of_a_critical_skill(self):
        from examples.train_garry_repertoire import allowed
        before={'sound_choice_rate':.6,'soft_cross_entropy':2.,'categories':{'block':{'samples':20,'sound_choice_rate':.8}}}
        after={'sound_choice_rate':.7,'soft_cross_entropy':1.,'categories':{'block':{'samples':20,'sound_choice_rate':.7}}}
        self.assertFalse(allowed(before,after))

    def test_cross_cycle_replay_cannot_import_prior_heldout_or_its_mirror(self):
        from logic_arena.diversity import HistoricalSplits
        from logic_arena.general import general_encode
        env=make_game('connect4');env.step({'column':0});obs=env.observation()
        held={'observation':obs,'family':'old-held','split':'test'}
        history=HistoricalSplits([held]);mirror={**obs,'board':[r[::-1] for r in obs['board']]}
        self.assertFalse(history.fresh(mirror,'new'));self.assertFalse(history.replayable({**held,'split':'train','observation':mirror}))
        env.step({'column':2});fresh=env.observation()
        self.assertFalse(history.fresh(fresh,'old-held'));self.assertTrue(history.fresh(fresh,'new'))
        self.assertFalse(history.replayable({'observation':fresh,'family':'old-held','split':'train'}))
        legacy=HistoricalSplits(encoded_rows=[general_encode(obs)])
        self.assertFalse(legacy.fresh(mirror,'new'));self.assertTrue(legacy.fresh(fresh,'new'))

    def test_atomic_status_retries_transient_windows_file_lock(self):
        import tempfile,json,os
        from unittest.mock import patch
        from examples.train_garry_curriculum import atomic_json
        real_replace=os.replace;attempts=[]
        def transient(source,target):
            attempts.append(1)
            if len(attempts)<3:raise PermissionError('temporary reader')
            return real_replace(source,target)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'status.json'
            with patch('examples.train_garry_curriculum.os.replace',side_effect=transient),patch('examples.train_garry_curriculum.time.sleep'):
                atomic_json(path,{'state':'completed'})
            self.assertEqual(json.loads(path.read_text()),{'state':'completed'});self.assertEqual(len(attempts),3)

    def test_completed_game_checkpoints_resume_without_relabelling(self):
        import tempfile
        from unittest.mock import patch
        from examples.build_garry_repertoire import build
        from logic_arena.diversity import GAMES,SPLITS
        counts={g:{s:1 for s in SPLITS} for g in GAMES}
        with tempfile.TemporaryDirectory() as directory:
            first,summary=build(self.base,counts,16090123,lambda *a:None,checkpoint=Path(directory))
            with patch('examples.build_garry_repertoire.example',side_effect=AssertionError('Regenerated completed game')):
                resumed,again=build(self.base,counts,16090123,lambda *a:None,checkpoint=Path(directory))
            self.assertEqual(first,resumed);self.assertEqual(summary,again);self.assertEqual(len(first),42)

if __name__=='__main__':unittest.main()

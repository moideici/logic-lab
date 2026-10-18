import importlib.util
from pathlib import Path
import unittest
import numpy as np

from logic_arena.general import GarryPolicy, GAMES, OUTPUT_OFFSETS
from logic_arena.games import make_game
from logic_arena.neural import SPECS

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('curriculum',ROOT/'examples'/'train_garry_curriculum.py')
curriculum=importlib.util.module_from_spec(spec)
spec.loader.exec_module(curriculum)


class CurriculumTests(unittest.TestCase):
    def test_truncation_is_not_counted_as_an_improvement(self):
        before={'game':'2048','wins':0,'losses':30,'truncated':0,'mean_score':100.}
        after={**before,'losses':29,'truncated':1}
        self.assertFalse(curriculum.compare_game(before,after)['improvement'])
        sudoku={'game':'sudoku','wins':0,'losses':0,'truncated':30,'mean_score':8.6}
        self.assertTrue(curriculum.compare_game(sudoku,{**sudoku,'mean_score':4.72})['regression'])

    def test_guarded_training_changes_only_the_selected_game_parameters(self):
        from examples.train_garry_guarded import fit_guarded_epoch,protected_weights_equal
        before=GarryPolicy.load(ROOT/'web'/'models'/'garry.json')
        after=GarryPolicy.from_dict(before.export())
        training,_=curriculum.dataset(before,4,314159,lambda *args:None)
        x,y,masks=training['connect4']
        fit_guarded_epoch(after,'connect4',x,y,masks,.001,np.random.default_rng(1))
        self.assertTrue(protected_weights_equal(before,after,'connect4'))
        self.assertFalse(np.array_equal(before.w2,after.w2))
        self.assertEqual(before.core['steps'],after.core['steps'])
        self.assertEqual(after.steps-before.steps,4)

    def test_all_playable_tictactoe_states_are_enumerated_once(self):
        states=curriculum.ttt_states()
        self.assertEqual(len(states),4520)
        self.assertEqual(len({b for b,p in states}),4520)
        for board,player in states:
            self.assertEqual(board.count(1)-board.count(2),0 if player==1 else 1)

    def test_symmetry_related_positions_cannot_cross_the_tictactoe_split(self):
        for board,player in curriculum.ttt_states()[::37]:
            matrix=[list(board[i:i+3]) for i in (0,3,6)]
            expected=curriculum.ttt_partition(matrix)
            for _ in range(4):
                self.assertEqual(curriculum.ttt_partition(matrix),expected)
                self.assertEqual(curriculum.ttt_partition([r[::-1] for r in matrix]),expected)
                matrix=[list(r) for r in zip(*matrix[::-1])]

    def test_dataset_is_unique_has_legal_targets_and_validation_has_no_overlap(self):
        teacher=GarryPolicy.load(ROOT/'web'/'models'/'garry.json')
        training,train_keys=curriculum.dataset(teacher,4,314159,lambda *args:None)
        validation,val_keys=curriculum.dataset(teacher,4,271828,lambda *args:None,split='validation',excluded=train_keys)
        for game in GAMES:
            self.assertEqual(len(train_keys[game]),4)
            self.assertEqual(len(val_keys[game]),4)
            self.assertFalse(train_keys[game]&val_keys[game])
            for x,y,mask in (training[game],validation[game]):
                self.assertTrue(mask[np.arange(len(y)),y].all())
                start=OUTPUT_OFFSETS[game];stop=start+SPECS[game][1]
                self.assertFalse(mask[:,:start].any())
                self.assertFalse(mask[:,stop:].any())
                self.assertEqual(len({row.tobytes() for row in x}),4)


if __name__=='__main__':unittest.main()

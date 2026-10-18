from pathlib import Path
import sys,json,unittest,numpy as np
ROOT=Path(__file__).resolve().parents[1];project=ROOT/'projets/garry';sys.path.insert(0,str(project));sys.path.insert(0,str(project/'tests'))
from logic_arena.games import GAMES,make_game
from logic_arena.neural import NeuralSuite,MODEL_DIR
from test_arena import RulesTests
assert Path(MODEL_DIR).resolve().is_relative_to(project.resolve())
suite=NeuralSuite.load();checked=[]
for name in GAMES:
    env=make_game(name,12);values=suite.models[name].logits(env.observation());assert np.isfinite(values).all();checked.append(name)
tests=unittest.TestSuite(RulesTests(name) for name in ('test_tictactoe_win_draw_and_terminal','test_connect4_gravity_win_and_full_column','test_2048_merges_once_and_conserves_mass'))
result=unittest.TextTestRunner(verbosity=2).run(tests)
report={'status':'passed' if result.wasSuccessful() else 'failed','model_directory':str(MODEL_DIR),'games_loaded_and_finite_logits':checked,'game_count':len(checked),'bounded_rule_tests':result.testsRun,'rule_failures':len(result.failures)+len(result.errors),'full_suite':'stopped after over seven minutes in test_saved_models_mask_actions_and_share_core; not declared passed','scope':'bounded verification of the relocated copy, not playing-strength evaluation'}
(ROOT/'outputs/verification-garry-regroupe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));assert result.wasSuccessful()

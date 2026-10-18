import copy,random,unittest,json,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from logic_arena.targeted import sample_pool,current_errors,restore_training_position,assert_retention,strict_promotion,load_replay
from logic_arena.continuous_service import ContinuousTraining
from logic_arena.general import GarryPolicy,INPUT_OFFSETS
from logic_arena.games import make_game
from logic_arena.neural import action_index

class TargetedTests(unittest.TestCase):
 def test_hard_replay_keeps_diverse_categories_and_rejects_reserved_cases(self):
  cases=[{'id':str(i),'split':'train','category':str(i%4)} for i in range(100)]
  selected=sample_pool(cases,{str(i) for i in range(70)},random.Random(42),limit=40)
  self.assertEqual(len(selected),40);self.assertGreaterEqual(sum(int(c['id'])<70 for c in selected),24);self.assertEqual({c['category'] for c in selected},{'0','1','2','3'})
  with self.assertRaises(ValueError):sample_pool([{'id':'held','split':'test','category':'x'}],set(),random.Random(1))
 def test_error_selection_uses_current_model_instead_of_old_baseline_flag(self):
  model=GarryPolicy(hidden=2);env=make_game('tictactoe');obs=env.observation();legal=env.legal_actions();z=model.for_game('tictactoe').logits(obs);best=max(legal,key=lambda a:float(z[action_index('tictactoe',a)]));chosen=action_index('tictactoe',best);other=next(action_index('tictactoe',a) for a in legal if a!=best)
  common={'split':'train','observation':obs,'legal':legal,'target':[1/9]*9,'category':'opening'}
  cases=[{**common,'id':'right','optimal':[chosen],'baseline_error':True},{**common,'id':'wrong','optimal':[other],'baseline_error':False}]
  self.assertEqual(current_errors(model,cases,'tictactoe'),{'wrong'})
 def test_seeded_continuation_restores_all_public_go_state_and_cannot_use_tests(self):
  env=make_game('go',42,{'size':9});env.step({'row':2,'col':2});case={'split':'train','observation':env.observation()};restored=restore_training_position(case,123)
  self.assertEqual(restored.observation(),env.observation());self.assertEqual(restored.legal_actions(),env.legal_actions())
  with self.assertRaises(ValueError):restore_training_position({**case,'split':'validation'},1)
 def test_retention_checks_other_heads_biases_core_and_steps(self):
  before=GarryPolicy(hidden=2);after=copy.deepcopy(before);after.w1[INPUT_OFFSETS['go'],0]+=.1;assert_retention(after,before,'go')
  after.b2[0]+=.1
  with self.assertRaises(AssertionError):assert_retention(after,before,'go')
 def test_promotion_rejects_validation_regressions_even_if_accuracy_rises(self):
  def m(rate,loss):return {'optimal_choice_rate':rate,'soft_cross_entropy':loss}
  self.assertFalse(strict_promotion(m(.5,1),m(.6,1.1),m(.5,1),m(.6,.9)))
  self.assertFalse(strict_promotion(m(.5,1),m(.6,.9),m(.5,1),m(.4,.8)))
  self.assertTrue(strict_promotion(m(.5,1),m(.6,.9),m(.5,1),m(.5,.9)))
 def test_historical_replay_never_reuses_tests_or_unprotected_sessions(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for name,quarantined in [('protected',1),('unprotected',0)]:
    folder=root/name;folder.mkdir();(folder/'status.json').write_text(json.dumps({'state':'completed','history_quarantined_cases':quarantined}),encoding='utf-8')
    (folder/'cases.jsonl').write_text(''.join(json.dumps({'id':name+split,'split':split,'observation':{'game':'hex'}})+'\n' for split in ('train','validation','test')),encoding='utf-8')
   train,validation,sources=load_replay(root,random.Random(42),lambda **kw:None)
   self.assertEqual([c['id'] for c in train['hex']],['protectedtrain']);self.assertEqual([c['id'] for c in validation['hex']],['protectedvalidation']);self.assertEqual(sources,['protected'])
 def test_service_launches_the_targeted_profile_independently(self):
  with tempfile.TemporaryDirectory() as tmp,patch('logic_arena.continuous_service.subprocess.Popen') as start:
   start.return_value.poll.return_value=None;service=ContinuousTraining(tmp);result=service.start(1800,'weakness')
   self.assertEqual(result['profile'],'weakness');self.assertEqual(result['duration_seconds'],1800)
   command=start.call_args.args[0];self.assertIn('logic_arena.targeted',command);self.assertEqual(command[-1],'1800')
   with self.assertRaises(ValueError):service.start(1800,'unknown')

if __name__=='__main__':unittest.main()

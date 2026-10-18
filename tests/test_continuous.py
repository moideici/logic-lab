import unittest,tempfile,json,time
from pathlib import Path
from unittest.mock import patch
from logic_arena.continuous import should_promote,atomic_json
from logic_arena.continuous_service import ContinuousTraining
class ContinuousTests(unittest.TestCase):
 def test_promotion_requires_both_validation_sets_and_real_improvement(self):
  def m(rate,loss=1):return {'optimal_choice_rate':rate,'soft_cross_entropy':loss}
  self.assertFalse(should_promote(m(.5),m(.4),m(.5),m(.8)))
  self.assertFalse(should_promote(m(.5),m(.8),m(.5),m(.4)))
  self.assertFalse(should_promote(m(.5),m(.5),m(.5),m(.5)))
  self.assertTrue(should_promote(m(.5),m(.6),m(.5),m(.5)))
  self.assertTrue(should_promote(m(.5),m(.5,.8),m(.5),m(.5)))
 def test_atomic_status_retries_temporary_windows_lock(self):
  import os
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'status.json';real=os.replace;calls=[]
   def replace(a,b):
    calls.append(1)
    if len(calls)<3:raise PermissionError('Temporary reader lock')
    return real(a,b)
   with patch('logic_arena.continuous.os.replace',side_effect=replace):atomic_json(p,{'moves':3})
   self.assertEqual(json.loads(p.read_text()),{'moves':3});self.assertEqual(len(calls),3)
 def test_validation_of_duration_and_stale_session(self):
  with tempfile.TemporaryDirectory() as d:
   service=ContinuousTraining(d)
   for duration in (0,3601,True,'3600'):
    with self.assertRaises(ValueError):service.start(duration)
   p=Path(d)/'stale';p.mkdir();f=p/'status.json';f.write_text(json.dumps({'state':'running','started_at':'2026-10-17'}));import os;os.utime(f,(time.time()-120,)*2);self.assertEqual(service.get('stale')['state'],'error')
if __name__=='__main__':unittest.main()

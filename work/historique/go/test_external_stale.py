import json,os,time,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from logic_arena.external import ExternalArena

class ExternalStaleTests(unittest.TestCase):
 def test_unknown_old_worker_is_reported_without_mutating_its_historical_status(self):
  with TemporaryDirectory() as tmp:
   root=Path(tmp);folder=root/'old';folder.mkdir();path=folder/'status.json';original={'state':'running','game':'go','steps':252};path.write_text(json.dumps(original),encoding='utf-8')
   arena=ExternalArena(root)
   self.assertEqual(arena.get('old')['state'],'running')
   old=time.time()-181;os.utime(path,(old,old));status=arena.get('old')
   self.assertEqual(status['state'],'error');self.assertIn('trois minutes',status['error']);self.assertEqual(status['steps'],252)
   self.assertEqual(json.loads(path.read_text(encoding='utf-8')),original)

if __name__=='__main__':unittest.main()

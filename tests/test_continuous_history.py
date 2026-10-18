import json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from logic_arena.continuous_history import historical_case_ids

class ContinuousHistoryTests(unittest.TestCase):
 def test_all_past_splits_are_quarantined_and_new_entries_invalidate_the_index(self):
  with TemporaryDirectory() as tmp:
   root=Path(tmp);older=root/'earlier';current=root/'current';older.mkdir();current.mkdir()
   path=older/'cases.jsonl';path.write_text(''.join(json.dumps({'id':split,'split':split})+'\n' for split in ('train','validation','test')),encoding='utf-8')
   (current/'cases.jsonl').write_text(json.dumps({'id':'current','split':'train'})+'\n',encoding='utf-8')
   keys,sources=historical_case_ids(root,current);self.assertEqual(keys,{'train','validation','test'});self.assertEqual(sources[0]['unique_states'],3)
   self.assertEqual(historical_case_ids(root,current)[0],keys)
   with path.open('a',encoding='utf-8') as stream:stream.write(json.dumps({'id':'new-heldout','split':'test'})+'\n')
   self.assertEqual(historical_case_ids(root,current)[0],keys|{'new-heldout'})
   with path.open('a',encoding='utf-8') as stream:stream.write('{incomplete')
   with self.assertRaisesRegex(ValueError,'Historique incomplet'):historical_case_ids(root,current)

if __name__=='__main__':unittest.main()

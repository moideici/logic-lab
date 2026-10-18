import unittest,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class BenchmarkTests(unittest.TestCase):
 def test_families_pairs_labels_and_fingerprints(self):
  import hashlib
  manifest=json.loads((R/'data/manifest.json').read_text(encoding='utf-8'));seen=set();pairs=set();ids=set()
  for split,meta in manifest['splits'].items():
   raw=(R/'data'/f'{split}.jsonl').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['sha256']);cases=[json.loads(s) for s in raw.decode().splitlines()];families=collections.defaultdict(list)
   for c in cases:
    pair=(c['premise'],c['hypothesis']);self.assertNotIn(pair,pairs);pairs.add(pair);self.assertNotIn(c['id'],ids);ids.add(c['id']);families[c['family']].append(c['label'])
   self.assertFalse(set(families)&seen);seen.update(families)
   for labels in families.values():self.assertEqual(sorted(labels),[0,1,2])
   self.assertEqual(len(cases),meta['cases']);self.assertEqual(len(set(collections.Counter(c['label'] for c in cases).values())),1)
 def test_new_names_and_composition_stay_reserved(self):
  train=(R/'data/train.jsonl').read_text(encoding='utf-8');comp=(R/'data/test_composition.jsonl').read_text(encoding='utf-8')
  for name in ('Inès','Sami','Yanis','Émile'):self.assertNotIn(name,train)
  self.assertNotIn('aile nord',train);self.assertIn('aile nord',comp)

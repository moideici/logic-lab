import unittest,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class LexiconTests(unittest.TestCase):
 def test_provenance_hash_and_word_partitions(self):
  meta=json.loads((R/'lexicon/manifest.json').read_text(encoding='utf-8'));raw=(R/'lexicon/senses.jsonl').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['sha256']);seen={};ids=set()
  for line in raw.decode().splitlines():
   r=json.loads(line);self.assertNotIn(r['id'],ids);ids.add(r['id']);self.assertEqual(r['source']['licence'],'CC-BY-SA-4.0');self.assertTrue(r['source']['wiktionnaire'].startswith('https://fr.wiktionary.org/wiki/'));self.assertTrue(r['definitions']);self.assertEqual(seen.setdefault(r['family'],r['split']),r['split']);self.assertNotIn('translations',r)
  self.assertEqual(len(ids),meta['senses']);self.assertEqual(len(seen),meta['words_imported'])

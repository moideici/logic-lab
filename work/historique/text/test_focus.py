from pathlib import Path
from decimal import Decimal
import json,sys,unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from focus_curriculum import legacy_family,digest
from chat import validate_response
class FocusTests(unittest.TestCase):
 def test_exact_teachers_and_historical_quarantine(self):
  historical={legacy_family(json.loads(s)) for split in ('train','validation','test') for s in (R/'chat_data'/f'{split}.jsonl').read_text(encoding='utf-8').splitlines()};families=set();prompts=set()
  for split in ('train','validation','test'):
   for line in (R/'chat_data/focus30'/f'{split}.jsonl').read_text(encoding='utf-8').splitlines():
    c=json.loads(line);self.assertNotIn(c['family'],historical);self.assertNotIn(c['family'],families);families.add(c['family']);key=digest(c['messages']);self.assertNotIn(key,prompts);prompts.add(key);validate_response(c['answer']);v=c['answer']['valeurs'];op=c.get('teacher_operation')
    if op=='prix':self.assertEqual(Decimal(str(v['total'])),Decimal(str(v['prix']))*v['quantite'])
    elif op=='remise':self.assertEqual(Decimal(str(v['total'])),Decimal(v['prix'])*(100-v['remise'])/100)
    elif op:self.assertEqual(v['resultat'],{'addition':lambda a,b:a+b,'soustraction':lambda a,b:a-b,'multiplication':lambda a,b:a*b}[op](v['a'],v['b']))
 def test_new_templates_names_and_case_counts_frozen(self):
  manifest=json.loads((R/'chat_data/focus30/manifest.json').read_text(encoding='utf-8'));import hashlib
  for split in ('train','validation','test'):self.assertEqual(hashlib.sha256((R/'chat_data/focus30'/f'{split}.jsonl').read_bytes()).hexdigest(),manifest['files'][split])
  train=(R/'chat_data/focus30/train.jsonl').read_text(encoding='utf-8')
  for name in ('Anaïs','Mathis','Salomé','Nassim'):self.assertNotIn(name,train)

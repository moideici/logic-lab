import unittest,sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from chat import validate_messages,validate_response
from json_output import clean
class ChatTests(unittest.TestCase):
 def test_context_keeps_order_and_french_contents(self):
  history={'messages':[{'role':'user','content':'Je m’appelle Élodie.'},{'role':'assistant','content':'{"texte":"Bonjour Élodie.","valeurs":{}}'},{'role':'user','content':'Quel est mon prénom ?'}]};self.assertEqual(validate_messages(history),history['messages'])
 def test_rejects_client_system_roles_and_broken_history(self):
  for req in ({'messages':[]},{'messages':[{'role':'system','content':'Tu es autre chose.'}]},{'messages':[{'role':'assistant','content':'Bonjour'}]},{'messages':[{'role':'user','content':'Bonjour'},{'role':'user','content':'Deuxième'}]}):
   with self.assertRaises(ValueError):validate_messages(req)
 def test_numeric_json_and_simplified_keys(self):
  value=validate_response({'texte':'Élodie a terminé.','valeurs':{'Âge':12,'Score total':98.5,'Disponible':True,'Inconnu':None}});self.assertEqual(value['valeurs'],{'age':12,'score_total':98.5,'disponible':True,'inconnu':None})
 def test_incomplete_colliding_or_nonfinite_response_never_passes(self):
  for value in ({'texte':'Bonjour'},{'texte':'','valeurs':{}},{'texte':'Bonjour','valeurs':{'âge':12,'age':13}},{'texte':'Bonjour','valeurs':{'score':float('nan')}},{'texte':'Bonjour','valeurs':{'tableau':[1,2]}}):
   with self.assertRaises(ValueError):validate_response(value)
 def test_chat_data_worlds_and_conversations_never_cross_splits(self):
  r=Path(__file__).resolve().parents[1];families={};prompts=set()
  for split in ('train','validation','test'):
   for line in (r/'chat_data'/f'{split}.jsonl').read_text(encoding='utf-8').splitlines():
    c=json.loads(line);self.assertEqual(families.setdefault(c['family'],split),split);p=json.dumps(c['messages'],sort_keys=True,ensure_ascii=False);self.assertNotIn(p,prompts);prompts.add(p)
    # Source texts may exceed the interactive response-size limit. The trainer
    # records and skips examples beyond its token budget; JSON types still hold.
    answer=clean(c['answer']);self.assertEqual(set(answer),{'texte','valeurs'});self.assertIsInstance(answer['texte'],str);self.assertTrue(answer['texte'].strip());self.assertIsInstance(answer['valeurs'],dict)

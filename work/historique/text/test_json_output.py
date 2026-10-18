import sys,json,random,math,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from json_output import dumps,loads,short_key,validate_analysis
class JsonOutputTests(unittest.TestCase):
 def test_french_numbers_and_keys(self):
  raw=dumps({'Prénom':'Élodie','Âge':12,'Score total':98.5,'Réponse': 'Elle dit « oui ».\nC:\\temp\\texte','Disponible':True,'Erreur':None});v=loads(raw)
  self.assertEqual(v['prenom'],'Élodie');self.assertIs(type(v['age']),int);self.assertIs(type(v['score_total']),float);self.assertEqual(v['reponse'],'Elle dit « oui ».\nC:\\temp\\texte');self.assertTrue(v['disponible']);self.assertIsNone(v['erreur']);self.assertIsNotNone(json.loads(raw))
 def test_rejects_non_json_duplicates_and_collisions(self):
  for v in (float('nan'),float('inf'),float('-inf'),object(),'\ud800'):
   with self.assertRaises(ValueError):dumps({'valeur':v})
  for raw in ('{"score":NaN}','{"score":1e999}','{"age":1,"age":2}','{"age":12,}',"{'age':12}"):
   with self.assertRaises(ValueError):loads(raw)
  with self.assertRaises(ValueError):dumps({'Âge':12,'age':13})
 def test_round_trip_1000_nested_french_objects(self):
  r=random.Random(1710)
  for _ in range(1000):
   value={'nom':r.choice(['Élodie','Noé','garçon','"guillemets"','ligne\nretour','\\chemin','😊']),'nombre':r.randint(-10**18,10**18),'score':r.uniform(-1e9,1e9),'valeurs':[None,True,False,{'texte':'L’été est là.'}]};self.assertEqual(loads(dumps(value)),value)
 def test_analysis_contract(self):
  value={'etat':'ok','type':'confirme','texte':'Le texte confirme cette affirmation.','score':.8,'scores':{'confirme':.8,'contredit':.1,'indetermine':.1},'modele':'scratch'};self.assertEqual(validate_analysis(value),value)
  for altered in ({**value,'score':'0.8'},{**value,'extra':1},{**value,'type':'peut_etre'}):
   with self.assertRaises(ValueError):validate_analysis(altered)

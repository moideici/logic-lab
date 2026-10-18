from pathlib import Path
import sys,json,urllib.request,urllib.error,re
R=Path(r'C:\Users\gabor\code\text-comprehension');sys.path.insert(0,str(R))
from json_output import validate_analysis
def post(raw):
 req=urllib.request.Request('http://127.0.0.1:8766/analyse',data=raw.encode(),headers={'Content-Type':'application/json'})
 try:r=urllib.request.urlopen(req,timeout=90)
 except urllib.error.HTTPError as e:r=e
 with r:body=r.read().decode();return r.status,r.headers.get('Content-Type'),body,json.loads(body)
records=[]
for kind in ('scratch','pretrained'):
 for text,claim in [('Lina donne le livre à Malo.','Malo reçoit le livre.'),('Nora n’aime pas les poires.','Nora aime les poires.'),('Hugo est à Lille. Ensuite, Hugo rejoint Nantes.','À la fin, Hugo est à Nantes.'),('Élodie regarde la pluie.','Élodie possède un chien.')]:
  status,content,raw,result=post(json.dumps({'texte':text,'affirmation':claim,'modele':kind},ensure_ascii=False));assert status==200,(status,result);assert content.startswith('application/json');assert raw.startswith('{') and raw.endswith('}');validate_analysis(result);assert isinstance(result['score'],float);records.append({'entree':text,'affirmation':claim,'sortie':result})
for raw in ('{"texte":"x","texte":"y","affirmation":"z"}','{"texte":"x","affirmation":"y","score":NaN}','{"texte":"x",}','{}'):
 status,content,body,result=post(raw);assert status==400;assert result['etat']=='erreur';assert content.startswith('application/json')
output=Path(r'C:\Users\gabor\code\logic-lab\outputs\verification-francais-json.json');output.write_text(json.dumps({'ok':True,'valid_responses':len(records),'invalid_requests_rejected':4,'cases':records},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'ok':True,'responses':len(records),'invalid_requests_rejected':4}));print(json.dumps(records[4],ensure_ascii=False))

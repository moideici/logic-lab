"""Local JSON API for the trained French classifier. No remote inference."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import argparse,json,threading
from json_output import dumps,loads,validate_analysis
ROOT=Path(__file__).resolve().parent;LOCK=threading.Lock();CACHE={}
PHRASES={'confirme':'Le texte confirme cette affirmation.','contredit':'Le texte contredit cette affirmation.','indetermine':'Le texte ne permet pas de confirmer ou de contredire cette affirmation.'}
def analyse(req):
 if not isinstance(req,dict) or set(req)-{'texte','affirmation','modele'}:raise ValueError('Champs attendus : texte, affirmation, modele')
 for key in ('texte','affirmation'):
  if not isinstance(req.get(key),str) or not req[key].strip():raise ValueError('Texte et affirmation sont obligatoires')
  if len(req[key])>2500:raise ValueError('Texte trop long pour ce prototype')
 kind=req.get('modele','pretrained')
 if kind not in ('scratch','pretrained'):raise ValueError('Modèle inconnu')
 import torch
 from safetensors.torch import load_file
 from transformers import AutoConfig,AutoModelForSequenceClassification,AutoTokenizer
 from experiment import ByteTransformer,tensors,predict,LABELS
 with LOCK:
  if kind not in CACHE:
   runs=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'models'/kind).glob('*/training.json')]
   if not runs:raise ValueError('Ce modèle est encore en préparation')
   selected=max(runs,key=lambda r:r['validation_accuracy']);folder=ROOT/'models'/kind/str(selected['seed']);device='cuda' if torch.cuda.is_available() else 'cpu'
   model=ByteTransformer() if kind=='scratch' else AutoModelForSequenceClassification.from_config(AutoConfig.from_pretrained(folder))
   model.load_state_dict(load_file(str(folder/'model.safetensors')));model.to(device);tokenizer=None if kind=='scratch' else AutoTokenizer.from_pretrained(ROOT/'models/tokenizer',local_files_only=True);CACHE[kind]=(model,tokenizer,device)
  model,tokenizer,device=CACHE[kind];cases=[{'premise':req['texte'],'hypothesis':req['affirmation']}];data=tensors(cases,kind,tokenizer);probs=predict(model,data,kind,device)[0];index=max(range(3),key=lambda i:probs[i]);conclusion=LABELS[index]
  return validate_analysis({'etat':'ok','type':conclusion,'texte':PHRASES[conclusion],'score':float(probs[index]),'scores':dict(zip(LABELS,map(float,probs))),'modele':kind})
class Handler(BaseHTTPRequestHandler):
 def send(self,value,status=200):
  data=dumps(value).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  if self.path=='/':self.send({'etat':'ok','texte':'Prototype de compréhension du français. Envoyez texte et affirmation en JSON à /analyse. Les scores ne sont pas calibrés.','exemple':{'texte':'Lina donne le livre à Malo.','affirmation':'Malo reçoit le livre.'}})
  elif self.path=='/etat':
   path=ROOT/'results/status.json';self.send(loads(path.read_text(encoding='utf-8')) if path.exists() else {'etat':'preparation'})
  else:self.send({'etat':'erreur','texte':'Adresse inconnue'},404)
 def do_POST(self):
  if self.path!='/analyse':self.send({'etat':'erreur','texte':'Adresse inconnue'},404);return
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<=20000:raise ValueError('Taille de requête invalide')
   if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':raise ValueError('Le contenu doit être du JSON')
   req=loads(self.rfile.read(n).decode('utf-8'));self.send(analyse(req))
  except (ValueError,UnicodeError,RecursionError)as e:self.send({'etat':'erreur','texte':str(e)},400)
  except Exception:self.send({'etat':'erreur','texte':'Le modèle est indisponible. Consultez les journaux locaux.'},503)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);args=p.parse_args();print(f'API français : http://127.0.0.1:{args.port}',flush=True);ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

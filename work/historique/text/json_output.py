"""Strict JSON boundary. Syntax is guaranteed by code, not by learned spelling."""
import json,math,re,unicodedata
KEY=re.compile(r'^[a-z][a-z0-9_]{0,31}$')
def short_key(key):
 if not isinstance(key,str):raise ValueError('Une clé doit être du texte')
 text=unicodedata.normalize('NFKD',key).encode('ascii','ignore').decode().lower();text=re.sub(r'[^a-z0-9]+','_',text).strip('_')
 if text and text[0].isdigit():text='v_'+text
 text=text[:32].rstrip('_')
 if not KEY.fullmatch(text):raise ValueError('Clé vide ou invalide après simplification')
 return text
def clean(value,simplify=True,depth=0):
 if depth>32:raise ValueError('JSON trop imbriqué')
 if type(value)is str:
  try:value.encode('utf-8')
  except UnicodeError:raise ValueError('Texte Unicode invalide') from None
  return value
 if value is None or type(value)in (bool,int):return value
 if type(value)is float:
  if not math.isfinite(value):raise ValueError('Un nombre JSON doit être fini')
  return value
 if type(value)is list:return [clean(v,simplify,depth+1) for v in value]
 if type(value)is dict:
  out={}
  for k,v in value.items():
   key=short_key(k) if simplify else k
   if not isinstance(key,str) or not KEY.fullmatch(key):raise ValueError('Les clés doivent être courtes et simples')
   if key in out:raise ValueError('Deux clés deviennent identiques après simplification : '+key)
   out[key]=clean(v,simplify,depth+1)
  return out
 raise ValueError('Type non pris en charge dans le JSON')
def dumps(value,simplify=True):return json.dumps(clean(value,simplify),ensure_ascii=False,allow_nan=False,separators=(',',':'))
def loads(raw):
 def pairs(items):
  out={}
  for k,v in items:
   if k in out:raise ValueError('Clé JSON répétée : '+k)
   out[k]=v
  return out
 def invalid(v):raise ValueError('Nombre non JSON : '+v)
 v=json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
 # Reject overflow such as 1e999, which the default parser converts to infinity.
 def finite(x):
  if type(x)is float and not math.isfinite(x):raise ValueError('Nombre JSON trop grand')
  if isinstance(x,dict):
   for y in x.values():finite(y)
  elif isinstance(x,list):
   for y in x:finite(y)
 finite(v);return v
def validate_analysis(value):
 if set(value)!={'etat','type','texte','score','scores','modele'}:raise ValueError('Champs de réponse incorrects')
 if value['etat']!='ok' or value['type'] not in ('confirme','contredit','indetermine') or not isinstance(value['texte'],str):raise ValueError('Réponse incorrecte')
 if type(value['score'])is not float or not 0<=value['score']<=1:raise ValueError('Score incorrect')
 if set(value['scores'])!={'confirme','contredit','indetermine'}:raise ValueError('Scores manquants')
 if any(type(v)is not float or not 0<=v<=1 for v in value['scores'].values()):raise ValueError('Scores incorrects')
 if abs(sum(value['scores'].values())-1)>1e-5:raise ValueError('Somme des scores incorrecte')
 if value['modele'] not in ('scratch','pretrained'):raise ValueError('Modèle incorrect')
 return clean(value,False)

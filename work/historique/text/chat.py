"""Local French dialogue with constrained JSON and bounded conversation context."""
from pathlib import Path
import json,threading,time,math
from json_output import clean,loads
ROOT=Path(__file__).resolve().parent;LOCK=threading.Lock();CACHE=None;CANCEL=threading.Event()
SYSTEM='''Tu es Input, un assistant local francophone. Réponds à la dernière demande, en français, en tenant compte de la conversation. Sois concis. Si une information manque, dis-le. Produis seulement un objet JSON : "texte" contient ta réponse ; "valeurs" contient les données explicitement demandées, avec des clés simples sans accents et de vrais nombres, booléens ou null. Si aucune donnée structurée n'est demandée, valeurs vaut {}. N'invente aucune donnée absente. Format : {"texte":"Une réponse en français.","valeurs":{}}.'''
SCHEMA={'type':'object','properties':{'texte':{'type':'string','minLength':1,'maxLength':1200},'valeurs':{'type':'object','maxProperties':12,'additionalProperties':{'anyOf':[{'type':'string','maxLength':200},{'type':'number'},{'type':'boolean'},{'type':'null'}]}}},'required':['texte','valeurs'],'additionalProperties':False}
def validate_response(v):
 if not isinstance(v,dict) or set(v)!={'texte','valeurs'} or not isinstance(v['texte'],str) or not v['texte'].strip() or len(v['texte'])>1200:raise ValueError('Réponse JSON incomplète ou hors format')
 if not isinstance(v['valeurs'],dict) or len(v['valeurs'])>12:raise ValueError('Valeurs JSON hors format')
 for x in v['valeurs'].values():
  if x is not None and type(x)not in (str,int,float,bool):raise ValueError('Une valeur doit être simple')
  if isinstance(x,str) and len(x)>200:raise ValueError('Valeur trop longue')
 return clean(v)
def validate_messages(req):
 if not isinstance(req,dict) or set(req)!={'messages'} or not isinstance(req['messages'],list) or not 1<=len(req['messages'])<=21:raise ValueError('Envoyez entre 1 et 21 messages de conversation')
 messages=req['messages']
 for i,m in enumerate(messages):
  if not isinstance(m,dict) or set(m)!={'role','content'} or m['role']!=('user' if i%2==0 else 'assistant') or not isinstance(m['content'],str) or not m['content'].strip() or len(m['content'])>4000:raise ValueError('Historique de conversation invalide')
 if messages[-1]['role']!='user':raise ValueError('Le dernier message doit être votre demande')
 return messages
def model():
 global CACHE
 base=json.loads((ROOT/'models/chat_base.json').read_text(encoding='utf-8'));active=ROOT/'models/chat/active.json';selected=json.loads(active.read_text(encoding='utf-8')) if active.exists() else None
 state=ROOT/'results/language_status.json';training=json.loads(state.read_text(encoding='utf-8')).get('etat')=='en_cours' if state.exists() else False
 key=json.dumps([selected,training],sort_keys=True)
 if CACHE is not None and CACHE['key']==key:return CACHE
 import torch
 from transformers import AutoModelForCausalLM,AutoTokenizer
 from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
 if CACHE is not None:del CACHE;CACHE=None;torch.cuda.empty_cache()
 torch.set_num_threads(4);tokenizer=AutoTokenizer.from_pretrained(base['path'],local_files_only=True,trust_remote_code=False);device='cuda' if torch.cuda.is_available() and not training else 'cpu';net=AutoModelForCausalLM.from_pretrained(base['path'],local_files_only=True,trust_remote_code=False,use_safetensors=True,torch_dtype=torch.bfloat16 if device=='cuda' else torch.float32,attn_implementation='sdpa').to(device)
 if selected:
  from peft import PeftModel
  net=PeftModel.from_pretrained(net,selected['path'],is_trainable=False)
 net.eval();CACHE={'key':key,'net':net,'tokenizer':tokenizer,'device':device,'adapted':bool(selected),'tokens':build_token_enforcer_tokenizer_data(tokenizer)};return CACHE
def respond(req):
 messages=validate_messages(req)
 if not (ROOT/'models/chat_base.json').exists():raise ValueError('Le modèle de dialogue est encore en téléchargement')
 import torch
 from transformers import StoppingCriteria,StoppingCriteriaList
 from lmformatenforcer import JsonSchemaParser
 from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
 with LOCK:
  began=time.perf_counter();m=model();tokenizer=m['tokenizer'];kept=list(messages)
  while True:
   prompt=tokenizer.apply_chat_template([{'role':'system','content':SYSTEM}]+kept,tokenize=False,add_generation_prompt=True,enable_thinking=False);inputs=tokenizer(prompt,return_tensors='pt').to(m['device'])
   if inputs['input_ids'].shape[1]<=2400:break
   if len(kept)<=1:raise ValueError('Message trop long pour la fenêtre de conversation')
   kept=kept[2:]
  parser=JsonSchemaParser(SCHEMA);prefix=build_transformers_prefix_allowed_tokens_fn(m['tokens'],parser)
  with torch.inference_mode():ids=m['net'].generate(**inputs,max_new_tokens=512,max_time=60,do_sample=False,prefix_allowed_tokens_fn=prefix,pad_token_id=tokenizer.eos_token_id,use_cache=True)
  raw=tokenizer.decode(ids[0,inputs['input_ids'].shape[1]:],skip_special_tokens=True).strip();answer=validate_response(loads(raw));return {'etat':'ok','reponse':answer,'modele':'input-0.2.0','base':'Qwen3-0.6B','adapte':m['adapted'],'temps_ms':round((time.perf_counter()-began)*1000),'messages_utilises':len(kept),'messages_retires':len(messages)-len(kept)}

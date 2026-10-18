"""Dialogue and structured French supervision, quarantined by conversation/world."""
from pathlib import Path
import collections,hashlib,json,random,re
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parent
def sha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def write(p,v):p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in v).encode())
def main():
 manifest=json.loads((ROOT/'corpus/manifest.json').read_text(encoding='utf-8'));cases=[];seen=set();fr_count=0
 for source in manifest['dialogues']:
  rows=pq.read_table(source['path']).to_pylist();by_id={r['message_id']:r for r in rows};fr_count+=sum(r['lang']=='fr' for r in rows)
  for r in rows:
   if r['lang']!='fr' or r['role']!='assistant' or r.get('deleted') or r.get('review_result')is False or r.get('rank')not in (None,0):continue
   if not 10<=len(r['text'])<=1400:continue
   chain=[];current=r
   while current and len(chain)<8:
    if current['lang']!='fr' or current.get('deleted'):chain=[];break
    chain.append(current);current=by_id.get(current['parent_id'])
   chain.reverse()
   if len(chain)<2 or chain[0]['role']!='prompter':continue
   expected=['prompter' if i%2==0 else 'assistant' for i in range(len(chain))]
   if [v['role'] for v in chain]!=expected:continue
   family='oasst:'+r['message_tree_id'];split='validation' if 'validation'in source['file'] or int(sha(family)[:8],16)%10==0 else 'train';messages=[{'role':'user' if c['role']=='prompter' else 'assistant','content':c['text']} for c in chain[:-1]];answer={'texte':r['text'],'valeurs':{}};key=sha([messages,answer])
   if key in seen:continue
   seen.add(key);cases.append({'id':key,'family':family,'split':split,'kind':'dialogue','messages':messages,'answer':answer,'source':'OpenAssistant/oasst2','licence':'Apache-2.0'})
 # A family has one partition even if it appears in both official source files.
 validation_families={c['family'] for c in cases if c['split']=='validation'}
 for c in cases:
  if c['family']in validation_families:c['split']='validation'
 rng=random.Random(171026);names=['Lina','Nora','Adam','Malo','Jade','Noé','Zoé','Hugo'];held_names=['Élodie','Inès','Sami','Émile']
 for split,count in [('train',3000),('validation',240),('test',240)]:
  for i in range(count):
   name=rng.choice(held_names if split=='test' else names);age=rng.randrange(8,85);quantity=rng.randrange(1,20);price=rng.randrange(50,2000)/100;score=rng.randrange(0,1000)/10;kind=i%3
   if kind==0:
    text=f'{name} a {age} ans et son score est {str(score).replace(".",",")}. Donne son nom, son age et son score dans valeurs.' if split!='test' else f'Voici une fiche : prénom {name} ; âge : {age} ; score obtenu : {str(score).replace(".",",")}. Extrais les trois données avec les clés nom, age, score.';answer={'texte':f'Voici les informations de {name}.','valeurs':{'nom':name,'age':age,'score':score}}
   elif kind==1:
    total=round(quantity*price,2);text=f'Une commande contient {quantity} cahiers à {str(price).replace(".",",")} euros chacun. Donne quantite, prix et total dans valeurs.' if split!='test' else f'Je commande des cahiers : prix unitaire {str(price).replace(".",",")} €, nombre {quantity}. Calcule le montant. Utilise quantite, prix, total.';answer={'texte':f'La commande coûte {str(total).replace(".",",")} euros.','valeurs':{'quantite':quantity,'prix':price,'total':total}}
   else:
    text=f'Je m’appelle {name} et j’ai {age} ans. Retiens ces informations.';messages=[{'role':'user','content':text},{'role':'assistant','content':json.dumps({'texte':f'D’accord, {name}.','valeurs':{}},ensure_ascii=False)},{'role':'user','content':'Quel est mon nom et quel est mon age ? Place ces données dans valeurs.'}];answer={'texte':f'Tu t’appelles {name} et tu as {age} ans.','valeurs':{'nom':name,'age':age}}
   if kind!=2:messages=[{'role':'user','content':text}]
   family=sha(['structured',name,age,quantity,price,score,kind]);cases.append({'id':sha([messages,answer]),'family':family,'split':split,'kind':['extraction','calcul','contexte'][kind],'messages':messages,'answer':answer,'source':'generated_controlled_french','licence':'project'})
 for line in (ROOT/'lexicon/senses.jsonl').read_text(encoding='utf-8').splitlines():
  c=json.loads(line)
  if c['split']=='test':continue
  definition=' '.join(c['definitions']);cases.append({'id':'lex:'+c['id'],'family':'lex:'+c['family'],'split':c['split'],'kind':'definition','messages':[{'role':'user','content':f'Que signifie « {c["mot"]} » ? Donne une définition en français.'}],'answer':{'texte':definition,'valeurs':{}},'source':c['source'],'licence':'CC-BY-SA-4.0'})
 # Exact duplicate prompts stay in one fold. Keep first consistent annotation.
 result=[];prompts={};family_splits={}
 for c in cases:
  p=sha(c['messages'])
  if p in prompts:continue
  if c['family']in family_splits and family_splits[c['family']]!=c['split']:continue
  prompts[p]=c['split'];family_splits[c['family']]=c['split'];result.append(c)
 for split in ('train','validation','test'):write(ROOT/'chat_data'/f'{split}.jsonl',[c for c in result if c['split']==split])
 report={'version':'0.2.0','french_oasst_messages':fr_count,'cases':len(result),'splits':{s:dict(collections.Counter(c['kind'] for c in result if c['split']==s)) for s in ('train','validation','test')},'wikipedia_documents_available':sum(f['rows'] for f in manifest['wikipedia']),'note':'French dialogues, controlled JSON supervision and definitions; Wikipedia remains a separate language-model stream. Tests never select checkpoints.'};(ROOT/'chat_data/manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

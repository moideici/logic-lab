"""Small reproducible French lexical corpus, with provenance for every sense."""
from pathlib import Path
import concurrent.futures,hashlib,json,time,unicodedata,urllib.request,urllib.parse
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
WORDS='apprendre comprendre lire écrire parler écouter répondre demander dire expliquer penser savoir connaître croire oublier souvenir français langue mot phrase texte sens définition exemple question réponse nom verbe adjectif pronom accord singulier pluriel présent passé futur avant après pendant toujours jamais parfois oui non vrai faux possible impossible certain incertain même autre tout aucun plusieurs beaucoup peu donner recevoir prendre poser porter garder laisser rendre mettre enlever ouvrir fermer entrer sortir aller venir partir arriver rester trouver chercher voir entendre aimer détester vouloir pouvoir devoir être avoir faire devenir vivre manger boire dormir jouer travailler maison école chambre bureau salon jardin ville village chemin route porte fenêtre table chaise livre cahier stylo sac boîte panier chat chien oiseau poisson arbre fleur fruit pomme poire eau feu terre air chaud froid grand petit jeune vieux bon mauvais rapide lent heureux triste clair sombre plein vide léger lourd près loin haut bas dedans dehors gauche droite banque souris glace voler page lettre histoire'.split()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def fetch(word):
 time.sleep(.3);base='https://kaikki.org/frwiktionary/Français/meaning/'+word[:1]+'/'+word[:2]+'/'+word+'.jsonl';url=urllib.parse.quote(base,safe=':/');cache=ROOT/'lexicon/raw'/f'{digest(word)}.jsonl';cache.parent.mkdir(parents=True,exist_ok=True)
 try:
  if cache.exists():raw=cache.read_bytes()
  else:
   req=urllib.request.Request(url,headers={'User-Agent':'FrenchTextResearchPrototype/0.1 (local educational lexical corpus)'})
   with urllib.request.urlopen(req,timeout=30)as r:raw=r.read(2_000_001)
   if len(raw)>2_000_000:raise ValueError('Entrée trop volumineuse')
   cache.write_bytes(raw)
  entries=[json.loads(s) for s in raw.decode().splitlines() if s.strip()];records=[]
  for entry in entries:
   if entry.get('lang_code')!='fr' or entry.get('word')!=word:continue
   family=digest(unicodedata.normalize('NFC',word).casefold());bucket=int(family[:8],16)%10;split='train' if bucket<8 else 'validation' if bucket==8 else 'test'
   for i,sense in enumerate(entry.get('senses',[])):
    glosses=sense.get('glosses',[])
    if not glosses:continue
    # Quoted examples can have separate rights. Keep only unquoted examples.
    examples=[e['text'] for e in sense.get('examples',[]) if e.get('text') and not e.get('ref')]
    r={'id':digest([word,entry.get('pos'),glosses]),'family':family,'split':split,'mot':word,'nature':entry.get('pos_title',entry.get('pos')),'definitions':glosses,'exemples':examples,'marques':sense.get('tags',[]),'formes':entry.get('forms',[]),'synonymes_du_sens':sense.get('synonyms',[]),'antonymes_du_sens':sense.get('antonyms',[]),'relations_non_desambiguees':{k:entry[k] for k in ('synonyms','antonyms') if entry.get(k)},'source':{'wiktionnaire':'https://fr.wiktionary.org/wiki/'+urllib.parse.quote(word),'auteurs':'Contributeurs du Wiktionnaire','historique':'https://fr.wiktionary.org/w/index.php?title='+urllib.parse.quote(word)+'&action=history','extraction':url,'raw_sha256':hashlib.sha256(raw).hexdigest(),'licence':'CC-BY-SA-4.0','licence_url':'https://creativecommons.org/licenses/by-sa/4.0/','modifications':'Extraction des champs, retrait des traductions et exemples cités, partition par mot.'}}
    records.append(r)
  return word,records,None
 except Exception as e:return word,[],str(e)
def main():
 records=[];errors=[];source=ROOT/'lexicon';source.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  for word,items,error in pool.map(fetch,WORDS):
   records.extend(items)
   if error:errors.append({'mot':word,'erreur':error})
   print(json.dumps({'mot':word,'sens':len(items),'erreur':error},ensure_ascii=False),flush=True)
 unique={r['id']:r for r in records};records=list(unique.values());raw=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records).encode();(source/'senses.jsonl').write_bytes(raw)
 for split in ('train','validation','test'):
  cases=[{'id':r['id'],'family':r['family'],'texte':f"Mot : {r['mot']}. Nature : {r['nature']}. Définition : {' '.join(r['definitions'])}"+''.join(' Exemple : '+e for e in r['exemples']),'source':r['source']} for r in records if r['split']==split];(source/f'{split}.jsonl').write_bytes(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases).encode())
 manifest={'created_at':datetime.now(timezone.utc).isoformat(),'source':'Wiktionnaire français, extraction Kaikki frwiktionary','selection':'Liste pédagogique de mots courants ; pas un échantillon représentatif du français','language':'fr','licence':'CC-BY-SA-4.0','words_requested':len(WORDS),'words_imported':len({r['mot'] for r in records}),'senses':len(records),'sha256':hashlib.sha256(raw).hexdigest(),'splits':{s:sum(r['split']==s for r in records) for s in ('train','validation','test')},'excluded_quoted_examples':True,'errors':errors,'usage':'Préparation du prochain cycle lexical. Non injecté dans la comparaison initiale 0.1.0 déjà en cours.'};(source/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False),flush=True)
if __name__=='__main__':main()

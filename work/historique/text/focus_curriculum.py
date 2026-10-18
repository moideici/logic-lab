"""Exact teachers and new semantic families for a 30-minute French session."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,random,collections
ROOT=Path(__file__).resolve().parent
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def family(kind,values):return digest([kind,values])
def legacy_family(c):
 v=c['answer']['valeurs'];k=c['kind']
 if k=='calcul' and 'quantite'in v and 'prix'in v:return family('prix',[v['quantite'],str(Decimal(str(v['prix'])).normalize())])
 if k=='extraction' and set(v)=={'nom','age','score'}:return family('fiche',[v['nom'],v['age'],str(Decimal(str(v['score'])).normalize())])
 if k=='contexte' and set(v)=={'nom','age'}:return family('identite',[v['nom'],v['age']])
 return digest(['legacy',c['messages']])
def decimal_text(v):return format(Decimal(str(v)),'f').replace('.',',')
def make(rng,kind,split):
 names={'train':['Alice','Benoît','Clara','David','Emma','Félix','Gabriel','Isabelle'],'validation':['Camille','Louis','Sarah','Youssef'],'test':['Anaïs','Mathis','Salomé','Nassim']}[split];name=rng.choice(names);age=rng.randint(7,90);n=rng.randint(1,24);price=Decimal(rng.randint(25,2999))/100;variant=rng.randrange(6) if split=='train' else rng.randrange(6,8) if split=='validation' else rng.randrange(8,10);messages=[]
 if kind=='calcul':
  op=rng.choice(['prix','prix','addition','soustraction','multiplication','remise']);a=rng.randint(1,800);b=rng.randint(1,99)
  if op=='prix':
   total=price*n;v={'quantite':n,'prix':float(price),'total':float(total)};world=family('prix',[n,str(price.normalize())]);sentences=[f'Il y a {n} articles à {decimal_text(price)} euros pièce.',f'Quantité commandée : {n}. Prix unitaire : {decimal_text(price)} euros.',f'Pour acheter {n} cahiers, chacun coûte {decimal_text(price)} euros.',f'{name} choisit {n} stylos vendus {decimal_text(price)} euros l’un.',f'La commande compte {n} unités, à {decimal_text(price)} euros par unité.',f'Calcule une commande : {n} objets ; coût individuel {decimal_text(price)} euros.',f'Je commande des cahiers : prix unitaire {decimal_text(price)} euros, nombre {n}.',f'Une facture doit contenir {n} exemplaires à {decimal_text(price)} euros.',f'Au magasin, chaque carnet vaut {decimal_text(price)} euros. {name} en prend {n}.',f'Le panier de {name} contient {n} unités. Une unité revient à {decimal_text(price)} euros.'];question=sentences[variant]+' Remplis les champs quantite, prix et total de valeurs avec des nombres. Une phrase seule ne suffit pas.';answer={'texte':'Voici le montant et les données de la commande.','valeurs':v}
  elif op=='remise':
   rate=rng.choice([5,10,15,20,25,50]);amount=Decimal(a);total=amount*(100-rate)/100;v={'prix':a,'remise':rate,'total':float(total)};world=family(op,[a,rate]);question=f'Un produit vaut {a} euros. Une réduction de {rate} % est appliquée. Donne prix, remise et total après réduction dans valeurs.' if variant<6 else f'Applique {rate} % de réduction sur {a} euros. Je veux un objet valeurs contenant prix, remise, total.';answer={'texte':'Voici le prix après réduction.','valeurs':v}
  else:
   if op=='soustraction':a=max(a,b);result=a-b;symbol='-';phrase=f'On a {a} unités et on en retire {b}.'
   elif op=='addition':result=a+b;symbol='+';phrase=f'On réunit {a} unités et {b} autres unités.'
   else:result=a*b;symbol='×';phrase=f'On dispose de {b} groupes contenant chacun {a} unités.'
   v={'a':a,'b':b,'resultat':result};world=family(op,[a,b]);intro=(f'Calcule {a} {symbol} {b}.' if variant%2==0 else phrase) if variant<6 else f'Les nombres a et b valent {a} et {b}. Effectue leur {op}.' if variant<8 else f'Effectue cette opération : a={a}, b={b}, {op}. Je veux le résultat exact.';question=intro+' Renvoie a, b et resultat dans valeurs, sous forme de nombres.';answer={'texte':'Voici le résultat du calcul.','valeurs':v}
 elif kind=='structure':
  if rng.random()<.65:
   score=Decimal(rng.randint(0,1000))/10;v={'nom':name,'age':age,'score':float(score)};world=family('fiche',[name,age,str(score.normalize())]);templates=[f'{name} a {age} ans et un score de {decimal_text(score)}.',f'Fiche de {name} : âge {age} ; score {decimal_text(score)}.',f'Le score de {name} est {decimal_text(score)}. Son âge est {age} ans.',f'Prénom : {name}. Score : {decimal_text(score)}. Âge : {age}.',f'Nous parlons de {name}, âgé de {age} ans, avec {decimal_text(score)} points.',f'{name} obtient {decimal_text(score)} points à {age} ans.',f'Voici une fiche : prénom {name} ; âge : {age} ; score obtenu : {decimal_text(score)}.',f'Un dossier indique : {name}, {age} ans, résultat {decimal_text(score)} points.',f'{age} est l’âge de {name}. Le relevé de points affiche {decimal_text(score)}.',f'Pour {name}, le relevé comporte {decimal_text(score)} points et {age} ans.'];question=templates[variant]+' Extrais nom, age et score dans valeurs.';answer={'texte':'Voici les informations demandées.','valeurs':v}
  else:
   available=bool(rng.randrange(2));text=rng.choice(['Il dit « bonjour ».','Une ligne\npuis une autre.','L’été à côté du château.','Le dossier C:\\notes\\français.']);v={'nom':name,'disponible':available,'age':None,'note':text};world=family('types',[name,available,text]);question=f'Le nom est {name}. Disponible : {"oui" if available else "non"}. L’âge est inconnu. La note exacte est : '+json.dumps(text,ensure_ascii=False)+'. Remplis valeurs avec nom, disponible (booléen), age (null) et note (texte conservé).';answer={'texte':'Les types et les informations sont conservés.','valeurs':v}
 elif kind=='contexte':
  changed=rng.random()<.6;new_age=age+rng.randint(1,5);world=family('identite',[name,age]);question='Quel est mon nom et mon age ? Remplis ces deux champs dans valeurs.'
  messages=[{'role':'user','content':f'Je m’appelle {name} et j’ai {age} ans.'},{'role':'assistant','content':json.dumps({'texte':'Je garde ces informations pour cette conversation.','valeurs':{}},ensure_ascii=False)}]
  if changed:messages.extend([{'role':'user','content':f'Correction : mon âge est {new_age} ans, et non {age}.'},{'role':'assistant','content':json.dumps({'texte':'La correction est prise en compte.','valeurs':{}},ensure_ascii=False)}]);age=new_age
  if variant>=6:question='En reprenant nos échanges précédents, indique mon nom et mon age actuels dans valeurs.'
  answer={'texte':'Voici les dernières informations de la conversation.','valeurs':{'nom':name,'age':age}}
 else:raise ValueError(kind)
 messages.append({'role':'user','content':question});return {'id':digest(messages),'family':world,'split':split,'kind':kind,'messages':messages,'answer':answer,'teacher_operation':op if kind=='calcul' else None,'source':'exact_decimal_teacher_and_controlled_context','licence':'project'}
def build(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True);seen=set();prompts=set();legacy=0
 for split in ('train','validation','test'):
  for line in (ROOT/'chat_data'/f'{split}.jsonl').read_text(encoding='utf-8').splitlines():
   c=json.loads(line);seen.add(legacy_family(c));prompts.add(digest(c['messages']));legacy+=1
 rng=random.Random(172210);rows=[]
 for split,counts in [('train',{'calcul':2400,'structure':1400,'contexte':600}),('validation',{'calcul':48,'structure':32,'contexte':24}),('test',{'calcul':48,'structure':32,'contexte':24})]:
  for kind,n in counts.items():
   count=0;attempts=0
   while count<n:
    c=make(rng,kind,split);attempts+=1
    if attempts>n*100:raise RuntimeError('Pas assez de mondes sémantiques distincts')
    key=digest(c['messages'])
    if c['family']in seen or key in prompts:continue
    seen.add(c['family']);prompts.add(key);rows.append(c);count+=1
  cases=[c for c in rows if c['split']==split];raw=''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases).encode();(output/f'{split}.jsonl').write_bytes(raw)
 natural=[('Salut, tu marches ?','Salut ! Oui, je fonctionne. Que veux-tu essayer ?'),('Coucou, ça va ?','Coucou ! Je suis prêt à discuter. Et toi ?'),('Bonjour !','Bonjour ! Que puis-je faire pour toi ?'),('Hey, comment vas-tu ?','Salut ! Je suis disponible pour échanger avec toi.'),('Quelle est ta phrase préférée ?','Je n’ai pas de préférence personnelle, mais je te propose : « On apprend en essayant. »'),('Propose une phrase inspirante.','« Chaque petit progrès compte. »'),('Donne un proverbe français.','« Petit à petit, l’oiseau fait son nid. »'),('Tu peux arrêter de te présenter ?','Oui. Je vais répondre directement à tes questions.'),('Explique simplement pourquoi il pleut.','L’eau des nuages forme des gouttes. Lorsqu’elles deviennent assez lourdes, elles tombent en pluie.'),('Quelle est la différence entre un chat et un chien ?','Le chat est un félin et le chien est un canidé. Ils ont des comportements et des besoins différents.'),('Que veut dire généreux ?','Une personne généreuse partage volontiers ce qu’elle possède ou donne de son temps.'),('À quoi sert une bibliothèque ?','Une bibliothèque permet de consulter ou d’emprunter des livres et d’autres documents.'),('Réécris : je va au marché.','Je vais au marché.'),('Mets le pluriel : un cheval.','Des chevaux.'),('Réponds en une phrase : pourquoi lire ?','Lire permet de découvrir des idées, d’apprendre et d’imaginer.'),('Trouve un synonyme de rapide.','Véloce est un synonyme de rapide.'),('Donne le contraire de chaud.','Le contraire de chaud est froid.'),('Raconte une histoire en deux phrases.','Un enfant trouva une graine dans son jardin. Il la planta et vit pousser une fleur.'),('Dis-moi quelque chose sur la Lune.','La Lune est le satellite naturel de la Terre.'),('De quelle couleur est mon sac ?','Tu ne m’as pas indiqué la couleur de ton sac.'),('Merci pour ton aide !','Avec plaisir !'),('Résume : Lina entre, ouvre le livre et commence à lire.','Lina entre et se met à lire.'),('Tu as des sentiments ?','Je n’ai pas de sentiments, mais je peux discuter et t’aider.'),('Propose une activité pour apprendre du vocabulaire.','Choisis cinq mots nouveaux et écris une phrase différente avec chacun.')]
 for question,text in natural:rows.append({'id':digest(question),'family':digest(['natural',question]),'split':'train','kind':'dialogue','messages':[{'role':'user','content':question}],'answer':{'texte':text,'valeurs':{}},'source':'authored_french_dialogue','licence':'project'})
 for split in ('train','validation','test'):write_rows=[c for c in rows if c['split']==split];(output/f'{split}.jsonl').write_bytes(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in write_rows).encode())
 report={'seed':172210,'legacy_cases_quarantined':legacy,'split_counts':{s:dict(collections.Counter(c['kind'] for c in rows if c['split']==s)) for s in ('train','validation','test')},'files':{s:hashlib.sha256((output/f'{s}.jsonl').read_bytes()).hexdigest() for s in ('train','validation','test')},'teacher':'Decimal arithmetic; booleans/null/escaping; latest-context corrections; authored natural French','split_policy':'Unique semantic world and prompt across all new splits; all legacy worlds excluded. New test names and price/record templates held out.'};(output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');return report
if __name__=='__main__':print(json.dumps(build(ROOT/'chat_data/focus30'),ensure_ascii=False))

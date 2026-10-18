"""French controlled inference benchmark; whole semantic worlds stay in one fold."""
from pathlib import Path
import hashlib,json,random,collections
ROOT=Path(__file__).resolve().parent
TRAIN_NAMES=[('Lina','elle'),('Malo','il'),('Nora','elle'),('Adam','il'),('Zoé','elle'),('Hugo','il'),('Jade','elle'),('Noé','il')]
NEW_NAMES=[('Inès','elle'),('Sami','il'),('Léa','elle'),('Yanis','il'),('Rose','elle'),('Émile','il')]
OBJECTS=['le livre','le sac','le cahier','le ballon','le stylo','le colis']
FRUITS=['les poires','les pommes','les fraises','les cerises','les abricots','les bananes']
CITIES=['Lyon','Nantes','Lille','Tours','Nice','Rouen']
BOXES=['le tiroir','le placard','le coffre','le panier','le casier','le carton']
ROOMS=['le bureau','le salon','l’atelier','le garage','le grenier','le couloir']
BUILDINGS=['la maison','le chalet','l’immeuble','le hangar','le pavillon','le château']
CATEGORIES=['negation','roles','temporal','coreference','spatial']
LABELS=['confirme','contredit','indetermine']
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def cap(s):return s[0].upper()+s[1:]
def make_world(rng,kind,names,template,depth=2):
 people=rng.sample(names,3);(a,pronoun),(b,_),(c,_)=people;obj=rng.sample(OBJECTS,3);fruit=rng.sample(FRUITS,3);cities=rng.sample(CITIES,3);boxes=rng.sample(BOXES,3);rooms=rng.sample(ROOMS,2);buildings=rng.sample(BUILDINGS,2);negative=bool(rng.randrange(2));query_negative=bool(rng.randrange(2));t=template
 # The latent identity ignores surface templates and query polarity.
 identity={'negation':[kind,people,fruit[:2],obj[0],negative], 'roles':[kind,people,obj[:2]], 'temporal':[kind,people,cities,obj[0]], 'coreference':[kind,people,obj,boxes[:2]], 'spatial':[kind,people[:2],rooms,buildings,obj[0],depth]}[kind]
 def be(subject,place):return f'{subject} '+('n’est pas' if query_negative else 'est')+f' dans {place}.'
 if kind=='negation':
  verb='apprécie' if t==2 else 'aime';deny=f'n’{verb} pas';fact=f'{a} {deny if negative else verb} {fruit[0]}.';distractor=f'{b} {verb} {fruit[1]}. {c} porte {obj[0]}.'
  premise=[fact+' '+distractor,distractor+' '+fact,f'À propos des fruits : {fact} {distractor}'][t]
  def h(neg,fr):return f'{a} '+('n’aime pas' if neg else 'aime')+f' {fr}.'
  hypotheses=[h(negative,fruit[0]),h(not negative,fruit[0]),h(query_negative,fruit[1])]
 elif kind=='roles':
  premise=[f'Pendant cet échange, {a} donne {obj[0]} à {b}. {c} mentionne {obj[1]}.',f'{b} reçoit {obj[0]} de {a}. {c} mentionne {obj[1]}.',f'Pendant l’échange, {obj[0]} passe de {a} à {b}. {c} mentionne {obj[1]}.'][t]
  def h(person,item):return f'Pendant cet échange, {person} '+('ne reçoit pas' if query_negative else 'reçoit')+f' {item}.'
  hypotheses=[h(b,obj[0]),h(a,obj[0]),h(b,obj[1])]
 elif kind=='temporal':
  premise=[f'{a} est à {cities[0]}. Ensuite, {a} se déplace à {cities[1]}. {b} reste à {cities[2]}. {c} porte {obj[0]}.',f'D’abord, {a} se trouve à {cities[0]}. Plus tard, {a} rejoint {cities[1]}. {b} est à {cities[2]}. {c} tient {obj[0]}.',f'Après avoir quitté {cities[0]}, {a} arrive à {cities[1]}. {b} demeure à {cities[2]}. {c} a {obj[0]} dans les mains.'][t]
  def h(person,city):return f'À la fin, {person} '+('n’est pas' if query_negative else 'est')+f' à {city}.'
  hypotheses=[h(a,cities[1]),h(a,cities[0]),h(c,cities[1])]
 elif kind=='coreference':
  premise=[f'{a} prend {obj[0]}. {cap(pronoun)} le pose dans {boxes[0]}. {b} range {obj[1]} dans {boxes[1]}. {c} mentionne {obj[2]}.',f'{a} tient {obj[0]}, puis {pronoun} le met dans {boxes[0]}. {b} place {obj[1]} dans {boxes[1]}. {c} mentionne {obj[2]}.',f'{obj[0].capitalize()} est pris par {a}. Ensuite, {pronoun} le dépose dans {boxes[0]}. {b} laisse {obj[1]} dans {boxes[1]}. {c} mentionne {obj[2]}.'][t]
  hypotheses=[be(cap(obj[0]),boxes[0]),be(cap(obj[0]),boxes[1]),be(cap(obj[2]),boxes[0])]
 else:
  chain=f'{cap(rooms[0])} est dans {buildings[0]}.' if depth==2 else f'{cap(rooms[0])} est dans l’aile nord. L’aile nord se situe dans {buildings[0]}.'
  first=[f'{a} est dans {rooms[0]}.',f'{a} se trouve dans {rooms[0]}.',f'{a} occupe {rooms[0]}.'][t]
  premise=f'{first} {chain} {cap(rooms[1])} est dans {buildings[1]}. {b} porte {obj[0]}.'
  hypotheses=[be(a,buildings[0]),be(a,buildings[1]),be(b,buildings[0])]
 if kind!='negation' and query_negative:hypotheses[0],hypotheses[1]=hypotheses[1],hypotheses[0]
 return identity,premise,hypotheses
def build(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True);rng=random.Random(17102026);seen=set();manifest={'version':'0.1.0','seed':17102026,'labels':LABELS,'scope':'controlled French inference; not a claim of general text understanding','splits':{}}
 plan={'train':(240,TRAIN_NAMES,(0,1),2,CATEGORIES),'validation':(40,TRAIN_NAMES,(0,1),2,CATEGORIES),'test_iid':(40,TRAIN_NAMES,(0,1),2,CATEGORIES),'test_rephrasing':(40,TRAIN_NAMES,(2,),2,CATEGORIES),'test_new_names':(40,NEW_NAMES,(0,1),2,CATEGORIES),'test_composition':(200,TRAIN_NAMES,(0,1),3,['spatial'])}
 for split,(count,names,templates,depth,categories) in plan.items():
  cases=[]
  for kind in categories:
   for family in range(count):
    while True:
     identity,premise,hs=make_world(rng,kind,names,rng.choice(templates),depth);key=digest(identity)
     if key not in seen:seen.add(key);break
    for label,hypothesis in enumerate(hs):cases.append({'id':digest([key,hypothesis]),'family':key,'category':kind,'premise':premise,'hypothesis':hypothesis,'label':label})
  rng.shuffle(cases);text=''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases);(output/(split+'.jsonl')).write_bytes(text.encode('utf-8'));manifest['splits'][split]={'cases':len(cases),'families':len({c['family'] for c in cases}),'sha256':hashlib.sha256(text.encode()).hexdigest(),'labels':dict(collections.Counter(LABELS[c['label']] for c in cases))}
 # Check family separation, duplicate pairs, and balanced labels before fitting.
 all_cases=[json.loads(line) for p in output.glob('*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()];pairs=[(c['premise'],c['hypothesis']) for c in all_cases];assert len(pairs)==len(set(pairs));assert all(len(set(v['labels'].values()))==1 for v in manifest['splits'].values())
 (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');return manifest
if __name__=='__main__':print(json.dumps(build(ROOT/'data'),ensure_ascii=False,indent=2))

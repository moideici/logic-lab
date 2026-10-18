from pathlib import Path
import json
ROOT=Path(__file__).parent
def edit(name,old,new):
    p=ROOT/name;s=p.read_text(encoding='utf-8');assert s.count(old)==1,(name,old[:60],s.count(old));p.write_text(s.replace(old,new),encoding='utf-8')

p=ROOT/'web/engine.js';p.write_text(p.read_text(encoding='utf-8')+(ROOT/'garry-engine.txt').read_text(encoding='utf-8'),encoding='utf-8')
edit('logic_arena/neural.py', 'return cls({game: NeuralPolicy.load(Path(directory)/f"{game}.json") for game in SPECS})', '''from .general import GarryPolicy
        path=Path(directory)
        suite=cls.__new__(cls)
        suite.general=GarryPolicy.load(path if path.is_file() else path/'garry.json')
        suite.models={game:suite.general.for_game(game) for game in SPECS}
        suite.core=suite.general.core
        return suite''')
edit('logic_arena/neural.py', 'def save(self, directory):\n        for game, model in self.models.items():', '''def save(self, directory):
        if hasattr(self,'general'):
            path=Path(directory)
            self.general.save(path if path.suffix=='.json' else path/'garry.json')
            return
        for game, model in self.models.items():''')
start='        path = MODEL_DIR/f"{obs[\'game\']}.json"'
p=ROOT/'logic_arena/neural.py';s=p.read_text();a=s.index(start);b=s.index('        logits = model.logits(obs)',a)
s=s[:a]+'''        from .general import GarryPolicy
        path = MODEL_DIR/'garry.json'
        if not path.is_file():
            raise ValueError('Modèle Garry absent ; lancer examples/fuse_garry.py')
        stamp = path.stat().st_mtime_ns
        with _MODEL_CACHE_LOCK:
            cached = _MODELS.get('garry')
            if cached is None or cached[0] != stamp:
                _MODELS['garry'] = stamp, GarryPolicy.load(path)
            model = _MODELS['garry'][1].for_game(obs['game'])
'''+s[b:];p.write_text(s,encoding='utf-8')
edit('logic_arena/connect4_wasm.py','remaining_ms = max(0,','remaining_ms = max(0.,')
edit('pyproject.toml','version = "1.1.0"','version = "2.0.0"')
p=ROOT/'web/agents.json';d=json.loads(p.read_text());d.update(version='2.0.0',name='garry');d['agents']={g:{'codename':'garry','version':'2.0.0','mode':g} for g in d['agents']};p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')

edit('web/app.js', 'Game,Network,NAMES,SPECS,STYLES,TEMPS,linkNetworks,rng','Game,Network,GarryModel,NAMES,SPECS,STYLES,TEMPS,linkNetworks,rng')
edit('web/app.js','const models={};','const models={};\nlet general=null;\nfunction useGarry(data){const next=data instanceof GarryModel?data:new GarryModel(data);general=next;for(const name of Object.keys(NAMES))models[name]=next.forGame(name);cancelInference(new DOMException(\'Modèle remplacé\',\'AbortError\'),true);}')
edit('web/app.js', "indexedDB.open('logic-lab-v2',1)","indexedDB.open('logic-lab-garry',1)")
edit('web/app.js',"for(const [name,m] of Object.entries(models))tx.objectStore('models').put(m.export(),name);", "tx.objectStore('models').put(general.export(),'garry');")
edit('web/app.js','${m.input} → 48 ⇄ 48 → ${m.output}','${m.input} → ${m.hidden} ⇄ ${m.hidden} → ${m.output}')
edit('web/app.js','for(const data of d.models)models[data.game]=new Network(data);linkNetworks(models);','useGarry(d.model);')
edit('web/app.js','models:Object.values(models).map(m=>m.export()),episodes','model:general.export(),episodes')
edit('web/app.js',"download(`logic-lab-suite.json`,JSON.stringify({format:'logic-arena-suite-v1',models:Object.values(models).map(m=>m.export())}));","download(`garry-${AGENT_VERSION}.json`,JSON.stringify(general.export()));")
p=ROOT/'web/app.js';s=p.read_text();a=s.index("const data=JSON.parse(await file.text()),incoming={};");b=s.index("pause();lastDecision=null;await persistModels();",a)
s=s[:a]+"const data=JSON.parse(await file.text());useGarry(data.format==='logic-arena-suite-v1'?GarryModel.fuse(data.models):data);"+s[b:]
a=s.index('const data=await Promise.all(Object.keys(NAMES).map(async name=>');b=s.index('lastDecision=null;await persistModels();',a)
s=s[:a]+"const response=await fetch('models/garry.json');if(!response.ok)throw Error('Chargement de Garry impossible');useGarry(await response.json());"+s[b:]
a=s.index('async function initialize()');s=s[:a]+'''async function initialize(){render();preset();drawLoss();try{db=await openDB();const stored=await storedModel('garry');if(stored)try{useGarry(stored);}catch{}if(!general){const response=await fetch('models/garry.json');if(!response.ok)throw Error('Garry indisponible');useGarry(await response.json());}emit('created');render();}catch(error){$('model-status').textContent=error.message;toast(error.message);}}
initialize();
'''
s=s.replace('Module partagé connecté aux six jeux.','Un seul modèle pour les six jeux.').replace('Modèles importés. Module commun connecté aux six jeux.','Garry importé pour les six jeux.').replace('Les six modèles initiaux et leur module partagé ont été restaurés.','Garry initial a été restauré.').replace('Les six jeux utilisent le module mis à jour.','Les six jeux utilisent le même Garry mis à jour.').replace('Le module commun a été mis à jour pour les six jeux.','Garry a été mis à jour pour les six jeux.')
p.write_text(s,encoding='utf-8')
edit('web/trainer.js',"import {Game,Network,linkNetworks}","import {Game,GarryModel,NAMES}")
edit('web/trainer.js','const models=Object.fromEntries(e.data.models.map(d=>[d.game,new Network(d)]));\n linkNetworks(models);',"const general=new GarryModel(e.data.model);\n const models=Object.fromEntries(Object.keys(NAMES).map(g=>[g,general.forGame(g)]));")
edit('web/trainer.js','models:Object.values(models).map(m=>m.export()),cancelled','model:general.export(),cancelled')
p=ROOT/'web/inference-worker.js';p.write_text('''import {GarryModel,rng} from './engine.js';
import {chooseDecision} from './decision.js';
let general=null;
self.onmessage=e=>{
 const {id,model,observation,legal,level,style,planning,seed}=e.data;
 try{
  if(model)general=new GarryModel(model);
  if(!general)throw Error('Garry non initialisé');
  const result=chooseDecision(general.forGame(observation.game),observation,legal,{level,style,planning,random:rng(seed)});
  self.postMessage({id,result});
 }catch(error){self.postMessage({id,error:error.message});}
};
''',encoding='utf-8')

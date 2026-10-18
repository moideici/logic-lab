from pathlib import Path
import json
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'product'
def read(p):return (ROOT/p).read_text(encoding='utf-8')
def write(p,s):
    f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8',newline='\n')

s=read('web/trainer.js').replace("{Game,GarryModel,NAMES}","{Game,GarryModel,NAMES,rng}")
s="import {parseRepertoire,sampleRepertoire} from './repertoire.js';\n"+s
s=s.replace(' const model=models[e.data.game]', ''' let bank=null;try{const response=await fetch('./models/garry-repertoire.json');if(response.ok)bank=parseRepertoire(await response.json());}catch{}
 const random=rng(e.data.seed??0),repertoireSeen=new Set();let repertoireExamples=0;
 const learnCase=(name,rate)=>{const c=sampleRepertoire(bank,name,random);if(!c)return null;const value=models[name].train(c.observation,c.legal,c.action,rate);repertoireExamples++;repertoireSeen.add(c.id);return value;};
 const model=models[e.data.game]''')
s=s.replace('   if(examples%4===0&&others.length)', '''   if(examples%3===0){const value=learnCase(model.game,lr*.5);if(value!==null){loss+=value;episodeLoss+=value;examples++;count++;}}
   if(examples%4===0&&others.length)''')
old="const name=others[rehearsals%others.length];let env=replay[name];"
new="const name=others[rehearsals%others.length];const bankLoss=rehearsals%2===0?learnCase(name,lr*.3):null;if(bankLoss!==null){rehearsals++;}else{let env=replay[name];"
s=s.replace(old,new).replace('env.step(target);rehearsals++;}', 'env.step(target);rehearsals++;}}')
s=s.replace("type:'progress',episode:", "type:'progress',repertoire_examples:repertoireExamples,repertoire_unique:repertoireSeen.size,repertoire_size:bank?.size??0,episode:").replace("type:'finished',model:", "type:'finished',repertoire_examples:repertoireExamples,repertoire_unique:repertoireSeen.size,repertoire_size:bank?.size??0,model:")
write('web/trainer.js',s);write('web/repertoire.js',(Path(__file__).parent/'repertoire.js').read_text(encoding='utf-8'))
s=read('web/app.js').replace("Rappels sur les autres jeux", "Rappels sur les autres jeux")
s=s.replace("${d.rehearsals} rappels sur les autres jeux. Poids appliqués à l’arrêt.", "${d.rehearsals} rappels · ${d.repertoire_unique??0} épreuves variées. Poids appliqués à l’arrêt.")
s=s.replace("${fmt(d.examples)} exemples, ${fmt(d.rehearsals)} rappels. Les six jeux utilisent le même Garry mis à jour.", "${fmt(d.examples)} exemples, ${fmt(d.rehearsals)} rappels, ${fmt(d.repertoire_unique??0)} épreuves variées. Garry a été mis à jour.")
write('web/app.js',s)
s=read('web/engine.js').replace("import {agentIdentity}","import {agentIdentity,AGENT_VERSION}").replace("d.version==='3.0.0'", "['3.0.0','3.1.0'].includes(d.version)").replace("version:'3.0.0',position_head:","version:AGENT_VERSION,position_head:")
write('web/engine.js',s)
s=read('logic_arena/general.py').replace('import copy','import copy\nfrom .identity import AGENT_VERSION').replace("'version':'3.0.0','position_head':", "'version':AGENT_VERSION,'position_head':").replace("('garry-mlp-v2','3.0.0'))", "('garry-mlp-v2','3.0.0'),('garry-mlp-v2','3.1.0'))")
write('logic_arena/general.py',s)
for p in ('web/agents.json','web/index.html','pyproject.toml'):
    s=read(p).replace('3.0.0','3.1.0')
    if p=='web/agents.json':s=s.replace('"previous_version": "1.0.0"','"previous_version": "3.0.0"')
    if p=='web/index.html':s=s.replace('Un exemple sur quatre rejoue un autre jeu pour entretenir le module partagé.', 'Des épreuves variées complètent les parties : pièges, défenses, fins de partie et nouvelles grilles. Les situations difficiles reviennent plus souvent ; les autres jeux sont aussi rejoués.')
    write(p,s)
for p in ('tests/garry.test.mjs','tests/levels.test.mjs','tests/test_versions.py'):
    write(p,read(p).replace("'3.0.0'","'3.1.0'"))

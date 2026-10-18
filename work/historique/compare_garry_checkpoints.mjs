// Comparer les poids à moteur et budgets identiques ; la référence reste figée.
import fs from 'node:fs';
import {parseArgs} from 'node:util';
import {Game,GarryModel} from '../web/engine.js';
import {connectDecision,connectReady} from '../web/connect4-runtime.js';
import {Network} from '../versions/1.0.0/web/engine.js';
import {connectSearch} from '../versions/1.0.0/web/fast-search.js';
await connectReady;
const {values}=parseArgs({options:{before:{type:'string'},after:{type:'string'},output:{type:'string'},episodes:{type:'string',default:'40'},seed:{type:'string',default:'9200000'},nodes:{type:'string',default:'3000000'}}});
if(!values.before||!values.after||!values.output)throw Error('Fichiers before, after et output requis');
const episodes=Number(values.episodes),seed=Number(values.seed),nodes=Number(values.nodes);
if(!Number.isInteger(episodes)||episodes<2||episodes%2||!Number.isInteger(nodes)||nodes<1||!Number.isInteger(seed))throw Error('Paramètres invalides');
const models={before:new GarryModel(JSON.parse(fs.readFileSync(values.before))),after:new GarryModel(JSON.parse(fs.readFileSync(values.after)))};
const opponent=new Network(JSON.parse(fs.readFileSync(new URL('../versions/1.0.0/web/models/connect4.json',import.meta.url))));
const report={game:'connect4',seed,episodes,current_node_budget:nodes,reference_node_budget:5000,paired_openings:true,opponent:'frozen_1.0.0',
 note:'Moteur et budgets identiques pour before/after. La référence 1.0.0 utilise son moteur et 5 000 nœuds. Plafond de sécurité : 10 secondes. Ce lot sert de contrôle, pas de garantie générale.',
 before:{wins:0,losses:0,draws:0},after:{wins:0,losses:0,draws:0},samples:[]};
const budget=limit=>({limit,nodes:0,tick(){if(this.nodes>=limit)throw Error('budget');this.nodes++;}});
for(let i=0;i<episodes;i++){
 const sample={seed:seed+Math.floor(i/2),player:1+i%2};
 for(const [name,model] of Object.entries(models)){
  const g=new Game('connect4',sample.seed),view=model.forGame('connect4');
  for(let n=0;n<6;n++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
  const began=performance.now();
  while(!g.done){const o=g.obs(),legal=g.legal();const d=g.player===sample.player?connectDecision(o,legal,view.forward(o).z,budget(nodes),{timeMs:10000}):connectSearch(o,legal,opponent.forward(o).z,budget(5000));g.step(d.action);}
  const outcome=g.winner===0?'draws':g.winner===sample.player?'wins':'losses';report[name][outcome]++;
  sample[name]={winner:g.winner,moves:g.moves,ms:Math.round(performance.now()-began)};
 }
 report.samples.push(sample);
 if((i+1)%10===0)console.log(JSON.stringify({completed:i+1,before:report.before,after:report.after}));
 fs.writeFileSync(values.output,JSON.stringify(report,null,2)+'\n');
}
report.no_observed_regression=report.after.wins>=report.before.wins&&report.after.losses<=report.before.losses;
fs.writeFileSync(values.output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));

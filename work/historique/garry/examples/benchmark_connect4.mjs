// Comparaison sur positions issues de parties aléatoires, sans budget mural.
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,Network} from '../web/engine.js';
import {connectSearch} from '../web/fast-search.js';

const options=Object.fromEntries(process.argv.slice(2).reduce((a,v,i,all)=>i%2?a:[...a,[v.replace(/^--/,''),all[i+1]]],[]));
const episodes=Number(options.episodes??40),duels=Number(options.duels??40),limit=Number(options.nodes??150),seed=Number(options.seed??7000);
if(!Number.isInteger(episodes)||episodes<1||!Number.isInteger(duels)||duels<0||!Number.isInteger(limit)||limit<0||!Number.isInteger(seed))throw Error('Options invalides');
const baseline=options.baseline??'HEAD';
let source=execFileSync('git',['show',`${baseline}:web/fast-search.js`],{cwd:new URL('..',import.meta.url),encoding:'utf8'});
source=source.replace("'./engine.js'",JSON.stringify(new URL('../web/engine.js',import.meta.url).href))
 .replace("'./models/sliding-distances.json'",JSON.stringify(new URL('../web/models/sliding-distances.json',import.meta.url).href));
const oldSearch=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).connectSearch;
const model=new Network(JSON.parse(fs.readFileSync(new URL('../versions/1.0.0/web/models/connect4.json',import.meta.url))));
const copy=g=>Object.assign(new Game('connect4'),g,{board:g.board.map(r=>r.slice())});
const wins=(g,player=g.player)=>g.legal().filter(a=>{const child=copy(g);child.player=player;child.step(a);return child.winner===player;}).map(a=>a.column);
const stats=()=>({positions:0,immediate_wins:0,immediate_wins_taken:0,avoidable_losses:0,avoidable_losses_prevented:0,forced_forks:0,forced_forks_taken:0,decision_ms:0});
const report={baseline,seed,episodes,node_limit:limit,teacher_used:false,note:'Diagnostic tactique, pas un taux de victoire en partie. Budgets en nœuds pour reproductibilité ; précontrôle tactique fixe hors budget. Les catégories peuvent se recouper.',before:stats(),after:stats()},seen=new Set();
for(let episode=0;episode<episodes;episode++){
 const g=new Game('connect4',seed+episode);
 while(!g.done){
  if(g.moves>=6){
   const key=JSON.stringify(g.board);
   if(!seen.has(key)){
    seen.add(key);
    const immediate=wins(g),safe=[],forks=[];
    for(const a of g.legal()){
     const child=copy(g);child.step(a);
     if(child.winner===g.player||!wins(child).length){safe.push(a.column);if(!child.done&&wins(child,g.player).length>=2)forks.push(a.column);}
    }
    const obs=g.obs(),legal=g.legal(),logits=model.forward(obs).z;
    for(const [name,solver] of [['before',oldSearch],['after',connectSearch]]){
     const budget={nodes:0,tick(){if(this.nodes>=limit)throw Error('budget');this.nodes++;}},began=performance.now();
     const result=solver(obs,legal,logits,budget),s=report[name];
     s.decision_ms+=performance.now()-began;s.positions++;
     if(immediate.length){s.immediate_wins++;if(immediate.includes(result.action.column))s.immediate_wins_taken++;}
     else{
      if(safe.length&&safe.length<legal.length){s.avoidable_losses++;if(safe.includes(result.action.column))s.avoidable_losses_prevented++;}
      if(forks.length){s.forced_forks++;if(forks.includes(result.action.column))s.forced_forks_taken++;}
     }
    }
   }
  }
  g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
 }
}
for(const s of [report.before,report.after]){s.mean_decision_ms=+(s.decision_ms/s.positions).toFixed(3);delete s.decision_ms;}
report.duels={episodes:duels,seed:seed+100000,random_opening_moves:6,paired_openings:true,alternating_sides:true,after_wins:0,before_wins:0,draws:0};
for(let episode=0;episode<duels;episode++){
 const g=new Game('connect4',seed+100000+Math.floor(episode/2)),newPlayer=1+episode%2;
 for(let i=0;i<6&&!g.done;i++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
 while(!g.done){
  const obs=g.obs(),legal=g.legal(),logits=model.forward(obs).z,budget={nodes:0,tick(){if(this.nodes>=limit)throw Error('budget');this.nodes++;}};
  g.step((g.player===newPlayer?connectSearch:oldSearch)(obs,legal,logits,budget).action);
 }
 report.duels[g.winner===0?'draws':g.winner===newPlayer?'after_wins':'before_wins']++;
}
console.log(JSON.stringify(report,null,2));
if(options.output)fs.writeFileSync(options.output,JSON.stringify(report,null,2)+'\n');

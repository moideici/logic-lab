// Référence figée 1.0.0 ; aucune partie défavorable n'est retirée du rapport.
import fs from 'node:fs';
import {parseArgs} from 'node:util';
import {Game,GarryModel,GARRY_GAMES} from '../web/engine.js';
import {chooseDecision} from '../web/decision.js';
import {connectDecision,connectReady} from '../web/connect4-runtime.js';
import {Network as OldNetwork} from '../versions/1.0.0/web/engine.js';
import {chooseDecision as oldChoose} from '../versions/1.0.0/web/decision.js';
import {connectSearch as oldConnect} from '../versions/1.0.0/web/fast-search.js';
await connectReady;
const {values}=parseArgs({options:{episodes:{type:'string',default:'20'},seed:{type:'string',default:'1100000'},output:{type:'string'},'new-nodes':{type:'string',default:'3000000'},'old-nodes':{type:'string',default:'5000'}}});
const episodes=Number(values.episodes),seed=Number(values.seed),newNodes=Number(values['new-nodes']),oldNodes=Number(values['old-nodes']);
if(!Number.isInteger(episodes)||episodes<2||episodes%2||!Number.isInteger(seed)||!Number.isInteger(newNodes)||newNodes<1||!Number.isInteger(oldNodes)||oldNodes<1)throw Error('Options invalides : nombre pair de parties requis');
const general=new GarryModel(JSON.parse(fs.readFileSync(new URL('../web/models/garry.json',import.meta.url))));
const previous=Object.fromEntries(GARRY_GAMES.map(g=>[g,new OldNetwork(JSON.parse(fs.readFileSync(new URL(`../versions/1.0.0/web/models/${g}.json`,import.meta.url))))]));
const report={name:'garry',version:'3.0.0',baseline:'1.0.0',seed,episodes,node_budgets:{current:newNodes,previous:oldNodes},runtime:process.version,
 note:'Puissance 4 : budgets en nœuds différents et plafond de sécurité de 10 secondes. Les autres jeux utilisent leurs budgets locaux habituels. Les pertes solo sont distinguées des régressions face à la référence. Les budgets muraux peuvent changer les résultats selon la machine.',games:{},zero_defeat_target_met:false};
const budget=limit=>({limit,nodes:0,depth:2,criticalDepth:3,tick(){if(this.nodes>=limit)throw Error('budget');this.nodes++;}});
for(const name of GARRY_GAMES){
 const stats={episodes,wins:0,losses:0,draws:0,regressions:0,samples:[]},multi=['tictactoe','connect4'].includes(name);
 for(let i=0;i<episodes;i++){
  const runSeed=seed+Math.floor(i/2),player=1+i%2,g=new Game(name,runSeed),old=previous[name],model=general.forGame(name);
  if(multi){
   if(name==='connect4')for(let n=0;n<6;n++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
   const began=performance.now();
   while(!g.done){const o=g.obs(),legal=g.legal();let d;
    if(name==='connect4')d=g.player===player?connectDecision(o,legal,model.forward(o).z,budget(newNodes),{timeMs:10000,maxDepth:20,positionHead:model.positionHead}):oldConnect(o,legal,old.forward(o).z,budget(oldNodes));
    else d=g.player===player?chooseDecision(model,o,legal):oldChoose(old,o,legal);
    g.step(d.action);
   }
   stats[g.winner===0?'draws':g.winner===player?'wins':'losses']++;
   stats.samples.push({seed:runSeed,player,winner:g.winner,moves:g.moves,ms:Math.round(performance.now()-began)});
  }else{
   const prior=new Game(name,runSeed),began=performance.now();
   for(const [env,m,choose] of [[g,model,chooseDecision],[prior,old,oldChoose]])while(!env.done&&env.moves<2500)env.step(choose(m,env.obs(),env.legal()).action);
   const nowWin=g.done&&g.winner===1,oldWin=prior.done&&prior.winner===1;
   stats[nowWin?'wins':'losses']++;
   if((oldWin&&!nowWin)||(nowWin===oldWin&&g.score<prior.score))stats.regressions++;
   stats.samples.push({seed:runSeed,current:{won:nowWin,score:g.score,moves:g.moves,truncated:!g.done},previous:{won:oldWin,score:prior.score,moves:prior.moves,truncated:!prior.done},ms:Math.round(performance.now()-began)});
  }
 }
 stats.loss_rate=stats.losses/episodes;report.games[name]=stats;
 console.log(name,JSON.stringify({...stats,samples:undefined}));
 if(values.output)fs.writeFileSync(values.output,JSON.stringify(report,null,2)+'\n');
}
report.zero_defeat_target_met=Object.values(report.games).every(g=>g.losses===0&&g.regressions===0);
if(values.output)fs.writeFileSync(values.output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({zero_defeat_target_met:report.zero_defeat_target_met}));

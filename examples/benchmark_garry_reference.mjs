import fs from 'node:fs';
import {Game,GarryModel} from '../web/engine.js';
import {connectReady,connectDecision} from '../web/connect4-runtime.js';
import {Network} from '../versions/1.0.0/web/engine.js';
import {connectSearch} from '../versions/1.0.0/web/fast-search.js';
await connectReady;
const m=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json'))),old=new Network(JSON.parse(fs.readFileSync('versions/1.0.0/web/models/connect4.json'))),episodes=40,seed=7900000;
const report={game:'connect4',version:'3.0.0',opponent:'frozen 1.0.0',episodes,seed,new_nodes:3000000,old_nodes:5000,time_safety_ms:10000,target_depth:20,wins:0,losses:0,draws:0,depth_max:0,samples:[],note:'Budgets différents, ouvertures jumelées six coups, camps alternés. Ce contrôle ne prouve pas une absence universelle de défaites.'};
const budget=limit=>({limit,nodes:0,tick(){if(this.nodes++>=this.limit)throw Error('budget');}});
for(let i=0;i<episodes;i++){
 const g=new Game('connect4',seed+Math.floor(i/2)),p=1+i%2;for(let j=0;j<6;j++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
 while(!g.done){const o=g.obs(),legal=g.legal();let d;if(g.player===p){d=connectDecision(o,legal,m.forGame('connect4').forward(o).z,budget(report.new_nodes),{timeMs:10000,maxDepth:20,positionHead:m.positionHead});report.depth_max=Math.max(report.depth_max,d.info.depth??0);}else d=connectSearch(o,legal,old.forward(o).z,budget(report.old_nodes));g.step(d.action);}
 report[g.winner===0?'draws':g.winner===p?'wins':'losses']++;report.samples.push({seed:seed+Math.floor(i/2),player:p,winner:g.winner,moves:g.moves});
 fs.writeFileSync('web/models/garry-reference-evaluation.json',JSON.stringify(report,null,2));if((i+1)%10===0)console.log(JSON.stringify({completed:i+1,wins:report.wins,losses:report.losses,draws:report.draws,depth_max:report.depth_max}));
}

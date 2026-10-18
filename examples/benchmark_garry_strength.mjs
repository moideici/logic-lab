import fs from 'node:fs';
import {Game,GarryModel} from '../web/engine.js';
import {connectReady,connectDecision} from '../web/connect4-runtime.js';
import {defaultPositionHead} from '../web/value.js';
await connectReady;
const [headPath,output,ep='80',seedText='7600000',variantText='0,.25,.5,1',nodeText='100000',oldNodeText=nodeText]=process.argv.slice(2);
if(!headPath||!output)throw Error('head output [episodes seed blends nodes oldNodes]');
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json'))),raw=JSON.parse(fs.readFileSync(headPath)),base=defaultPositionHead().weights,episodes=Number(ep),seed=Number(seedText),nodes=Number(nodeText),oldNodes=Number(oldNodeText);
const old=(await WebAssembly.instantiate(fs.readFileSync('versions/2.0.0/connect4-search.wasm'),{env:{now:()=>performance.now(),abort(){throw Error('abort');}}})).instance.exports;
function oldDecision(o,z){const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));const order=[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]);order.forEach((c,i)=>old.setPrior(c,7-i));return {column:old.decide(bits[1],bits[2],o.current_player,oldNodes,10000,40)};}
const report={seed,episodes,nodes,old_nodes:oldNodes,paired_openings:true,baseline:'frozen Garry 2.0.0 WASM; identical policy weights',target_depth:20,variants:{},samples:[],note:'Fixed node budgets, independent seeded paired openings, 10s safety only. No excluded defeats.'};
for(const mix of variantText.split(',').map(Number)){
 const head={...raw,weights:raw.weights.map((v,i)=>mix*v+(1-mix)*base[i]),enabled:mix>0};
 const stats={wins:0,losses:0,draws:0,ms:0,depth_sum:0,searches:0,max_depth:0,proofs:0};
 for(let i=0;i<episodes;i++){
  const g=new Game('connect4',seed+Math.floor(i/2)),player=1+i%2;for(let j=0;j<6;j++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
  const began=performance.now();
  while(!g.done){const o=g.obs(),legal=g.legal(),z=model.forGame('connect4').forward(o).z;let action;
   if(g.player===player){const d=connectDecision(o,legal,z,{nodes:0,limit:nodes},{timeMs:10000,maxDepth:20,positionHead:head});action=d.action;stats.depth_sum+=d.info.depth??0;stats.max_depth=Math.max(stats.max_depth,d.info.depth??0);stats.searches++;if(d.info.proof)stats.proofs++;}
   else action=oldDecision(o,z);g.step(action);
  }
  stats[g.winner===0?'draws':g.winner===player?'wins':'losses']++;stats.ms+=performance.now()-began;
  report.samples.push({mix,seed:seed+Math.floor(i/2),player,winner:g.winner,moves:g.moves});
  if((i+1)%20===0)console.log(JSON.stringify({mix,complete:i+1,...stats}));
 }
 report.variants[mix]=stats;fs.writeFileSync(output,JSON.stringify(report,null,2));
}
console.log(JSON.stringify(report.variants));

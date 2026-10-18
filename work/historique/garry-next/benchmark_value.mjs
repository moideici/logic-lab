import fs from 'node:fs';
import {Game,GarryModel} from '../web/engine.js';
import {connectReady,connectDecision} from '../web/connect4-runtime.js';
await connectReady;
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json'))),raw=JSON.parse(fs.readFileSync('training-runs/garry-value-20261016/head.json'));
const old=(await WebAssembly.instantiate(fs.readFileSync('versions/2.0.0/connect4-search.wasm'),{env:{now:()=>performance.now(),abort(){throw Error('abort');}}})).instance.exports;
const output=process.argv[2]??'training-runs/garry-value-20261016/duels.json',episodes=Number(process.argv[3]??80),nodes=100000;
function oldDecision(o,z){const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));const order=[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]);order.forEach((c,i)=>old.setPrior(c,7-i));return {column:old.decide(bits[1],bits[2],o.current_player,nodes,10000,40)};}
const report={seed:7300000,episodes,nodes,paired_openings:true,baseline:'frozen Garry 2.0.0 WASM and identical policy weights',variants:{},samples:[],note:'Fixed node budgets; two seats per opening. Independent seed from training. Safety clock 10 s.'};
// Compare old evaluator and learned one under identical complete-root search.
for(const [variant,head] of [['untrained',null],['learned',raw]]){
 const stats={wins:0,losses:0,draws:0,ms:0};
 for(let i=0;i<episodes;i++){
  const g=new Game('connect4',report.seed+Math.floor(i/2)),player=1+i%2;
  for(let j=0;j<6;j++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
  const began=performance.now();
  while(!g.done){const o=g.obs(),legal=g.legal(),z=model.forGame('connect4').forward(o).z;const action=g.player===player?connectDecision(o,legal,z,{nodes:0,limit:nodes},{timeMs:10000,analyze:true,positionHead:head}).action:oldDecision(o,z);g.step(action);}
  const result=g.winner===0?'draws':g.winner===player?'wins':'losses';stats[result]++;stats.ms+=performance.now()-began;
  report.samples.push({variant,seed:report.seed+Math.floor(i/2),player,winner:g.winner,moves:g.moves});
  if((i+1)%20===0)console.log(JSON.stringify({variant,complete:i+1,...stats}));
 }
 report.variants[variant]=stats;fs.writeFileSync(output,JSON.stringify(report,null,2));
}
console.log(JSON.stringify(report.variants));

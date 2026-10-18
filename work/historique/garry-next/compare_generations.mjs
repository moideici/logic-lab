import fs from 'node:fs';
import {Game,GarryModel} from '../web/engine.js';
import {connectReady,connectDecision} from '../web/connect4-runtime.js';
import {Network} from '../versions/1.0.0/web/engine.js';
import {connectSearch} from '../versions/1.0.0/web/fast-search.js';
await connectReady;
const m=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json'))),old=new Network(JSON.parse(fs.readFileSync('versions/1.0.0/web/models/connect4.json')));
const frozen=(await WebAssembly.instantiate(fs.readFileSync('versions/2.0.0/connect4-search.wasm'),{env:{now:()=>performance.now(),abort(){throw Error('abort');}}})).instance.exports;
const budget=limit=>({limit,nodes:0,tick(){if(this.nodes++>=this.limit)throw Error('budget');}});
function baseline(o,z){const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));const order=[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]);order.forEach((c,i)=>frozen.setPrior(c,7-i));return {column:frozen.decide(bits[1],bits[2],o.current_player,3000000,10000,40)};}
const report={seed:9200000,episodes:40,new_nodes:3000000,opponent_nodes:5000,paired_openings:true,baseline:'frozen Garry 2.0.0 model and WASM',opponent:'frozen 1.0.0',before:{wins:0,losses:0,draws:0},after:{wins:0,losses:0,draws:0},samples:[],note:'Same paired seeds and node budgets for before/after. Different node budgets versus opponent; no universal zero-loss guarantee.'};
for(let i=0;i<40;i++){
 const sample={seed:9200000+Math.floor(i/2),player:1+i%2};
 for(const variant of ['before','after']){
  const g=new Game('connect4',sample.seed);for(let j=0;j<6;j++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
  while(!g.done){const o=g.obs(),legal=g.legal();let action;if(g.player===sample.player){const z=m.forGame('connect4').forward(o).z;action=variant==='before'?baseline(o,z):connectDecision(o,legal,z,budget(3000000),{timeMs:10000,maxDepth:42,positionHead:m.positionHead}).action;}else action=connectSearch(o,legal,old.forward(o).z,budget(5000)).action;g.step(action);}
  report[variant][g.winner===0?'draws':g.winner===sample.player?'wins':'losses']++;sample[variant]={winner:g.winner,moves:g.moves};
 }
 report.samples.push(sample);fs.writeFileSync('web/models/garry-generations-evaluation.json',JSON.stringify(report,null,2));if((i+1)%10===0)console.log(JSON.stringify({completed:i+1,before:report.before,after:report.after}));
}
// Two distinct trajectories from the actual empty starting board. Do not
// inflate their count by replaying identical deterministic games with new seeds.
report.standard_start=[];
for(const player of [1,2]){const g=new Game('connect4');while(!g.done){const o=g.obs(),legal=g.legal();const d=g.player===player?connectDecision(o,legal,m.forGame('connect4').forward(o).z,budget(3000000),{timeMs:10000,maxDepth:42,positionHead:m.positionHead}):connectSearch(o,legal,old.forward(o).z,budget(5000));g.step(d.action);}report.standard_start.push({player,winner:g.winner,moves:g.moves});}
fs.writeFileSync('web/models/garry-generations-evaluation.json',JSON.stringify(report,null,2));console.log(JSON.stringify({before:report.before,after:report.after,standard_start:report.standard_start}));

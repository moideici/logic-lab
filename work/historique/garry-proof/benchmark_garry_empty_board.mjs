import fs from 'node:fs';
import {parseArgs} from 'node:util';
import {Game,GarryModel,rng} from '../web/engine.js';
import {chooseDecision} from '../web/decision.js';
import {connectReady} from '../web/connect4-runtime.js';
import {Network} from '../versions/1.0.0/web/engine.js';
import {chooseDecision as chooseLegacy} from '../versions/1.0.0/web/decision.js';
await connectReady;
const {values:v}=parseArgs({options:{output:{type:'string'},repetitions:{type:'string',default:'1'},opponents:{type:'string',default:'previous,legacy1'},compare:{type:'boolean',default:false}}});
const repetitions=Number(v.repetitions);if(!v.output||!Number.isInteger(repetitions)||repetitions<1)throw Error('--output and positive --repetitions required');
const load=p=>new GarryModel(JSON.parse(fs.readFileSync(p))),active=load('web/models/garry.json'),previous=load('versions/3.1.0/garry.json'),old=new Network(JSON.parse(fs.readFileSync('versions/1.0.0/web/models/connect4.json')));
const instantiate=async()=>(await WebAssembly.instantiate(fs.readFileSync('versions/3.1.0/connect4-search.wasm'),{env:{now:()=>performance.now(),abort(){throw Error('abort')}}})).instance.exports;
const before=await instantiate(),opponent=await instantiate();for(const rt of [before,opponent]){rt.enableValue(1);previous.positionHead.weights.forEach((w,i)=>rt.setValueWeight(i,w));}
function frozen(rt,o,legal){const bits=[0n,0n,0n],z=previous.forGame('connect4').forward(o).z;o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r)}));for(let c=0;c<7;c++)rt.setPrior(c,-1);legal.slice().sort((a,b)=>z[b.column]-z[a.column]).forEach((a,i)=>rt.setPrior(a.column,7-i));const start=performance.now(),column=rt.decide(bits[1],bits[2],o.current_player,200000000,2000,42);return {action:{column},info:{runtime:'frozen_3.1.0',nodes:rt.getNodes(),depth:rt.getDepth(),value:rt.getValue(),time_ms:performance.now()-start}};}
const count=()=>({wins:0,losses:0,draws:0});
const report={format:'garry-empty-board-public-api-v1',version:active.export().version,opponent_version:'3.1.0',repetitions,nodes:200000000,time_ms:2000,max_depth:42,opening_prefix:0,variants:v.compare?['before','after']:['after'],opponents:{},samples:[],started:new Date().toISOString(),note:'Every game starts empty, both seats, original level-10 settings. Previous uses its frozen binary and weights; legacy1 uses its original complete decision pipeline (100000 nodes / 30ms). Repeated deterministic starts are stability runs, not independent opening strategies. No failed or losing game is omitted.'};
for(const name of v.opponents.split(',')){
 if(!['previous','legacy1'].includes(name))throw Error('Unknown opponent');
 const stats={before:count(),after:count(),seats:{1:count(),2:count()}};
 for(let repetition=0;repetition<repetitions;repetition++)for(const player of [1,2])for(const variant of report.variants){
  const g=new Game('connect4',17105500+repetition),random=rng(17105500+repetition),trace=[],history=[];
  while(!g.done){const o=g.obs(),legal=g.legal(),own=g.player===player;
   const d=own?(variant==='after'?chooseDecision(active,o,legal,{level:10,planning:true,random}):frozen(before,o,legal)):name==='previous'?frozen(opponent,o,legal):chooseLegacy(old,o,legal,{level:10,planning:true,random});
   if(!legal.some(a=>a.column===d.action.column))throw Error('Illegal move');trace.push({observation:o,side:own?'tested':'opponent',action:d.action,info:d.info});history.push(d.action.column);g.step(d.action);
  }
  const result=g.winner===0?'draws':g.winner===player?'wins':'losses';stats[variant][result]++;if(variant==='after')stats.seats[player][result]++;
  report.samples.push({opponent:name,repetition,player,variant,result,moves:g.moves,history,trace});report.opponents[name]=stats;fs.writeFileSync(v.output,JSON.stringify(report,null,2));console.log(JSON.stringify({opponent:name,repetition,player,variant,result,moves:g.moves}));
 }
}
report.completed=true;report.finished=new Date().toISOString();report.zero_defeats=Object.values(report.opponents).every(s=>s.after.losses===0&&[1,2].every(p=>Object.values(s.seats[p]).reduce((a,b)=>a+b,0)===repetitions));fs.writeFileSync(v.output,JSON.stringify(report,null,2));console.log(JSON.stringify({zero_defeats:report.zero_defeats,opponents:report.opponents}));

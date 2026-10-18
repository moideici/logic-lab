import fs from 'node:fs';
import {parseArgs} from 'node:util';
import {Game,GarryModel,rng} from '../web/engine.js';
import {connectDecision,connectReady} from '../web/connect4-runtime.js';
import {Network} from '../versions/1.0.0/web/engine.js';
import {connectSearch as legacy1Search} from '../versions/1.0.0/web/fast-search.js';
await connectReady;
const {values}=parseArgs({options:{before:{type:'string',default:'versions/3.0.0/garry.json'},after:{type:'string'},dataset:{type:'string'},output:{type:'string'},nodes:{type:'string',default:'50000'},pairs:{type:'string',default:'12'},seed:{type:'string',default:'16048000'}}});
if(!values.after||!values.dataset||!values.output)throw Error('--after --dataset --output requis');
const nodes=Number(values.nodes),pairs=Number(values.pairs),seed=Number(values.seed);
if(!Number.isInteger(nodes)||nodes<1||!Number.isInteger(pairs)||pairs<4||!Number.isInteger(seed))throw Error('Paramètres invalides');
const load=file=>new GarryModel(JSON.parse(fs.readFileSync(file))),models={before:load(values.before),after:load(values.after)},champion=load(values.before),old2=load('versions/2.0.0/garry.json'),old1=new Network(JSON.parse(fs.readFileSync('versions/1.0.0/web/models/connect4.json')));
const frozen=(await WebAssembly.instantiate(fs.readFileSync('versions/2.0.0/connect4-search.wasm'),{env:{now:()=>performance.now(),abort(){throw Error('abort');}}})).instance.exports;
const test=JSON.parse(fs.readFileSync(values.dataset)).cases.filter(c=>c.split==='test'&&c.observation.game==='connect4'),categories=[...new Set(test.map(c=>c.category))].sort();
const budget=limit=>({limit,nodes:0,tick(){if(this.nodes++>=limit)throw Error('budget');}});
function legacy2(o,z){const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));const order=[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]);order.forEach((c,i)=>frozen.setPrior(c,7-i));return {column:frozen.decide(bits[1],bits[2],o.current_player,nodes,10000,42)};}
function opponent(name,g,random){const o=g.obs(),legal=g.legal();
 if(name==='random')return legal[Math.floor(random()*legal.length)];
 if(name==='center'||name==='edges'){const weights=legal.map(a=>Math.exp((name==='center'?-1:1)*Math.abs(a.column-3))),total=weights.reduce((a,b)=>a+b,0);let r=random()*total;return legal[weights.findIndex(w=>(r-=w)<0)]??legal.at(-1);}
 if(name==='legacy1')return legacy1Search(o,legal,old1.forward(o).z,budget(5000)).action;
 if(name==='legacy2')return legacy2(o,old2.forGame('connect4').forward(o).z);
 return connectDecision(o,legal,champion.forGame('connect4').forward(o).z,budget(name==='tactical'?0:nodes),{timeMs:10000,maxDepth:42,positionHead:champion.positionHead}).action;
}
const report={format:'garry-league-v1',seed,nodes,pairs_per_opponent:pairs,opponents:{},before:{wins:0,losses:0,draws:0},after:{wins:0,losses:0,draws:0},samples:[],failures:[],note:'Paired starts and seats. Random, center, edges, tactical, frozen 1.0, 2.0 and champion 3.0. No defeats excluded. Legacy 1.0 has 5000 nodes; tactical has no tree search; other search agents have equal fixed nodes. Held-out failures stay quarantined.'};
for(const [index,name] of ['random','center','edges','tactical','legacy1','legacy2','champion'].entries()){
 const stats={before:{wins:0,losses:0,draws:0},after:{wins:0,losses:0,draws:0}};
 for(let pair=0;pair<pairs;pair++){
  const random=rng(seed+index*10000+pair),start=new Game('connect4',seed+pair);let challenge='standard',caseId=null;
  if(pair>0&&pair<4){const plies=[0,2,4,6][pair];for(let j=0;j<plies;j++)start.step(start.legal()[Math.floor(random()*start.legal().length)]);challenge=`random_prefix_${plies}`;}
  else if(pair>=4){const category=categories[(pair-4)%categories.length],pool=test.filter(c=>c.category===category),c=pool[Math.floor(random()*pool.length)];start.board=c.observation.board.map(r=>r.slice());start.player=c.observation.current_player;start.moves=c.observation.moves;challenge='heldout_'+category;caseId=c.id;}
  if(start.done)throw Error('Terminal challenge generation');
  for(const player of [1,2]){
   const sample={opponent:name,pair,player,challenge,case_id:caseId,start:start.obs()};
   for(const variant of ['before','after']){
    const g=new Game('connect4',seed+pair),m=models[variant],oppRandom=rng(seed+index*10000+pair*2+player);g.board=start.board.map(r=>r.slice());g.player=start.player;g.moves=start.moves;const trace=[];
    while(!g.done){const o=g.obs();let action;if(g.player===player){const d=connectDecision(o,g.legal(),m.forGame('connect4').forward(o).z,budget(nodes),{timeMs:10000,maxDepth:42,positionHead:m.positionHead});action=d.action;trace.push({observation:o,action,value:d.info.value,depth:d.info.depth});if(trace.length>6)trace.shift();}else action=opponent(name,g,oppRandom);g.step(action);}
    const result=g.winner===0?'draws':g.winner===player?'wins':'losses';stats[variant][result]++;report[variant][result]++;sample[variant]={winner:g.winner,moves:g.moves};
    if(variant==='after'&&result==='losses')report.failures.push({opponent:name,challenge,case_id:caseId,player,trace,eligible_for_training:false,reason:'quarantined_evaluation_trajectory'});
   }
   report.samples.push(sample);
  }
 }
 report.opponents[name]=stats;fs.writeFileSync(values.output,JSON.stringify(report,null,2));console.log(JSON.stringify({opponent:name,...stats}));
}
report.passed=report.after.losses<=report.before.losses&&report.after.wins+report.after.draws/2>=report.before.wins+report.before.draws/2&&Object.values(report.opponents).every(s=>s.after.losses<=s.before.losses);
fs.writeFileSync(values.output,JSON.stringify(report,null,2));console.log(JSON.stringify({passed:report.passed,before:report.before,after:report.after}));

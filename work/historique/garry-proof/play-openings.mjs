import fs from 'node:fs';
const dir='C:/Users/gabor/code/logic-lab/work/garry-proof',root='C:/Users/gabor/code/playi';
const {Game,GarryModel}=await import(`file:///${root}/web/engine.js`);
const load=async file=>(await WebAssembly.instantiate(fs.readFileSync(file),{env:{now:()=>performance.now(),abort(){throw Error('abort')}}})).instance.exports;
const own=await load(`${dir}/candidate.wasm`),opponent=await load(`${dir}/before.wasm`),model=new GarryModel(JSON.parse(fs.readFileSync(`${dir}/before.json`)));
for(const rt of [own,opponent]){rt.enableValue(1);model.positionHead.weights.forEach((w,i)=>rt.setValueWeight(i,w));}
function prepare(rt,o){const b=[0n,0n,0n],z=model.forGame('connect4').forward(o).z;o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)b[p]|=1n<<BigInt(c*7+5-r)}));[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]).forEach((c,i)=>rt.setPrior(c,7-i));return b;}
const report={opponent:'frozen 3.1.0',nodes:200000000,time_ms:2000,opening_nodes:100000000,opening_ms:10000,samples:[],wins:0,losses:0,draws:0};
for(const plan of [[2],[4],[1,3,2],[0,3,2],[1,3,1]]){
 const g=new Game('connect4'),history=[],trace=[];let turn=0;
 while(!g.done){const o=g.obs(),rt=g.player===2?own:opponent,b=prepare(rt,o);let c,method;
  if(g.player===1){c=opponent.decide(b[1],b[2],1,report.nodes,report.time_ms,42);method='previous';}
  else if(turn<plan.length){c=plan[turn];method='exploration_plan';turn++;}
  else if(g.moves<=9){c=own.certify(b[1],b[2],2,report.opening_nodes,report.opening_ms);method='offline_exact_opening';if(own.getProofState()===0||own.getProofState()===4){c=own.decideVerified(b[1],b[2],2,report.nodes,report.time_ms,42);method='bounded_fallback';}}
  else {c=own.decideVerified(b[1],b[2],2,report.nodes,report.time_ms,42);method='verified_runtime';}
  trace.push({observation:o,column:c,method,proof:g.player===2?own.getProofState():null});history.push(c);g.step({column:c});
 }
 const result=g.winner===0?'draws':g.winner===2?'wins':'losses';report[result]++;report.samples.push({plan,result,history,trace});fs.writeFileSync(`${dir}/opening-duels.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({plan,result,history}));
}
report.completed=true;fs.writeFileSync(`${dir}/opening-duels.json`,JSON.stringify(report,null,2));

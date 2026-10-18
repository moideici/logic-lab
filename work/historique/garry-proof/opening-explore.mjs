import fs from 'node:fs';
const dir='C:/Users/gabor/code/logic-lab/work/garry-proof',root='C:/Users/gabor/code/playi';
const {Game,GarryModel}=await import(`file:///${root}/web/engine.js`);
const load=async file=>(await WebAssembly.instantiate(fs.readFileSync(file),{env:{now:()=>performance.now(),abort(){throw Error('abort')}}})).instance.exports;
const opponent=await load(`${dir}/before.wasm`),oracle=await load(`${dir}/candidate.wasm`),model=new GarryModel(JSON.parse(fs.readFileSync(`${dir}/before.json`)));
opponent.enableValue(1);model.positionHead.weights.forEach((w,i)=>opponent.setValueWeight(i,w));
const save=(p,x)=>{fs.writeFileSync(p+'.tmp',JSON.stringify(x,null,2));fs.renameSync(p+'.tmp',p);};
const cacheFile=`${dir}/opening-cache.json`,cache=fs.existsSync(cacheFile)?JSON.parse(fs.readFileSync(cacheFile)):{};
const reportFile=`${dir}/opening-explore.json`,report=fs.existsSync(reportFile)?JSON.parse(fs.readFileSync(reportFile)):{format:'garry-opening-exploration-v1',opponent:'frozen 3.1.0',opponent_nodes:200000000,opponent_ms:2000,oracle_nodes:100000000,oracle_ms:3000,completed_depth:0,nodes:[],solutions:[],started:new Date().toISOString()};
function bits(o){const b=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)b[p]|=1n<<BigInt(c*7+5-r)}));return b;}
function key(o){return o.board.flat().join('')+':'+o.current_player;}
function oldMove(g){const o=g.obs(),k=key(o);if(cache[k])return cache[k];const b=bits(o),z=model.forGame('connect4').forward(o).z;[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]).forEach((c,i)=>opponent.setPrior(c,7-i));const column=opponent.decide(b[1],b[2],o.current_player,report.opponent_nodes,report.opponent_ms,42);const result={column,nodes:opponent.getNodes(),depth:opponent.getDepth(),value:opponent.getValue()};cache[k]=result;save(cacheFile,cache);return result;}
function position(history){const g=new Game('connect4');for(const column of history)g.step({column});return g;}
let frontier=report.completed_depth?report.nodes.filter(n=>n.depth===report.completed_depth&&n.oracle.state!==2&&n.oracle.state!==3).map(n=>n.history):[[oldMove(new Game('connect4')).column]];
const seen=new Set(report.nodes.map(n=>key(position(n.history).obs())));
for(let depth=report.completed_depth+1;depth<=6;depth++){
 const next=report.nodes.filter(n=>n.depth===depth&&!n.terminal&&![2,3].includes(n.oracle.state)).map(n=>n.history);
 for(const history of frontier){
  const parent=position(history);if(parent.done)continue;
  // Every legal defence is examined; no losses are excluded from evaluation.
  for(const a of parent.legal()){
   const g=position(history);g.step(a);if(g.done){if(g.winner===2)report.solutions.push({history:[...history,a.column],terminal:true});continue;}
   const reply=oldMove(g);g.step({column:reply.column});const path=[...history,a.column,reply.column],k=key(g.obs());if(seen.has(k))continue;seen.add(k);
   if(g.done){report.nodes.push({depth,history:path,reply,terminal:true,winner:g.winner,oracle:{state:g.winner===2?2:g.winner===0?3:4}});save(reportFile,report);continue;}
   const b=bits(g.obs()),start=performance.now(),column=oracle.certify(b[1],b[2],2,report.oracle_nodes,report.oracle_ms);const proof={state:oracle.getProofState(),column,nodes:oracle.getProofNodes(),ms:performance.now()-start};
   const entry={depth,history:path,reply,oracle:proof};report.nodes.push(entry);
   if(proof.state===2||proof.state===3)report.solutions.push(entry);else next.push(path);
   save(reportFile,report);
   console.log(JSON.stringify({depth,examined:report.nodes.length,solutions:report.solutions.length,history:path,oracle:proof.state}));
   if(report.solutions.length>=3){report.state='found_defences';save(reportFile,report);process.exit(0);}
  }
 }
 report.completed_depth=depth;save(reportFile,report);frontier=next;
}
report.state='search_limit_reached';save(reportFile,report);

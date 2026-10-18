import fs from 'node:fs';
const root='C:/Users/gabor/code/playi',dir='C:/Users/gabor/code/logic-lab/work/garry-proof';
const {Game,GarryModel}=await import(`file:///${root}/web/engine.js`);
const {Network}=await import(`file:///${root}/versions/1.0.0/web/engine.js`);
const {connectSearch}=await import(`file:///${root}/versions/1.0.0/web/fast-search.js`);
const model=new GarryModel(JSON.parse(fs.readFileSync(`${root}/web/models/garry.json`))),old=new Network(JSON.parse(fs.readFileSync(`${root}/versions/1.0.0/web/models/connect4.json`)));
const load=async path=>(await WebAssembly.instantiate(fs.readFileSync(path),{env:{now:()=>performance.now(),abort(){throw Error('abort')}}})).instance.exports;
const baseline=await load(`${root}/web/connect4-search.wasm`),candidate=await load(`${dir}/candidate.wasm`);
function prepare(rt,o){const bits=[0n,0n,0n];o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r)}));const z=model.forGame('connect4').forward(o).z;[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]).forEach((c,i)=>rt.setPrior(c,7-i));return bits;}
baseline.enableValue(1);model.positionHead.weights.forEach((w,i)=>baseline.setValueWeight(i,w));
const budget=limit=>({limit,nodes:0,tick(){if(this.nodes++>=limit)throw Error('budget')}});
const report={seed:7900000,episodes:40,baseline:{wins:0,losses:0,draws:0},losses:[]};
for(let i=0;i<40;i++){
 const g=new Game('connect4',7900000+Math.floor(i/2)),p=1+i%2,trace=[],prefix=[];
 for(let j=0;j<6;j++){const a=g.legal()[Math.floor(g.random()*g.legal().length)];prefix.push(a.column);g.step(a);}
 const initial=g.obs();
 while(!g.done){const o=g.obs();let action;
  if(g.player===p){const bits=prepare(baseline,o);action={column:baseline.decide(bits[1],bits[2],p,3000000,10000,20)};trace.push({observation:o,action,value:baseline.getValue(),depth:baseline.getDepth()});}
  else action=connectSearch(o,g.legal(),old.forward(o).z,budget(5000)).action;
  g.step(action);
 }
 const result=g.winner===0?'draws':g.winner===p?'wins':'losses';report.baseline[result]++;
 if(result==='losses')report.losses.push({i,p,prefix,initial,trace});
 if(i%10===9)console.log(JSON.stringify({phase:'replay',completed:i+1,...report.baseline}));
 fs.writeFileSync(`${dir}/audit.json`,JSON.stringify(report,null,2));
}
for(const game of report.losses){
 for(const t of [...game.trace].reverse()){
  const o=t.observation,bits=prepare(candidate,o),start=performance.now();
  const column=candidate.certify(bits[1],bits[2],o.current_player,o.moves<14?100000000:40000000,5000);
  t.certification={column,state:candidate.getProofState(),nodes:candidate.getProofNodes(),ms:performance.now()-start};
  console.log(JSON.stringify({game:game.i,moves:o.moves,played:t.action.column,...t.certification}));
  fs.writeFileSync(`${dir}/audit.json`,JSON.stringify(report,null,2));
 }
}

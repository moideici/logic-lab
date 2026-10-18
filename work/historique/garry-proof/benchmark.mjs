import fs from 'node:fs';
import {parseArgs} from 'node:util';
const root='C:/Users/gabor/code/playi',dir='C:/Users/gabor/code/logic-lab/work/garry-proof';
const {Game,GarryModel,rng}=await import(`file:///${root}/web/engine.js`),{Network}=await import(`file:///${root}/versions/1.0.0/web/engine.js`),{connectSearch}=await import(`file:///${root}/versions/1.0.0/web/fast-search.js`);
const {values:v}=parseArgs({options:{output:{type:'string',default:`${dir}/duels.json`},pairs:{type:'string',default:'20'},prefix:{type:'string',default:'0'},seed:{type:'string',default:'17017000'},nodes:{type:'string',default:'3000000'},time:{type:'string',default:'2000'},opponents:{type:'string',default:'legacy1,previous'}}});
const load=async p=>(await WebAssembly.instantiate(fs.readFileSync(p),{env:{now:()=>performance.now(),abort(){throw Error('abort')}}})).instance.exports;
const model=new GarryModel(JSON.parse(fs.readFileSync(`${dir}/before.json`))),old=new Network(JSON.parse(fs.readFileSync(`${root}/versions/1.0.0/web/models/connect4.json`))),before=await load(`${dir}/before.wasm`),after=await load(`${dir}/candidate.wasm`),previous=await load(`${dir}/before.wasm`);
for(const rt of [before,after,previous]){rt.enableValue(1);model.positionHead.weights.forEach((w,i)=>rt.setValueWeight(i,w));}
function choose(rt,o,verified=false){const bits=[0n,0n,0n],z=model.forGame('connect4').forward(o).z;o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r)}));[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]).forEach((c,i)=>rt.setPrior(c,7-i));const column=rt[verified?'decideVerified':'decide'](bits[1],bits[2],o.current_player,Number(v.nodes),Number(v.time),42);return {action:{column},proof:verified?rt.getProofState():0,depth:rt.getDepth(),nodes:rt.getNodes()};}
const budget=n=>({limit:n,nodes:0,tick(){if(this.nodes++>=n)throw Error('budget')}});
const report={seed:Number(v.seed),pairs:Number(v.pairs),prefix:Number(v.prefix),nodes:Number(v.nodes),time_ms:Number(v.time),baseline:'frozen current 3.1.0 binary and weights, no candidate search code',opponents:{},samples:[],before:{wins:0,losses:0,draws:0},after:{wins:0,losses:0,draws:0},certificates:{},losses:[]};
for(const [oi,name] of v.opponents.split(',').entries()){
 const stats={before:{wins:0,losses:0,draws:0},after:{wins:0,losses:0,draws:0}};
 for(let i=0;i<Number(v.pairs)*2;i++){
  const seed=Number(v.seed)+Math.floor(i/2),player=1+i%2;
  const sample={opponent:name,seed,player,prefix:[]};
  for(const [variant,rt] of [['before',before],['after',after]]){
   const g=new Game('connect4',seed),random=rng(seed+oi*100000),trace=[];
   for(let j=0;j<Number(v.prefix);j++){if(g.done)throw Error('Terminal prefix');const a=g.legal()[Math.floor(random()*g.legal().length)];if(variant==='before')sample.prefix.push(a.column);g.step(a);}
   while(!g.done){const o=g.obs();let action;
    if(g.player===player){const d=choose(rt,o,variant==='after');action=d.action;trace.push({observation:o,...d});if(variant==='after')report.certificates[d.proof]=(report.certificates[d.proof]??0)+1;}
    else if(name==='legacy1')action=connectSearch(o,g.legal(),old.forward(o).z,budget(5000)).action;
    else if(name==='previous')action=choose(previous,o).action;
    else if(name==='random')action=g.legal()[Math.floor(random()*g.legal().length)];
    else throw Error('Unknown opponent');
    g.step(action);
   }
   const result=g.winner===0?'draws':g.winner===player?'wins':'losses';report[variant][result]++;stats[variant][result]++;sample[variant]={result,moves:g.moves};
   if(variant==='after'&&result==='losses')report.losses.push({seed,player,opponent:name,prefix:sample.prefix,trace,eligible_for_training:false});
  }
  report.samples.push(sample);
  if(i%10===9){fs.writeFileSync(v.output,JSON.stringify(report,null,2));console.log(JSON.stringify({opponent:name,completed:i+1,...stats}));}
 }
 report.opponents[name]=stats;fs.writeFileSync(v.output,JSON.stringify(report,null,2));
}
report.completed=true;fs.writeFileSync(v.output,JSON.stringify(report,null,2));console.log(JSON.stringify({before:report.before,after:report.after,certificates:report.certificates}));

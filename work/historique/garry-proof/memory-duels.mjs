import fs from 'node:fs';
import {lookupSearchMemory,memoryDecision} from './search-memory.js';
const dir='C:/Users/gabor/code/logic-lab/work/garry-proof',root='C:/Users/gabor/code/playi';
const {Game,GarryModel}=await import(`file:///${root}/web/engine.js`);
const load=async file=>(await WebAssembly.instantiate(fs.readFileSync(file),{env:{now:()=>performance.now(),abort(){throw Error('abort')}}})).instance.exports;
const own=await load(`${dir}/candidate.wasm`),old=await load(`${dir}/before.wasm`),model=new GarryModel(JSON.parse(fs.readFileSync(`${dir}/before.json`))),memory=JSON.parse(fs.readFileSync(`${dir}/memory.json`));
for(const rt of [own,old]){rt.enableValue(1);model.positionHead.weights.forEach((w,i)=>rt.setValueWeight(i,w));}
function choose(rt,o,verified){const entry=verified?lookupSearchMemory(o,o.board[0].flatMap((v,column)=>v?[]:[{column}]),memory):null;if(entry)return {...memoryDecision(entry,42-o.moves),ms:0};const b=[0n,0n,0n],z=model.forGame('connect4').forward(o).z;o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)b[p]|=1n<<BigInt(c*7+5-r)}));[0,1,2,3,4,5,6].sort((a,b)=>z[b]-z[a]).forEach((c,i)=>rt.setPrior(c,7-i));const start=performance.now(),column=rt[verified?'decideVerified':'decide'](b[1],b[2],o.current_player,200000000,2000,42);return {action:{column},info:{proof:verified?rt.getProofState():0,depth:rt.getDepth(),nodes:rt.getNodes()},ms:performance.now()-start};}
const report={format:'garry-empty-board-duels-v1',opponent:'frozen 3.1.0',nodes:200000000,time_ms:2000,opening_memory:memory.entries.length,samples:[],wins:0,losses:0,draws:0};
for(let repeat=0;repeat<2;repeat++)for(const player of [1,2]){
 const g=new Game('connect4',17088500+repeat),history=[],trace=[];
 while(!g.done){const o=g.obs(),verified=g.player===player,d=choose(verified?own:old,o,verified);trace.push({observation:o,variant:verified?'candidate':'previous',...d});history.push(d.action.column);g.step(d.action);}
 const result=g.winner===0?'draws':g.winner===player?'wins':'losses';report[result]++;report.samples.push({repeat,player,result,history,trace});fs.writeFileSync(`${dir}/memory-duels.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({repeat,player,result,moves:g.moves}));
}
report.completed=true;fs.writeFileSync(`${dir}/memory-duels.json`,JSON.stringify(report,null,2));

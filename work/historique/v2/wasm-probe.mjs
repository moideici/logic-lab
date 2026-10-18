import fs from 'node:fs';
import {Game,Network} from 'file:///C:/Users/gabor/code/playi/web/engine.js';
import {connectSearch as old} from 'file:///C:/Users/gabor/code/playi/versions/1.0.0/web/fast-search.js';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(new URL('./web/connect4-search.wasm',import.meta.url)),{env:{now:()=>performance.now(),abort(){throw Error('wasm abort');}}}),w=instance.exports;
const model=new Network(JSON.parse(fs.readFileSync('C:/Users/gabor/code/playi/web/models/connect4.json')));
const games=Number(process.argv[2]??20),nodes=Number(process.argv[3]??3000000),oldNodes=Number(process.argv[4]??5000),stats={games,nodes,oldNodes,wins:0,losses:0,draws:0,ms:0,decisions:0,failures:[]};
for(let i=0;i<games;i++){
 const seed=1200000+Math.floor(i/2),g=new Game('connect4',seed),player=1+i%2,history=[];
 for(let n=0;n<6;n++){const a=g.legal()[Math.floor(g.random()*g.legal().length)];g.step(a);history.push(a.column);}
 while(!g.done){
  const obs=g.obs(),legal=g.legal(),logits=model.forward(obs).z,isNew=g.player===player,budget={nodes:0,tick(){if(this.nodes>=oldNodes)throw Error('budget');this.nodes++;}},start=performance.now();let action;
  if(isNew){const bits=[0n,0n,0n];obs.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));const rank=legal.slice().sort((a,b)=>logits[b.column]-logits[a.column]);rank.forEach((a,i)=>w.setPrior(a.column,7-i));action={column:w.decide(bits[1],bits[2],g.player,nodes,10000,40)};stats.ms+=performance.now()-start;stats.decisions++;}
  else action=old(obs,legal,logits,budget).action;
  history.push(action.column);g.step(action);
 }
 stats[g.winner===0?'draws':g.winner===player?'wins':'losses']++;
 if(g.winner&&g.winner!==player)stats.failures.push({seed,player,history});
 if((i+1)%10===0)console.log(JSON.stringify({...stats,mean_ms:stats.ms/stats.decisions}));
}

import fs from 'node:fs';
import assert from 'node:assert/strict';
import {Game} from 'file:///C:/Users/gabor/code/playi/web/engine.js';
const {instance}=await WebAssembly.instantiate(fs.readFileSync(new URL('./web/connect4-search.wasm',import.meta.url)),{env:{now:()=>performance.now(),abort(){throw Error('abort');}}}),w=instance.exports;
let checked=0;
for(let seed=1;seed<=30;seed++){
 const g=new Game('connect4',seed);
 while(!g.done){
  const bits=[0n,0n,0n];g.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));
  for(const p of [1,2]){
   const mask=w.winningMask(bits[p],bits[1]|bits[2]);
   for(const a of g.legal()){
    const child=Object.assign(new Game('connect4'),g,{board:g.board.map(r=>r.slice()),player:p});child.step(a);
    const r=g.board.map(row=>row[a.column]).lastIndexOf(0),bit=1n<<BigInt(a.column*7+5-r);
    assert.equal(Boolean(mask&bit),child.winner===p);
   }
  }
  checked++;g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
 }
}
console.log({checked});
const g=new Game('connect4',1200000);for(let i=0;i<6;i++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
const bits=[0n,0n,0n];g.board.forEach((row,r)=>row.forEach((p,c)=>{if(p)bits[p]|=1n<<BigInt(c*7+5-r);}));
console.log({col:w.decide(bits[1],bits[2],g.player,1000000000,10000,40),nodes:w.getNodes(),depth:w.getDepth(),value:w.getValue()});

import fs from 'node:fs';
import {Game} from 'file:///C:/Users/gabor/code/playi/web/engine.js';
function copy(g){const out=new Game('connect4');Object.assign(out,g,{board:g.board.map(r=>r.slice())});return out;}
function wins(g,player=g.player){const out=[];for(const a of g.legal()){const child=copy(g);child.player=player;child.step(a);if(child.winner===player)out.push(a.column);}return out;}
const cases=[],seen=new Set(),examples={};
for(let seed=7000;seed<7300;seed++){
 const g=new Game('connect4',seed),history=[];
 while(!g.done){
  if(g.moves>=6){
   const immediate=wins(g),safe=[],forks=[];
   for(const a of g.legal()){
    const child=copy(g);child.step(a);
    if(child.winner===g.player||!wins(child).length){safe.push(a.column);if(!child.done&&wins(child,g.player).length>=2)forks.push(a.column);}
   }
   const key=JSON.stringify(g.board);
   if(!seen.has(key)){
    seen.add(key);cases.push({history:history.slice(),immediate,safe,forks});
    if(!immediate.length&&safe.length&&safe.length<g.legal().length&&!examples.support)examples.support=history.slice();
    if(!immediate.length&&forks.length&&!examples.fork)examples.fork=history.slice();
    if(immediate.length&&!examples.win)examples.win=history.slice();
    if(!immediate.length&&safe.length===1&&!examples.block)examples.block=history.slice();
   }
  }
  const a=g.legal()[Math.floor(g.random()*g.legal().length)];history.push(a.column);g.step(a);
 }
}
fs.writeFileSync(new URL('./positions.json',import.meta.url),JSON.stringify(cases));
console.log(JSON.stringify({positions:cases.length,examples},null,2));

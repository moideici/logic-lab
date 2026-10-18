import fs from 'node:fs';
import {Game,GarryModel,rng} from './web/engine.js';
import {chooseDecision} from './web/decision.js';
const active=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json'))),initial=new GarryModel(JSON.parse(fs.readFileSync('training/new-games-4.0.0/nine-game-bootstrap.json'))),results=[];
for(const name of ['draughts','breakthrough']){
 for(const kind of ['neural_vs_initial','level_10_vs_random']){
  const count=kind==='neural_vs_initial'?8:4;
  for(let trial=0;trial<count;trial++){
   const g=new Game(name,trial),random=rng(171811+Math.floor(trial/2)),seat=1+trial%2,opening=[];
   for(let ply=0;ply<Math.floor(trial/2)*2&&!g.done;ply++){const a=g.legal()[Math.floor(random()*g.legal().length)];g.step(a);opening.push(a);}
   const start=performance.now();let steps=0;
   for(;steps<400&&!g.done;steps++){
    const legal=g.legal(),isActive=g.player===seat;
    const action=kind==='level_10_vs_random'&&!isActive?legal[Math.floor(random()*legal.length)]:chooseDecision(isActive?active:initial,g.obs(),legal,{level:10,planning:kind==='level_10_vs_random'&&isActive,random}).action;
    g.step(action);
   }
   const outcome=!g.done?'truncated':g.winner===0?'draw':g.winner===seat?'win':'loss';results.push({game:name,kind,trial,seat,opening,outcome,steps,seconds:Math.round((performance.now()-start)/10)/100});
  }
  console.log(JSON.stringify({game:name,kind,outcomes:results.filter(r=>r.game===name&&r.kind===kind).map(r=>r.outcome)}));
 }
}
fs.writeFileSync('training/strategy-4.0.0/full-games.json',JSON.stringify({version:'4.0.0',scope:'Four opening histories, both seats against initialized added modes; two histories, both seats against random at actual level 10. Finite samples, no invincibility claim.',results},null,2));

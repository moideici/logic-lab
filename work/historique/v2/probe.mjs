import fs from 'node:fs';
import {Game,Network} from 'file:///C:/Users/gabor/code/playi/web/engine.js';
import {connectSearch as old} from 'file:///C:/Users/gabor/code/playi/versions/1.0.0/web/fast-search.js';
import {connectStrong as next} from './web/connect4.js';
const model=new Network(JSON.parse(fs.readFileSync('C:/Users/gabor/code/playi/web/models/connect4.json')));
const games=Number(process.argv[2]??20),nodes=Number(process.argv[3]??30000),oldNodes=Number(process.argv[4]??5000),stats={games,nodes,oldNodes,wins:0,losses:0,draws:0,ms:0,decisions:0,failures:[]};
for(let i=0;i<games;i++){
 const seed=1200000+Math.floor(i/2),g=new Game('connect4',seed),player=1+i%2;
 for(let n=0;n<6;n++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);
 while(!g.done){
  const obs=g.obs(),legal=g.legal(),logits=model.forward(obs).z,isNew=g.player===player,limit=isNew?nodes:oldNodes,budget={nodes:0,tick(){if(this.nodes>=limit)throw Error('budget');this.nodes++;}},start=performance.now();
  const d=(isNew?next:old)(obs,legal,logits,budget);if(isNew){stats.ms+=performance.now()-start;stats.decisions++;}g.step(d.action);
 }
 stats[g.winner===0?'draws':g.winner===player?'wins':'losses']++;
 if(g.winner&&g.winner!==player)stats.failures.push({seed,player});
 if((i+1)%10===0)console.log(JSON.stringify({...stats,mean_ms:stats.ms/stats.decisions}));
}

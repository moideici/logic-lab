import fs from 'node:fs';
import {Game} from 'file:///C:/Users/gabor/code/playi/web/engine.js';
const positions=JSON.parse(fs.readFileSync(new URL('./positions.json',import.meta.url))),selected=[],counts={};
for(const p of positions){
 const g=new Game('connect4');for(const column of p.history)g.step({column});
 const hypothetical=Object.assign(new Game('connect4'),g,{player:3-g.player});
 const threats=hypothetical.legal().filter(a=>{const child=Object.assign(new Game('connect4'),hypothetical,{board:g.board.map(r=>r.slice())});child.step(a);return child.winner===hypothetical.player;});
 const category=p.immediate.length?'win':p.forks.length?'fork':!p.safe.length?'forced_loss':p.safe.length<g.legal().length?(threats.length?'block':'support_trap'):'quiet';
 if((counts[category]??0)<4){selected.push({category,...p});counts[category]=(counts[category]??0)+1;}
 if(Object.keys(counts).length===6&&Object.values(counts).every(n=>n===4))break;
}
fs.writeFileSync(new URL('./connect4-positions.json',import.meta.url),'[\n'+selected.map(p=>'  '+JSON.stringify(p)).join(',\n')+'\n]\n');
console.log(JSON.stringify(counts));

// Évaluation sans professeur des politiques + solveurs express, dans Node.js.
import fs from 'node:fs';
import {Game,GarryModel,NAMES} from '../web/engine.js';
import {chooseDecision} from '../web/decision.js';
import {slidingDistance} from '../web/fast-search.js';

const report={version:'express-v2',runtime:`Node ${process.version}`,level:10,style:'balanced',interval_ms:0,teacher_used:false,
 objective:'win_then_fewest_moves',note:'Les temps dépendent de la machine. Optimalité globale prouvée pour le taquin et les sudokus résolus sans annulation ; recherches bornées ou hasard pour les autres jeux.',games:{}};
const general=new GarryModel(JSON.parse(fs.readFileSync(new URL('../web/models/garry.json',import.meta.url))));
for(const name of Object.keys(NAMES)){
 const model=general.forGame(name),episodes=name==='2048'?5:name==='minesweeper'?50:20;
 const stats={episodes,wins:0,draws:0,losses:0,truncated:0,mean_moves:0,mean_ms:0,opponent:['tictactoe','connect4'].includes(name)?'random_legal':null,minimum_verified:0,samples:[]};
 for(let i=0;i<episodes;i++){
  const g=new Game(name,1000000+i),player=g.multiplayer?1+i%2:1,start=performance.now();
  const minimum=name==='sliding_puzzle'?slidingDistance(g.board):name==='sudoku'?g.board.flat().filter(v=>!v).length:null;
  while(!g.done&&g.moves<2500){const o=g.obs(),legal=g.legal();const a=g.player===player?chooseDecision(model,o,legal).action:legal[Math.floor(g.random()*legal.length)];g.step(a);}
  const ms=performance.now()-start;
  stats[g.done?g.winner===player?'wins':g.multiplayer&&g.winner===0?'draws':'losses':'truncated']++;
  if(minimum!==null&&g.winner===1&&g.moves===minimum)stats.minimum_verified++;
  stats.mean_moves+=g.moves/episodes;stats.mean_ms+=ms/episodes;
  stats.samples.push({seed:1000000+i,winner:g.winner,moves:g.moves,minimum,ms:Math.round(ms)});
 }
 stats.mean_moves=+stats.mean_moves.toFixed(2);stats.mean_ms=+stats.mean_ms.toFixed(2);
 report.games[name]=stats;console.log(name,JSON.stringify({...stats,samples:undefined}));
}
fs.writeFileSync(new URL('../web/models/express-evaluation.json',import.meta.url),JSON.stringify(report,null,2));

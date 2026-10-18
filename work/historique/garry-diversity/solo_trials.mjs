import fs from 'node:fs';
import {Game,GarryModel,actionIndex} from '../web/engine.js';
import {tileSearch,mineSearch,exactSliding} from '../web/fast-search.js';
import {sudokuValues,selectQuality} from '../web/quality.js';
const [afterFile,datasetFile,output]=process.argv.slice(2);if(!afterFile||!datasetFile||!output)throw Error('after dataset output');
const load=p=>new GarryModel(JSON.parse(fs.readFileSync(p))),models={before:load('versions/3.0.0/garry.json'),after:load(afterFile)},cases=JSON.parse(fs.readFileSync(datasetFile)).cases.filter(c=>c.split==='test');
const report={format:'garry-solo-trials-v1',seed:16059000,episodes:8,games:{},note:'Eight paired games or held-out puzzles per mode. Fixed node budgets; no time comparison. 2048 has a 500-move cap; truncations never count as wins.'};
const budget=limit=>({limit,nodes:0,depth:2,criticalDepth:2,tick(){if(this.nodes++>=this.limit)throw Error('budget');}});
for(const game of ['2048','sudoku','minesweeper','sliding_puzzle']){
 const stats={before:{wins:0,losses:0,truncated:0,total_score:0,moves:0},after:{wins:0,losses:0,truncated:0,total_score:0,moves:0},samples:[]};
 const families=new Set(),pool=cases.filter(c=>c.observation.game===game).filter(c=>{if(families.has(c.family))return false;families.add(c.family);return true;});
 for(let i=0;i<8;i++){
  const sample={seed:report.seed+i};
  for(const [variant,m] of Object.entries(models)){
   const g=new Game(game,report.seed+i),cap=game==='2048'?500:game==='minesweeper'?64:game==='sudoku'?100:50;
   if(game==='sudoku'||game==='sliding_puzzle'){const c=pool[i%pool.length],o=c.observation;g.board=o.board.map(r=>r.slice());g.moves=o.moves;g.score=o.score;if(game==='sudoku'){g.givens=o.givens.map(r=>r.slice());g.history=o.history.map(r=>r.slice());}sample.case_id=c.id;}
   if(game==='minesweeper'){const openings=[[0,0],[0,3],[3,3],[7,7],[7,4],[4,7],[0,7],[7,0]];const [row,col]=openings[i];g.step({row,col});}
   let played=0;
   while(!g.done&&played<cap){const o=g.obs(),legal=g.legal(),z=m.forGame(game).forward(o).z,b=budget(game==='2048'?4000:20000);const d=game==='2048'?tileSearch(o,legal,z,b):game==='minesweeper'?mineSearch(o,legal,z,b):game==='sliding_puzzle'?exactSliding(o,legal,z):sudokuValues(o,legal,z,b);const selected=d.action_values?selectQuality(d.action_values,10,z,game).selected.action:d.action;g.step(selected);played++;}
   const result=!g.done?'truncated':g.winner===1?'wins':'losses';stats[variant][result]++;stats[variant].total_score+=g.score;stats[variant].moves+=played;sample[variant]={result,score:g.score,moves:played};
  }
  stats.samples.push(sample);
 }
 stats.passed=stats.after.wins>=stats.before.wins&&stats.after.truncated<=stats.before.truncated&&(stats.after.wins>stats.before.wins||stats.after.total_score>=stats.before.total_score);
 report.games[game]=stats;fs.writeFileSync(output,JSON.stringify(report,null,2));console.log(JSON.stringify({game,...stats,samples:undefined}));
}

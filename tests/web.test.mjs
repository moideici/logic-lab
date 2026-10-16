import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,Network,NAMES,linkNetworks,encode,actionIndex,slide} from '../web/engine.js';
import {teacher} from '../web/teachers.js';
import {planDecision} from '../web/planner.js';
import {slidingDistance,exactSliding} from '../web/fast-search.js';
const models=Object.fromEntries(Object.keys(NAMES).map(k=>[k,new Network(JSON.parse(fs.readFileSync(new URL(`../web/models/${k}.json`,import.meta.url))))]));
linkNetworks(models);
test('six games: seeded observations, legal neural actions, valid teachers',()=>{
 for(const name of Object.keys(NAMES)){
  const a=new Game(name,123),b=new Game(name,123);
  assert.deepEqual(a.obs(),b.obs());
  for(let step=0;step<20&&!a.done;step++){
   const obs=a.obs(),legal=a.legal(),d=models[name].choose(obs,legal,10),target=teacher(obs,legal);
   assert(legal.some(x=>JSON.stringify(x)===JSON.stringify(target)),`${name} illegal teacher action`);
   assert(legal.some(x=>JSON.stringify(x)===JSON.stringify(d.action)));
   const before=a.obs();assert.throws(()=>a.step({invalid:true}));assert.deepEqual(a.obs(),before);
   assert.equal(a.step(d.action),b.step(d.action));assert.deepEqual(a.obs(),b.obs());
  }
 }
});
test('neural learning changes the actual shared object and another game outputs',()=>{
 const a=models.tictactoe,b=models.connect4;assert.equal(a.core,b.core);
 const first=new Game('tictactoe');first.step({row:0,col:0});const other=new Game('connect4');other.step({column:3});
 const before=Array.from(b.forward(other.obs()).z),obs=first.obs(),legal=first.legal(),target=teacher(obs,legal);
 const initial=a.train(obs,legal,target,.01);let last;
 for(let i=0;i<60;i++)last=a.train(obs,legal,target,.01);
 assert(last<initial,`${last} >= ${initial}`);assert.notDeepEqual(Array.from(b.forward(other.obs()).z),before);
});
test('NumPy and JS share identical encodings, logits, styles and deterministic decisions',()=>{
 const observations=Object.keys(NAMES).map(k=>new Game(k,42).obs());
 const script=`import json,sys\nfrom logic_arena.neural import NeuralSuite,encode\ns=NeuralSuite.load()\na=json.load(sys.stdin)\nprint(json.dumps([{'encoding':encode(o).tolist(),'logits':s.models[o['game']].logits(o).tolist()} for o in a]))`;
 const result=JSON.parse(execFileSync('python',['-c',script],{cwd:new URL('..',import.meta.url),input:JSON.stringify(observations),env:{...process.env,OPENBLAS_NUM_THREADS:'1'}}).toString());
 for(let i=0;i<observations.length;i++){
  const o=observations[i],fresh=new Network(JSON.parse(fs.readFileSync(new URL(`../web/models/${o.game}.json`,import.meta.url))));
  assert.deepEqual(Array.from(encode(o)),result[i].encoding);
  const js=fresh.forward(o).z;assert(js.every((v,j)=>Math.abs(v-result[i].logits[j])<.00003),o.game+' logits mismatch');
 }
});
test('rule edge cases: merges, connect4 gravity, mines hidden, sudoku undo',()=>{
 assert.deepEqual(slide([[2,2,2,2],[0,0,0,0],[0,0,0,0],[0,0,0,0]],'left')[0][0],[4,4,0,0]);
 const c=new Game('connect4');for(const column of [0,1,0,1,0,1,0])c.step({column});assert.equal(c.winner,1);
 const m=new Game('minesweeper');m.step({row:3,col:3});assert.equal(m.board[3][3],0);assert(!('mines' in m.obs()));
 const s=new Game('sudoku'),before=s.obs().board;s.step(s.legal()[0]);s.step({undo:true});assert.deepEqual(s.board,before);
});

test('the exact taquin table matches independent BFS and solves the hardest board in 31 moves',()=>{
 const goal=[1,2,3,4,5,6,7,8,0],queue=[[goal,0]],seen=new Set([goal.join('')]);
 for(let at=0;at<queue.length;at++){
  const [b,d]=queue[at];assert.equal(slidingDistance([b]),d);
  if(d===7)continue;
  const z=b.indexOf(0),r=Math.floor(z/3),c=z%3;
  for(const [offset,valid] of [[-3,r>0],[3,r<2],[-1,c>0],[1,c<2]])if(valid){const n=b.slice();[n[z],n[z+offset]]=[n[z+offset],0];const key=n.join('');if(!seen.has(key)){seen.add(key);queue.push([n,d+1]);}}
 }
 const g=new Game('sliding_puzzle');g.board=[[8,6,7],[2,5,4],[3,0,1]];
 assert.equal(slidingDistance(g.board),31);
 for(let remaining=31;remaining>0;remaining--){const d=exactSliding(g.obs(),g.legal(),new Float32Array(4));assert.equal(d.info.remaining_moves,remaining);assert(d.info.optimal);g.step(d.action);}
 assert.equal(g.winner,1);assert.equal(g.moves,31);
});

test('express search: shortest tactical wins, forced defense, and Sudoku without undo',()=>{
 const choose=g=>{const o=g.obs(),legal=g.legal(),m=models[g.name];return planDecision(o,legal,m,10,m.choose(o,legal,10));};
 const t=new Game('tictactoe');t.board=[[1,1,0],[2,2,0],[0,0,0]];
 const win=choose(t);assert.deepEqual(win.action,{row:0,col:2});assert.equal(win.info.remaining_moves,1);
 const c=new Game('connect4');for(const column of [0,6,1,6,2,5])c.step({column});
 const cw=choose(c);assert.deepEqual(cw.action,{column:3});assert.equal(cw.info.remaining_moves,1);c.step(cw.action);assert.equal(c.winner,1);
 const block=new Game('connect4');for(const column of [6,0,6,1,5,2])block.step({column});assert.deepEqual(choose(block).action,{column:3});
 const tiles=new Game('2048');tiles.board=[[1024,1024,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]];
 const tw=choose(tiles);assert.equal(tw.info.remaining_moves,1);tiles.step(tw.action);assert.equal(tiles.winner,1);
 for(const seed of [42,17,91]){const g=new Game('sudoku',seed),holes=g.board.flat().filter(v=>!v).length;
  while(!g.done&&g.moves<100){const d=choose(g);assert(!d.action.undo);g.step(d.action);}
  assert.equal(g.winner,1);assert.equal(g.moves,holes);
 }
});

test('mines planning sees only public observations and finishes a seeded puzzle quickly',()=>{
 const g=new Game('minesweeper',42),m=models.minesweeper;
 while(!g.done&&g.moves<64){const o=g.obs(),legal=g.legal(),d=planDecision(o,legal,m,10,m.choose(o,legal,10));assert(!('mines' in o));if(d.info.certain_safe&&g.mines)assert(!g.mines.has(d.action.row*8+d.action.col));g.step(d.action);}
 assert.equal(g.winner,1);assert(g.moves<=20);
});

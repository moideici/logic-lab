import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,Network,NAMES,linkNetworks,encode,actionIndex,slide} from '../web/engine.js';
import {teacher} from '../web/teachers.js';
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

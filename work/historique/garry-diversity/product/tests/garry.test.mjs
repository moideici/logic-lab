import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,Network,GarryModel,GARRY_GAMES,encodeGeneral} from '../web/engine.js';
import {chooseDecision} from '../web/decision.js';
import {connectDecision,connectReady,connectRuntime} from '../web/connect4-runtime.js';
const file=new URL('../web/models/garry.json',import.meta.url),load=()=>new GarryModel(JSON.parse(fs.readFileSync(file)));
test('Garry compiled search keeps tactical guarantees when the search budget is exhausted',async()=>{
 await connectReady;assert.equal(connectRuntime(),'wasm');
 const positions=JSON.parse(fs.readFileSync(new URL('./fixtures/connect4-positions.json',import.meta.url)));
 for(const p of positions){
  const g=new Game('connect4');for(const column of p.history)g.step({column});const before=g.obs();
  const d=connectDecision(before,g.legal(),Array.from({length:7},(_,i)=>i*1e12),{limit:0,nodes:0},{timeMs:10000});
  if(p.immediate.length)assert(p.immediate.includes(d.action.column));
  else if(p.forks.length){assert(p.forks.includes(d.action.column));assert(d.info.optimal);assert.equal(d.info.remaining_moves,3);}
  else if(p.safe.length)assert(p.safe.includes(d.action.column));
  assert.deepEqual(g.obs(),before);
 }
});
test('Garry is one physical model with one encoder and one output matrix for all games',()=>{
 const m=load(),views=GARRY_GAMES.map(g=>m.forGame(g));
 assert.equal(m.input,1912);assert.equal(m.output,818);
 for(const v of views){assert.equal(v.w1,m.w1);assert.equal(v.w2,m.w2);assert.equal(v.b1,m.b1);assert.equal(v.b2,m.b2);assert.equal(v.core,m.core);}
 const fused=GarryModel.fuse(GARRY_GAMES.map(g=>JSON.parse(fs.readFileSync(new URL(`../versions/1.0.0/web/models/${g}.json`,import.meta.url)))));
 for(const g of GARRY_GAMES){const old=new Network(JSON.parse(fs.readFileSync(new URL(`../versions/1.0.0/web/models/${g}.json`,import.meta.url)))),env=new Game(g,42);
  for(let i=0;i<12&&!env.done;i++){const o=env.obs(),legal=env.legal(),fresh=fused.forGame(g),a=fresh.forward(o).z,b=old.forward(o).z;assert(a.every((v,k)=>Math.abs(v-b[k])<3e-5));assert.equal(encodeGeneral(o).length,1912);assert(legal.some(x=>JSON.stringify(x)===JSON.stringify(fresh.choose(o,legal).action)));assert(legal.some(x=>JSON.stringify(x)===JSON.stringify(m.forGame(g).choose(o,legal).action)));env.step(legal[Math.floor(env.random()*legal.length)]);}
 }
});
test('Garry learning updates the common model and survives a single JSON export',()=>{
 const m=load(),a=new Game('tictactoe');a.step({row:0,col:0});const b=new Game('connect4');b.step({column:3});
 const before=Array.from(m.forGame('connect4').forward(b.obs()).z),legal=a.legal(),target={row:1,col:1},start=m.train(a.obs(),legal,target,.01);let last=start;
 for(let i=0;i<30;i++)last=m.train(a.obs(),legal,target,.01);
 assert(last<start);assert.notDeepEqual(Array.from(m.forGame('connect4').forward(b.obs()).z),before);
 const restored=new GarryModel(m.export());assert.deepEqual(Array.from(restored.w1),Array.from(m.w1));assert.deepEqual(Array.from(restored.w2),Array.from(m.w2));
});
test('one general forward pass, Python/JS parity, named decisions and legal masks',()=>{
 const m=load(),inputs=GARRY_GAMES.map(g=>new Game(g,42).obs());
 const script=`import json,sys\nfrom logic_arena.general import GarryPolicy,general_encode\nm=GarryPolicy.load('web/models/garry.json')\nprint(json.dumps([{'x':general_encode(o).tolist(),'z':m.logits(o).tolist()} for o in json.load(sys.stdin)]))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{cwd:new URL('..',import.meta.url),input:JSON.stringify(inputs),env:{...process.env,OPENBLAS_NUM_THREADS:'1'}}));
 inputs.forEach((o,i)=>{assert.deepEqual(Array.from(encodeGeneral(o)),expected[i].x);assert(m.forward(o).z.every((v,k)=>Math.abs(v-expected[i].z[k])<3e-5));});
 const original=m.forward.bind(m);let calls=0;m.forward=o=>{calls++;return original(o);};
 const g=new Game('tictactoe'),d=chooseDecision(m,g.obs(),g.legal());assert.equal(calls,1);assert.equal(d.info.identity.codename,'garry');assert.equal(d.info.identity.version,'3.1.0');
 assert.throws(()=>new GarryModel({...m.export(),input:897}));
});

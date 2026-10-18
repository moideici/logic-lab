import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,Network,NAMES,linkNetworks,encode,actionIndex,slide} from '../web/engine.js';
import {teacher} from '../web/teachers.js';
import {planDecision} from '../web/planner.js';
import {slidingDistance,exactSliding,tables2048,spawnExpectation,mineSearch,connectSearch} from '../web/fast-search.js';
import {chooseDecision} from '../web/decision.js';
const models=Object.fromEntries(Object.keys(NAMES).map(k=>[k,new Network(JSON.parse(fs.readFileSync(new URL(`../versions/1.0.0/web/models/${k}.json`,import.meta.url))))]));
linkNetworks(models);
const tacticalPositions=JSON.parse(fs.readFileSync(new URL('./fixtures/connect4-positions.json',import.meta.url)));
const copyConnect=g=>Object.assign(new Game('connect4'),g,{board:g.board.map(row=>row.slice())});
const winningColumns=(g,player=g.player)=>g.legal().filter(a=>{const child=copyConnect(g);child.player=player;child.step(a);return child.winner===player;}).map(a=>a.column);

test('connect4: endgame choice agrees with exhaustive search through the rules',()=>{
 const g=new Game('connect4');for(const column of [4,2,0,4,6,4,1,2,2,5,1,0,6,0,4,6,2,4,0,5,5,1,2,0,1,2,5,4,6,6,1,1,0,5])g.step({column});
 const root=g.player;
 function value(state){if(state.done)return !state.winner?0:state.winner===root?1:-1;const scores=state.legal().map(a=>{const child=copyConnect(state);child.step(a);return value(child);});return (state.player===root?Math.max:Math.min)(...scores);}
 const expected=value(g),budget={nodes:0,tick(){if(this.nodes>=100000)throw Error('budget');this.nodes++;}},d=connectSearch(g.obs(),g.legal(),new Float32Array(7),budget);
 const child=copyConnect(g);child.step(d.action);assert.equal(value(child),expected);assert(d.info.depth>1);
});

test('connect4: tactical wins, safe fallback and forks survive budget exhaustion',()=>{
 for(const p of tacticalPositions){
  const g=new Game('connect4');for(const column of p.history)g.step({column});
  const before=g.obs(),legal=g.legal(),wins=winningColumns(g),safe=[],forks=[];
  for(const a of legal){const child=copyConnect(g);child.step(a);if(child.winner===g.player||!winningColumns(child).length){safe.push(a.column);if(!child.done&&winningColumns(child,g.player).length>=2)forks.push(a.column);}}
  assert.deepEqual(wins,p.immediate);assert.deepEqual(safe,p.safe);assert.deepEqual(forks,p.forks);
  for(const limit of [0,150]){
   const budget={nodes:0,tick(){if(this.nodes>=limit)throw Error('budget');this.nodes++;}},logits=Float64Array.from({length:7},(_,i)=>i*1e12);
   const d=connectSearch(before,legal,logits,budget),column=d.action.column;
   assert(legal.some(a=>a.column===column));
   if(wins.length){assert(wins.includes(column));assert.equal(d.info.remaining_moves,1);}
   else if(forks.length){
    assert(forks.includes(column));assert.equal(d.info.remaining_moves,3);assert(d.info.optimal);
    const child=copyConnect(g);child.step(d.action);
    for(const reply of child.legal()){const response=copyConnect(child);response.step(reply);assert(!response.done);assert(winningColumns(response).length);}
   }else if(safe.length)assert(safe.includes(column),JSON.stringify(p.history));
   else assert(!d.info.optimal);
   assert.deepEqual(g.obs(),before);
  }
 }
});

test('connect4: Python and JavaScript agree with the same priors and node budget',()=>{
 const inputs=tacticalPositions.map(p=>{const g=new Game('connect4');for(const column of p.history)g.step({column});return {obs:g.obs(),legal:g.legal(),logits:Array.from({length:7},(_,i)=>(i*13%7)/3)};});
 const script=`import json,sys\nfrom logic_arena.connect4 import search\nfrom logic_arena.agents import Budget\nprint(json.dumps([search(p['obs'],p['legal'],Budget(150,10000),p['logits']) for p in json.load(sys.stdin)]))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{cwd:new URL('..',import.meta.url),input:JSON.stringify(inputs),env:{...process.env,OPENBLAS_NUM_THREADS:'1'}}));
 inputs.forEach((p,i)=>{const budget={nodes:0,tick(){if(this.nodes>=150)throw Error('budget');this.nodes++;}},actual=connectSearch(p.obs,p.legal,p.logits,budget);assert.deepEqual(actual.action,expected[i][0],JSON.stringify(tacticalPositions[i].history));assert.equal(actual.info.method,expected[i][1].method);assert.equal(actual.info.remaining_moves,expected[i][1].remaining_moves);});
});
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
 const script=`import json,sys\nfrom pathlib import Path\nfrom logic_arena.neural import NeuralPolicy,SPECS,encode\ns={g:NeuralPolicy.load(Path('versions/1.0.0/web/models')/f'{g}.json') for g in SPECS}\na=json.load(sys.stdin)\nprint(json.dumps([{'encoding':encode(o).tolist(),'logits':s[o['game']].logits(o).tolist()} for o in a]))`;
 const result=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{cwd:new URL('..',import.meta.url),input:JSON.stringify(observations),env:{...process.env,OPENBLAS_NUM_THREADS:'1'}}).toString());
 for(let i=0;i<observations.length;i++){
  const o=observations[i],fresh=new Network(JSON.parse(fs.readFileSync(new URL(`../versions/1.0.0/web/models/${o.game}.json`,import.meta.url))));
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

test('one neural evaluation is shared by policy and planner',()=>{
 const g=new Game('tictactoe'),m=models.tictactoe,original=m.forward;
 let calls=0;
 m.forward=function(o){calls++;return original.call(this,o);};
 try{const result=chooseDecision(m,g.obs(),g.legal());assert(result.action);assert.equal(calls,1);}
 finally{m.forward=original;}
});

test('analytical spawn expectation equals explicit enumeration',()=>{
 const tables=tables2048();
 const columns=rows=>Array.from({length:4},(_,c)=>rows.reduce((s,row,r)=>s|(((row>>>(c*4))&15)<<(r*4)),0));
 const heuristic=rows=>rows.concat(columns(rows)).reduce((s,row)=>s+tables.value[row],0);
 const g=new Game('2048',91);
 for(let sample=0;sample<80;sample++){
  const rows=Array.from({length:4},()=>Array.from({length:4},()=>Math.floor(g.random()*8)).reduce((s,v,c)=>s|(v<<(4*c)),0));
  const empty=[];for(let r=0;r<4;r++)for(let c=0;c<4;c++)if(!((rows[r]>>>(c*4))&15))empty.push([r,c]);
  if(!empty.length)continue;
  let expected=0;
  for(const [r,c] of empty)for(const [rank,p] of [[1,.9],[2,.1]]){const child=rows.slice();child[r]|=rank<<(c*4);expected+=p*heuristic(child)/empty.length;}
  assert(Math.abs(spawnExpectation(rows)-expected)<1e-7);
 }
});

test('2048 row tables agree between NumPy and JS',()=>{
 const codes=[0,0x1111,0x2211,0xaaaa,0xffff,...Array.from({length:80},(_,i)=>(i*7151+4327)%65536)];
 const script=`import json,sys\nfrom logic_arena.tiles import row_tables\nt=row_tables()\nprint(json.dumps([[table[code] for table in t] for code in json.load(sys.stdin)]))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{cwd:new URL('..',import.meta.url),input:JSON.stringify(codes),env:{...process.env,OPENBLAS_NUM_THREADS:'1'}}));
 const actual=tables2048();
 codes.forEach((code,i)=>{assert.equal(actual.left[code],expected[i][0]);assert.equal(actual.right[code],expected[i][1]);assert.equal(actual.gain[code],expected[i][2]);assert(Math.abs(actual.value[code]-expected[i][3])<1e-7);});
});

test('a neural preference never overrides a provably safe mines move',()=>{
 const g=new Game('minesweeper',42);g.step({row:3,col:3});
 const logits=new Float32Array(64);
 // Le moteur reçoit seulement les observations. Le test choisit un a priori
 // adversarial pour vérifier, après coup, que les mines restent évitées.
 for(const i of g.mines)logits[i]=1e12;
 const budget={nodes:0,tick(){if(++this.nodes>100000)throw Error('budget');}};
 const result=mineSearch(g.obs(),g.legal(),logits,budget);
 assert(result.info.certain_safe);assert.equal(result.info.risk,0);
 assert(!g.mines.has(result.action.row*8+result.action.col));
});

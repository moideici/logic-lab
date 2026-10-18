import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,GarryModel,actionIndex} from '../web/engine.js';
import {chooseDecision} from '../web/decision.js';
import {connectReady,connectDecision,positionRuntimeValue} from '../web/connect4-runtime.js';
import {positionFeatures} from '../web/value.js';
import {selectQuality,compareQuality} from '../web/quality.js';
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json')));
test('all levels select monotone quantiles; neural endpoint choices resist styles',()=>{
 const values=[0,500,-10,3,-50,7,9].map((v,column)=>({action:{column},quality:[v]}));let last=-Infinity;
 for(let level=0;level<=10;level++){const {selected}=selectQuality(values,level,Array(7).fill(0),'connect4');assert(selected.quality[0]>=last);last=selected.quality[0];}
 for(const game of ['tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle']){const env=new Game(game,91),o=env.obs(),legal=env.legal(),z=model.forGame(game).forward(o).z,scores=legal.map(a=>z[actionIndex(game,a)]);for(const style of ['balanced','exploratory','aggressive'])for(const [level,value] of [[0,Math.min(...scores)],[10,Math.max(...scores)]]){const d=chooseDecision(model,o,legal,{level,style,planning:false});assert.equal(z[actionIndex(game,d.action)],value);}}
});
test('browser planner ranks all six games including intentional errors at zero',async()=>{
 await connectReady;
 for(const game of ['tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle']){const env=new Game(game,91);if(game==='connect4')for(const c of [6,0,6,1,5,2])env.step({column:c});if(game==='tictactoe')env.board=[[1,1,0],[2,2,0],[0,0,0]];const o=env.obs(),legal=env.legal(),a=chooseDecision(model,o,legal,{level:0}),b=chooseDecision(model,o,legal,{level:10});assert(a.info.selected_is_worst,game);assert(b.info.selected_is_best,game);assert(compareQuality(a.info.quality,b.info.quality)<=0,game);assert.deepEqual(env.obs(),o);if(game==='connect4'){assert.equal(b.action.column,3);assert.notEqual(a.action.column,3);assert(a.info.forced_loss);assert(!a.info.forced_win);}if(game==='sudoku'){assert.deepEqual(a.info.quality,[-2]);assert.deepEqual(b.info.quality,[1]);assert(!a.info.optimal);}}
});
test('value features and learned values agree in Python, JS and WASM; migration is lossless',async()=>{
 await connectReady;const old=JSON.parse(fs.readFileSync('versions/2.0.0/garry.json')),migrated=new GarryModel(old);assert.equal(migrated.export().version,'3.2.0');assert.deepEqual(Array.from(migrated.w1),old.w1);assert.deepEqual(new GarryModel(model.export()).positionHead,model.positionHead);
 const obs=[];for(let i=0;i<30;i++){const g=new Game('connect4',i);for(let j=0;j<i&&!g.done;j++)g.step(g.legal()[Math.floor(g.random()*g.legal().length)]);obs.push(g.obs());}
 const py=`import json,sys\nfrom logic_arena.value import features\nprint(json.dumps([features(o).tolist() for o in json.load(sys.stdin)]))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',py],{input:JSON.stringify(obs)}));
 obs.forEach((o,i)=>{const x=positionFeatures(o);assert.deepEqual(x,expected[i]);assert.deepEqual(positionFeatures({...o,current_player:3-o.current_player}),x.map(v=>v===0?0:-v));const head={...model.positionHead,enabled:true};assert(Math.abs(positionRuntimeValue(o,head)-model.positionValue(o))<=.501);});
 for(const position_head of [null,{weights:[]}])assert.throws(()=>new GarryModel({...model.export(),position_head}));
});
test('root analysis preserves every legal move and all tactical guarantees with zero nodes',async()=>{
 await connectReady;const corpus=JSON.parse(fs.readFileSync('tests/fixtures/connect4-positions.json'));
 for(const p of corpus){const g=new Game('connect4');for(const column of p.history)g.step({column});const legal=g.legal(),d=connectDecision(g.obs(),legal,Array(7).fill(0),{nodes:0,limit:0},{analyze:true,timeMs:10000,positionHead:model.positionHead});assert.equal(d.action_values.length,legal.length);const b=selectQuality(d.action_values,10,Array(7).fill(0),'connect4').selected;if(p.immediate.length)assert(p.immediate.includes(b.action.column));else if(p.forks.length)assert(p.forks.includes(b.action.column));else if(p.safe.length)assert(p.safe.includes(b.action.column));}
});

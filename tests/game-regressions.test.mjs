import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {Game,GarryModel,rng,actionIndex} from '../web/engine.js';
import {chooseDecision} from '../web/decision.js';import {planDecision} from '../web/planner.js';import {slidingDistance} from '../web/fast-search.js';import {goAiActions} from '../web/go-ai-policy.js';import {solveSudoku} from '../web/sudoku-solver.js';
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json')));
test('sudoku: rejected guesses cost one life, never fill or recur, third loses',()=>{
 const e=new Game('sudoku',42,{error_limit:3}),answer=solveSudoku(e.board,{limit:1}).solutions[0];
 for(let i=0;i<3;i++){const a=e.legal().find(a=>a.value!==answer[a.row][a.col]),before=structuredClone(e.board);assert(a);e.step(a);assert.deepEqual(e.board,before);assert.equal(e.sudokuState.errors,i+1);assert(!e.legal().some(x=>JSON.stringify(x)===JSON.stringify(a)));assert.equal(e.done,i===2);assert(!JSON.stringify(e.obs()).includes('sudokuAnswer'));}assert.equal(e.winner,0);
});
test('sudoku: all levels terminate in three-life mode, strongest solves, no undo loop',()=>{
 for(const difficulty of ['easy','medium','hard','expert'])for(const level of [0,3,6,9,10]){const e=new Game('sudoku',42,{difficulty,error_limit:3});let steps=0;while(!e.done&&steps<100){const d=chooseDecision(model,e.obs(),e.legal(),{level,random:e.random});assert(!d.action.undo);e.step(d.action);steps++;}assert(e.done,`${difficulty}/${level} did not end`);assert(steps<=84);if(level===10){assert.equal(e.winner,1,difficulty);assert.equal(e.sudokuState.errors,0);}}
});
test('sudoku styles favor constrained versus open cells among proven good placements',()=>{
 const e=new Game('sudoku',42,{error_limit:3}),z=new Float32Array(730),stub={forward:()=>({z}),choose:()=>({action:e.legal()[0],info:{style:'balanced',time_ms:0}})};
 const run=style=>planDecision(e.obs(),e.legal(),stub,10,{info:{style,time_ms:0}},z).action;
 assert.notDeepEqual(run('aggressive'),run('defensive'));
});
test('taquin full trajectories: intermediate strengths differ, level ten remains exactly shortest',()=>{
 const means=[];
 for(const level of [1,5,9,10]){let total=0;for(let seed=0;seed<10;seed++){const e=new Game('sliding_puzzle',seed,{size:3,difficulty:'expert'}),random=rng(seed),z=new Float32Array(4);assert.equal(slidingDistance(e.board),31);while(!e.done&&e.moves<2000){const d=planDecision(e.obs(),e.legal(),{},level,{info:{style:'balanced',time_ms:0}},z,random);e.step(d.action);}assert(e.done);if(level===10)assert.equal(e.moves,31);total+=e.moves;}means.push(total/10);}for(let i=1;i<means.length;i++)assert(means[i]<means[i-1],JSON.stringify(means));
});
test('Go automated games finish legally without negotiation loops; human passes remain legal',()=>{
 for(const level of [0,5,10]){const e=new Game('go',1,{size:9});assert(e.legal().some(a=>a.pass));while(!e.done&&e.moves<167){const legal=goAiActions(e.obs(),e.legal());assert(!legal.some(a=>a.resign||a.dead));e.step(legal[Math.round(level*(legal.length-1)/10)]);}assert(e.done);assert(e.moves<=166);assert.equal(e.goState.phase,'finished');}
 const e=new Game('go',0,{size:19});e.moves=722;for(let i=0;i<4;i++)e.step(goAiActions(e.obs(),e.legal())[0]);assert(e.done);assert.equal(e.moves,726);
});

import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {execFileSync} from 'node:child_process';
import {Game,GarryModel,encode} from '../web/engine.js';
import {largeSliding} from '../web/large-sliding.js';import {slidingDistance} from '../web/fast-search.js';
import {chooseDecision} from '../web/decision.js';import {verifyTransition,decideScore} from '../tools/real-games/external-2048.mjs';
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json')));
test('Hex and Swap2 complete games match Python including legal actions and encodings',()=>{
 const script=`import json,random\nfrom logic_arena.games import make_game\nfrom logic_arena.neural import encode\nr=random.Random(125);out=[]\nfor name in ('hex','gomoku'):\n for seed in range(3):\n  e=make_game(name,seed);steps=[]\n  for i in range(240):\n   if e.done:break\n   o=e.observation();legal=e.legal_actions();a=r.choice(legal);x=encode(o).tolist();reward=e.step(a);steps.append(dict(before=o,legal=legal,x=x,a=a,reward=reward,after=e.observation()))\n  out.append(dict(name=name,seed=seed,steps=steps))\nprint(json.dumps(out))`;
 const corpus=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{maxBuffer:32*1024*1024}));for(const c of corpus){const e=new Game(c.name,c.seed);for(const s of c.steps){assert.deepEqual(e.obs(),s.before);assert.deepEqual(e.legal(),s.legal);assert.deepEqual(Array.from(encode(e.obs())),s.x);assert.equal(e.step(s.a),s.reward);assert.deepEqual(e.obs(),s.after);}}
});
test('all puzzle profiles and large encodings match Python',()=>{
 const script=`import json\nfrom logic_arena.games import make_game\nfrom logic_arena.neural import encode\nout=[]\nfor seed in (0,171,999999):\n for name in ('sudoku','sliding_puzzle'):\n  for n in ((3,4,5) if name=='sliding_puzzle' else (9,)):\n   for d in ('easy','medium','hard','expert'):\n    options=dict(difficulty=d);options.update(dict(size=n) if name=='sliding_puzzle' else {});e=make_game(name,seed,options);out.append(dict(name=name,seed=seed,options=options,o=e.observation(),legal=e.legal_actions(),x=encode(e.observation()).tolist()))\nprint(json.dumps(out))`;
 const corpus=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{maxBuffer:8*1024*1024}));for(const c of corpus){const e=new Game(c.name,c.seed,c.options);assert.deepEqual(e.obs(),c.o);assert.deepEqual(e.legal(),c.legal);assert.deepEqual(Array.from(encode(e.obs())),c.x);if(c.name==='sliding_puzzle'&&c.options.size===3&&c.options.difficulty==='expert')assert.equal(slidingDistance(e.board),31);}
});
test('large A star finds certified shortest public paths and solves easy 4x4 and 5x5',()=>{
 for(const size of [4,5]){const e=new Game('sliding_puzzle',171,{size,difficulty:'easy'}),before=e.obs(),budget=()=>({nodes:0,tick(){if(this.nodes++>=100000)throw Error('budget');}});const result=largeSliding(e.obs(),e.legal(),budget());assert(result.info.solution_found);assert(result.info.optimal);assert(!result.info.analysis_exact);assert.deepEqual(e.obs(),before);const length=result.info.remaining_moves;for(let i=0;i<length;i++){const r=largeSliding(e.obs(),e.legal(),budget()),best=r.action_values.sort((a,b)=>b.quality[0]-a.quality[0]||b.quality[1]-a.quality[1])[0];e.step(best.action);}assert(e.done);}
});
test('new games and puzzle sizes have legal level 0 and 10 decisions without mutation',()=>{
 for(const [name,options]of [['hex',{}],['gomoku',{}],['sliding_puzzle',{size:5,difficulty:'easy'}],['sudoku',{difficulty:'expert'}]]){const e=new Game(name,171,options),before=e.obs(),legal=e.legal();for(const level of [0,10]){const d=chooseDecision(model,before,legal,{level});assert(legal.some(a=>JSON.stringify(a)===JSON.stringify(d.action)));assert(level===10?d.info.selected_is_best:d.info.selected_is_worst);}assert.deepEqual(e.obs(),before);}
});
test('original 2048 adapter verifies score and spawn rather than trusting arbitrary site changes',()=>{
 const before={board:[[2,2,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],score:0},after={board:[[4,0,2,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],score:4};assert(verifyTransition(before,after,'left'));assert(!verifyTransition(before,{...after,score:8},'left'));const bad=structuredClone(after);bad.board[0][0]=8;assert(!verifyTransition(before,bad,'left'));
});
test('score mode keeps searching when a 2048 tile is already present',()=>{
 const e=new Game('2048');e.board=[[2048,1024,512,256],[128,64,32,16],[8,4,2,0],[2,0,0,0]];const d=decideScore(model,e.obs(),e.legal());assert(d.info.score_mode);assert(d.info.nodes>0);assert(e.legal().some(a=>a.direction===d.action.direction));
});

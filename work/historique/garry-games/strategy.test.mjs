import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,GarryModel,encode,actionIndex} from '../web/engine.js';
import {strategyValues} from '../web/strategy-planner.js';
import {newDraughtsState} from '../web/strategy-games.js';
import {chooseDecision} from '../web/decision.js';
import {teacher} from '../web/teachers.js';
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json')));
test('draughts and pawn-race rules, histories and encodings agree with Python over full games',()=>{
 const script=`import json,random\nfrom logic_arena.games import make_game\nfrom logic_arena.neural import encode,action_index\nout=[];rng=random.Random(1710711)\nfor name in ('draughts','breakthrough'):\n for seed in range(3):\n  e=make_game(name,seed);steps=[]\n  for i in range(180):\n   if e.done:break\n   o=e.observation();legal=e.legal_actions();a=rng.choice(legal);x=encode(o).tolist();k=action_index(name,a);reward=e.step(a);steps.append({'before':o,'legal':legal,'action':a,'x':x,'index':k,'reward':reward,'after':e.observation()})\n  out.append({'game':name,'seed':seed,'steps':steps})\nprint(json.dumps(out))`;
 const corpus=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{maxBuffer:32*1024*1024}));
 for(const c of corpus){const g=new Game(c.game,c.seed);for(const s of c.steps){assert.deepEqual(g.obs(),s.before);assert.deepEqual(g.legal(),s.legal);assert.equal(new Set(s.legal.map(a=>actionIndex(g.name,a))).size,s.legal.length);assert(Array.from(encode(g.obs())).every((v,i)=>Math.abs(v-s.x[i])<1e-7));assert.equal(actionIndex(g.name,s.action),s.index);assert.equal(g.step(s.action),s.reward);assert.deepEqual(g.obs(),s.after);}}
});
test('maximum captures retain their player, victims block until the capture ends',()=>{
 const g=new Game('draughts');g.board=Array.from({length:10},()=>Array(10).fill(0));for(const [r,c,v]of [[6,1,1],[5,2,2],[3,4,2],[6,7,1],[5,8,2]])g.board[r][c]=v;g.draughtsState=newDraughtsState(g.board);
 assert.deepEqual(g.legal(),[{from:[6,1],to:[4,3]}]);assert.throws(()=>g.step({from:[6,7],to:[4,9]}));g.step(g.legal()[0]);assert.equal(g.player,1);assert.equal(g.board[5][2],2);assert.deepEqual(g.legal(),[{from:[4,3],to:[2,5]}]);g.step(g.legal()[0]);assert.equal(g.player,2);assert.equal(g.board[5][2],0);assert.equal(g.board[3][4],0);
});
test('bounded search scores and exact capture continuations match Python',()=>{
 const script=`import json\nfrom logic_arena.games import make_game\nfrom logic_arena.strategy_planner import strategy_values\nfrom logic_arena.agents import Budget\nout=[]\nfor name in ('draughts','breakthrough'):\n e=make_game(name);o=e.observation();v,i=strategy_values(o,e.legal_actions(),Budget(100000,10000),max_depth=2);out.append({'obs':o,'legal':e.legal_actions(),'values':v,'depth':i['depth']})\nprint(json.dumps(out))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script]));
 for(const c of expected){const before=structuredClone(c.obs),budget={nodes:0,tick(){if(this.nodes++>=100000)throw Error('budget');}},result=strategyValues(c.obs,c.legal,budget,{maxDepth:2});assert.deepEqual(result.action_values,c.values);assert.equal(result.info.depth,c.depth);assert.deepEqual(c.obs,before);}
});
test('both strategy modes have valid teachers and playable levels zero through ten',()=>{
 for(const name of ['draughts','breakthrough']){const g=new Game(name),legal=g.legal(),obs=g.obs();assert(legal.some(a=>JSON.stringify(a)===JSON.stringify(teacher(obs,legal))));for(const level of [0,5,10]){const d=chooseDecision(model,obs,legal,{level});assert(legal.some(a=>JSON.stringify(a)===JSON.stringify(d.action)));assert.equal(d.info.identity.codename,'garry');if(level===0)assert(d.info.selected_is_worst);if(level===10)assert(d.info.selected_is_best);}assert.deepEqual(g.obs(),obs);}
});

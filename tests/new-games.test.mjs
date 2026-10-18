import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,GarryModel,encode,actionIndex,SPECS} from '../web/engine.js';
import {extraValues,nimValue,lightSolutions} from '../web/extra-planner.js';
import {teacher} from '../web/teachers.js';
import {chooseDecision} from '../web/decision.js';
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json')));
test('new rules, seeds, encodings and transitions agree between Python and JS',()=>{
 const py=`import json,random\nfrom logic_arena.games import make_game\nfrom logic_arena.neural import encode,action_index\nfrom logic_arena.extra_planner import extra_values\nfrom logic_arena.agents import Budget\nout=[];rng=random.Random(1710400)\nfor game in ('reversi','nim','lightsout'):\n for seed in (-12,0,42,4294967301):\n  env=make_game(game,seed);start=env.observation();steps=[]\n  for i in range(35):\n   if env.done:break\n   obs=env.observation();legal=env.legal_actions();a=rng.choice(legal);x=encode(obs).tolist();index=action_index(game,a);reward=env.step(a);steps.append({'observation':obs,'legal':legal,'action':a,'encode':x,'index':index,'reward':reward,'after':env.observation()})\n  out.append({'game':game,'seed':seed,'start':start,'steps':steps})\nprint(json.dumps(out))`;
 const corpus=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',py]));
 for(const c of corpus){const g=new Game(c.game,c.seed);assert.deepEqual(g.obs(),c.start);for(const s of c.steps){assert.deepEqual(g.obs(),s.observation);assert.deepEqual(g.legal(),s.legal);assert.deepEqual(Array.from(encode(g.obs())),s.encode);assert.equal(actionIndex(g.name,s.action),s.index);assert.equal(g.step(s.action),s.reward);assert.deepEqual(g.obs(),s.after);}}
});
test('Nim is exact for every representable position and Lights Out finishes at its minimum',()=>{
 for(let a=0;a<16;a++)for(let b=0;b<16;b++)for(let c=0;c<16;c++)assert.equal(nimValue([a,b,c])[0],(a^b^c)?1:-1);
 for(let seed=0;seed<40;seed++){const g=new Game('lightsout',seed),s=lightSolutions(g.board)[0];let distance=0;for(let v=s;v;v&=v-1)distance++;for(let n=0;n<distance;n++){const d=chooseDecision(model,g.obs(),g.legal(),{level:10});assert(d.info.optimal);g.step(d.action);}assert(g.done);assert.equal(g.moves,distance);assert.equal(g.score,25);}
});
test('Reversi pass is a legal action, capture terminates with the correct score',()=>{
 const g=new Game('reversi');g.board=Array.from({length:6},()=>Array(6).fill(1));g.board[0][0]=0;g.board[0][1]=2;g.player=2;
 assert.deepEqual(g.legal(),[{pass:true}]);assert.equal(actionIndex('reversi',{pass:true}),36);g.step({pass:true});assert.equal(g.player,1);assert(!g.done);g.step({row:0,col:0});assert(g.done);assert.equal(g.winner,1);assert.equal(g.score,36);
});
test('new modes support human actions, legal teachers and all eleven difficulty settings',()=>{
 for(const name of ['reversi','nim','lightsout']){const g=new Game(name,42),obs=g.obs(),legal=g.legal();assert(legal.some(a=>JSON.stringify(a)===JSON.stringify(teacher(obs,legal))));for(let level=0;level<=10;level++){const d=chooseDecision(model,obs,legal,{level});assert(legal.some(a=>JSON.stringify(a)===JSON.stringify(d.action)));if(level===0)assert(d.info.selected_is_worst);if(level===10)assert(d.info.selected_is_best);}assert.deepEqual(g.obs(),obs);}
});
test('legacy imports migrate losslessly and new initial weights match Python',()=>{
 const old=JSON.parse(fs.readFileSync('versions/3.2.0/garry.json')),m=new GarryModel(old),data=m.export();assert.equal(data.version,'0.6.0');assert.deepEqual(data.search_memory,old.search_memory);
 assert.deepEqual(data.w1.slice(0,1906*48),old.w1.slice(0,1906*48));assert.deepEqual(data.w1.slice(4858*48,4864*48),old.w1.slice(1906*48));
 const py=`import json\nfrom logic_arena.general import GarryPolicy\nm=GarryPolicy.load('versions/3.2.0/garry.json').export()\nprint(json.dumps({'w1':m['w1'][1906*48:1910*48],'w2':m['w2'][818:925]}))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',py]));assert.deepEqual(data.w1.slice(1906*48,1910*48),expected.w1);assert.deepEqual(data.w2.slice(818,925),expected.w2);
});

import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {execFileSync} from 'node:child_process';
import {Game,GarryModel} from '../web/engine.js';import {goValues} from '../web/go-planner.js';import {goKey,goCandidate} from '../web/go-games.js';import {chooseDecision} from '../web/decision.js';import {applyStrategicStyles} from '../web/strategic-styles.js';import {inferGoMove} from '../tools/real-games/external-go.mjs';
const styles=['balanced','aggressive','defensive','positional','greedy','exploratory'];
test('styles produce distinct strategic choices while every forced Go capture is preserved',()=>{
 const m=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json'))),e=new Game('go',0,{size:9});const choices=styles.map(style=>chooseDecision(m,e.obs(),e.legal(),{style}).action);assert(new Set(choices.map(a=>JSON.stringify(a))).size>=3);
 for(const [r,c,v]of [[1,1,2],[0,1,1],[1,0,1],[2,1,1]])e.board[r][c]=v;e.goState.seen=[goKey(e.board)];for(const style of styles)assert.deepEqual(chooseDecision(m,e.obs(),e.legal(),{style}).action,{row:1,col:2});
});
test('proved values remain byte-for-byte unchanged by all styles',()=>{
 const e=new Game('go',0,{size:9}),values=[{action:{row:0,col:0},quality:[1]},{action:{row:4,col:4},quality:[-1]}];for(const style of styles)assert.deepEqual(applyStrategicStyles(e.obs(),values,style,true),{values,changed:false});
});
test('strategic style evaluation agrees between Python and JavaScript',()=>{
 const e=new Game('go',0,{size:9});e.step({row:2,col:2});e.step({row:6,col:6});const o=e.obs(),v=goValues(o,e.legal(),{nodes:0,tick(){throw Error('budget');}}).action_values;
 const script=`import json,sys\nfrom logic_arena.strategic_styles import apply_styles\nd=json.load(sys.stdin);print(json.dumps([apply_styles(d['o'],d['v'],s,False)[0] for s in d['styles']]))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{input:JSON.stringify({o,v,styles}),maxBuffer:4*1024*1024}));styles.forEach((style,i)=>{const actual=applyStrategicStyles(o,v,style).values;assert.equal(actual.length,expected[i].length);actual.forEach((v,j)=>{assert.deepEqual(v.action,expected[i][j].action);assert(Math.abs(v.quality[0]-expected[i][j].quality[0])<1e-9);});});
});
test('external Go infers only a legal exact transition, including captures',()=>{
 const e=new Game('go',0,{size:9});for(const [r,c,v]of [[1,1,2],[0,1,1],[1,0,1],[2,1,1]])e.board[r][c]=v;e.goState.seen=[goKey(e.board)];const result=goCandidate(e.board,1,1,2,new Set(e.goState.seen));assert.deepEqual(inferGoMove(e,result.board),{row:1,col:2});const bad=structuredClone(result.board);bad[8][8]=2;assert.equal(inferGoMove(e,bad),null);assert.equal(inferGoMove(e,e.board),null);
});

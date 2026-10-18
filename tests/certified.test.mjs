import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {Game,GarryModel} from '../web/engine.js';
import {chooseDecision} from '../web/decision.js';
import {connectReady} from '../web/connect4-runtime.js';
import {validateSearchMemory,memoryKey,emptySearchMemory} from '../web/search-memory.js';
const model=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json')));
test('learned opening is separated from mathematical non-loss and survives export',async()=>{
 await connectReady;const g=new Game('connect4');g.step({column:3});const experience=chooseDecision(model,g.obs(),g.legal(),{level:10});assert.equal(experience.action.column,2);assert.equal(experience.info.proof,null);assert(!experience.info.certified_non_loss);
 g.step(experience.action);g.step({column:3});const proven=chooseDecision(model,g.obs(),g.legal(),{level:10});assert.equal(proven.info.proof,'non_loss');assert(proven.info.certified_non_loss);assert(!proven.info.search_complete);assert.equal(proven.info.depth,0);
 assert.deepEqual(new GarryModel(model.export()).searchMemory,model.searchMemory);
 assert.deepEqual(new GarryModel(JSON.parse(fs.readFileSync('versions/3.1.0/garry.json'))).searchMemory,emptySearchMemory());
});
test('opening memory and proof semantics agree between Python and JS',async()=>{
 await connectReady;const observations=[],g=new Game('connect4');for(const c of [3,2,3,3,3,3,2,3,2]){g.step({column:c});if(g.player===2)observations.push(g.obs());}
 const script=`import sys,json\nfrom logic_arena.general import GarryPolicy\nfrom logic_arena.planner import plan\nm=GarryPolicy.load('web/models/garry.json').for_game('connect4')\nout=[]\nfor o in json.load(sys.stdin):\n legal=[{'column':c} for c in range(7) if not o['board'][0][c]]\n a,i=plan(o,legal,m,10,legal[0])\n out.append({'action':a,'proof':i['proof'],'certified_non_loss':i['certified_non_loss'],'outcome_proven':i['outcome_proven']})\nprint(json.dumps(out))`;
 const expected=JSON.parse(execFileSync(process.env.PYTHON??'python',['-c',script],{input:JSON.stringify(observations)}));
 observations.forEach((o,i)=>{const legal=o.board[0].flatMap((v,column)=>v?[]:[{column}]),d=chooseDecision(model,o,legal,{level:10});assert.deepEqual({action:d.action,proof:d.info.proof,certified_non_loss:d.info.certified_non_loss,outcome_proven:d.info.outcome_proven},expected[i]);const mirror={...o,board:o.board.map(r=>r.slice().reverse())};assert.equal(memoryKey(o).key,memoryKey(mirror).key);});
});
test('search memory rejects malformed imported knowledge',()=>{
 const e={key:'0000000200000',column:2,guarantee:'experience'};
 for(const entries of [[e,e],[{...e,column:7}],[{...e,guarantee:'perfect'}],[{...e,key:'fffffffffffff'}],[{...e,key:'000000000003f',column:0}]])assert.throws(()=>validateSearchMemory({...emptySearchMemory(),entries}));
 assert.throws(()=>new GarryModel({...model.export(),search_memory:null}));
});

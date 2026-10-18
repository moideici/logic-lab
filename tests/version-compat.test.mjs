import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {GarryModel,Game} from '../web/engine.js';
import {AGENT_VERSION} from '../web/agents.js';

test('0.6.0 accepts the previous 6.0.0 alias and preserves coefficients and decisions',()=>{
 const data=JSON.parse(fs.readFileSync(new URL('../web/models/garry.json',import.meta.url)));
 const before=structuredClone(data),legacy=new GarryModel({...data,version:'6.0.0'}),current=new GarryModel({...data,version:'0.6.0'});
 assert.equal(AGENT_VERSION,'0.6.0');
 assert.equal(legacy.export().version,'0.6.0');
 for(const key of ['w1','w2','b1','b2'])assert.deepEqual(Array.from(legacy[key]),Array.from(current[key]));
 for(const name of ['go','sudoku','sliding_puzzle']){
  const g=new Game(name,42),o=g.obs();
  assert.deepEqual(Array.from(legacy.forward(o).z),Array.from(current.forward(o).z));
 }
 assert.deepEqual(data,before);
 assert.throws(()=>new GarryModel({...data,version:'0.7.0'}));
 assert.throws(()=>new GarryModel({...data,version:'0.6.0',input:data.input-1}));
});

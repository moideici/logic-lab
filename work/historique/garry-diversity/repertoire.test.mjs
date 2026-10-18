import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parseRepertoire,sampleRepertoire} from '../web/repertoire.js';
import {GARRY_GAMES,rng,actionIndex} from '../web/engine.js';
const load=()=>JSON.parse(fs.readFileSync('web/models/garry-repertoire.json'));
test('the shipped repertoire covers all games and contains training data only',()=>{
 const data=load(),bank=parseRepertoire(data);assert(bank.size>1000);assert.deepEqual([...bank.groups.keys()].sort(),GARRY_GAMES.slice().sort());
 assert(data.cases.every(c=>c.split==='train'));assert.equal(new Set(data.cases.map(c=>c.id)).size,data.cases.length);
 const random=rng(3917);for(const game of GARRY_GAMES){const seen=new Set();for(let i=0;i<100;i++){const c=sampleRepertoire(bank,game,random);assert(c);assert(c.legal.some(a=>JSON.stringify(a)===JSON.stringify(c.action)));assert(c.target[actionIndex(game,c.action)]>0);assert(!('mines' in c.observation));seen.add(c.id);}assert(seen.size>=5,game);}
});
test('the sampler is reproducible and rejects held-out data or hidden information',()=>{
 const data=load(),bank=parseRepertoire(data),a=rng(9),b=rng(9);assert.deepEqual(Array.from({length:30},()=>sampleRepertoire(bank,'connect4',a).id),Array.from({length:30},()=>sampleRepertoire(bank,'connect4',b).id));
 const one=structuredClone(data);one.cases=one.cases.slice(0,1);one.cases[0].split='test';assert.throws(()=>parseRepertoire(one),/tests/);
 one.cases[0].split='train';one.cases[0].observation.mines=[1,2];assert.throws(()=>parseRepertoire(one),/privé/);
});
test('invalid labels and duplicates are rejected before browser learning',()=>{
 const data=load(),c=data.cases.find(c=>c.observation.game==='connect4'),one={format:data.format,cases:[structuredClone(c)]};one.cases[0].target.fill(0);assert.throws(()=>parseRepertoire(one));
 assert.throws(()=>parseRepertoire({format:data.format,cases:[c,c]}));
 one.cases[0].target[0]=NaN;assert.throws(()=>parseRepertoire(one));
});

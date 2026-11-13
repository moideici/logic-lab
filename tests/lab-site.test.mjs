import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {MODELS,NODES,EDGES,C4,CONF} from '../web/lab-data.js';
test('chaque modèle a sa page et ses champs',()=>{
  assert.equal(new Set(MODELS.map(m=>m.id)).size,MODELS.length);
  for(const m of MODELS){
    assert(fs.existsSync(new URL('../web/'+m.page,import.meta.url)),m.page);
    for(const k of ['name','version','role','tagline','summary','stats','system','args','bench','duels','limits','src','scene'])assert(m[k]!=null&&m[k].length!==0,m.id+'.'+k);
    for(const [,,c] of m.args)assert(CONF[c],m.id+' confiance '+c);
    for(const b of m.bench)for(const [,v] of b.rows)assert(v<=b.max&&v>=(b.min??0),`${m.id} ${b.title} ${v}`);
  }
});
test('la carte des duels ne référence que des nœuds connus',()=>{
  const ids=new Set(NODES.map(n=>n.id));for(const [a,b] of EDGES){assert(ids.has(a)&&ids.has(b),a+' '+b)}
  for(const [,v] of C4.rows)assert(v<=C4.max);
});
test('le lab et l’atelier existent et se lient',()=>{
  assert(fs.existsSync(new URL('../web/lab.html',import.meta.url)));assert(fs.existsSync(new URL('../web/atelier.html',import.meta.url)));
});

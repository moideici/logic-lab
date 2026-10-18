exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
p=ROOT/'tests/strategy.test.mjs';p.write_text(p.read_text(encoding='utf-8')+'''
test('personal legacy models receive only added trained blocks',()=>{
 const old=JSON.parse(fs.readFileSync('versions/3.2.0/garry.json')),m=new GarryModel(old),before=m.export();
 m.adoptAddedModes(model,old.games);const after=m.export();assert.deepEqual(after.w1.slice(0,1906*48),before.w1.slice(0,1906*48));assert.deepEqual(after.w1.slice(2483*48,2489*48),before.w1.slice(2483*48,2489*48));assert.deepEqual(after.b1,before.b1);assert.deepEqual(after.core,before.core);
 for(let j=0;j<48;j++)assert.deepEqual(after.w2.slice(j*3617,j*3617+818),before.w2.slice(j*3617,j*3617+818));
 assert.deepEqual(after.position_head,before.position_head);assert.deepEqual(after.search_memory,before.search_memory);for(const g of ['draughts','breakthrough','reversi','nim','lightsout'])assert.equal(after.game_steps[g],model.gameSteps[g]);
});
''',encoding='utf-8')
p=ROOT/'tests/repertoire.test.mjs';p.write_text(p.read_text(encoding='utf-8')+'''
test('draughts replay validates capture-state coordinates and rejects private fields',()=>{
 const data=load(),c=structuredClone(data.cases.find(c=>c.observation.game==='draughts')),one={format:data.format,cases:[c]};assert(parseRepertoire(one));
 c.observation.draughts_state.secret_solution=[];assert.throws(()=>parseRepertoire(one));delete c.observation.draughts_state.secret_solution;
 c.observation.draughts_state.forced_piece=[0,0];assert.throws(()=>parseRepertoire(one));
});
''',encoding='utf-8')
print('Added retention and draughts-replay regressions.')

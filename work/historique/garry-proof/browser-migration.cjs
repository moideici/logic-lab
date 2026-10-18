const {chromium}=require('C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true});try{
  const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:8765');await page.waitForFunction(()=>document.getElementById('model-status').textContent.includes('garry v3.2.0'));
  const old=JSON.parse(fs.readFileSync('versions/3.1.0/garry.json'));old.w1[0]=Math.fround(old.w1[0]+.03125);old.steps++;old.game_steps.tictactoe++;old.core.steps++;
  await page.evaluate(data=>new Promise((resolve,reject)=>{const open=indexedDB.open('logic-lab-garry');open.onsuccess=()=>{const tx=open.result.transaction('models','readwrite');tx.objectStore('models').put(data,'garry');tx.oncomplete=resolve;tx.onerror=reject;};open.onerror=reject;}),old);
  await page.reload();await page.waitForFunction(()=>document.getElementById('model-status').textContent.includes('garry v3.2.0'));
  await page.locator('[data-tab="training"]').click();const pending=page.waitForEvent('download');await page.locator('#model-export').click();const download=await pending,model=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  assert.equal(model.version,'3.2.0');assert.equal(model.search_memory.entries.length,7);
  for(const k of ['w1','b1','w2','b2','core','steps','game_steps','position_head'])assert.deepEqual(model[k],old[k],k);
  const decisions=await page.evaluate(async()=>{
   const created=window.logicArena.request({op:'create',game:'connect4',seed:42});if(!created.ok)throw Error(JSON.stringify(created));const session_id=window.logicArena.getSnapshot().session_id;
   function step(column){const r=window.logicArena.request({op:'step',session_id,action:{column}});if(!r.ok)throw Error(JSON.stringify(r));}
   step(3);const experience=await window.logicArena.requestAsync({op:'suggest',session_id,agent:{level:10}});if(!experience.ok)throw Error(JSON.stringify(experience));step(experience.result.action.column);step(3);
   const proof=await window.logicArena.requestAsync({op:'suggest',session_id,agent:{level:10}});if(!proof.ok)throw Error(JSON.stringify(proof));return {experience:experience.result,proof:proof.result};
  });
  assert.equal(decisions.experience.action.column,2);assert.equal(decisions.experience.info.proof,null);assert.equal(decisions.proof.info.proof,'non_loss');assert(decisions.proof.info.certified_non_loss);assert(!decisions.proof.info.search_complete);assert.deepEqual(errors,[]);
  const stored=await page.evaluate(()=>new Promise((resolve,reject)=>{const open=indexedDB.open('logic-lab-garry');open.onsuccess=()=>{const r=open.result.transaction('models').objectStore('models').get('garry');r.onsuccess=()=>resolve({version:r.result.version,memory:r.result.search_memory.entries.length});r.onerror=reject;};open.onerror=reject;}));
  assert.deepEqual(stored,{version:'3.2.0',memory:7});
  const result={version:model.version,memory:7,learned_weights_and_steps_preserved:true,worker_opening:decisions.experience.action,worker_proof:decisions.proof.info.proof,indexedDB:stored,errors};fs.writeFileSync('training-runs/garry-zero-20261017/browser-migration.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

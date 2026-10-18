const {chromium}=require('C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1400,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765');await page.waitForFunction(()=>document.getElementById('model-status').textContent.includes('garry v3.1.0'));
  assert.equal(await page.locator('.game-card').count(),6);
  const states=await page.evaluate(async()=>{
   const result=[];
   for(const game of ['tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle']){
    const created=window.logicArena.request({op:'create',game,seed:42});if(!created.ok)throw Error(JSON.stringify(created));
    const sid=window.logicArena.getSnapshot().session_id; const zero=await window.logicArena.requestAsync({op:'suggest',session_id:sid,agent:{level:0}});if(!zero.ok||!zero.result.info.selected_is_worst)throw Error('Niveau zéro incorrect');
    const reply=await window.logicArena.requestAsync({op:'suggest',session_id:sid,agent:{level:10}});
    if(!reply.ok)throw Error(JSON.stringify(reply));
    if(game==='connect4'&&reply.result.info.target_depth!==20)throw Error('Profondeur cible absente');if(reply.result.info.identity.codename!=='garry')throw Error('Wrong identity');
    const played=await window.logicArena.requestAsync({op:'play',session_id:sid,agent:{level:10}});
    if(!played.ok)throw Error(JSON.stringify(played));
    result.push({game,identity:reply.result.info.identity,runtime:reply.result.info.runtime,revision:window.logicArena.getSnapshot().revision});
   }
   return result;
  });
  await page.evaluate(()=>window.logicArena.request({op:'create',game:'tictactoe',seed:42}));
  await page.locator('[data-tab="training"]').click();await page.locator('#episodes').fill('1');await page.locator('#train-start').click();
  await page.waitForFunction(()=>document.getElementById('training-status').textContent.startsWith('Terminé'),{timeout:30000});
  const exportPending=page.waitForEvent('download');await page.locator('#model-export').click();const download=await exportPending;
  const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(exported.name,'garry');assert.equal(exported.format,'garry-mlp-v2');assert.equal(exported.position_head.enabled,true);assert(!exported.models);assert.equal(exported.input,1912);
  await page.reload();await page.waitForFunction(()=>document.getElementById('model-status').textContent.includes('garry v3.1.0'));
  const keys=await page.evaluate(()=>new Promise((resolve,reject)=>{const request=indexedDB.open('logic-lab-garry');request.onsuccess=()=>{const read=request.result.transaction('models').objectStore('models').getAllKeys();read.onsuccess=()=>resolve(read.result);read.onerror=reject;};request.onerror=reject;}));
  assert.deepEqual(keys,['garry']);assert.deepEqual(errors,[]);const replay=await page.evaluate(async()=>{const response=await fetch('/models/garry.json'),model=await response.json();return await new Promise((resolve,reject)=>{const w=new Worker('./trainer.js',{type:'module'});w.onmessage=e=>{if(e.data.type==='error'){w.terminate();reject(Error(e.data.message));}if(e.data.type==='finished'){w.terminate();resolve({bank:e.data.repertoire_size,examples:e.data.repertoire_examples,unique:e.data.repertoire_unique,version:e.data.model.version});}};w.onerror=e=>reject(Error(e.message));w.postMessage({op:'train',model,game:'tictactoe',episodes:3,seed:77,lr:.005});});});assert.equal(replay.bank,2523);assert(replay.unique>0);assert(replay.examples>0);assert.equal(replay.version,'3.1.0');console.log(JSON.stringify({repertoireReplay:replay}));
  await page.locator('[data-tab="arena"]').click();await page.screenshot({path:'C:/Users/gabor/code/logic-lab/work/garry/interface.png',fullPage:true});
  console.log(JSON.stringify({states,export:{name:exported.name,version:exported.version,architecture:[exported.input,exported.hidden,exported.hidden,exported.output]},indexedDBKeys:keys,errors},null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});



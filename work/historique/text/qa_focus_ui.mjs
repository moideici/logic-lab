import {chromium} from 'file:///C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true}),page=await browser.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('http://127.0.0.1:8766/bilan');
 await page.waitForFunction(()=>document.querySelector('#steps').textContent.includes('restantes'));
 const state=await page.evaluate(()=>({steps:document.querySelector('#steps').textContent,max:document.querySelector('#steps-bar').max,value:document.querySelector('#steps-bar').value,baseline:document.querySelector('#before-values').textContent,curve:document.querySelector('#curve-state').textContent}));
 assert.equal(state.max,1800);assert(state.value>0&&state.value<1800);assert.equal(state.baseline,'25,0 %');assert(!state.steps.includes('NaN'));
 const api=await(await page.request.get('http://127.0.0.1:8766/api/progres')).json();assert.equal(api.entrainement.session,'focus-20261017-210925');assert.equal(api.reference.generation.cas,28);
 assert.deepEqual(errors,[]);fs.writeFileSync('outputs/verification-input-focus-interface.json',JSON.stringify({ok:true,...state,errors,session:api.entrainement.session},null,2));console.log(JSON.stringify({ok:true,...state,errors}));
}finally{await browser.close();}

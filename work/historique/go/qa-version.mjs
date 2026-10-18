import {chromium} from 'file:///C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('http://127.0.0.1:8765');
 await page.waitForFunction(()=>window.logicArena&&document.querySelector('#model-status').textContent.includes('Poids appris'));
 const title=await page.locator('.transfer-strip strong').first().textContent();assert.match(title,/0\.6\.0/);
 const catalog=await(await page.request.get('http://127.0.0.1:8765/api/catalog')).json();
 assert(catalog.ok);assert.equal(catalog.result.games.length,14);for(const game of catalog.result.games)assert.equal(game.ai.version,'0.6.0');
 const decision=await page.evaluate(async()=>{const s=window.logicArena.getSnapshot();return window.logicArena.requestAsync({op:'suggest',session_id:s.session_id});});
 assert(decision.ok);assert.equal(decision.result.info.identity.version,'0.6.0');
 const first=await(await page.request.get('http://127.0.0.1:8765/api/continuous/status')).json();assert.equal(first.result.state,'running');
 await page.screenshot({path:'outputs/garry-0.6.0.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
 const second=await(await page.request.get('http://127.0.0.1:8765/api/continuous/status')).json();assert.equal(second.result.pid,first.result.pid);
 assert.deepEqual(errors,[]);
 const report={ok:true,current_version:'0.6.0',legacy_import_version:'6.0.0',games:14,continuous_pid:first.result.pid,continuous_state:second.result.state,moves_total:second.result.moves_total,promotions:second.result.promotions,remaining_seconds:second.result.remaining_seconds,errors};
 fs.writeFileSync('outputs/verification-version-0.6.0.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}

import {chromium} from 'file:///C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('http://127.0.0.1:8765');await page.waitForFunction(()=>window.logicArena);await page.locator('[data-tab="training"]').click();await page.waitForFunction(()=>document.querySelector('#continuous-progress').max===1800&&Number(document.querySelector('#continuous-moves').textContent)>0);
 assert(await page.locator('#continuous-start').isDisabled());assert(await page.locator('#continuous-stop').isEnabled());
 const status=await(await page.request.get('http://127.0.0.1:8765/api/continuous/status')).json();assert.equal(status.result.id,'8a996a3b756d469aa0ff2be307fb554b');assert.equal(status.result.profile,'weakness');assert.equal(status.result.state,'running');
 const count=await page.locator('#continuous-board .continuous-cell').count();assert(count>0);await page.screenshot({path:'outputs/garry-programme-30-min.png',fullPage:true});assert.deepEqual(errors,[]);const result={ok:true,job:status.result.id,remaining:await page.locator('#continuous-remaining').textContent(),visible_board_cells:count,moves:await page.locator('#continuous-moves').textContent(),errors};fs.writeFileSync('outputs/verification-garry-30min-interface.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await browser.close();}

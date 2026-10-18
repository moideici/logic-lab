import {chromium} from 'file:///C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('http://127.0.0.1:8765');await page.waitForFunction(()=>window.logicArena&&document.querySelector('#model-status').textContent.includes('Poids appris'));
 const link=page.getByRole('link',{name:'Input',exact:true});
 assert.equal(await link.getAttribute('href'),'http://127.0.0.1:8766/');assert.equal(await link.getAttribute('target'),null);assert(await link.isVisible());
 const data=await(await page.request.get('http://127.0.0.1:8765/models/garry.json')).json();assert.equal(data.version,'0.6.0');
 await page.screenshot({path:'outputs/logiclab-input-link-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});assert(await link.isVisible());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 const box=await link.boundingBox();assert(box.x>=0&&box.y>=0&&box.x+box.width<=390&&box.y+box.height<=844);
 await page.screenshot({path:'outputs/logiclab-input-link-mobile.png',fullPage:true});
 await link.click();await page.waitForURL('http://127.0.0.1:8766/');const destination=page.url();await page.goBack();await page.waitForURL('http://127.0.0.1:8765/');await page.waitForFunction(()=>window.logicArena);
 assert.deepEqual(errors,[]);const report={ok:true,destination,same_tab:true,back_navigation:true,mobile_visible:true,garry_version:data.version,errors};fs.writeFileSync('outputs/verification-logiclab-input-link.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}

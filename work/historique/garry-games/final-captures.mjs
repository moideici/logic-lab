import {chromium} from 'file:///C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1440,height:1100}}),out='C:/Users/gabor/code/logic-lab/outputs';
await page.goto('http://127.0.0.1:8765');await page.waitForFunction(()=>document.querySelector('#model-status').textContent.includes('Poids appris'));
const catalog=await page.evaluate(async()=>await(await fetch('/api/catalog')).json());assert.equal(catalog.result.games.length,11);assert.deepEqual(catalog.result.model.architecture,[2494,48,48,3617]);
await page.locator('.game-card').filter({hasText:'Dames internationales'}).click();await page.selectOption('#mode','human');await page.locator('#board .cell:not(:disabled)').first().click();await page.screenshot({path:out+'/Garry-Dames.png',fullPage:true});await page.locator('#board').screenshot({path:out+'/Garry-Dames-plateau.png'});
await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:out+'/Garry-mobile.png',fullPage:true});
console.log(JSON.stringify({catalog:11,architecture:catalog.result.model.architecture,mobile_overflow:false}));await browser.close();

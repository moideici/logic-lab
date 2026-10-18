import {chromium} from 'file:///C:/Users/gabor/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(15000);
const obs=()=>page.evaluate(()=>window.logicArena.getSnapshot().observation);
const create=(game,options={})=>page.evaluate(({game,options})=>window.logicArena.request({op:'create',game,seed:42,options}),{game,options});
const mode=value=>page.selectOption('#mode',value);
const visible=id=>page.locator('#'+id).isVisible();
async function flush(){await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
async function clickFirstMove(){
 const snapshot=await page.evaluate(()=>window.logicArena.getSnapshot()),a=snapshot.legal_actions[0],g=snapshot.observation.game;
 if(g==='2048'){await page.getByRole('button',{name:{up:'Déplacer vers haut',down:'Déplacer vers bas',left:'Déplacer vers gauche',right:'Déplacer vers droite'}[a.direction],exact:true}).click();return;}
 if(g==='nim'){await page.getByRole('button',{name:`Retirer ${a.take} du tas ${a.pile+1}`,exact:true}).click();return;}
 if(g==='sudoku'){await page.locator('.sudoku-grid .cell').nth(a.row*9+a.col).click();await page.getByRole('button',{name:`Saisir ${a.value}`,exact:true}).click();return;}
 if(g==='sliding_puzzle'){const flat=snapshot.observation.board.flat(),n=snapshot.observation.board.length,i=flat.indexOf(0),delta={up:-n,down:n,left:-1,right:1}[a.direction];await page.locator('.sliding-grid .cell').nth(i+delta).click();return;}
 if(a.from){const n=snapshot.observation.board.length;await page.locator('#board .cell').nth(a.from[0]*n+a.from[1]).click();await page.locator('#board .cell').nth(a.to[0]*n+a.to[1]).click();return;}
 if(g==='connect4'){await page.locator('#board .cell').nth(a.column).click();return;}
 const selector=g==='go'?'.go-cell':g==='gomoku'?'.gomoku-cell':g==='hex'?'.hex-cell':'#board .cell';await page.locator(selector).nth(a.row*snapshot.observation.board.length+a.col).click();
}
try{
 await page.goto('http://127.0.0.1:8765');await page.waitForFunction(()=>window.logicArena&&document.querySelector('#model-status').textContent.includes('Poids appris'));
 const catalog=await page.evaluate(()=>window.logicArena.request({op:'catalog'}).result.games),games=[];
 for(const {id:game,players} of catalog){
  await mode('watch');assert((await create(game,game==='go'?{size:9}:{})).ok);await flush();
  assert.equal(await visible('level-two-options'),players===2);assert(await visible('ai-controls'));
  if(['nim','lightsout','connect4'].includes(game))assert.equal(await visible('style-options'),false);
  if(game==='go'){assert.equal(await page.locator('.go-actions').isVisible(),false);assert.match(await page.locator('#turn').innerText(),/Noir/);}
  await mode('human');await flush();assert.equal(await visible('ai-controls'),players===2);assert.equal(await visible('step'),false);assert.equal(await visible('play'),players===2);
  if(game==='go'){assert(await page.getByRole('button',{name:'Passer',exact:true}).isVisible());assert.equal(await page.locator('#human-player option').first().textContent(),'Noir');}
  if(game==='2048'){assert(await visible('manual-actions'));assert.equal(await page.locator('#board .cell:enabled').count(),0);}
  await clickFirstMove();await page.waitForFunction(()=>window.logicArena.getSnapshot().observation.moves>=1);games.push({game,human_action:true,duel_levels:players===2});
  await page.setViewportSize({width:390,height:844});await flush();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`mobile overflow ${game}`);await page.setViewportSize({width:1440,height:1100});
 }
 // Sudoku manual undo restores exactly the same public grid.
 await mode('human');await create('sudoku',{difficulty:'medium'});await flush();const sudokuBefore=(await obs()).board;await clickFirstMove();await flush();await page.getByRole('button',{name:'Annuler',exact:true}).click();await flush();assert.deepEqual((await obs()).board,sudokuBefore);
 // Keyboard 2048 performs one legal move; the board remains a display.
 await create('2048');await flush();const legal=await page.evaluate(()=>window.logicArena.getSnapshot().legal_actions[0].direction);await page.locator('h1').click();await page.keyboard.press({up:'ArrowUp',down:'ArrowDown',left:'ArrowLeft',right:'ArrowRight'}[legal]);await page.waitForFunction(()=>window.logicArena.getSnapshot().observation.moves===1);
 // Go scoring can be accepted by a human and by the automatic opponent.
 await create('go',{size:9});await page.evaluate(()=>{for(let i=0;i<2;i++){const s=window.logicArena.getSnapshot();const r=window.logicArena.request({op:'step',session_id:s.session_id,action:{pass:true}});if(!r.ok)throw Error(JSON.stringify(r));}});await flush();assert.equal((await obs()).go_state.phase,'scoring');await page.getByRole('button',{name:'Accepter le comptage',exact:true}).click();await page.waitForFunction(()=>window.logicArena.getSnapshot().observation.done);await flush();assert.equal(await page.locator('.go-actions').isVisible(),false);
 await create('go',{size:9,komi:0});await page.evaluate(()=>{for(let i=0;i<2;i++){const s=window.logicArena.getSnapshot();window.logicArena.request({op:'step',session_id:s.session_id,action:{pass:true}});}});await flush();await page.getByRole('button',{name:'Accepter le comptage',exact:true}).click();await page.waitForFunction(()=>window.logicArena.getSnapshot().observation.done);await flush();assert.equal((await obs()).winner,0);assert.match(await page.locator('#game-result').textContent(),/Égalité/);
 await create('go',{size:9,komi:5});await flush();assert.equal(await page.locator('#go-komi').inputValue(),'5');
 // A certified expert 3x3 remains solved in exactly 31 moves at level 10.
 await mode('watch');await create('sliding_puzzle',{size:3,difficulty:'expert'});await page.locator('#level').fill('10');await page.locator('#play').click();await page.waitForFunction(()=>window.logicArena.getSnapshot().observation.done);const sliding=await obs();assert.equal(sliding.moves,31);
 await page.screenshot({path:'outputs/garry-coherence-desktop.png',fullPage:true});
 // Browser training has working start/finish and model import/export controls.
 await create('tictactoe');await page.locator('[data-tab="training"]').click();await page.locator('#episodes').fill('1');await page.locator('#train-start').click();await page.waitForFunction(()=>document.querySelector('#training-status').textContent.startsWith('Terminé'));assert(await page.locator('#train-start').isEnabled());assert(await page.locator('#train-stop').isDisabled());
 const downloadPromise=page.waitForEvent('download');await page.locator('#model-export').click();const download=await downloadPromise;assert.equal(download.suggestedFilename(),'garry-0.6.0.json');
 await page.locator('#model-file').setInputFiles('C:/Users/gabor/code/playi/web/models/garry.json');await page.waitForFunction(()=>document.querySelector('#toast').textContent.includes('Garry importé'));
 await page.locator('#model-reset').click();await page.waitForFunction(()=>document.querySelector('#toast').textContent.includes('Derniers poids fournis'));
 await page.locator('[data-tab="protocol"]').click();await page.selectOption('#request-preset','observe');await page.locator('#json-send').click();await page.waitForFunction(()=>{try{return JSON.parse(document.querySelector('#json-output').textContent).ok===true;}catch{return false;}});
 await page.locator('[data-tab="external"]').click();await page.waitForFunction(()=>document.querySelectorAll('.external-history-row').length>0);await page.locator('.external-history-row').filter({hasText:'Go 19 × 19'}).first().click();assert.equal(await visible('external-probes'),false);assert.match(await page.locator('#external-description').textContent(),/pierres/);assert.match(await page.locator('#external-image').getAttribute('alt'),/Go/);
 await page.setViewportSize({width:390,height:844});await flush();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:'outputs/garry-coherence-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);const result={ok:true,games,go_scoring_ends:true,taquin_expert_moves:sliding.moves,sudoku_undo:true,keyboard_2048:true,mobile_no_overflow:true,external_go_metrics_coherent:true,errors};fs.writeFileSync('outputs/verification-coherence-14-jeux.json',JSON.stringify(result,null,2));console.log(JSON.stringify({ok:true,games:games.length,go_scoring_ends:true,taquin_moves:sliding.moves,errors}));
}finally{await browser.close();}

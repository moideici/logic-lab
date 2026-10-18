import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
import {GarryModel,Game,slide,rng,actionIndex} from '../../web/engine.js';
import {tileSearch} from '../../web/fast-search.js';
import {selectQuality} from '../../web/quality.js';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
export const SITE='https://classic.play2048.co/';
export function verifyTransition(before,after,direction){
 const [moved,gain]=slide(before.board,direction);let spawned=0;
 for(let r=0;r<4;r++)for(let c=0;c<4;c++)if(moved[r][c]!==after.board[r][c]){if(moved[r][c]!==0||![2,4].includes(after.board[r][c]))return false;spawned++;}
 return spawned===1&&after.score===before.score+gain;
}
export function decideScore(model,observation,legal,{mode='garry',seed=0,deep=false}={}){
 const began=performance.now(),view=model.forGame('2048'),z=view.forward(observation).z;
 if(mode==='network'){const d=view.choose(observation,legal,10,'balanced',rng(seed),z);return {action:d.action,info:{...d.info,score_mode:true},values:null};}
 if(mode==='random')return {action:legal[Math.floor(rng(seed)()*legal.length)],info:{method:'random_baseline'},values:null};
 const budget={nodes:0,limit:deep?300000:100000,depth:deep?3:2,criticalDepth:deep?4:3,goalRank:16,tick(){if(this.nodes++>=this.limit||performance.now()-began>(deep?200:40))throw Error('budget');}};
 const result=tileSearch(observation,legal,z,budget),selected=selectQuality(result.action_values,10,z,'2048').selected;
 return {action:selected.action,values:result.action_values,info:{...result.info,agent:'garry',score_mode:true,time_ms:performance.now()-began}};
}
async function atomicJSON(filename,value){const tmp=filename+'.'+process.pid+'.tmp';fs.writeFileSync(tmp,JSON.stringify(value));for(let n=0;n<8;n++){try{fs.renameSync(tmp,filename);return;}catch(e){if(!['EPERM','EACCES','EBUSY'].includes(e.code)||n===7)throw e;await new Promise(r=>setTimeout(r,20*(n+1)));}}}
export async function readVisible(page){return page.evaluate(()=>{
 const board=Array.from({length:4},()=>Array(4).fill(0));for(const el of document.querySelectorAll('.tile-container .tile')){const p=el.className.match(/tile-position-(\d+)-(\d+)/),v=Number(el.querySelector('.tile-inner')?.textContent);if(p&&v){const r=+p[2]-1,c=+p[1]-1;if(r>=0&&r<4&&c>=0&&c<4)board[r][c]=Math.max(board[r][c],v);}}
 return {board,score:parseInt(document.querySelector('.score-container')?.textContent??'0',10),game_over:!!document.querySelector('.game-message.game-over'),won:!!document.querySelector('.game-message.game-won')};
 });}
export async function runExternal({jobDir,maxSteps=10000,mode='garry',seed=1712048}){
 if(!Number.isInteger(maxSteps)||maxSteps<1||maxSteps>10000||!['garry','network','random'].includes(mode))throw Error('Paramètres de partie invalides');
 fs.mkdirSync(jobDir,{recursive:true});const modelPath=path.join(ROOT,'web/models/garry.json'),raw=fs.readFileSync(modelPath),model=new GarryModel(JSON.parse(raw)),started=Date.now(),status={state:'starting',site:SITE,game:'2048',mode,steps:0,score:0,best_tile:0,transition_checks:0,probes:0,probe_agreements:0,estimated_regret_sum:0,model_sha256:crypto.createHash('sha256').update(raw).digest('hex'),model_version:model.export().version,seed_scope:'decision tie-breaks only; website tile spawning is uncontrolled',started_at:new Date(started).toISOString()};
 const save=async()=>atomicJSON(path.join(jobDir,'status.json'),{...status,elapsed_seconds:(Date.now()-started)/1000,probe_agreement:status.probes?status.probe_agreements/status.probes:null,estimated_regret_mean:status.probes?status.estimated_regret_sum/status.probes:null});await save();
 let browser;
 try{
  browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:900,height:900}}),page=await context.newPage();page.setDefaultTimeout(15000);await page.goto(SITE,{waitUntil:'domcontentloaded',timeout:30000});await page.waitForSelector('.tile-container .tile');
  await page.addStyleTag({content:'.tile,.tile-inner{transition:none!important;animation:none!important}'});
  let state=await readVisible(page);status.state='running';
  for(let step=0;step<maxSteps;step++){
   if(fs.existsSync(path.join(jobDir,'stop.json'))){status.state='stopped';break;}
   if(state.game_over){status.state='finished';break;}
   if(state.won){const keep=page.locator('.keep-playing-button');if(await keep.isVisible())await keep.click();state=await readVisible(page);}
   const env=Object.assign(Object.create(Game.prototype),{name:'2048',board:state.board,player:1,done:false,winner:null,moves:step,score:state.score});const observation=env.obs(),legal=env.legal();
   if(!legal.length){status.state='finished';break;}
   const decision=decideScore(model,observation,legal,{mode,seed:seed+step});let probe=null;
   if(step%25===0){const deeper=decideScore(model,observation,legal,{deep:true}),at=deeper.values.find(v=>v.action.direction===decision.action.direction),best=Math.max(...deeper.values.map(v=>v.quality[0]));const regret=Math.max(0,best-at.quality[0]);status.probes++;if(regret<1e-7)status.probe_agreements++;status.estimated_regret_sum+=regret;probe={depth:deeper.info.depth,regret,analysis_ms:deeper.info.time_ms,scope:'bounded_expectimax_estimate'};}
   const before=state;await page.keyboard.press({up:'ArrowUp',down:'ArrowDown',left:'ArrowLeft',right:'ArrowRight'}[decision.action.direction]);
   let after=null;for(let attempt=0;attempt<12;attempt++){await page.waitForTimeout(45);after=await readVisible(page);if(verifyTransition(before,after,decision.action.direction))break;}
   if(!verifyTransition(before,after,decision.action.direction))throw Error('Transition du site incompatible : partie arrêtée sans corriger le score ni le plateau.');
   status.transition_checks++;status.steps=step+1;status.score=after.score;status.best_tile=Math.max(...after.board.flat());status.board=after.board;status.last_action=decision.action.direction;status.last_depth=decision.info.depth??0;status.last_decision_ms=decision.info.time_ms??null;
   fs.appendFileSync(path.join(jobDir,'trace.jsonl'),JSON.stringify({step:step+1,before:{board:before.board,score:before.score},action:decision.action,info:decision.info,probe,after:{board:after.board,score:after.score},verified:true})+'\n');state=after;
   if(step%10===0||state.game_over){const tmp=path.join(jobDir,'board.tmp.png');await page.locator('.game-container').screenshot({path:tmp});fs.renameSync(tmp,path.join(jobDir,'board.png'));await save();}
  }
  if(status.state==='running')status.state=state.game_over?'finished':'truncated';status.score=state.score;status.best_tile=Math.max(...state.board.flat());status.board=state.board;
  const tmp=path.join(jobDir,'board.tmp.png');await page.locator('.game-container').screenshot({path:tmp});fs.renameSync(tmp,path.join(jobDir,'board.png'));
 }catch(error){status.state='error';status.error=error.message;}
 finally{if(browser)await browser.close();status.finished_at=new Date().toISOString();await save();}
 console.log(JSON.stringify(status));return status;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args=Object.fromEntries(process.argv.slice(2).reduce((pairs,v,i,a)=>{if(v.startsWith('--'))pairs.push([v.slice(2),a[i+1]]);return pairs;},[]));
 if(!args['job-dir'])throw Error('--job-dir est nécessaire');await runExternal({jobDir:path.resolve(args['job-dir']),maxSteps:Number(args['max-steps']??10000),mode:args.mode??'garry',seed:Number(args.seed??1712048)});
}

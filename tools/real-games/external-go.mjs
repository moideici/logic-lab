import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';import {chromium} from 'playwright';
import {Game,GarryModel} from '../../web/engine.js';import {goKey,goCandidate} from '../../web/go-games.js';import {chooseDecision} from '../../web/decision.js';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');export const GO_SITE='https://www.cosumi.net/en/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function atomic(file,value){const tmp=file+'.tmp';fs.writeFileSync(tmp,JSON.stringify(value));for(let i=0;i<12;i++)try{fs.renameSync(tmp,file);return;}catch(e){if(!['EPERM','EACCES','EBUSY'].includes(e.code)||i===11)throw e;await sleep(15*(i+1));}}
export async function readGoVisible(page,size){return page.evaluate(n=>{const el=document.querySelector('#stone'),ctx=el.getContext('2d'),step=document.querySelector('#blackstone').width,margin=(el.width-step*(n-1))/2;const board=Array.from({length:n},(_,r)=>Array.from({length:n},(_,c)=>{const d=ctx.getImageData(Math.round(margin+c*step),Math.round(margin+r*step),1,1).data;return d[3]<128?0:(d[0]+d[1]+d[2])/3<150?1:2;}));return {board,message:document.querySelector('#message')?.textContent??'',step,margin,width:el.width,ready:getComputedStyle(document.querySelector('#darkener')).display==='none'};},size);}
export async function submitGoPass(page){await page.locator('#pass-2').click();await page.locator('#yes').waitFor();await sleep(650);if(!/Are You Sure to Pass/.test(await page.locator('#message').innerText()))throw Error('Confirmation de passe inattendue');await page.locator('#yes').click();await page.locator('#yes').waitFor({state:'detached'});}
export function inferGoMove(env,board){const n=board.length,added=[];for(let r=0;r<n;r++)for(let c=0;c<n;c++)if(!env.board[r][c]&&board[r][c]===env.player)added.push({row:r,col:c});if(added.length!==1)return null;const a=added[0],candidate=goCandidate(env.board,env.player,a.row,a.col,new Set(env.goState.seen));return candidate&&goKey(candidate.board)===goKey(board)?a:null;}
export async function runGoExternal({jobDir,size=19,maxSteps=500,mode='garry',opponentLevel=1}){
 if(![9,13,19].includes(size)||!Number.isInteger(maxSteps)||maxSteps<1||maxSteps>1000||!['garry','network','random'].includes(mode)||!Number.isInteger(opponentLevel)||opponentLevel<1||opponentLevel>9)throw Error('Paramètres Go invalides');
 fs.mkdirSync(jobDir,{recursive:true});const raw=fs.readFileSync(path.join(ROOT,'web/models/garry.json')),model=new GarryModel(JSON.parse(raw)),env=new Game('go',0,{size,komi:6.5}),began=Date.now(),s={state:'starting',game:'go',site:GO_SITE,mode,size,opponent:'COSUMI',opponent_level:opponentLevel,site_rules:'Japanese territory scoring, komi 6.5; site result is authoritative',local_legality:'no suicide and positional superko; stricter repetition filter',steps:0,transition_checks:0,garry_moves:0,model_sha256:crypto.createHash('sha256').update(raw).digest('hex'),model_version:model.export().version,started_at:new Date().toISOString()};let browser;
 let verifiedBoard=env.board.map(row=>row.slice());
 const save=async()=>{s.elapsed_seconds=(Date.now()-began)/1000;s.board=verifiedBoard;s.current_player=env.player;s.captures=env.goState.captures;await atomic(path.join(jobDir,'status.json'),s);};
 const record=async(action,actor,source)=>{verifiedBoard=env.board.map(row=>row.slice());s.steps++;s.transition_checks++;if(actor===s.garry_color)s.garry_moves++;fs.appendFileSync(path.join(jobDir,'trace.jsonl'),JSON.stringify({step:s.steps,actor,action,source,board:env.board,verified:true,time:new Date().toISOString()})+'\n');await save();};
 const terminal=message=>/^(You Win|You Lose|Draw)/.test(message);
 try{
  await save();browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1100,height:1000}});page.setDefaultTimeout(20000);await page.goto(GO_SITE,{waitUntil:'domcontentloaded',timeout:45000});await page.locator('#choice-'+size).click();if(size!==9)await page.locator('#choice-0').click();await page.locator('#choice-'+opponentLevel).click();await page.locator('#ok').waitFor();await sleep(650);const color=await page.locator('#message').innerText();s.garry_color=/Black/.test(color)?1:2;await page.locator('#ok').click();await page.locator('#ok').waitFor({state:'detached'});await sleep(500);s.state='running';await save();
  const screenshot=async()=>{const tmp=path.join(jobDir,'board.tmp.png');await page.locator('#thearea').screenshot({path:tmp});for(let i=0;i<10;i++)try{fs.renameSync(tmp,path.join(jobDir,'board.png'));break;}catch(e){if(i===9)throw e;await sleep(20*(i+1));}};
  await screenshot();let waiting=Date.now(),lastMessage='';
  while(s.steps<maxSteps){
   if(fs.existsSync(path.join(jobDir,'stop.json'))){s.state='stopped';break;}
   let visible=await readGoVisible(page,size);s.site_message=visible.message;
   if(terminal(visible.message)){s.state='finished';s.result_text=visible.message;s.winner=visible.message.startsWith('You Win')?'garry':visible.message.startsWith('You Lose')?'cosumi':'draw';break;}
   if(visible.message==='COSUMI Passed'&&lastMessage!==visible.message){if(env.player===s.garry_color)throw Error('Passe adverse reçue hors tour');env.step({pass:true});await record({pass:true},3-s.garry_color,'site_pass_message');lastMessage=visible.message;await sleep(650);await page.locator('#ok').click();await sleep(450);continue;}
   if(!visible.message)lastMessage='';
   if(env.player!==s.garry_color){const action=inferGoMove(env,visible.board);if(action){const actor=env.player;env.step(action);await record(action,actor,'canvas_pixels');waiting=Date.now();await screenshot();continue;}if(Date.now()-waiting>90000)throw Error('Délai de réponse du site dépassé');await sleep(100);continue;}
   if(goKey(visible.board)!==goKey(env.board))throw Error('Le plateau visible diverge de la partie vérifiée');
   if(!visible.ready){await sleep(100);continue;}
   if(env.goState.phase!=='play'){await sleep(100);if(Date.now()-waiting>90000)throw Error('Le site n’a pas publié son résultat après les passes');continue;}
   const legal=env.legal().filter(a=>!a.resign);let decision;
   if(mode==='random')decision={action:legal[Math.floor(Math.random()*legal.length)],info:{method:'random'}};
   else if(mode==='network')decision=model.forGame('go').choose(env.obs(),legal,10);
   else decision=chooseDecision(model,env.obs(),legal,{level:10});
   const a=decision.action,before=goKey(env.board),actor=env.player;if(a.pass)await submitGoPass(page);else{const box=await page.locator('#clickable').boundingBox();await page.mouse.click(box.x+(visible.margin+a.col*visible.step)*box.width/visible.width,box.y+(visible.margin+a.row*visible.step)*box.height/visible.width);}
   env.step(a);let accepted=false;const ownKey=goKey(env.board),moveStart=Date.now();
   while(Date.now()-moveStart<90000){visible=await readGoVisible(page,size);const actual=goKey(visible.board);if(actual===ownKey){accepted=true;break;}const reply=inferGoMove(env,visible.board);if(reply){await record(a,actor,'canvas_pixels_composed_reply');const other=env.player;env.step(reply);await record(reply,other,'canvas_pixels');accepted=true;break;}if(terminal(visible.message)){s.state='finished';s.result_text=visible.message;s.winner=visible.message.startsWith('You Win')?'garry':visible.message.startsWith('You Lose')?'cosumi':'draw';accepted=true;break;}if(actual!==before&&actual!==ownKey)throw Error('Transition Go non reconnue : arrêt sans modifier le site');await sleep(80);}
   if(!accepted)throw Error('Le site n’a pas confirmé le coup envoyé');
   if(env.player!==actor&&goKey(visible.board)===ownKey)await record(a,actor,a.pass?'site_pass_control':'canvas_pixels');
   s.last_action=a;s.last_decision_ms=decision.info.time_ms??null;waiting=Date.now();await save();await screenshot();if(s.state==='finished')break;
  }
  if(s.state==='running')s.state='truncated';await screenshot();
 }catch(e){s.state='error';s.error=e.message;}finally{if(browser)await browser.close();s.finished_at=new Date().toISOString();await save();}
 console.log(JSON.stringify({state:s.state,steps:s.steps,garry_moves:s.garry_moves,result:s.result_text,error:s.error}));return s;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){const a=Object.fromEntries(process.argv.slice(2).reduce((out,v,i,all)=>{if(v.startsWith('--'))out.push([v.slice(2),all[i+1]]);return out;},[]));if(!a['job-dir'])throw Error('--job-dir requis');await runGoExternal({jobDir:path.resolve(a['job-dir']),size:Number(a.size??19),maxSteps:Number(a['max-steps']??500),mode:a.mode??'garry',opponentLevel:Number(a['opponent-level']??1)});}

import {gameUiPolicy} from './game-ui-policy.js';
import {altDecision} from './arena-players.js';
import {AGENTS,AGENT_VERSION,agentIdentity} from './agents.js';
import {CONNECT_LIMITS,CONNECT_TIMES} from './connect4-runtime.js';
import {LIMITS,TIMES} from './planner.js';
import {chooseDecision} from './decision.js';
import {slidingDistance} from './fast-search.js';
import {Game,Network,GarryModel,NAMES,SPECS,STYLES,TEMPS,linkNetworks,rng} from './engine.js';

const $=id=>document.getElementById(id);
import {puzzleOptions,resetPuzzleSelection,renderPuzzleControls,renderPuzzleBoard} from './puzzle-ui.js';
import {renderGoBoard,renderGoControls} from './go-ui.js';
const icons={tictactoe:'×○','2048':'2ⁿ',sudoku:'1·9',connect4:'●●',minesweeper:'✳',sliding_puzzle:'▦',reversi:'◐',nim:'Ⅲ',lightsout:'☼',draughts:'◎',breakthrough:'⇧',hex:'⬡',gomoku:'●·●',go:'●○'};
const models={};
let general=null,selectedPiece=null,packagedModel=null;
function useGarry(data,knownGames=data?.games){const next=data instanceof GarryModel?data:new GarryModel(data);if(packagedModel&&Array.isArray(knownGames)&&knownGames.length<14)next.adoptAddedModes(packagedModel,knownGames);general=next;for(const name of Object.keys(NAMES))models[name]=next.forGame(name);cancelInference(new DOMException('Modèle remplacé','AbortError'),true);}
let game=new Game('tictactoe',42),sessionId=crypto.randomUUID(),revision=0,sequence=0;
let running=false,timer=null,training=false,worker=null,lastDecision=null,lastAction=null;
let generation=0,trace=[],listeners=new Set(),lossCurve=[],db=null,trainingGame=null;
let inferenceWorker=null,requestId=0,runVersion=0,frame=null,startedAt=null,finishedAt=null;
const pending=new Map(),workerModels=new Map();
function queueRender(){if(frame!==null)return;frame=requestAnimationFrame(()=>{frame=null;render();renderEvents();});}
function clockStart(){if(startedAt===null)startedAt=performance.now();}
function cancelInference(error=new DOMException('Calcul annulé','AbortError'),force=false){
 if(!pending.size&&!force)return;
 const instance=inferenceWorker;inferenceWorker=null;workerModels.clear();
 if(instance)instance.terminate();
 for(const task of pending.values()){clearTimeout(task.timeout);task.reject(error);}
 pending.clear();
}
function decideAsync(config={}){
 const alt=altDecision(game,game.multiplayer?game.player:1);if(alt)return alt;
 if(!current())return Promise.reject(Error('Le modèle se charge.'));
 if(!inferenceWorker){
  const instance=new Worker('./inference-worker.js',{type:'module'});
  inferenceWorker=instance;workerModels.clear();
  instance.onmessage=e=>{
   if(inferenceWorker!==instance)return;
   const task=pending.get(e.data.id);if(!task)return;
   pending.delete(e.data.id);clearTimeout(task.timeout);
   e.data.error?task.reject(Error(e.data.error)):task.resolve(e.data.result);
  };
  instance.onerror=e=>{
   if(inferenceWorker!==instance)return;
   cancelInference(Error(e.message||'Erreur de calcul'),true);
  };
 }
 const m=current(),previous=workerModels.get(m.game),changed=!previous||previous.model!==m||previous.core!==m.core||previous.steps!==m.steps;
 const id=++requestId,message={id,observation:game.obs(),legal:game.legal(),level:config.level??effectiveLevel(),style:config.style??$('style').value,planning:config.planning??$('planning').checked,seed:config.seed??((game.seed+revision*2654435761)>>>0)};
 if(changed)message.model=m.export();
 return new Promise((resolve,reject)=>{
  const timeout=setTimeout(()=>{if(pending.has(id))cancelInference(Error('Le calcul a dépassé 10 secondes. Vous pouvez le relancer.'));},10000);
  pending.set(id,{resolve,reject,timeout});
  try{inferenceWorker.postMessage(message);if(changed)workerModels.set(m.game,{model:m,core:m.core,steps:m.steps});}
  catch(error){pending.delete(id);clearTimeout(timeout);reject(error);}
 });
}
const fmt=n=>new Intl.NumberFormat('fr-FR').format(n);
const current=()=>models[game.name];
const effectiveLevel=()=>game.multiplayer&&$('mode').value==='watch'&&game.player===2?+$('level-two').value:+$('level').value;
const humanTurn=()=>$('mode').value==='human'&&(game.multiplayer?game.player===+$('human-player').value:true);
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,5000);}
function errorMessage(error){if(error.name!=='AbortError')toast(error.message||String(error));}
function download(name,text,type='application/json'){const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function openDB(){return new Promise(resolve=>{try{const req=indexedDB.open('logic-lab-garry',1);req.onupgradeneeded=()=>req.result.createObjectStore('models');req.onsuccess=()=>resolve(req.result);req.onerror=()=>resolve(null);}catch{resolve(null);}});}
function storedModel(name){return new Promise(resolve=>{if(!db)return resolve(null);const r=db.transaction('models').objectStore('models').get(name);r.onsuccess=()=>resolve(r.result||null);r.onerror=()=>resolve(null);});}
async function persistModels(){if(!db){toast('Stockage indisponible : exportez vos modèles pour les conserver.');return;}await new Promise((resolve,reject)=>{const tx=db.transaction('models','readwrite');tx.objectStore('models').put(general.export(),'garry');tx.oncomplete=resolve;tx.onerror=()=>reject(Error('Sauvegarde impossible. Exportez vos modèles.'));});}
function setTab(tab){document.querySelectorAll('.tab-panel').forEach(el=>el.hidden=el.id!==`${tab}-tab`);document.querySelectorAll('[data-tab]').forEach(el=>el.classList.toggle('active',el.dataset.tab===tab));if(tab!=='arena')pause();if(tab==='protocol')preset();if(tab==='training')drawLoss();}
function snapshot(){return {session_id:sessionId,revision,running,seed:game.seed,observation:game.obs(),legal_actions:game.legal()};}
function emit(type,extra={}){const e={protocol:'logic-arena.v1',seq:++sequence,type,timestamp:Date.now()/1000,...snapshot(),...extra};trace.push(e);for(const fn of listeners){try{fn(e);}catch(error){console.error(error);}}window.dispatchEvent(new CustomEvent('logic-arena',{detail:e}));queueRender();return e;}
function pause(){cancelInference();clearTimeout(timer);timer=null;if(!running)return;running=false;runVersion++;clearTimeout(timer);timer=null;renderControls();emit('stopped',{reason:game.done?'terminal':'cancelled'});}
function newGame(name=game.name,seed=+$('seed').value,options=null){options??=name==='go'?{size:+$('go-size').value,komi:+$('go-komi').value}:puzzleOptions(name);if(!Number.isInteger(seed))throw Error('La graine doit être un entier');const next=new Game(name,seed,options);pause();game=next;selectedPiece=null;resetPuzzleSelection();sessionId=crypto.randomUUID();revision=0;sequence=0;trace=[];lastDecision=null;lastAction=null;startedAt=null;finishedAt=null;generation++;emit('created',{});render();}
function selectGame(name){if(training){toast('Arrêtez l’entraînement avant de changer de jeu.');return;}newGame(name);preset();}
function decide(config={}){if(!current())throw Error('Le modèle est encore en cours de chargement');const level=config.level??effectiveLevel(),style=config.style??$('style').value;const random=Number.isInteger(config.seed)?rng(config.seed):game.random;return chooseDecision(current(),game.obs(),game.legal(),{level,style,random,planning:config.planning??$('planning').checked});}
function transition(action,info={}){clockStart();const actor=game.player,reward=game.step(action);revision++;if(game.done)finishedAt=performance.now();lastAction=action;lastDecision=info.agent?.startsWith('neural')?info:null;const e=emit(game.done?'finished':'step',{action,reward,actor,info});return e;}
async function playOne(){if(game.done)return;if(humanTurn()){toast('C’est votre tour : cliquez sur le plateau.');return;}clockStart();const version=generation,rev=revision,promise=decideAsync();renderControls();let d;try{d=await promise;}finally{renderControls();}if(version===generation&&rev===revision&&!game.done){transition(d.action,d.info);if($('mode').value==='human'&&!game.done&&!humanTurn()&&!running){timer=setTimeout(()=>{if(version===generation&&!humanTurn()&&!game.done&&!running)playOne().catch(errorMessage);},+$('speed').value);}}}
async function schedule(token){
 if(!running||token!==runVersion)return;
 const began=performance.now();
 try{do{
  if(game.done){pause();return;}
  if(game.moves>=10000){pause();emit('truncated',{reason:'max_steps'});toast('Budget de 10 000 coups atteint.');return;}
  if(humanTurn())break;
  const version=generation,rev=revision,d=await decideAsync();
  if(!running||token!==runVersion)return;
  if(version!==generation||rev!==revision){timer=setTimeout(()=>schedule(token),0);return;}
  transition(d.action,d.info);
  await new Promise(resolve=>requestAnimationFrame(resolve));
 }while(+$('speed').value===0&&performance.now()-began<12);
 }catch(error){if(!running||token!==runVersion)return;pause();errorMessage(error);return;}
 if(game.done){pause();return;}
 if(running&&token===runVersion)timer=setTimeout(()=>schedule(token),humanTurn()?100:+$('speed').value);
}
function start(){if($('mode').value==='human'){playOne().catch(errorMessage);return;}if(game.done){toast('Lancez une nouvelle partie pour rejouer.');return;}if(!current()){toast('Chargement du réseau en cours…');return;}if(running){pause();return;}clockStart();running=true;const token=++runVersion;emit('started');renderControls();schedule(token);}
function clickCell(r,c){humanAction(game.name==='connect4'?{column:c}:{row:r,col:c});}
function humanAction(action){if(!humanTurn()||game.done)return;try{transition(action,{agent:'human'});if(!game.done&&!humanTurn()&&!running){const version=generation;timer=setTimeout(()=>{if(version===generation&&!humanTurn()&&!game.done&&!running)playOne().catch(errorMessage);},+$('speed').value);}}catch(error){errorMessage(error);}}
const extraHints={hex:'Bleu relie le haut au bas ; orange relie la gauche à la droite. Après le premier coup, le second joueur peut échanger les couleurs.',draughts:'Sélectionnez un pion puis sa destination. Prise maximale obligatoire, pions capables de prendre en arrière, dames à longue portée. Blanc commence.',breakthrough:'Sélectionnez un pion puis sa destination. Avancez tout droit ou en diagonale, prenez en diagonale. Atteignez la dernière rangée pour gagner.',reversi:'Encadrez les pions adverses pour les retourner. Noir commence. Si aucun coup n’est possible, passez. Le plus de pions à la fin gagne.',nim:'Retirez une ou plusieurs allumettes d’un seul tas. Celui qui prend la dernière gagne.',lightsout:'Cliquez sur une lampe : elle et ses voisines en croix changent d’état. Éteignez les 25 lampes.'};
function gomokuHint(){return {opening_three:'Swap2 : le premier joueur pose noir, blanc, puis noir.',choose_or_extend:'Le second joueur choisit sa couleur, ou pose encore blanc puis noir pour laisser le choix à son adversaire.',opening_two:'Posez maintenant la seconde pierre supplémentaire : noire.',choose_color:'Le premier joueur choisit sa couleur. Blanc jouera ensuite.',play:'Alignez exactement cinq pierres. Six pierres ou plus ne gagnent pas.'}[game.gomokuState.phase];}
function renderGomokuBoard(){const b=$('board'),s=game.gomokuState,active=humanTurn()&&!game.done,canPlace=s.phase!=='choose_color';b.className='board-gomoku';b.innerHTML='';const grid=document.createElement('div');grid.className='gomoku-grid';game.board.forEach((row,r)=>row.forEach((v,c)=>{const cell=document.createElement('button');cell.className='gomoku-cell'+(v?' stone-'+v:'');cell.disabled=!active||!!v||!canPlace;cell.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v===1?'noir':v===2?'blanc':'vide'}`);if(lastAction?.row===r&&lastAction?.col===c)cell.classList.add('last-stone');if(s.winning_line.some(p=>p[0]===r&&p[1]===c))cell.classList.add('winning-stone');cell.onclick=()=>humanAction({row:r,col:c});grid.append(cell);}));b.append(grid);if(['choose_or_extend','choose_color'].includes(s.phase)){const choices=document.createElement('div');choices.className='gomoku-choices';for(const [value,text]of [['black','Choisir noir'],['white','Choisir blanc']]){const button=document.createElement('button');button.textContent=text;button.disabled=!active;button.onclick=()=>humanAction({choose:value});choices.append(button);}b.append(choices);}$('game-result').hidden=!game.done;$('game-result').textContent=game.winner===0?'Match nul':$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez aligné cinq pierres !':`Victoire du joueur ${game.winner}`;}
function renderHexBoard(){
 const board=$('board'),active=humanTurn()&&!game.done,path=game.hexState.winning_path;
 board.className='board-hex';board.innerHTML='';
 const legend=document.createElement('p');legend.className='hex-legend';legend.innerHTML='<span>Bleu ↕</span><span>Orange ↔</span>';board.append(legend);
 const grid=document.createElement('div');grid.className='hex-grid';
 for(let r=0;r<7;r++){const row=document.createElement('div');row.className='hex-row';row.style.setProperty('--row',r);for(let c=0;c<7;c++){
  const v=game.board[r][c],cell=document.createElement('button');cell.className='hex-cell'+(v===1?' hex-blue':v===2?' hex-orange':'');cell.disabled=!active||!!v;cell.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v===1?'bleu':v===2?'orange':'vide'}`);
  if(path.some(p=>p[0]===r&&p[1]===c))cell.classList.add('winning-stone');if(lastAction?.row===r&&lastAction?.col===c)cell.classList.add('hex-last');cell.onclick=()=>humanAction({row:r,col:c});row.append(cell);
 }grid.append(row);}board.append(grid);
 if(game.hexState.swap_available&&!game.done){const swap=document.createElement('button');swap.className='hex-swap';swap.textContent='Échanger les couleurs · premier coup';swap.disabled=!active;swap.onclick=()=>humanAction({swap:true});board.append(swap);}
 $('game-result').hidden=!game.done;const color=game.hexState.colors[(game.winner??1)-1];$('game-result').textContent=$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez relié vos deux bords !':`Connexion gagnante · ${color===1?'Bleu':'Orange'}`;
}
function renderStrategyBoard(){
 const board=$('board'),legal=game.legal(),active=humanTurn()&&!game.done,same=(a,b)=>a&&b&&a[0]===b[0]&&a[1]===b[1];
 if(game.name==='gomoku')$('game-hint').textContent=gomokuHint();if(game.name==='draughts'&&game.draughtsState.forced_piece)selectedPiece=game.draughtsState.forced_piece;
 if(selectedPiece&&!legal.some(a=>same(a.from,selectedPiece)))selectedPiece=null;
 board.className='board-'+game.name;board.innerHTML='';
 game.board.forEach((row,r)=>row.forEach((v,c)=>{
  const button=document.createElement('button'),origin=legal.some(a=>same(a.from,[r,c])),dest=selectedPiece&&legal.some(a=>same(a.from,selectedPiece)&&same(a.to,[r,c])),owner=v?(v-1)%2+1:0;
  button.className='cell '+((r+c)%2?'dark-square':'light-square');button.disabled=!active||(!origin&&!dest);
  if(v){button.classList.add('piece'+owner);if(v>2){button.classList.add('crowned');button.textContent='D';}}
  button.classList.toggle('selected-piece',!!same(selectedPiece,[r,c]));if(dest)button.classList.add('legal-destination');else if(origin)button.classList.add('movable-piece');
  if(game.name==='draughts'&&game.draughtsState.pending_captures.some(p=>same(p,[r,c])))button.classList.add('captured-piece');
  if(lastAction?.to&&same(lastAction.to,[r,c]))button.classList.add('last');
  button.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v?(v>2?'dame':'pion')+' '+(owner===1?'blanc':'noir'):'vide'}${dest?', destination possible':''}`);
  button.setAttribute('aria-pressed',String(!!same(selectedPiece,[r,c])));
  button.onclick=()=>{if(!active)return;const action=selectedPiece&&legal.find(a=>same(a.from,selectedPiece)&&same(a.to,[r,c]));if(action){selectedPiece=null;humanAction(action);}else if(origin){selectedPiece=same(selectedPiece,[r,c])?null:[r,c];renderStrategyBoard();}};
  board.append(button);
 }));
 $('game-result').hidden=!game.done;$('game-result').textContent=game.winner===0?'Match nul':$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez gagné !':`Victoire · ${game.winner===1?'Blanc':'Noir'}`;
}
function renderExtraBoard(){
 const board=$('board'),legal=game.legal(),canPlay=humanTurn()&&!game.done;
 board.className='board-'+game.name;board.innerHTML='';
 if(game.name==='nim'){
  game.board.forEach((row,pile)=>{
   const count=row.reduce((s,v)=>s+v,0),section=document.createElement('section');section.className='nim-heap';
   const label=document.createElement('strong');label.textContent=`Tas ${pile+1} · ${count} allumette${count>1?'s':''}`;
   const tokens=document.createElement('div');tokens.className='nim-tokens';tokens.setAttribute('aria-hidden','true');
   for(let n=0;n<count;n++){const token=document.createElement('i');tokens.append(token);}
   if(!count)tokens.textContent='Tas vide';
   const actions=document.createElement('div');actions.className='nim-actions';actions.hidden=!canPlay;
   for(let take=1;take<=count;take++){const button=document.createElement('button');button.textContent=`−${take}`;button.setAttribute('aria-label',`Retirer ${take} du tas ${pile+1}`);button.disabled=!canPlay;button.onclick=()=>humanAction({pile,take});actions.append(button);}
   section.append(label,tokens,actions);board.append(section);
  });
 }else{
  game.board.forEach((row,r)=>row.forEach((v,c)=>{
   const button=document.createElement('button'),valid=legal.some(a=>a.row===r&&a.col===c);
   button.className='cell';button.disabled=!canPlay||!valid;
   if(game.name==='reversi'){
    if(v)button.classList.add('p'+v);else if(valid)button.classList.add('legal-move');
    button.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v===1?'noir':v===2?'blanc':valid?'coup possible':'vide'}`);
   }else{button.classList.toggle('light-on',!!v);button.textContent=v?'☼':'·';button.setAttribute('aria-label',`Lampe ${r+1}, ${c+1} : ${v?'allumée':'éteinte'}`);button.setAttribute('aria-pressed',String(!!v));}
   if(lastAction?.row===r&&lastAction?.col===c)button.classList.add('last');
   button.onclick=()=>humanAction({row:r,col:c});board.append(button);
  }));
  if(game.name==='reversi'&&canPlay&&legal.some(a=>a.pass)){const pass=document.createElement('button');pass.className='reversi-pass';pass.textContent='Aucun coup possible · Passer';pass.disabled=!canPlay;pass.onclick=()=>humanAction({pass:true});board.append(pass);}
 }
 $('game-result').hidden=!game.done;
 const labels=game.name==='go'?['Noir','Blanc']:game.name==='gomoku'?game.gomokuState.colors.map((c,i)=>c===1?'Noir':c===2?'Blanc':`Joueur ${i+1} · ouverture`):game.name==='hex'?game.hexState.colors.map(c=>c===1?'Bleu · haut / bas':'Orange · gauche / droite'):['draughts','breakthrough'].includes(game.name)?['Blanc','Noir']:game.name==='reversi'?['Noir','Blanc']:['Joueur 1','Joueur 2'];
 $('game-result').textContent=!game.multiplayer?'Toutes les lampes sont éteintes !':game.winner===0?'Match nul':$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez gagné !':`Victoire · ${labels[game.winner-1]}`;
}
function renderGames(){const container=$('games');container.innerHTML='';for(const [name,title] of Object.entries(NAMES)){const b=document.createElement('button');b.className='game-card'+(name===game.name?' selected':'');b.setAttribute('aria-pressed',name===game.name?'true':'false');b.disabled=training;b.innerHTML=`<span class="game-icon">${icons[name]}</span><strong>${title}</strong><small>${AGENTS[name].codename} · V${AGENTS[name].version}</small>`;b.onclick=()=>selectGame(name);container.append(b);}}
function renderBoard(){if(game.name==='go'){renderGoBoard(game,humanTurn(),humanAction,lastAction);return;}if(['sudoku','sliding_puzzle'].includes(game.name)){renderPuzzleBoard(game,humanTurn(),humanAction);return;}if(game.name==='gomoku'){renderGomokuBoard();return;}if(game.name==='hex'){renderHexBoard();return;}if(['draughts','breakthrough'].includes(game.name)){renderStrategyBoard();return;}if(['reversi','nim','lightsout'].includes(game.name)){renderExtraBoard();return;}const b=$('board');b.className='board-'+game.name;b.innerHTML='';game.board.forEach((row,r)=>row.forEach((v,c)=>{const cell=document.createElement('button');cell.className='cell';cell.disabled=!humanTurn()||game.done||game.name==='2048'||!game.legal().some(a=>game.name==='connect4'?a.column===c:a.row===r&&a.col===c);cell.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v===-1?'caché':v}`);if(!cell.disabled)cell.classList.add('playable');if(game.multiplayer){cell.textContent=game.name==='tictactoe'?(v===1?'×':v===2?'○':''):'';if(v)cell.classList.add('p'+v);}else if(game.name==='2048'){cell.textContent=v||'';if(v){const colors=['#e4edda','#d9e9c5','#c7e8a1','#a6d47c','#75ac58','#4f8842','#306834','#254e2d'];const n=Math.max(0,Math.log2(v)-1);cell.style.background=colors[Math.min(n,colors.length-1)];if(n>3)cell.style.color='#f4f9e7';}}else if(game.name==='minesweeper'){cell.textContent=v===-1?'':v===-2?'✳':v||'';if(v>=0)cell.classList.add('revealed');if(v===-2)cell.classList.add('bomb');}else{cell.textContent=v||'';if(game.name==='sudoku'&&game.givens[r][c])cell.classList.add('given');if(game.name==='sliding_puzzle'&&!v)cell.classList.add('blank');}if(lastAction&&((lastAction.row===r&&lastAction.col===c)||(game.name==='connect4'&&lastAction.column===c&&v&&(!r||!game.board[r-1][c]))))cell.classList.add('last');cell.onclick=()=>clickCell(r,c);b.append(cell);}));
 $('game-result').hidden=!game.done;$('game-result').textContent=game.multiplayer?(game.winner===0?'Match nul':game.winner===+$('human-player').value&&$('mode').value==='human'?'Vous avez gagné !':`Victoire du joueur ${game.winner===1?'X / rouge':'O / jaune'}`):game.winner===1?'Objectif atteint !':'Partie terminée';}
function renderControls(){
 const policy=gameUiPolicy({game:game.name,mode:$('mode').value,planning:$('planning').checked,level:+$('level').value,levelTwo:+$('level-two').value});
 const {multi,manualSolo,duel}=policy,human=humanTurn(),busy=pending.size>0;
 $('ai-controls').hidden=!policy.showAi;
 $('level-two-options').hidden=!duel;
 $('level-title').textContent=policy.levelTitle;
 const probabilityPuzzle=['sudoku','sliding_puzzle'].includes(game.name)&&$('planning').checked&&+$('level').value>0&&+$('level').value<10;
 $('level-note').textContent=probabilityPuzzle?`${50+5*+$('level').value} % de meilleurs coups évalués à chaque décision ; les autres coups créent la difficulté.`:'Le niveau classe les coups évalués. Des niveaux différents peuvent choisir des coups de même qualité.';

 const labels=game.name==='gomoku'?game.gomokuState.colors.map((c,i)=>c===1?'Noir':c===2?'Blanc':`Joueur ${i+1} · ouverture`):game.name==='hex'?game.hexState.colors.map(c=>c===1?'Bleu · haut / bas':'Orange · gauche / droite'):['draughts','breakthrough'].includes(game.name)?['Blanc','Noir']:['go','reversi'].includes(game.name)?['Noir','Blanc']:game.name==='nim'?['Joueur 1','Joueur 2']:game.name==='connect4'?['Rouge · premier','Jaune · second']:['X · premier','O · second'];
 [...$('human-player').options].forEach((o,i)=>o.textContent=labels[i]);
 $('mode').options[0].textContent=multi?'IA contre IA':'IA autonome';
 $('mode').options[1].disabled=false;$('mode').options[1].textContent=policy.humanLabel;
 $('mode').disabled=training;$('human-player').disabled=training;
 $('human-options').hidden=!multi||$('mode').value!=='human';
 $('style-options').hidden=!policy.showStyles;
 $('style-note').hidden=manualSolo;$('style-note').textContent=policy.styleHint;
 const choices=JSON.stringify(policy.styles);
 if($('style').dataset.choices!==choices){const previous=$('style').value;$('style').replaceChildren(...policy.styles.map(([value,label])=>{const option=document.createElement('option');option.value=value;option.textContent=label;return option;}));if(policy.styles.some(([value])=>value===previous))$('style').value=previous;$('style').dataset.choices=choices;}
 if(!policy.styles.length){const option=document.createElement('option');option.value='balanced';option.textContent='Équilibré';$('style').replaceChildren(option);}
 $('play').hidden=manualSolo;$('step').hidden=$('mode').value==='human';
 $('play').querySelector('span').textContent=running?'Pause':$('mode').value==='human'?'Faire jouer l’IA':multi?'Observer les IA':'Observer l’IA';
 $('play').firstChild.textContent=running?'Ⅱ ':'▶ ';
 $('play').disabled=!current()||game.done||training||(!running&&(human||busy));
 $('play').title=human?'À vous de jouer sur le plateau.':busy?'Calcul du coup en cours.':'';
 $('step').disabled=game.done||!current()||human||running||busy||training;
 $('new').disabled=training;$('new').title=training?'Arrêtez l’entraînement du navigateur pour changer la partie.':'Nouvelle partie';
 const label=labels[game.player-1];
 $('turn').textContent=game.done?'Partie terminée':human?'À vous de jouer':multi?`Au tour du réseau ${label}`:'Le réseau joue en solo';
 const bound=game.name==='sliding_puzzle'?game.board.length===3?slidingDistance(game.board):game.distance():game.name==='sudoku'?game.board.flat().filter(v=>!v).length:null;
 $('move-counter').textContent=`${game.moves} coup${game.moves>1?'s':''}${bound!==null?' · '+bound+' restant'+(bound>1?'s':''):''}`;
 $('elapsed-counter').textContent=startedAt===null?'0,00 s':`${(((finishedAt??performance.now())-startedAt)/1000).toFixed(2).replace('.',',')} s`;
 $('game-title').textContent=NAMES[game.name];$('game-category').textContent=multi?'DUEL · 2 JOUEURS':'RÉSOLUTION · 1 JOUEUR';$('train-game').textContent=NAMES[game.name];
 $('game-hint').textContent=game.name==='2048'?(human?'Utilisez les flèches du clavier ou les boutons de direction. Les coups sans effet sont désactivés.':'Fusionnez les tuiles. Garry continue après 2048 pour augmenter le score.'):game.name==='minesweeper'?(human?'Cliquez sur une case cachée. Le premier clic est protégé ; les nombres indiquent les mines voisines.':'Priorité aux cases sûres et aux grandes ouvertures. Les mines restent cachées.'):
 human?'Cliquez sur une case libre ou une colonne pour jouer.':'Priorité à la victoire, puis au moins de coups possible dans la recherche.';
 if(game.name==='connect4'&&lastDecision?.depth!==undefined)$('game-hint').textContent=lastDecision.forced_win?'Victoire forcée trouvée dans la recherche.':`Recherche : ${lastDecision.depth} demi-coups analysés · cible ${lastDecision.target_depth??20}.`;
 if(extraHints[game.name])$('game-hint').textContent=extraHints[game.name];
 if(game.name==='gomoku')$('game-hint').textContent=gomokuHint();
 if(game.name==='draughts'&&game.draughtsState.forced_piece)$('game-hint').textContent='Rafle en cours : continuez avec le pion sélectionné. Les pièces prises seront retirées à la fin.';
 renderPuzzleControls(game,human,training,lastDecision);renderGoControls(game);
 $('go-size').disabled=training;$('go-komi').disabled=training;
 if(!$('planning').checked&&!manualSolo)$('game-hint').textContent+=' Réseau seul : le niveau utilise ses scores appris ; la recherche est désactivée.';
 if(manualSolo&&game.done)$('turn').textContent=game.winner===1?'Objectif atteint':'Partie terminée';
}
function renderNetwork(){const m=current();if(!m)return;const parameters=m.w1.length+m.w2.length+m.b1.length+m.b2.length+m.core.w.length+m.core.b.length+(m.positionHead?.weights.length??0);$('architecture').textContent=`${m.input} → ${m.hidden} ⇄ ${m.hidden} → ${m.output}`;$('parameter-count').textContent=`${fmt(parameters)} paramètres`;$('metric-steps').textContent=fmt(m.steps);$('shared-steps').textContent=fmt(m.core.steps);$('model-status').textContent=`${AGENTS[game.name].codename} v${AGENTS[game.name].version} · Poids appris · ${fmt(m.steps)} exemples. Un seul modèle pour les quatorze jeux.`;$('metric-time').innerHTML=lastDecision?`${lastDecision.time_ms.toFixed(2)}<small> ms</small>`:'—<small> ms</small>';$('metric-confidence').textContent=lastDecision?.confidence!=null?`${(lastDecision.confidence*100).toFixed(1)} %`:lastDecision?.agent==='neural+planner'?'Recherche':'—';$('metric-score').textContent=fmt(game.score);$('score-caption').textContent=game.name==='2048'?'Somme des fusions':game.name==='sudoku'?'Cases remplies par l’agent':game.name==='minesweeper'?'Cases sûres découvertes':game.name==='sliding_puzzle'?'Opposé de la distance de Manhattan':game.name==='reversi'?'Pions noirs moins pions blancs':game.name==='nim'?'Allumettes restantes':game.name==='lightsout'?'Lampes éteintes sur 25':game.name==='go'?'Écart final Noir − Blanc, komi compris':['draughts','breakthrough'].includes(game.name)?'Avantage matériel des blancs':'Une victoire vaut un point';
 const canvas=$('network-viz'),ctx=canvas.getContext('2d'),{h}=m.forward(game.obs());ctx.clearRect(0,0,310,100);const columns=[4,8,8,4],xs=[25,108,200,284];for(let k=0;k<3;k++)for(let a=0;a<columns[k];a++)for(let b=0;b<columns[k+1];b++){ctx.strokeStyle=`rgba(94,135,66,${.04+Math.abs(h[(a*8+b)%h.length])*.18})`;ctx.beginPath();ctx.moveTo(xs[k],15+a*70/(columns[k]-1));ctx.lineTo(xs[k+1],15+b*70/(columns[k+1]-1));ctx.stroke();}columns.forEach((n,k)=>{for(let i=0;i<n;i++){const v=Math.abs(h[(k*8+i)%h.length]);ctx.beginPath();ctx.arc(xs[k],15+i*70/(n-1),3+v*2,0,Math.PI*2);ctx.fillStyle=`rgba(78,123,47,${.2+.8*v})`;ctx.fill();}});}
function render(){renderGames();renderControls();renderBoard();renderManualActions();renderNetwork();}
function renderEvents(){$('event-count').textContent=`${trace.length} événements`;const container=$('events');container.innerHTML='';for(const e of trace.slice(-6).reverse()){const row=document.createElement('div');row.className='event-row';const n=document.createElement('span');n.textContent=String(e.seq).padStart(3,'0');const a=document.createElement('span');a.textContent=e.action?`${e.info?.agent==='human'?'Vous':'Réseau'} → ${JSON.stringify(e.action)}`:({created:'Nouvelle session',started:'Lecture autonome',stopped:'Lecture arrêtée'}[e.type]||e.type);const t=document.createElement('span');t.textContent=e.info?.time_ms!==undefined?`${e.info.time_ms.toFixed(2)} ms`:e.type==='created'?NAMES[e.observation.game]:'';row.append(n,a,t);container.append(row);}}
function drawLoss(){const c=$('loss-chart'),ctx=c.getContext('2d'),w=c.width,h=c.height;ctx.clearRect(0,0,w,h);ctx.strokeStyle='#e3e9d8';ctx.lineWidth=1;ctx.font='11px monospace';ctx.fillStyle='#98a98a';const max=Math.max(1,...lossCurve)*1.12;for(let i=0;i<5;i++){const y=25+i*(h-55)/4;ctx.beginPath();ctx.moveTo(45,y);ctx.lineTo(w-20,y);ctx.stroke();ctx.fillText((max*(1-i/4)).toFixed(1),8,y+4);}if(!lossCurve.length){ctx.fillText('La courbe apparaîtra pendant l’entraînement.',70,h/2);return;}ctx.strokeStyle='#6f9a47';ctx.lineWidth=2.5;ctx.beginPath();lossCurve.forEach((v,i)=>{const x=45+i*(w-65)/Math.max(1,lossCurve.length-1),y=h-30-v/max*(h-55);if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);});ctx.stroke();}
async function beginTraining(){if(training)return;if(!current())return toast('Les modèles se chargent.');const episodes=+$('episodes').value,seed=+$('seed').value;if(!Number.isInteger(episodes)||episodes<1||episodes>10000||!Number.isInteger(seed))return toast('Choisissez 1 à 10 000 épisodes et une graine entière.');pause();training=true;trainingGame=game.name;lossCurve=[];drawLoss();$('train-start').disabled=true;$('train-stop').disabled=false;$('model-import').disabled=true;$('model-reset').disabled=true;$('training-status').textContent='Apprentissage en cours · répétition inter-jeux activée.';render();worker=new Worker('./trainer.js',{type:'module'});worker.onmessage=async e=>{const d=e.data;if(d.type==='progress'){lossCurve=d.curve;$('train-episodes').textContent=`${d.episode} / ${episodes}`;$('train-examples').textContent=fmt(d.examples);$('train-loss').textContent=d.loss.toFixed(3);$('loss-label').textContent=`Dernier épisode : ${d.episode_loss.toFixed(3)}`;$('training-status').textContent=`${d.episode}/${episodes} épisodes · ${d.rehearsals} rappels · ${d.repertoire_unique??0} épreuves variées. Poids appliqués à l’arrêt.`;drawLoss();}else if(d.type==='finished'){useGarry(d.model);finishTraining();try{await persistModels();}catch(error){errorMessage(error);}$('training-status').textContent=`${d.cancelled?'Arrêté':'Terminé'} · ${fmt(d.examples)} exemples, ${fmt(d.rehearsals)} rappels, ${fmt(d.repertoire_unique??0)} épreuves variées. Garry a été mis à jour.`;lastDecision=null;renderNetwork();toast('Garry a été mis à jour pour les quatorze jeux.');}else if(d.type==='error'){finishTraining();$('training-status').textContent=d.message;toast(d.message);}};worker.onerror=e=>{finishTraining();toast('Le worker a rencontré une erreur : '+e.message);};worker.postMessage({op:'train',game:trainingGame,model:general.export(),episodes,seed,lr:+$('learning-rate').value});}
function finishTraining(){training=false;if(worker){worker.terminate();worker=null;}$('train-start').disabled=false;$('train-stop').disabled=true;$('model-import').disabled=false;$('model-reset').disabled=false;render();}
function preset(){const op=$('request-preset').value;$('json-input').value=JSON.stringify({protocol:'logic-arena.v1',id:'demo-1',op,...(op==='catalog'?{}:{session_id:sessionId}),...(['suggest','play'].includes(op)?{agent:{type:'neural',level:+$('level').value,style:$('style').value}}:{})},null,2);}
function request(req){let id=req?.id??null;try{if(!req||Array.isArray(req)||typeof req!=='object')throw Error('La requête doit être un objet');if(req.protocol&&req.protocol!=='logic-arena.v1')throw Error('Version inconnue');if(!['catalog','create','observe','suggest','play','step','run','stop'].includes(req.op))throw Error('Opération inconnue');let result;if(req.op==='catalog')result={protocol:'logic-arena.v1',games:Object.keys(NAMES).map(id=>({id,players:['tictactoe','connect4','reversi','nim','draughts','breakthrough','hex','gomoku','go'].includes(id)?2:1,ai:agentIdentity(id)})),agent_version:AGENT_VERSION,model:{name:'garry',version:AGENT_VERSION,format:'garry-mlp-v3',architecture:[4872,48,48,4259],position_head:{game:'connect4',features:32,outputs:1},files:1},styles:STYLES,default_level:10,objective:'win_then_fewest_moves',default_interval_ms:0,levels:Array.from({length:11},(_,level)=>({level,quality_quantile:level/10,planning_nodes:LIMITS[9],planning_time_ms:TIMES[9],connect4_nodes:CONNECT_LIMITS[9],connect4_time_ms:CONNECT_TIMES[9],connect4_target_depth:20})),shared_module:{id:current()?.core.id,hidden:48,training_steps:current()?.core.steps}};else if(req.op==='create'){if(training)throw Error('Entraînement en cours');newGame(req.game??'tictactoe',req.seed??0,req.options??{});result=snapshot();}else{if(req.session_id!==sessionId)throw Error('Session inconnue');if(req.expected_revision!==undefined&&req.expected_revision!==revision)throw Error('Révision obsolète');if(running&&['step','play'].includes(req.op))throw Error('Arrêtez la lecture avant une action externe');if(req.op==='observe')result=snapshot();if(req.op==='suggest'){const d=decide(req.agent);result={revision,...d};}if(req.op==='step')result=transition(req.action,{agent:'external'});if(req.op==='play'){const d=decide(req.agent);result=transition(d.action,d.info);}if(req.op==='run'){if(!running)start();result=snapshot();}if(req.op==='stop'){pause();result=snapshot();}}return {protocol:'logic-arena.v1',id,ok:true,result};}catch(error){return {protocol:'logic-arena.v1',id,ok:false,error:{code:error.name==='AbortError'?'cancelled':'invalid_request',message:error.message}};}}
async function requestAsync(req){
 if(!['suggest','play'].includes(req?.op))return request(req);
 const id=req.id??null;
 try{
  if(req.protocol&&req.protocol!=='logic-arena.v1')throw Error('Version inconnue');
  if(req.session_id!==sessionId)throw Error('Session inconnue');
  if(req.expected_revision!==undefined&&req.expected_revision!==revision)throw Error('Révision obsolète');
  if(req.op==='play'&&running)throw Error('Arrêtez la lecture avant une action externe');
  const rev=revision,version=generation;
  if(req.op==='play')clockStart();
  const decision=await decideAsync(req.agent);
  if(rev!==revision||version!==generation)throw Error('Session modifiée pendant le calcul ; relire l’observation');
  const result=req.op==='play'?transition(decision.action,decision.info):{revision,...decision};
  return {protocol:'logic-arena.v1',id,ok:true,result};
 }catch(error){return {protocol:'logic-arena.v1',id,ok:false,error:{code:error.name==='AbortError'?'cancelled':'invalid_request',message:error.message}};}
}
window.logicArena={request,requestAsync,subscribe(fn){listeners.add(fn);return()=>listeners.delete(fn);},getSnapshot:snapshot};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));$('open-training').onclick=()=>setTab('training');$('about-link').onclick=e=>{e.preventDefault();$('about').showModal();};$('transfer-info').onclick=()=>$('about').showModal();$('close-about').onclick=()=>$('about').close();$('play').onclick=start;$('step').onclick=()=>playOne().catch(errorMessage);$('new').onclick=()=>{try{$('seed').value=+$('seed').value+1;newGame();}catch(error){errorMessage(error);}};$('mode').onchange=()=>{generation++;clearTimeout(timer);newGame();};$('human-player').onchange=()=>newGame();$('level').oninput=()=>{$('level-label').innerHTML=`${$('level').value}<span> / 10</span>`;renderControls();};$('planning').onchange=()=>renderControls();$('speed').oninput=()=>{$('speed-label').textContent=+$('speed').value===0?'Express · aucune pause':`${$('speed').value} ms / coup`;renderControls();};$('export-replay').onclick=()=>download(`logic-lab-${game.name}.jsonl`,trace.map(e=>JSON.stringify(e)).join('\n')+'\n','application/x-ndjson');$('train-start').onclick=beginTraining;$('train-stop').onclick=()=>{if(worker){worker.postMessage({op:'stop'});$('train-stop').disabled=true;$('training-status').textContent='Arrêt en cours, conservation des poids appris…';}};$('model-export').onclick=()=>{if(!current())return;download(`garry-${AGENT_VERSION}.json`,JSON.stringify(general.export()));};$('model-import').onclick=()=>$('model-file').click();$('model-file').onchange=async()=>{try{const file=$('model-file').files[0];if(!file)return;if(file.size>15000000)throw Error('Fichier trop volumineux (15 Mo maximum)');const data=JSON.parse(await file.text());useGarry(data.format==='logic-arena-suite-v1'?GarryModel.fuse(data.models):data,data.format==='logic-arena-suite-v1'?data.models.map(m=>m.game):data.games);pause();lastDecision=null;await persistModels();renderNetwork();toast('Garry importé pour les quatorze jeux.');}catch(error){errorMessage(error);}finally{$('model-file').value='';}};$('model-reset').onclick=async()=>{try{pause();const response=await fetch('models/garry.json');if(!response.ok)throw Error('Chargement de Garry impossible');useGarry(await response.json());lastDecision=null;await persistModels();renderNetwork();toast('Derniers poids fournis par le serveur restaurés.');}catch(error){errorMessage(error);}};$('request-preset').onchange=preset;$('json-send').onclick=async()=>{$('json-send').disabled=true;$('json-output').textContent='Calcul dans le worker…';try{const response=await requestAsync(JSON.parse($('json-input').value));$('json-output').textContent=JSON.stringify(response,null,2);}catch(error){$('json-output').textContent=JSON.stringify({ok:false,error:{message:error.message}},null,2);}finally{$('json-send').disabled=false;}};$('copy-output').onclick=async()=>{try{await navigator.clipboard.writeText($('json-output').textContent);toast('Réponse copiée.');}catch{toast('Sélectionnez le texte pour le copier.');}};
async function initialize(){render();preset();drawLoss();try{db=await openDB();const stored=await storedModel('garry');let shipped=null;try{const response=await fetch('models/garry.json');if(response.ok){shipped=await response.json();packagedModel=new GarryModel(shipped);}}catch{}if(stored)try{useGarry(stored);if(stored.format==='garry-mlp-v1'&&shipped?.position_head)general.positionHead=structuredClone(shipped.position_head);if(stored.version!==AGENT_VERSION&&shipped?.search_memory&&!general.searchMemory.entries.length){useGarry({...general.export(),search_memory:shipped.search_memory});await persistModels();}if(stored.version!==AGENT_VERSION||stored.input!==general.input)await persistModels();}catch{}if(!general){if(!shipped)throw Error('Garry indisponible');useGarry(shipped);}emit('created');render();}catch(error){$('model-status').textContent=error.message;toast(error.message);}}
initialize();

for(const id of ['sudoku-difficulty','sliding-size','sliding-difficulty','go-size','go-komi'])$(id).onchange=()=>{try{newGame();}catch(error){errorMessage(error);}};

$('level-two').oninput=()=>{$('level-two-label').innerHTML=`${$('level-two').value}<span> / 10</span>`;renderControls();};
window.addEventListener('garry-load-server-model',async()=>{try{if(training)throw Error('Arrêtez l’entraînement du navigateur avant de charger les poids');pause();const response=await fetch('models/garry.json',{cache:'no-store'});useGarry(await response.json());await persistModels();lastDecision=null;render();toast('Derniers poids du serveur chargés.');}catch(e){errorMessage(e);}});

function renderManualActions(){
 const el=$('manual-actions');el.hidden=game.name!=='2048'||!humanTurn()||game.done;el.replaceChildren();if(el.hidden)return;
 const legal=game.legal();for(const [direction,label]of [['up','↑ Haut'],['left','← Gauche'],['down','↓ Bas'],['right','→ Droite']]){
  const button=document.createElement('button');button.className='button secondary';button.textContent=label;button.setAttribute('aria-label',`Déplacer vers ${label.slice(2).toLowerCase()}`);button.disabled=!legal.some(a=>a.direction===direction);button.onclick=()=>humanAction({direction});el.append(button);
 }
}
window.addEventListener('keydown',event=>{
 if(game.name!=='2048'||!humanTurn()||game.done||event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||event.target.closest?.('input,select,textarea,[contenteditable="true"]')||document.querySelector('dialog[open]'))return;
 const direction={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right'}[event.key];if(!direction)return;event.preventDefault();if(game.legal().some(a=>a.direction===direction))humanAction({direction});
});

// Barre « qui joue contre qui » de l'arène : choix du joueur de chaque camp (moi, Garry avec son niveau, Zéro, Optimus, moteur, hasard).
// Elle pilote les contrôles existants (#mode, #human-player, #level, #level-two) et arena-players.js ; aucune autre logique de jeu.
import {NAMES} from './engine.js';
import {SIDES,CATALOG,forGame,loadRemote} from './arena-players.js';

const $=id=>document.getElementById(id);
const byTitle=Object.fromEntries(Object.entries(NAMES).map(([k,v])=>[v,k]));
const who={1:'ai:garry',2:'ai:garry'};
const fire=(el,type)=>el.dispatchEvent(new Event(type,{bubbles:true}));
const gameName=()=>byTitle[document.querySelector('.game-card.selected strong')?.textContent]||'tictactoe';
const isDuel=()=>/DUEL/.test($('game-category').textContent);
const label=id=>CATALOG.find(p=>p.id===id)?.label||id;

function options(n){
 const list=forGame(gameName());
 const o=[];
 o.push(['human','Moi']);
 for(const p of list)o.push(['ai:'+p.id,p.label]);
 return o;
}
const badge=document.createElement('div');badge.id='whoplays';badge.className='whoplays';
document.querySelector('.play-panel .board-stage')?.before(badge);
const who_label=n=>{const w=who[n];if(w==='human')return 'Vous';const id=w.replace('ai:','');return label(id)+(id==='garry'?` niv. ${$('pc'+n+'-range').value}`:'');};
function render(){
 const g=gameName(),duel=isDuel();
 $('pc2').hidden=!duel;document.querySelector('#match .vs').hidden=!duel;
 $('match-sub').textContent=duel?'CHOISISSEZ LES DEUX CAMPS':'QUI RÉSOUT ?';
 document.querySelector('#pc1 .pc-role').textContent=duel?'Joueur 1':'Joueur';
 document.querySelector('#pc1 .pc-first').hidden=!duel;
 for(const n of duel?[1,2]:[1]){
  const sel=$('psel'+n),opts=options(n);
  if(!opts.some(([v])=>v===who[n]))who[n]=opts[1]?.[0]||'human';
  sel.innerHTML=opts.map(([v,l])=>`<option value="${v}"${v===who[n]?' selected':''}>${l}</option>`).join('');
  const id=who[n].replace('ai:','');
  const garry=who[n]==='ai:garry';
  $('pc'+n+'-level').hidden=!garry;
  $('phint'+n).textContent=who[n]==='human'?'Vous jouez ce camp.':CATALOG.find(p=>p.id===id)?.hint||'';
  document.getElementById('pc'+n).classList.toggle('me',who[n]==='human');
 }
 badge.textContent=duel?`Joueur 1 · ${who_label(1)}   contre   Joueur 2 · ${who_label(2)}`:`Joueur · ${who_label(1)}`;
}
function apply(){
 const duel=isDuel();
 if(duel&&who[1]==='human'&&who[2]==='human')who[2]='ai:garry';
 const mode=$('mode'),hp=$('human-player');
 const human=duel?(who[1]==='human'?1:who[2]==='human'?2:0):(who[1]==='human'?1:0);
 const wantMode=human?'human':'watch',modeChanged=mode.value!==wantMode,hpChanged=duel&&human&&hp.value!==String(human);
 mode.value=wantMode;
 if(duel&&human)hp.value=String(human);
 for(const n of [1,2]){const w=who[n];SIDES[n]=w.startsWith('ai:')?w.slice(3):'garry';}
 // niveau de Garry : en duel IA/IA, #level = camp 1 et #level-two = camp 2 ; contre un humain, #level = le camp IA
 const aiSide=human===1?2:1;
 const set=(real,range)=>{const r=$(real);if(r.value!==range.value){r.value=range.value;fire(r,'input');}};
 if(human)set('level',$('pc'+aiSide+'-range'));else{set('level',$('pc1-range'));if(duel)set('level-two',$('pc2-range'));}
 if(modeChanged)fire(mode,'change');if(hpChanged)fire(hp,'change');
 render();
}
for(const n of [1,2]){
 $('psel'+n).addEventListener('change',e=>{who[n]=e.target.value;apply();});
 const r=$('pc'+n+'-range'),v=$('pc'+n+'-val');
 r.addEventListener('input',()=>{v.textContent=r.value;apply();});
}
let busy=false;
const redo=()=>{if(busy)return;busy=true;try{render();apply();}finally{setTimeout(()=>{busy=false;},120);}};
let lastTitle='';
new MutationObserver(()=>{const t=$('game-title').textContent;if(t!==lastTitle){lastTitle=t;redo();}}).observe($('game-title'),{childList:true,characterData:true,subtree:true});
new MutationObserver(render).observe($('game-category'),{childList:true,characterData:true,subtree:true});
loadRemote().then(redo);
setTimeout(redo,300);

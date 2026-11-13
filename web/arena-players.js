// Joueurs de l'arène. Garry (niveaux 0 à 10) reste géré par app.js ; ici : les autres modèles et moteurs.
//   engine  : moteurs à la main Gomoku et Hex (navigateur, aucun entraînement)
//   random  : hasard
//   zero    : Garry Zéro, Puissance 4 (serveur : /api/player, MCTS + réseau)
//   optimus : Garry Optimus, réseau seul (serveur : /api/player)
import {gomokuValues} from './gomoku-engine.js';
import {hexValues} from './hex-engine.js';

export const SIDES={1:'garry',2:'garry'};
export const CATALOG=[
 {id:'garry',label:'Garry 0.6.0',games:'*',hint:'14 jeux · niveaux 0 à 10'},
 {id:'optimus',label:'Garry Optimus',games:['tictactoe','connect4','hex','gomoku','2048'],server:true,hint:'réseau seul, sans recherche'},
 {id:'zero',label:'Garry Zéro',games:['connect4'],server:true,hint:'auto-apprentissage · recherche 200 simulations'},
 {id:'engine',label:'Moteur à la main',games:['gomoku','hex'],hint:'tables de motifs / ponts, sans entraînement'},
 {id:'random',label:'Hasard',games:'*',hint:'coup légal au hasard'}];
let remote={},loaded=false;
export async function loadRemote(){if(loaded)return remote;loaded=true;try{const r=await fetch('/api/players',{cache:'no-store'});const j=await r.json();remote=j.players||{};}catch{remote={};}return remote;}
export const forGame=name=>CATALOG.filter(p=>(p.games==='*'||p.games.includes(name))&&(!p.server||remote[p.id]?.games.includes(name)));
const pick=a=>a[Math.floor(Math.random()*a.length)];
function engineChoose(o,legal){
 const began=performance.now(),budget={nodes:0,limit:100000,tick(){if(this.nodes++>=this.limit||performance.now()-began>=300)throw Error('budget');}};
 const r=o.game==='gomoku'?gomokuValues(o,legal,budget):hexValues(o,legal,budget);
 const best=r.action_values.reduce((b,v)=>v.quality[0]>b.quality[0]?v:b,r.action_values[0]);
 return {action:best.action,info:{...r.info,agent:'engine'}};
}
// Renvoie une promesse {action,info} si le camp `side` n'est pas Garry, sinon null (app.js décide alors lui-même).
export function altDecision(game,side){
 const id=SIDES[side]||'garry';if(id==='garry')return null;
 const o=game.obs(),legal=game.legal(),t0=performance.now();
 if(id==='random')return Promise.resolve({action:pick(legal),info:{agent:'random',ms:0}});
 if(id==='engine')return Promise.resolve(engineChoose(o,legal));
 return fetch('/api/player',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({player:id,observation:o,legal})})
  .then(r=>r.json()).then(j=>{if(!j.ok)throw Error(j.error||'Joueur indisponible');return {action:j.action,info:{agent:id,ms:Math.round(performance.now()-t0)}};});
}

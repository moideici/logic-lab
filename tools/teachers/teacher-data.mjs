// Auto-parties du moteur à la main (Gomoku ou Hex) avec bruit : une ligne JSON par position, étiquetée après la partie.
// Sortie : {game, obs, moves:[actions], scores:[qualités], z} où z = résultat (+1 gagne, -1 perd, 0 nul) du joueur au trait ; scores = les K meilleurs coups.
// usage : node tools/teachers/teacher-data.mjs --game gomoku|hex --games 20 --seed 1 --ms 60 --noise 0.15 --top 16
import {newGomoku,legalGomoku,stepGomoku} from '../../web/gomoku-games.js';
import {gomokuValues as gomokuEngine} from '../../web/gomoku-engine.js';
import {gomokuValues as gomokuRef} from '../../web/gomoku-planner.js';
import {newHex,legalHex,stepHex} from '../../web/hex-games.js';
import {hexValues} from '../../web/hex-engine.js';
const args=Object.fromEntries(process.argv.slice(2).reduce((a,x,i,arr)=>x.startsWith('--')?[...a,[x.slice(2),arr[i+1]]]:a,[]));
const game=args.game,games=+(args.games??10),seed=+(args.seed??1),ms=+(args.ms??60),noise=+(args.noise??.15),top=+(args.top??16);
let s=(seed*2654435761)>>>0;const R=()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296;};
const budget=()=>{const t0=performance.now();return {nodes:0,tick(){if(this.nodes++>=100000||performance.now()-t0>=ms)throw Error('budget');}};};
const clone=x=>structuredClone(x);
function ranked(values){return values.slice().sort((a,b)=>b.quality[0]-a.quality[0]);}
function choose(values){const r=ranked(values);if(r.length>1&&R()<noise)return r[1+Math.floor(R()*Math.min(3,r.length-1))].action;return r[0].action;}
function playGomoku(){
 const g=newGomoku(),log=[];let player=1,done=false,winner=null,moves=0;
 while(!done&&moves<300){
  const legal=legalGomoku(g.board,g.state),ph=g.state.phase;let action;
  if(ph==='opening_three'||ph==='opening_two'){const cells=legal.filter(a=>Math.abs(a.row-7)<=2&&Math.abs(a.col-7)<=2);action=cells[Math.floor(R()*cells.length)];}
  else{
   const o={board:g.board.map(r=>r.slice()),current_player:player,gomoku_state:clone(g.state),done:false};
   if(ph==='choose_or_extend'||ph==='choose_color'){action=ranked(gomokuRef(o,legal.filter(a=>a.choose),budget()).action_values)[0].action;}
   else{
    const values=gomokuEngine(o,legal,budget()).action_values,r=ranked(values);action=choose(values);
    log.push({obs:{game:'gomoku',...o},player,moves:r.slice(0,top).map(v=>v.action),scores:r.slice(0,top).map(v=>v.quality[0])});}}
  const st=stepGomoku(g.board,player,action,g.state);player=st.player;done=st.done;winner=st.winner;moves++;}
 return {log,winner:done?winner:0};
}
function playHex(){
 const g=newHex(),log=[];let player=1,done=false,winner=null,moves=0;
 while(!done&&moves<80){
  const legal=legalHex(g.board,g.state),o={board:g.board.map(r=>r.slice()),current_player:player,hex_state:clone(g.state),done:false};
  const values=hexValues(o,legal,budget()).action_values,r=ranked(values);let action=choose(values);
  if(moves===0&&R()<.5)action=legal[Math.floor(R()*legal.length)];
  log.push({obs:{game:'hex',...o},player,moves:r.slice(0,top).map(v=>v.action),scores:r.slice(0,top).map(v=>v.quality[0])});
  const st=stepHex(g.board,player,action,g.state);player=st.player;done=st.done;winner=st.winner;moves++;}
 return {log,winner:done?winner:0,colors:null};
}
for(let i=0;i<games;i++){
 const res=game==='gomoku'?playGomoku():playHex();
 for(const e of res.log){
  // le joueur 1 ou 2 est un siège : le vainqueur est un siège également (Hex : 'winner' = joueur)
  const z=res.winner===0||res.winner===null?0:res.winner===e.player?1:-1;
  console.log(JSON.stringify({game,obs:e.obs,moves:e.moves,scores:e.scores,z}));}
}

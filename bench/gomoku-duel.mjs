// Duels Gomoku : joueur « A » (web/gomoku-engine.js) contre « B » (web/gomoku-planner.js, version de référence).
// usage : node bench/gomoku-duel.mjs --games 20 --seed 1 --ms 200 [--params '{"own2":0.5}'] [--b engine|ref]
import {newGomoku,legalGomoku,stepGomoku,gomokuColor} from '../web/gomoku-games.js';
import {gomokuValues as refValues} from '../web/gomoku-planner.js';
import {gomokuValues as engValues,PARAMS} from '../web/gomoku-engine.js';
const args=Object.fromEntries(process.argv.slice(2).reduce((a,x,i,arr)=>x.startsWith('--')?[...a,[x.slice(2),arr[i+1]]]:a,[]));
const games=+(args.games??10),seed0=+(args.seed??1),ms=+(args.ms??200),limit=+(args.nodes??100000);
const DEF=structuredClone(PARAMS);
if(args.params)Object.assign(PARAMS,JSON.parse(args.params));
const bParams=args.bparams?JSON.parse(args.bparams):null;
const mkBudget=()=>{const t0=performance.now();return {nodes:0,tick(){if(this.nodes++>=limit||performance.now()-t0>=ms)throw Error('budget');}};};
function rng(s){return ()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296;};}
function pick(values){let best=values[0];for(const v of values)if(v.quality[0]>best.quality[0])best=v;return best.action;}
function play(seed,aIsPlayer1){
 const g=newGomoku(),R=rng(seed*7919+13);let player=1,done=false,winner=null,moves=0;
 const agentFor=p=>(p===1)===aIsPlayer1?'A':'B';
 const B0=args.b==='engine'?engValues:refValues;
 const saved={...PARAMS};
 while(!done&&moves<260){
  const legal=legalGomoku(g.board,g.state),who=agentFor(player);let action;
  if(g.state.phase==='opening_three'||g.state.phase==='opening_two'){// ouvertures aléatoires au centre
   const cells=legal.filter(a=>Math.abs(a.row-7)<=2&&Math.abs(a.col-7)<=2);action=cells[Math.floor(R()*cells.length)];}
  else if(g.state.phase==='choose_or_extend'||g.state.phase==='choose_color'){
   const ch=legal.filter(a=>a.choose),o={board:g.board.map(r=>r.slice()),current_player:player,gomoku_state:structuredClone(g.state),done:false};
   action=pick(refValues(o,ch,mkBudget()).action_values);}
  else{
   const o={board:g.board.map(r=>r.slice()),current_player:player,gomoku_state:structuredClone(g.state),done:false};
   let vals;
   if(who==='A')vals=engValues(o,legal,mkBudget()).action_values;
   else{Object.assign(PARAMS,bParams||DEF);vals=B0(o,legal,mkBudget()).action_values;Object.assign(PARAMS,saved);}
   action=pick(vals);}
  const s=stepGomoku(g.board,player,action,g.state);player=s.player;done=s.done;winner=s.winner;moves++;
 }
 if(!done)return 0.5;
 if(winner===0)return 0.5;
 return agentFor(winner)==='A'?1:0;
}
let w=0,d=0,l=0;
for(let i=0;i<games;i++){const seed=seed0*1000+(i>>1),r=play(seed,i%2===0);if(r===1)w++;else if(r===0)l++;else d++;}
console.log(JSON.stringify({games,wins:w,draws:d,losses:l,score:(w+d/2)/games}));

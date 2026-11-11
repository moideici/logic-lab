// Duels Hex 7x7 (règle de la tarte) : « A » = web/hex-engine.js contre « B » = web/hex-planner.js (référence) ou le moteur (--b engine).
// usage : node bench/hex-duel.mjs --games 20 --seed 1 --ms 200 [--params '{...}'] [--b engine]
import {newHex,legalHex,stepHex} from '../web/hex-games.js';
import {hexValues as refValues} from '../web/hex-planner.js';
import {hexValues as engValues,PARAMS} from '../web/hex-engine.js';
const args=Object.fromEntries(process.argv.slice(2).reduce((a,x,i,arr)=>x.startsWith('--')?[...a,[x.slice(2),arr[i+1]]]:a,[]));
const games=+(args.games??10),seed0=+(args.seed??1),ms=+(args.ms??200),limit=+(args.nodes??100000);
const DEF=structuredClone(PARAMS);if(args.params)Object.assign(PARAMS,JSON.parse(args.params));
const mkBudget=()=>{const t0=performance.now();return {nodes:0,tick(){if(this.nodes++>=limit||performance.now()-t0>=ms)throw Error('budget');}};};
function rng(s){return ()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296;};}
const pick=values=>values.reduce((a,v)=>v.quality[0]>a.quality[0]?v:a).action;
function play(seed,aIsPlayer1){
 const g=newHex(),R=rng(seed*7919+13);let player=1,done=false,winner=null,moves=0;
 const who=p=>(p===1)===aIsPlayer1?'A':'B',saved={...PARAMS};
 while(!done&&moves<120){
  const legal=legalHex(g.board,g.state);let action;
  if(moves===0){const cells=legal;action=cells[Math.floor(R()*cells.length)];}
  else{
   const o={board:g.board.map(r=>r.slice()),current_player:player,hex_state:structuredClone(g.state),done:false};let vals;
   if(who(player)==='A')vals=engValues(o,legal,mkBudget()).action_values;
   else{if(args.b==='engine'){Object.assign(PARAMS,DEF);vals=engValues(o,legal,mkBudget()).action_values;Object.assign(PARAMS,saved);}else vals=refValues(o,legal,mkBudget()).action_values;}
   action=pick(vals);}
  const s=stepHex(g.board,player,action,g.state);player=s.player;done=s.done;winner=s.winner;moves++;}
 if(!done||winner===null)return 0.5;
 return who(winner)==='A'?1:0;
}
let w=0,d=0,l=0;for(let i=0;i<games;i++){const r=play(seed0*1000+(i>>1),i%2===0);if(r===1)w++;else if(r===0)l++;else d++;}
console.log(JSON.stringify({games,wins:w,draws:d,losses:l,score:(w+d/2)/games}));

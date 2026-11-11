// Carte des ouvertures Hex 7x7 : pour chaque première pierre (au sens de la symétrie par rotation de 180°),
// taux de victoire du propriétaire de la pierre quand le moteur joue les deux camps (bruit : 2e meilleur coup avec proba 0.2).
// usage : node bench/hex-opening-map.mjs --cells 0,1,2 --games 40 --ms 100
import {newHex,legalHex,stepHex} from '../web/hex-games.js';
import {hexValues} from '../web/hex-engine.js';
const args=Object.fromEntries(process.argv.slice(2).reduce((a,x,i,arr)=>x.startsWith('--')?[...a,[x.slice(2),arr[i+1]]]:a,[]));
const cells=(args.cells??'0').split(',').map(Number),games=+(args.games??40),ms=+(args.ms??100);
let seed=+(args.seed??7);const R=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
const mk=()=>{const t0=performance.now();return {nodes:0,tick(){if(this.nodes++>=100000||performance.now()-t0>=ms)throw Error('budget');}};};
const out={};
for(const cell of cells){let wins=0;
 for(let g=0;g<games;g++){
  const h=newHex();h.board[Math.floor(cell/7)][cell%7]=1;h.state.swap_available=false;let player=2,done=false,winner=null,n=0;
  while(!done&&n<60){const legal=legalHex(h.board,h.state),o={board:h.board.map(r=>r.slice()),current_player:player,hex_state:structuredClone(h.state),done:false};
   const vals=hexValues(o,legal,mk()).action_values.filter(v=>!v.action.swap).sort((a,b)=>b.quality[0]-a.quality[0]);
   const a=(R()<.2&&vals.length>1?vals[1]:vals[0]).action;const s=stepHex(h.board,player,a,h.state);player=s.player;done=s.done;winner=s.winner;n++;}
  if(done&&h.state.colors[winner-1]===1)wins++;}
 out[cell]=wins/games;}
console.log(JSON.stringify(out));

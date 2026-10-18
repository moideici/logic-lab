import {AGENT_VERSION} from './agents.js';
export const LEGACY_GAMES=['tictactoe','connect4','2048','sudoku','minesweeper','sliding_puzzle'];
export function initialWeight(index){let x=(index+0x9e3779b9)>>>0;x^=x>>>16;x=Math.imul(x,0x85ebca6b);x^=x>>>13;x=Math.imul(x,0xc2b2ae35);x^=x>>>16;return Math.fround(((x>>>8)/16777216-.5)/16);}
export function upgradeLegacy(d,specs,defaultHead){
 const layouts=[[LEGACY_GAMES,1906,1912,818],[[...LEGACY_GAMES,'reversi','nim','lightsout'],2051,2060,925],[[...LEGACY_GAMES,'reversi','nim','lightsout','draughts','breakthrough'],2483,2494,3617],[[...LEGACY_GAMES,'reversi','nim','lightsout','draughts','breakthrough','hex'],2583,2595,3667],[[...LEGACY_GAMES,'reversi','nim','lightsout','draughts','breakthrough','hex','gomoku'],3042,3055,3894]];
 const layout=layouts.find(l=>JSON.stringify(l[0])===JSON.stringify(d.games));if(!layout)throw Error('Architecture historique invalide');
 const [oldGames,oldFeatures,oldInput,oldOutput]=layout,h=d.hidden;
 if(!Number.isInteger(h)||h<1||h>256||d.input!==oldInput||d.output!==oldOutput)throw Error('Architecture historique invalide');
 for(const [k,n]of[['w1',oldInput*h],['w2',oldOutput*h],['b1',h],['b2',oldOutput]])if(!Array.isArray(d[k])||d[k].length!==n)throw Error('Poids historiques invalides');
 const games=[...LEGACY_GAMES,...Object.keys(specs).filter(g=>!LEGACY_GAMES.includes(g))],features=Object.values(specs).reduce((n,s)=>n+s[0],0),input=features+games.length,output=Object.values(specs).reduce((n,s)=>n+s[1],0);
 const out={...d,format:'garry-mlp-v3',version:AGENT_VERSION,games,input,output,w1:Array.from({length:input*h},(_,i)=>initialWeight(i)),w2:Array.from({length:output*h},(_,i)=>initialWeight(1000000+i)),b2:Array(output).fill(0),game_steps:Object.fromEntries(games.map(g=>[g,d.games.includes(g)?d.game_steps?.[g]:0]))};
 for(let i=0;i<oldFeatures*h;i++)out.w1[i]=d.w1[i];
 for(let g=0;g<d.games.length;g++)for(let j=0;j<h;j++)out.w1[(features+g)*h+j]=d.w1[(oldFeatures+g)*h+j];
 for(let j=0;j<h;j++)for(let k=0;k<oldOutput;k++)out.w2[j*output+k]=d.w2[j*oldOutput+k];
 for(let k=0;k<oldOutput;k++)out.b2[k]=d.b2[k];if(d.format==='garry-mlp-v1')out.position_head=structuredClone(defaultHead);return out;
}

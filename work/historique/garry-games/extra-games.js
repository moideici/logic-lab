export const EXTRA_NAMES={reversi:'Reversi 6 × 6',nim:'Nim',lightsout:'Lights Out'};
export const EXTRA_SPECS={reversi:[72,37],nim:[48,45],lightsout:[25,25]};
const dirs=[];for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++)if(dr||dc)dirs.push([dr,dc]);
export function flipLights(b,row,col){for(const [dr,dc]of[[0,0],[1,0],[-1,0],[0,1],[0,-1]]){const r=row+dr,c=col+dc;if(r>=0&&r<5&&c>=0&&c<5)b[r][c]^=1;}}
export function createExtra(name,seed){let state=seed>>>0;const random=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296;};
 if(name==='reversi'){const b=Array.from({length:6},()=>Array(6).fill(0));b[2][2]=b[3][3]=2;b[2][3]=b[3][2]=1;return b;}
 if(name==='nim')return [3+Math.floor(random()*4),5+Math.floor(random()*4),7+Math.floor(random()*4)].map(n=>Array.from({length:15},(_,i)=>Number(i<n)));
 const b=Array.from({length:5},()=>Array(5).fill(0));for(let i=0;i<25;i++)if(random()<.5)flipLights(b,Math.floor(i/5),i%5);if(!b.flat().some(Boolean))flipLights(b,2,2);return b;
}
export function reversiFlips(b,p,row,col){if(b[row][col])return [];const out=[];for(const [dr,dc]of dirs){let r=row+dr,c=col+dc;const line=[];while(r>=0&&r<6&&c>=0&&c<6&&b[r][c]===3-p){line.push([r,c]);r+=dr;c+=dc;}if(line.length&&r>=0&&r<6&&c>=0&&c<6&&b[r][c]===p)out.push(...line);}return out;}
export function reversiMoves(b,p){const a=[];for(let r=0;r<6;r++)for(let c=0;c<6;c++)if(reversiFlips(b,p,r,c).length)a.push({row:r,col:c});return a;}
export function legalExtra(name,b,p){if(name==='nim')return b.flatMap((row,pile)=>Array.from({length:row.reduce((a,v)=>a+v,0)},(_,i)=>({pile,take:i+1})));if(name==='lightsout')return Array.from({length:25},(_,i)=>({row:Math.floor(i/5),col:i%5}));const moves=reversiMoves(b,p);return moves.length?moves:reversiMoves(b,3-p).length?[{pass:true}]:[];}
export function stepExtra(name,b,p,a){
 if(name==='nim'){const n=b[a.pile].reduce((s,v)=>s+v,0)-a.take;b[a.pile]=Array.from({length:15},(_,i)=>Number(i<n));const left=b.flat().reduce((s,v)=>s+v,0),done=left===0;return {player:done?p:3-p,done,winner:done?p:null,score:left,reward:done?1:0};}
 if(name==='lightsout'){const before=b.flat().reduce((s,v)=>s+v,0);flipLights(b,a.row,a.col);const left=b.flat().reduce((s,v)=>s+v,0),done=left===0;return {player:p,done,winner:done?1:null,score:25-left,reward:(before-left)/25+(done?1:0)};}
 const actor=p;if(!a.pass){const flips=reversiFlips(b,p,a.row,a.col);b[a.row][a.col]=p;for(const [r,c]of flips)b[r][c]=p;}p=3-p;const done=!reversiMoves(b,1).length&&!reversiMoves(b,2).length,score=b.flat().filter(v=>v===1).length-b.flat().filter(v=>v===2).length,winner=done?(score>0?1:score<0?2:0):null;return {player:p,done,winner,score,reward:done?(winner===actor?1:winner?-1:0):0};
}
export function encodeExtra(o){const x=new Float32Array(EXTRA_SPECS[o.game][0]);if(o.game==='nim')o.board.forEach((row,p)=>x[p*16+row.reduce((s,v)=>s+v,0)]=1);else if(o.game==='lightsout')x.set(o.board.flat());else o.board.flat().forEach((v,i)=>{if(v)x[i*2+(v===o.current_player?0:1)]=1;});return x;}
export function extraActionIndex(game,a){return game==='nim'?a.pile*15+a.take-1:game==='reversi'?(a.pass?36:a.row*6+a.col):a.row*5+a.col;}

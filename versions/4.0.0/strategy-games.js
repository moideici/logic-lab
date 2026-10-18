// FMJD international draughts: https://www.fmjd.org/downloads/FMJD_Annexes_2024_8-sig.pdf
// Breakthrough: https://superdupergames.org/rules/break.pdf
export const STRATEGY_NAMES={draughts:'Dames internationales',breakthrough:'Percée'};
export const STRATEGY_SPECS={draughts:[304,2500],breakthrough:[128,192]};
const diagonals=[[-1,-1],[-1,1],[1,-1],[1,1]],inside=(r,c,n=10)=>r>=0&&r<n&&c>=0&&c<n;
export const pieceOwner=v=>v?(v-1)%2+1:0;
export const positionKey=(b,p)=>p+':'+b.flat().join('');
export function newDraughtsState(board=null,player=1){return {forced_piece:null,pending_captures:[],quiet_plies:0,endgame_16:null,endgame_5:null,repetitions:board?{[positionKey(board,player)]:1}:{}};}
export function createStrategy(name){const n=name==='draughts'?10:8,b=Array.from({length:n},()=>Array(n).fill(0)),rows=name==='draughts'?4:2;for(let r=0;r<n;r++)for(let c=0;c<n;c++){if(name==='draughts'&&(r+c)%2!==1)continue;if(r<rows)b[r][c]=2;else if(r>=n-rows)b[r][c]=1;}return {board:b,state:newDraughtsState(b)};}
export function captureLegs(b,p,r,c,pending){const king=b[r][c]>2,out=[];for(const [dr,dc]of diagonals){let y=r+dr,x=c+dc;if(king)while(inside(y,x)&&!b[y][x]){y+=dr;x+=dc;}if(!inside(y,x)||pieceOwner(b[y][x])!==3-p||pending.has(y*10+x))continue;const victim=[y,x];y+=dr;x+=dc;while(inside(y,x)&&!b[y][x]){out.push([y,x,victim]);if(!king)break;y+=dr;x+=dc;}}return out;}
export function maximalFirstLegs(b,p,origins,pending){const memo=new Map();function length(r,c,captured){const key=r+','+c+':'+[...captured].sort((a,b)=>a-b).join(',');if(memo.has(key))return memo.get(key);let best=0;for(const [y,x,victim]of captureLegs(b,p,r,c,captured)){const piece=b[r][c];b[r][c]=0;b[y][x]=piece;let n;try{n=1+length(y,x,new Set([...captured,victim[0]*10+victim[1]]));}finally{b[r][c]=piece;b[y][x]=0;}best=Math.max(best,n);}memo.set(key,best);return best;}let best=0,out=[];for(const [r,c]of origins){memo.clear();for(const [y,x,victim]of captureLegs(b,p,r,c,pending)){const piece=b[r][c];b[r][c]=0;b[y][x]=piece;let n;try{n=1+length(y,x,new Set([...pending,victim[0]*10+victim[1]]));}finally{b[r][c]=piece;b[y][x]=0;}const action={from:[r,c],to:[y,x]};if(n>best){best=n;out=[action];}else if(n===best)out.push(action);}}return out;}
export function legalStrategy(name,b,p,state=newDraughtsState()){
 if(name==='breakthrough'){const out=[],dr=p===1?-1:1;for(let r=0;r<8;r++)for(let c=0;c<8;c++)if(b[r][c]===p)for(const dc of [-1,0,1]){const y=r+dr,x=c+dc;if(inside(y,x,8)&&(!b[y][x]||(dc&&b[y][x]===3-p)))out.push({from:[r,c],to:[y,x]});}return out;}
 const pending=new Set(state.pending_captures.map(([r,c])=>r*10+c)),origins=state.forced_piece?[state.forced_piece]:b.flatMap((row,r)=>row.flatMap((v,c)=>pieceOwner(v)===p?[[r,c]]:[])),captures=maximalFirstLegs(b,p,origins,pending);
 if(captures.length||state.forced_piece)return captures;const out=[];
 for(const [r,c]of origins)for(const [dr,dc]of diagonals){if(b[r][c]<=2&&dr!==(p===1?-1:1))continue;let y=r+dr,x=c+dc;while(inside(y,x)&&!b[y][x]){out.push({from:[r,c],to:[y,x]});if(b[r][c]<=2)break;y+=dr;x+=dc;}}
 return out;
}
export const material=b=>b.flat().reduce((s,v)=>s+(v?(pieceOwner(v)===1?1:-1)*(v>2?3:1):0),0);
function drawLimits(b,state){const pieces={1:[],2:[]};b.forEach((row,r)=>row.forEach((v,c)=>{if(v)pieces[pieceOwner(v)].push([r,c,v]);}));for(const p of [1,2]){const lone=pieces[p],other=pieces[3-p];if(lone.length!==1||lone[0][2]<=2||!other.some(v=>v[2]>2))continue;if(other.length===3&&state.endgame_16===null)state.endgame_16=0;if(((other.length>=1&&other.length<=2)||(other.length===3&&lone[0][0]+lone[0][1]===9))&&state.endgame_5===null)state.endgame_5=0;}}
export function stepStrategy(name,b,p,a,state=newDraughtsState()){
 const [r,c]=a.from,[y,x]=a.to,piece=b[r][c];
 if(name==='breakthrough'){b[r][c]=0;b[y][x]=piece;let won=y===(p===1?0:7)||!b.flat().includes(3-p),player=won?p:3-p;if(!won&&!legalStrategy(name,b,player).length){won=true;player=p;}return {player,done:won,winner:won?p:null,score:material(b),reward:won?1:0,state};}
 const dr=y>r?1:-1,dc=x>c?1:-1,victims=[];let rr=r+dr,cc=c+dc;while(rr!==y||cc!==x){if(b[rr][cc])victims.push([rr,cc]);rr+=dr;cc+=dc;}
 b[r][c]=0;b[y][x]=piece;
 if(victims.length){state.pending_captures.push(...victims);state.forced_piece=[y,x];if(captureLegs(b,p,y,x,new Set(state.pending_captures.map(([r,c])=>r*10+c))).length)return {player:p,done:false,winner:null,score:material(b),reward:0,state};}
 const captured=state.pending_captures.length>0;for(const [r,c]of state.pending_captures)b[r][c]=0;state.pending_captures=[];state.forced_piece=null;
 if(piece<=2&&y===(p===1?0:9))b[y][x]=p+2;
 state.quiet_plies=piece<=2||captured?0:state.quiet_plies+1;for(const key of ['endgame_16','endgame_5'])if(state[key]!==null)state[key]++;drawLimits(b,state);
 const player=3-p,won=!legalStrategy(name,b,player,state).length,key=positionKey(b,player);state.repetitions[key]=(state.repetitions[key]??0)+1;
 const drawn=!won&&(state.repetitions[key]>=3||state.quiet_plies>=50||(state.endgame_16!==null&&state.endgame_16>=32)||(state.endgame_5!==null&&state.endgame_5>=10));
 return {player:won?p:player,done:won||drawn,winner:won?p:drawn?0:null,score:material(b),reward:won?1:0,state};
}
export function encodeStrategy(o){const x=Array(STRATEGY_SPECS[o.game][0]).fill(0),p=o.current_player;if(o.game==='breakthrough'){o.board.flat().forEach((v,i)=>{if(v)x[i*2+(v===p?0:1)]=1;});return x;}o.board.forEach((row,r)=>row.forEach((v,c)=>{if(v)x[(r*5+Math.floor(c/2))*4+(pieceOwner(v)===p?0:2)+Number(v>2)]=1;}));const s=o.draughts_state??newDraughtsState();if(s.forced_piece)x[200+s.forced_piece[0]*5+Math.floor(s.forced_piece[1]/2)]=1;for(const [r,c]of s.pending_captures)x[250+r*5+Math.floor(c/2)]=1;x[300]=s.quiet_plies/50;x[301]=(s.endgame_16??0)/32;x[302]=(s.endgame_5??0)/10;x[303]=(s.repetitions[positionKey(o.board,p)]??0)/3;return x;}
export function strategyActionIndex(name,a){const [r,c]=a.from,[y,x]=a.to;return name==='draughts'?(r*5+Math.floor(c/2))*50+y*5+Math.floor(x/2):(r*8+c)*3+x-c+1;}

export function defaultPositionHead(){return {id:'garry-position-v1',features:32,game:'connect4',weights:[...Array.from({length:8},()=>[2,16,120]).flat(),0,0,0,7,0,0,0,0],samples:0,revision:'initial',enabled:false};}
export function validatePositionHead(h){
 if(!h||h.id!=='garry-position-v1'||h.features!==32||h.game!=='connect4'||!Array.isArray(h.weights)||h.weights.length!==32||!h.weights.every(v=>typeof v==='number'&&Number.isFinite(v)&&Math.abs(v)<=10000)||!Number.isInteger(h.samples)||h.samples<0||typeof h.enabled!=='boolean'||typeof h.revision!=='string')throw Error('Évaluateur Garry invalide');
 return {...h,weights:h.weights.slice()};
}
export function positionFeatures(o){
 const b=o.board,p=o.current_player,x=Array(32).fill(0),threats=[new Set(),new Set()];
 for(let r=0;r<6;r++)for(let c=0;c<7;c++)for(const [d,[dr,dc]] of [[0,[0,1]],[1,[1,0]],[2,[1,1]],[3,[1,-1]]]){
  if(r+3*dr>=6||c+3*dc<0||c+3*dc>=7)continue;
  const cells=Array.from({length:4},(_,i)=>[r+i*dr,c+i*dc]),a=cells.filter(([r,c])=>b[r][c]===p).length,e=cells.filter(([r,c])=>b[r][c]===3-p).length;
  for(const [count,other,sign,side] of [[a,e,1,0],[e,a,-1,1]])if(count&&!other&&count<4){x[(d*2+r%2)*3+count-1]+=sign;if(count===3)cells.filter(([r,c])=>!b[r][c]).forEach(([r,c])=>threats[side].add(r*7+c));}
 }
 for(let r=0;r<6;r++)for(let c=0;c<7;c++)if(b[r][c])x[24+Math.min(c,6-c)]+=b[r][c]===p?1:-1;
 for(const [side,sign] of [[0,1],[1,-1]])for(const i of threats[side]){const r=Math.floor(i/7),c=i%7,playable=r===5||!!b[r+1][c];x[28+(playable?0:2)+r%2]+=sign;}
 return x;
}

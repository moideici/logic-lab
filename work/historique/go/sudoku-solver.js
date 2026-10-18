// Public-board solver. No environment answer or hidden state is read.
export function solveSudoku(board,{limit=2,tick=()=>{}}={}){
 const b=board.map(row=>row.slice()),rows=Array(9).fill(0),cols=Array(9).fill(0),boxes=Array(9).fill(0),solutions=[];
 for(let r=0;r<9;r++)for(let c=0;c<9;c++){const v=b[r][c];if(!v)continue;const bit=1<<v,k=3*Math.floor(r/3)+Math.floor(c/3);if((rows[r]|cols[c]|boxes[k])&bit)return {solutions,complete:true};rows[r]|=bit;cols[c]|=bit;boxes[k]|=bit;}
 let complete=true;
 function visit(){tick();let cell=null;
  for(let r=0;r<9;r++)for(let c=0;c<9;c++)if(!b[r][c]){const k=3*Math.floor(r/3)+Math.floor(c/3),mask=1022&~(rows[r]|cols[c]|boxes[k]);if(!mask)return;let count=0;for(let m=mask;m;m&=m-1)count++;if(!cell||count<cell.count)cell={r,c,k,mask,count};}
  if(!cell){solutions.push(b.map(row=>row.slice()));return;}
  const {r,c,k}=cell;for(let mask=cell.mask;mask;mask&=mask-1){const bit=mask&-mask,v=31-Math.clz32(bit);b[r][c]=v;rows[r]|=bit;cols[c]|=bit;boxes[k]|=bit;try{visit();}finally{b[r][c]=0;rows[r]^=bit;cols[c]^=bit;boxes[k]^=bit;}if(solutions.length>=limit)return;}
 }
 try{visit();}catch(e){if(e.message!=='budget')throw e;complete=false;}
 return {solutions,complete};
}

// Array representation preserves tiles above the four-bit packed solver range.
import {slide} from './engine.js';
const directions=['up','down','left','right'];
export function scoreArraySearch(o,legal,logits,budget){
 const same=(a,b)=>a.every((row,r)=>row.every((v,c)=>v===b[r][c]));
 function heuristic(b){let total=0;const rows=b.concat(Array.from({length:4},(_,c)=>b.map(row=>row[c])));for(const row of rows){const v=row.map(n=>n?Math.log2(n):0),nz=v.filter(Boolean);let down=0,up=0,merges=0,sum=0;for(let i=0;i<4;i++){sum+=v[i]**3.5;if(i<3){const d=v[i]**4-v[i+1]**4;if(d>0)down+=d;else up-=d;}}for(let i=1;i<nz.length;i++)if(nz[i]===nz[i-1])merges++;total+=270*(4-nz.length)+700*merges-47*Math.min(up,down)-11*sum;}return total;}
 function max(b,depth){budget.tick();if(!depth)return heuristic(b);let best=-1e9;for(const d of directions){const [child,g]=slide(b,d);if(!same(b,child))best=Math.max(best,chance(child,depth)+g*.05);}return best;}
 function chance(b,depth){budget.tick();const empty=[];b.forEach((row,r)=>row.forEach((v,c)=>{if(!v)empty.push([r,c]);}));if(!empty.length)return max(b,depth-1);let value=0;for(const [r,c]of empty)for(const [v,p]of [[2,.9],[4,.1]]){const child=b.map(row=>row.slice());child[r][c]=v;value+=p*(depth===1?heuristic(child):max(child,depth-1))/empty.length;}return value;}
 let values=legal.map(action=>{const [b,g]=slide(o.board,action.direction);return {action,quality:[heuristic(b)+g*.05]};}),reached=0;
 for(let depth=1;depth<=(budget.depth??2);depth++){const next=[];try{for(const action of legal){const [b,g]=slide(o.board,action.direction);next.push({action,quality:[chance(b,depth)+g*.05]});}}catch(e){if(e.message!=='budget')throw e;break;}values=next;reached=depth;}
 const best=values.slice().sort((a,b)=>b.quality[0]-a.quality[0]||logits[directions.indexOf(b.action.direction)]-logits[directions.indexOf(a.action.direction)])[0];return {action:best.action,action_values:values,info:{method:'array_score_expectimax',nodes:budget.nodes,depth:reached,analysis_exact:false,optimal:false,evaluation_scope:'bounded_score_expectimax'}};
}

import {actionIndex,candidates} from './engine.js';

export function compareQuality(a,b){for(let i=0;i<Math.max(a.length,b.length);i++){const d=(a[i]??0)-(b[i]??0);if(d)return d;}return 0;}
export function selectQuality(values,level,logits,game){
 if(!Number.isInteger(level)||level<0||level>10)throw Error('Le niveau doit être un entier de 0 à 10');
 if(!values.length)throw Error('Aucun coup évalué');
 const sorted=values.slice().sort((a,b)=>compareQuality(a.quality,b.quality)||(logits[actionIndex(game,a.action)]-logits[actionIndex(game,b.action)]));
 const rank=Math.floor(level*(sorted.length-1)/10+.5),selected=sorted[rank];
 return {selected,info:{level,quality_rank:rank,legal_count:sorted.length,selected_is_best:compareQuality(selected.quality,sorted.at(-1).quality)===0,selected_is_worst:compareQuality(selected.quality,sorted[0].quality)===0,quality:selected.quality,level_semantics:'legal_move_quality_quantile'}};
}

// Enumerate at most two completions. Uniqueness is asserted only after the
// entire remaining search has finished, never on an interrupted traversal.
const sudokuCache=new Map();
export function sudokuValues(o,legal,logits,budget){
 const key=JSON.stringify(o.board);let result=sudokuCache.get(key);
 if(!result){
  const b=o.board.map(r=>r.slice()),solutions=[];let complete=true;
  function visit(){budget.tick();let cell=null;for(let r=0;r<9;r++)for(let c=0;c<9;c++)if(!b[r][c]){const vals=candidates(b,r,c);if(!vals.length)return;if(!cell||vals.length<cell.vals.length)cell={r,c,vals};}
   if(!cell){solutions.push(b.map(r=>r.slice()));return;}
   for(const v of cell.vals){b[cell.r][cell.c]=v;try{visit();}finally{b[cell.r][cell.c]=0;}if(solutions.length>=2)return;}
  }
  try{visit();}catch(e){if(e.message!=='budget')throw e;complete=false;}
  result={solutions,complete,unique:complete&&solutions.length===1};
  if(complete){if(sudokuCache.size>1000)sudokuCache.clear();sudokuCache.set(key,result);}
 }
 const {solutions,complete,unique}=result,unsat=complete&&!solutions.length;
 const values=legal.map(action=>{
  let q=0,proved=false;
  if(action.undo){q=unsat?2:-1;proved=unsat||!!solutions.length;}
  else if(solutions.some(b=>b[action.row][action.col]===action.value)){q=1;proved=true;}
  else if(unique||unsat){q=-2;proved=true;}
  else {const b=o.board.map(r=>r.slice());b[action.row][action.col]=action.value;if(b.some((row,r)=>row.some((v,c)=>!v&&!candidates(b,r,c).length))){q=-2;proved=true;}}
  return {action,quality:[q],proved};
 });
 return {action:values.slice().sort((a,b)=>b.quality[0]-a.quality[0]||logits[actionIndex(o.game,b.action)]-logits[actionIndex(o.game,a.action)])[0].action,
  action_values:values,info:{method:'sudoku_completion_ranking',optimal:!!solutions.length,analysis_exact:unique||unsat,nodes:budget.nodes,solution_found:!!solutions.length,unique_solution:unique,remaining_moves:o.board.flat().filter(v=>!v).length}};
}

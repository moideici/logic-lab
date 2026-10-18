import {CONNECT_LIMITS,CONNECT_TIMES} from './connect4-runtime.js';
import {exactSliding,exactTictactoe,connectSearch,tileSearch,mineSearch} from './fast-search.js';
import {selectQuality,sudokuValues} from './quality.js';
export const LIMITS=[16,50,150,500,1500,4000,10000,25000,50000,100000];
export const TIMES=[.5,1,2,3,5,8,12,16,22,30];
export function planDecision(o,legal,model,level,decision,preparedLogits=null){
 if(o.done)return decision;
 const began=performance.now(),logits=preparedLogits??model.forward(o).z;
 const budget={nodes:0,limit:o.game==='connect4'?CONNECT_LIMITS[9]:LIMITS[9],depth:2,criticalDepth:3,tick(){if(this.nodes++>=this.limit||performance.now()-began>=(o.game==='connect4'?CONNECT_TIMES[9]:TIMES[9]))throw Error('budget');}};
 const solver={tictactoe:exactTictactoe,sliding_puzzle:exactSliding,connect4:connectSearch,'2048':tileSearch,minesweeper:mineSearch,sudoku:sudokuValues}[o.game];
 if(!solver)return decision;
 const result=solver(o,legal,logits,budget,{timeMs:CONNECT_TIMES[9],analyze:true,positionHead:model.positionHead});
 const {selected,info}=selectQuality(result.action_values,level,logits,o.game),best=info.selected_is_best;
 const selectedInfo={...selected};delete selectedInfo.action;delete selectedInfo.quality;
 return {action:selected.action,info:{...decision.info,...result.info,...selectedInfo,...info,agent:'neural+planner',optimal:best&&!!result.info.optimal,confidence:null,policy_confidence:decision.info.confidence,evaluation_scope:result.info.analysis_exact?'exact_legal_move_values':result.info.evaluation_scope??'bounded_public_analysis',objective:'win_then_fewest_moves',time_ms:performance.now()-began+decision.info.time_ms}};
}

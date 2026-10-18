import {selectSlidingLevel} from './sliding-levels.js';
import {applyStrategicStyles} from './strategic-styles.js';
import {goValues} from './go-planner.js';
import {gomokuValues} from './gomoku-planner.js';
import {hexValues} from './hex-planner.js';
import {strategyValues} from './strategy-planner.js';
import {extraValues} from './extra-planner.js';
import {CONNECT_LIMITS,CONNECT_TIMES} from './connect4-runtime.js';
import {exactSliding,exactTictactoe,connectSearch,tileSearch,mineSearch} from './fast-search.js';
import {actionIndex,styleBias} from './engine.js';
import {selectQuality,sudokuValues} from './quality.js';
export const LIMITS=[16,50,150,500,1500,4000,10000,25000,50000,100000];
export const TIMES=[.5,1,2,3,5,8,12,16,22,30];
export function planDecision(o,legal,model,level,decision,preparedLogits=null,random=Math.random){
 if(o.done)return decision;
 const began=performance.now(),logits=preparedLogits??model.forward(o).z;
 const budget={nodes:0,limit:o.game==='connect4'?CONNECT_LIMITS[9]:o.game==='hex'?4000:['draughts','breakthrough'].includes(o.game)?30000:LIMITS[9],depth:2,criticalDepth:3,tick(){if(this.nodes++>=this.limit||performance.now()-began>=(o.game==='connect4'?CONNECT_TIMES[9]:o.game==='go'?250:(['draughts','breakthrough','hex','gomoku'].includes(o.game)||o.game==='sliding_puzzle'&&o.board.length>3)?200:o.game==='reversi'?150:TIMES[9]))throw Error('budget');}};
 const solver={go:(o,legal,logits,budget)=>goValues(o,legal,budget),gomoku:(o,legal,logits,budget)=>gomokuValues(o,legal,budget),hex:(o,legal,logits,budget)=>hexValues(o,legal,budget),...Object.fromEntries(['draughts','breakthrough'].map(g=>[g,(o,legal,logits,budget)=>strategyValues(o,legal,budget)])),tictactoe:exactTictactoe,sliding_puzzle:exactSliding,connect4:connectSearch,'2048':tileSearch,minesweeper:mineSearch,sudoku:sudokuValues,...Object.fromEntries(['reversi','nim','lightsout'].map(g=>[g,(o,legal,logits,budget)=>extraValues(o,legal,budget)]))}[o.game];
 if(!solver)return decision;
 const result=solver(o,legal,logits,budget,{timeMs:CONNECT_TIMES[9],analyze:level!==10,maxDepth:level===10?42:20,positionHead:model.positionHead,searchMemory:model.searchMemory});
 if(o.game==='connect4'&&level===10)return {action:result.action,info:{...decision.info,...result.info,level,agent:'neural+planner',confidence:null,selected_is_best:true,selected_is_worst:false,level_semantics:'strongest_completed_search',target_depth:20,depth_target_reached:result.info.depth>=20,quality:[result.info.value??0],time_ms:performance.now()-began+decision.info.time_ms}};
 const tieLogits=Float32Array.from(logits);for(const a of legal)tieLogits[actionIndex(o.game,a)]+=styleBias(o,a,decision.info.style??'balanced');
 const styled=applyStrategicStyles(o,result.action_values,decision.info.style??'balanced',result.info.analysis_exact);result.action_values=styled.values;result.info.style_effect=styled.changed?'strategic_evaluation':'equal_quality_tiebreak';const {selected,info}=['sliding_puzzle','sudoku'].includes(o.game)?selectSlidingLevel(result.action_values,level,tieLogits,random,o.game):selectQuality(result.action_values,level,tieLogits,o.game),best=info.selected_is_best;
 const selectedInfo={...selected};
 if(o.game==='connect4'){const v=selected.quality[0];selectedInfo.value=v;selectedInfo.forced_win=v>999957;selectedInfo.forced_loss=v< -999957;selectedInfo.remaining_moves=Math.abs(v)>999957?1000000-Math.abs(v):undefined;}
delete selectedInfo.action;delete selectedInfo.quality;
 return {action:selected.action,info:{...decision.info,...result.info,...selectedInfo,...info,agent:'neural+planner',optimal:best&&(!!result.info.optimal||(o.game==='connect4'&&[999999,999997].includes(selected.quality[0]))),confidence:null,policy_confidence:decision.info.confidence,evaluation_scope:result.info.analysis_exact?'exact_legal_move_values':result.info.evaluation_scope??'bounded_public_analysis',objective:'win_then_fewest_moves',time_ms:performance.now()-began+decision.info.time_ms}};
}

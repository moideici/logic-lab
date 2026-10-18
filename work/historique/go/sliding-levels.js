import {selectQuality,compareQuality} from './quality.js';
export function selectSlidingLevel(values,level,logits,random=Math.random){
 if(level===0||level===10)return selectQuality(values,level,logits,'sliding_puzzle');
 if(!Number.isInteger(level)||level<0||level>10)throw Error('Niveau du taquin invalide');
 const sorted=values.slice().sort((a,b)=>compareQuality(a.quality,b.quality)),best=sorted.at(-1).quality,optimal=sorted.filter(v=>compareQuality(v.quality,best)===0),others=sorted.filter(v=>compareQuality(v.quality,best)!==0),probability=.5+level*.05;
 const pool=!others.length||random()<probability?optimal:others,selected=pool[Math.min(pool.length-1,Math.floor(random()*pool.length))];
 return {selected,info:{level,quality_rank:sorted.indexOf(selected),legal_count:sorted.length,selected_is_best:compareQuality(selected.quality,best)===0,selected_is_worst:compareQuality(selected.quality,sorted[0].quality)===0,quality:selected.quality,level_semantics:'optimal_path_probability',optimal_move_probability:probability}};
}

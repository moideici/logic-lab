// Search experience and solved public positions travel inside the one model.
export const emptySearchMemory=()=>({format:'garry-search-memory-v1',game:'connect4',entries:[]});
function mirror(key){let out=0n;for(let c=0;c<7;c++){out=(out<<7n)|(key&127n);key>>=7n;}return out;}
export function memoryKey(o){let position=0n,mask=0n;o.board.forEach((row,r)=>row.forEach((p,c)=>{if(p){const bit=1n<<BigInt(c*7+5-r);mask|=bit;if(p===o.current_player)position|=bit;}}));const raw=position+mask,other=mirror(raw),flip=other<raw;return {key:(flip?other:raw).toString(16).padStart(13,'0'),flip};}
export function validateSearchMemory(data){
 if(data===undefined)return emptySearchMemory();
 if(!data||data.format!=='garry-search-memory-v1'||data.game!=='connect4'||!Array.isArray(data.entries)||data.entries.length>100000)throw Error('Mémoire de recherche invalide');
 const seen=new Set();const entries=data.entries.map(e=>{
  if(!e||!/^([0-9a-f]{13})$/.test(e.key)||!Number.isInteger(e.column)||e.column<0||e.column>6||!['experience','non_loss','win','draw'].includes(e.guarantee)||seen.has(e.key))throw Error('Position de mémoire invalide');
  let key=BigInt('0x'+e.key),copy=key;if(key>=(1n<<49n)||mirror(key)<key)throw Error('Clé de mémoire invalide');
  for(let c=0;c<7;c++){const chunk=Number(copy&127n);if(chunk===127||(c===e.column&&chunk>=63))throw Error('Colonne de mémoire illégale');copy>>=7n;}
  seen.add(e.key);return {key:e.key,column:e.column,guarantee:e.guarantee};
 });
 return {format:data.format,game:data.game,entries};
}
const indices=new WeakMap();
export function lookupSearchMemory(o,legal,memory){if(!memory?.entries?.length)return null;let index=indices.get(memory);if(!index){index=new Map(memory.entries.map(e=>[e.key,e]));indices.set(memory,index);}const {key,flip}=memoryKey(o),entry=index.get(key);if(!entry)return null;const column=flip?6-entry.column:entry.column;if(!legal.some(a=>a.column===column))return null;return {...entry,column};}
export function memoryDecision(entry,remaining){const guarantee=entry.guarantee,proof=guarantee==='experience'?null:guarantee,complete=proof==='win'||proof==='draw',value=proof==='win'?1000000-remaining:0;return {action:{column:entry.column},info:{method:proof?'solved_opening':'self_play_opening',runtime:'opening_memory',nodes:0,depth:0,value,proof,search_complete:complete,outcome_proven:complete,certified_non_loss:!!proof,certificate_nodes:0,solved_horizon:complete?remaining:null,mate_distance_known:false,principal_variation:[entry.column],learned_value:false,evaluation_scope:proof?'offline_certified_move':'adversarial_self_play',forced_win:proof==='win',forced_loss:false,optimal:proof==='draw',outcome_optimal:complete,opening_memory:true}};}

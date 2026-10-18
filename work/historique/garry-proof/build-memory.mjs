import fs from 'node:fs';
import {memoryKey,validateSearchMemory} from './search-memory.js';
const dir='C:/Users/gabor/code/logic-lab/work/garry-proof';
const trials=JSON.parse(fs.readFileSync(`${dir}/opening-duels.json`)),entries=new Map(),evidence=[];
function add(o,column,guarantee,source){const {key,flip}=memoryKey(o),entry={key,column:flip?6-column:column,guarantee},prior=entries.get(key),rank={experience:0,non_loss:1,draw:2,win:3};if(prior&&['win','draw'].includes(prior.guarantee)&&['win','draw'].includes(guarantee)&&prior.guarantee!==guarantee)throw Error('Contradictory solved outcome');if(!prior||rank[guarantee]>rank[prior.guarantee])entries.set(key,entry);evidence.push({entry,observation:o,column,source});}
const opening=trials.samples.find(s=>s.plan.length===1&&s.plan[0]===2).trace.find(t=>t.observation.current_player===2);
add(opening.observation,2,'experience','adversarial opening exploration; no mathematical non-loss claim');
for(const sample of trials.samples)for(const t of sample.trace)if(t.method==='offline_exact_opening'&&[1,2,3].includes(t.proof))add(t.observation,t.column,({1:'non_loss',2:'win',3:'draw'})[t.proof],'offline exact WDL search, 100M nodes / 10s maximum');
const memory=validateSearchMemory({format:'garry-search-memory-v1',game:'connect4',entries:[...entries.values()].sort((a,b)=>a.key.localeCompare(b.key))});
fs.writeFileSync(`${dir}/memory.json`,JSON.stringify(memory,null,2));fs.writeFileSync(`${dir}/memory-evidence.json`,JSON.stringify({trials:{wins:trials.wins,losses:trials.losses,draws:trials.draws},evidence},null,2));console.log(JSON.stringify(memory));

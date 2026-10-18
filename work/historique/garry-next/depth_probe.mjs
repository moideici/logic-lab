import fs from 'node:fs';
import {GarryModel} from '../web/engine.js';
import {connectDecision,connectReady,CONNECT_LIMITS,CONNECT_TIMES} from '../web/connect4-runtime.js';
await connectReady;
const m=new GarryModel(JSON.parse(fs.readFileSync('web/models/garry.json'))),data=JSON.parse(fs.readFileSync('training-runs/garry-value-20261016/positions.json'));
const samples=[];
for(const phase of [0,6,12,18,24]){
 const o=phase===0?{game:'connect4',board:Array.from({length:6},()=>Array(7).fill(0)),current_player:1,done:false,moves:0}:data.find(d=>d.obs.moves>=phase&&d.obs.moves<phase+3).obs;
 const legal=o.board[0].flatMap((v,column)=>v?[]:[{column}]),began=performance.now();
 const d=connectDecision(o,legal,m.forGame('connect4').forward(o).z,{nodes:0,limit:CONNECT_LIMITS[9]},{timeMs:CONNECT_TIMES[9],maxDepth:20,positionHead:m.positionHead});
 samples.push({phase:o.moves,board:o.board,player:o.current_player,action:d.action,ms:performance.now()-began,...d.info});
}
const report={target_depth:20,time_budget_ms:CONNECT_TIMES[9],node_budget:CONNECT_LIMITS[9],selection:'Five targeted phases, not a win-rate test',samples};
fs.writeFileSync('web/models/garry-depth.json',JSON.stringify(report,null,2));console.log(JSON.stringify(samples.map(({phase,depth,ms,proof,nodes,principal_variation})=>({phase,depth,ms,proof,nodes,pv:principal_variation}))));

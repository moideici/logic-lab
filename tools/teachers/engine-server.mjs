// Serveur d'adversaire pour les juges Python : lit une requête JSON par ligne sur l'entrée standard, répond une ligne.
// requête : {id, game:'gomoku'|'hex', obs, legal, ms}  →  réponse : {id, action, quality}
import {gomokuValues} from '../../web/gomoku-engine.js';
import {hexValues} from '../../web/hex-engine.js';
import readline from 'node:readline';
const engines={gomoku:gomokuValues,hex:hexValues};
const rl=readline.createInterface({input:process.stdin});
rl.on('line',line=>{
 let req;try{req=JSON.parse(line);}catch(e){console.log(JSON.stringify({error:'json'}));return;}
 const ms=req.ms??100,t0=performance.now(),budget={nodes:0,tick(){if(this.nodes++>=100000||performance.now()-t0>=ms)throw Error('budget');}};
 try{
  const res=engines[req.game](req.obs,req.legal,budget).action_values;
  let best=res[0];for(const v of res)if(v.quality[0]>best.quality[0])best=v;
  console.log(JSON.stringify({id:req.id,action:best.action,quality:best.quality[0]}));
 }catch(e){console.log(JSON.stringify({id:req.id,error:String(e.message)}));}
});

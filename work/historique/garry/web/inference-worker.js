import {GarryModel,rng} from './engine.js';
import {chooseDecision} from './decision.js';
import {connectReady} from './connect4-runtime.js';
let general=null;
self.onmessage=async e=>{
 const {id,model,observation,legal,level,style,planning,seed}=e.data;
 try{
  await connectReady;
  if(model)general=new GarryModel(model);
  if(!general)throw Error('Garry non initialisé');
  const result=chooseDecision(general.forGame(observation.game),observation,legal,{level,style,planning,random:rng(seed)});
  self.postMessage({id,result});
 }catch(error){self.postMessage({id,error:error.message});}
};

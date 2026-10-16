import {Network,rng} from './engine.js';
import {planDecision} from './planner.js';
const models=new Map();
self.onmessage=e=>{
 const {id,model,observation,legal,level,style,planning,seed}=e.data;
 try{
  if(model)models.set(model.game,new Network(model));
  const network=models.get(observation.game);
  if(!network)throw Error('Modèle non initialisé dans le worker');
  let result=network.choose(observation,legal,level,style,rng(seed));
  if(planning)result=planDecision(observation,legal,network,level,result);
  self.postMessage({id,result});
 }catch(error){self.postMessage({id,error:error.message});}
};

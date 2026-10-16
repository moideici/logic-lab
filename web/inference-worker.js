import {Network,rng} from './engine.js';
import {chooseDecision} from './decision.js';
const models=new Map();
self.onmessage=e=>{
 const {id,model,observation,legal,level,style,planning,seed}=e.data;
 try{
  if(model)models.set(model.game,new Network(model));
  const network=models.get(observation.game);
  if(!network)throw Error('Modèle non initialisé dans le worker');
  const result=chooseDecision(network,observation,legal,{level,style,planning,random:rng(seed)});
  self.postMessage({id,result});
 }catch(error){self.postMessage({id,error:error.message});}
};

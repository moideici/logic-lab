import {Game,GarryModel,NAMES} from './engine.js';
import {teacher} from './teachers.js';
let cancelled=false,busy=false;
self.onmessage=async e=>{
 if(e.data.op==='stop'){cancelled=true;return;}
 if(e.data.op!=='train'||busy)return;
 busy=true;cancelled=false;
 try{
 const general=new GarryModel(e.data.model);
 const models=Object.fromEntries(Object.keys(NAMES).map(g=>[g,general.forGame(g)]));
 const model=models[e.data.game],episodes=e.data.episodes,seed=e.data.seed||0,lr=e.data.lr||.015;
 const others=Object.keys(models).filter(k=>k!==model.game);
 const replay=Object.fromEntries(others.map((k,i)=>[k,new Game(k,seed+i,k==='sliding_puzzle'?{scramble:10}:{})]));
 if(!Number.isInteger(episodes)||episodes<1||episodes>10000)throw Error('Nombre d’épisodes invalide');
 let loss=0,examples=0,completed=0,solved=0,truncated=0,rehearsals=0;const curve=[];
 for(let episode=0;episode<episodes&&!cancelled;episode++){
  const game=new Game(model.game,seed+episode,model.game==='sliding_puzzle'?{scramble:8+episode%12}:{});
  let episodeLoss=0,count=0;
  for(let step=0;step<150&&!game.done&&!cancelled;step++){
   const o=game.obs(),legal=game.legal(),target=teacher(o,legal);
   const l=model.train(o,legal,target,lr);loss+=l;episodeLoss+=l;examples++;count++;
   if(examples%4===0&&others.length){const name=others[rehearsals%others.length];let env=replay[name];if(env.done||env.moves>=100)env=replay[name]=new Game(name,seed+rehearsals,name==='sliding_puzzle'?{scramble:10}:{});const publicObs=env.obs(),moves=env.legal(),target=teacher(publicObs,moves);models[name].train(publicObs,moves,target,lr*.3);env.step(target);rehearsals++;}
   // Mélange de trajectoires du professeur et de l'élève (imitation interactive).
   const action=step%4===3?model.choose(o,legal,8,'balanced',game.random).action:target;
   game.step(action);
   if(step%8===0)await new Promise(r=>setTimeout(r,0));
  }
  if(cancelled)break;
  completed++;if(game.done&&game.winner)solved++;if(!game.done)truncated++;
  curve.push(episodeLoss/Math.max(1,count));
  self.postMessage({type:'progress',episode:completed,episodes,examples,rehearsals,shared_steps:model.core.steps,loss:loss/examples,episode_loss:curve.at(-1),solved,truncated,curve:curve.slice(-80)});
 }
 self.postMessage({type:'finished',model:general.export(),cancelled,completed,examples,rehearsals,loss:examples?loss/examples:0,solved,truncated,curve});
 }catch(error){self.postMessage({type:'error',message:error.message});}
 finally{busy=false;}
};

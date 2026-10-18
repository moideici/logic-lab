import {planDecision} from './planner.js';

// Pipeline commun au worker et à l'API synchrone : un seul passage du réseau
// sur le plateau courant, dont les scores sont réutilisés par la recherche.
export function chooseDecision(model,observation,legal,{level=10,style='balanced',planning=true,random=Math.random}={}){
 if(typeof model.forGame==='function'&&!model.game)model=model.forGame(observation.game);
 const started=performance.now();
 if(typeof planning!=='boolean')throw Error('planning doit être un booléen');
 const logits=model.forward(observation).z;
 let decision=model.choose(observation,legal,level,style,random,logits);
 if(planning)decision=planDecision(observation,legal,model,level,decision,logits);
 decision.info.time_ms=performance.now()-started;
 return decision;
}

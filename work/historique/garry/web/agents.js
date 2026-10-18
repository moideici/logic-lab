import manifest from './agents.json' with {type:'json'};
export const AGENTS=Object.freeze(Object.fromEntries(Object.entries(manifest.agents).map(([game,identity])=>[game,Object.freeze({...identity})])));
export const AGENT_VERSION=manifest.version;
export function agentIdentity(game){if(!AGENTS[game])throw Error('Jeu inconnu');return {...AGENTS[game]};}

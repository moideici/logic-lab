import test from 'node:test';import assert from 'node:assert/strict';
import {gameUiPolicy} from '../web/game-ui-policy.js';
import {GARRY_GAMES} from '../web/engine.js';
test('all fourteen games offer a coherent human or solo mode and independent duel controls',()=>{
 for(const game of GARRY_GAMES){const human=gameUiPolicy({game,mode:'human'}),watch=gameUiPolicy({game});assert.equal(human.showAi,human.multi);assert.equal(human.manualSolo,!human.multi);assert.equal(human.duel,false);assert.equal(watch.duel,watch.multi);assert.equal(watch.showAi,true);if(!human.multi)assert.match(human.humanLabel,/Moi/);}
});
test('the interface suppresses styles when the selected engine cannot apply them',()=>{
 for(const game of ['nim','lightsout'])for(const planning of [false,true])assert.equal(gameUiPolicy({game,planning}).showStyles,false);
 assert.equal(gameUiPolicy({game:'connect4',level:10,levelTwo:10}).showStyles,false);
 assert.equal(gameUiPolicy({game:'connect4',level:10,levelTwo:5}).showStyles,true);
 for(const game of ['sudoku','sliding_puzzle']){assert.equal(gameUiPolicy({game,level:5}).showStyles,false);assert.equal(gameUiPolicy({game,level:10}).showStyles,true);}
 for(const game of ['go','hex','gomoku','draughts','breakthrough','reversi'])assert.equal(gameUiPolicy({game,planning:false}).showStyles,false);
});

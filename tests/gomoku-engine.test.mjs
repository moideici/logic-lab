import test from 'node:test';
import assert from 'node:assert/strict';
import {gomokuValues} from '../web/gomoku-engine.js';
import {newGomoku,legalGomoku} from '../web/gomoku-games.js';
const budget=()=>{const t0=performance.now();return {nodes:0,tick(){if(this.nodes++>=100000||performance.now()-t0>=400)throw Error('budget');}};};
function position(black,white,player){const g=newGomoku();g.state.phase='play';g.state.colors=[1,2];for(const [r,c] of black)g.board[r][c]=1;for(const [r,c] of white)g.board[r][c]=2;
 return {board:g.board,current_player:player,gomoku_state:g.state,done:false,legal:legalGomoku(g.board,g.state)};}
function best(o){const v=gomokuValues(o,o.legal,budget());let b=v.action_values[0];for(const x of v.action_values)if(x.quality[0]>b.quality[0])b=x;return b;}
const at=(a,r,c)=>a.action.row===r&&a.action.col===c;
test('gomoku: takes an immediate exact five',()=>{
 const o=position([[7,3],[7,4],[7,5],[7,6]],[[9,3],[9,4],[9,5],[10,5]],1);
 const b=best(o);assert(at(b,7,2)||at(b,7,7));assert(b.quality[0]>=999000);});
test('gomoku: an overline is not a win, so a six-making cell is not played as a win',()=>{
 // noirs en 7,2..7,5 et 7,7 : 7,6 ferait six, jamais un cinq exact ; le coup gagnant est 7,1 ou aucun
 const o=position([[7,2],[7,3],[7,4],[7,5],[7,7]],[[3,3],[11,11]],1);
 const b=best(o);assert(!at(b,7,6)||b.quality[0]<999000);});
test('gomoku: blocks the only completion of an opponent four',()=>{
 const o=position([[3,3],[11,11]],[[7,3],[7,4],[7,5],[7,6]],1);
 const b=best(o);assert(at(b,7,2)||at(b,7,7));});
test('gomoku: sees a lost position when two completions exist',()=>{
 const o=position([[3,3],[11,11],[1,1]],[[7,4],[7,5],[7,6],[7,7]],1);
 const v=gomokuValues(o,o.legal,budget()).action_values;const m=Math.max(...v.map(x=>x.quality[0]));assert(m<-900000);});
test('gomoku: creates an open four from an open three',()=>{
 const o=position([[7,6],[7,7],[7,8]],[[3,3],[11,11]],1);
 const b=best(o);assert(b.quality[0]>900000);assert([[7,5],[7,9]].some(([r,c])=>at(b,r,c)));});
test('gomoku: finds a forced win by consecutive fours (VCF)',()=>{
 // quatre-trois classique : deux fours consécutifs gagnants depuis un trois en croix
 const o=position([[7,7],[7,8],[7,9],[8,8],[9,8]],[[3,3],[11,11],[6,6]],1);
 const v=gomokuValues(o,o.legal,budget());const b=v.action_values.reduce((a,x)=>x.quality[0]>a.quality[0]?x:a);assert(b.quality[0]>900000,JSON.stringify(b));});
test('gomoku: legal result for every legal action and no mutation of the observation',()=>{
 const o=position([[7,7],[7,8]],[[8,8]],2),before=JSON.stringify(o.board);
 const v=gomokuValues(o,o.legal,budget());assert.equal(v.action_values.length,o.legal.length);assert.equal(JSON.stringify(o.board),before);});

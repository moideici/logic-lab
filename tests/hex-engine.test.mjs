import test from 'node:test';
import assert from 'node:assert/strict';
import {hexValues} from '../web/hex-engine.js';
import {newHex,legalHex} from '../web/hex-games.js';
const budget=()=>{const t0=performance.now();return {nodes:0,tick(){if(this.nodes++>=100000||performance.now()-t0>=400)throw Error('budget');}};};
function position(color1,color2,player,swap=false){const g=newHex();for(const [r,c] of color1)g.board[r][c]=1;for(const [r,c] of color2)g.board[r][c]=2;g.state.swap_available=swap;
 return {board:g.board,current_player:player,hex_state:g.state,done:false,legal:legalHex(g.board,g.state)};}
const best=o=>hexValues(o,o.legal,budget()).action_values.reduce((a,v)=>v.quality[0]>a.quality[0]?v:a);
test('hex: completes an immediate connection',()=>{
 const o=position([[0,3],[1,3],[2,3],[3,3],[4,3],[5,3]],[[0,0],[6,6],[3,0]],1);
 const b=best(o);assert([[6,3],[6,2]].some(([r,c])=>b.action.row===r&&b.action.col===c));assert(b.quality[0]>=99000);});
test('hex: blocks the single completion of an opponent chain',()=>{
 const o=position([[0,0],[2,6]],[[3,0],[3,1],[3,2],[3,3],[3,4],[3,5]],1);
 const b=best(o);assert.deepEqual([b.action.row,b.action.col],[3,6]);});
test('hex: as first player it avoids the centre, which an informed opponent would swap',()=>{
 const o=position([],[],1),v=hexValues(o,o.legal,budget()).action_values.reduce((a,x)=>x.quality[0]>a.quality[0]?x:a);
 assert.notDeepEqual([v.action.row,v.action.col],[3,3]);});
test('hex: the swap action is valued when the pie rule is available',()=>{
 const o=position([[3,3]],[],2,true),v=hexValues(o,o.legal,budget()).action_values.find(x=>x.action.swap);assert(Number.isFinite(v.quality[0]));});
test('hex: every legal action is valued, observation untouched',()=>{
 const o=position([[3,3]],[[2,2]],1),before=JSON.stringify(o.board),v=hexValues(o,o.legal,budget());
 assert.equal(v.action_values.length,o.legal.length);assert.equal(JSON.stringify(o.board),before);});

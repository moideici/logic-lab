import {goCandidate,goGroup,goNeighbors} from './go-games.js';
export function goAiActions(o,legal){
 const s=o.go_state,n=o.board.length,p=o.current_player;
 if(s.phase==='scoring'){
  const disputed=s.dead.some(id=>o.board[Math.floor(id/n)][id%n]===p&&goGroup(o.board,Math.floor(id/n),id%n).liberties.size>=2);
  return legal.filter(a=>disputed?!!a.resume:!!a.accept);
 }
 const placements=legal.filter(a=>'row'in a),pass=legal.find(a=>a.pass);
 // This is the automatic players' analysis budget, not an extra rule of Go.
 // Both still pass normally, then agree the actual area count.
 if(o.moves>=2*n*n||!placements.length)return pass?[pass]:placements;
 const seen=new Set(s.seen),useful=placements.some(a=>{const next=goCandidate(o.board,p,a.row,a.col,seen);if(next.captured)return true;const adj=goNeighbors(n,a.row,a.col);if(adj.every(([r,c])=>o.board[r][c]===p))return false;return goGroup(next.board,a.row,a.col).liberties.size>=2;});
 return useful?placements:pass?[pass]:placements;
}

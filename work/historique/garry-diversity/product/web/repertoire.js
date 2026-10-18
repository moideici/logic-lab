import {Game,SPECS,actionIndex} from './engine.js';

export function parseRepertoire(data){
 if(data?.format!=='garry-repertoire-v1'||!Array.isArray(data.cases)||data.cases.length>20000)throw Error('Répertoire incompatible');
 const groups=new Map(),ids=new Set();
 for(const c of data.cases){
  const o=c?.observation,shape={tictactoe:[3,3],connect4:[6,7],'2048':[4,4],sudoku:[9,9],minesweeper:[8,8],sliding_puzzle:[3,3]}[o?.game];
  if(c.split!=='train')throw Error('Les épreuves réservées aux tests ne peuvent pas entraîner Garry');
  if(!shape||typeof c.id!=='string'||ids.has(c.id)||typeof c.category!=='string'||!c.category||!o||o.done!==false||!Array.isArray(o.board)||o.board.length!==shape[0]||o.board.some(row=>!Array.isArray(row)||row.length!==shape[1]))throw Error('Épreuve invalide');
  const allowed=['game','board','current_player','done','winner','score','moves','givens','history','mine_count'];
  if(Object.keys(o).some(k=>!allowed.includes(k)))throw Error('État privé interdit dans le répertoire');
  const cells=o.board.flat();if(!cells.every(Number.isInteger))throw Error('Plateau invalide');
  const max={tictactoe:2,connect4:2,sudoku:9,minesweeper:8,sliding_puzzle:8}[o.game];
  if(o.game==='2048'?cells.some(v=>v!==0&&(v<2||v>32768||(v&(v-1))!==0)):cells.some(v=>v<(o.game==='minesweeper'?-1:0)||v>max))throw Error('Valeur de case invalide');
  if(o.game==='sliding_puzzle'&&new Set(cells).size!==9)throw Error('Taquin invalide');
  if(o.game==='sudoku'&&(!Array.isArray(o.givens)||o.givens.length!==9||o.givens.some((row,r)=>!Array.isArray(row)||row.length!==9||row.some((v,col)=>!Number.isInteger(v)||v<0||v>9||(v&&o.board[r][col]!==v)))||!Array.isArray(o.history)))throw Error('Indices de sudoku invalides');
  const env=Object.assign(Object.create(Game.prototype),{name:o.game,board:o.board,done:false,history:o.history??[],givens:o.givens});
  const legal=env.legal(),no=SPECS[o.game][1],mask=new Set(legal.map(a=>actionIndex(o.game,a)));
  if(!Array.isArray(c.target)||c.target.length!==no||c.target.some((v,k)=>typeof v!=='number'||!Number.isFinite(v)||v<0||(!mask.has(k)&&v!==0))||Math.abs(c.target.reduce((s,v)=>s+v,0)-1)>1e-5)throw Error('Distribution de coups invalide');
  ids.add(c.id);if(!groups.has(o.game))groups.set(o.game,new Map());const game=groups.get(o.game);if(!game.has(c.category))game.set(c.category,[]);
  game.get(c.category).push({id:c.id,observation:o,legal,target:c.target,category:c.category,hard:!!c.baseline_error});
 }
 return {groups,size:ids.size};
}

export function sampleRepertoire(bank,game,random=Math.random){
 const groups=bank?.groups.get(game);if(!groups?.size)return null;
 const categories=[...groups.keys()],category=categories[Math.min(categories.length-1,Math.floor(random()*categories.length))],all=groups.get(category),hard=all.filter(c=>c.hard);
 const choices=hard.length&&random()<.5?hard:all,c=choices[Math.min(choices.length-1,Math.floor(random()*choices.length))];
 let r=random(),target=c.legal.at(-1);for(const a of c.legal){r-=c.target[actionIndex(game,a)];if(r<0){target=a;break;}}
 return {...c,action:target};
}

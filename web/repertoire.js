import {Game,SPECS,actionIndex} from './engine.js';

export function parseRepertoire(data){
 if(data?.format!=='garry-repertoire-v1'||!Array.isArray(data.cases)||data.cases.length>20000)throw Error('Répertoire incompatible');
 const groups=new Map(),ids=new Set();
 for(const c of data.cases){
  const o=c?.observation,shape={tictactoe:[3,3],connect4:[6,7],'2048':[4,4],sudoku:[9,9],minesweeper:[8,8],sliding_puzzle:[o?.board?.length,o?.board?.length],reversi:[6,6],nim:[3,15],lightsout:[5,5],draughts:[10,10],breakthrough:[8,8],hex:[7,7],gomoku:[15,15],go:[o?.board?.length,o?.board?.length]}[o?.game];
  if(c.split!=='train')throw Error('Les épreuves réservées aux tests ne peuvent pas entraîner Garry');
  if(!shape||typeof c.id!=='string'||ids.has(c.id)||typeof c.category!=='string'||!c.category||!o||o.done!==false||!Array.isArray(o.board)||o.board.length!==shape[0]||o.board.some(row=>!Array.isArray(row)||row.length!==shape[1]))throw Error('Épreuve invalide');
  const allowed=['game','board','current_player','done','winner','score','moves','givens','history','mine_count','draughts_state','hex_state','gomoku_state','difficulty_info','go_state'];
  if(Object.keys(o).some(k=>!allowed.includes(k)))throw Error('État privé interdit dans le répertoire');
  const cells=o.board.flat();if(!cells.every(Number.isInteger))throw Error('Plateau invalide');
  const max={tictactoe:2,connect4:2,sudoku:9,minesweeper:8,sliding_puzzle:o.board.length**2-1,reversi:2,nim:1,lightsout:1,draughts:4,breakthrough:2,hex:2,gomoku:2,go:2}[o.game];
  if(o.game==='2048'?cells.some(v=>v!==0&&(v<2||v>32768||(v&(v-1))!==0)):cells.some(v=>v<(o.game==='minesweeper'?-1:0)||v>max))throw Error('Valeur de case invalide');
  if(o.game==='sliding_puzzle'&&(![3,4,5].includes(o.board.length)||new Set(cells).size!==o.board.length**2))throw Error('Taquin invalide');
  if(o.game==='sudoku'&&(!Array.isArray(o.givens)||o.givens.length!==9||o.givens.some((row,r)=>!Array.isArray(row)||row.length!==9||row.some((v,col)=>!Number.isInteger(v)||v<0||v>9||(v&&o.board[r][col]!==v)))||!Array.isArray(o.history)))throw Error('Indices de sudoku invalides');
  if(![1,2].includes(o.current_player))throw Error('Joueur invalide');
  if(o.game==='draughts'){
   const s=o.draughts_state,coordinate=p=>Array.isArray(p)&&p.length===2&&p.every(v=>Number.isInteger(v)&&v>=0&&v<10)&&(p[0]+p[1])%2===1;
   if(!s||Object.keys(s).some(k=>!['forced_piece','pending_captures','quiet_plies','endgame_16','endgame_5','repetitions'].includes(k))||s.forced_piece!==null&&!coordinate(s.forced_piece)||!Array.isArray(s.pending_captures)||s.pending_captures.length>20||s.pending_captures.some(p=>!coordinate(p))||new Set(s.pending_captures.map(p=>p.join(','))).size!==s.pending_captures.length||!Number.isInteger(s.quiet_plies)||s.quiet_plies<0||s.quiet_plies>50||['endgame_16','endgame_5'].some(k=>s[k]!==null&&(!Number.isInteger(s[k])||s[k]<0||s[k]>32))||!s.repetitions||typeof s.repetitions!=='object'||Array.isArray(s.repetitions)||Object.entries(s.repetitions).some(([k,v])=>!/^[12]:[0-4]{100}$/.test(k)||!Number.isInteger(v)||v<1||v>3)||o.board.some((row,r)=>row.some((v,c)=>v&&(r+c)%2!==1)))throw Error('État public des dames invalide');
  }
  if(o.game==='go'){const s=o.go_state,n=o.board.length;if(![9,13,19].includes(n)||!s||s.size!==n||Object.keys(s).some(k=>!['size','komi','passes','captures','seen','phase','dead','accepted','resume_player','final_score'].includes(k))||typeof s.komi!=='number'||!Number.isFinite(s.komi)||Math.abs(s.komi)>20||![0,1,2].includes(s.passes)||!['play','scoring'].includes(s.phase)||!Array.isArray(s.seen)||s.seen.length>2000||s.seen.some(k=>typeof k!=='string'||k.length!==n*n||/[^012]/.test(k))||!Array.isArray(s.captures)||s.captures.length!==2||s.captures.some(v=>!Number.isInteger(v)||v<0)||!Array.isArray(s.dead)||s.dead.some(i=>!Number.isInteger(i)||i<0||i>=n*n)||!Array.isArray(s.accepted)||s.accepted.some(v=>![1,2].includes(v))||![1,2].includes(s.resume_player)||s.final_score!==null)throw Error('État public de Go invalide');}
  if(o.game==='hex'){const s=o.hex_state,coord=p=>Array.isArray(p)&&p.length===2&&p.every(v=>Number.isInteger(v)&&v>=0&&v<7);if(!s||Object.keys(s).some(k=>!['colors','swap_available','winning_path'].includes(k))||!Array.isArray(s.colors)||s.colors.length!==2||![1,2].includes(s.colors[0])||s.colors[1]!==3-s.colors[0]||typeof s.swap_available!=='boolean'||!Array.isArray(s.winning_path)||s.winning_path.length>49||s.winning_path.some(p=>!coord(p)))throw Error('État Hex invalide');}
  if(o.game==='gomoku'){const s=o.gomoku_state;if(!s||Object.keys(s).some(k=>!['phase','colors','placed','winning_line'].includes(k))||!['opening_three','choose_or_extend','opening_two','choose_color','play'].includes(s.phase)||!Array.isArray(s.colors)||s.colors.length!==2||s.colors.some(v=>![0,1,2].includes(v))||!Number.isInteger(s.placed)||s.placed<0||s.placed>225||!Array.isArray(s.winning_line))throw Error('État Gomoku invalide');}
  const env=Object.assign(Object.create(Game.prototype),{name:o.game,board:o.board,player:o.current_player,goState:o.go_state,hexState:o.hex_state,gomokuState:o.gomoku_state,draughtsState:o.draughts_state,done:false,history:o.history??[],givens:o.givens});
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

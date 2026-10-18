exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
edit('web/app.js',[
("lightsout:'☼'}", "lightsout:'☼',draughts:'◎',breakthrough:'⇧'}"),
("let general=null;", "let general=null,selectedPiece=null;"),
("pause();game=next;sessionId", "pause();game=next;selectedPiece=null;sessionId"),
("if(version===generation&&rev===revision&&!game.done)transition(d.action,d.info);", "if(version===generation&&rev===revision&&!game.done){transition(d.action,d.info);if($('mode').value==='human'&&!game.done&&!humanTurn()&&!running){timer=setTimeout(()=>{if(version===generation&&!humanTurn()&&!game.done&&!running)playOne().catch(errorMessage);},+$('speed').value);}}"),
("function renderBoard(){if(", "function renderBoard(){if(['draughts','breakthrough'].includes(game.name)){renderStrategyBoard();return;}if("),
("const labels=game.name==='reversi'?", "const labels=['draughts','breakthrough'].includes(game.name)?['Blanc','Noir']:game.name==='reversi'?"),
("if(extraHints[game.name])$('game-hint').textContent=extraHints[game.name];", "if(extraHints[game.name])$('game-hint').textContent=extraHints[game.name];if(game.name==='draughts'&&game.draughtsState.forced_piece)$('game-hint').textContent='Rafle en cours : continuez avec le pion sélectionné. Les pièces prises seront retirées à la fin.';"),
("les neuf jeux", "les onze jeux"),
("['tictactoe','connect4','reversi','nim'].includes(id)","['tictactoe','connect4','reversi','nim','draughts','breakthrough'].includes(id)"),
("architecture:[2060,48,48,925]", "architecture:[2494,48,48,3617]"),
("'Lampes éteintes sur 25':'Une victoire vaut un point'", "'Lampes éteintes sur 25':['draughts','breakthrough'].includes(game.name)?'Avantage matériel des blancs':'Une victoire vaut un point'"),
("const extraHints={", "const extraHints={draughts:'Sélectionnez un pion puis sa destination. Prise maximale obligatoire, pions capables de prendre en arrière, dames à longue portée. Blanc commence.',breakthrough:'Sélectionnez un pion puis sa destination. Avancez tout droit ou en diagonale, prenez en diagonale. Atteignez la dernière rangée pour gagner.',")])
p=ROOT/'web/app.js';s=p.read_text(encoding='utf-8');marker='function renderExtraBoard(){'
extra='''function renderStrategyBoard(){
 const board=$('board'),legal=game.legal(),active=humanTurn()&&!game.done,same=(a,b)=>a&&b&&a[0]===b[0]&&a[1]===b[1];
 if(game.name==='draughts'&&game.draughtsState.forced_piece)selectedPiece=game.draughtsState.forced_piece;
 if(selectedPiece&&!legal.some(a=>same(a.from,selectedPiece)))selectedPiece=null;
 board.className='board-'+game.name;board.innerHTML='';
 game.board.forEach((row,r)=>row.forEach((v,c)=>{
  const button=document.createElement('button'),origin=legal.some(a=>same(a.from,[r,c])),dest=selectedPiece&&legal.some(a=>same(a.from,selectedPiece)&&same(a.to,[r,c])),owner=v?(v-1)%2+1:0;
  button.className='cell '+((r+c)%2?'dark-square':'light-square');button.disabled=!active||(!origin&&!dest);
  if(v){button.classList.add('piece'+owner);if(v>2){button.classList.add('crowned');button.textContent='D';}}
  button.classList.toggle('selected-piece',!!same(selectedPiece,[r,c]));if(dest)button.classList.add('legal-destination');else if(origin)button.classList.add('movable-piece');
  if(game.name==='draughts'&&game.draughtsState.pending_captures.some(p=>same(p,[r,c])))button.classList.add('captured-piece');
  if(lastAction?.to&&same(lastAction.to,[r,c]))button.classList.add('last');
  button.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v?(v>2?'dame':'pion')+' '+(owner===1?'blanc':'noir'):'vide'}${dest?', destination possible':''}`);
  button.setAttribute('aria-pressed',String(!!same(selectedPiece,[r,c])));
  button.onclick=()=>{if(!active)return;const action=selectedPiece&&legal.find(a=>same(a.from,selectedPiece)&&same(a.to,[r,c]));if(action){selectedPiece=null;humanAction(action);}else if(origin){selectedPiece=same(selectedPiece,[r,c])?null:[r,c];renderStrategyBoard();}};
  board.append(button);
 }));
 $('game-result').hidden=!game.done;$('game-result').textContent=game.winner===0?'Match nul':$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez gagné !':`Victoire · ${game.winner===1?'Blanc':'Noir'}`;
}
'''
assert marker in s;s=s.replace(marker,extra+marker);p.write_text(s,encoding='utf-8')
p=ROOT/'web/style.css';p.write_text(p.read_text(encoding='utf-8')+'''
.games{grid-template-columns:repeat(auto-fit,minmax(135px,1fr))}
#board.board-draughts,#board.board-breakthrough{display:grid;grid-template-columns:repeat(10,1fr);gap:0;width:min(100%,440px);border:6px solid #315747;border-radius:8px;overflow:hidden}
#board.board-breakthrough{grid-template-columns:repeat(8,1fr);width:min(100%,400px)}
.board-draughts .cell,.board-breakthrough .cell{position:relative;aspect-ratio:1;min-width:0;border:0;border-radius:0;font:700 clamp(13px,2vw,22px) Georgia,serif;isolation:isolate;padding:0}
.board-draughts .light-square,.board-breakthrough .light-square{background:#eee8d2}.board-draughts .dark-square,.board-breakthrough .dark-square{background:#72917a}
.board-draughts .cell:disabled,.board-breakthrough .cell:disabled{opacity:1}
.board-draughts .piece1,.board-breakthrough .piece1{color:#34483b}.board-draughts .piece2,.board-breakthrough .piece2{color:#f4edcf}
.board-draughts .piece1::before,.board-draughts .piece2::before,.board-breakthrough .piece1::before,.board-breakthrough .piece2::before{content:'';position:absolute;inset:12%;border-radius:50%;box-shadow:0 2px 3px #0004;z-index:-1}
.board-draughts .piece1::before,.board-breakthrough .piece1::before{background:#fff9e9;border:2px solid #d5ccb4}.board-draughts .piece2::before,.board-breakthrough .piece2::before{background:#253e36;border:2px solid #112d26}
.board-draughts .crowned::before{outline:2px solid #d0ae59;outline-offset:-5px}
.board-draughts .selected-piece,.board-breakthrough .selected-piece{box-shadow:inset 0 0 0 3px #edce6f}.board-draughts .movable-piece:not(:disabled),.board-breakthrough .movable-piece:not(:disabled){cursor:pointer}
.board-draughts .legal-destination::after,.board-breakthrough .legal-destination::after{content:'';position:absolute;inset:35%;border-radius:50%;background:#eedb73;box-shadow:0 0 0 2px #23423455}
.board-draughts .captured-piece::after{content:'×';position:absolute;inset:0;display:grid;place-items:center;color:#e77552;font-size:30px}
@media(max-width:600px){.games{grid-template-columns:repeat(3,minmax(0,1fr))}.game-card{padding:10px;min-width:0}.game-card strong{font-size:11px}.game-card small{font-size:8px}.board-draughts .cell,.board-breakthrough .cell{font-size:15px}}
''',encoding='utf-8')
print('International draughts and Breakthrough now have selectable pieces, destinations and capture continuations.')

exec((__import__('pathlib').Path(__file__).parent/'install_hex.py').read_text(encoding='utf-8').split('archive=')[0])
edit('web/app.js',[
("breakthrough:'⇧'}", "breakthrough:'⇧',hex:'⬡'}"),
("knownGames.length<11", "knownGames.length<12"),
("function renderBoard(){", "function renderBoard(){if(game.name==='hex'){renderHexBoard();return;}"),
("const extraHints={", "const extraHints={hex:'Bleu relie le haut au bas ; orange relie la gauche à la droite. Après le premier coup, le second joueur peut échanger les couleurs.',"),
("const labels=['draughts','breakthrough'].includes(game.name)?", "const labels=game.name==='hex'?game.hexState.colors.map(c=>c===1?'Bleu · haut / bas':'Orange · gauche / droite'):['draughts','breakthrough'].includes(game.name)?"),
("'draughts','breakthrough'].includes(id)", "'draughts','breakthrough','hex'].includes(id)"),
("architecture:[2494,48,48,3617]", "architecture:[2595,48,48,3667]"),
("les onze jeux", "les douze jeux")])
p=ROOT/'web/app.js';s=p.read_text(encoding='utf-8');marker='function renderStrategyBoard(){'
code='''function renderHexBoard(){
 const board=$('board'),active=humanTurn()&&!game.done,path=game.hexState.winning_path;
 board.className='board-hex';board.innerHTML='';
 const legend=document.createElement('p');legend.className='hex-legend';legend.innerHTML='<span>Bleu ↕</span><span>Orange ↔</span>';board.append(legend);
 const grid=document.createElement('div');grid.className='hex-grid';
 for(let r=0;r<7;r++){const row=document.createElement('div');row.className='hex-row';row.style.setProperty('--row',r);for(let c=0;c<7;c++){
  const v=game.board[r][c],cell=document.createElement('button');cell.className='hex-cell'+(v===1?' hex-blue':v===2?' hex-orange':'');cell.disabled=!active||!!v;cell.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v===1?'bleu':v===2?'orange':'vide'}`);
  if(path.some(p=>p[0]===r&&p[1]===c))cell.classList.add('winning-stone');if(lastAction?.row===r&&lastAction?.col===c)cell.classList.add('hex-last');cell.onclick=()=>humanAction({row:r,col:c});row.append(cell);
 }grid.append(row);}board.append(grid);
 if(game.hexState.swap_available&&!game.done){const swap=document.createElement('button');swap.className='hex-swap';swap.textContent='Échanger les couleurs · premier coup';swap.disabled=!active;swap.onclick=()=>humanAction({swap:true});board.append(swap);}
 $('game-result').hidden=!game.done;const color=game.hexState.colors[(game.winner??1)-1];$('game-result').textContent=$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez relié vos deux bords !':`Connexion gagnante · ${color===1?'Bleu':'Orange'}`;
}
'''
s=s.replace(marker,code+marker);p.write_text(s,encoding='utf-8')
p=ROOT/'web/style.css';p.write_text(p.read_text(encoding='utf-8')+'''
#board.board-hex{width:min(100%,440px);display:block}.hex-legend{display:flex;justify-content:space-between;font:600 13px Arial;margin:0 0 16px}.hex-legend span:first-child{color:#347dab}.hex-legend span:last-child{color:#b8642d}
.hex-grid{padding:7px 0}.hex-grid::before,.hex-grid::after{content:'';display:block;height:4px;width:68.6%;background:#5f9ec3;border-radius:4px;margin-bottom:4px}.hex-grid::after{margin-left:29.4%;margin-top:4px}
.hex-row{display:flex;gap:.1%;padding-left:calc(var(--row)*4.9%);margin-top:-2px}.hex-cell{flex:0 0 9.8%;width:9.8%;aspect-ratio:1.13;border:0;padding:0;clip-path:polygon(25% 0,75% 0,100% 50%,75% 100%,25% 100%,0 50%);background:#ccdbbb;position:relative}
.hex-cell:disabled{opacity:1}.hex-cell:first-child,.hex-cell:last-child{box-shadow:inset 0 0 0 3px #dcaa72}.hex-cell.hex-blue{background:#498db8;box-shadow:inset 0 0 0 3px #286d9b}.hex-cell.hex-orange{background:#da925a;box-shadow:inset 0 0 0 3px #af6834}
.hex-cell:not(:disabled):hover{background:#a9c68d}.hex-last::after{content:'';position:absolute;inset:37%;border-radius:50%;background:#fff5}.hex-cell.winning-stone{filter:brightness(1.25);box-shadow:inset 0 0 0 4px #ffe39b}
.hex-swap{display:block;margin:16px auto 0;padding:10px 16px;border-radius:8px;background:#e7eddc;font-size:12px}
''',encoding='utf-8')
edit('web/index.html',[(a,b) for a,b in [('onze jeux','douze jeux'),('11 jeux','12 jeux'),('11 ENVIRONNEMENTS','12 ENVIRONNEMENTS'),('Onze façons','Douze façons'),('4.0.0','5.0.0'),('2494','2595'),('2 494','2 595'),('3617','3667'),('3 617','3 667'),('299 377','306 675')]])
print('Hex board, ownership swap and live controls installed.')

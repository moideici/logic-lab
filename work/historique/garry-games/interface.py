exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
edit('web/index.html',[(a,b) for a,b in [('six jeux','neuf jeux'),('6 jeux','9 jeux'),('3.2.0','4.0.0'),('1912','2060'),('1 912','2 060'),('818','925'),('134 290','146 637'),('et contraintes/probabilités publiques au démineur','contraintes/probabilités publiques au démineur, recherche au Reversi, calcul exact à Nim et résolution minimale à Lights Out')]])
edit('web/app.js',[
("sliding_puzzle:'▦'}", "sliding_puzzle:'▦',reversi:'◐',nim:'Ⅲ',lightsout:'☼'}"),
("game.multiplayer&&$('mode').value==='human'&&game.player===+$('human-player').value", "$('mode').value==='human'&&(game.multiplayer?game.player===+$('human-player').value:game.name==='lightsout')"),
("function clickCell(r,c){if(!humanTurn()||game.done)return;const action=game.name==='connect4'?{column:c}:{row:r,col:c};try", "function clickCell(r,c){humanAction(game.name==='connect4'?{column:c}:{row:r,col:c});}\nfunction humanAction(action){if(!humanTurn()||game.done)return;try"),
("if(humanTurn())$('game-hint').textContent='À vous de jouer : cliquez sur une case ou une colonne.';", ""),
("function renderBoard(){", "function renderBoard(){if(['reversi','nim','lightsout'].includes(game.name)){renderExtraBoard();return;}"),
("$('mode').options[1].disabled=!multi;if(!multi)$('mode').value='watch';", "$('mode').options[1].disabled=!multi&&game.name!=='lightsout';$('mode').options[1].textContent=game.name==='lightsout'?'Moi · résoudre l’énigme':'Moi contre l’IA';if(!multi&&game.name!=='lightsout')$('mode').value='watch';"),
("function renderControls(){const multi=game.multiplayer;", "function renderControls(){const multi=game.multiplayer;const labels=game.name==='reversi'?['Noir','Blanc']:game.name==='nim'?['Joueur 1','Joueur 2']:['X / rouge','O / jaune'];[...$('human-player').options].forEach((o,i)=>o.textContent=labels[i]);"),
("$('mode').value==='human'?'Reprendre le duel'", "$('mode').value==='human'?(game.multiplayer?'Reprendre le duel':'Reprendre l’énigme')"),
("const label=game.player===1?'X / rouge':'O / jaune';", "const label=labels[game.player-1];"),
(" ;if(!$('planning').checked)", " ;if(extraHints[game.name])$('game-hint').textContent=extraHints[game.name];if(!$('planning').checked)"),
("les six jeux", "les neuf jeux"),
("'Opposé de la distance de Manhattan':'Une victoire vaut un point'", "'Opposé de la distance de Manhattan':game.name==='reversi'?'Pions noirs moins pions blancs':game.name==='nim'?'Allumettes restantes':game.name==='lightsout'?'Lampes éteintes sur 25':'Une victoire vaut un point'"),
("['tictactoe','connect4'].includes(id)?2:1", "['tictactoe','connect4','reversi','nim'].includes(id)?2:1"),
("format:'garry-mlp-v2',architecture:[1912,48,48,818]", "format:'garry-mlp-v3',architecture:[2060,48,48,925]"),
("await persistModels();}}catch{}if(!general)", "await persistModels();}if(stored.version!==AGENT_VERSION)await persistModels();}catch{}if(!general)")])
p=ROOT/'web/app.js';s=p.read_text(encoding='utf-8');marker='function renderGames()'
extra='''const extraHints={reversi:'Encadrez les pions adverses pour les retourner. Noir commence. Si aucun coup n’est possible, passez. Le plus de pions à la fin gagne.',nim:'Retirez une ou plusieurs allumettes d’un seul tas. Celui qui prend la dernière gagne.',lightsout:'Cliquez sur une lampe : elle et ses voisines en croix changent d’état. Éteignez les 25 lampes.'};
function renderExtraBoard(){
 const board=$('board'),legal=game.legal(),canPlay=humanTurn()&&!game.done;
 board.className='board-'+game.name;board.innerHTML='';
 if(game.name==='nim'){
  game.board.forEach((row,pile)=>{
   const count=row.reduce((s,v)=>s+v,0),section=document.createElement('section');section.className='nim-heap';
   const label=document.createElement('strong');label.textContent=`Tas ${pile+1} · ${count} allumette${count>1?'s':''}`;
   const tokens=document.createElement('div');tokens.className='nim-tokens';tokens.setAttribute('aria-hidden','true');
   for(let n=0;n<count;n++){const token=document.createElement('i');tokens.append(token);}
   if(!count)tokens.textContent='Tas vide';
   const actions=document.createElement('div');actions.className='nim-actions';
   for(let take=1;take<=count;take++){const button=document.createElement('button');button.textContent=`−${take}`;button.setAttribute('aria-label',`Retirer ${take} du tas ${pile+1}`);button.disabled=!canPlay;button.onclick=()=>humanAction({pile,take});actions.append(button);}
   section.append(label,tokens,actions);board.append(section);
  });
 }else{
  game.board.forEach((row,r)=>row.forEach((v,c)=>{
   const button=document.createElement('button'),valid=legal.some(a=>a.row===r&&a.col===c);
   button.className='cell';button.disabled=!canPlay||!valid;
   if(game.name==='reversi'){
    if(v)button.classList.add('p'+v);else if(valid)button.classList.add('legal-move');
    button.setAttribute('aria-label',`Ligne ${r+1}, colonne ${c+1} : ${v===1?'noir':v===2?'blanc':valid?'coup possible':'vide'}`);
   }else{button.classList.toggle('light-on',!!v);button.textContent=v?'☼':'·';button.setAttribute('aria-label',`Lampe ${r+1}, ${c+1} : ${v?'allumée':'éteinte'}`);button.setAttribute('aria-pressed',String(!!v));}
   if(lastAction?.row===r&&lastAction?.col===c)button.classList.add('last');
   button.onclick=()=>humanAction({row:r,col:c});board.append(button);
  }));
  if(game.name==='reversi'&&legal.some(a=>a.pass)){const pass=document.createElement('button');pass.className='reversi-pass';pass.textContent='Aucun coup possible · Passer';pass.disabled=!canPlay;pass.onclick=()=>humanAction({pass:true});board.append(pass);}
 }
 $('game-result').hidden=!game.done;
 const labels=game.name==='reversi'?['Noir','Blanc']:['Joueur 1','Joueur 2'];
 $('game-result').textContent=!game.multiplayer?'Toutes les lampes sont éteintes !':game.winner===0?'Match nul':$('mode').value==='human'&&game.winner===+$('human-player').value?'Vous avez gagné !':`Victoire · ${labels[game.winner-1]}`;
}
'''
assert marker in s;s=s.replace(marker,extra+marker);p.write_text(s,encoding='utf-8')
p=ROOT/'web/style.css';p.write_text(p.read_text(encoding='utf-8')+'''
/* Three distinct mechanics, with controls sized for touch and keyboard. */
.board-reversi{display:grid;grid-template-columns:repeat(6,1fr);gap:5px;background:#315e4b;padding:10px;border-radius:16px;width:min(100%,420px);aspect-ratio:1}
.board-reversi .cell{position:relative;background:#4f8668;border-radius:5px;min-width:0;aspect-ratio:1}
.board-reversi .cell.p1::after,.board-reversi .cell.p2::after{content:'';position:absolute;inset:12%;border-radius:50%;box-shadow:0 2px 4px #0004}
.board-reversi .cell.p1::after{background:#142c29}.board-reversi .cell.p2::after{background:#f7f7e9}
.board-reversi .legal-move::before{content:'';position:absolute;inset:39%;border-radius:50%;background:#cfe5ba88}
.reversi-pass{grid-column:1/-1;padding:12px;background:#e4edda;border-radius:8px}
.board-lightsout{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;width:min(100%,400px)}
.board-lightsout .cell{aspect-ratio:1;min-width:0;border-radius:12px;background:#233c38;color:#789183;font-size:clamp(18px,4vw,32px)}
.board-lightsout .cell.light-on{background:#eac768;color:#554615;box-shadow:0 0 15px #eac76844}
.board-nim{display:flex;flex-direction:column;gap:16px;width:min(100%,460px)}
.nim-heap{padding:14px;border:1px solid #d5dfc9;border-radius:12px;min-width:0;text-align:left}.nim-heap strong{font-size:13px}
.nim-tokens{display:flex;align-items:center;gap:8px;min-height:45px;margin:10px 0;color:#76856c;font-size:12px}
.nim-tokens i{display:block;width:7px;height:36px;background:linear-gradient(#c86c4e 0 25%,#d4bc80 25%);border-radius:4px;flex-shrink:1}
.nim-actions{display:flex;flex-wrap:wrap;gap:5px}.nim-actions button{padding:7px 9px;border-radius:6px;background:#e4edda;color:#294936;min-width:34px;min-height:34px}
.nim-actions button:disabled{opacity:.45}.nim-actions button:not(:disabled):hover{background:#bcd591}
.board-reversi .cell:disabled,.board-lightsout .cell:disabled{opacity:1}.board-reversi .cell:not(:disabled):hover{outline:2px solid #e4d787}
@media(max-width:500px){.board-reversi{gap:4px;padding:7px}.board-lightsout{gap:5px}.nim-heap{padding:10px}.nim-tokens{gap:6px}}
''',encoding='utf-8')
print('New boards, human play, rules and nine-game interface installed.')

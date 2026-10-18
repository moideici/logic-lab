from pathlib import Path
root=Path(r'C:\Users\gabor\code\playi');stage=Path(__file__).parent
def edit(name,old,new):
 p=root/name;t=p.read_text(encoding='utf-8')
 if old not in t:raise RuntimeError(f'Expected text absent {name}: {old[:100]}')
 p.write_text(t.replace(old,new),encoding='utf-8')
(root/'web/game-ui-policy.js').write_text((stage/'game-ui-policy.js').read_text(encoding='utf-8'),encoding='utf-8')
edit('web/index.html','<div class="label-row"><label for="level"','<div id="ai-controls"><div class="label-row"><label for="level"')
edit('web/index.html','<label class="field-label" for="style">','<div id="style-options"><label class="field-label" for="style">')
edit('web/index.html','</select><p class="fine-print">Le style change les préférences stratégiques. Une victoire prouvée ou une défense nécessaire reste prioritaire.</p>','</select></div><p id="style-note" class="fine-print"></p>')
edit('web/index.html','<div class="control-divider"></div><div class="network-head">','</div><div class="control-divider"></div><div class="network-head">')
edit('web/index.html','</div></div><div class="play-toolbar"><button id="play"','</div></div><div id="manual-actions" class="manual-actions" hidden></div><div class="play-toolbar"><button id="play"')
edit('web/app.js',"import {AGENTS,", "import {gameUiPolicy} from './game-ui-policy.js';\nimport {AGENTS,")
edit('web/app.js',"game.player===+$('human-player').value:['lightsout','sudoku','sliding_puzzle'].includes(game.name)","game.player===+$('human-player').value:true")
p=root/'web/app.js';t=p.read_text(encoding='utf-8');a=t.index('function renderControls(){');b=t.index('function renderNetwork(){',a);t=t[:a]+(stage/'render_controls.txt').read_text(encoding='utf-8')+t[b:];p.write_text(t,encoding='utf-8')
edit('web/app.js',"function start(){if(game.done)","function start(){if($('mode').value==='human'){playOne().catch(errorMessage);return;}if(game.done)")
edit('web/app.js',"rev=revision,d=await decideAsync();if(version===generation", "rev=revision,promise=decideAsync();renderControls();let d;try{d=await promise;}finally{renderControls();}if(version===generation")
edit('web/app.js',"cell.disabled=!humanTurn()||game.done;cell.setAttribute", "cell.disabled=!humanTurn()||game.done||game.name==='2048'||!game.legal().some(a=>game.name==='connect4'?a.column===c:a.row===r&&a.col===c);cell.setAttribute")
edit('web/app.js',"function render(){renderGames();renderControls();renderBoard();renderNetwork();}","function render(){renderGames();renderControls();renderBoard();renderManualActions();renderNetwork();}")
edit('web/app.js',"training-status').textContent='Apprentissage en cours · répétition inter-jeux activée.';renderGames();", "training-status').textContent='Apprentissage en cours · répétition inter-jeux activée.';render();")
edit('web/app.js',"$('model-reset').disabled=false;renderGames();}","$('model-reset').disabled=false;render();}")
edit('web/app.js',"$('level').value}<span> / 10</span>`;};", "$('level').value}<span> / 10</span>`;renderControls();};")
edit('web/app.js',"$('level-two').value}<span> / 10</span>`;};", "$('level-two').value}<span> / 10</span>`;renderControls();};")
edit('web/app.js',"toast('Garry initial a été restauré.');", "toast('Derniers poids fournis par le serveur restaurés.');")
edit('web/index.html','Restaurer le réseau initial ↻','Charger les poids du serveur ↻')
manual='''
function renderManualActions(){
 const el=$('manual-actions');el.hidden=game.name!=='2048'||!humanTurn()||game.done;el.replaceChildren();if(el.hidden)return;
 const legal=game.legal();for(const [direction,label]of [['up','↑ Haut'],['left','← Gauche'],['down','↓ Bas'],['right','→ Droite']]){
  const button=document.createElement('button');button.className='button secondary';button.textContent=label;button.setAttribute('aria-label',`Déplacer vers ${label.slice(2).toLowerCase()}`);button.disabled=!legal.some(a=>a.direction===direction);button.onclick=()=>humanAction({direction});el.append(button);
 }
}
window.addEventListener('keydown',event=>{
 if(game.name!=='2048'||!humanTurn()||game.done||event.defaultPrevented||event.altKey||event.ctrlKey||event.metaKey||event.target.closest?.('input,select,textarea,[contenteditable="true"]')||document.querySelector('dialog[open]'))return;
 const direction={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right'}[event.key];if(!direction)return;event.preventDefault();if(game.legal().some(a=>a.direction===direction))humanAction({direction});
});
'''
p=root/'web/app.js';p.write_text(p.read_text(encoding='utf-8')+manual,encoding='utf-8')
edit('web/puzzle-ui.js',"undo.disabled=game.done||!game.history.length;", "undo.disabled=game.done||!legal.some(a=>a.undo);undo.title=undo.disabled?'Aucune saisie à annuler.':'Annuler la dernière saisie';")
edit('web/go-ui.js',"actions.className='go-actions';", "actions.className='go-actions';actions.hidden=!human||game.done;")
edit('web/app.js',"if(game.name==='reversi'&&legal.some(a=>a.pass))", "if(game.name==='reversi'&&canPlay&&legal.some(a=>a.pass))")
edit('web/app.js',"actions.className='nim-actions';", "actions.className='nim-actions';actions.hidden=!canPlay;")
css=root/'web/style.css';css.write_text(css.read_text(encoding='utf-8')+'\n.manual-actions{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;padding:0 15px 18px}.manual-actions .button{min-width:94px}.nav{font-family:inherit}\n',encoding='utf-8')
print('Contrôles et jeu manuel cohérents installés.')

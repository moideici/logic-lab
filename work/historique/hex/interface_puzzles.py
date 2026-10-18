from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
shutil.copyfile(S/'puzzle-ui.js',R/'web/puzzle-ui.js')
def edit(file,old,new):
 p=R/file;t=p.read_text(encoding='utf-8');assert old in t,(file,old[:100]);p.write_text(t.replace(old,new,1),encoding='utf-8')
p=R/'web/app.js';t=p.read_text(encoding='utf-8');t=t.replace("!multi&&game.name!=='lightsout'","!multi&&!['lightsout','sudoku','sliding_puzzle'].includes(game.name)").replace("game.name==='lightsout'?'Moi · résoudre l’énigme'","['lightsout','sudoku','sliding_puzzle'].includes(game.name)?'Moi · résoudre l’énigme'")
needle="if(!$('planning').checked)$('game-hint').textContent=";t=t.replace(needle,"renderPuzzleControls(game,humanTurn(),training,lastDecision);"+needle,1)
t+="\nfor(const id of ['sudoku-difficulty','sliding-size','sliding-difficulty'])$(id).onchange=()=>{try{newGame();}catch(error){errorMessage(error);}};\n";p.write_text(t,encoding='utf-8')
levels=''.join(f'<option value="{k}">{v}</option>' for k,v in [('easy','Facile'),('medium','Moyen'),('hard','Difficile'),('expert','Expert')]).replace('value="medium"','value="medium" selected')
html=f'''<div id="sudoku-options" hidden><label class="field-label" for="sudoku-difficulty">DIFFICULTÉ DE LA GRILLE</label><select id="sudoku-difficulty">{levels}</select></div><div id="sliding-options" hidden><label class="field-label" for="sliding-size">TAILLE DU TAQUIN</label><select id="sliding-size"><option value="3">3 × 3 · 8 tuiles</option><option value="4">4 × 4 · 15 tuiles</option><option value="5">5 × 5 · 24 tuiles</option></select><label class="field-label" for="sliding-difficulty">DIFFICULTÉ DE LA GRILLE</label><select id="sliding-difficulty">{levels}</select></div>'''
edit('web/index.html','<div class="control-divider"></div><div class="label-row">',html+'<div class="control-divider"></div><div class="label-row">')
edit('web/index.html','Le minimum de coups est garanti au taquin','Le minimum de coups est garanti au taquin 3 × 3')
p=R/'web/style.css'
if not p.exists():p=R/'web/styles.css'
with p.open('a',encoding='utf-8') as f:f.write('''\n.puzzle-container{width:min(100%,430px);display:flex;flex-direction:column;gap:18px}.puzzle-grid{display:grid;width:100%;aspect-ratio:1;gap:4px}.puzzle-grid .cell{min-width:0;min-height:0;aspect-ratio:1;font-size:clamp(16px,3vw,29px);padding:0;border-radius:7px}.puzzle-grid .blank{background:transparent;box-shadow:none}.sudoku-grid{gap:0;border:2px solid #637253}.sudoku-grid .cell{border-radius:0;border:1px solid #d9decd;font-size:clamp(14px,2vw,22px)}.sudoku-grid .box-right{border-right:3px solid #637253}.sudoku-grid .box-bottom{border-bottom:3px solid #637253}.sudoku-grid .given{font-weight:800;background:#e5eadc}.sudoku-grid .selected-cell{background:#bdd697;outline:2px solid #426526;outline-offset:-2px}.puzzle-digits{display:flex;gap:5px;flex-wrap:wrap}.puzzle-digits button{min-width:30px;padding:9px;border:1px solid #bac7a7;border-radius:6px;background:#edf2e5}.puzzle-digits button:disabled{opacity:.35}.puzzle-digits button:not(:disabled){cursor:pointer}\n''')
# Public teacher handles large grids without using an old 3x3 search.
edit('logic_arena/agents.py','    def sliding(self, obs, actions, budget, fallback):', '''    def sliding(self, obs, actions, budget, fallback):
        if len(obs['board'])>3:
            from .large_sliding import large_sliding_values
            values,info=large_sliding_values(obs,actions,budget)
            return max(values,key=lambda v:v['quality'])['action'],info''')
edit('logic_arena/diversity.py',"    elif game=='sliding_puzzle':", "    elif game=='sliding_puzzle' and len(obs['board'])>3:\n        from .large_sliding import large_sliding_values\n        values,info=large_sliding_values(obs,legal,Budget(nodes,10000));info.update(category='large_grid',exact=False)\n    elif game=='sliding_puzzle':")
print('Puzzle interface installed')

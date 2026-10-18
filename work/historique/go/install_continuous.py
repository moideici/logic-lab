from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\playi');S=Path(__file__).parent
for name in ('continuous.py','continuous_service.py'):shutil.copyfile(S/name,R/'logic_arena'/name)
shutil.copyfile(S/'continuous-ui.js',R/'web/continuous-ui.js')
def edit(file,old,new):
 p=R/file;t=p.read_text(encoding='utf-8');assert old in t,(file,old[:90]);p.write_text(t.replace(old,new,1),encoding='utf-8')
edit('logic_arena/server.py','EXTERNAL=ExternalArena()','EXTERNAL=ExternalArena()\nfrom .continuous_service import ContinuousTraining\nCONTINUOUS=ContinuousTraining()')
edit('logic_arena/server.py',"        if urlparse(self.path).path.startswith('/api/external/'):","""        if urlparse(self.path).path.startswith('/api/continuous/'):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=4096:raise ValueError('Taille JSON invalide')
                data=json_line(self.rfile.read(size).decode('utf-8'));op=urlparse(self.path).path.rsplit('/',1)[-1]
                if not isinstance(data,dict):raise ValueError('Objet JSON requis')
                if op=='start' and set(data)<={'seconds'}:result=CONTINUOUS.start(data.get('seconds',3600))
                elif op=='stop' and set(data)=={'id'}:result=CONTINUOUS.stop(data['id'])
                else:raise ValueError('Opération continue invalide')
                self.send_json({'ok':True,'result':result})
            except (ValueError,TypeError,UnicodeError) as error:self.send_json({'ok':False,'error':str(error)},400)
            return
        if urlparse(self.path).path.startswith('/api/external/'):""")
edit('logic_arena/server.py','        parsed = urlparse(self.path)','''        parsed = urlparse(self.path)
        if parsed.path=='/api/continuous/status':
            self.send_json({'ok':True,'result':CONTINUOUS.get()});return''')
html='''<section class="continuous-panel"><div class="panel-head"><div><p class="eyebrow" id="continuous-live">ENTRAÎNEMENT CONTINU</p><h2 id="continuous-game">Garry en direct</h2><p id="continuous-status" role="status">Prêt pour une heure d’apprentissage.</p></div><strong id="continuous-remaining">60 min</strong></div><div class="continuous-layout"><div id="continuous-board" class="continuous-board" aria-label="Plateau de la partie d’apprentissage en direct"></div><div class="continuous-statistics"><p><strong id="continuous-moves">0</strong> coups joués</p><p id="continuous-rate">0 coups/s</p><p><strong id="continuous-samples">0</strong> nouvelles épreuves</p><p><strong id="continuous-promotions">0</strong> candidats retenus</p><p id="continuous-evaluation">Les candidats sont contrôlés sur des épreuves séparées avant de remplacer les poids.</p><button id="continuous-start" class="button primary">Lancer une heure</button><button id="continuous-stop" class="button secondary" disabled>Arrêter</button><button id="continuous-reload" class="text-button" hidden>Charger les derniers poids dans l’arène ↻</button></div></div><progress id="continuous-progress" value="0" max="3600"></progress><p class="fine-print">Le calcul continue si vous changez d’onglet ou fermez cette page. Le serveur et l’ordinateur doivent rester allumés. Le plateau montre les coups effectivement calculés ; les contrôles mesurent l’accord avec un professeur borné.</p></section>'''
edit('web/index.html','<section id="training-tab" class="tab-panel" hidden>','<section id="training-tab" class="tab-panel" hidden>'+html)
edit('web/index.html','<script type="module" src="external-ui.js"></script>','<script type="module" src="external-ui.js"></script><script type="module" src="continuous-ui.js"></script>')
edit('web/index.html','<label for="level">Niveau de jeu</label>','<label for="level" id="level-title">Niveau de jeu</label>')
edit('web/index.html','<label class="field-label" for="style">','<div id="level-two-options" hidden><div class="label-row"><label for="level-two">Niveau IA 2</label><strong id="level-two-label">10<span> / 10</span></strong></div><input id="level-two" type="range" min="0" max="10" step="1" value="10"></div><label class="field-label" for="style">')
p=R/'web/app.js';t=p.read_text(encoding='utf-8').replace("config.level??+$('level').value","config.level??effectiveLevel()");t=t.replace("const current=()=>models[game.name];","const current=()=>models[game.name];\nconst effectiveLevel=()=>game.multiplayer&&$('mode').value==='watch'&&game.player===2?+$('level-two').value:+$('level').value;")
t=t.replace("function renderControls(){const multi=game.multiplayer;","function renderControls(){const multi=game.multiplayer;const duel=multi&&$('mode').value==='watch';$('level-two-options').hidden=!duel;$('level-title').textContent=duel?'Niveau IA 1':'Niveau de jeu';")
t+="\n$('level-two').oninput=()=>{$('level-two-label').innerHTML=`${$('level-two').value}<span> / 10</span>`;};\nwindow.addEventListener('garry-load-server-model',async()=>{try{if(training)throw Error('Arrêtez l’entraînement du navigateur avant de charger les poids');pause();const response=await fetch('models/garry.json',{cache:'no-store'});useGarry(await response.json());await persistModels();lastDecision=null;render();toast('Derniers poids du serveur chargés.');}catch(e){errorMessage(e);}});\n";p.write_text(t,encoding='utf-8')
with (R/'web/style.css').open('a',encoding='utf-8')as f:f.write('''\n.continuous-panel{background:var(--white);border:1px solid var(--line);border-radius:14px;padding:25px;margin-bottom:30px}.continuous-layout{display:grid;grid-template-columns:minmax(180px,460px) 1fr;gap:35px;align-items:start}.continuous-board{display:grid;aspect-ratio:1;width:100%;background:#dbbf8d;padding:7px;border:2px solid #9d8359;gap:0}.continuous-cell{position:relative;aspect-ratio:1;background:linear-gradient(90deg,transparent 48%,#9c8154 49% 51%,transparent 52%),linear-gradient(transparent 48%,#9c8154 49% 51%,transparent 52%)}.continuous-cell.stone-1::before,.continuous-cell.stone-2::before{content:'';position:absolute;inset:6%;border-radius:50%;background:#223830}.continuous-cell.stone-2::before{background:#fffaf0;box-shadow:0 1px 2px #0004}.continuous-last::after{content:'';position:absolute;inset:32%;border:2px solid #e6964f;border-radius:50%}.continuous-statistics p{line-height:1.5}.continuous-statistics strong{font-size:25px}.continuous-statistics .button{margin:5px}.continuous-panel progress{width:100%;margin-top:20px;accent-color:#80a95d}.continuous-hex .continuous-cell{background:#eadbc1}.continuous-hex .stone-1::before{background:#498db8}.continuous-hex .stone-2::before{background:#d48c54}@media(max-width:650px){.continuous-layout{grid-template-columns:1fr}.continuous-panel{padding:16px}}\n''')
print('Live training and separate duel levels installed')

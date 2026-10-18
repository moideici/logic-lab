from pathlib import Path
import shutil
ROOT=Path(r'C:\Users\gabor\code\playi');HERE=Path(__file__).parent
shutil.copy2(HERE/'external.py',ROOT/'logic_arena/external.py');shutil.copy2(HERE/'external-ui.js',ROOT/'web/external-ui.js')
p=ROOT/'logic_arena/server.py';s=p.read_text(encoding='utf-8');s=s.replace('from .harness import Arena, json_line','from .harness import Arena, json_line\nfrom .external import ExternalArena\nEXTERNAL=ExternalArena()')
s=s.replace('    def do_POST(self):\n', '''    def do_POST(self):
        if urlparse(self.path).path.startswith('/api/external/'):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=4096:raise ValueError('Taille JSON invalide')
                data=json_line(self.rfile.read(size).decode('utf-8'));op=urlparse(self.path).path.rsplit('/',1)[-1]
                if op=='start':result=EXTERNAL.start(data)
                elif op=='stop' and isinstance(data,dict):result=EXTERNAL.stop(data.get('id'))
                else:raise ValueError('Opération externe inconnue')
                self.send_json({'ok':True,'result':result})
            except (ValueError,TypeError,UnicodeError) as error:self.send_json({'ok':False,'error':str(error)},400)
            return
''')
s=s.replace('        parts = parsed.path.strip("/").split("/")', '''        if parsed.path.startswith('/api/external/'):
            try:
                op=parsed.path.rsplit('/',1)[-1];identifier=parse_qs(parsed.query).get('id',[''])[0]
                if op=='list':self.send_json({'ok':True,'result':EXTERNAL.list()});return
                if op=='status':self.send_json({'ok':True,'result':EXTERNAL.get(identifier)});return
                if op in ('image','trace'):
                    path=EXTERNAL.image(identifier) if op=='image' else EXTERNAL._path(identifier)/'trace.jsonl'
                    if not path.is_file():self.send_json({'ok':False,'error':'Partie en préparation'},404);return
                    raw=path.read_bytes();self.send_response(200);self.send_header('Content-Type','image/png' if op=='image' else 'application/x-ndjson');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw);return
                raise ValueError('Opération externe inconnue')
            except (ValueError,OSError) as error:self.send_json({'ok':False,'error':str(error)},400)
            return
        parts = parsed.path.strip("/").split("/")''')
p.write_text(s,encoding='utf-8')
p=ROOT/'web/index.html';s=p.read_text(encoding='utf-8');s=s.replace('</nav><div class="rail-bottom">','<button data-tab="external" class="nav" title="Jeux réels"><span>↗</span><small>Jeux réels</small></button></nav><div class="rail-bottom">')
panel='''<section id="external-tab" class="tab-panel" hidden><div class="external-layout"><section class="play-panel"><div class="panel-head"><div><p class="eyebrow">JOUER SUR LE VRAI SITE</p><h2>2048 original</h2><p>Garry utilise les flèches du clavier sur <a href="https://classic.play2048.co/" target="_blank" rel="noopener">le site original ↗</a>.</p></div></div><div class="external-preview"><img id="external-image" alt="Capture du vrai plateau 2048" hidden><p id="external-status" role="status">Prêt à ouvrir une partie sur le site original.</p></div><div class="play-toolbar"><label for="external-mode">Joueur</label><select id="external-mode"><option value="garry">Garry · réseau et recherche</option><option value="network">Garry · réseau seul</option><option value="random">Référence aléatoire</option></select><button id="external-start" class="button primary">Lancer sur le vrai site ↗</button><button id="external-stop" class="button secondary" disabled>Arrêter</button></div><p class="game-hint">Le navigateur lit les tuiles visibles et le score du site. Il ne modifie ni le plateau ni les apparitions aléatoires. Garry continue après 2048 pour viser le meilleur score.</p></section><aside class="controls"><h3>Mesurer ses progrès</h3><div class="external-stat"><small>SCORE DU SITE</small><strong id="external-score">0</strong></div><div class="external-stat"><small>MEILLEURE TUILE</small><strong id="external-tile">0</strong></div><div class="external-stat"><small>COUPS JOUÉS</small><strong id="external-steps">0</strong></div><p id="external-verified">0 transitions vérifiées</p><div class="control-divider"></div><div class="external-stat"><small>ACCORD AVEC L’ANALYSE APPROFONDIE</small><strong id="external-agreement">—</strong></div><div class="external-stat"><small>ÉCART MOYEN D’ÉVALUATION</small><strong id="external-regret">—</strong></div><p class="fine-print">Une sonde tous les 25 coups compare Garry à une recherche plus longue. C’est une estimation des erreurs de choix, sans promesse de gain de score. Les parties ont des tirages différents.</p><a id="external-record" class="text-button" href="#" target="_blank">Ouvrir la trace des coups ↗</a></aside></div><section class="event-panel"><div class="event-head"><h3>Parties sur le site original</h3></div><div id="external-history"></div></section></section>
'''
s=s.replace('<footer>',panel+'<footer>').replace('<script type="module" src="app.js"></script>','<script type="module" src="app.js"></script><script type="module" src="external-ui.js"></script>');p.write_text(s,encoding='utf-8')
p=ROOT/'web/style.css';p.write_text(p.read_text(encoding='utf-8')+'''
.external-layout{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:22px}.external-preview{text-align:center;padding:24px}.external-preview img{max-width:100%;width:420px;border-radius:8px}.external-stat{padding:13px 0}.external-stat small{display:block;font:9px var(--mono);color:var(--muted);line-height:1.6}.external-stat strong{display:block;font-size:28px;font-weight:400;margin-top:8px}.external-history-row{display:block;width:100%;padding:13px 20px;text-align:left;border-width:0 0 1px;font-size:12px}.external-layout .play-toolbar{flex-wrap:wrap}.external-layout select{max-width:100%;padding:9px;border-radius:7px}
@media(max-width:850px){.external-layout{grid-template-columns:1fr}.external-layout .play-toolbar{padding:16px;gap:10px}.external-layout .button{font-size:11px}}
''',encoding='utf-8')
p=ROOT/'.gitignore';s=p.read_text(encoding='utf-8');s+='\n# Local browser adapter dependencies\nnode_modules/\n';p.write_text(s,encoding='utf-8')
print('Real-game API and dashboard installed; browser jobs are limited to the original 2048 site.')

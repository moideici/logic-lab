from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
for f in ('bilan.html','bilan.css','bilan.js'):shutil.copyfile(S/f,R/'web'/f)
p=R/'web/input.html';t=p.read_text(encoding='utf-8').replace('<div class="header-meta">','<div class="header-meta"><a href="/bilan">Bilan d’apprentissage ↗</a>').replace('<div class="principles">','<a class="secondary" href="/bilan" style="display:inline-block;margin:12px 0">Voir le bilan d’apprentissage ↗</a><div class="principles">');p.write_text(t,encoding='utf-8')
p=R/'serve.py';t=p.read_text(encoding='utf-8').replace("static={'/':", "static={'/bilan':('bilan.html','text/html'),'/bilan.css':('bilan.css','text/css'),'/bilan.js':('bilan.js','text/javascript'),'/':");p.write_text(t,encoding='utf-8')
print('Training report page installed')

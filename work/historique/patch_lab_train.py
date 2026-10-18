"""Ajoute la section « Entraînement en direct » à lab.html et ses styles à lab.css."""
from pathlib import Path

web = Path(r"C:\Users\gabor\code\logic-lab\projets\garry\web")
section = """
<section class="lab-card train-card"><div class="card-head"><h2>Entraînement en direct</h2><p>Un petit réseau apprend à jouer comme le professeur. En mode <b>Graine</b>, il commence à 2 + 2 neurones, en gagne quand il stagne et en perd quand ils ne servent à rien. Comparez avec un réseau de taille fixe.</p></div>
<div class="lab-bar train-bar"><label>Jeu <select id="train-game"><option value="tictactoe">tictactoe</option><option value="nim">nim</option><option value="connect4">connect4</option></select></label>
<label>Réseau <select id="train-mode"><option value="graine-A">Graine A · prudente</option><option value="graine-B" selected>Graine B · croît vite, élague à la fin</option><option value="graine-C">Graine C · croît seule</option><option value="fixe-4">Fixe 4 + 4</option><option value="fixe-8">Fixe 8 + 8</option><option value="fixe-16">Fixe 16 + 16</option><option value="fixe-48">Fixe 48 + 48</option></select></label>
<label>Pas <input id="train-steps" type="number" min="200" max="20000" step="100" value="3000"></label>
<button id="train-start" class="button primary">Lancer</button><button id="train-stop" class="button" disabled>Arrêter</button></div>
<p id="train-status" class="muted">Aucun entraînement.</p>
<div class="train-grid"><svg id="train-net" viewBox="0 0 380 300" role="img" aria-label="Réseau en cours d'entraînement"></svg><svg id="train-chart" viewBox="0 0 380 300" role="img" aria-label="Accord avec le professeur et taille du réseau au fil des pas"></svg></div>
<ul id="train-events" class="events"></ul>
<h3>Comparaison des entraînements de cette session</h3><table id="train-compare" class="compare"><thead><tr><th>Jeu</th><th>Réseau</th><th>Tailles</th><th>Paramètres</th><th>Accord (test)</th></tr></thead><tbody></tbody></table>
<p class="muted">Accord = part des positions de test où le réseau choisit le coup du professeur. Positions de test jamais vues à l'entraînement.</p></section>
"""
h = (web / "lab.html").read_text(encoding="utf-8")
if "train-card" not in h:
    marker = "</main>"
    h = h.replace(marker, section + marker, 1)
    h = h.replace('<script type="module" src="lab.js"></script>', '<script type="module" src="lab.js"></script>\n<script type="module" src="lab-train.js"></script>', 1)
    (web / "lab.html").write_text(h, encoding="utf-8", newline="")
c = (web / "lab.css").read_text(encoding="utf-8")
if "train-grid" not in c:
    c += """
.train-card{margin-top:18px}.train-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px}.train-card svg{width:100%;height:auto;display:block;background:#fbfbf7;border:1px solid var(--line);border-radius:10px}
.events{list-style:none;margin:10px 0 0;padding:0;font-size:12px;color:var(--muted);max-height:120px;overflow:auto}.events li{padding:2px 0}.events .grow{color:#3d7a52}.events .cut{color:var(--orange)}
.compare{width:100%;border-collapse:collapse;font-size:13px}.compare th,.compare td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}.train-bar{margin:10px 0}
@media(max-width:900px){.train-grid{grid-template-columns:1fr}}
"""
    (web / "lab.css").write_text(c, encoding="utf-8", newline="")
print("ok")

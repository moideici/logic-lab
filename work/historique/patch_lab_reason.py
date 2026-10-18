"""Ajoute la section « Réflexion en direct » (Loop, sudoku 6×6) à lab.html et lab.css."""
from pathlib import Path

web = Path(r"C:\Users\gabor\code\logic-lab\projets\garry\web")
section = """
<section class="lab-card reason-card"><div class="card-head"><h2>Réflexion en direct · Loop</h2><p>Un petit réseau récurrent, entraîné de zéro, résout un sudoku 6×6. À chaque passe il propose une grille ; la couleur dit si la case est juste, l'opacité dit sa confiance. Plus le problème est dur, plus il lui faut de passes.</p><p id="reason-info" class="muted"></p></div>
<div class="lab-bar train-bar"><label>Cases vides <span id="reason-empties-v">20</span><input id="reason-empties" type="range" min="6" max="27" value="20"></label>
<label>Graine <input id="reason-seed" type="number" min="0" max="999999999" value="1"></label>
<label>Passes <select id="reason-passes"><option>8</option><option selected>16</option><option>32</option></select></label>
<button id="reason-new" class="button">Nouveau problème</button><button id="reason-think" class="button primary">Faire réfléchir</button></div>
<p id="reason-status" class="muted">…</p>
<div class="train-grid"><div id="reason-grid" class="rgrid" aria-label="Grille de sudoku 6 par 6"></div><div><svg id="reason-chart" viewBox="0 0 380 150" role="img" aria-label="Cases fausses à chaque passe"></svg>
<div class="player"><button id="reason-play" class="button" disabled>▶ Rejouer</button><input id="reason-slider" type="range" min="1" max="16" value="1" disabled aria-label="Passe affichée"></div>
<p class="muted">Vert = case juste, orange = case fausse (par rapport à la solution unique). Cliquer une barre affiche cette passe.</p></div></div></section>
"""
h = (web / "lab.html").read_text(encoding="utf-8")
if "reason-card" not in h:
    h = h.replace("</main>", section + "</main>", 1)
    h = h.replace('<script type="module" src="lab-train.js"></script>', '<script type="module" src="lab-train.js"></script>\n<script type="module" src="lab-reason.js"></script>', 1)
    (web / "lab.html").write_text(h, encoding="utf-8", newline="")
c = (web / "lab.css").read_text(encoding="utf-8")
if "rgrid" not in c:
    c += """
.reason-card{margin-top:18px}.rgrid{display:grid;grid-template-columns:repeat(6,1fr);width:min(100%,340px);aspect-ratio:1;border:2px solid var(--dark);border-radius:6px;overflow:hidden;background:#fff}
.rc{display:flex;align-items:center;justify-content:center;font-size:clamp(16px,4vw,26px);border:1px solid var(--line);font-variant-numeric:tabular-nums}.rc.rb{border-top:2px solid var(--dark)}.rc.cb{border-right:2px solid var(--dark)}.rc:nth-child(6n){border-right:1px solid var(--line)}.rc.cb:nth-child(6n){border-right:1px solid var(--line)}
.rc.given{font-weight:800;color:var(--ink);background:#f1f4ea}.rc.ok{color:#2f7a4a}.rc.bad{color:#c25a2a;background:#fbefe8}.player{display:flex;gap:10px;align-items:center;margin:8px 0}.player input{flex:1}
.reason-bar label{display:grid;gap:4px}
"""
    (web / "lab.css").write_text(c, encoding="utf-8", newline="")
print("ok")

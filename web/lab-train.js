const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
const svgEl = (tag, attrs = {}, text) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (text !== undefined) e.textContent = text; return e; };
const api = async (path, body) => {
  const r = await fetch(path, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || 'Erreur');
  return j.result;
};
let timer = null;
const color = v => { const a = Math.min(1, Math.abs(v)); return v >= 0 ? `rgba(25,90,70,${0.12 + 0.88 * a})` : `rgba(223,128,86,${0.12 + 0.88 * a})`; };

function drawNet(s) {
  const svg = $('train-net'); svg.replaceChildren();
  const acts = s.activations || {}, sizes = s.tailles || [0, 0];
  svg.append(svgEl('text', { x: 14, y: 20, 'font-size': 11, fill: '#7a8580' }, `Encodeur · ${sizes[0]}`), svgEl('text', { x: 200, y: 20, 'font-size': 11, fill: '#7a8580' }, `Cœur · ${sizes[1]}`));
  [['encodeur', 14], ['coeur', 200]].forEach(([layer, x0]) => {
    const a = acts[layer] || [];
    const cols = Math.min(8, Math.max(2, Math.ceil(Math.sqrt(a.length || 1)))), gap = Math.min(20, 160 / cols);
    a.forEach((v, i) => svg.append(svgEl('circle', { cx: x0 + 10 + (i % cols) * gap, cy: 42 + Math.floor(i / cols) * gap, r: Math.min(8, gap / 2 - 1), fill: color(v), stroke: '#c9d2c4' })));
  });
  svg.append(svgEl('text', { x: 14, y: 288, 'font-size': 10, fill: '#7a8580' }, `${(s.parametres || 0).toLocaleString('fr-FR')} paramètres · couleurs : activations sur une position fixe`));
}

function drawChart(s) {
  const svg = $('train-chart'); svg.replaceChildren();
  const pts = s.historique || [], W = 380, H = 300, L = 34, R = 34, T = 20, B = 30, total = s.pas_total || 1;
  const X = step => L + (W - L - R) * step / total, Y = acc => T + (H - T - B) * (1 - acc);
  [0, .25, .5, .75, 1].forEach(t => svg.append(svgEl('line', { x1: L, x2: W - R, y1: Y(t), y2: Y(t), stroke: '#e6eae1' }), svgEl('text', { x: 2, y: Y(t) + 3, 'font-size': 9, fill: '#7a8580' }, Math.round(t * 100) + ' %')));
  svg.append(svgEl('text', { x: L, y: H - 8, 'font-size': 10, fill: '#7a8580' }, 'pas →'), svgEl('text', { x: L, y: 12, 'font-size': 10, fill: '#14352e' }, 'accord (vert) · taille (orange)'));
  if (pts.length) {
    const maxH = Math.max(...pts.map(p => Math.max(p.h1, p.h2)), 8);
    svg.append(svgEl('polyline', { points: pts.map(p => `${X(p.step)},${Y(p.val_acc)}`).join(' '), fill: 'none', stroke: '#14352e', 'stroke-width': 2 }));
    svg.append(svgEl('polyline', { points: pts.map(p => `${X(p.step)},${T + (H - T - B) * (1 - p.h1 / maxH)}`).join(' '), fill: 'none', stroke: '#df8056', 'stroke-width': 2, 'stroke-dasharray': '4 3' }));
    svg.append(svgEl('text', { x: W - R + 3, y: T + 8, 'font-size': 9, fill: '#df8056' }, `${maxH}`));
  }
  (s.evenements || []).forEach(e => svg.append(svgEl('line', { x1: X(e.step), x2: X(e.step), y1: T, y2: H - B, stroke: e.type === 'croissance' ? '#3d7a52' : '#df8056', 'stroke-width': 1, opacity: 0.45 })));
}

function render(s) {
  const running = s.etat === 'en cours' || s.etat === 'preparation';
  $('train-start').disabled = running; $('train-stop').disabled = !running;
  const last = (s.historique || []).slice(-1)[0];
  $('train-status').textContent = s.etat === 'inactif' ? 'Aucun entraînement.' : s.etat === 'erreur' ? 'Erreur : ' + s.erreur
    : `${s.etat} · ${s.jeu} · ${s.mode} · pas ${s.pas || 0}/${s.pas_total}` + (last ? ` · accord validation ${(last.val_acc * 100).toFixed(1)} % · tailles ${(s.tailles || [last.h1, last.h2]).join('+')}` : '');
  drawNet(s); drawChart(s);
  const ul = $('train-events'); ul.replaceChildren();
  (s.evenements || []).slice(-12).forEach(e => { const li = document.createElement('li'); li.className = e.type === 'croissance' ? 'grow' : 'cut'; li.textContent = e.type === 'croissance' ? `pas ${e.step} : croissance → ${e.h1}+${e.h2} neurones` : `pas ${e.step} : élagage ${JSON.stringify(e.supprimes)} → ${e.h1}+${e.h2} neurones`; ul.append(li); });
  const tb = $('train-compare').querySelector('tbody'); tb.replaceChildren();
  (s.comparaison || []).forEach(r => { const tr = document.createElement('tr'); [r.jeu, r.mode + (r.arrete ? ' (arrêté)' : ''), r.tailles.join(' + '), r.parametres.toLocaleString('fr-FR'), (r.test_accord * 100).toFixed(1) + ' %'].forEach(t => { const td = document.createElement('td'); td.textContent = t; tr.append(td); }); tb.append(tr); });
  if (!running && timer) { clearInterval(timer); timer = null; }
}

async function poll() { try { render(await api('/api/lab/train/status')); } catch (e) { $('train-status').textContent = 'Erreur : ' + e.message; } }
$('train-start').addEventListener('click', async () => {
  try { await api('/api/lab/train/start', { game: $('train-game').value, mode: $('train-mode').value, steps: Number($('train-steps').value) || 3000 }); } catch (e) { $('train-status').textContent = 'Erreur : ' + e.message; return; }
  if (!timer) timer = setInterval(poll, 500);
  poll();
});
$('train-stop').addEventListener('click', async () => { try { await api('/api/lab/train/stop', {}); } catch (e) { $('train-status').textContent = 'Erreur : ' + e.message; } });
poll();

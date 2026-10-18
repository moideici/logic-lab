const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
const svgEl = (tag, attrs = {}, text) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (text !== undefined) e.textContent = text; return e; };
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
const api = async (path, body) => {
  const r = await fetch(path, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || 'Erreur du Lab');
  return j.result;
};
const LAYERS = ['encodeur', 'coeur'];
const COLS = 8, ROWS = 6, GAP = 21, R = 8;
const origin = { encodeur: [215, 130], coeur: [440, 130] };
let state = null, importance = null, selected = null, busy = false;

function note(text) { $('game-status').textContent = text; }
function color(v) {
  const a = Math.min(1, Math.abs(v));
  return v >= 0 ? `rgba(25,90,70,${0.12 + 0.88 * a})` : `rgba(223,128,86,${0.12 + 0.88 * a})`;
}
function importanceOf(layer, i) { return importance?.neurones.find(n => n.couche === layer && n.indice === i); }

function drawNet() {
  const svg = $('net'); svg.replaceChildren();
  svg.append(svgEl('text', { x: 20, y: 22, class: 'col-label' }, 'Entrée'), svgEl('text', { x: origin.encodeur[0], y: 22, class: 'col-label' }, 'Encodeur · 48'),
    svgEl('text', { x: origin.coeur[0], y: 22, class: 'col-label' }, 'Cœur partagé · 48'), svgEl('text', { x: 640, y: 22, class: 'col-label' }, 'Sortie'));
  // entrée : une zone par jeu, la zone du jeu courant est allumée
  const games = window.__games || [];
  const total = games.reduce((s, g) => s + g.entrees, 0) || 1;
  let y = 36;
  for (const g of games) {
    const h = Math.max(3, 300 * g.entrees / total);
    const on = state && g.id === state.jeu;
    svg.append(svgEl('rect', { x: 20, y, width: 120, height: h - 1, rx: 2, fill: on ? '#c0ed8d' : '#eef1e8', stroke: on ? '#14352e' : 'none' }));
    if (h > 12 || on) svg.append(svgEl('text', { x: 26, y: y + Math.min(h - 3, 12), 'font-size': 9, fill: '#193c35' }, g.id));
    y += h;
  }
  for (const layer of LAYERS) {
    const acts = state?.activations?.[layer] || [];
    const off = new Set(state?.eteints?.[layer] || []);
    for (let i = 0; i < 48; i++) {
      const cx = origin[layer][0] + (i % COLS) * GAP, cy = origin[layer][1] + Math.floor(i / COLS) * GAP;
      const c = svgEl('circle', { cx, cy, r: R, fill: color(acts[i] ?? 0), class: 'neuron' + (off.has(i) ? ' off' : '') + (selected && selected.layer === layer && selected.index === i ? ' sel' : '') });
      c.append(svgEl('title', {}, `${layer} #${i} · activation ${(acts[i] ?? 0).toFixed(3)}`));
      c.addEventListener('click', () => select(layer, i));
      svg.append(c);
      const imp = importanceOf(layer, i);
      if (imp && imp.sensibilite > 0) svg.append(svgEl('circle', { cx, cy, r: R + 3, class: 'ring', 'stroke-width': 1 + 4 * imp.sensibilite, opacity: 0.8 }));
    }
  }
  // sortie : meilleurs coups
  const acts = state?.actions || [];
  const max = Math.max(0.001, ...acts.map(a => Math.abs(a.score)));
  acts.forEach((a, k) => {
    const y0 = 40 + k * 36;
    const w = 60 * Math.abs(a.score) / max;
    svg.append(svgEl('rect', { x: 620, y: y0, width: Math.max(2, w), height: 12, rx: 2, fill: a.choisie ? '#14352e' : '#9fb59a' }));
    svg.append(svgEl('text', { x: 620, y: y0 + 26, 'font-size': 10, fill: '#193c35' }, a.action.length > 24 ? a.action.slice(0, 23) + '…' : a.action));
  });
  // liens indicatifs entre colonnes
  [[140, 215], [origin.encodeur[0] + 7 * GAP + R, origin.coeur[0] - R], [origin.coeur[0] + 7 * GAP + R, 612]].forEach(([x1, x2]) => {
    svg.insertBefore(svgEl('path', { d: `M${x1} 190 C ${(x1 + x2) / 2} 190, ${(x1 + x2) / 2} 190, ${x2} 190`, stroke: '#cfd8ca', fill: 'none', 'stroke-width': 2, 'stroke-dasharray': '3 4' }), svg.firstChild);
  });
}

function drawBoard() {
  const box = $('board'); box.replaceChildren();
  const b = state?.plateau;
  if (!Array.isArray(b)) { box.textContent = 'Pas de plateau affichable pour ce jeu.'; return; }
  const rows = b.length, cols = Array.isArray(b[0]) ? b[0].length : 1;
  box.style.gridTemplateColumns = `repeat(${cols}, auto)`;
  for (const row of b) for (const v of (Array.isArray(row) ? row : [row])) box.append(el('span', '', v === 0 || v === null ? '·' : (typeof v === 'object' ? JSON.stringify(v) : String(v))));
}

function drawActions() {
  const ol = $('actions'); ol.replaceChildren();
  for (const a of state?.actions || []) {
    const li = el('li', a.choisie ? 'chosen' : '', `${a.action} · ${a.score.toFixed(2)}`);
    if (a.meilleure_complet && !a.choisie) li.append(el('span', 'flag', 'préféré du réseau complet'));
    ol.append(li);
  }
  $('choice-note').textContent = state?.termine ? 'Partie terminée.' : state?.choix_change ? 'Les neurones éteints ont changé le coup préféré.' : (Object.values(state?.eteints || {}).some(s => s.length) ? 'Même coup préféré que le réseau complet.' : '');
}

function neuronInfo() {
  const box = $('neuron-info'); box.replaceChildren();
  if (!selected) { box.textContent = 'Cliquez sur un neurone du schéma.'; return; }
  const { layer, index } = selected;
  const act = state?.activations?.[layer]?.[index];
  const imp = importanceOf(layer, index);
  const off = (state?.eteints?.[layer] || []).includes(index);
  const lines = [['Neurone', `${layer} #${index}`], ['Activation', act === undefined ? '—' : act.toFixed(3)], ['État', off ? 'éteint' : 'allumé']];
  if (imp) lines.push(['Sensibilité', `${Math.round(imp.sensibilite * 100)} % des positions changent de coup si on l’éteint`], ['Décalage moyen des scores', imp.decalage.toFixed(4)]);
  else lines.push(['Importance', 'non mesurée (bouton sous le schéma)']);
  for (const [k, v] of lines) { const p = el('div'); p.append(el('b', '', k + ' : '), document.createTextNode(v)); box.append(p); }
  const b = el('button', 'button', off ? 'Rallumer' : 'Éteindre'); b.addEventListener('click', () => run(() => toggleMute(layer, index))); box.append(b);
}

function render() {
  note(state ? `${state.jeu} · coup ${state.coups}${state.termine ? ' · terminé' : ''} · ${state.coups_legaux ?? 0} coups légaux` : '');
  drawNet(); drawBoard(); drawActions(); neuronInfo();
}

function select(layer, index) { selected = { layer, index }; render(); }

async function toggleMute(layer, index) {
  const off = (state?.eteints?.[layer] || []).includes(index);
  state = await api('/api/lab/mute', { layer, index, on: !off });
  render();
}

async function run(fn) {
  if (busy) return; busy = true;
  document.querySelectorAll('.lab-bar button').forEach(b => b.disabled = true);
  try { await fn(); } catch (e) { note('Erreur : ' + e.message); } finally { busy = false; document.querySelectorAll('.lab-bar button').forEach(b => b.disabled = false); }
}

function drawCurve(data) {
  const svg = $('curve'); svg.replaceChildren();
  const W = 760, H = 260, L = 60, Rr = 20, T = 38, B = 40;
  const pts = data.courbe;
  const xs = pts.map(p => p.parametres), xmin = Math.min(...xs), xmax = data.pleine;
  const X = v => L + (W - L - Rr) * (xmax - v) / Math.max(1, xmax - xmin);
  const Y = v => T + (H - T - B) * (1 - v);
  for (const t of [0, .25, .5, .75, 1]) {
    svg.append(svgEl('line', { x1: L, x2: W - Rr, y1: Y(t), y2: Y(t), stroke: '#e6eae1' }), svgEl('text', { x: 8, y: Y(t) + 4, 'font-size': 10, fill: '#7a8580' }, Math.round(t * 100) + ' %'));
  }
  svg.append(svgEl('text', { x: L, y: H - 8, 'font-size': 10, fill: '#7a8580' }, 'paramètres retirés →  (gauche : réseau complet ' + xmax.toLocaleString('fr-FR') + ')'),
    svgEl('text', { x: 8, y: 12, 'font-size': 10, fill: '#7a8580' }, 'accord avec le réseau complet'));
  svg.append(svgEl('polyline', { points: pts.map(p => `${X(p.parametres)},${Y(p.accord)}`).join(' '), fill: 'none', stroke: '#14352e', 'stroke-width': 2 }));
  for (const p of pts) {
    const c = svgEl('circle', { cx: X(p.parametres), cy: Y(p.accord), r: 4, fill: '#c0ed8d', stroke: '#14352e' });
    c.append(svgEl('title', {}, `${p.eteints} neurones éteints · ${p.parametres.toLocaleString('fr-FR')} paramètres · accord ${Math.round(p.accord * 100)} %`));
    svg.append(c, svgEl('text', { x: X(p.parametres), y: Y(p.accord) - 8, 'font-size': 9, 'text-anchor': 'middle', fill: '#193c35' }, String(p.eteints)));
  }
}

async function init() {
  const net = await api('/api/lab/net');
  window.__games = net.jeux;
  $('net-shape').textContent = `Garry ${net.version} · ${net.forme.join(' → ')} · ${net.parametres.toLocaleString('fr-FR')} paramètres`;
  for (const g of net.jeux) $('game').append(new Option(g.id, g.id));
  $('input-link').href = `${location.protocol}//${location.hostname}:8766/`;
  state = await api('/api/lab/new', { game: $('game').value, seed: 0 });
  render();
}

$('new').addEventListener('click', () => run(async () => { importance = null; selected = null; state = await api('/api/lab/new', { game: $('game').value, seed: Number($('seed').value) || 0 }); render(); }));
$('game').addEventListener('change', () => $('new').click());
for (const [id, mode] of [['step-net', 'reseau'], ['step-full', 'complet'], ['step-random', 'hasard']]) $(id).addEventListener('click', () => run(async () => { state = await api('/api/lab/step', { mode }); render(); }));
$('reset-mutes').addEventListener('click', () => run(async () => { state = await api('/api/lab/reset', {}); render(); }));
$('measure').addEventListener('click', () => run(async () => { $('measure-note').textContent = 'Mesure en cours…'; importance = await api('/api/lab/importance?game=' + encodeURIComponent($('game').value)); const top = [...importance.neurones].sort((a, b) => b.sensibilite - a.sensibilite)[0]; $('measure-note').textContent = `${importance.positions} positions · le plus sensible : ${top.couche} #${top.indice} (${Math.round(top.sensibilite * 100)} %). Les anneaux orange montrent la sensibilité.`; render(); }));
$('curve-run').addEventListener('click', () => run(async () => { $('curve-note').textContent = 'Mesure en cours…'; const d = await api('/api/lab/prune-curve?game=' + encodeURIComponent($('game').value)); $('curve-note').textContent = `${d.positions} positions de contrôle, différentes de celles qui classent les neurones.`; drawCurve(d); }));
init().catch(e => note('Erreur : ' + e.message));

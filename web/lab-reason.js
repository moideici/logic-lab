const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
const svgEl = (tag, attrs = {}, text) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (text !== undefined) e.textContent = text; return e; };
const api = async (path, body) => {
  const r = await fetch(path, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const j = await r.json();
  if (!j.ok) throw new Error(j.error || 'Erreur');
  return j.result;
};
let problem = null, run = null, shown = 0, player = null;

function say(text) { $('reason-status').textContent = text; }

function drawGrid() {
  const box = $('reason-grid'); box.replaceChildren();
  if (!problem) return;
  const step = run && shown > 0 ? run.etapes[shown - 1] : null;
  for (let i = 0; i < 36; i++) {
    const cell = document.createElement('div');
    const r = Math.floor(i / 6), c = i % 6;
    cell.className = 'rc' + (r % 2 === 1 ? ' rb' : '') + (c % 3 === 2 ? ' cb' : '');
    const given = problem.puzzle[i] > 0;
    if (given) { cell.classList.add('given'); cell.textContent = problem.puzzle[i]; }
    else if (step) {
      cell.textContent = step.grille[i];
      cell.classList.add(step.grille[i] === problem.solution[i] ? 'ok' : 'bad');
      cell.style.opacity = String(0.35 + 0.65 * step.confiance[i]);
    }
    box.append(cell);
  }
}

function drawChart() {
  const svg = $('reason-chart'); svg.replaceChildren();
  if (!run) return;
  const W = 380, H = 150, L = 28, B = 22, T = 14, steps = run.etapes, max = Math.max(1, ...steps.map(s => s.fausses ?? 0));
  const bw = (W - L - 6) / steps.length;
  svg.append(svgEl('text', { x: 2, y: 10, 'font-size': 9, fill: '#7a8580' }, 'cases fausses par passe'));
  steps.forEach((s, i) => {
    const h = (H - B - T) * (s.fausses ?? 0) / max;
    const rect = svgEl('rect', { x: L + i * bw + 1, y: H - B - h, width: Math.max(2, bw - 2), height: Math.max(h, 1), fill: s.valide ? '#3d7a52' : '#df8056', opacity: i + 1 === shown ? 1 : 0.55 });
    rect.append(svgEl('title', {}, `passe ${s.passe} : ${s.fausses} fausses${s.valide ? ' · grille valide' : ''}`));
    rect.addEventListener('click', () => show(i + 1));
    svg.append(rect);
    if (steps.length <= 20 || i % 4 === 0) svg.append(svgEl('text', { x: L + i * bw + bw / 2, y: H - 8, 'font-size': 8, 'text-anchor': 'middle', fill: '#7a8580' }, String(s.passe)));
  });
  svg.append(svgEl('text', { x: 2, y: H - B + 4, 'font-size': 8, fill: '#7a8580' }, '0'), svgEl('text', { x: 2, y: T + 4, 'font-size': 8, fill: '#7a8580' }, String(max)));
}

function show(t) {
  shown = t;
  if (run) {
    const s = run.etapes[t - 1];
    say(`Passe ${t}/${run.passes} · cases fausses : ${s.fausses} · grille ${s.valide ? 'valide' : 'non valide'}` + (run.premiere_valide ? ` · première grille valide à la passe ${run.premiere_valide}` : ' · aucune grille valide'));
    $('reason-slider').value = String(t);
  }
  drawGrid(); drawChart();
}

async function newProblem() {
  stop();
  try { problem = await api('/api/lab/reason/new', { empties: Number($('reason-empties').value), seed: Number($('reason-seed').value) || 0 }); } catch (e) { say('Erreur : ' + e.message); return; }
  run = null; shown = 0; $('reason-slider').disabled = true; $('reason-play').disabled = true;
  say(`Nouveau problème : ${problem.vides} cases vides. Faites-le réfléchir.`);
  drawGrid(); drawChart();
}

async function think() {
  if (!problem) await newProblem();
  stop();
  try { run = await api('/api/lab/reason/solve', { puzzle: problem.puzzle, passes: Number($('reason-passes').value), solution: problem.solution }); } catch (e) { say('Erreur : ' + e.message); return; }
  const slider = $('reason-slider'); slider.max = String(run.passes); slider.disabled = false; $('reason-play').disabled = false;
  show(1); play();
}

function stop() { if (player) { clearInterval(player); player = null; } $('reason-play').textContent = '▶ Rejouer'; }
function play() {
  stop(); if (!run) return;
  $('reason-play').textContent = '■ Pause';
  if (shown >= run.passes) show(1);
  player = setInterval(() => { if (shown >= run.passes) { stop(); return; } show(shown + 1); }, 450);
}

$('reason-new').addEventListener('click', newProblem);
$('reason-think').addEventListener('click', think);
$('reason-play').addEventListener('click', () => (player ? stop() : play()));
$('reason-slider').addEventListener('input', e => { stop(); show(Number(e.target.value)); });
$('reason-empties').addEventListener('input', e => { $('reason-empties-v').textContent = e.target.value; });
api('/api/lab/reason/info').then(i => { $('reason-info').textContent = `Loop · ${i.parametres.toLocaleString('fr-FR')} paramètres · poids liés · entraîné à ${i.passes_entrainement} passes · ${(i.exact_dur_32_passes * 100).toFixed(0)} % des problèmes durs résolus à 32 passes`; newProblem(); }).catch(e => say('Erreur : ' + e.message));

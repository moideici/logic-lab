// Page Maths du Lab : poser un calcul à un modèle (ou à tous) et voir les étapes, vérifiées une à une par l'évaluateur exact.
const h = (tag, attrs = {}, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (k === 'class') e.className = v; else if (k === 'html') e.innerHTML = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v); } for (const c of kids.flat(Infinity)) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c)); return e; };
const EXAMPLES = ['(3+4)*2-5', '48/6+3*7', '2x+6=20', '2^3+√16', '(1/2)+(1/3)', 'x^2=49', '5*(2+3)^2-10', '∛27+4'];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const pretty = (s) => String(s).replace(/\*/g, '×').replace(/-/g, '−');

async function api(path, body) {
  const r = await fetch(path, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {});
  const j = await r.json().catch(() => ({ ok: false, error: 'Réponse illisible du serveur' }));
  if (!j.ok) throw new Error(j.error || 'Erreur');
  return j;
}

export async function mountMathsTester(host) {
  const input = h('input', { id: 'm-expr', type: 'text', value: EXAMPLES[0], autocomplete: 'off', spellcheck: 'false', 'aria-label': 'Calcul à résoudre' });
  const sel = h('select', { id: 'm-model', 'aria-label': 'Modèle' });
  const mode = h('select', { id: 'm-mode', 'aria-label': 'Mode' }, h('option', { value: 'alone' }, 'Réseau seul'), h('option', { value: 'verified' }, 'Avec vérificateur'));
  const go = h('button', { class: 'button primary', type: 'button' }, 'Résoudre');
  const out = h('div', { id: 'm-out', class: 'm-out', 'aria-live': 'polite' }, h('p', { class: 'm-hint' }, 'Écrivez un calcul, choisissez un modèle, appuyez sur Résoudre.'));
  const chips = h('div', { class: 'm-chips' }, EXAMPLES.map((e) => h('button', { type: 'button', class: 'm-chip', onclick: () => { input.value = e; run(); } }, e)));
  host.append(h('div', { class: 'm-box' }, h('div', { class: 'm-row' }, input, sel, mode, go), chips, out,
    h('p', { class: 'm-note' }, 'Chaque étape est jugée par un évaluateur exact écrit à part. « Réseau seul » : la première étape proposée est gardée, juste ou fausse. « Avec vérificateur » : le réseau propose 8 étapes et la première valide est gardée. Aucun résultat n’est calculé par le serveur à la place du modèle.')));
  let models = [];
  try { models = (await api('/api/maths/models')).models; } catch { /* serveur absent */ }
  sel.append(h('option', { value: 'best' }, 'Garry Maths : le premier modèle qui réussit'), h('option', { value: 'all' }, 'Tous les modèles (comparaison)'), ...models.map((m) => h('option', { value: m.id }, `${m.label} · ${(m.params / 1000).toFixed(0)} k`)));
  if (!models.length) out.replaceChildren(h('p', { class: 'm-hint' }, 'Les poids du modèle Maths ne sont pas disponibles sur ce serveur.'));

  const chain = (r, animate) => {
    const box = h('div', { class: 'm-chain' });
    const lines = [h('div', { class: 'm-step start' }, h('span', { class: 'm-expr' }, pretty(r.expression)), h('span', { class: 'm-tag' }, 'départ'))];
    r.steps.forEach((s, i) => lines.push(h('div', { class: 'm-step ' + (s.valid ? 'ok' : 'bad') }, h('span', { class: 'm-arrow' }, '↓'), h('span', { class: 'm-expr' }, pretty(s.to)), h('span', { class: 'm-tag' }, s.valid ? 'étape valide' : 'étape invalide'))));
    lines.forEach((l, i) => { if (animate) { l.style.opacity = 0; l.style.transform = 'translateY(8px)'; } box.append(l); });
    if (animate) lines.forEach((l, i) => setTimeout(() => { l.style.transition = 'opacity .35s,transform .35s'; l.style.opacity = 1; l.style.transform = 'none'; }, 160 * i));
    return box;
  };
  const verdict = (r) => h('div', { class: 'm-verdict ' + (r.correct ? 'ok' : 'bad') },
    r.correct ? h('span', {}, 'Résultat exact : ', h('b', {}, pretty(r.final))) : h('span', {}, r.status === 'ok' ? `Résultat faux : ${pretty(r.final)} (attendu ${pretty(r.reference)})` : `Échec (${r.status}). Réponse exacte : ${pretty(r.reference)}`),
    h('small', {}, `${r.steps.length} étape${r.steps.length > 1 ? 's' : ''} · ${r.ms} ms`));

  let busy = false;
  async function run() {
    if (busy) return;
    const expression = input.value.trim();
    if (!expression) return;
    busy = true; go.disabled = true; go.textContent = 'Calcul…';
    out.replaceChildren(h('p', { class: 'm-hint' }, 'Le modèle écrit les étapes…'));
    try {
      const body = { expression, model: sel.value, verified: mode.value === 'verified' };
      const { result } = await api('/api/maths/solve', body);
      out.replaceChildren();
      if (Array.isArray(result)) {
        out.append(h('div', { class: 'm-table' }, result.map((r) => r.error ? h('div', { class: 'm-trow bad' }, h('b', {}, r.label), h('span', {}, r.error)) :
          h('div', { class: 'm-trow ' + (r.correct ? 'ok' : 'bad') }, h('b', {}, r.label), h('span', { class: 'm-final' }, r.final ? pretty(r.final) : '—'), h('span', { class: 'm-tag' }, r.correct ? '✓ exact' : r.status === 'ok' ? '✗ faux' : '✗ ' + r.status), h('small', {}, `${r.steps.length} étapes`)))));
        const good = result.filter((r) => r.correct).length;
        out.append(h('div', { class: 'm-verdict ' + (good ? 'ok' : 'bad') }, h('span', {}, `${good} modèle${good > 1 ? 's' : ''} sur ${result.length} résolvent ce calcul. Réponse exacte : `, h('b', {}, pretty(result[0].reference)))));
      } else {
        if (result.attempts) out.append(h('p', { class: 'm-hint' }, 'Modèles essayés : ' + result.attempts.map((a) => `${a.label} ${a.ok ? '✓' : '✗'}`).join(' · ')));
        out.append(h('div', { class: 'm-model' }, result.label || sel.selectedOptions[0].textContent), chain(result, true), verdict(result));
      }
    } catch (e) {
      out.replaceChildren(h('div', { class: 'm-verdict bad' }, h('span', {}, e.message)));
    } finally { busy = false; go.disabled = false; go.textContent = 'Résoudre'; }
  }
  go.addEventListener('click', run);
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') run(); });
}

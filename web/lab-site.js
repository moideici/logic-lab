import { MODELS, NODES, EDGES, C4, CONF, OPTIMUS_STATUS } from './lab-data.js';
import { mount } from './lab-scenes.js';

const $ = (s, r = document) => r.querySelector(s);
const h = (tag, attrs = {}, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (k === 'class') e.className = v; else if (k === 'html') e.innerHTML = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v); } for (const c of kids.flat(Infinity)) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c)); return e; };
const fmt = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

// Rail + en-tête communs à toutes les pages du site (arène, lab, atelier).
export function chrome(active, { wordmark = 'lab', chips = true } = {}) {
  const rail = h('aside', { class: 'rail' }, h('a', { class: 'logo', href: '/', 'aria-label': 'Logic Lab', html: 'L<span>✳</span>' }), h('div', { class: 'rail-label' }, 'LOGIC LAB'),
    h('nav', {}, ...[['/', 'arena', '◫', 'Arène'], ['/lab.html', 'lab', '⚗', 'Lab'], ['/atelier.html', 'atelier', '⚒', 'Atelier'], ['http://127.0.0.1:8766/', 'input', 'Aa', 'Input']].map(([href, id, ic, lb]) =>
      h('a', { class: 'nav' + (active === id || (id === 'lab' && MODELS.some((m) => m.id === active)) ? ' active' : ''), href, title: lb }, h('span', {}, ic), h('small', {}, lb)))),
    h('div', { class: 'rail-bottom', html: '<i></i><small>LOCAL<br>INFERENCE</small>' }));
  const top = h('header', { class: 'top' }, h('a', { class: 'wordmark', href: '/lab.html', html: `logic<span>lab</span><sup> / ${wordmark}</sup>` }),
    chips ? h('nav', { class: 'chips' }, h('a', { href: '/lab.html', class: active === 'lab' ? 'on' : '' }, 'Tous'), ...MODELS.map((m) => h('a', { href: m.page, class: active === m.id ? 'on' : '' }, m.short))) : null);
  const bar = h('div', { class: 'progress' }, h('i'));
  document.body.prepend(bar, top); document.body.prepend(rail);
  addEventListener('scroll', () => { bar.firstChild.style.width = (scrollY / Math.max(1, document.documentElement.scrollHeight - innerHeight) * 100) + '%'; }, { passive: true });
  queueMicrotask(() => document.body.append(h('footer', {}, h('span', {}, 'logic lab · local'), h('span', {}, 'chiffres issus des rapports du dépôt'))));
}

export function reveals() {
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); e.target.dispatchEvent(new Event('shown')); io.unobserve(e.target); } }), { threshold: .12 });
  document.querySelectorAll('.reveal').forEach((e) => io.observe(e));
}

function counter(el, target, text) {
  if (text) { el.textContent = text; return; }
  const start = performance.now(), dur = 1600;
  const tick = (now) => { const p = Math.min(1, (now - start) / dur); el.textContent = fmt(Math.round(target * (1 - Math.pow(1 - p, 4)))); if (p < 1) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
}

const line = (a, b) => h('div', { class: 'section-line' }, h('span', {}, a), h('span', {}, b));

function benchBlock(b) {
  const min = b.min ?? 0, span = b.max - min;
  const rows = b.rows.map(([name, v, hl]) => {
    const pct = Math.max(0, Math.min(100, ((v - min) / span) * 100));
    const shown = b.unit === '%' ? String(v).replace('.', ',') + ' %' : (v === 1 ? '1,000' : String(v).replace('.', ','));
    return h('div', { class: 'row' + (hl ? ' hl' : '') }, h('span', { class: 'name' }, name), h('div', { class: 'track' }, h('div', { class: 'fill', 'data-w': pct })), h('span', { class: 'val' }, shown));
  });
  const box = h('div', { class: 'bench reveal', title: b.note + (b.lower ? ' Plus bas = mieux.' : '') }, h('h3', {}, b.title + (b.lower ? ' ↓' : '')), rows);
  box.addEventListener('shown', () => box.querySelectorAll('.fill').forEach((f, i) => setTimeout(() => { f.style.width = f.dataset.w + '%'; }, i * 90)));
  return box;
}

function hub() {
  chrome('lab', { wordmark: 'lab' });
  const main = h('main'); document.body.append(main);
  main.append(h('section', { class: 'intro' },
    h('div', {}, h('p', { class: 'eyebrow' }, 'Le terrain de jeu des modèles'), h('h1', { html: 'Comprendre.<br>Comparer.<br><span>Mesurer.</span>' }), h('p', { class: 'sub' }, 'Sept modèles, leurs duels, leurs chiffres.'),
      h('div', { class: 'btns' }, h('a', { class: 'button primary', href: '#modeles' }, 'Voir les modèles'), h('a', { class: 'button', href: '#duels' }, 'Qui joue contre qui'))),
    h('div', { class: 'stage' }, h('canvas', { id: 'hero-canvas' }))));

  const cards = h('div', { class: 'cards' });
  MODELS.forEach((m) => {
    const cv = h('canvas');
    cards.append(h('a', { class: 'mcard reveal', href: m.page }, cv, h('span', { class: 'glyph' }, m.glyph), h('div', { class: 'in' }, h('h3', {}, m.name), h('small', {}, m.role), h('span', { class: 'go' }, '↗'))));
    requestAnimationFrame(() => mount(cv, m.scene, { hue: m.hue, hover: true }));
  });
  main.append(line('01 / CHOISIR UN MODÈLE', `${MODELS.length} MODÈLES`), cards);

  main.append(line('02 / QUI JOUE CONTRE QUI', 'DUELS MESURÉS'), h('canvas', { id: 'graph' }), h('div', { id: 'edge-info' }, 'Touchez un trait ou un nœud pour lire le duel.'),
    h('div', { class: 'legend' }, h('span', {}, h('i', { style: 'background:#c0ed8d' }), 'modèle'), h('span', {}, h('i', { style: 'background:#df8056' }), 'juge')));
  graph($('#graph'));

  main.append(line('03 / BENCHMARK COMMUN', 'PUISSANCE 4'), benchBlock(C4));

  const st = h('div', { class: 'status' }, h('span', { class: 'pulse off' }), h('b', {}, 'Garry Optimus'), h('span', { id: 'opt-status', style: 'color:var(--muted)' }, '…'));
  main.append(line('04 / ENTRAÎNEMENT', 'EN COURS'), st);
  Promise.all([OPTIMUS_STATUS, '/optimus-2048-status.json'].map((u) => fetch(u, { cache: 'no-store' }).then((r) => r.ok ? r.json() : null).catch(() => null))).then(([multi, t48]) => {
    const parts = [multi && `multi-jeux : ${multi.text}`, t48 && `2048 : ${t48.text}`].filter(Boolean);
    $('#opt-status').textContent = parts.length ? parts.join('  ·  ') : 'aucun statut';
    if ((multi && multi.running) || (t48 && t48.running)) st.querySelector('.pulse').classList.remove('off');
  });
  mount($('#hero-canvas'), 'field', { hue: 96 });
  reveals();
}

function graph(cv) {
  const ctx = cv.getContext('2d'); let W = 0, H = 0, hover = null, node = null; const t0 = performance.now(), pos = {};
  const place = () => { const r = cv.getBoundingClientRect(), d = Math.min(devicePixelRatio || 1, 2); W = r.width; H = r.height; cv.width = W * d; cv.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0);
    const ms = NODES.filter((n) => n.kind === 'model'), js = NODES.filter((n) => n.kind === 'judge');
    ms.forEach((n, i) => { pos[n.id] = [W * .27, H * (.12 + .76 * (i + .5) / ms.length)]; }); js.forEach((n, i) => { pos[n.id] = [W * .74, H * (.05 + .9 * (i + .5) / js.length)]; }); };
  const edgeAt = (x, y) => { let best = null, bd = 14; EDGES.forEach((e, i) => { const [ax, ay] = pos[e[0]], [bx, by] = pos[e[1]], dx = bx - ax, dy = by - ay, u = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy))), d = Math.hypot(x - (ax + u * dx), y - (ay + u * dy)); if (d < bd) { bd = d; best = i; } }); return best; };
  const nodeAt = (x, y) => NODES.find((n) => Math.hypot(x - pos[n.id][0], y - pos[n.id][1]) < 22)?.id ?? null;
  const info = $('#edge-info'), L = (id) => NODES.find((n) => n.id === id).label;
  const sel = (i) => { hover = i; if (i == null) { info.textContent = node ? `Duels de ${L(node)}` : 'Touchez un trait ou un nœud pour lire le duel.'; return; } const e = EDGES[i]; info.innerHTML = `<b>${L(e[0])}</b> contre <b>${L(e[1])}</b> · ${e[2]} · <span style="color:#c0ed8d;font-family:var(--mono)">${e[3]}</span>`; };
  const pt = (ev) => { const r = cv.getBoundingClientRect(), p = ev.touches ? ev.touches[0] : ev; return [p.clientX - r.left, p.clientY - r.top]; };
  cv.addEventListener('mousemove', (ev) => { const [x, y] = pt(ev); cv.style.cursor = nodeAt(x, y) ? 'pointer' : 'default'; sel(edgeAt(x, y)); });
  cv.addEventListener('click', (ev) => { const [x, y] = pt(ev), n = nodeAt(x, y); node = n === node ? null : n; sel(n ? null : edgeAt(x, y)); });
  cv.addEventListener('touchstart', (ev) => sel(edgeAt(...pt(ev))), { passive: true });
  new ResizeObserver(place).observe(cv); place();
  const good = (e) => !/défaite|0,425|0,17|0,20|0,39/.test(e[3]);
  const draw = (now) => { const t = (now - t0) / 1000; ctx.clearRect(0, 0, W, H);
    EDGES.forEach((e, i) => { const [ax, ay] = pos[e[0]], [bx, by] = pos[e[1]], on = hover === i || (node && (e[0] === node || e[1] === node)), dim = (node && !on) || (hover != null && hover !== i), mx = (ax + bx) / 2;
      ctx.strokeStyle = on ? '#c0ed8d' : `rgba(134,165,149,${dim ? .1 : .38})`; ctx.lineWidth = on ? 3 : good(e) ? 2.2 : 1.1; ctx.beginPath(); ctx.moveTo(ax, ay); ctx.bezierCurveTo(mx, ay, mx, by, bx, by); ctx.stroke();
      const u = (t * .25 + i * .13) % 1, x = (1 - u) ** 3 * ax + 3 * (1 - u) ** 2 * u * mx + 3 * (1 - u) * u * u * mx + u ** 3 * bx, y = (1 - u) ** 3 * ay + 3 * (1 - u) ** 2 * u * ay + 3 * (1 - u) * u * u * by + u ** 3 * by;
      if (!dim) { ctx.fillStyle = on ? '#fff' : '#c0ed8d'; ctx.beginPath(); ctx.arc(x, y, on ? 4 : 2.4, 0, 6.3); ctx.fill(); } });
    NODES.forEach((n) => { const [x, y] = pos[n.id], m = n.kind === 'model', dim = node && node !== n.id && !EDGES.some((e) => (e[0] === node && e[1] === n.id) || (e[1] === node && e[0] === n.id));
      ctx.globalAlpha = dim ? .25 : 1; ctx.fillStyle = m ? '#c0ed8d' : '#df8056'; ctx.beginPath(); ctx.arc(x, y, m ? 11 : 8, 0, 6.3); ctx.fill();
      if (m) { ctx.strokeStyle = '#c0ed8d55'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, 17 + 3 * Math.sin(t * 2 + x), 0, 6.3); ctx.stroke(); }
      ctx.fillStyle = '#eaf2e3'; ctx.font = '13px Inter,Arial'; ctx.textAlign = m ? 'right' : 'left'; ctx.textBaseline = 'middle'; ctx.fillText(n.label, x + (m ? -26 : 17), y); ctx.globalAlpha = 1; });
    requestAnimationFrame(draw); };
  requestAnimationFrame(draw);
}

function modelPage(id) {
  const i = MODELS.findIndex((m) => m.id === id), m = MODELS[i];
  document.title = `${m.name} · Logic Lab`;
  chrome(id, { wordmark: m.short.toLowerCase() });
  const main = h('main'); document.body.append(main);
  const stats = h('div', { class: 'stats' }, m.stats.map((s) => h('div', { class: 'stat' }, h('span', {}, s.l), h('b', {}, '0'))));
  main.append(h('section', { class: 'intro' },
    h('div', {}, h('p', { class: 'eyebrow' }, `${m.role} · ${m.version}`), h('h1', { html: m.name.split(' ').length > 1 ? `${m.name.split(' ').slice(0, -1).join(' ')}<br><span>${m.name.split(' ').slice(-1)}</span>` : `<span>${m.name}</span>` }), h('p', { class: 'sub' }, m.tagline),
      h('div', { class: 'btns' }, h('a', { class: 'button primary', href: '#systeme' }, 'Le système'), h('a', { class: 'button', href: '#bench' }, 'Les benchmarks'))),
    h('div', { class: 'stage' }, h('canvas', { id: 'scene' }))), stats);
  m.stats.forEach((s, k) => counter(stats.children[k].lastChild, s.v, s.fmt));

  const pipe = h('div', { class: 'pipe' }, m.system.map(([t]) => h('div', { class: 'step' }, h('i'), t))), desc = h('div', { id: 'step-desc' });
  main.append(h('div', { id: 'systeme' }, line('01 / LE SYSTÈME', `${m.system.length} ÉTAPES`)), pipe, desc);
  const steps = [...pipe.children], set = (k) => { steps.forEach((s, j) => s.classList.toggle('lit', j === k)); desc.textContent = '› ' + m.system[k][1]; }; let timer = 0, cur = 0;
  new IntersectionObserver((e) => { clearInterval(timer); if (e[0].isIntersecting) { set(cur); timer = setInterval(() => set(cur = (cur + 1) % steps.length), 2600); } }, { threshold: .4 }).observe(pipe);
  steps.forEach((s, k) => s.addEventListener('mouseenter', () => { clearInterval(timer); set(cur = k); }));

  main.append(line('02 / CE QUE LES CHIFFRES DISENT', 'ÉTABLI · INDICATIF · NON ÉTABLI'),
    h('div', { class: 'acc reveal' }, m.args.map(([t, d, c], k) => h('details', k === 0 ? { open: '' } : {}, h('summary', {}, h('span', { class: 'badge ' + c, title: CONF[c][1] }, CONF[c][0]), t), h('p', {}, d)))));
  main.append(line('03 / CONTRE QUI', `${m.duels.length} DUELS`),
    h('div', { class: 'duels reveal' }, m.duels.map(([a, b, g, r]) => h('div', { class: 'duel' }, h('div', {}, h('b', {}, a), h('span', { class: 'vs' }, '  contre  '), h('b', {}, b)), h('div', { class: 'g' }, g), h('div', { class: 'r' }, r)))));
  main.append(h('div', { id: 'bench' }, line('04 / BENCHMARKS', 'SOURCES EN BAS')), m.bench.map(benchBlock));

  const prev = MODELS[(i + MODELS.length - 1) % MODELS.length], next = MODELS[(i + 1) % MODELS.length];
  main.append(h('details', { class: 'more', style: 'margin-top:28px' }, h('summary', {}, 'Limites et sources'), h('ul', {}, m.limits.map((l) => h('li', {}, l))), h('p', {}, m.src.map((s) => [h('code', {}, s), ' ']))),
    h('div', { class: 'pager' }, h('a', { href: prev.page }, '← ' + prev.short), h('a', { href: '/lab.html' }, 'Le Lab'), h('a', { href: next.page }, next.short + ' →')));
  mount($('#scene'), m.scene, { hue: m.hue });
  reveals();
}

const page = document.body.dataset.page;
if (page === 'hub') hub(); else if (page) modelPage(page);

import { MODELS, NODES, EDGES, C4, CONF, OPTIMUS_STATUS } from './lab-data.js';
import { mount } from './lab-scenes.js';

const $ = (s, r = document) => r.querySelector(s);
const h = (tag, attrs = {}, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (k === 'class') e.className = v; else if (k === 'html') e.innerHTML = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v); } for (const c of kids.flat(Infinity)) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c)); return e; };
const fmt = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const arrow = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 11 11 3M5 3h6v6"/></svg>';

function chrome(active) {
  document.body.prepend(h('div', { class: 'progress', id: 'progress' }));
  const nav = h('nav', {}, h('a', { href: '/lab.html', class: active === 'hub' ? 'on' : '' }, 'Lab'),
    ...MODELS.map((m) => h('a', { href: m.page, class: active === m.id ? 'on' : '' }, m.short)),
    h('a', { href: '/atelier.html' }, 'Atelier'), h('a', { href: '/' }, 'Arène'));
  document.querySelector('.top')?.remove();
  document.body.prepend(h('header', { class: 'top' }, h('a', { class: 'brand', href: '/lab.html' }, h('i', {}, '◆'), 'logiclab'), nav));
  const bar = $('#progress');
  addEventListener('scroll', () => { bar.style.width = (scrollY / Math.max(1, document.documentElement.scrollHeight - innerHeight) * 100) + '%'; }, { passive: true });
  queueMicrotask(() => document.body.append(h('footer', {}, 'logic lab · chiffres issus des rapports du dépôt')));
}

function reveals() {
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); e.target.dispatchEvent(new Event('shown')); io.unobserve(e.target); } }), { threshold: .12 });
  document.querySelectorAll('.reveal').forEach((e) => io.observe(e));
}

function counter(el, target, text) {
  if (text) { el.textContent = text; return; }
  const start = performance.now(), dur = 1600;
  const tick = (now) => { const p = Math.min(1, (now - start) / dur); el.textContent = fmt(Math.round(target * (1 - Math.pow(1 - p, 4)))); if (p < 1) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
}

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

function stage(id) { return h('div', { class: 'stage' }, h('div', { class: 'dots' }, h('i'), h('i'), h('i')), h('canvas', { id })); }

function hub() {
  chrome('hub');
  const main = h('main'); document.body.append(main);
  const hero = h('section', { class: 'hero center' },
    h('span', { class: 'tag' }, 'Lab'),
    h('h1', { html: 'Des modèles.<br><em>Mesurés.</em>' }),
    h('p', { class: 'sub' }, 'Sept modèles, leurs duels, leurs chiffres.'),
    h('div', { class: 'btns' }, h('a', { class: 'btn', href: '#modeles', html: 'Voir les modèles ' + arrow }), h('a', { class: 'btn blue', href: '#duels' }, 'Qui joue contre qui')),
    stage('hero-canvas'));
  hero.querySelector('.stage').prepend(h('span', { class: 'path' }, '~/logic-lab/lab'));
  main.append(hero);
  const names = MODELS[0].games, belt = h('div', {}, [...names, ...names, ...names, ...names].map((g) => h('span', {}, g)));
  main.append(h('div', { class: 'marquee' }, belt));

  const cards = h('div', { class: 'cards' });
  MODELS.forEach((m) => {
    const cv = h('canvas');
    cards.append(h('a', { class: 'mcard reveal', href: m.page }, cv, h('div', { class: 'in' }, h('div', {}, h('h3', {}, m.name), h('small', {}, m.role.toUpperCase())), h('span', { class: 'go', html: arrow }))));
    requestAnimationFrame(() => mount(cv, m.scene, { hue: m.hue, hover: true }));
  });
  main.append(h('section', { id: 'modeles' }, h('div', { class: 'head' }, h('span', { class: 'tag' }, 'Modèles'), h('h2', { html: 'Un par <em>idée.</em>' })), cards));

  main.append(h('section', { id: 'duels' }, h('div', { class: 'head' }, h('span', { class: 'tag' }, 'Duels'), h('h2', { html: 'Qui joue <em>contre qui.</em>' }), h('p', { class: 'sub' }, 'Chaque trait est une série de parties mesurée. Touchez un trait ou un nœud.')),
    h('canvas', { id: 'graph' }), h('div', { id: 'edge-info' }, 'Aucun duel sélectionné.'),
    h('div', { class: 'legend' }, h('span', {}, h('i', { style: 'background:#7fa0ff' }), 'modèle'), h('span', {}, h('i', { style: 'background:#ff9a5c' }), 'juge'))));
  graph($('#graph'));

  main.append(h('section', {}, h('div', { class: 'head' }, h('span', { class: 'tag' }, 'Benchmark commun'), h('h2', { html: 'Un jeu, <em>tous</em> les modèles.' })), benchBlock(C4)));

  const st = h('div', { class: 'status' }, h('span', { class: 'pulse off' }), h('b', {}, 'Garry Optimus'), h('span', { class: 'muted', id: 'opt-status', style: 'color:var(--muted)' }, '…'));
  main.append(h('section', { class: 'center' }, h('span', { class: 'tag' }, 'Entraînement'), h('div', { style: 'margin-top:18px' }, st),
    h('div', { class: 'btns' }, h('a', { class: 'btn ghost', href: '/atelier.html' }, 'Atelier'), h('a', { class: 'btn ghost', href: '/' }, 'Arène'))));
  fetch(OPTIMUS_STATUS, { cache: 'no-store' }).then((r) => r.ok ? r.json() : Promise.reject()).then((s) => { $('#opt-status').textContent = s.text; if (s.running) st.querySelector('.pulse').classList.remove('off'); }).catch(() => { $('#opt-status').textContent = 'aucun statut'; });
  mount($('#hero-canvas'), 'field', { hue: 220 });
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
  const sel = (i) => { hover = i; if (i == null) { info.textContent = node ? `Duels de ${L(node)}` : 'Aucun duel sélectionné.'; return; } const e = EDGES[i]; info.innerHTML = `<b>${L(e[0])}</b> contre <b>${L(e[1])}</b> · ${e[2]} · <span style="color:#7fa0ff;font-family:var(--mono)">${e[3]}</span>`; };
  const pt = (ev) => { const r = cv.getBoundingClientRect(), p = ev.touches ? ev.touches[0] : ev; return [p.clientX - r.left, p.clientY - r.top]; };
  cv.addEventListener('mousemove', (ev) => { const [x, y] = pt(ev); cv.style.cursor = nodeAt(x, y) ? 'pointer' : 'default'; sel(edgeAt(x, y)); });
  cv.addEventListener('click', (ev) => { const [x, y] = pt(ev), n = nodeAt(x, y); node = n === node ? null : n; sel(n ? null : edgeAt(x, y)); });
  cv.addEventListener('touchstart', (ev) => sel(edgeAt(...pt(ev))), { passive: true });
  new ResizeObserver(place).observe(cv); place();
  const good = (e) => !/défaite|0,425|0,17|0,20|0,39/.test(e[3]);
  const draw = (now) => { const t = (now - t0) / 1000; ctx.clearRect(0, 0, W, H);
    EDGES.forEach((e, i) => { const [ax, ay] = pos[e[0]], [bx, by] = pos[e[1]], on = hover === i || (node && (e[0] === node || e[1] === node)), dim = (node && !on) || (hover != null && hover !== i), mx = (ax + bx) / 2;
      ctx.strokeStyle = on ? '#7fa0ff' : `rgba(122,133,166,${dim ? .1 : .38})`; ctx.lineWidth = on ? 3 : good(e) ? 2.2 : 1.1; ctx.beginPath(); ctx.moveTo(ax, ay); ctx.bezierCurveTo(mx, ay, mx, by, bx, by); ctx.stroke();
      const u = (t * .25 + i * .13) % 1, x = (1 - u) ** 3 * ax + 3 * (1 - u) ** 2 * u * mx + 3 * (1 - u) * u * u * mx + u ** 3 * bx, y = (1 - u) ** 3 * ay + 3 * (1 - u) ** 2 * u * ay + 3 * (1 - u) * u * u * by + u ** 3 * by;
      if (!dim) { ctx.fillStyle = on ? '#fff' : '#7fa0ff'; ctx.beginPath(); ctx.arc(x, y, on ? 4 : 2.4, 0, 6.3); ctx.fill(); } });
    NODES.forEach((n) => { const [x, y] = pos[n.id], m = n.kind === 'model', dim = node && node !== n.id && !EDGES.some((e) => (e[0] === node && e[1] === n.id) || (e[1] === node && e[0] === n.id));
      ctx.globalAlpha = dim ? .25 : 1; ctx.fillStyle = m ? '#7fa0ff' : '#ff9a5c'; ctx.beginPath(); ctx.arc(x, y, m ? 11 : 8, 0, 6.3); ctx.fill();
      if (m) { ctx.strokeStyle = '#4d7cff66'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, 17 + 3 * Math.sin(t * 2 + x), 0, 6.3); ctx.stroke(); }
      ctx.fillStyle = '#eef1fa'; ctx.font = '13px Inter,Arial'; ctx.textAlign = m ? 'right' : 'left'; ctx.textBaseline = 'middle'; ctx.fillText(n.label, x + (m ? -26 : 17), y); ctx.globalAlpha = 1; });
    requestAnimationFrame(draw); };
  requestAnimationFrame(draw);
}

function modelPage(id) {
  const i = MODELS.findIndex((m) => m.id === id), m = MODELS[i];
  document.documentElement.style.setProperty('--hue', m.hue);
  document.title = `${m.name} · Logic Lab`;
  chrome(id);
  const main = h('main'); document.body.append(main);
  const stats = h('div', { class: 'stats' }, m.stats.map((s) => h('div', { class: 'stat' }, h('b', {}, '0'), h('span', {}, s.l))));
  const [first, ...rest] = m.name.split(' ');
  const hero = h('section', { class: 'hero center' }, h('span', { class: 'tag' }, m.role),
    h('h1', { html: rest.length ? `${first} <em>${rest.join(' ')}</em>` : `<em>${first}</em>` }), h('p', { class: 'sub' }, m.tagline), stats, stage('scene'));
  hero.querySelector('.stage').prepend(h('span', { class: 'path' }, `~/logic-lab/${m.id}`));
  main.append(hero);
  m.stats.forEach((s, k) => counter(stats.children[k].firstChild, s.v, s.fmt));

  const pipe = h('div', { class: 'pipe' }, m.system.map(([t]) => h('div', { class: 'step' }, h('i'), t)));
  const desc = h('div', { id: 'step-desc' });
  main.append(h('section', {}, h('div', { class: 'head' }, h('span', { class: 'tag' }, 'Système'), h('h2', { html: 'Comment <em>ça marche.</em>' })), pipe, desc));
  const steps = [...pipe.children], set = (k) => { steps.forEach((s, j) => s.classList.toggle('lit', j === k)); desc.textContent = '› ' + m.system[k][1]; }; let timer = 0, cur = 0;
  new IntersectionObserver((e) => { clearInterval(timer); if (e[0].isIntersecting) { set(cur); timer = setInterval(() => set(cur = (cur + 1) % steps.length), 2600); } }, { threshold: .4 }).observe(pipe);
  steps.forEach((s, k) => s.addEventListener('mouseenter', () => { clearInterval(timer); set(cur = k); }));

  main.append(h('section', {}, h('div', { class: 'head' }, h('span', { class: 'tag' }, 'Arguments'), h('h2', { html: 'Ce que les chiffres <em>disent.</em>' })),
    h('div', { class: 'acc reveal' }, m.args.map(([t, d, c], k) => h('details', k === 0 ? { open: '' } : {}, h('summary', {}, h('span', { class: 'badge ' + c, title: CONF[c][1] }, CONF[c][0]), t), h('p', {}, d))))));

  main.append(h('section', {}, h('div', { class: 'head' }, h('span', { class: 'tag' }, 'Duels'), h('h2', { html: 'Contre <em>qui.</em>' })),
    h('div', { class: 'duels reveal' }, m.duels.map(([a, b, g, r]) => h('div', { class: 'duel' }, h('div', {}, h('b', {}, a), h('span', { class: 'vs' }, ' contre '), h('b', {}, b)), h('div', { class: 'g' }, g), h('div', { class: 'r' }, r))))));

  main.append(h('section', { id: 'bench' }, h('div', { class: 'head' }, h('span', { class: 'tag' }, 'Benchmarks'), h('h2', { html: 'Les <em>chiffres.</em>' })), m.bench.map(benchBlock)));

  const prev = MODELS[(i + MODELS.length - 1) % MODELS.length], next = MODELS[(i + 1) % MODELS.length];
  main.append(h('section', {}, h('details', { class: 'more' }, h('summary', {}, 'Limites et sources'), h('ul', {}, m.limits.map((l) => h('li', {}, l))), h('p', {}, m.src.map((s) => [h('code', {}, s), ' ']))),
    h('div', { class: 'pager', style: 'margin-top:40px' }, h('a', { href: prev.page }, '← ' + prev.short), h('a', { href: '/lab.html' }, 'Le Lab'), h('a', { href: next.page }, next.short + ' →'))));
  mount($('#scene'), m.scene, { hue: m.hue });
  reveals();
}

const page = document.body.dataset.page;
if (page === 'hub') hub(); else if (page) modelPage(page);

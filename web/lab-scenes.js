// Scènes animées (canvas 2D) : une par modèle. Chaque scène est une fonction (ctx, w, h, t, S, c) appelée à chaque image.
// S est un état persistant propre à la scène ; c = couleur d'accent (hsl). Aucune dépendance.
const TAU = Math.PI * 2;
const rng = (seed) => () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const ease = (x) => x * x * (3 - 2 * x);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const hsl = (h, s, l, a = 1) => `hsl(${h} ${s}% ${l}% / ${a})`;
const glow = (ctx, x, y, r, col) => { const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, col); g.addColorStop(1, 'transparent'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); };
const line = (ctx, a, b, col, w = 1) => { ctx.strokeStyle = col; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); };
const text = (ctx, s, x, y, size, col, align = 'center', font = 'ui-monospace,Consolas,monospace') => { ctx.font = `${size}px ${font}`; ctx.fillStyle = col; ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.fillText(s, x, y); };

// ---------- Garry : 4 872 -> 48 -> 48 -> 4 259, impulsions le long des connexions ----------
function garry(ctx, w, h, t, S, H) {
  if (!S.n) { const r = rng(7); S.cols = [26, 16, 16, 22].map((n) => Array.from({ length: n }, () => r())); S.n = 1; S.pulses = []; S.games = ['Morpion', '2048', 'Sudoku', 'Puissance 4', 'Démineur', 'Taquin', 'Reversi', 'Nim', 'Lights Out', 'Dames', 'Percée', 'Hex', 'Gomoku', 'Go']; }
  const xs = [0.14, 0.38, 0.62, 0.86], pos = S.cols.map((c, i) => c.map((_, j) => [w * xs[i], h * (0.14 + 0.72 * (j + 0.5) / c.length)]));
  const labels = ['4 872', '48', '48', '4 259'];
  for (let i = 0; i < 3; i++) for (let a = 0; a < pos[i].length; a += 2) for (let b = 0; b < pos[i + 1].length; b += 3) line(ctx, pos[i][a], pos[i + 1][b], hsl(H, 40, 50, .07));
  if (Math.random() < .35 && S.pulses.length < 40) { const i = Math.floor(Math.random() * 3), a = Math.floor(Math.random() * pos[i].length), b = Math.floor(Math.random() * pos[i + 1].length); S.pulses.push({ i, a, b, p: 0 }); }
  S.pulses = S.pulses.filter((q) => q.p < 1);
  for (const q of S.pulses) { q.p += .018; const A = pos[q.i][q.a], B = pos[q.i + 1][q.b], x = A[0] + (B[0] - A[0]) * q.p, y = A[1] + (B[1] - A[1]) * q.p; line(ctx, A, [x, y], hsl(H, 80, 70, .5), 1.4); glow(ctx, x, y, 12, hsl(H, 90, 70, .8)); }
  pos.forEach((col, i) => col.forEach((p, j) => { const act = .5 + .5 * Math.sin(t * 1.7 + j * .8 + i * 1.3); ctx.fillStyle = hsl(H, 70, 35 + act * 40); ctx.beginPath(); ctx.arc(p[0], p[1], i === 1 || i === 2 ? 5.5 : 3.6, 0, TAU); ctx.fill(); }));
  labels.forEach((l, i) => text(ctx, l, w * xs[i], h * .07, 12, hsl(H, 60, 75)));
  text(ctx, ['entrée', 'cœur', 'cœur', 'coups'][0], w * xs[0], h * .94, 10, '#8fb09f'); text(ctx, 'module commun', w * .5, h * .94, 10, '#8fb09f'); text(ctx, 'coups légaux', w * xs[3], h * .94, 10, '#8fb09f');
  const g = S.games[Math.floor(t / 1.1) % S.games.length], k = (t / 1.1) % 1;
  text(ctx, g, w * .5, h * .5, Math.min(w, h) * .07, hsl(H, 80, 80, Math.sin(k * Math.PI) * .55));
}

// ---------- Optimus : cinq jeux -> un tronc partagé -> têtes ----------
function optimus(ctx, w, h, t, S, H) {
  const ys = [0.14, 0.32, 0.5, 0.68, 0.86], bx = w * .13, tx = w * .52, hx = w * .86;
  const names = ['Morpion', 'Puissance 4', 'Hex', 'Gomoku', 'Dames'];
  const bs = Math.min(w * .1, h * .12);
  const board = (i, cx, cy) => {
    ctx.save(); ctx.translate(cx, cy); ctx.strokeStyle = hsl(H, 50, 65, .8); ctx.lineWidth = 1;
    if (i === 0) { for (let k = 1; k < 3; k++) { line(ctx, [-bs / 2 + k * bs / 3, -bs / 2], [-bs / 2 + k * bs / 3, bs / 2], ctx.strokeStyle); line(ctx, [-bs / 2, -bs / 2 + k * bs / 3], [bs / 2, -bs / 2 + k * bs / 3], ctx.strokeStyle); } }
    if (i === 1) { for (let r = 0; r < 6; r++) for (let c = 0; c < 7; c++) { ctx.fillStyle = (r + c + Math.floor(t)) % 5 === 0 ? hsl(H, 80, 60) : hsl(H, 30, 30, .6); ctx.beginPath(); ctx.arc(-bs / 2 + c * bs / 6.5, -bs / 2.4 + r * bs / 6.5, bs / 18, 0, TAU); ctx.fill(); } }
    if (i === 2) { for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) { ctx.fillStyle = (r * 3 + c + Math.floor(t * 1.3)) % 7 === 0 ? hsl(H, 80, 60) : hsl(H, 30, 30, .6); ctx.beginPath(); ctx.arc(-bs / 2 + c * bs / 3 + r * bs / 9, -bs / 2.4 + r * bs / 4.5, bs / 14, 0, TAU); ctx.fill(); } }
    if (i === 3) { for (let k = 0; k < 5; k++) { line(ctx, [-bs / 2 + k * bs / 4, -bs / 2], [-bs / 2 + k * bs / 4, bs / 2], ctx.strokeStyle); line(ctx, [-bs / 2, -bs / 2 + k * bs / 4], [bs / 2, -bs / 2 + k * bs / 4], ctx.strokeStyle); } }
    if (i === 4) { for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) if ((r + c) % 2) { ctx.fillStyle = hsl(H, 40, 40, .7); ctx.fillRect(-bs / 2 + c * bs / 4, -bs / 2 + r * bs / 4, bs / 4, bs / 4); } }
    ctx.restore();
  };
  // faisceaux
  ys.forEach((y, i) => {
    const sy = h * y, ph = (t * .5 + i * .2) % 1;
    ctx.strokeStyle = hsl(H, 50, 55, .25); ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(bx + bs, sy); ctx.bezierCurveTo(w * .3, sy, w * .3, h * .5, tx - w * .08, h * .5); ctx.stroke();
    const u = ph, x = (1 - u) ** 3 * (bx + bs) + 3 * (1 - u) ** 2 * u * w * .3 + 3 * (1 - u) * u * u * w * .3 + u ** 3 * (tx - w * .08), yy = (1 - u) ** 3 * sy + 3 * (1 - u) ** 2 * u * sy + 3 * (1 - u) * u * u * h * .5 + u ** 3 * h * .5;
    glow(ctx, x, yy, 10, hsl(H, 90, 65, .9));
    board(i, bx, sy); text(ctx, names[i], bx, sy + bs * .72, 10, '#9fbfae');
  });
  // tronc : 6 blocs résiduels
  for (let k = 0; k < 6; k++) { const bxk = tx - w * .08 + k * (w * .032), act = clamp(Math.sin(t * 2.2 - k * .7) * .5 + .6), bh = h * .44; ctx.fillStyle = hsl(H, 70, 25 + act * 35); ctx.fillRect(bxk, h * .5 - bh / 2, w * .024, bh); }
  text(ctx, 'tronc partagé · 6 × 64', tx + w * .02, h * .5 + h * .28, 11, hsl(H, 70, 78));
  // têtes
  ys.forEach((y, i) => { const sy = h * y; ctx.strokeStyle = hsl(H, 50, 55, .25); ctx.beginPath(); ctx.moveTo(tx + w * .12, h * .5); ctx.bezierCurveTo(w * .72, h * .5, w * .72, sy, hx - w * .04, sy); ctx.stroke(); const act = clamp(Math.sin(t * 2 - i) * .5 + .5); ctx.fillStyle = hsl(H, 80, 40 + act * 35); ctx.beginPath(); ctx.roundRect(hx - w * .04, sy - 9, w * .09, 18, 5); ctx.fill(); text(ctx, 'coup', hx + w * .005, sy, 9, '#0b211c'); });
  text(ctx, '5 jeux, 1 réseau', w * .5, h * .94, 11, '#8fb09f');
}

// ---------- Zéro : un arbre de recherche (MCTS) qui pousse, puis le meilleur chemin ----------
function zero(ctx, w, h, t, S, H) {
  const T = 9, ph = (t % T) / T;
  if (S.k === undefined || Math.floor(t / T) !== S.k) { S.k = Math.floor(t / T); const r = rng(11 + S.k * 31); S.nodes = [{ x: .5, y: .08, d: 0, p: -1, v: 1 }]; for (let i = 1; i < 90; i++) { const p = Math.floor(Math.pow(r(), 1.6) * Math.min(i, 40)); const par = S.nodes[p]; if (par.d >= 5) { i--; continue; } const kids = S.nodes.filter((n) => n.p === p).length; S.nodes.push({ x: par.x + (r() - .5) * .42 / (par.d + 1) + (kids - 1) * .02, y: .08 + (par.d + 1) * .17, d: par.d + 1, p, v: 1 }); } for (let i = S.nodes.length - 1; i > 0; i--) S.nodes[S.nodes[i].p].v += S.nodes[i].v; }
  const upto = Math.floor(clamp(ph / .7) * S.nodes.length), best = new Set();
  let cur = 0; best.add(0); for (;;) { const kids = S.nodes.map((n, i) => [n, i]).filter(([n, i]) => n.p === cur && i < upto); if (!kids.length) break; cur = kids.sort((a, b) => b[0].v - a[0].v)[0][1]; best.add(cur); }
  const P = (n) => [n.x * w, n.y * h];
  S.nodes.slice(0, upto).forEach((n, i) => { if (n.p >= 0) line(ctx, P(S.nodes[n.p]), P(n), best.has(i) && ph > .72 ? hsl(H, 90, 70, .95) : hsl(H, 40, 60, .22), best.has(i) && ph > .72 ? 2.4 : 1); });
  S.nodes.slice(0, upto).forEach((n, i) => { const [x, y] = P(n), r = 3 + Math.min(11, Math.sqrt(n.v) * 1.5), age = clamp((upto - i) / 8); ctx.fillStyle = best.has(i) && ph > .72 ? hsl(H, 90, 65) : hsl(H, 60, 30 + 30 * (n.v / S.nodes[0].v) ** .4, .9); ctx.beginPath(); ctx.arc(x, y, r * ease(Math.min(1, age + .3)), 0, TAU); ctx.fill(); });
  glow(ctx, w * .5, h * .08, 30, hsl(H, 90, 65, .3));
  text(ctx, `simulations : ${upto}`, w * .12, h * .94, 11, hsl(H, 70, 78), 'left');
  text(ctx, ph > .72 ? 'meilleur chemin choisi' : 'la recherche explore…', w * .88, h * .94, 11, '#8fb09f', 'right');
  text(ctx, 'auto-jeu → réseau → meilleure recherche → …', w * .5, h * .975, 9, '#5f8472');
}

// ---------- Maths : un calcul qui s'écrit étape par étape ----------
function maths(ctx, w, h, t, S, H) {
  const probs = [[['(3 + 4) × 2 − 5', '7 × 2 − 5', '14 − 5', '9']], [['2x + 6 = 20', '2x = 14', 'x = 7']], [['8 + 12 ÷ 4 × 3', '8 + 3 × 3', '8 + 9', '17']], [['(25 − 7) ÷ 3', '18 ÷ 3', '6']]].map((x) => x[0]);
  const T = 8, k = Math.floor(t / T) % probs.length, ph = (t % T), steps = probs[k], fs = Math.min(w * .05, 34);
  // attention en arrière-plan
  for (let i = 0; i < 14; i++) { const a = (i / 14) * TAU + t * .15; ctx.strokeStyle = hsl(H, 60, 60, .06); ctx.beginPath(); ctx.arc(w * .5, h * .5, Math.min(w, h) * (.22 + .03 * i), a, a + 1.4); ctx.stroke(); }
  steps.forEach((s, i) => {
    const start = i * (T / (steps.length + .6)), loc = ph - start; if (loc < 0) return;
    const n = Math.min(s.length, Math.floor(loc * 9)), y = h * (.26 + i * .15), done = n >= s.length;
    const arrow = i > 0 ? clamp(loc * 3) : 0;
    if (i > 0) text(ctx, '↓', w * .5, y - h * .075, fs * .7, hsl(H, 80, 70, arrow));
    ctx.fillStyle = hsl(H, 70, 25, .35 * Math.min(1, loc * 2)); ctx.beginPath(); ctx.roundRect(w * .1, y - fs * .85, w * .8, fs * 1.7, 14); ctx.fill();
    text(ctx, s.slice(0, n) + (!done && Math.floor(t * 4) % 2 ? '▍' : ''), w * .5, y, fs, i === steps.length - 1 && done ? hsl(H, 90, 78) : '#e9f3e2', 'center', 'ui-monospace,Consolas,monospace');
    if (done) { ctx.fillStyle = hsl(H, 80, 60); ctx.beginPath(); ctx.arc(w * .86, y, 7, 0, TAU); ctx.fill(); text(ctx, '✓', w * .86, y + .5, 10, '#0b211c'); }
  });
  text(ctx, 'étape suivante · vérifiée par un évaluateur indépendant', w * .5, h * .94, 11, '#8fb09f');
}

// ---------- Loop : un sudoku 6x6 qui converge à chaque passe ----------
function loop(ctx, w, h, t, S, H) {
  const sol = [[1, 2, 3, 4, 5, 6], [4, 5, 6, 1, 2, 3], [2, 3, 1, 5, 6, 4], [5, 6, 4, 2, 3, 1], [3, 1, 2, 6, 4, 5], [6, 4, 5, 3, 1, 2]];
  const N = 16, T = 12, ph = (t % T) / T, pass = Math.min(N, Math.floor(ph / .85 * N)), r = rng(5 + Math.floor(t / T) * 13);
  if (S.k !== Math.floor(t / T)) { S.k = Math.floor(t / T); S.given = Array.from({ length: 36 }, () => r() < .45); S.conf = Array.from({ length: 36 }, () => r() * 6 + 2); }
  const cs = Math.min(w, h) * .105, gx = w * .12, gy = h * .12;
  for (let i = 0; i < 36; i++) {
    const rr = Math.floor(i / 6), cc = i % 6, x = gx + cc * cs, y = gy + rr * cs; const ok = S.given[i] || pass >= S.conf[i];
    ctx.fillStyle = S.given[i] ? hsl(H, 30, 22) : ok ? hsl(H, 60, 30, .8) : hsl(25, 70, 40, .7); ctx.fillRect(x + 2, y + 2, cs - 4, cs - 4);
    const wrong = ((i * 7 + pass * 3) % 6) + 1, v = ok ? sol[rr][cc] : wrong;
    text(ctx, String(v), x + cs / 2, y + cs / 2 + 1, cs * .5, S.given[i] ? '#e9f3e2' : ok ? hsl(H, 90, 78) : hsl(25, 90, 75, .8), 'center', 'Inter,Arial');
  }
  for (let k = 0; k < 7; k++) { const y = gy + k * cs, thick = k % 3 === 0 ? 2.6 : 1; line(ctx, [gx, y], [gx + 6 * cs, y], hsl(H, 40, 60, .6), thick); const x = gx + k * (cs); line(ctx, [x, gy], [x, gy + 6 * cs], hsl(H, 40, 60, .6), k % 2 === 0 ? 2.6 : 1); }
  // barres des cases fausses par passe
  const bx = w * .66, bw = w * .3, by = h * .14, bh = h * .52;
  text(ctx, 'cases fausses par passe', bx + bw / 2, by - 14, 11, '#8fb09f');
  for (let p = 0; p < N; p++) { const wrongN = S.given.reduce((a, g, i) => a + (!g && p < S.conf[i] ? 1 : 0), 0), nonGiven = S.given.filter((g) => !g).length || 1, bhh = (wrongN / nonGiven) * bh, x = bx + p * (bw / N); ctx.fillStyle = p <= pass ? hsl(p === pass ? 25 : H, 70, 55) : hsl(H, 30, 25, .5); ctx.fillRect(x, by + bh - bhh, bw / N - 3, bhh); }
  text(ctx, `passe ${pass}/${N}`, bx + bw / 2, h * .74, 20, hsl(H, 80, 78));
  // flèche récurrente
  ctx.strokeStyle = hsl(H, 80, 65, .8); ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(w * .5 - 4, h * .88, 16, -Math.PI * .8 + t * 3, Math.PI * .8 + t * 3); ctx.stroke();
  text(ctx, 'mêmes poids, repassés', w * .5 + 28, h * .88, 11, '#8fb09f', 'left');
}

// ---------- Graine : un réseau qui pousse puis s'élague ----------
function graine(ctx, w, h, t, S, H) {
  const T = 14, ph = (t % T) / T, grow = ease(clamp(ph / .55)), prune = ease(clamp((ph - .62) / .3));
  const sizes = [3, 2 + Math.round(grow * 12) - Math.round(prune * 5), 2 + Math.round(grow * 12) - Math.round(prune * 5), 2];
  const xs = [.16, .4, .64, .88]; const r = rng(3);
  const pts = sizes.map((n, i) => Array.from({ length: Math.max(1, n) }, (_, j) => [w * xs[i], h * (.18 + .62 * (j + .5) / Math.max(1, n))]));
  for (let i = 0; i < 3; i++) for (const a of pts[i]) for (const b of pts[i + 1]) line(ctx, a, b, hsl(H, 50, 60, .1));
  pts.forEach((col, i) => col.forEach((p, j) => { const newborn = i > 0 && i < 3 && j >= 2 && ph < .55; const dying = prune > 0 && i > 0 && i < 3 && j > col.length - 3; ctx.fillStyle = dying ? hsl(25, 80, 55, 1 - prune * .5) : newborn ? hsl(H, 90, 70) : hsl(H, 60, 45); ctx.beginPath(); ctx.arc(p[0], p[1], 6 + (newborn ? 2 * Math.sin(t * 6 + j) : 0), 0, TAU); ctx.fill(); if (newborn) glow(ctx, p[0], p[1], 18, hsl(H, 90, 70, .35)); }));
  const params = (3 * sizes[1] + sizes[1] * sizes[2] + sizes[2] * 2) + sizes[1] + sizes[2] + 2;
  text(ctx, `${sizes[1]} + ${sizes[2]} neurones · ${params} paramètres`, w * .5, h * .06, 12, hsl(H, 70, 78));
  text(ctx, ph < .58 ? 'croissance : la validation stagne → +2 neurones' : 'élagage : extinction sans coût → on retire', w * .5, h * .93, 11, '#8fb09f');
  ctx.strokeStyle = hsl(H, 60, 55, .8); ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(w * .1, h * .88); for (let x = 0; x <= 1; x += .02) { const y = .88 - .08 * (1 - Math.exp(-x * 5)) * (x <= ph ? 1 : 0); ctx.lineTo(w * (.1 + .8 * x), h * y); if (x > ph) break; } ctx.stroke();
}

// ---------- Moteurs : un plateau de Hex, les ponts et le plus court chemin ----------
function moteurs(ctx, w, h, t, S, H) {
  const n = 7, hs = Math.min(w / (n * 1.74 * 1.62), h * .068), ox = w * .5 - (n - 1) * .75 * 1.74 * hs, oy = h * .2, T = 10, ph = (t % T) / T;
  const P = (r, c) => [ox + (c + r * .5) * hs * 1.74, oy + r * hs * 1.5];
  if (S.k !== Math.floor(t / T)) { S.k = Math.floor(t / T); const q = rng(19 + S.k * 7); S.path = []; let c = Math.floor(q() * n); for (let r = 0; r < n; r++) { S.path.push([r, c]); c = Math.max(0, Math.min(n - 1, c + (q() < .5 ? -1 : 0) + (q() < .5 ? 1 : 0) - (r % 2 ? 0 : 0))); } S.stones = []; for (let i = 0; i < 9; i++) S.stones.push([Math.floor(q() * n), Math.floor(q() * n), i % 2]); }
  // bords
  ctx.fillStyle = hsl(H, 70, 55, .35); ctx.fillRect(ox - hs, oy - hs * 1.25, (n - 1) * 1.74 * hs + hs * 2, 5); ctx.fillStyle = hsl(25, 70, 55, .35); ctx.fillRect(ox + (n - 1) * .5 * 1.74 * hs - hs, oy + (n - 1) * hs * 1.5 + hs * 1.15, (n - 1) * 1.74 * hs + hs * 2, 5);
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const [x, y] = P(r, c); ctx.beginPath(); for (let k = 0; k < 6; k++) { const a = TAU / 6 * k - Math.PI / 2; ctx.lineTo(x + hs * Math.cos(a), y + hs * Math.sin(a)); } ctx.closePath(); ctx.fillStyle = hsl(H, 25, 18, .8); ctx.fill(); ctx.strokeStyle = hsl(H, 40, 50, .35); ctx.lineWidth = 1; ctx.stroke(); }
  S.stones.forEach(([r, c, who], i) => { if (ph < i / 14) return; const [x, y] = P(r, c); ctx.fillStyle = who ? hsl(25, 80, 60) : hsl(H, 70, 70); ctx.beginPath(); ctx.arc(x, y, hs * .55 * ease(clamp((ph - i / 14) * 8)), 0, TAU); ctx.fill(); });
  const L = Math.floor(clamp((ph - .25) / .5) * S.path.length);
  for (let i = 0; i < L; i++) { const [r, c] = S.path[i], [x, y] = P(r, c); glow(ctx, x, y, hs * 1.3, hsl(H, 90, 65, .45)); if (i) line(ctx, P(...S.path[i - 1]), [x, y], hsl(H, 90, 75, .9), 3); ctx.fillStyle = hsl(H, 90, 78); ctx.beginPath(); ctx.arc(x, y, hs * .3, 0, TAU); ctx.fill(); }
  // bandeau alpha-bêta
  const by = h * .84; for (let i = 0; i < 9; i++) { const x = w * (.14 + i * .09), d = Math.sin(t * 2 + i) * .5 + .5; line(ctx, [w * .5, by - 12], [x, by + 12], hsl(H, 50, 60, .25)); ctx.fillStyle = i === Math.floor(t * 2) % 9 ? hsl(25, 80, 60) : hsl(H, 60, 30 + d * 25); ctx.beginPath(); ctx.arc(x, by + 14, 5, 0, TAU); ctx.fill(); }
  text(ctx, 'alpha-bêta · coupures', w * .5, h * .95, 11, '#8fb09f');
  text(ctx, 'ponts et bords virtuels', w * .5, h * .06, 11, hsl(H, 70, 78));
}

// ---------- Fond du Lab : un réseau de particules reliées ----------
function field(ctx, w, h, t, S, H) {
  if (!S.p) { const r = rng(2); S.p = Array.from({ length: 70 }, () => ({ x: r(), y: r(), vx: (r() - .5) * .0004, vy: (r() - .5) * .0004, k: Math.floor(r() * 4) })); }
  for (const q of S.p) { q.x = (q.x + q.vx * 16 + 1) % 1; q.y = (q.y + q.vy * 16 + 1) % 1; }
  for (let i = 0; i < S.p.length; i++) for (let j = i + 1; j < S.p.length; j++) { const a = S.p[i], b = S.p[j], d = Math.hypot((a.x - b.x) * w, (a.y - b.y) * h); if (d < w * .14) line(ctx, [a.x * w, a.y * h], [b.x * w, b.y * h], hsl(H + a.k * 30, 60, 60, (1 - d / (w * .14)) * .35)); }
  for (const q of S.p) { ctx.fillStyle = hsl(H + q.k * 30, 80, 70, .9); ctx.beginPath(); ctx.arc(q.x * w, q.y * h, 2.4, 0, TAU); ctx.fill(); }
}

export const SCENES = { garry, optimus, zero, maths, loop, graine, moteurs, field };

// Monte une scène sur un canvas. Anime seulement quand il est visible (et au survol si `hover`).
// Respecte prefers-reduced-motion : une image fixe.
export function mount(canvas, name, { hue = 96, hover = false } = {}) {
  const ctx = canvas.getContext('2d'), fn = SCENES[name], S = {};
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let vis = !hover, hot = !hover, raf = 0, t0 = performance.now(), frozen = 0;
  const size = () => { const d = Math.min(devicePixelRatio || 1, 2), r = canvas.getBoundingClientRect(); canvas.width = Math.max(2, r.width * d); canvas.height = Math.max(2, r.height * d); ctx.setTransform(d, 0, 0, d, 0, 0); return [r.width, r.height]; };
  let [w, h] = size();
  const draw = (t) => { ctx.clearRect(0, 0, w, h); try { fn(ctx, w, h, t, S, hue); } catch (e) { console.error(e); } };
  const loop = (now) => { raf = 0; const t = (now - t0) / 1000 + frozen; draw(t); if (!reduce && vis && hot) raf = requestAnimationFrame(loop); };
  const kick = () => { if (!raf) { t0 = performance.now() - frozen * 1000; raf = requestAnimationFrame(loop); } };
  new ResizeObserver(() => { [w, h] = size(); draw(frozen); if (vis && hot) kick(); }).observe(canvas);
  new IntersectionObserver((e) => { vis = e[0].isIntersecting; if (vis && hot) kick(); }, { threshold: .05 }).observe(canvas);
  if (hover) { const host = canvas.closest('a,section,div') || canvas; host.addEventListener('mouseenter', () => { hot = true; kick(); }); host.addEventListener('mouseleave', () => { hot = false; }); frozen = 3.2; }
  draw(frozen || 3.2); if (!hover) kick();
}

// Pont entre les moteurs de multi (TypeScript pur) et Python : processus persistant, un objet JSON par ligne sur stdin, une réponse par ligne sur stdout.
// Les états restent côté Node (poignées entières) : seuls la vue, les coups légaux et les résultats traversent le pont.
// Opérations : games | init | view | legal | apply | bot | outcome | free | playout (partie complète avec bots/hasard, côté Node).
// Usage : node bridge.mjs [chemin/vers/multi]    (défaut : variable MULTI_DIR ou C:/Users/gabor/code/multi)
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const multi = resolve(process.argv[2] ?? process.env.MULTI_DIR ?? 'C:/Users/gabor/code/multi');
const engines = (rel) => import(pathToFileURL(resolve(multi, 'packages/engines/src', rel)).href);
const { registry } = await engines('registry.generated.ts');
const { Rng } = await engines('rng.ts');

const states = new Map();
let next = 1;
const keep = (game, state) => { const h = next++; states.set(h, { game, state }); return h; };
const def = (id) => { const g = registry[id]; if (!g) throw new Error(`jeu inconnu : ${id}`); return g; };
const get = (h) => { const s = states.get(h); if (!s) throw new Error(`poignée inconnue : ${h}`); return s; };
const players = (n) => Array.from({ length: n }, (_, seat) => ({ seat, name: `Joueur ${seat + 1}`, isBot: true }));
const guard = (fn) => { try { return fn(); } catch (e) { return { error: String(e?.message ?? e) }; } };

function snapshot(h, seat) {
  const { game, state } = get(h);
  const g = def(game);
  const active = g.activeSeats(state);
  const outcome = g.outcome(state);
  const s = seat ?? (active[0] ?? 0);
  return {
    h, active, over: outcome !== null, outcome,
    view: g.viewFor(state, s),
    legal: g.legalActions ? g.legalActions(state, s) : null,
  };
}

const ops = {
  games: () => Object.fromEntries(Object.entries(registry).map(([id, g]) => [id, {
    name: g.meta.name, minPlayers: g.meta.minPlayers, maxPlayers: g.meta.maxPlayers, solo: !!g.meta.solo,
    hasLegal: typeof g.legalActions === 'function', hasBot: !!g.bot, options: (g.options ?? []).map((o) => ({ key: o.key, default: o.default })),
  }])),
  init: (r) => {
    const g = def(r.game);
    const n = r.players ?? g.meta.minPlayers;
    const options = Object.fromEntries((g.options ?? []).map((o) => [o.key, o.default]));
    const state = g.init({ players: players(n), seed: r.seed ?? 1, options: { ...options, ...(r.options ?? {}) } });
    return snapshot(keep(r.game, state), r.seat);
  },
  view: (r) => snapshot(r.h, r.seat),
  legal: (r) => { const { game, state } = get(r.h); const g = def(game); return { legal: g.legalActions ? g.legalActions(state, r.seat) : null }; },
  apply: (r) => {
    const { game, state } = get(r.h);
    const res = def(game).apply(state, r.seat, r.action, { now: r.now ?? 0 });
    if (!res.ok) return { ok: false, error: res.error };
    return { ok: true, ...snapshot(keep(game, res.state), r.next_seat) };
  },
  bot: (r) => {
    const { game, state } = get(r.h);
    const g = def(game);
    if (!g.bot) return { action: null, hasBot: false };
    return { action: g.bot.act(state, r.seat, new Rng(r.seed ?? 7)), hasBot: true };
  },
  outcome: (r) => { const { game, state } = get(r.h); return { outcome: def(game).outcome(state) }; },
  free: (r) => { for (const h of r.hs) states.delete(h); return { freed: r.hs.length }; },
  // Partie complète côté Node : joueurs « bot » (bot de multi), « random » (coup légal au hasard) ; renvoie la trace compacte pour l'imitation.
  playout: (r) => {
    const g = def(r.game);
    const n = r.players ?? g.meta.minPlayers;
    const options = Object.fromEntries((g.options ?? []).map((o) => [o.key, o.default]));
    let state = g.init({ players: players(n), seed: r.seed ?? 1, options: { ...options, ...(r.options ?? {}) } });
    const rng = new Rng((r.seed ?? 1) * 7919 + 13);
    const kinds = r.kinds ?? Array(n).fill('random');
    const trace = [];
    for (let ply = 0; ply < (r.maxPlies ?? 400) && g.outcome(state) === null; ply++) {
      const active = g.activeSeats(state);
      if (!active.length) break;
      const seat = active[0];
      const legal = g.legalActions ? g.legalActions(state, seat) : null;
      let action = null;
      if (kinds[seat] === 'bot' && g.bot) action = g.bot.act(state, seat, rng);
      if (action === null && legal && legal.length) action = rng.pick(legal);
      if (action === null) break;
      if (r.record) trace.push({ seat, view: g.viewFor(state, seat), legal, action });
      const res = g.apply(state, seat, action, { now: 0 });
      if (!res.ok) { if (legal && legal.length) { const a = rng.pick(legal); const r2 = g.apply(state, seat, a, { now: 0 }); if (!r2.ok) break; state = r2.state; continue; } break; }
      state = res.state;
    }
    return { outcome: g.outcome(state), plies: trace.length, trace: r.record ? trace : undefined };
  },
};


// UCT générique (tout jeu au tour par tour où un seul joueur agit à la fois) : parties aléatoires jusqu'au bout, aucune connaissance du jeu.
// Valeurs dans [0, 1] du point de vue du joueur qui a choisi l'arête. Renvoie les coups légaux de la racine, leurs visites et leurs valeurs moyennes.
function seatValue(outcome, seat) {
  const groups = outcome.ranking;
  if (groups.length < 2) return 0.5;
  if (groups[0].includes(seat)) return 1;
  if (groups[groups.length - 1].includes(seat)) return 0;
  return 0.5;
}
function uct(h, seat, sims, seed, c = 1.4, maxRollout = 300) {
  const { game, state } = get(h);
  const g = def(game);
  const rng = new Rng(seed ?? 11);
  const key = (a) => JSON.stringify(a);
  const mk = (st) => {
    const out = g.outcome(st);
    const act = out ? [] : g.activeSeats(st);
    const s = act[0];
    return { st, out, seat: s, legal: out || s === undefined || !g.legalActions ? [] : g.legalActions(st, s), kids: new Map(), n: 0, w: new Map(), nn: new Map() };
  };
  const root = mk(state);
  if (root.seat !== seat) root.seat = seat, root.legal = g.legalActions ? g.legalActions(state, seat) : [];
  const rollout = (st) => {
    let cur = st;
    for (let i = 0; i < maxRollout; i++) {
      const out = g.outcome(cur);
      if (out) return out;
      const act = g.activeSeats(cur);
      if (!act.length) return null;
      const legal = g.legalActions(cur, act[0]);
      if (!legal.length) return null;
      let res = g.apply(cur, act[0], rng.pick(legal), { now: 0 });
      if (!res.ok) { res = g.apply(cur, act[0], legal[0], { now: 0 }); if (!res.ok) return null; }
      cur = res.state;
    }
    return null;
  };
  for (let sim = 0; sim < sims; sim++) {
    let node = root;
    const path = [];
    let out = null;
    for (;;) {
      if (node.out) { out = node.out; break; }
      if (!node.legal.length) break;
      // arête non essayée d'abord, sinon UCB1
      let pick = -1, best = -Infinity;
      for (let i = 0; i < node.legal.length; i++) {
        const k = key(node.legal[i]);
        const n = node.nn.get(k) ?? 0;
        if (n === 0) { pick = i; break; }
        const score = node.w.get(k) / n + c * Math.sqrt(Math.log(node.n + 1) / n);
        if (score > best) { best = score; pick = i; }
      }
      const a = node.legal[pick], k = key(a);
      path.push({ node, k });
      let child = node.kids.get(k);
      if (!child) {
        const res = g.apply(node.st, node.seat, a, { now: 0 });
        if (!res.ok) { node.legal.splice(pick, 1); path.pop(); continue; }
        child = mk(res.state);
        node.kids.set(k, child);
        out = child.out ?? rollout(child.st);
        break;
      }
      node = child;
    }
    for (const { node: nd, k } of path) {
      const v = out ? seatValue(out, nd.seat) : 0.5;
      nd.n++;
      nd.nn.set(k, (nd.nn.get(k) ?? 0) + 1);
      nd.w.set(k, (nd.w.get(k) ?? 0) + v);
    }
  }
  const legal = g.legalActions(state, seat);
  const keys = legal.map(key);
  return { actions: legal, visits: keys.map((k) => root.nn.get(k) ?? 0), q: keys.map((k) => (root.nn.get(k) ? root.w.get(k) / root.nn.get(k) : 0.5)) };
}
ops.uct = (r) => uct(r.h, r.seat, r.sims ?? 200, r.seed, r.c ?? 1.4, r.maxRollout ?? 300);

const rl = createInterface({ input: process.stdin });
for await (const line of rl) {
  if (!line.trim()) continue;
  let req;
  try { req = JSON.parse(line); } catch { process.stdout.write(JSON.stringify({ error: 'JSON invalide' }) + '\n'); continue; }
  const out = guard(() => ops[req.op] ? ops[req.op](req) : { error: `opération inconnue : ${req.op}` });
  process.stdout.write(JSON.stringify({ id: req.id, ...out }) + '\n');
}

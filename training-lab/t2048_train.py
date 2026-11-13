"""Garry Optimus apprend le 2048 : distillation d'un professeur expectimax (C++), puis DAgger (le réseau joue, le professeur étiquette
les positions que le réseau rencontre vraiment). Réseau seul à l'inférence : aucune recherche. Pas de limite à 2048.

Usage : python training-lab/t2048_train.py --minutes 50 [--out training-lab/models/unified/optimus-2048] [--depth 2]
Reprise : relancer avec le même --out (continue depuis last.pt et dataset.npz).
Sorties : last.pt, best.pt (meilleur sur le banc de parties du réseau seul), dataset.npz, log.jsonl ; statut dans web/optimus-2048-status.json."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from logic_arena import t2048 as T  # noqa: E402

DEV = "cuda" if torch.cuda.is_available() else "cpu"
NEG = -1e29


class Block(nn.Module):
    def __init__(self, ch):
        super().__init__()
        self.c1, self.b1 = nn.Conv2d(ch, ch, 3, padding=1, bias=False), nn.BatchNorm2d(ch)
        self.c2, self.b2 = nn.Conv2d(ch, ch, 3, padding=1, bias=False), nn.BatchNorm2d(ch)

    def forward(self, x):
        return F.relu(x + self.b2(self.c2(F.relu(self.b1(self.c1(x))))))


class Net2048(nn.Module):
    """Entrée : 17 plans (un par exposant de tuile, 0 = vide) sur la grille 4×4. Sortie : 4 logits (haut, bas, gauche, droite)."""

    def __init__(self, ch=128, blocks=6):
        super().__init__()
        self.ch, self.blocks = ch, blocks
        self.inp = nn.Sequential(nn.Conv2d(17, ch, 3, padding=1, bias=False), nn.BatchNorm2d(ch), nn.ReLU())
        self.trunk = nn.Sequential(*[Block(ch) for _ in range(blocks)])
        self.head = nn.Sequential(nn.Flatten(), nn.Linear(ch * 16, 256), nn.ReLU(), nn.Linear(256, 4))

    def forward(self, e):  # e : (N, 4, 4) exposants uint8
        x = F.one_hot(e.long().clamp(max=16), 17).permute(0, 3, 1, 2).float()
        return self.head(self.trunk(self.inp(x)))

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())


# ---------- symétries : 8 transformations de la grille, permutation des coups déterminée empiriquement ----------
def _sym(e, k):  # e : (N,4,4) numpy
    e = np.rot90(e, k % 4, axes=(1, 2))
    return np.flip(e, axis=2) if k >= 4 else e


def action_perms():
    rng = np.random.default_rng(0)
    boards = []
    for _ in range(400):
        e = np.zeros(16, dtype=np.uint8)
        k = int(rng.integers(4, 12))
        e[rng.choice(16, k, replace=False)] = rng.integers(1, 8, k)
        boards.append(int(T.pack_exponents(e)[0]))
    perms = []
    for k in range(8):
        perm = []
        for a in range(4):
            votes = np.zeros(4, int)
            for b in boards:
                nb = T.move(b, a)
                if nb == b:
                    continue
                target = _sym(T.exponents([nb]), k)[0]
                fb = int(T.pack_exponents(_sym(T.exponents([b]), k)[0].copy())[0])
                for a2 in range(4):
                    m = T.move(fb, a2)
                    if m != fb and np.array_equal(T.exponents([m])[0], target):
                        votes[a2] += 1
            perm.append(int(votes.argmax()))
        assert sorted(perm) == [0, 1, 2, 3], (k, perm)
        perms.append(perm)
    return perms


PERMS = None


def augment(E, Q, g):
    """Applique une symétrie aléatoire différente à chaque huitième du lot. E : (N,4,4) uint8 tensor ; Q : (N,4)."""
    n = len(E)
    out_e, out_q = [], []
    for k, idx in enumerate(torch.randperm(n, device=E.device, generator=g).chunk(8)):
        e, q = E[idx], Q[idx]
        e = torch.rot90(e, k % 4, dims=(1, 2))
        if k >= 4:
            e = torch.flip(e, dims=(2,))
        p = torch.tensor(PERMS[k], device=E.device)
        qn = torch.empty_like(q)
        qn[:, p] = q
        out_e.append(e)
        out_q.append(qn)
    return torch.cat(out_e), torch.cat(out_q)


def soft_target(Q, temp):
    legal = Q > NEG
    z = torch.where(legal, (Q - Q.masked_fill(~legal, -1e30).max(1, keepdim=True).values) / temp, torch.full_like(Q, -1e9))
    return torch.softmax(z, 1), legal


def train(net, opt, E, Q, steps, batch, temp, g, log):
    net.train()
    t0 = time.time()
    for s in range(1, steps + 1):
        idx = torch.randint(0, len(E), (batch,), device=E.device, generator=g)
        e, q = augment(E[idx], Q[idx], g)
        target, legal = soft_target(q, temp)
        logits = net(e).masked_fill(~legal, -1e9)
        loss = -(target * F.log_softmax(logits, 1)).sum(1).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if s % 500 == 0:
            acc = (logits.argmax(1) == target.argmax(1)).float().mean().item()
            log(f"  pas {s}/{steps} perte {loss.item():.4f} accord {acc:.3f} ({time.time() - t0:.0f}s)")
    net.eval()


@torch.no_grad()
def policy_moves(net, boards, eps, rng):
    e = torch.from_numpy(T.exponents(boards)).to(DEV)
    logits = net(e).float().cpu().numpy()
    mask = T.legal_masks(boards)
    legal = ((mask[:, None] >> np.arange(4)) & 1).astype(bool)
    logits = np.where(legal, logits, -1e9)
    d = logits.argmax(1)
    if eps > 0:
        rnd = rng.random(len(d)) < eps
        for i in np.where(rnd)[0]:
            ch = np.where(legal[i])[0]
            d[i] = rng.choice(ch) if len(ch) else d[i]
    return d, legal.any(1)


def play(net, n, cap, seed, eps=0.0, record_every=0, teacher_mix=0.0, depth=2):
    """n parties du réseau seul (ou mélangé au professeur). Renvoie exposants max, nombre de coups, et les positions enregistrées."""
    rng = np.random.default_rng(seed)
    seeds = rng.integers(1, 2**62, n, dtype=np.uint64)
    cur = T.new_boards(n, seeds)
    alive = np.ones(n, bool)
    moves = np.zeros(n, int)
    rec = []
    for step in range(cap):
        idx = np.where(alive)[0]
        if not len(idx):
            break
        if teacher_mix > 0:
            use_t = rng.random(len(idx)) < teacher_mix
        else:
            use_t = np.zeros(len(idx), bool)
        d, ok = policy_moves(net, cur[idx], eps, rng) if net is not None else (np.zeros(len(idx), int), np.ones(len(idx), bool))
        if use_t.any():
            v = T.values(cur[idx[use_t]], depth)
            d[use_t] = v.argmax(1)
        if record_every and step % record_every == 0:
            rec.append(cur[idx].copy())
        alive[idx[~ok]] = False
        idx, d = idx[ok], d[ok]
        if not len(idx):
            break
        s = np.ascontiguousarray(seeds[idx])
        cur[idx] = T.step(cur[idx], d, s)
        seeds[idx] = s
        moves[idx] += 1
    mx = T.exponents(cur).reshape(n, -1).max(1)
    return mx, moves, (np.concatenate(rec) if rec else np.zeros(0, np.uint64))


def label(boards, depth, chunk=4096):
    out = []
    for i in range(0, len(boards), chunk):
        out.append(T.values(boards[i:i + chunk], depth))
    return np.concatenate(out) if out else np.zeros((0, 4), np.float32)


def summary(mx):
    n = len(mx)
    return {"parties": n, "tuile_max_mediane": int(2 ** np.median(mx)), "pct_2048": round(float((mx >= 11).mean()), 3),
            "pct_4096": round(float((mx >= 12).mean()), 3), "pct_8192": round(float((mx >= 13).mean()), 3), "pct_1024": round(float((mx >= 10).mean()), 3)}


def main():
    global PERMS
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "training-lab" / "models" / "unified" / "optimus-2048"))
    ap.add_argument("--minutes", type=float, default=50)
    ap.add_argument("--depth", type=int, default=2, help="profondeur du professeur (coups regardés)")
    ap.add_argument("--channels", type=int, default=128)
    ap.add_argument("--blocks", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--teacher-games", type=int, default=48)
    ap.add_argument("--student-games", type=int, default=64)
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--temp", type=float, default=250.0, help="température du softmax sur les valeurs du professeur")
    ap.add_argument("--eval-games", type=int, default=48)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    status = ROOT / "web" / "optimus-2048-status.json"
    logf = open(out / "log.jsonl", "a", encoding="utf-8")
    t_start = time.time()

    def log(msg):
        print(msg, flush=True)

    def publish(text, running=True):
        try:
            status.write_text(json.dumps({"running": running, "text": text, "t": time.strftime("%Y-%m-%d %H:%M")}, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    torch.manual_seed(a.seed)
    PERMS = action_perms()
    log(f"permutations des coups par symétrie : {PERMS}")
    g = torch.Generator(device=DEV)
    g.manual_seed(a.seed)
    net = Net2048(a.channels, a.blocks).to(DEV)
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-4)
    log(f"réseau 2048 : {net.parameter_count():,} paramètres, appareil {DEV}")
    data_path = out / "dataset.npz"
    it = 0
    if (out / "last.pt").exists() and data_path.exists():
        blob = torch.load(out / "last.pt", map_location=DEV, weights_only=True)
        net.load_state_dict(blob["net"])
        it = blob["iteration"]
        d = np.load(data_path)
        B, Q = d["boards"], d["q"]
        log(f"reprise : itération {it}, {len(B):,} positions")
    else:
        publish("génération des parties du professeur")
        t0 = time.time()
        # parties du professeur avec un peu de bruit pour diversifier les positions
        mx, moves, B = play(None, a.teacher_games, 6000, a.seed + 1, teacher_mix=1.0, record_every=1, depth=a.depth)
        Q = label(B, a.depth)
        ok = (Q > NEG).any(1)
        B, Q = B[ok], Q[ok]
        log(f"professeur (profondeur {a.depth}) : {summary(mx)} ; {len(B):,} positions étiquetées en {time.time() - t0:.0f}s")
        logf.write(json.dumps({"phase": "professeur", **summary(mx), "positions": int(len(B))}) + "\n")
        logf.flush()
    best = -1.0
    if (out / "best.json").exists():
        best = json.loads((out / "best.json").read_text())["score"]
    while time.time() - t_start < a.minutes * 60:
        E = torch.from_numpy(T.exponents(B)).to(DEV)
        Qt = torch.from_numpy(Q).to(DEV)
        publish(f"itération {it}: apprentissage sur {len(B):,} positions")
        train(net, opt, E, Qt, a.steps, a.batch, a.temp, g, log)
        it += 1
        # banc : le réseau seul, sans recherche, sans bruit
        mx, moves, _ = play(net, a.eval_games, 12000, 10_000 + it)
        s = summary(mx)
        score = float(mx.mean())
        log(f"itération {it}: banc réseau seul {s} (coups moyens {int(moves.mean())})")
        logf.write(json.dumps({"phase": "banc", "iteration": it, "positions": int(len(B)), **s, "coups_moyens": int(moves.mean()), "minutes": round((time.time() - t_start) / 60, 1)}) + "\n")
        logf.flush()
        torch.save({"net": net.state_dict(), "iteration": it, "channels": a.channels, "blocks": a.blocks}, out / "last.pt")
        np.savez_compressed(data_path, boards=B, q=Q)
        if score > best:
            best = score
            torch.save({"net": net.state_dict(), "iteration": it, "channels": a.channels, "blocks": a.blocks, "bench": s}, out / "best.pt")
            (out / "best.json").write_text(json.dumps({"score": score, "iteration": it, **s}))
        publish(f"itération {it}: réseau seul, {int(s['pct_2048'] * 100)} % des parties ≥ 2048, {int(s['pct_4096'] * 100)} % ≥ 4096 (tuile médiane {s['tuile_max_mediane']})")
        if time.time() - t_start >= a.minutes * 60:
            break
        # DAgger : le réseau joue, le professeur étiquette les positions rencontrées (parties plus courtes dans les premières itérations)
        t0 = time.time()
        _, _, R = play(net, a.student_games, 4000, 50_000 + it, eps=0.03, record_every=3)
        if len(R):
            R = np.unique(R)
            QR = label(R, a.depth)
            ok = (QR > NEG).any(1)
            B = np.concatenate([B, R[ok]])
            Q = np.concatenate([Q, QR[ok]])
            log(f"DAgger : +{int(ok.sum()):,} positions du réseau ({time.time() - t0:.0f}s)")
    publish(f"terminé : meilleur banc {best:.2f} (exposant moyen de la tuile max)", running=False)
    log("terminé")


if __name__ == "__main__":
    main()

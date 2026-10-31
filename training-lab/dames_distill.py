"""Distillation de la recherche renforcée des dames dans un réseau politique-valeur.
Cible de politique : softmax des scores de la recherche (température T) sur les coups légaux ; cible de valeur : tanh(meilleur score / 300).
Usage : python training-lab/dames_distill.py --data training-lab/data/dames-labels-1.npz --minutes 20 --out training-lab/models/dames/distill.pt
Validation (réservée) : accord avec le meilleur coup de la recherche, et part des coups choisis à moins de 20 points du meilleur."""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero import dames  # noqa: E402
from logic_arena.zero import dames_net as dn  # noqa: E402

K = 128


def prepare(path, temperature):
    d = np.load(path)
    cells, nxt, quiet, scores = d["cells"], d["next"], d["quiet"], d["scores"]
    n = len(cells)
    X = np.zeros((n, *dn.PLANES), dtype=np.float32)
    IDX = np.zeros((n, K), dtype=np.int64)
    P = np.zeros((n, K), dtype=np.float32)
    V = np.zeros(n, dtype=np.float32)
    BEST = np.zeros(n, dtype=np.int64)
    REG = np.full((n, K), -1e9, dtype=np.float32)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        moves = dames.legal_moves(cells[i], int(nxt[i]))
        sc = scores[i][:len(moves)]
        if len(moves) == 0 or len(moves) > K or np.isnan(sc).any():
            keep[i] = False
            continue
        X[i] = dn.encode(cells[i], int(nxt[i]), int(quiet[i]))
        IDX[i, :len(moves)] = [dn.action_index(m[0], int(nxt[i])) for m in moves]
        w = np.exp((sc - sc.max()) / temperature)
        P[i, :len(moves)] = w / w.sum()
        REG[i, :len(moves)] = sc - sc.max()
        best = float(sc.max())
        V[i] = 1.0 if best > 50000 else -1.0 if best < -50000 else np.tanh(best / 300.0)
        BEST[i] = int(np.argmax(sc))
    return X[keep], IDX[keep], P[keep], V[keep], BEST[keep], REG[keep]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--channels", type=int, default=64)
    ap.add_argument("--blocks", type=int, default=6)
    ap.add_argument("--temperature", type=float, default=40.0)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()
    X, IDX, P, V, BEST, REG = prepare(a.data, a.temperature)
    n = len(X)
    print(f"{n} positions préparées en {time.time() - t0:.0f}s", flush=True)
    order = np.random.default_rng(0).permutation(n)
    n_val = max(2000, int(n * 0.03))
    val, tr = order[:n_val], order[n_val:]
    net = dn.build_net(a.channels, a.blocks).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    Xt, IDXt, Pt, Vt = (torch.tensor(t, device=device) for t in (X, IDX, P, V))
    print(f"réseau {net.parameter_count()} paramètres sur {device}", flush=True)

    def validate():
        net.eval()
        top1 = near = 0
        with torch.no_grad():
            for i in range(0, len(val), 2048):
                rows = val[i:i + 2048]
                sel = torch.tensor(rows, device=device)
                logits, _ = net(Xt[sel])
                lg = logits.gather(1, IDXt[sel]).masked_fill(Pt[sel] <= 0, -1e9)
                pick = lg.argmax(1).cpu().numpy()
                top1 += int((pick == BEST[rows]).sum())
                near += int((REG[rows, pick] >= -20).sum())
        net.train()
        return top1 / len(val), near / len(val)

    start = time.time()
    deadline = start + a.minutes * 60
    steps, best_near = 0, 0.0
    trt = torch.tensor(tr, device=device)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    log = Path(a.out).with_suffix(".jsonl")
    while time.time() < deadline:
        sel = trt[torch.randint(len(trt), (a.batch,), device=device)]
        frac = (time.time() - start) / (a.minutes * 60)
        for g in opt.param_groups:
            g["lr"] = a.lr * (0.03 + 0.97 * 0.5 * (1 + np.cos(np.pi * min(1.0, frac))))
        logits, value = net(Xt[sel])
        target = torch.zeros(len(sel), dn.N_ACTIONS, device=device)
        target.scatter_add_(1, IDXt[sel], Pt[sel])
        loss = -(target * F.log_softmax(logits, 1)).sum(1).mean() + 0.5 * F.mse_loss(value, Vt[sel])
        opt.zero_grad()
        loss.backward()
        opt.step()
        steps += 1
        if steps % 1000 == 0:
            top1, near = validate()
            entry = {"pas": steps, "perte": round(loss.item(), 4), "accord_meilleur_coup": round(top1, 4), "coup_acceptable": round(near, 4)}
            print(json.dumps(entry), flush=True)
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            if near >= best_near:
                best_near = near
                torch.save({"net": net.state_dict(), "channels": a.channels, "blocks": a.blocks, "validation": entry}, a.out)
    top1, near = validate()
    print(json.dumps({"fin": True, "pas": steps, "accord_meilleur_coup": round(top1, 4), "coup_acceptable": round(near, 4), "meilleur_acceptable": round(best_near, 4)}))


if __name__ == "__main__":
    main()

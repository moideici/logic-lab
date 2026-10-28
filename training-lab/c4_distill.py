"""Distillation du solveur exact de Puissance 4 dans un réseau politique-valeur (cible : coups qui conservent le résultat théorique).

Usage : python training-lab/c4_distill.py --data training-lab/data/c4-labels-1.npz [...] --minutes 20 --channels 96 --blocks 6 --out training-lab/models/zero-c4/distill.pt
Part des poids de Zéro si --init est donné. Validation : 8 % des positions réservées ; métrique = coup choisi (réseau seul) parmi les coups optimaux.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero import c4  # noqa: E402
from logic_arena.zero.net import PolicyValueNet  # noqa: E402


def load(paths):
    pos, mask, out = [], [], []
    for p in paths:
        d = np.load(p)
        pos.append(d["pos"]), mask.append(d["mask"]), out.append(d["out"])
    return np.concatenate(pos), np.concatenate(mask), np.concatenate(out)


def targets(out):
    legal = out != -2
    best = np.where(legal, out, -3).max(1)
    good = legal & (out == best[:, None])
    pi = good / good.sum(1, keepdims=True)
    return pi.astype(np.float32), best.astype(np.float32), legal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--channels", type=int, default=96)
    ap.add_argument("--blocks", type=int, default=6)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--init")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pos, mask, out = load(a.data)
    X = c4.planes(pos, mask)
    PI, V, LEGAL = targets(out)
    n = len(X)
    rng = np.random.default_rng(0)
    order = rng.permutation(n)
    val, tr = order[: int(n * 0.08)], order[int(n * 0.08):]
    net = PolicyValueNet((2, 6, 7), 7, a.channels, a.blocks).to(device)
    if a.init:
        blob = torch.load(a.init, map_location=device, weights_only=True)
        net.load_state_dict(blob["net"])
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    Xt, PIt, Vt = (torch.tensor(t, device=device) for t in (X, PI, V))
    LEGt = torch.tensor(LEGAL, device=device)
    print(f"{n} positions ({len(tr)} entraînement, {len(val)} validation) ; réseau {net.parameter_count()} paramètres ; {device}", flush=True)

    def validate():
        net.eval()
        hit = 0
        with torch.no_grad():
            for i in range(0, len(val), 2048):
                idx = torch.tensor(val[i:i + 2048], device=device)
                p, _ = net(Xt[idx])
                p = p.masked_fill(~LEGt[idx], -1e9)
                pick = p.argmax(1)
                hit += (PIt[idx].gather(1, pick[:, None]) > 0).sum().item()
        net.train()
        return hit / len(val)

    deadline = time.time() + a.minutes * 60
    steps = 0
    trt = torch.tensor(tr, device=device)
    total = max(1, int(a.minutes * 60 * 25))  # estimation de pas pour le recuit du taux d'apprentissage
    best_acc, log = 0.0, Path(a.out).with_suffix(".jsonl")
    while time.time() < deadline:
        idx = trt[torch.randint(len(trt), (a.batch,), device=device)]
        x, pi, v = Xt[idx], PIt[idx], Vt[idx]
        flip = torch.rand(a.batch, device=device) < 0.5  # symétrie miroir
        x = torch.where(flip[:, None, None, None], x.flip(-1), x)
        pi = torch.where(flip[:, None], pi.flip(-1), pi)
        for g in opt.param_groups:
            g["lr"] = a.lr * (0.5 * (1 + np.cos(np.pi * min(1.0, (time.time() - (deadline - a.minutes * 60)) / (a.minutes * 60)))) * 0.97 + 0.03)
        p, pv = net(x)
        loss = -(pi * F.log_softmax(p, 1)).sum(1).mean() + 0.5 * F.mse_loss(pv, v)
        opt.zero_grad()
        loss.backward()
        opt.step()
        steps += 1
        if steps % 1000 == 0:
            acc = validate()
            entry = {"pas": steps, "perte": round(loss.item(), 4), "validation_coup_optimal": round(acc, 4)}
            print(json.dumps(entry), flush=True)
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            if acc >= best_acc:
                best_acc = acc
                Path(a.out).parent.mkdir(parents=True, exist_ok=True)
                torch.save({"net": net.state_dict(), "channels": a.channels, "blocks": a.blocks, "validation": acc, "steps": steps}, a.out)
    acc = validate()
    print(json.dumps({"fin": True, "pas": steps, "validation_coup_optimal": round(acc, 4), "meilleur": round(best_acc, 4)}))


if __name__ == "__main__":
    main()

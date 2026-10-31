"""Entraîne l'emplacement « dames » du MLP de Garry par distillation des visites du MCTS de Zéro (anciens jeux gelés bit à bit).

Seuls sont modifiés : les lignes d'entrée des dames et leur étiquette, les colonnes de sortie des dames, et (si --extra-hidden > 0) les connexions des unités ajoutées.
Usage : python training-lab/garry_dames_train.py --data training-lab/data/dames-garry-1.npz --minutes 20 --extra-hidden 0 --out training-lab/models/garry-dames/h48.npz"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.garry_dames import (DAMES_FEATURES, DAMES_IN, DAMES_OUT, DAMES_TAG, GarryDames, dames_features_batch)  # noqa: E402
from logic_arena.general import GarryPolicy  # noqa: E402
from logic_arena.zero import dames_net as dn  # noqa: E402

BASE = Path(__file__).resolve().parents[1] / "web" / "models" / "garry.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--extra-hidden", type=int, default=0)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--train-core", action="store_true", help="entraîne aussi le noyau partagé (modifie les anciens jeux : à valider ensuite)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    parts = [np.load(p) for p in a.data]
    states = np.concatenate([p["states"] for p in parts])
    idx = np.concatenate([p["idx"] for p in parts]).astype(np.int64)
    prob = np.concatenate([p["prob"] for p in parts])
    feats = dames_features_batch(states[:, :64], states[:, 64], states[:, 65])
    n = len(feats)
    order = np.random.default_rng(0).permutation(n)
    n_val = max(3000, int(n * 0.03))
    val, tr = order[:n_val], order[n_val:]
    base = GarryPolicy.load(BASE)
    model = GarryDames(base, a.extra_hidden, seed=a.seed)
    T = lambda x: torch.tensor(x, device=device)  # noqa: E731
    w1d = T(model.w1[DAMES_IN:DAMES_IN + DAMES_FEATURES]).requires_grad_()
    tag = T(model.w1[DAMES_TAG]).requires_grad_()
    b1 = T(model.b1)
    core_w = T(model.core_w).requires_grad_(a.train_core or a.extra_hidden > 0)
    core_b = T(model.core_b).requires_grad_(a.train_core or a.extra_hidden > 0)
    w2d = T(model.w2[:, DAMES_OUT:]).requires_grad_()
    b2d = T(model.b2[DAMES_OUT:]).requires_grad_()
    mask_core_w = T(np.ones_like(model.core_w) if a.train_core else model.mask_core_w)
    mask_core_b = T(np.ones_like(model.core_b) if a.train_core else model.mask_core_b)
    params = [w1d, tag, w2d, b2d] + ([core_w, core_b] if (a.train_core or a.extra_hidden > 0) else [])
    opt = torch.optim.Adam(params, lr=a.lr)
    X, IDX, P = T(feats), T(idx), T(prob)
    print(f"{n} positions ; modèle {model.parameter_count()} paramètres (dont entraînables {sum(p.numel() for p in params)}) sur {device}", flush=True)

    def forward(x):
        e = torch.tanh(x @ w1d + tag + b1)
        h = torch.tanh(e @ core_w + core_b)
        return h @ w2d + b2d

    def validate():
        with torch.no_grad():
            top1 = 0
            ce = 0.0
            for i in range(0, len(val), 4096):
                sel = T(val[i:i + 4096])
                logits = forward(X[sel])
                lg = logits.gather(1, IDX[sel]).masked_fill(P[sel] <= 0, -1e9)
                top1 += int((lg.argmax(1) == P[sel].argmax(1)).sum())
                target = torch.zeros_like(logits).scatter_add_(1, IDX[sel], P[sel])
                ce += float(-(target * F.log_softmax(logits, 1)).sum())
        return top1 / len(val), ce / len(val)

    start = time.time()
    deadline = start + a.minutes * 60
    steps, best = 0, -1.0
    trt = T(tr)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    log = Path(a.out).with_suffix(".jsonl")
    while time.time() < deadline:
        sel = trt[torch.randint(len(trt), (a.batch,), device=device)]
        frac = (time.time() - start) / (a.minutes * 60)
        for g in opt.param_groups:
            g["lr"] = a.lr * (0.02 + 0.98 * 0.5 * (1 + np.cos(np.pi * min(1.0, frac))))
        logits = forward(X[sel])
        target = torch.zeros_like(logits).scatter_add_(1, IDX[sel], P[sel])
        loss = -(target * F.log_softmax(logits, 1)).sum(1).mean()
        opt.zero_grad()
        loss.backward()
        if core_w.grad is not None and not a.train_core:
            core_w.grad *= mask_core_w
            core_b.grad *= mask_core_b
        opt.step()
        steps += 1
        if steps % 2000 == 0:
            top1, ce = validate()
            entry = {"pas": steps, "perte": round(loss.item(), 4), "validation_accord_mcts": round(top1, 4), "validation_ce": round(ce, 4)}
            print(json.dumps(entry), flush=True)
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            if top1 >= best:
                best = top1
                model.w1[DAMES_IN:DAMES_IN + DAMES_FEATURES] = w1d.detach().cpu().numpy()
                model.w1[DAMES_TAG] = tag.detach().cpu().numpy()
                model.w2[:, DAMES_OUT:] = w2d.detach().cpu().numpy()
                model.b2[DAMES_OUT:] = b2d.detach().cpu().numpy()
                model.core_w = core_w.detach().cpu().numpy()
                model.core_b = core_b.detach().cpu().numpy()
                model.save(a.out)
    top1, ce = validate()
    print(json.dumps({"fin": True, "pas": steps, "validation_accord_mcts": round(top1, 4), "meilleur": round(best, 4)}))


if __name__ == "__main__":
    main()

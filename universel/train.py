"""Entraînement de Garry Universel par imitation des visites d'UCT (et de la valeur de position).

Usage : python -m universel.train --data universel/data/train.pkl --minutes 20 --out universel/models/u1.pt [--init universel/models/u1.pt]
Le même script sert à l'adaptation sur un jeu réservé (--init pour partir du modèle préentraîné, sinon initialisation au hasard) avec un nombre de pas fixé (--steps)."""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universel import tokens as tk  # noqa: E402
from universel.model import UniversalPlayer  # noqa: E402


def encode_sample(r):
    """Jetons + cible de politique (visites normalisées sur les coups gardés) + z."""
    legal, visits = r["legal"], np.array(r["visits"], dtype=np.float64)
    if len(legal) > tk.MAX_ACTIONS:  # garder les plus visités (d'abord) et quelques autres
        order = np.argsort(-visits, kind="stable")[:tk.MAX_ACTIONS]
        legal, visits = [legal[i] for i in order], visits[order]
    enc = tk.encode(r["view"], legal, r["seat"], r["nplayers"])
    target = np.zeros(tk.MAX_ACTIONS, dtype=np.float32)
    target[:len(visits)] = visits / max(visits.sum(), 1)
    enc["target"], enc["z"] = target, np.float32(r["z"])
    return enc


def load_encoded(paths, games=None, limit_games=None):
    data = []
    for p in paths:
        with open(p, "rb") as f:
            data.extend(pickle.load(f))
    if games:
        data = [r for r in data if r["game"] in games]
    return [encode_sample(r) for r in data], data


def batchify(encs, device):
    batch = tk.collate(encs, device)
    batch["target"] = torch.tensor(np.stack([e["target"] for e in encs]), device=device)
    batch["z"] = torch.tensor(np.array([e["z"] for e in encs]), device=device)
    return batch


def evaluate_agreement(model, encs, device, n=2000):
    model.eval()
    hit = 0
    ce = 0.0
    with torch.no_grad():
        for i in range(0, min(n, len(encs)), 64):
            b = batchify(encs[i:i + 64], device)
            scores, _ = model(b)
            hit += int((scores.argmax(1) == b["target"].argmax(1)).sum())
            ce += float(-(b["target"] * F.log_softmax(scores, 1).clamp(min=-30)).sum())
    model.train()
    m = min(n, len(encs))
    return hit / m, ce / m


def train(model, encs, device, minutes=None, steps=None, batch=64, lr=5e-4, log=None, val_frac=0.03, seed=0):
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(encs))
    n_val = max(200, int(len(encs) * val_frac)) if len(encs) > 600 else max(1, len(encs) // 10)
    val = [encs[i] for i in order[:n_val]]
    tr = [encs[i] for i in order[n_val:]]
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    start = time.time()
    deadline = start + minutes * 60 if minutes else None
    step = 0
    model.train()
    while True:
        if steps is not None and step >= steps:
            break
        if deadline is not None and time.time() >= deadline:
            break
        frac = step / steps if steps else (time.time() - start) / (minutes * 60)
        for g in opt.param_groups:
            g["lr"] = lr * (0.03 + 0.97 * 0.5 * (1 + np.cos(np.pi * min(1.0, frac))))
        idx = rng.integers(0, len(tr), size=batch)
        b = batchify([tr[i] for i in idx], device)
        scores, value = model(b)
        loss_p = -(b["target"] * F.log_softmax(scores, 1).clamp(min=-30)).sum(1).mean()
        loss = loss_p + 0.3 * F.mse_loss(value, b["z"])
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        step += 1
        if step % 500 == 0:
            agree, ce = evaluate_agreement(model, val, device, 1000)
            entry = {"pas": step, "perte_politique": round(float(loss_p), 4), "accord_uct": round(agree, 4), "ce_val": round(ce, 4)}
            print(json.dumps(entry), flush=True)
            if log:
                with open(log, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
    return evaluate_agreement(model, val, device, 2000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--games", nargs="*")
    ap.add_argument("--minutes", type=float)
    ap.add_argument("--steps", type=int)
    ap.add_argument("--init")
    ap.add_argument("--d", type=int, default=128)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--max-gids", type=int, help="n'utilise que les N premières parties (adaptation à budget de données fixe)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(a.seed)
    encs, raw = load_encoded(a.data, a.games)
    if a.max_gids:
        gids = sorted({r["gid"] for r in raw})[:a.max_gids]
        keep = [i for i, r in enumerate(raw) if r["gid"] in set(gids)]
        encs = [encs[i] for i in keep]
    model = UniversalPlayer(a.d, a.layers).to(device)
    if a.init:
        model.load_state_dict(torch.load(a.init, map_location=device, weights_only=True)["model"])
    print(f"{len(encs)} exemples, {model.parameter_count()} paramètres, {device}", flush=True)
    agree, ce = train(model, encs, device, a.minutes, a.steps, a.batch, a.lr, log=Path(a.out).with_suffix(".jsonl"), seed=a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "d": a.d, "layers": a.layers}, a.out)
    print(json.dumps({"fin": True, "accord_uct": round(agree, 4), "ce_val": round(ce, 4)}))


if __name__ == "__main__":
    main()

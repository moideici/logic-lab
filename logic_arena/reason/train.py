"""Entraînement et mesures du solveur récurrent sur les problèmes à contraintes."""
from __future__ import annotations

import time

import numpy as np
import torch

from .model import RecurrentSolver, loss_over_passes, predicted_grid
from .problems import dataset, is_valid_solution, peers


def tensors(P, S, device):
    return torch.as_tensor(P, device=device), torch.as_tensor(S, device=device)


def fit(model, n, train_data, steps=4000, batch=128, lr=2e-3, seed=0, device="cpu", eval_data=None, eval_every=500, on_point=None):
    """Entraîne `model` (supervision profonde : perte à chaque passe). Retourne l'historique."""
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    model.to(device).train()
    pe = torch.as_tensor(peers(n), device=device)
    P, S = tensors(train_data[0], train_data[1], device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.1)
    history, started = [], time.time()
    for step in range(1, steps + 1):
        idx = torch.as_tensor(rng.integers(0, len(P), size=batch), device=device)
        logits = model(P[idx], pe)
        loss = loss_over_passes(logits, S[idx], P[idx])
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % eval_every == 0 or step == steps:
            point = {"pas": step, "perte": round(float(loss), 4), "secondes": round(time.time() - started, 1)}
            if eval_data is not None:
                point["exact"] = round(evaluate(model, n, eval_data, device=device)["exact"], 4)
            history.append(point)
            if on_point:
                on_point(point)
            model.train()
    return history


@torch.no_grad()
def evaluate(model, n, data, passes=None, device="cpu", batch=500, stop_at_valid=True):
    """Exactitude de la grille entière (valide et conforme aux données), précision par case vide, et passes utilisées.

    `passes_moy` : en s'arrêtant à la première passe dont la grille est valide (vérificateur exact), nombre moyen de passes
    nécessaires parmi les problèmes résolus ; c'est la « durée de réflexion ».
    """
    model.eval().to(device)
    pe = torch.as_tensor(peers(n), device=device)
    P, S = tensors(data[0], data[1], device)
    solved = 0
    cells_ok = cells = 0
    first_valid = []
    T = model.passes if passes is None else passes
    for i in range(0, len(P), batch):
        p, s = P[i:i + batch], S[i:i + batch]
        logits = model(p, pe, passes=T)
        final = predicted_grid(logits[-1], p)
        for b in range(len(p)):
            ok = is_valid_solution(n, final[b].cpu().numpy())
            solved += ok
        empty = p == 0
        cells_ok += int(((final == s) & empty).sum())
        cells += int(empty.sum())
        if stop_at_valid:
            for b in range(len(p)):
                for t in range(T):
                    g = predicted_grid(logits[t][b:b + 1], p[b:b + 1])[0].cpu().numpy()
                    if is_valid_solution(n, g):
                        first_valid.append(t + 1)
                        break
    return {"exact": solved / len(P), "case": cells_ok / max(cells, 1), "passes_moy": float(np.mean(first_valid)) if first_valid else None, "resolus": solved, "cas": len(P)}

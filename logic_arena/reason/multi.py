"""Entraînement et mesure sur plusieurs familles de problèmes (sudoku 6×6, coloration de graphe) avec le même modèle.

Un jeu de données est un dictionnaire : P (puzzles), S (solutions), K (nombre de valeurs permises), et pour les graphes propres à chaque
exemple A (adjacences) et V (nœuds réels). Sans A, c'est un sudoku 6×6 : graphe global de `problems.peers(6)`.
"""
from __future__ import annotations

import time

import numpy as np
import torch

from .graphs import is_valid_coloring
from .model import loss_over_passes, predicted_grid
from .problems import is_valid_solution, peers


def sudoku_data(P, S):
    return {"P": np.asarray(P), "S": np.asarray(S), "K": np.full(len(P), 6)}


def _batch(data, idx, device, sudoku_peers):
    P = torch.as_tensor(data["P"][idx], device=device)
    S = torch.as_tensor(data["S"][idx], device=device)
    K = torch.as_tensor(data["K"][idx], device=device)
    if "A" in data:
        return P, S, K, torch.as_tensor(data["A"][idx], device=device), torch.as_tensor(data["V"][idx], device=device)
    return P, S, K, sudoku_peers, None


def fit_mixed(model, families, steps=5000, batch=128, lr=2e-3, seed=0, device="cpu", weights=None, on_point=None, eval_every=1000):
    """`families` : liste de jeux de données ; chaque lot vient d'une seule famille, tirée selon `weights` (égaux par défaut)."""
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    model.to(device).train()
    pe6 = torch.as_tensor(peers(6), device=device)
    w = np.array(weights if weights is not None else [1.0] * len(families), dtype=float)
    w /= w.sum()
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.1)
    history, started = [], time.time()
    for step in range(1, steps + 1):
        data = families[int(rng.choice(len(families), p=w))]
        idx = rng.integers(0, len(data["P"]), size=batch)
        P, S, K, A, V = _batch(data, idx, device, pe6)
        logits = model(P, A, domain=K)
        loss = loss_over_passes(logits, S, P, V)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % eval_every == 0 or step == steps:
            point = {"pas": step, "perte": round(float(loss), 4), "secondes": round(time.time() - started, 1)}
            history.append(point)
            if on_point:
                on_point(point)
    return history


@torch.no_grad()
def evaluate_data(model, data, passes=None, device="cpu", batch=250):
    """Exactitude (grille entière valide, vérificateur exact), précision par case à trouver, passes avant la première grille valide."""
    model.eval().to(device)
    pe6 = torch.as_tensor(peers(6), device=device)
    T = model.passes if passes is None else passes
    solved = cells_ok = cells = 0
    first = []
    count = len(data["P"])
    for i in range(0, count, batch):
        idx = np.arange(i, min(count, i + batch))
        P, S, K, A, V = _batch(data, idx, device, pe6)
        logits = model(P, A, passes=T, domain=K)
        grids = [predicted_grid(logits[t], P).cpu().numpy() for t in range(T)]
        Pn, Sn, Kn = P.cpu().numpy(), S.cpu().numpy(), K.cpu().numpy()
        An = None if "A" not in data else A.cpu().numpy()
        Vn = None if V is None else V.cpu().numpy()
        for b in range(len(idx)):
            def valid(g):
                if An is None:
                    return is_valid_solution(6, g)
                return is_valid_coloring(An[b], int(Kn[b]), g, Vn[b])
            ok = valid(grids[-1][b])
            solved += ok
            live = (Pn[b] == 0) if Vn is None else ((Pn[b] == 0) & Vn[b])
            cells_ok += int(((grids[-1][b] == Sn[b]) & live).sum())
            cells += int(live.sum())
            if ok:
                for t in range(T):
                    if valid(grids[t][b]):
                        first.append(t + 1)
                        break
    return {"exact": solved / count, "case": cells_ok / max(cells, 1), "passes_moy": float(np.mean(first)) if first else None, "resolus": solved, "cas": count}

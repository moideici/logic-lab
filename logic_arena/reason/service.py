"""Service du Lab pour le Loop : tirer un sudoku 6×6 et regarder le modèle réfléchir passe par passe.

Le modèle est entraîné par `training-lab/entrainer_loop.py` (non versionné). Aucune écriture dans les poids du site.
"""
from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
import torch

from .model import RecurrentSolver, predicted_grid
from .problems import count_solutions, is_valid_solution, make_puzzle, peers

PATH = Path(__file__).resolve().parents[2] / "training-lab" / "models" / "loop-sudoku6.pt"
N = 6
_lock = threading.Lock()
_model = None


def _load():
    global _model
    with _lock:
        if _model is None:
            if not PATH.exists():
                raise ValueError("Modèle Loop absent : lancer training-lab/entrainer_loop.py (environ 4 minutes)")
            blob = torch.load(PATH, map_location="cpu", weights_only=True)
            c = blob["config"]
            m = RecurrentSolver(c["n"], c["n"] ** 2, d=c["d"], heads=c["heads"], passes=c["passes"], tied=c["tied"])
            m.load_state_dict(blob["state"])
            m.eval()
            _model = (m, blob)
        return _model


def info():
    m, blob = _load()
    return {"n": N, "parametres": m.parameter_count(), "passes_entrainement": blob["config"]["passes"], "pas": blob["pas"],
            "exact_dur_32_passes": round(blob["exact_dur_32"], 3), "poids_lies": blob["config"]["tied"]}


def new_puzzle(empties, seed):
    if type(empties) is not int or not 6 <= empties <= 27:
        raise ValueError("Cases vides : entre 6 et 27")
    if type(seed) is not int or not 0 <= seed < 10 ** 9:
        raise ValueError("Graine invalide")
    rng = np.random.default_rng(seed)
    puzzle, solution, removed = make_puzzle(N, empties, rng)
    return {"puzzle": [int(v) for v in puzzle], "solution": [int(v) for v in solution], "vides": int(removed)}


@torch.no_grad()
def solve(puzzle, passes, solution=None):
    """Grille proposée à chaque passe, confiance par case, validité exacte, et passe de la première grille valide."""
    if not isinstance(puzzle, list) or len(puzzle) != N * N or any(type(v) is not int or not 0 <= v <= N for v in puzzle):
        raise ValueError("Grille invalide : 36 entiers entre 0 et 6")
    if type(passes) is not int or not 1 <= passes <= 64:
        raise ValueError("Passes : entre 1 et 64")
    if count_solutions(N, np.array(puzzle)) != 1:
        raise ValueError("Ce problème n'a pas exactement une solution")
    m, _ = _load()
    p = torch.as_tensor(np.array(puzzle, dtype=np.int64))[None]
    logits = m(p, torch.as_tensor(peers(N)), passes=passes)
    steps, first_valid = [], None
    for t in range(passes):
        grid = predicted_grid(logits[t], p)[0].numpy()
        conf = torch.softmax(logits[t][0], -1).max(-1).values.numpy()
        valid = is_valid_solution(N, grid)
        if valid and first_valid is None:
            first_valid = t + 1
        wrong = int(((grid != np.array(solution)) & (np.array(puzzle) == 0)).sum()) if solution else None
        steps.append({"passe": t + 1, "grille": [int(v) for v in grid], "confiance": [round(float(c), 3) for c in conf], "valide": bool(valid), "fausses": wrong})
    return {"passes": passes, "etapes": steps, "premiere_valide": first_valid}

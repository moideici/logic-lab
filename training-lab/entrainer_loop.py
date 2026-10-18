"""Entraîne le Loop pour le Lab (sudoku 6×6, poids liés, 16 passes) et enregistre le modèle : training-lab/models/loop-sudoku6.pt

Usage : python training-lab/entrainer_loop.py [--steps 6000] [--seed 0]
Le modèle fait environ 0,2 Mo ; il n'est pas versionné (régénérable).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.reason.model import RecurrentSolver  # noqa: E402
from logic_arena.reason.problems import dataset  # noqa: E402
from logic_arena.reason.train import evaluate, fit  # noqa: E402

HERE = Path(__file__).resolve().parent
CONFIG = {"n": 6, "d": 64, "heads": 4, "passes": 16, "tied": True}


def load_train():
    path = HERE / "data" / "sudoku6-train-40000.npz"
    if path.exists():
        d = np.load(path)
        return d["P"], d["S"], d["E"]
    return dataset(6, 40000, (8, 22), seed=11)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = RecurrentSolver(CONFIG["n"], CONFIG["n"] ** 2, d=CONFIG["d"], heads=CONFIG["heads"], passes=CONFIG["passes"], tied=CONFIG["tied"])
    fit(model, 6, load_train(), steps=a.steps, batch=128, lr=2e-3, seed=a.seed, device=device, on_point=print)
    test = dataset(6, 300, (22, 27), seed=777)
    r = evaluate(model, 6, (test[0], test[1]), passes=32, device=device)
    print("dur, 32 passes :", {k: v for k, v in r.items()})
    out = HERE / "models"
    out.mkdir(exist_ok=True)
    torch.save({"config": CONFIG, "state": model.cpu().state_dict(), "pas": a.steps, "graine": a.seed, "exact_dur_32": r["exact"]}, out / "loop-sudoku6.pt")
    (out / "loop-sudoku6.json").write_text(json.dumps({"config": CONFIG, "pas": a.steps, "graine": a.seed, "exact_dur_32": r["exact"]}, indent=1), encoding="utf-8")
    print("enregistré", out / "loop-sudoku6.pt")

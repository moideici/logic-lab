"""Expérience Loop : un cœur récurrent résout-il des sudokus 6×6, et la réflexion (nombre de passes) suit-elle la difficulté ?

Modèles : Loop (poids liés, 8 passes à l'entraînement), Loop-16 (16 passes), non lié (8 blocs différents, 8× plus de paramètres),
une passe (même bloc, aucune récurrence). Entraînés sur 8 à 22 cases vides ; testés sur trois tranches de difficulté dont une
plus dure que tout l'entraînement (22 à 27 vides), en variant le nombre de passes à l'inférence.
Usage : python training-lab/experience_raisonnement.py [--steps 5000] [--seeds 2]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.reason.model import RecurrentSolver  # noqa: E402
from logic_arena.reason.problems import dataset  # noqa: E402
from logic_arena.reason.train import evaluate, fit  # noqa: E402

N = 6
DATA = Path(__file__).resolve().parent / "data"
BUCKETS = {"facile 8-14": (8, 14), "moyen 15-21": (15, 21), "dur 22-27 (jamais vu)": (22, 27)}
VARIANTS = {
    "Loop (liés, 8 passes)": dict(tied=True, passes=8),
    "Loop-16 (liés, 16 passes)": dict(tied=True, passes=16),
    "non lié (8 blocs)": dict(tied=False, passes=8),
    "une passe (aucune boucle)": dict(tied=True, passes=1),
}


def cached(name, n, count, rng_range, seed):
    path = DATA / f"{name}.npz"
    if path.exists():
        d = np.load(path)
        return d["P"], d["S"], d["E"]
    P, S, E = dataset(n, count, rng_range, seed)
    DATA.mkdir(exist_ok=True)
    np.savez_compressed(path, P=P, S=S, E=E)
    return P, S, E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=5000)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--train-size", type=int, default=40000)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()
    train = cached(f"sudoku{N}-train-{a.train_size}", N, a.train_size, (8, 22), seed=11)
    tests = {k: cached(f"sudoku{N}-test-{k.split()[0]}", N, 500, r, seed=100 + i) for i, (k, r) in enumerate(BUCKETS.items())}
    print(f"données prêtes en {time.time() - t0:.0f} s ; appareil {device}", flush=True)
    rows = []
    for seed in range(a.seeds):
        for name, cfg in VARIANTS.items():
            model = RecurrentSolver(N, N * N, d=64, heads=4, **cfg)
            t = time.time()
            history = fit(model, N, train, steps=a.steps, batch=128, lr=2e-3, seed=seed, device=device)
            row = {"modele": name, "graine": seed, "parametres": model.parameter_count(), "entrainement_s": round(time.time() - t), "perte_finale": history[-1]["perte"], "tranches": {}}
            for bucket, data in tests.items():
                grid = {}
                for T in (1, 2, 4, 8, 16, 32):
                    if not cfg["tied"] and T > cfg["passes"]:
                        continue
                    r = evaluate(model, N, (data[0], data[1]), passes=T, device=device)
                    grid[str(T)] = {"exact": round(r["exact"], 3), "case": round(r["case"], 3), "passes_moy": None if r["passes_moy"] is None else round(r["passes_moy"], 2)}
                row["tranches"][bucket] = grid
            rows.append(row)
            best = max(v["exact"] for v in row["tranches"]["dur 22-27 (jamais vu)"].values())
            print(f"{name:28s} graine {seed} : {row['parametres']:7d} paramètres, {row['entrainement_s']:4d} s, dur : {best:.3f}", flush=True)
    out = Path(__file__).resolve().parent / "results" / "raisonnement-sudoku6.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"n": N, "pas": a.steps, "graines": a.seeds, "tranches": {k: list(v) for k, v in BUCKETS.items()}, "essais": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("fini", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()

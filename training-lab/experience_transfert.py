"""Transfert entre familles : le Loop a-t-il appris la règle « voisines différentes » ou seulement le sudoku ?

Trois entraînements (sans embedding de position, pour que seule la structure du graphe compte) :
  S  : sudoku 6×6 seul ;  C : coloration de graphe seule (4 couleurs, 12 à 24 nœuds) ;  SC : les deux.
Chacun est testé sur : sudoku moyen et dur, coloration dans la distribution, coloration de plus grands graphes (26 à 32 nœuds),
coloration à 5 couleurs (jamais vue), coloration de graphes plus denses.
Usage : python training-lab/experience_transfert.py [--steps 6000] [--seeds 2]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.reason.graphs import coloring_dataset  # noqa: E402
from logic_arena.reason.model import RecurrentSolver  # noqa: E402
from logic_arena.reason.multi import evaluate_data, fit_mixed, sudoku_data  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"


def load_sudoku(name):
    d = np.load(DATA / f"{name}.npz")
    return sudoku_data(d["P"], d["S"])


def cached_coloring(name, count, nodes, k, degree, seed):
    path = DATA / f"{name}.npz"
    if path.exists():
        d = np.load(path)
        return {key: d[key] for key in d.files}
    data = coloring_dataset(count, nodes, k, degree, seed)
    np.savez_compressed(path, **data)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--seeds", type=int, default=2)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    DATA.mkdir(exist_ok=True)
    t0 = time.time()
    sud_train = load_sudoku("sudoku6-train-40000")
    col_train = cached_coloring("color4-train-30000", 30000, (12, 24), 4, (4.0, 7.0), 21)
    tests = {
        "sudoku moyen": load_sudoku("sudoku6-test-moyen"),
        "sudoku dur": load_sudoku("sudoku6-test-dur"),
        "coloration (distribution)": cached_coloring("color4-test-dist", 500, (12, 24), 4, (4.0, 7.0), 301),
        "coloration plus grands graphes": cached_coloring("color4-test-grands", 500, (26, 32), 4, (5.0, 8.0), 302),
        "coloration 5 couleurs": cached_coloring("color5-test", 500, (12, 24), 5, (5.0, 9.0), 303),
        "coloration plus dense": cached_coloring("color4-test-dense", 500, (12, 24), 4, (8.0, 11.0), 304),
    }
    print(f"données prêtes en {time.time() - t0:.0f} s ; appareil {device}", flush=True)
    variants = {"S : sudoku seul": [sud_train], "C : coloration seule": [col_train], "SC : les deux": [sud_train, col_train]}
    rows = []
    for seed in range(a.seeds):
        for name, families in variants.items():
            model = RecurrentSolver(6, 36, d=64, heads=4, passes=16, tied=True, use_position=False)
            t = time.time()
            history = fit_mixed(model, families, steps=a.steps, batch=128, lr=2e-3, seed=seed, device=device)
            row = {"modele": name, "graine": seed, "parametres": model.parameter_count(), "entrainement_s": round(time.time() - t), "perte_finale": history[-1]["perte"], "tests": {}}
            for test_name, data in tests.items():
                row["tests"][test_name] = {}
                for T in (16, 32):
                    r = evaluate_data(model, data, passes=T, device=device)
                    row["tests"][test_name][str(T)] = {"exact": round(r["exact"], 3), "case": round(r["case"], 3), "passes_moy": None if r["passes_moy"] is None else round(r["passes_moy"], 2)}
            rows.append(row)
            print(f"{name:24s} graine {seed} : {row['entrainement_s']:4d} s | " + " | ".join(f"{k.split(' ', 1)[-1][:14]} {v['32']['exact']:.2f}" for k, v in row["tests"].items()), flush=True)
    out = Path(__file__).resolve().parent / "results" / "transfert.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"pas": a.steps, "graines": a.seeds, "essais": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("fini", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()

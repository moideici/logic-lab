"""Expérience Graine : un réseau qui pousse et s'élague pendant l'entraînement contre des réseaux de taille fixe.

Pour chaque jeu : réseaux fixes de plusieurs tailles, Graine (départ 2+2 neurones), et un réseau fixe de la taille finale de Graine
(même graine) pour savoir si l'architecture trouvée vaut mieux que la croissance elle-même. Même budget de pas, mêmes données,
trois graines. Mesures : perte et accord avec le professeur sur positions de test inédites, force contre le professeur de niveau 4.
Usage : python training-lab/experience_graine.py --game nim [--steps 4000] [--seeds 3]
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.labtrain import TorchMLP, build_dataset, evaluate, strength, train  # noqa: E402
from logic_arena.neural import SPECS  # noqa: E402

SIZES = {"tictactoe": [2, 4, 8, 16, 48], "nim": [2, 4, 8, 16, 48], "connect4": [4, 8, 16, 48]}
EPISODES = {"tictactoe": (3000, 500, 500), "nim": (3000, 500, 500), "connect4": (300, 80, 80)}
GRAINES = {
    "Graine A (prudente)": {"grow_by": 2, "plateau": 0.03, "patience": 2, "prune_every": 400, "prune_tol": 0.001, "max": 64, "min": 2},
    "Graine B (croît vite, élague à la fin)": {"grow_by": 2, "plateau": 0.06, "patience": 1, "prune_every": 200, "prune_rel": 0.01, "prune_start": 0.6, "max": 64, "min": 2},
    "Graine C (croît seule)": {"grow_by": 2, "plateau": 0.06, "patience": 1, "max": 64, "min": 2},
}


def run(game, steps, seeds, games_strength):
    torch.set_num_threads(4)
    tr, va, te = EPISODES[game]
    train_d, val_d, test_d = build_dataset(game, "train", tr), build_dataset(game, "val", va), build_dataset(game, "test", te)
    n_in, n_out = SPECS[game]
    rows = []

    def measure(label, model, hist, seed):
        t_loss, t_acc = evaluate(model, test_d)
        rows.append({"config": label, "graine": seed, "h1": model.sizes[0], "h2": model.sizes[1], "parametres": model.parameter_count(), "test_perte": round(t_loss, 4),
                     "val_accord": round(hist["historique"][-1]["val_acc"], 4), "test_accord": round(t_acc, 4), "force_n8": round(strength(model, game, 8, games_strength), 3), "historique": hist["historique"], "evenements": hist["evenements"]})
        print(f"  {label:18s} graine {seed} : {model.sizes} {model.parameter_count():6d} paramètres, accord {t_acc:.3f}, val {rows[-1]['val_accord']:.3f} force {rows[-1]['force_n8']:.2f}", flush=True)

    for seed in range(seeds):
        for h in SIZES[game]:
            m = TorchMLP(n_in, n_out, h, h, seed=seed)
            measure(f"fixe {h}+{h}", m, train(m, train_d, val_d, steps=steps, seed=seed), seed)
        for name, rules in GRAINES.items():
            g = TorchMLP(n_in, n_out, 2, 2, seed=seed)
            hist = train(g, train_d, val_d, steps=steps, seed=seed, graine=rules)
            measure(name, g, hist, seed)
            f = TorchMLP(n_in, n_out, g.sizes[0], g.sizes[1], seed=seed)
            measure(name.split(" (")[0] + " → fixe de même taille", f, train(f, train_d, val_d, steps=steps, seed=seed), seed)
    return rows


def summary(rows):
    out = {}
    for label in dict.fromkeys(r["config"] for r in rows):
        sel = [r for r in rows if r["config"] == label]
        mean = lambda k: round(statistics.mean(r[k] for r in sel), 4)
        out[label] = {"parametres": mean("parametres"), "test_accord": mean("test_accord"), "val_accord": mean("val_accord"), "force_n8": mean("force_n8"),
                      "accord_ecart": round(statistics.pstdev([r["test_accord"] for r in sel]), 4) if len(sel) > 1 else 0.0,
                      "tailles": [[r["h1"], r["h2"]] for r in sel]}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True, choices=list(SIZES))
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--games-strength", type=int, default=20)
    a = ap.parse_args()
    t = time.time()
    rows = run(a.game, a.steps, a.seeds, a.games_strength)
    res = {"jeu": a.game, "pas": a.steps, "graines": a.seeds, "graine_regles": GRAINES, "secondes": round(time.time() - t), "resume": summary(rows), "essais": rows}
    out = Path(__file__).resolve().parent / "results" / f"graine-{a.game}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res["resume"], ensure_ascii=False, indent=1))

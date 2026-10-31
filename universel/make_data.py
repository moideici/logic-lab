"""Données d'imitation de Garry Universel : parties jouées par UCT générique (pont Node), avec la distribution des visites comme cible.

Sortie .pkl : liste d'exemples {game, seat, nplayers, view, legal, visits, q, z}. z = résultat de la partie pour le joueur qui avait le trait (1 gain, 0 nul, -1 perte).
Usage : python -m universel.make_data --plan morpion:600,puissance-4:300 --sims 200 --out universel/data/train.pkl --workers 8"""
from __future__ import annotations

import argparse
import pickle
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universel.bridge import Bridge  # noqa: E402


def z_for(outcome, seat):
    groups = outcome["ranking"]
    if len(groups) < 2:
        return 0.0
    if seat in groups[0]:
        return 1.0
    if seat in groups[-1]:
        return -1.0
    return 0.0


def play_game(bridge, game, seed, sims, rng, temp_plies=12, eps=0.08, opening=2, max_plies=400):
    snap = bridge.init(game, seed=seed, players=2)
    # ouverture aléatoire pour la variété
    for _ in range(int(rng.integers(0, opening + 1))):
        if snap["over"] or not snap["legal"]:
            break
        seat = snap["active"][0]
        snap = bridge.apply(snap["h"], seat, snap["legal"][int(rng.integers(len(snap["legal"])))])
    records = []
    ply = 0
    while not snap["over"] and snap["legal"] and ply < max_plies:
        seat = snap["active"][0]
        r = bridge.uct(snap["h"], seat, sims=sims, seed=int(rng.integers(1 << 30)))
        v = np.array(r["visits"], dtype=np.float64)
        if v.sum() == 0:
            break
        records.append({"game": game, "gid": seed, "seat": seat, "nplayers": 2, "view": snap["view"], "legal": r["actions"], "visits": r["visits"], "q": r["q"]})
        if rng.random() < eps:
            k = int(rng.integers(len(v)))
        elif ply < temp_plies:
            k = int(rng.choice(len(v), p=v / v.sum()))
        else:
            k = int(v.argmax())
        res = bridge.apply(snap["h"], seat, r["actions"][k])
        if not res.get("ok", True):
            break
        snap = res
        ply += 1
    outcome = snap["outcome"] if snap["over"] else None
    for rec in records:
        rec["z"] = z_for(outcome, rec["seat"]) if outcome else 0.0
    return records


def work(args):
    game, seeds, sims, seed0 = args
    rng = np.random.default_rng(seed0)
    out = []
    with Bridge() as bridge:
        for s in seeds:
            out.extend(play_game(bridge, game, s, sims, rng))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="jeu:nombre_de_parties,...")
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    jobs = []
    for item in a.plan.split(","):
        game, count = item.split(":")
        seeds = list(range(a.seed * 100000 + 1, a.seed * 100000 + int(count) + 1))
        chunk = max(1, len(seeds) // a.workers)
        for i in range(0, len(seeds), chunk):
            jobs.append((game, seeds[i:i + chunk], a.sims, a.seed * 977 + len(jobs)))
    t = time.time()
    with Pool(a.workers) as pool:
        parts = pool.map(work, jobs, chunksize=1)
    data = [r for p in parts for r in p]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "wb") as f:
        pickle.dump(data, f)
    counts = {}
    for r in data:
        counts[r["game"]] = counts.get(r["game"], 0) + 1
    print(f"{len(data)} décisions en {time.time() - t:.0f}s :", counts)


if __name__ == "__main__":
    main()

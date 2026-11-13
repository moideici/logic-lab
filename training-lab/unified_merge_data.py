"""Fusionne les jeux de donnees d'un meme jeu (ex. hex-1.npz + hex-2.npz -> hex-m.npz).
Usage : python training-lab/unified_merge_data.py --games hex,gomoku --seeds 1,2 --tag m
Les positions de la 2e graine viennent en fin de fichier : la validation (5 % de queue) est donc faite de parties neuves."""
import argparse
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent / "data" / "unified"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", default="hex,gomoku")
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--tag", default="m")
    a = ap.parse_args()
    for g in a.games.split(","):
        parts = [np.load(DATA / f"{g}-{s}.npz", allow_pickle=True) for s in a.seeds.split(",")]
        out = {k: (parts[0][k] if parts[0][k].ndim == 0 else np.concatenate([p[k] for p in parts])) for k in parts[0].files}
        np.savez_compressed(DATA / f"{g}-{a.tag}.npz", **out)
        print(g, [len(p["value"]) for p in parts], "->", len(out["value"]))


if __name__ == "__main__":
    main()

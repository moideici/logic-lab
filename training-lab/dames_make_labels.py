"""Positions de dames étiquetées par la recherche renforcée (score de chaque coup légal à profondeur D).
Les parties sont jouées par un mélange de joueurs (recherche courte, copies du bot de multi, coups aléatoires) pour varier les positions.
Sortie .npz : cells (n,64) int8, next (n,), quiet (n,), scores (n,128) float32 (NaN au-delà des coups légaux, ordre de dames.legal_moves).
Usage : python training-lab/dames_make_labels.py --minutes 30 --workers 14 --depth 6 --out training-lab/data/dames-labels-1.npz [--seed 1]"""
import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
K = 128


def work(args):
    seed, seconds, depth = args
    from logic_arena.zero import dames
    rng = np.random.default_rng(seed)
    cells_l, next_l, quiet_l, scores_l = [], [], [], []
    end = time.time() + seconds
    while time.time() < end:
        state = dames.State.new()
        style = rng.choice(["teacher", "teacher", "multi-normal", "multi-difficile", "random"])
        eps = float(rng.choice([0.0, 0.1, 0.25]))
        opening = int(rng.integers(0, 7))
        plies = 0
        while state.status == "playing" and plies < 240 and time.time() < end:
            moves = state.moves()
            if plies >= opening and len(moves) > 1 and plies % 1 == 0:
                sc = dames.scores(state.cells, state.next, state.quiet, depth, 3_000_000, 1)
                if len(sc) == len(moves) and (sc > -999999).all():
                    row = np.full(K, np.nan, dtype=np.float32)
                    row[:len(sc)] = sc
                    cells_l.append(np.array(state.cells, dtype=np.int8))
                    next_l.append(state.next)
                    quiet_l.append(state.quiet)
                    scores_l.append(row)
            if plies < opening or style == "random" or rng.random() < eps:
                move = moves[int(rng.integers(len(moves)))]
            elif style == "teacher":
                move = dames.search(state.cells, state.next, state.quiet, 4, 20000, 1)[0]
            else:
                d, b = (4, 2000) if style == "multi-normal" else (7, 20000)
                move = dames.search(state.cells, state.next, state.quiet, d, b, 0)[0]
            state = state.advance(*move)
            plies += 1
    return np.array(cells_l), np.array(next_l, dtype=np.int8), np.array(quiet_l, dtype=np.int16), np.array(scores_l, dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--depth", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with Pool(a.workers) as pool:
        parts = pool.map(work, [(a.seed * 1000 + i, a.minutes * 60, a.depth) for i in range(a.workers)])
    parts = [p for p in parts if len(p[0])]
    cells = np.concatenate([p[0] for p in parts])
    nxt = np.concatenate([p[1] for p in parts])
    quiet = np.concatenate([p[2] for p in parts])
    scores = np.concatenate([p[3] for p in parts])
    key = [hash((c.tobytes(), int(n))) for c, n in zip(cells, nxt)]
    _, idx = np.unique(np.array(key), return_index=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, cells=cells[idx], next=nxt[idx], quiet=quiet[idx], scores=scores[idx])
    print(f"{len(idx)} positions uniques sur {len(cells)}")


if __name__ == "__main__":
    main()

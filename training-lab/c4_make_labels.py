"""Étiquette des positions de Puissance 4 avec le solveur exact (résultat théorique de chaque colonne).

Les positions viennent de parties jouées à moitié au hasard, à moitié avec le coup optimal, pour couvrir des positions réalistes et des erreurs.
Sortie : fichier .npz avec pos, mask (bitboards, joueur au trait) et out (n, 7) valant +1 gain, 0 nul, -1 perte, -2 colonne pleine.
Usage : python training-lab/c4_make_labels.py --minutes 25 --workers 14 --out training-lab/data/c4-labels-1.npz [--seed 0]
"""
import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

COL = (1 << 6) - 1


def drop(mask, c):
    return (mask + (1 << (c * 7))) & (COL << (c * 7))


def won(p):
    for sh in (1, 7, 6, 8):
        m = p & (p >> sh)
        if m & (m >> (2 * sh)):
            return True
    return False


def work(args):
    seed, seconds, min_ply = args
    from logic_arena.zero import c4solver
    rng = np.random.default_rng(seed)
    c4solver.reset()
    P, M, O = [], [], []
    end = time.time() + seconds
    while time.time() < end:
        pos = mask = n = 0
        p_opt = rng.choice([0.0, 0.5, 0.8, 1.0])
        done = False
        while not done and time.time() < end:
            cols = [c for c in range(7) if drop(mask, c)]
            if not cols:
                break
            if n >= min_ply:
                s = c4solver.scores(pos, mask, True)
                out = np.sign(s)
                out[s == -1000] = -2
                P.append(pos)
                M.append(mask)
                O.append(out)
                best = max(out[c] for c in cols)
                good = [c for c in cols if out[c] == best]
                c = int(rng.choice(good)) if rng.random() < p_opt else int(rng.choice(cols))
            else:
                c = int(rng.choice(cols))
            m = drop(mask, c)
            if won(pos | m):
                done = True
            pos ^= mask
            mask |= m
            n += 1
        if len(P) % 5000 < 3:
            c4solver.reset()
    return np.array(P, dtype=np.uint64), np.array(M, dtype=np.uint64), np.array(O, dtype=np.int8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=25)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--min-ply", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with Pool(a.workers) as pool:
        parts = pool.map(work, [(a.seed * 1000 + i, a.minutes * 60, a.min_ply) for i in range(a.workers)])
    pos = np.concatenate([p[0] for p in parts])
    mask = np.concatenate([p[1] for p in parts])
    out = np.concatenate([p[2] for p in parts])
    key = pos + mask * np.uint64(1000003)  # dédoublonnage approximatif sans collision pratique
    _, idx = np.unique(key, return_index=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, pos=pos[idx], mask=mask[idx], out=out[idx])
    print(f"{len(idx)} positions uniques sur {len(pos)}")


if __name__ == "__main__":
    main()

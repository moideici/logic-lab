"""Vérifie que le joueur parfait (livre + solveur) gagne toutes ses parties en jouant premier, contre un adversaire qui joue au hasard
(jusqu'au 6e coup) puis au mieux avec probabilité p (solveur) ou au hasard."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero import c4perfect, c4solver  # noqa: E402

COL = (1 << 6) - 1


def drop(mask, c):
    return (mask + (1 << (c * 7))) & (COL << (c * 7))


def won(p):
    for sh in (1, 7, 6, 8):
        m = p & (p >> sh)
        if m & (m >> (2 * sh)):
            return True
    return False


def main(games=60):
    rng = np.random.default_rng(5)
    wins = 0
    t = time.time()
    for g in range(games):
        pos = mask = n = 0
        p_opt = [0.0, 0.5, 1.0][g % 3]
        winner = None
        while True:
            cols = [c for c in range(7) if drop(mask, c)]
            if not cols:
                break
            if n % 2 == 0:
                c = c4perfect.choose(pos, mask)
            elif n >= 6 and rng.random() < p_opt:
                s = c4solver.scores(pos, mask, True)
                best = max(np.sign(s[c]) for c in cols)
                c = int(rng.choice([c for c in cols if np.sign(s[c]) == best]))
            else:
                c = int(rng.choice(cols))
            m = drop(mask, c)
            if won(pos | m):
                winner = n % 2
                break
            pos ^= mask
            mask |= m
            n += 1
        wins += winner == 0
        if winner != 0:
            print("PARTIE NON GAGNEE", g, n, winner)
    print(f"{wins}/{games} parties gagnées par le premier joueur parfait en {time.time()-t:.0f}s")


if __name__ == "__main__":
    main()

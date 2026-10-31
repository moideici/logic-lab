"""Positions de référence pour le solveur TypeScript de multi : suite de coups (colonnes 0-6, joueur 0 en premier) et valeur de chaque colonne (1 gain, 0 nul, -1 perte, null pleine) selon le solveur C++."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero import c4solver  # noqa: E402

COL = (1 << 6) - 1


def drop(mask, c):
    return (mask + (1 << (c * 7))) & (COL << (c * 7))


def four(x):
    for sh in (1, 7, 6, 8):
        m = x & (x >> sh)
        if m & (m >> (2 * sh)):
            return True
    return False


rng = random.Random(11)
out = []
for target in [10] * 10 + [12] * 10 + [14] * 15 + [18] * 15 + [22] * 15 + [26] * 15:
    while True:
        pos = mask = 0
        seq = []
        ok = True
        for _ in range(target):
            c = rng.choice([c for c in range(7) if drop(mask, c)])
            m = drop(mask, c)
            if four(pos | m):
                ok = False
                break
            seq.append(c)
            pos ^= mask
            mask |= m
        if ok and not four(pos ^ mask):
            break
    s = c4solver.scores(pos, mask, True)
    out.append({"moves": "".join(map(str, seq)), "values": [None if x == -1000 else (1 if x > 0 else -1 if x < 0 else 0) for x in s]})
Path(sys.argv[1]).write_text(json.dumps(out), encoding="utf-8")
print(len(out))

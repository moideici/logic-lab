"""Livre d'ouverture du premier joueur à Puissance 4 : pour chaque position atteignable (plis 0, 2 et 4, Garry au trait) en suivant une stratégie gagnante,
toutes les colonnes qui conservent le gain. À partir du 6e coup le solveur exact répond en moins d'une seconde.

Sortie JSON {"pos,mask": [colonnes]} (bitboards du joueur au trait), les deux orientations du miroir. Usage : python training-lab/c4_book.py [--workers 14]
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

COL = (1 << 6) - 1
OUT = Path(__file__).resolve().parents[1] / "logic_arena" / "zero" / "c4_book.json"


def drop(mask, c):
    return (mask + (1 << (c * 7))) & (COL << (c * 7))


def play(pos, mask, c):
    m = drop(mask, c)
    return pos ^ mask, mask | m


def mirror(pos, mask):
    def mir(x):
        out = 0
        for c in range(7):
            out |= ((x >> (c * 7)) & 0x7F) << ((6 - c) * 7)
        return out
    return mir(pos), mir(mask)


def canon(pos, mask):
    a, b = (pos, mask), mirror(pos, mask)
    return (a, False) if a <= b else (b, True)


def winning_columns(task):
    pos, mask = task
    from logic_arena.zero import c4solver
    c4solver.reset()
    s = c4solver.scores(pos, mask, True)
    return task, [c for c in range(7) if s[c] != -1000 and s[c] > 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=14)
    a = ap.parse_args()
    book = {(0, 0): [3]}
    frontier = {(0, 0)}  # positions où Garry (premier joueur) doit jouer
    for ply in (0, 2, 4):
        todo = sorted({canon(*p)[0] for p in frontier if p not in book or ply == 0} - {(0, 0)})
        if ply:
            with Pool(a.workers) as pool:
                for task, cols in pool.imap_unordered(winning_columns, todo):
                    if not cols:
                        raise SystemExit(f"aucune colonne gagnante au pli {ply} : stratégie du livre fausse")
                    book[task] = cols
                    print(ply, task, cols, flush=True)
        # positions suivantes : Garry joue sa colonne du livre (la plus centrale), l'adversaire répond partout
        nxt = set()
        for p in frontier:
            cp, flipped = canon(*p)
            cols = book[cp] if p == (0, 0) or cp in book else None
            cols = [6 - c for c in cols] if flipped else cols
            c = min(cols, key=lambda x: abs(x - 3))
            q = play(*p, c)
            for r in range(7):
                if drop(q[1], r):
                    nxt.add(play(*q, r))
        frontier = {p for p in nxt}
    full = {}
    for (pos, mask), cols in book.items():
        full[f"{pos},{mask}"] = cols
        mp, mm = mirror(pos, mask)
        full[f"{mp},{mm}"] = [6 - c for c in cols]
    OUT.write_text(json.dumps(full), encoding="utf-8")
    print(len(full), "entrées écrites dans", OUT)


if __name__ == "__main__":
    main()

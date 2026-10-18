"""Problèmes à contraintes sur grille : sudoku réduit (4×4 et 6×6), générateurs à solution unique et vérificateur exact.

Un problème est décrit par un **graphe de contraintes** : pour chaque case, la liste de ses « voisines » (même ligne, même colonne,
même bloc) qui doivent porter un chiffre différent. C'est la forme commune prévue pour les autres familles (coloration de graphe,
n-reines) : le modèle ne connaît que ce graphe, pas le sudoku.
"""
from __future__ import annotations

import numpy as np

# taille n -> (hauteur, largeur) d'un bloc
BOXES = {4: (2, 2), 6: (2, 3)}


def peers(n):
    """Matrice booléenne n²×n² : cases qui ne peuvent pas porter le même chiffre (la case elle-même exclue)."""
    bh, bw = BOXES[n]
    m = np.zeros((n * n, n * n), dtype=bool)
    for a in range(n * n):
        ra, ca = divmod(a, n)
        for b in range(n * n):
            if a == b:
                continue
            rb, cb = divmod(b, n)
            if ra == rb or ca == cb or (ra // bh == rb // bh and ca // bw == cb // bw):
                m[a, b] = True
    return m


def _units(n):
    bh, bw = BOXES[n]
    units = [[r * n + c for c in range(n)] for r in range(n)] + [[r * n + c for r in range(n)] for c in range(n)]
    for br in range(0, n, bh):
        for bc in range(0, n, bw):
            units.append([(br + i) * n + bc + j for i in range(bh) for j in range(bw)])
    return units


def is_valid_solution(n, grid):
    """Vérificateur exact : chaque ligne, colonne et bloc contient une fois chaque chiffre de 1 à n."""
    g = np.asarray(grid).reshape(-1)
    if g.shape[0] != n * n or g.min() < 1 or g.max() > n:
        return False
    return all(sorted(g[u]) == list(range(1, n + 1)) for u in _units(n))


def respects_givens(puzzle, grid):
    p, g = np.asarray(puzzle).reshape(-1), np.asarray(grid).reshape(-1)
    return bool(((p == 0) | (p == g)).all())


def count_solutions(n, puzzle, limit=2):
    """Nombre de solutions (arrêt à `limit`), par retour sur trace avec choix de la case la plus contrainte."""
    nb = peers(n)
    grid = [int(v) for v in np.asarray(puzzle).reshape(-1)]
    neigh = [np.flatnonzero(nb[i]).tolist() for i in range(n * n)]

    def candidates(i):
        used = {grid[j] for j in neigh[i]}
        return [d for d in range(1, n + 1) if d not in used]

    found = 0

    def solve():
        nonlocal found
        best, options = None, None
        for i in range(n * n):
            if grid[i] == 0:
                c = candidates(i)
                if not c:
                    return
                if options is None or len(c) < len(options):
                    best, options = i, c
                    if len(c) == 1:
                        break
        if best is None:
            found += 1
            return
        for d in options:
            grid[best] = d
            solve()
            grid[best] = 0
            if found >= limit:
                return

    solve()
    return found


def random_solution(n, rng):
    """Grille complète valide, tirée au hasard (retour sur trace avec ordre aléatoire)."""
    nb = peers(n)
    neigh = [np.flatnonzero(nb[i]).tolist() for i in range(n * n)]
    grid = [0] * (n * n)

    def fill(i):
        if i == n * n:
            return True
        used = {grid[j] for j in neigh[i]}
        options = [d for d in range(1, n + 1) if d not in used]
        rng.shuffle(options)
        for d in options:
            grid[i] = d
            if fill(i + 1):
                return True
        grid[i] = 0
        return False

    fill(0)
    return np.array(grid, dtype=np.int64)


def make_puzzle(n, empties, rng, unique=True, tries=200):
    """(puzzle, solution) avec `empties` cases vides et une seule solution (si `unique`). Les vides sont retirés un à un."""
    solution = random_solution(n, rng)
    order = list(rng.permutation(n * n))
    puzzle = solution.copy()
    removed = 0
    for i in order:
        if removed >= empties:
            break
        keep = puzzle[i]
        puzzle[i] = 0
        if unique and count_solutions(n, puzzle) != 1:
            puzzle[i] = keep
            continue
        removed += 1
    return puzzle, solution, removed


def dataset(n, count, empties_range, seed, unique=True):
    """`count` problèmes dont le nombre de vides est tiré dans `empties_range` (bornes incluses). Retourne puzzles, solutions, vides."""
    rng = np.random.default_rng(seed)
    P, S, E = [], [], []
    while len(P) < count:
        target = int(rng.integers(empties_range[0], empties_range[1] + 1))
        puzzle, solution, removed = make_puzzle(n, target, rng, unique)
        if removed >= min(target, empties_range[0]):  # un puzzle moins vide que demandé est accepté seulement s'il atteint le minimum
            P.append(puzzle)
            S.append(solution)
            E.append(removed)
    return np.array(P), np.array(S), np.array(E)

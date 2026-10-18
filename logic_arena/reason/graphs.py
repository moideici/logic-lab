"""Deuxième famille : coloration de graphe (voisins de couleurs différentes), sous la même forme que le sudoku.

Chaque problème est un graphe de contraintes (matrice d'adjacence propre à l'exemple), un nombre de couleurs k, des couleurs déjà
fixées (0 = à trouver) et une solution unique. Les graphes ont au plus MAX_NODES nœuds ; les exemples plus petits sont complétés par
des nœuds de remplissage isolés (masque `nodes`) pour pouvoir former des lots.
"""
from __future__ import annotations

import numpy as np

MAX_NODES = 36


def _adjacency_lists(adj):
    return [np.flatnonzero(adj[i]).tolist() for i in range(len(adj))]


def count_solutions_graph(adj, k, assignment, limit=2):
    """Nombre de colorations propres compatibles avec `assignment` (0 = libre), arrêt à `limit` ; MRV et retour sur trace."""
    neigh = _adjacency_lists(adj)
    colors = [int(v) for v in assignment]
    n = len(colors)
    for i in range(n):  # les couleurs imposées doivent déjà être compatibles
        if colors[i] and any(colors[j] == colors[i] for j in neigh[i]):
            return 0
    found = 0

    def solve():
        nonlocal found
        best, options = None, None
        for i in range(n):
            if colors[i] == 0:
                used = {colors[j] for j in neigh[i]}
                c = [d for d in range(1, k + 1) if d not in used]
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
            colors[best] = d
            solve()
            colors[best] = 0
            if found >= limit:
                return

    solve()
    return found


def is_valid_coloring(adj, k, colors, nodes=None):
    """Toutes les couleurs sont dans 1..k et aucune arête ne relie deux nœuds de même couleur (nœuds de remplissage ignorés)."""
    c = np.asarray(colors)
    live = np.ones(len(c), dtype=bool) if nodes is None else np.asarray(nodes, dtype=bool)
    if (c[live] < 1).any() or (c[live] > k).any():
        return False
    same = (c[:, None] == c[None, :]) & adj & live[:, None] & live[None, :]
    return not same.any()


def planted_instance(n_nodes, k, mean_degree, rng):
    """Graphe aléatoire dont une k-coloration est connue (arêtes seulement entre couleurs différentes)."""
    colors = np.array([(i % k) + 1 for i in range(n_nodes)])
    rng.shuffle(colors)
    p = min(1.0, mean_degree / max(1.0, n_nodes * (k - 1) / k))
    adj = np.zeros((n_nodes, n_nodes), dtype=bool)
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if colors[i] != colors[j] and rng.random() < p:
                adj[i, j] = adj[j, i] = True
    return adj, colors


def make_coloring_puzzle(n_nodes, k, mean_degree, empties, rng):
    """(adj, puzzle, solution, retirés) : on part de la coloration complète et on retire des nœuds tant que la solution reste unique."""
    adj, solution = planted_instance(n_nodes, k, mean_degree, rng)
    puzzle = solution.copy()
    removed = 0
    for i in rng.permutation(n_nodes):
        if removed >= empties:
            break
        keep = puzzle[i]
        puzzle[i] = 0
        if count_solutions_graph(adj, k, puzzle) != 1:
            puzzle[i] = keep
            continue
        removed += 1
    return adj, puzzle, solution, removed


def pad(adj, puzzle, solution, n_max=MAX_NODES):
    n = len(puzzle)
    A = np.zeros((n_max, n_max), dtype=bool)
    A[:n, :n] = adj
    P = np.zeros(n_max, dtype=np.int64)
    S = np.zeros(n_max, dtype=np.int64)
    V = np.zeros(n_max, dtype=bool)
    P[:n], S[:n], V[:n] = puzzle, solution, True
    return A, P, S, V


def coloring_dataset(count, nodes_range, k, degree_range, seed, min_empty_fraction=0.25):
    """`count` problèmes (graphes de taille tirée dans `nodes_range`, degré moyen dans `degree_range`, k couleurs), complétés à MAX_NODES.

    Retourne un dictionnaire : P (puzzles), S (solutions), A (adjacences par exemple), V (nœuds réels), K (nombre de couleurs), E (vides).
    On exige au moins `min_empty_fraction` de nœuds à trouver, sinon le problème est trop facile et on le retire du jeu.
    """
    rng = np.random.default_rng(seed)
    P, S, A, V, E = [], [], [], [], []
    while len(P) < count:
        n = int(rng.integers(nodes_range[0], nodes_range[1] + 1))
        deg = float(rng.uniform(*degree_range))
        target = int(n * rng.uniform(min_empty_fraction, 0.9))
        adj, puzzle, solution, removed = make_coloring_puzzle(n, k, deg, target, rng)
        if removed < int(n * min_empty_fraction):
            continue
        a, p, s, v = pad(adj, puzzle, solution)
        A.append(a), P.append(p), S.append(s), V.append(v), E.append(removed)
    return {"P": np.array(P), "S": np.array(S), "A": np.array(A), "V": np.array(V), "K": np.full(count, k), "E": np.array(E)}

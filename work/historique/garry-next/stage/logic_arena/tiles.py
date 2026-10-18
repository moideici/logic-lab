"""2048 : tables de lignes et expectimax, sans copie d'environnement ni état caché.

Une grille est un tuple de quatre entiers de 16 bits. Chaque quartet contient
le logarithme d'une tuile. Les tables sont construites une fois avec NumPy ;
la recherche utilise ensuite des scalaires Python et des vues sans copie.
"""
from functools import lru_cache

import numpy as np

DIRECTIONS = ("up", "down", "left", "right")


@lru_cache(maxsize=1)
def row_tables():
    codes = np.arange(65536, dtype=np.uint32)
    values = (codes[:, None] >> np.array([0, 4, 8, 12])) & 15
    order = np.argsort(values == 0, axis=1, kind="stable")
    compact = np.take_along_axis(values, order, axis=1)
    cursor = np.zeros(65536, dtype=np.int32)
    indices = np.arange(65536)
    merged = np.zeros_like(values)
    gain = np.zeros(65536, dtype=np.uint32)
    for pos in range(4):
        first = np.where(cursor < 4, compact[indices, np.minimum(cursor, 3)], 0)
        second = compact[indices, np.minimum(cursor + 1, 3)]
        combine = (cursor < 3) & (first != 0) & (first == second)
        merged[:, pos] = np.minimum(15, first + combine)
        gain += np.where(combine, 1 << merged[:, pos], 0).astype(np.uint32)
        cursor += 1 + combine
    left = np.sum(merged << np.array([0, 4, 8, 12]), axis=1).astype(np.uint16)
    reversed_codes = ((codes & 15) << 12) | ((codes & 240) << 4) | ((codes >> 4) & 240) | (codes >> 12)
    reversed_left = left[reversed_codes].astype(np.uint32)
    right = (((reversed_left & 15) << 12) | ((reversed_left & 240) << 4)
             | ((reversed_left >> 4) & 240) | (reversed_left >> 12)).astype(np.uint16)

    ranks = values.astype(np.float64)
    diffs = ranks[:, :-1]**4 - ranks[:, 1:]**4
    monotone = np.minimum(np.maximum(diffs, 0).sum(axis=1), np.maximum(-diffs, 0).sum(axis=1))
    merges = ((compact[:, 1:] == compact[:, :-1]) & (compact[:, 1:] != 0)).sum(axis=1)
    value = (270*(values == 0).sum(axis=1) + 700*merges
             - 47*monotone - 11*(ranks**3.5).sum(axis=1))
    return tuple(memoryview(a) for a in (left, right, gain, value))


def pack(board):
    return tuple(sum((int(v).bit_length()-1 if v else 0) << (4*c) for c, v in enumerate(row)) for row in board)


def columns(rows):
    a, b, c, d = rows
    return ((a & 15) | ((b & 15) << 4) | ((c & 15) << 8) | ((d & 15) << 12),
            ((a >> 4) & 15) | (b & 240) | ((c & 240) << 4) | ((d & 240) << 8),
            ((a >> 8) & 15) | ((b >> 4) & 240) | (c & 3840) | ((d & 3840) << 4),
            (a >> 12) | ((b >> 8) & 240) | ((c >> 4) & 3840) | (d & 61440))


def move(rows, direction, tables=None):
    left, right, gain, _ = tables or row_tables()
    vertical = direction in ("up", "down")
    source = columns(rows) if vertical else rows
    table = left if direction in ("up", "left") else right
    moved = tuple(table[row] for row in source)
    return (columns(moved) if vertical else moved), sum(gain[row] for row in source)


def heuristic(rows, tables=None):
    value = (tables or row_tables())[3]
    return sum(value[row] for row in rows) + sum(value[row] for row in columns(rows))


def spawn_expectation(rows, tables=None):
    """Espérance exacte de l'heuristique après l'apparition d'une tuile.

    Une apparition ne change qu'une ligne et une colonne. On met donc à jour
    leurs contributions au lieu de reconstruire toutes les grilles filles.
    """
    value = (tables or row_tables())[3]
    cols = columns(rows)
    base = sum(value[row] for row in rows) + sum(value[col] for col in cols)
    adjustment, count = 0., 0
    for r, row in enumerate(rows):
        for c, shift in enumerate((0, 4, 8, 12)):
            if (row >> shift) & 15:
                continue
            col = cols[c]
            old = value[row] + value[col]
            adjustment += (.9*(value[row | (1 << shift)] + value[col | (1 << (r*4))] - old)
                           + .1*(value[row | (2 << shift)] + value[col | (2 << (r*4))] - old))
            count += 1
    return base + adjustment/count if count else base


def won(rows):
    return any((row & 15) >= 11 or ((row >> 4) & 15) >= 11
               or ((row >> 8) & 15) >= 11 or (row >> 12) >= 11 for row in rows)


def search(obs, legal, logits, budget, max_depth=2, critical_depth=None):
    from .agents import Exhausted

    tables = row_tables()
    initial = pack(obs["board"])
    ordered = sorted(legal, key=lambda a: -logits[DIRECTIONS.index(a["direction"])])
    cache = {}
    chance_cache = {}

    def max_value(rows, depth):
        budget.tick()
        if depth == 0:
            return heuristic(rows, tables)
        key = rows, depth
        if key in cache:
            return cache[key]
        best = -1e9
        for direction in DIRECTIONS:
            child, gain = move(rows, direction, tables)
            if child != rows:
                best = max(best, 1e9 if won(child) else chance(child, depth) + gain*.05)
        cache[key] = best
        return best

    def chance(rows, depth):
        budget.tick()
        key = rows, depth
        if key in chance_cache:
            return chance_cache[key]
        if depth == 0:
            return heuristic(rows, tables)
        if depth == 1:
            value = spawn_expectation(rows, tables)
            chance_cache[key] = value
            return value
        empty = [(r, shift) for r, row in enumerate(rows) for shift in (0, 4, 8, 12) if not ((row >> shift) & 15)]
        if not empty:
            return max_value(rows, depth-1)
        total = 0.
        for r, shift in empty:
            for rank, probability in ((1, .9), (2, .1)):
                child = list(rows)
                child[r] |= rank << shift
                total += probability*max_value(tuple(child), depth-1)/len(empty)
        chance_cache[key] = total
        return total

    best, best_value, depth_reached = ordered[0], -float("inf"), 0
    root_values=[]
    # Cette passe non récursive fournit toujours un coup évalué, même si le
    # délai expire pendant l'approfondissement ou l'initialisation des tables.
    for action in ordered:
        child, gain = move(initial, action["direction"], tables)
        value = 1e9 if won(child) else heuristic(child, tables) + gain*.05
        root_values.append({'action':action,'quality':[value]})
        if value > best_value + 1e-7:
            best, best_value = action, value
    depth_limit = critical_depth if critical_depth and sum(((row >> shift) & 15) == 0 for row in initial for shift in (0,4,8,12)) <= 4 else max_depth
    for depth in range(1, depth_limit+1):
        candidate, value = best, -float("inf")
        next_values=[]
        try:
            for action in ordered:
                child, gain = move(initial, action["direction"], tables)
                score = 1e9 if won(child) else chance(child, depth) + gain*.05
                next_values.append({'action':action,'quality':[score]})
                if score > value + 1e-7:
                    candidate, value = action, score
            best, depth_reached = candidate, depth
            root_values=next_values
        except Exhausted:
            break
    return best, {"method": "expectimax_goal" if best_value==1e9 else "neural_expectimax_tables", "optimal":best_value==1e9,"remaining_moves":1 if best_value==1e9 else None,"depth": depth_reached, "nodes": budget.nodes,"action_values":root_values}

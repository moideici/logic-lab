"""Alpha-bêta Puissance 4 avec protections tactiques et bitboards publics."""
from functools import lru_cache
import math


CENTER = (3, 2, 4, 1, 5, 0, 6)


def _won(bits):
    for shift in (1, 7, 6, 8):
        pairs = bits & (bits >> shift)
        if pairs & (pairs >> (2 * shift)):
            return True
    return False


@lru_cache(maxsize=1)
def _lines():
    lines = []
    for r in range(6):
        for c in range(7):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if 0 <= r + 3 * dr < 6 and 0 <= c + 3 * dc < 7:
                    lines.append(sum(1 << ((c + i * dc) * 7 + r + i * dr) for i in range(4)))
    return tuple(lines)


def search(obs, legal, budget, logits=None, weights=None, max_depth=10):
    # Six cases et une sentinelle par colonne empêchent les alignements
    # artificiels entre le sommet d'une colonne et le bas de la suivante.
    from .agents import Exhausted

    bits = [0, 0, 0]
    heights = [0] * 7
    for c in range(7):
        for r in range(6):
            player = obs["board"][5-r][c]
            if player:
                bits[player] |= 1 << (c * 7 + r)
                heights[c] = r + 1
    root = obs["current_player"]
    attack = (weights or {}).get("attack", 1.)
    defense = (weights or {}).get("defense", 1.)
    space = (weights or {}).get("space", 1.)
    masks = _lines()
    center_mask = sum(1 << (3 * 7 + r) for r in range(6))

    def available():
        return [c for c in CENTER if heights[c] < 6]

    def play(c, player):
        move = 1 << (c * 7 + heights[c])
        heights[c] += 1
        bits[player] |= move
        return move

    def undo(c, player, move):
        heights[c] -= 1
        bits[player] ^= move

    def immediate(player):
        return [c for c in available() if _won(bits[player] | (1 << (c * 7 + heights[c])))]

    def preference(c):
        return float(logits[c]) if logits is not None else -abs(c-3)

    def result(c, method, **info):
        return {"column": c}, {"method": method, "optimal": False, "nodes": budget.nodes, **info}

    wins = immediate(root)
    if wins:
        return result(max(wins, key=preference), "tactical_win", optimal=True, remaining_moves=1)

    # Ce précontrôle fixe (au plus sept coups et sept réponses chacun) reste
    # disponible quand la recherche bornée n'achève aucune profondeur.
    threats, safe, forks = immediate(3-root), [], []
    for c in available():
        move = play(c, root)
        try:
            if not immediate(3-root):
                safe.append(c)
                if len(immediate(root)) >= 2:
                    forks.append(c)
        finally:
            undo(c, root, move)
    if forks:
        return result(max(forks, key=preference), "tactical_fork", optimal=True,
                      remaining_moves=3, forced_win=True)
    if len(safe) == 1:
        return result(safe[0], "forced_block" if threats else "only_safe_move")

    def evaluate():
        score = 0.
        for line in masks:
            a, d = (bits[root] & line).bit_count(), (bits[3-root] & line).bit_count()
            if not d:
                score += (0, 2, 16, 120, 100000)[a] * attack
            if not a:
                score -= (0, 2, 18, 140, 100000)[d] * defense
        score += 7 * space * ((bits[root] & center_mask).bit_count()
                              - (bits[3-root] & center_mask).bit_count())
        return score

    cache, preferred = {}, {}

    def visit(depth, player, alpha, beta, ply):
        budget.tick()
        moves = available()
        if not moves:
            return 0
        if immediate(player):
            return 1000000-ply-1 if player == root else -1000000+ply+1
        threats = immediate(3-player)
        if len(threats) >= 2:
            return -1000000+ply+2 if player == root else 1000000-ply-2
        if threats:
            moves = threats
        elif not depth:
            return evaluate()
        original_a, original_b = alpha, beta
        position = bits[1], bits[2], player
        key = position + (depth,)
        cached = cache.get(key)
        if cached:
            value, flag = cached
            if flag == "exact":
                return value
            if flag == "lower":
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value
        prior = preferred.get(position)
        if prior in moves:
            moves = [prior] + [c for c in moves if c != prior]
        maximize = player == root
        value = -math.inf if maximize else math.inf
        best_column = moves[0]
        for c in moves:
            move = play(c, player)
            try:
                child = visit(max(0, depth-1), 3-player, alpha, beta, ply+1)
            finally:
                undo(c, player, move)
            better = child > value if maximize else child < value
            if better:
                value, best_column = child, c
            if maximize:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                break
        preferred[position] = best_column
        cache[key] = value, "upper" if value <= original_a else "lower" if value >= original_b else "exact"
        return value

    legal_columns = {a["column"] for a in legal}
    order = sorted((c for c in safe or available() if c in legal_columns), key=preference, reverse=True)
    best, depth_reached, best_value = order[0], 0, -math.inf
    for depth in range(1, max_depth+1):
        candidate, value = best, -math.inf
        try:
            for c in [best] + [c for c in order if c != best]:
                move = play(c, root)
                try:
                    score = visit(depth-1, 3-root, value, math.inf, 1)
                finally:
                    undo(c, root, move)
                if score > value:
                    candidate, value = c, score
            best, best_value, depth_reached = candidate, value, depth
            if value > 900000:
                break
        except Exhausted:
            break
    return result(best, "neural_alpha_beta" if logits is not None else "alpha_beta",
                  value=best_value if math.isfinite(best_value) else evaluate(),depth=depth_reached, forced_win=best_value > 900000)

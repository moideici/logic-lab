"""Agents de référence ; ils ne reçoivent que l'observation publique du jeu."""
from __future__ import annotations

import heapq
import itertools
import math
import random
import time
from dataclasses import dataclass

from .games import slide_2048, sudoku_candidates
from .identity import agent_identity


STYLES = {
    "balanced": {"attack": 1., "defense": 1., "space": 1., "risk": 0., "exploration": 0.},
    "aggressive": {"attack": 1.7, "defense": .7, "space": .7, "risk": .25, "exploration": 0.},
    "defensive": {"attack": .7, "defense": 1.7, "space": 1.2, "risk": -.25, "exploration": 0.},
    "greedy": {"attack": 1.4, "defense": .8, "space": .4, "risk": .15, "exploration": 0.},
    "positional": {"attack": .9, "defense": 1.1, "space": 2., "risk": -.1, "exploration": 0.},
    "exploratory": {"attack": 1., "defense": 1., "space": 1., "risk": .1, "exploration": .15},
}
NODE_LIMITS = (8, 32, 100, 300, 900, 2500, 7000, 18000, 45000, 100000)
TIME_LIMITS = (2, 4, 8, 15, 25, 45, 75, 120, 200, 350)


class Exhausted(Exception):
    pass


class Budget:
    def __init__(self, nodes, time_ms):
        self.limit = nodes
        self.nodes = 0
        self.start = time.monotonic()
        self.deadline = self.start + time_ms/1000

    def tick(self):
        if self.nodes >= self.limit or time.monotonic() >= self.deadline:
            raise Exhausted
        self.nodes += 1


@dataclass
class Decision:
    action: dict
    info: dict

    def as_dict(self):
        return {"action": self.action, "info": self.info}


class ReferenceAgent:
    def __init__(self, level=5, style="balanced", seed=0, time_ms=None):
        if type(level) is not int or not 1 <= level <= 10:
            raise ValueError("level doit être un entier entre 1 et 10")
        if style not in STYLES:
            raise ValueError(f"style doit être parmi {list(STYLES)}")
        if time_ms is not None and (type(time_ms) not in (int, float) or not math.isfinite(time_ms) or not 0 < time_ms <= 10000):
            raise ValueError("time_ms doit être entre 0 (exclu) et 10000")
        self.level, self.style = level, style
        self.weights = STYLES[style]
        self.rng = random.Random(seed)
        self.time_ms = TIME_LIMITS[level-1] if time_ms is None else time_ms

    def choose(self, observation, legal_actions):
        if not legal_actions or observation["done"]:
            raise ValueError("Aucun coup disponible")
        budget = Budget(NODE_LIMITS[self.level-1], self.time_ms)
        fallback = self.rng.choice(legal_actions)
        method = "random"
        action = fallback
        explore = max((10-self.level)*.025, self.weights["exploration"])
        if self.level == 1 or self.rng.random() < explore:
            pass
        else:
            name = observation["game"]
            method = {"tictactoe": "alpha_beta", "connect4": "alpha_beta", "2048": "expectimax",
                      "sudoku": "mrv_backtracking", "minesweeper": "public_constraints", "sliding_puzzle": "a_star"}[name]
            solver = {"tictactoe": self.line_game, "connect4": self.line_game, "2048": self.tiles,
                      "sudoku": self.sudoku, "minesweeper": self.mines, "sliding_puzzle": self.sliding}[name]
            action = solver(observation, legal_actions, budget, fallback)
        return Decision(action, {"agent": "reference", "identity": agent_identity(observation["game"]), "method": method, "level": self.level,
                                 "style": self.style, "nodes": budget.nodes, "node_limit": budget.limit,
                                 "time_ms": round((time.monotonic()-budget.start)*1000, 3),
                                 "budget_ms": self.time_ms})

    def line_game(self, obs, actions, budget, fallback):
        if obs["game"] == "connect4":
            from .connect4_wasm import search
            return search(obs, actions, budget, weights=self.weights, max_depth=min(10, self.level))[0]
        board = [r[:] for r in obs["board"]]
        rows, cols = len(board), len(board[0])
        target = 3 if cols == 3 else 4
        root = obs["current_player"]
        lines = []
        for r in range(rows):
            for c in range(cols):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    coords = [(r+i*dr, c+i*dc) for i in range(target)]
                    if all(0 <= x < rows and 0 <= y < cols for x, y in coords):
                        lines.append(coords)

        def moves():
            if cols == 3:
                return [(r, c) for r in range(rows) for c in range(cols) if not board[r][c]]
            return [(next(r for r in range(rows-1, -1, -1) if not board[r][c]), c) for c in range(cols) if not board[0][c]]

        def evaluate(ply):
            value = 0.
            for coords in lines:
                values = [board[r][c] for r, c in coords]
                a, d = values.count(root), values.count(3-root)
                if a == target:
                    return 1e6-ply, True
                if d == target:
                    return -1e6+ply, True
                if not d:
                    value += 8**a*self.weights["attack"]
                if not a:
                    value -= 8**d*self.weights["defense"]
            for r in range(rows):
                for c in range(cols):
                    if board[r][c]:
                        value += (1 if board[r][c] == root else -1)*(cols-abs(c-(cols-1)/2))*self.weights["space"]
            return value, False

        cache = {}

        def search(depth, player, alpha, beta, ply):
            budget.tick()
            key = (tuple(tuple(r) for r in board), player, depth)
            if key in cache:
                return cache[key]
            full_window = alpha == -math.inf and beta == math.inf
            value, terminal = evaluate(ply)
            available = moves()
            if terminal or not available or depth == 0:
                return value if terminal or available else 0
            maximize = player == root
            best = -math.inf if maximize else math.inf
            cut = False
            for r, c in sorted(available, key=lambda p: abs(p[1]-(cols-1)/2)):
                board[r][c] = player
                try:
                    v = search(depth-1, 3-player, alpha, beta, ply+1)
                finally:
                    board[r][c] = 0
                best = max(best, v) if maximize else min(best, v)
                if maximize:
                    alpha = max(alpha, best)
                else:
                    beta = min(beta, best)
                if beta <= alpha:
                    cut = True
                    break
            # Alpha-beta bounds are not exact transposition values.
            if not cut and full_window:
                cache[key] = best
            return best

        best_action = fallback
        max_depth = 9 if cols == 3 else min(10, self.level)
        for depth in range(1, max_depth+1):
            best_value, candidate = -math.inf, best_action
            try:
                for action in actions:
                    c = action.get("column", action.get("col"))
                    r = action.get("row")
                    if r is None:
                        r = next(r for r in range(rows-1, -1, -1) if not board[r][c])
                    board[r][c] = root
                    try:
                        v = search(depth-1, 3-root, -math.inf, math.inf, 1)
                    finally:
                        board[r][c] = 0
                    if v > best_value:
                        best_value, candidate = v, action
                best_action = candidate
                if best_value > 900000:
                    break
            except Exhausted:
                break
        return best_action

    def tiles(self, obs, actions, budget, fallback):
        def heuristic(board):
            logs = [[math.log2(v) if v else 0 for v in row] for row in board]
            empty = sum(v == 0 for row in board for v in row)
            smooth = sum(abs(logs[r][c]-logs[x][y]) for r in range(4) for c in range(4) for x, y in ((r+1, c), (r, c+1)) if x < 4 and y < 4 and logs[r][c] and logs[x][y])
            monotone = 0
            for line in logs + [list(col) for col in zip(*logs)]:
                monotone += max(sum(max(0, a-b) for a, b in zip(line, line[1:])), sum(max(0, b-a) for a, b in zip(line, line[1:])))
            largest = max(map(max, logs))
            corner = largest if largest in (logs[0][0], logs[0][3], logs[3][0], logs[3][3]) else 0
            return empty*25*self.weights["space"]-smooth*2*self.weights["defense"]+monotone*3+corner*8

        def search(board, depth, chance):
            budget.tick()
            if depth == 0:
                return heuristic(board)
            if chance:
                empty = [(r, c) for r in range(4) for c in range(4) if not board[r][c]]
                if not empty:
                    return search(board, depth-1, False)
                value = 0
                for r, c in empty:
                    for tile, p in ((2, .9), (4, .1)):
                        child = [row[:] for row in board]
                        child[r][c] = tile
                        value += p*search(child, depth-1, False)/len(empty)
                return value
            values = []
            for d in ("up", "down", "left", "right"):
                child, gain = slide_2048(board, d)
                if child != board:
                    values.append(gain*self.weights["attack"]+search(child, depth-1, True))
            return max(values, default=-10000)

        best = fallback
        for depth in range(0, min(6, self.level)+1, 2):
            candidate, value = best, -math.inf
            try:
                for action in actions:
                    child, gain = slide_2048(obs["board"], action["direction"])
                    score = gain*self.weights["attack"]+search(child, depth, True)
                    if score > value:
                        candidate, value = action, score
                best = candidate
            except Exhausted:
                break
        return best

    def sudoku(self, obs, actions, budget, fallback):
        board = [r[:] for r in obs["board"]]
        placements = [a for a in actions if "value" in a]
        cells = [(sudoku_candidates(board, r, c), r, c) for r in range(9) for c in range(9) if not board[r][c]]
        cells.sort(key=lambda x: (len(x[0]), x[1], x[2]))
        if cells and not cells[0][0]:
            return {"undo": True} if {"undo": True} in actions else fallback
        if not cells:
            return fallback
        candidates, r0, c0 = cells[0]
        if len(candidates) == 1:
            return {"row": r0, "col": c0, "value": candidates[0]}

        def solve():
            budget.tick()
            empty = [(sudoku_candidates(board, r, c), r, c) for r in range(9) for c in range(9) if not board[r][c]]
            if not empty:
                return True
            values, r, c = min(empty, key=lambda x: len(x[0]))
            if self.style == "exploratory":
                self.rng.shuffle(values)
            elif self.style in ("aggressive", "greedy"):
                values.reverse()
            for v in values:
                board[r][c] = v
                if solve():
                    return True
                board[r][c] = 0
            return False

        try:
            if solve():
                return {"row": r0, "col": c0, "value": board[r0][c0]}
            if {"undo": True} in actions:
                return {"undo": True}
        except Exhausted:
            pass
        # No answer key is available to the agent. A bounded search may need undo later.
        if placements:
            return {"row": r0, "col": c0, "value": candidates[-1 if self.style == "aggressive" else 0]}
        return fallback

    def mines(self, obs, actions, budget, fallback):
        board = obs["board"]
        n = len(board)
        hidden = {(r, c) for r in range(n) for c in range(n) if board[r][c] == -1}
        constraints = set()
        for r in range(n):
            for c in range(n):
                if board[r][c] >= 0:
                    cells = frozenset((x, y) for x in range(max(0, r-1), min(n, r+2)) for y in range(max(0, c-1), min(n, c+2)) if (x, y) in hidden)
                    if cells:
                        constraints.add((cells, board[r][c]))
        safe, bombs = set(), set()
        try:
            while True:
                budget.tick()
                updated = set()
                for cells, count in constraints:
                    count -= len(cells & bombs)
                    cells = cells - safe - bombs
                    if cells and 0 <= count <= len(cells):
                        updated.add((cells, count))
                old = len(safe)+len(bombs)
                for cells, count in updated:
                    if count == 0:
                        safe.update(cells)
                    elif count == len(cells):
                        bombs.update(cells)
                derived = set(updated)
                for a, na in updated:
                    for b, nb in updated:
                        budget.tick()
                        if a < b and 0 <= nb-na <= len(b-a):
                            derived.add((b-a, nb-na))
                if derived == constraints and old == len(safe)+len(bombs):
                    break
                constraints = derived
        except Exhausted:
            pass
        available = hidden-bombs or hidden
        if safe & available:
            available = safe & available
        base = max(0, obs["mine_count"]-len(bombs))/max(1, len(hidden-bombs))

        def value(p):
            local = [count/len(cells) for cells, count in constraints if p in cells and cells]
            risk = max(local) if local else base
            r, c = p
            area = sum((x, y) in hidden for x in range(max(0, r-1), min(n, r+2)) for y in range(max(0, c-1), min(n, c+2)))
            # Information preference only refines risk; inferred mines are never selected.
            return risk - area*.002*(1+self.weights["risk"]*3)
        r, c = min(sorted(available), key=value)
        return {"row": r, "col": c}

    def sliding(self, obs, actions, budget, fallback):
        initial = tuple(v for row in obs["board"] for v in row)
        goal = (1, 2, 3, 4, 5, 6, 7, 8, 0)

        def distance(state):
            return sum(abs(i//3-(v-1)//3)+abs(i%3-(v-1)%3) for i, v in enumerate(state) if v)

        weight = 1.3 if self.style in ("aggressive", "greedy") else 1.
        serial = itertools.count()
        queue = [(distance(initial)*weight, 0, next(serial), initial, None)]
        visited = {initial: 0}
        best_distance, best = distance(initial), fallback
        try:
            while queue:
                budget.tick()
                _, cost, _, state, first = heapq.heappop(queue)
                if visited.get(state) != cost:
                    continue
                h = distance(state)
                if first and h < best_distance:
                    best_distance, best = h, first
                if state == goal:
                    return first or fallback
                zero = state.index(0)
                r, c = divmod(zero, 3)
                for d, dr, dc in (("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)):
                    if not (0 <= r+dr < 3 and 0 <= c+dc < 3):
                        continue
                    target = (r+dr)*3+c+dc
                    child = list(state)
                    child[zero], child[target] = child[target], child[zero]
                    child = tuple(child)
                    if cost+1 < visited.get(child, math.inf):
                        visited[child] = cost+1
                        heapq.heappush(queue, (cost+1+weight*distance(child), cost+1, next(serial), child, first or {"direction": d}))
        except Exhausted:
            pass
        return best

"""Règles pures : observations publiques, actions JSON, récompenses par transition."""
from __future__ import annotations

import random
from copy import deepcopy


class Game:
    players = 1
    name = ""

    def __init__(self, seed=0, options=None):
        if type(seed) is not int:
            raise ValueError("seed doit être un entier")
        self.rng = random.Random(seed)
        self.options = options or {}
        self.current_player = 1
        self.done = False
        self.winner = None
        self.score = 0
        self.moves = 0

    def observation(self):
        return {"game": self.name, "board": deepcopy(self.board),
                "current_player": self.current_player, "done": self.done,
                "winner": self.winner, "score": self.score, "moves": self.moves}

    def step(self, action):
        # Equality in Python conflates True and 1; JSON actions must match types too.
        import json
        key = json.dumps(action, sort_keys=True)
        if self.done or key not in {json.dumps(a, sort_keys=True) for a in self.legal_actions()}:
            raise ValueError("Action illégale ou partie terminée")
        self.moves += 1
        return self.apply(action)


class LineGame(Game):
    players = 2

    def lines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    cells = [(r + i*dr, c + i*dc) for i in range(self.target)]
                    if all(0 <= x < self.rows and 0 <= y < self.cols for x, y in cells):
                        yield [self.board[x][y] for x, y in cells]

    def apply(self, action):
        if self.name == "connect4":
            c = action["column"]
            r = next(r for r in range(self.rows-1, -1, -1) if not self.board[r][c])
        else:
            r, c = action["row"], action["col"]
        self.board[r][c] = self.current_player
        if any(all(v == self.current_player for v in line) for line in self.lines()):
            self.done, self.winner = True, self.current_player
            self.score = 1
            return 1.0
        if not any(0 in row for row in self.board):
            self.done, self.winner = True, 0
        self.current_player = 3 - self.current_player
        return 0.0


class TicTacToe(LineGame):
    name, rows, cols, target = "tictactoe", 3, 3, 3

    def __init__(self, seed=0, options=None):
        super().__init__(seed, options)
        self.board = [[0]*3 for _ in range(3)]

    def legal_actions(self):
        return [] if self.done else [{"row": r, "col": c} for r in range(3) for c in range(3) if not self.board[r][c]]


class Connect4(LineGame):
    name, rows, cols, target = "connect4", 6, 7, 4

    def __init__(self, seed=0, options=None):
        super().__init__(seed, options)
        self.board = [[0]*7 for _ in range(6)]

    def legal_actions(self):
        return [] if self.done else [{"column": c} for c in range(7) if not self.board[0][c]]


def slide_2048(board, direction):
    """Déplacement déterministe ; apparition des tuiles séparée pour la recherche."""
    result = [[0]*4 for _ in range(4)]
    gain = 0
    for i in range(4):
        coords = {
            "left": [(i, j) for j in range(4)],
            "right": [(i, j) for j in range(3, -1, -1)],
            "up": [(j, i) for j in range(4)],
            "down": [(j, i) for j in range(3, -1, -1)],
        }[direction]
        values = [board[r][c] for r, c in coords if board[r][c]]
        merged = []
        j = 0
        while j < len(values):
            if j + 1 < len(values) and values[j] == values[j+1]:
                merged.append(values[j]*2)
                gain += values[j]*2
                j += 2
            else:
                merged.append(values[j])
                j += 1
        merged += [0]*(4-len(merged))
        for (r, c), v in zip(coords, merged):
            result[r][c] = v
    return result, gain


class Game2048(Game):
    name = "2048"

    def __init__(self, seed=0, options=None):
        super().__init__(seed, options)
        self.board = [[0]*4 for _ in range(4)]
        self.spawn()
        self.spawn()

    def spawn(self):
        empty = [(r, c) for r in range(4) for c in range(4) if not self.board[r][c]]
        if empty:
            r, c = self.rng.choice(empty)
            self.board[r][c] = 2 if self.rng.random() < .9 else 4

    def legal_actions(self):
        return [] if self.done else [{"direction": d} for d in ("up", "down", "left", "right") if slide_2048(self.board, d)[0] != self.board]

    def apply(self, action):
        self.board, gain = slide_2048(self.board, action["direction"])
        self.score += gain
        self.spawn()
        if max(map(max, self.board)) >= 2048:
            self.done, self.winner = True, 1
        elif not self.legal_actions():
            self.done, self.winner = True, 0
        return gain / 2048.0 + (1.0 if self.winner == 1 else 0.0)


def sudoku_candidates(board, r, c):
    if board[r][c]:
        return []
    used = set(board[r]) | {board[i][c] for i in range(9)}
    used |= {board[i][j] for i in range(r//3*3, r//3*3+3) for j in range(c//3*3, c//3*3+3)}
    return sorted(set(range(1, 10)) - used)


class Sudoku(Game):
    name = "sudoku"
    # Grille à solution unique, transformée par symétries qui préservent les règles.
    puzzle = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"

    def __init__(self, seed=0, options=None):
        super().__init__(seed, options)
        digits = list(range(1, 10))
        self.rng.shuffle(digits)
        groups = list(range(3))
        self.rng.shuffle(groups)
        rows = []
        for g in groups:
            sub = list(range(3))
            self.rng.shuffle(sub)
            rows.extend(g*3+i for i in sub)
        self.board = [[digits[int(self.puzzle[r*9+c])-1] if self.puzzle[r*9+c] != "0" else 0 for c in range(9)] for r in rows]
        self.givens = deepcopy(self.board)
        self.history = []

    def observation(self):
        return {**super().observation(), "givens": deepcopy(self.givens), "history": [list(cell) for cell in self.history]}

    def legal_actions(self):
        if self.done:
            return []
        actions = [{"row": r, "col": c, "value": v} for r in range(9) for c in range(9) for v in sudoku_candidates(self.board, r, c)]
        if self.history:
            actions.append({"undo": True})
        return actions

    def apply(self, action):
        if "undo" in action:
            r, c = self.history.pop()
            self.board[r][c] = 0
            self.score -= 1
            return -.02
        r, c = action["row"], action["col"]
        self.board[r][c] = action["value"]
        self.history.append((r, c))
        self.score += 1
        if all(all(row) for row in self.board):
            self.done, self.winner = True, 1
        return 1.0 if self.done else .01


class Minesweeper(Game):
    name = "minesweeper"

    def __init__(self, seed=0, options=None):
        super().__init__(seed, options)
        self.size, self.mine_count = 8, 10
        self.board = [[-1]*self.size for _ in range(self.size)]
        self.mines = None

    def neighbors(self, r, c):
        return [(x, y) for x in range(max(0, r-1), min(self.size, r+2)) for y in range(max(0, c-1), min(self.size, c+2)) if (x, y) != (r, c)]

    def observation(self):
        return {**super().observation(), "mine_count": self.mine_count}

    def legal_actions(self):
        return [] if self.done else [{"row": r, "col": c} for r in range(self.size) for c in range(self.size) if self.board[r][c] == -1]

    def apply(self, action):
        r, c = action["row"], action["col"]
        if self.mines is None:
            protected = set(self.neighbors(r, c)) | {(r, c)}
            self.mines = set(self.rng.sample([(x, y) for x in range(self.size) for y in range(self.size) if (x, y) not in protected], self.mine_count))
        if (r, c) in self.mines:
            self.board[r][c] = -2
            self.done, self.winner = True, 0
            return -1.0
        before = self.score
        stack = [(r, c)]
        while stack:
            x, y = stack.pop()
            if self.board[x][y] != -1:
                continue
            count = sum(p in self.mines for p in self.neighbors(x, y))
            self.board[x][y] = count
            self.score += 1
            if not count:
                stack.extend(p for p in self.neighbors(x, y) if self.board[p[0]][p[1]] == -1)
        if self.score == self.size*self.size-self.mine_count:
            self.done, self.winner = True, 1
        return (self.score-before)/54 + (1.0 if self.done else 0.0)


class SlidingPuzzle(Game):
    name = "sliding_puzzle"

    def __init__(self, seed=0, options=None):
        super().__init__(seed, options)
        scramble = self.options.get("scramble", 30)
        if type(scramble) is not int or not 1 <= scramble <= 200:
            raise ValueError("scramble doit être un entier entre 1 et 200")
        self.board = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        previous = None
        for _ in range(scramble):
            choices = self.legal_actions()
            candidates = [a for a in choices if a["direction"] != previous] or choices
            action = self.rng.choice(candidates)
            self.swap(action["direction"])
            previous = {"up": "down", "down": "up", "left": "right", "right": "left"}[action["direction"]]
        if self.distance() == 0:
            self.swap("up")

    def distance(self):
        return sum(abs(r-(v-1)//3)+abs(c-(v-1)%3) for r, row in enumerate(self.board) for c, v in enumerate(row) if v)

    def legal_actions(self):
        if self.done:
            return []
        r, c = next((r, c) for r in range(3) for c in range(3) if self.board[r][c] == 0)
        return [{"direction": d} for d, dr, dc in (("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)) if 0 <= r+dr < 3 and 0 <= c+dc < 3]

    def swap(self, direction):
        r, c = next((r, c) for r in range(3) for c in range(3) if not self.board[r][c])
        dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[direction]
        self.board[r][c], self.board[r+dr][c+dc] = self.board[r+dr][c+dc], 0

    def apply(self, action):
        before = self.distance()
        self.swap(action["direction"])
        after = self.distance()
        self.score = -after
        if not after:
            self.done, self.winner = True, 1
        return 1.0 if self.done else (before-after)*.05-.01


GAMES = {g.name: g for g in (TicTacToe, Game2048, Sudoku, Connect4, Minesweeper, SlidingPuzzle)}


def make_game(name, seed=0, options=None):
    if name not in GAMES:
        raise ValueError(f"Jeu inconnu : {name}. Choix : {', '.join(GAMES)}")
    options = {} if options is None else options
    if not isinstance(options, dict):
        raise ValueError("options doit être un objet JSON")
    allowed = {"scramble"} if name == "sliding_puzzle" else set()
    if set(options) - allowed:
        raise ValueError(f"Options inconnues : {sorted(set(options)-allowed)}")
    return GAMES[name](seed, options)

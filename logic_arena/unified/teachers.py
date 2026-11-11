"""Professeurs : morpion (minimax exact), Puissance 4 (solveur exact, étiquettes existantes), dames (recherche renforcée, étiquettes existantes),
Gomoku et Hex (moteurs à la main en JS, auto-parties). Chaque fonction renvoie un `Records`."""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from .dataset import Records

ROOT = Path(__file__).resolve().parents[2]
VALUE_SCALE = {"gomoku": 2e4, "hex": 200.0, "dames": 300.0}


def squash(game, score):
    return float(np.tanh(score / VALUE_SCALE[game]))


# ---------------------------------------------------------------- morpion
_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def _ttt_winner(b):
    for x, y, z in _LINES:
        if b[x] and b[x] == b[y] == b[z]:
            return b[x]
    return 0


def ttt_records():
    """Toutes les positions atteignables non terminales ; score d'un coup = valeur exacte (+1 gain, 0 nul, -1 perte) pour qui le joue."""
    cache = {}

    def value(b, p):  # valeur pour le joueur p au trait
        key = (b, p)
        if key in cache:
            return cache[key]
        if _ttt_winner(b):
            v = -1
        elif all(b):
            v = 0
        else:
            v = max(-value(b[:i] + (p,) + b[i + 1:], 3 - p) for i in range(9) if not b[i])
        cache[key] = v
        return v

    rec = Records("tictactoe", 9)
    seen = set()
    stack = [((0,) * 9, 1)]
    while stack:
        b, p = stack.pop()
        if (b, p) in seen or _ttt_winner(b) or all(b):
            continue
        seen.add((b, p))
        acts, sc = [], []
        for i in range(9):
            if not b[i]:
                nb = b[:i] + (p,) + b[i + 1:]
                acts.append({"row": i // 3, "col": i % 3})
                sc.append(-value(nb, 3 - p))
                stack.append((nb, 3 - p))
        board = [list(b[r * 3:r * 3 + 3]) for r in range(3)]
        rec.add({"game": "tictactoe", "board": board, "current_player": p}, acts, sc, max(sc))
    return rec


# ---------------------------------------------------------------- Puissance 4
def c4_board(pos, mask):
    """Plateau (rangée 0 = haut) d'une position en bitboards ; le joueur au trait (pos) est le joueur 1."""
    board = [[0] * 7 for _ in range(6)]
    for c in range(7):
        for r in range(6):
            bit = 1 << (c * 7 + r)
            if mask & bit:
                board[5 - r][c] = 1 if pos & bit else 2
    return board


def c4_records(path=None, limit=None):
    """Étiquettes du solveur exact : +1 gain, 0 nul, -1 perte, -2 colonne pleine (training-lab/data/c4-labels-1.npz)."""
    d = dict(np.load(path or ROOT / "training-lab" / "data" / "c4-labels-1.npz"))
    n = len(d["pos"]) if limit is None else min(limit, len(d["pos"]))
    rec = Records("connect4", 7)
    for i in range(n):
        out = d["out"][i]
        cols = [c for c in range(7) if out[c] != -2]
        rec.add({"game": "connect4", "board": c4_board(int(d["pos"][i]), int(d["mask"][i])), "current_player": 1},
                [{"column": c} for c in cols], [float(out[c]) for c in cols], float(max(out[c] for c in cols)))
    return rec


# ---------------------------------------------------------------- dames
def dames_records(path=None, limit=None):
    """Étiquettes de la recherche renforcée (training-lab/data/dames-labels-1.npz) : score de chaque coup légal, ordre de `legal_moves`."""
    from ..zero import dames
    d = dict(np.load(path or ROOT / "training-lab" / "data" / "dames-labels-1.npz"))
    n = len(d["next"]) if limit is None else min(limit, len(d["next"]))
    rec = Records("dames", 128)
    for i in range(n):
        cells, nxt = d["cells"][i].tolist(), int(d["next"][i])
        moves = dames.legal_moves(cells, nxt)
        sc = d["scores"][i][:len(moves)]
        if not len(moves) or np.isnan(sc).any():
            continue
        obs = {"game": "dames", "cells": cells, "next": nxt, "quiet": int(d["quiet"][i]), "current_player": nxt + 1}
        rec.add(obs, moves, [float(x) for x in sc], squash("dames", float(sc.max())))
    return rec


# ---------------------------------------------------------------- Gomoku / Hex (moteurs JS)
def _run_teacher(args):
    game, games, seed, ms, noise = args
    cmd = ["node", str(ROOT / "tools" / "teachers" / "teacher-data.mjs"), "--game", game, "--games", str(games), "--seed", str(seed), "--ms", str(ms), "--noise", str(noise)]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def js_records(game, games_per_worker=4, workers=8, seed=1, ms=60, noise=0.15, top=16):
    """Auto-parties du moteur à la main ; valeur = résultat réel de la partie (+1/0/-1), valeur de recherche en second."""
    jobs = [(game, games_per_worker, seed * 1000 + w, ms, noise) for w in range(workers)]
    rec = Records(game, top)
    with ThreadPoolExecutor(workers) as pool:
        for lines in pool.map(_run_teacher, jobs):
            for e in lines:
                rec.add(e["obs"], e["moves"], e["scores"], float(e["z"]), squash(game, max(e["scores"])))
    return rec

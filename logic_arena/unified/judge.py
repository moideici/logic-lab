"""Juges indépendants : un joueur `policy(obs, legal) -> action` est mesuré contre des adversaires qui ne sont pas son professeur d'entraînement.

morpion : minimax exact · Puissance 4 : solveur exact (taux de coups fautifs) · Hex et Gomoku : moteurs à la main (serveur JS) · dames : recherche C++.
Ouvertures identiques pour chaque paire de parties (camps échangés).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from .adapters import make_adapter

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- adversaires de référence
class JsEngine:
    """Moteur Gomoku / Hex à la main, en processus Node persistant."""

    def __init__(self):
        self.proc = subprocess.Popen(["node", str(ROOT / "tools" / "teachers" / "engine-server.mjs")], cwd=ROOT, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True, bufsize=1)
        self.n = 0

    def choose(self, obs, legal, ms=100):
        self.n += 1
        self.proc.stdin.write(json.dumps({"id": self.n, "game": obs["game"], "obs": obs, "legal": legal, "ms": ms}) + "\n")
        self.proc.stdin.flush()
        reply = json.loads(self.proc.stdout.readline())
        if "error" in reply:
            raise RuntimeError(reply["error"])
        return reply["action"]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def random_policy(seed=0):
    rng = np.random.default_rng(seed)
    return lambda obs, legal: legal[int(rng.integers(len(legal)))]


def _score(results):
    n = max(1, results["w"] + results["d"] + results["l"])
    return round((results["w"] + results["d"] / 2) / n, 3)


# ---------------------------------------------------------------- morpion
_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def _ttt_value(b, p, cache={}):
    key = (b, p)
    if key not in cache:
        w = next((b[x] for x, y, z in _LINES if b[x] and b[x] == b[y] == b[z]), 0)
        cache[key] = -1 if w else 0 if all(b) else max(-_ttt_value(b[:i] + (p,) + b[i + 1:], 3 - p) for i in range(9) if not b[i])
    return cache[key]


def judge_tictactoe(policy, games=40, seed=0):
    rng = np.random.default_rng(seed)
    out = {"perfect": {"w": 0, "d": 0, "l": 0}, "random": {"w": 0, "d": 0, "l": 0}}
    for opp in out:
        for g in range(games):
            env, seat = make_adapter("tictactoe"), 1 + g % 2
            while not env.done:
                obs, legal = env.observation(), env.legal()
                if env.player == seat:
                    action = policy(obs, legal)
                elif opp == "random":
                    action = legal[int(rng.integers(len(legal)))]
                else:
                    b, p = tuple(v for row in obs["board"] for v in row), env.player
                    vals = [(-_ttt_value(b[:a["row"] * 3 + a["col"]] + (p,) + b[a["row"] * 3 + a["col"] + 1:], 3 - p), a) for a in legal]
                    best = max(v for v, _ in vals)
                    action = [a for v, a in vals if v == best][int(rng.integers(sum(v == best for v, _ in vals)))]
                env.step(action)
            out[opp]["w" if env.winner == seat else "d" if env.winner == 0 else "l"] += 1
    return {"vs_perfect": out["perfect"], "vs_random": out["random"], "losses_vs_perfect": out["perfect"]["l"]}


# ---------------------------------------------------------------- Puissance 4
def judge_connect4(policy, games=40, opening=6, seed=0):
    """Écart à la perfection : un coup est fautif s'il dégrade le résultat théorique de la position (solveur exact)."""
    from ..zero import c4, c4solver

    def bits(obs):
        pos, mask = c4.from_board(obs["board"], obs["current_player"])
        return int(pos), int(mask)

    rng = np.random.default_rng(seed)
    moves = errors = reached = played = 0
    res = {"w": 0, "d": 0, "l": 0}
    for g in range(games):
        env = make_adapter("connect4", seed + g)
        orng = np.random.default_rng(seed + g // 2)
        for _ in range(opening):
            legal = env.legal()
            env.step(legal[int(orng.integers(len(legal)))])
        if env.done:
            continue
        seat = 1 + g % 2
        start_theory = np.sign(c4solver.solve(*bits(env.observation()), True)) * (1 if env.player == seat else -1)
        while not env.done:
            obs, legal = env.observation(), env.legal()
            pos, mask = bits(obs)
            s = c4solver.scores(pos, mask, True)
            if env.player == seat:
                a = policy(obs, legal)
                outcome = np.sign(s)
                best = max(outcome[x["column"]] for x in legal)
                errors += outcome[a["column"]] < best
                moves += 1
            else:
                best = [c for c in c4solver.optimal_columns(pos, mask, True)]
                a = {"column": int(best[int(rng.integers(len(best)))])}
            env.step(a)
        r = 1 if env.winner == seat else 0 if env.winner == 0 else -1
        reached += r >= start_theory
        played += 1
        res["w" if r > 0 else "d" if r == 0 else "l"] += 1
    return {"games": played, "moves": moves, "error_rate": round(errors / max(1, moves), 4), "theory_reached": round(reached / max(1, played), 3),
            "score_vs_perfect": _score(res), **res}


# ---------------------------------------------------------------- Gomoku et Hex contre les moteurs à la main
def judge_engine_match(game, policy, games=20, ms=100, seed=0, engine=None):
    """Gomoku : ouvertures Swap2 jouées par le moteur (le joueur testé joue la phase « play »). Hex : première pierre aléatoire, ensuite tout est au joueur testé."""
    own = engine is None
    engine = engine or JsEngine()
    res = {"w": 0, "d": 0, "l": 0}
    try:
        for g in range(games):
            env = make_adapter(game, seed + g)
            orng = np.random.default_rng(seed * 7919 + g // 2)
            seat = 1 + g % 2
            plies = 0
            while not env.done and plies < (300 if game == "gomoku" else 100):
                obs, legal = env.observation(), env.legal()
                if game == "gomoku" and obs["gomoku_state"]["phase"] in ("opening_three", "opening_two"):
                    cells = [a for a in legal if abs(a["row"] - 7) <= 2 and abs(a["col"] - 7) <= 2]
                    action = cells[int(orng.integers(len(cells)))]
                elif game == "gomoku" and obs["gomoku_state"]["phase"] != "play":
                    action = engine.choose(obs, [a for a in legal if "choose" in a], ms)
                elif game == "hex" and plies == 0:
                    action = legal[int(orng.integers(len(legal)))]
                elif env.player == seat:
                    action = policy(obs, legal)
                else:
                    action = engine.choose(obs, legal, ms)
                env.step(action)
                plies += 1
            res["w" if env.winner == seat else "l" if env.winner in (1, 2) else "d"] += 1
    finally:
        if own:
            engine.close()
    return {"games": games, **res, "score": _score(res), "ms": ms}


# ---------------------------------------------------------------- dames
def judge_dames(policy, games=20, level="normal", opening=4, seed=0):
    """Adversaire : copie du bot de multi (normal : profondeur 4, difficile : profondeur 7) ou recherche renforcée (fort)."""
    from ..zero import dames
    depth, budget, mode = {"facile": (2, 2000, 0), "normal": (4, 2000, 0), "difficile": (7, 20000, 0), "fort": (6, 100000, 1)}[level]
    res = {"w": 0, "d": 0, "l": 0}
    for g in range(games):
        env = make_adapter("dames")
        orng = np.random.default_rng(seed + g // 2)
        for _ in range(opening):
            legal = env.legal()
            env.step(legal[int(orng.integers(len(legal)))])
        seat = 1 + g % 2
        plies = 0
        while not env.done and plies < 300:
            obs, legal = env.observation(), env.legal()
            if env.player == seat:
                action = policy(obs, legal)
            else:
                action = dames.search(obs["cells"], obs["next"], obs["quiet"], depth, budget, mode)[0]
            env.step(action)
            plies += 1
        res["w" if env.winner == seat else "l" if env.winner in (1, 2) else "d"] += 1
    return {"games": games, **res, "score": _score(res), "level": level}

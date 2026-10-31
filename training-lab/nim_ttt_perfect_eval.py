"""Garry contre la théorie exacte : Nim (somme xor des piles = 0 est perdante) et morpion (négamax exhaustif).
Mesure : sur les positions où Garry peut gagner (Nim) ou ne pas perdre (morpion), part des coups qui conservent le résultat théorique.
Usage : python training-lab/nim_ttt_perfect_eval.py [--agent garry10|teacher10] [--games 200]"""
import argparse
import functools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.games import make_game  # noqa: E402


def make_agent(name):
    level = int(name.replace("garry", "").replace("teacher", ""))
    if name.startswith("garry"):
        from logic_arena.neural import NeuralAgent
        return NeuralAgent(level=level, seed=0, time_ms=100)
    from logic_arena.agents import ReferenceAgent
    return ReferenceAgent(level, seed=0, time_ms=100)


def nim_eval(agent, games, seed):
    rng = np.random.default_rng(seed)
    moves = good = 0
    wins = n_win_pos = 0
    for g in range(games):
        env = make_game("nim", seed + g, None)
        me = 1 + g % 2
        start_n = None
        while not env.done:
            obs, legal = env.observation(), env.legal_actions()
            sizes = [sum(r) for r in obs["board"]]
            x = int(np.bitwise_xor.reduce(sizes))
            if obs["current_player"] == me:
                a = agent.choose(obs, legal).action
                if x:
                    after = list(sizes)
                    after[a["pile"]] -= a["take"]
                    moves += 1
                    good += int(np.bitwise_xor.reduce(after) == 0)
                    start_n = True if start_n is None else start_n
            else:
                # adversaire : au hasard, mais joue le coup parfait avec probabilité 0,3 pour mettre Garry sous pression
                perfect = [m for m in legal if int(np.bitwise_xor.reduce([s - (m["take"] if i == m["pile"] else 0) for i, s in enumerate(sizes)])) == 0]
                a = perfect[0] if perfect and rng.random() < 0.3 else legal[int(rng.integers(len(legal)))]
            env.step(a)
    return {"jeu": "nim", "coups_sur_position_gagnante": moves, "coups_parfaits": good, "taux": round(good / max(moves, 1), 4)}


TTT_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


@functools.lru_cache(maxsize=None)
def ttt_value(cells, player):
    for a, b, c in TTT_LINES:
        if cells[a] and cells[a] == cells[b] == cells[c]:
            return 1 if cells[a] == player else -1
    if all(cells):
        return 0
    return max(-ttt_value(cells[:i] + (player,) + cells[i + 1:], 3 - player) for i in range(9) if not cells[i])


def ttt_eval(agent, games, seed):
    rng = np.random.default_rng(seed)
    moves = good = losses = 0
    for g in range(games):
        env = make_game("tictactoe", seed + g, None)
        me = 1 + g % 2
        while not env.done:
            obs, legal = env.observation(), env.legal_actions()
            cells = tuple(v for row in obs["board"] for v in row)
            if obs["current_player"] == me:
                a = agent.choose(obs, legal).action
                best = max(-ttt_value(cells[:i] + (me,) + cells[i + 1:], 3 - me) for i in range(9) if not cells[i])
                i = a["row"] * 3 + a["col"]
                moves += 1
                good += int(-ttt_value(cells[:i] + (me,) + cells[i + 1:], 3 - me) == best)
            else:
                a = legal[int(rng.integers(len(legal)))]
            env.step(a)
        losses += int(env.winner not in (None, 0, me))
    return {"jeu": "morpion", "coups": moves, "coups_optimaux": good, "taux": round(good / max(moves, 1), 4), "defaites_contre_hasard": losses, "parties": games}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="garry10")
    ap.add_argument("--games", type=int, default=200)
    a = ap.parse_args()
    agent = make_agent(a.agent)
    for f in (nim_eval, ttt_eval):
        print(json.dumps({"agent": a.agent, **f(agent, a.games, 100)}, ensure_ascii=False))

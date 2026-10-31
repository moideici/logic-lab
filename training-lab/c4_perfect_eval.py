"""Mesure de l'écart à la perfection au Puissance 4 : un joueur de Garry contre le solveur exact, depuis des ouvertures aléatoires de 6 coups.

Pour chaque coup du joueur testé on demande au solveur si ce coup conserve le résultat théorique de la position (gain, nul ou perte).
Sorties : taux d'erreurs (coups qui dégradent le résultat), taux de parties où le résultat théorique est atteint, score contre le joueur parfait.
Usage : python training-lab/c4_perfect_eval.py --player garry10|teacher10|zero [--games 40] [--opening 6]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.games import make_game  # noqa: E402
from logic_arena.zero import c4, c4solver  # noqa: E402


def sign(x):
    return (x > 0) - (x < 0)


def bitboards(env):
    obs = env.observation()
    pos, mask = c4.from_board(obs["board"], obs["current_player"])
    return int(pos), int(mask), obs


def load_player(name, sims):
    if name.startswith(("garry", "teacher")):
        from logic_arena.zero.arena import GarryOpponent, TeacherOpponent
        level = int(name.split("garry")[-1] if name.startswith("garry") else name.split("teacher")[-1])
        opp = GarryOpponent(level, time_ms=100) if name.startswith("garry") else TeacherOpponent(level, time_ms=100)
        return lambda env, obs, legal: opp.choose(obs, legal)["column"]
    import torch
    raw = name.startswith(("raw", "safe"))
    depth = int(name.split(":")[0][4:] or 12) if name.startswith("safe") else 0
    from logic_arena.zero.mcts import BatchedMCTS
    from logic_arena.zero.net import PolicyValueNet
    from logic_arena.zero.rules import Connect4Rules
    rules = Connect4Rules()
    ckpt = Path(__file__).resolve().parent / "models" / "zero-c4" / (name.split(":", 1)[1] if ":" in name else "dernier.pt")
    blob = torch.load(ckpt, map_location="cpu", weights_only=True)
    net = PolicyValueNet(rules.planes_shape, rules.n_actions, blob.get("channels", 64), blob.get("blocks", 4))
    net.load_state_dict(blob["net"])
    net.eval()
    mcts = BatchedMCTS(rules, net, "cpu", sims=sims, seed=1)

    def choose(env, obs, legal):
        if raw:  # réseau seul, sans recherche
            x = torch.tensor(c4.planes(*[np.array([v], dtype=np.uint64) for v in c4.from_board(obs["board"], obs["current_player"])]))
            with torch.no_grad():
                logits = net(x)[0][0].numpy()
            allowed = {a["column"] for a in legal}
            if depth:  # réseau + recherche tactique : gain forcé d'abord, jamais une perte forcée si on peut l'éviter
                pos, mask = c4.from_board(obs["board"], obs["current_player"])
                t = c4solver.tactical(int(pos), int(mask), depth)
                wins = [c for c in allowed if t[c] == 1]
                if wins:
                    return max(wins, key=lambda c: logits[c])
                safe = [c for c in allowed if t[c] != -1] or list(allowed)
                return max(safe, key=lambda c: logits[c])
            return max(allowed, key=lambda c: logits[c])
        visits, _ = mcts.search(rules.from_observation(obs), noise=False)
        allowed = {a["column"] for a in legal}
        return next(int(i) for i in np.argsort(-visits[0], kind="stable") if int(i) in allowed)
    return choose


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--player", required=True)
    ap.add_argument("--games", type=int, default=40)
    ap.add_argument("--opening", type=int, default=6)
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    play = load_player(a.player, a.sims)
    rng = np.random.default_rng(a.seed)
    moves = errors = 0
    reached = 0
    results = {"v": 0, "n": 0, "d": 0}
    for g in range(a.games):
        env = make_game("connect4", a.seed + g, None)
        orng = np.random.default_rng(a.seed + g // 2)  # même ouverture pour la paire de parties (camps échangés)
        for _ in range(a.opening):
            legal = env.legal_actions()
            env.step(legal[int(orng.integers(len(legal)))])
        if env.done:
            continue
        me = 1 + g % 2
        pos, mask, obs = bitboards(env)
        start_value = sign(c4solver.solve(pos, mask, True)) * (1 if obs["current_player"] == me else -1)
        while not env.done:
            pos, mask, obs = bitboards(env)
            legal = env.legal_actions()
            s = c4solver.scores(pos, mask, True)
            outcome = np.sign(s)
            best = max(outcome[c] for c in range(7) if s[c] != -1000)
            if obs["current_player"] == me:
                col = play(env, obs, legal)
                moves += 1
                if outcome[col] < best:
                    errors += 1
            else:
                col = int(rng.choice([c for c in range(7) if s[c] != -1000 and outcome[c] == best]))
            env.step({"column": col})
        mine = 1 if env.winner == me else (-1 if env.winner not in (None, 0) else 0)
        results["v" if mine > 0 else "d" if mine < 0 else "n"] += 1
        reached += mine >= start_value
    n = results["v"] + results["n"] + results["d"]
    out = {"joueur": a.player, "parties": n, "coups": moves, "erreurs": errors, "taux_erreur": round(errors / max(moves, 1), 4),
           "resultat_theorique_atteint": round(reached / max(n, 1), 3), "score": round((results["v"] + 0.5 * results["n"]) / max(n, 1), 3), **results}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

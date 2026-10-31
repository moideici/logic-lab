"""Duels de dames (règles de multi) entre deux joueurs de recherche, ouvertures aléatoires identiques par paire (camps échangés).
Joueurs : reseau-FICHIER.pt (réseau seul, sans recherche), multi-facile|multi-normal|multi-difficile (copie du bot de multi, la facile joue au hasard 35 % du temps), fort-D-B (mode renforcé : profondeur D, budget B nœuds).
Usage : python training-lab/dames_match.py A B [--games 40] [--opening 4]"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero import dames  # noqa: E402


def make_player(name, rng):
    if name.startswith("multi-"):
        level = name.split("-")[1]
        depth, budget = {"facile": (2, 2000), "normal": (4, 2000), "difficile": (7, 20000)}[level]

        def choose(state):
            moves = state.moves()
            if level == "facile" and rng.random() < 0.35:
                return moves[int(rng.integers(len(moves)))]
            return dames.search(state.cells, state.next, state.quiet, depth, budget, 0)[0]
        return choose
    if name.startswith("reseau-"):
        import torch
        from logic_arena.zero import dames_net as dn
        blob = torch.load(Path(__file__).resolve().parent / "models" / "dames" / name.split("-", 1)[1], map_location="cpu", weights_only=True)
        net = dn.build_net(blob["channels"], blob["blocks"])
        net.load_state_dict(blob["net"])
        return dn.NetPlayer(net).choose
    _, depth, budget = name.split("-")

    def choose(state):
        return dames.search(state.cells, state.next, state.quiet, int(depth), int(budget), 1)[0]
    return choose


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--games", type=int, default=40)
    ap.add_argument("--opening", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    pa, pb = make_player(args.a, rng), make_player(args.b, rng)
    wins = draws = losses = 0
    for g in range(args.games):
        orng = np.random.default_rng(args.seed + g // 2)
        state = dames.State.new()
        for _ in range(args.opening):
            moves = state.moves()
            state = state.advance(*moves[int(orng.integers(len(moves)))])
        a_seat = g % 2
        plies = 0
        while state.status == "playing" and plies < 300:
            move = (pa if state.next == a_seat else pb)(state)
            state = state.advance(*move)
            plies += 1
        if state.status == "won":
            wins += state.winner == a_seat
            losses += state.winner != a_seat
        else:
            draws += 1
    print(json.dumps({"A": args.a, "B": args.b, "parties": args.games, "victoires_A": wins, "nuls": draws, "defaites_A": losses,
                      "score_A": round((wins + 0.5 * draws) / args.games, 3)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Garry Zéro aux Dames de multi : auto-apprentissage avec MCTS, initialisé par le réseau distillé de la recherche.

Boucle : parties contre soi-même (MCTS guidé par le réseau) -> exemples -> entraînement -> duels périodiques (MCTS du réseau) contre les bots de multi
et la recherche renforcée, arbitrés par le moteur de règles complet (`dames.State`, répétitions comprises).
Usage : python training-lab/dames_zero.py --init training-lab/models/dames/distill.pt --minutes 60 --out training-lab/models/dames-zero
        python training-lab/dames_zero.py --init ... --eval-only   (mesure seulement réseau + MCTS)
Aucune écriture hors de --out."""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero import dames, dames_net as dn  # noqa: E402
from logic_arena.zero.dames_rules import DamesRules  # noqa: E402
from logic_arena.zero.mcts import BatchedMCTS  # noqa: E402
from logic_arena.zero.selfplay import Replay, self_play, train_steps  # noqa: E402

OPPONENTS = {"multi-normal": (0, 4, 2000), "multi-difficile": (0, 7, 20000), "fort-6": (1, 6, 100000)}


def opponent_move(name, state):
    mode, depth, budget = OPPONENTS[name]
    return dames.search(state.cells, state.next, state.quiet, depth, budget, mode)[0]


def mcts_match(rules, net, opponent, games=20, sims=100, device="cpu", seed=500, opening=4):
    """Le réseau (avec MCTS, sans bruit) contre `opponent`, ouvertures aléatoires identiques par paire de parties, camps échangés."""
    mcts = BatchedMCTS(rules, net, device, sims=sims, seed=seed)
    states = []
    for g in range(games):
        orng = np.random.default_rng(seed + g // 2)
        s = dames.State.new()
        for _ in range(opening):
            moves = s.moves()
            s = s.advance(*moves[int(orng.integers(len(moves)))])
        states.append(s)
    ours = [g % 2 for g in range(games)]
    plies = 0
    while plies < 300 and any(s.status == "playing" for s in states):
        plies += 1
        mine = [g for g, s in enumerate(states) if s.status == "playing" and s.next == ours[g]]
        if mine:
            rows = np.concatenate([rules.from_state(states[g]) for g in mine])
            visits, _ = mcts.search(rows, noise=False)
            for k, g in enumerate(mine):
                moves = states[g].moves()
                by_index = {}
                for m in moves:
                    by_index.setdefault(dn.action_index(m[0], states[g].next), m)
                best = max(by_index, key=lambda i: visits[k][i])
                states[g] = states[g].advance(*by_index[best])
        for g, s in enumerate(states):
            if s.status == "playing" and s.next != ours[g]:
                states[g] = s.advance(*opponent_move(opponent, s))
    wins = draws = losses = 0
    for g, s in enumerate(states):
        if s.status == "won":
            wins += s.winner == ours[g]
            losses += s.winner != ours[g]
        else:
            draws += 1
    return {"v": int(wins), "n": int(draws), "d": int(losses), "score": round((wins + 0.5 * draws) / games, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", required=True)
    ap.add_argument("--minutes", type=float, default=60)
    ap.add_argument("--games", type=int, default=96)
    ap.add_argument("--sims", type=int, default=80)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--eval-every", type=int, default=5)
    ap.add_argument("--eval-games", type=int, default=20)
    ap.add_argument("--eval-sims", type=int, default=100)
    ap.add_argument("--eval-only", action="store_true")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "models" / "dames-zero"))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rules = DamesRules()
    blob = torch.load(a.init, map_location=device, weights_only=True)
    net = dn.build_net(blob["channels"], blob["blocks"]).to(device)
    net.load_state_dict(blob["net"])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    def duels():
        return {name: mcts_match(rules, net, name, a.eval_games, a.eval_sims, device) for name in OPPONENTS}

    if a.eval_only:
        print(json.dumps({"duels": duels()}, ensure_ascii=False))
        return
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    replay = Replay(300_000)
    rng = np.random.default_rng(a.seed)
    deadline = time.time() + a.minutes * 60
    iteration = 0

    def log(entry):
        with (out / "journal.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(json.dumps(entry, ensure_ascii=False), flush=True)

    log({"iteration": 0, "duels": duels()})
    while time.time() < deadline:
        iteration += 1
        t = time.time()
        X, PI, Z, stats = self_play(rules, net, device, games=a.games, sims=a.sims, temp_moves=16, seed=a.seed * 100000 + iteration)
        replay.add(list(X), list(PI), list(Z))
        t_play = time.time() - t
        t = time.time()
        loss = train_steps(net, opt, replay, rules, device, a.steps, a.batch, rng) if len(replay) >= a.batch else (float("nan"), float("nan"))
        entry = {"iteration": iteration, "positions": len(replay), "perte_politique": round(float(loss[0]), 4), "perte_valeur": round(float(loss[1]), 4),
                 "selfplay_s": round(t_play), "train_s": round(time.time() - t), **stats}
        if iteration % a.eval_every == 0:
            entry["duels"] = duels()
        log(entry)
        torch.save({"net": net.state_dict(), "channels": blob["channels"], "blocks": blob["blocks"], "iteration": iteration}, out / "dernier.pt")
        if iteration % a.eval_every == 0:
            torch.save({"net": net.state_dict(), "channels": blob["channels"], "blocks": blob["blocks"], "iteration": iteration}, out / f"iteration-{iteration:04d}.pt")
    print("terminé", flush=True)


if __name__ == "__main__":
    main()

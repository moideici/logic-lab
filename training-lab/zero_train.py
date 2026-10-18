"""Garry Zéro : auto-apprentissage avec recherche, sans professeur, pour Puissance 4 ou Go 9×9.

Boucle : parties contre soi-même (MCTS guidé par le réseau) -> exemples -> entraînement -> duels périodiques contre les adversaires de Garry.
Usage : python training-lab/zero_train.py --game go9 --minutes 120 [--games 128] [--sims 64] [--out training-lab/models/zero-go9]
Aucune écriture dans web/models : points de contrôle et journal dans --out (non versionné).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.zero.arena import GarryOpponent, RandomOpponent, TeacherOpponent, match  # noqa: E402
from logic_arena.zero.go import GoRules9  # noqa: E402
from logic_arena.zero.net import PolicyValueNet  # noqa: E402
from logic_arena.zero.rules import Connect4Rules  # noqa: E402
from logic_arena.zero.selfplay import Replay, self_play, train_steps  # noqa: E402

GAMES = {
    "connect4": dict(rules=Connect4Rules, game="connect4", options=None, temp_moves=10, channels=64, blocks=4, games=192, sims=100,
                     duels=[("aléatoire", lambda s: RandomOpponent(s)), ("professeur niveau 4", lambda s: TeacherOpponent(4, seed=s)),
                            ("professeur niveau 10", lambda s: TeacherOpponent(10, seed=s))]),
    "go9": dict(rules=GoRules9, game="go", options={"size": 9, "komi": 7.5}, temp_moves=24, channels=48, blocks=4, games=128, sims=64,
                duels=[("aléatoire", lambda s: RandomOpponent(s)), ("Garry niveau 1", lambda s: GarryOpponent(1, time_ms=60, seed=s)),
                       ("Garry niveau 4", lambda s: GarryOpponent(4, time_ms=100, seed=s))]),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", choices=list(GAMES), required=True)
    ap.add_argument("--minutes", type=float, default=60)
    ap.add_argument("--games", type=int)
    ap.add_argument("--sims", type=int)
    ap.add_argument("--steps", type=int, default=150)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--channels", type=int)
    ap.add_argument("--blocks", type=int)
    ap.add_argument("--eval-every", type=int, default=10)
    ap.add_argument("--eval-games", type=int, default=20)
    ap.add_argument("--out")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    cfg = GAMES[a.game]
    games, sims = a.games or cfg["games"], a.sims or cfg["sims"]
    channels, blocks = a.channels or cfg["channels"], a.blocks or cfg["blocks"]
    out = Path(a.out or Path(__file__).resolve().parent / "models" / f"zero-{a.game}")
    out.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rules = cfg["rules"]()
    torch.manual_seed(a.seed)
    net = PolicyValueNet(rules.planes_shape, rules.n_actions, channels, blocks).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    iteration = 0
    if a.resume and (out / "dernier.pt").exists():
        blob = torch.load(out / "dernier.pt", map_location=device, weights_only=True)
        net.load_state_dict(blob["net"])
        opt.load_state_dict(blob["opt"])
        iteration = blob["iteration"]
    replay = Replay(150_000)
    rng = np.random.default_rng(a.seed)
    deadline = time.time() + a.minutes * 60
    print(f"{a.game} : réseau {net.parameter_count()} paramètres ; appareil {device} ; {games} parties × {sims} simulations", flush=True)

    def log(entry):
        with (out / "journal.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(json.dumps(entry, ensure_ascii=False), flush=True)

    while time.time() < deadline:
        iteration += 1
        t = time.time()
        X, PI, Z, stats = self_play(rules, net, device, games=games, sims=sims, temp_moves=cfg["temp_moves"], seed=a.seed * 100000 + iteration)
        replay.add(list(X), list(PI), list(Z))
        t_play = time.time() - t
        t = time.time()
        loss = train_steps(net, opt, replay, rules, device, a.steps, a.batch, rng) if len(replay) >= a.batch else (float("nan"), float("nan"))
        entry = {"iteration": iteration, "positions": len(replay), "perte_politique": round(float(loss[0]), 4), "perte_valeur": round(float(loss[1]), 4),
                 "selfplay_s": round(t_play), "train_s": round(time.time() - t), **stats}
        if iteration % a.eval_every == 0:
            res = {}
            for name, factory in cfg["duels"]:
                r = match(rules, net, factory, games=a.eval_games, sims=sims * 2, device=device, game_name=cfg["game"], options=cfg["options"])
                res[name] = {"score": r["score"], "v": r["victoires"], "n": r["nuls"], "d": r["defaites"]}
            entry["duels"] = res
        log(entry)
        torch.save({"net": net.state_dict(), "opt": opt.state_dict(), "iteration": iteration, "args": vars(a), "channels": channels, "blocks": blocks}, out / "dernier.pt")
        if iteration % a.eval_every == 0:
            torch.save({"net": net.state_dict(), "iteration": iteration, "channels": channels, "blocks": blocks}, out / f"iteration-{iteration:04d}.pt")
    print("terminé", flush=True)


if __name__ == "__main__":
    main()

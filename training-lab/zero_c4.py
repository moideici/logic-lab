"""Garry Zéro sur Puissance 4 : auto-apprentissage avec recherche, sans professeur.

Boucle : parties contre soi-même (MCTS guidé par le réseau) -> exemples -> entraînement -> évaluations périodiques par duels.
Usage : python training-lab/zero_c4.py --minutes 60 [--games 192] [--sims 100] [--out training-lab/models/zero-c4]
Les points de contrôle et le journal sont écrits dans --out (non versionné). Aucune écriture dans web/models.
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
from logic_arena.zero.net import PolicyValueNet  # noqa: E402
from logic_arena.zero.rules import Connect4Rules  # noqa: E402
from logic_arena.zero.selfplay import Replay, self_play, train_steps  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=60)
    ap.add_argument("--games", type=int, default=192)
    ap.add_argument("--sims", type=int, default=100)
    ap.add_argument("--steps", type=int, default=150, help="pas d'entraînement par itération")
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--channels", type=int, default=64)
    ap.add_argument("--blocks", type=int, default=4)
    ap.add_argument("--eval-every", type=int, default=10)
    ap.add_argument("--eval-games", type=int, default=40)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "models" / "zero-c4"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rules = Connect4Rules()
    torch.manual_seed(a.seed)
    net = PolicyValueNet(rules.planes_shape, rules.n_actions, a.channels, a.blocks).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    log_path = out / "journal.jsonl"
    iteration = 0
    if a.resume and (out / "dernier.pt").exists():
        blob = torch.load(out / "dernier.pt", map_location=device, weights_only=True)
        net.load_state_dict(blob["net"])
        opt.load_state_dict(blob["opt"])
        iteration = blob["iteration"]
    replay = Replay(120_000)
    rng = np.random.default_rng(a.seed)
    deadline = time.time() + a.minutes * 60
    print(f"réseau {net.parameter_count()} paramètres ; appareil {device}", flush=True)

    def log(entry):
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(json.dumps(entry, ensure_ascii=False), flush=True)

    while time.time() < deadline:
        iteration += 1
        t = time.time()
        X, PI, Z, stats = self_play(rules, net, device, games=a.games, sims=a.sims, seed=a.seed * 100000 + iteration)
        replay.add(list(X), list(PI), list(Z))
        t_play = time.time() - t
        t = time.time()
        loss = train_steps(net, opt, replay, rules, device, a.steps if len(replay) >= a.batch else 0, a.batch, rng) if len(replay) >= a.batch else (np.nan, np.nan)
        entry = {"iteration": iteration, "positions": len(replay), "perte_politique": round(float(loss[0]), 4), "perte_valeur": round(float(loss[1]), 4),
                 "selfplay_s": round(t_play), "train_s": round(time.time() - t), **stats}
        if iteration % a.eval_every == 0:
            ev = [match(rules, net, lambda s: RandomOpponent(s), games=a.eval_games, sims=a.sims * 2, device=device),
                  match(rules, net, lambda s: TeacherOpponent(4, seed=s), games=a.eval_games, sims=a.sims * 2, device=device),
                  match(rules, net, lambda s: TeacherOpponent(10, seed=s), games=a.eval_games, sims=a.sims * 2, device=device)]
            entry["duels"] = {e["adversaire"]: e["score"] for e in ev}
        log(entry)
        torch.save({"net": net.state_dict(), "opt": opt.state_dict(), "iteration": iteration, "args": vars(a)}, out / "dernier.pt")
        if iteration % a.eval_every == 0:
            torch.save({"net": net.state_dict(), "iteration": iteration, "args": vars(a)}, out / f"iteration-{iteration:04d}.pt")
    print("terminé", flush=True)


if __name__ == "__main__":
    main()

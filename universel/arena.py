"""Duels de Garry Universel (réseau seul, sans recherche) contre le hasard ou UCT, sur n'importe quel jeu de multi via le pont Node.

Ouvertures aléatoires de 2 coups identiques pour chaque paire de parties (camps échangés). Score : victoire 1, nul 0,5, défaite 0.
Usage : python -m universel.arena --model universel/models/u1.pt --games morpion puissance-4 --opponents random uct50 --n 100"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universel import tokens as tk  # noqa: E402
from universel.bridge import Bridge  # noqa: E402
from universel.model import UniversalPlayer  # noqa: E402


def load_model(path, device):
    blob = torch.load(path, map_location=device, weights_only=True)
    model = UniversalPlayer(blob["d"], blob["layers"]).to(device)
    model.load_state_dict(blob["model"])
    return model.eval()


@torch.no_grad()
def choose(model, snap, seat, device):
    legal = snap["legal"]
    best, best_score = 0, -1e18
    for start in range(0, len(legal), tk.MAX_ACTIONS):
        chunk = legal[start:start + tk.MAX_ACTIONS]
        scores, _ = model(tk.collate([tk.encode(snap["view"], chunk, seat, 2)], device))
        i = int(scores[0, :len(chunk)].argmax())
        if float(scores[0, i]) > best_score:
            best, best_score = start + i, float(scores[0, i])
    return legal[best]


def play_match(bridge, model, game, opponent, n=100, seed=0, device="cpu", opening=2):
    wins = draws = losses = 0
    for g in range(n):
        rng = np.random.default_rng(seed + g // 2)
        snap = bridge.init(game, seed=seed + g // 2 + 1, players=2)
        for _ in range(opening):
            if snap["over"] or not snap["legal"]:
                break
            snap = bridge.apply(snap["h"], snap["active"][0], snap["legal"][int(rng.integers(len(snap["legal"])))])
        me = g % 2
        orng = np.random.default_rng(seed * 31 + g)
        plies = 0
        while not snap["over"] and snap["legal"] and plies < 500:
            seat = snap["active"][0]
            if seat == me and isinstance(model, str):  # joueur de référence « uctN » ou « random » à la place du réseau
                if model == "random":
                    action = snap["legal"][int(orng.integers(len(snap["legal"])))]
                else:
                    r = bridge.uct(snap["h"], seat, sims=int(model.replace("uct", "")), seed=int(orng.integers(1 << 30)))
                    action = r["actions"][int(np.argmax(r["visits"]))]
            elif seat == me:
                action = choose(model, snap, seat, device)
            elif opponent == "random":
                action = snap["legal"][int(orng.integers(len(snap["legal"])))]
            else:
                sims = int(opponent.replace("uct", ""))
                r = bridge.uct(snap["h"], seat, sims=sims, seed=int(orng.integers(1 << 30)))
                action = r["actions"][int(np.argmax(r["visits"]))]
            res = bridge.apply(snap["h"], seat, action)
            if not res.get("ok", True):
                break
            snap = res
            plies += 1
        out = snap["outcome"] if snap["over"] else None
        groups = out["ranking"] if out else [[0, 1]]
        if len(groups) < 2:
            draws += 1
        elif me in groups[0]:
            wins += 1
        else:
            losses += 1
    return {"victoires": wins, "nuls": draws, "defaites": losses, "score": round((wins + 0.5 * draws) / n, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--games", nargs="+", required=True)
    ap.add_argument("--opponents", nargs="+", default=["random", "uct50"])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=5000)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = load_model(a.model, device)
    with Bridge() as bridge:
        for game in a.games:
            for opp in a.opponents:
                print(json.dumps({"modele": Path(a.model).name, "jeu": game, "contre": opp, **play_match(bridge, model, game, opp, a.n, a.seed, device)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

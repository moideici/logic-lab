"""Mesure d'adaptation (protocole universel/PROTOCOLE.md, mesure 3) : sur un jeu réservé, le réseau préentraîné et le même réseau initialisé au hasard
sont ajustés avec le même budget de parties de professeur UCT, le même nombre de pas et les mêmes hyperparamètres, puis comparés en partie.

Usage : python -m universel.adapt --game moulin --budgets 100 300 1000 --pretrained universel/models/u1.pt --data universel/data/heldout.pkl
Résultats ajoutés à universel/adaptation.jsonl (une ligne par exécution)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universel.arena import play_match  # noqa: E402
from universel.bridge import Bridge  # noqa: E402
from universel.model import UniversalPlayer  # noqa: E402
from universel.train import load_encoded, train  # noqa: E402

OUT = Path(__file__).resolve().parent / "adaptation.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--budgets", type=int, nargs="+", default=[100, 300, 1000])
    ap.add_argument("--pretrained", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--eval-n", type=int, default=200)
    ap.add_argument("--device", default="auto", help="cpu pour ne pas toucher à la carte graphique")
    a = ap.parse_args()
    device = ("cuda" if torch.cuda.is_available() else "cpu") if a.device == "auto" else a.device
    torch.set_num_threads(2) if device == "cpu" else None
    encs, raw = load_encoded([a.data], [a.game])
    gids = sorted({r["gid"] for r in raw})
    blob = torch.load(a.pretrained, map_location="cpu", weights_only=True)
    done = set()  # reprise : on saute les mesures déjà écrites
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add((r["jeu"], r["parties_prof"], r["init"], r["graine"]))
    with Bridge() as bridge:
        for budget in a.budgets:
            keep = set(gids[:budget])
            sub = [e for e, r in zip(encs, raw) if r["gid"] in keep]
            for init in ("pretrained", "scratch"):
                if (a.game, budget, init, a.seed) in done:
                    continue
                torch.manual_seed(a.seed)
                model = UniversalPlayer(blob["d"], blob["layers"]).to(device)
                if init == "pretrained":
                    model.load_state_dict(blob["model"])
                agree, ce = train(model, sub, device, steps=a.steps, batch=64, lr=a.lr, seed=a.seed)
                model.eval()
                res = {"jeu": a.game, "parties_prof": budget, "exemples": len(sub), "init": init, "pas": a.steps, "graine": a.seed,
                       "accord_uct_val": round(agree, 4)}
                for opp in ("random", "uct50"):
                    res[opp] = play_match(bridge, model, a.game, opp, a.eval_n, seed=9000 + a.seed, device=device)["score"]
                with OUT.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
                print(json.dumps(res, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

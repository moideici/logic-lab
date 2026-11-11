"""Pilote P1 : trois bras à budget égal en exemples vus par jeu (un pas = 256 positions réparties également entre les jeux du réseau).
  mono   : un réseau par jeu, N/5 pas chacun
  multi  : un réseau pour les cinq jeux, N pas
  family : un réseau pour les jeux de pose (morpion, Puissance 4, Hex, Gomoku), 4N/5 pas, et un réseau de dames, N/5 pas
Usage : python training-lab/unified_train.py --arm multi --seed 0 --steps 30000 --out training-lab/models/unified/p1"""
import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.unified import training  # noqa: E402
from logic_arena.unified.spec import GAMES  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "unified"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["mono", "multi", "family"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=30000, help="N : budget total en pas à 5 jeux")
    ap.add_argument("--out", required=True)
    ap.add_argument("--channels", type=int, default=64)
    ap.add_argument("--blocks", type=int, default=6)
    ap.add_argument("--log-every", type=int, default=2000)
    a = ap.parse_args()
    out = Path(a.out) / f"{a.arm}-{a.seed}"
    out.mkdir(parents=True, exist_ok=True)
    datas = {g: training.GameData(g, DATA / f"{g}-1.npz", "cuda") for g in GAMES}
    plan = {"mono": [([g], a.steps // 5) for g in GAMES], "multi": [(list(GAMES), a.steps)],
            "family": [(["tictactoe", "connect4", "hex", "gomoku"], a.steps * 4 // 5), (["dames"], a.steps // 5)]}[a.arm]
    report = {"arm": a.arm, "seed": a.seed, "steps": a.steps, "models": []}
    t0 = time.time()
    for games, steps in plan:
        name = "+".join(games)
        if (out / f"{name}.pt").exists() and (out / f"{name}.json").exists():  # déjà terminé
            report["models"].append(json.loads((out / f"{name}.json").read_text(encoding="utf-8")))
            continue
        net, history = training.train_model(games, datas, steps, a.seed, channels=a.channels, blocks=a.blocks, label=f"{a.arm}-{a.seed}:{name}", log_every=a.log_every, ckpt=out / f"{name}.ckpt")
        torch.save({"games": games, "channels": a.channels, "blocks": a.blocks, "state": net.state_dict()}, out / f"{name}.pt")
        entry = {"games": games, "steps": steps, "params": net.parameter_count(), "final_val": history[-1]["val"], "history": history}
        (out / f"{name}.json").write_text(json.dumps(entry), encoding="utf-8")
        report["models"].append(entry)
    report["seconds"] = round(time.time() - t0)
    (out / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print("terminé", a.arm, a.seed, f"{report['seconds']}s")


if __name__ == "__main__":
    main()

"""Mesure d'un bras du pilote par les juges indépendants (réseau seul, sans recherche).
Usage : python training-lab/unified_eval.py --dir training-lab/models/unified/p1/multi-0 [--scale 1.0]"""
import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.unified import judge  # noqa: E402
from logic_arena.unified.model import UnifiedNet  # noqa: E402
from logic_arena.unified.policy import NetPolicy  # noqa: E402


def load_nets(folder):
    nets = {}
    for path in sorted(Path(folder).glob("*.pt")):
        blob = torch.load(path, map_location="cpu", weights_only=True)
        net = UnifiedNet(blob["games"], blob["channels"], blob["blocks"])
        net.load_state_dict(blob["state"])
        for g in blob["games"]:
            nets[g] = net
    return nets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--scale", type=float, default=1.0, help="multiplie le nombre de parties")
    a = ap.parse_args()
    policy = NetPolicy(load_nets(a.dir))
    n = lambda k: max(2, int(k * a.scale))
    res = {}
    with judge.JsEngine() as engine:
        for game, fn in (("tictactoe", lambda: judge.judge_tictactoe(policy, n(40))),
                         ("hex", lambda: judge.judge_engine_match("hex", policy, n(30), 100, engine=engine)),
                         ("gomoku", lambda: judge.judge_engine_match("gomoku", policy, n(30), 100, engine=engine)),
                         ("dames", lambda: {"normal": judge.judge_dames(policy, n(30), "normal"), "difficile": judge.judge_dames(policy, n(20), "difficile")}),
                         ("connect4", lambda: judge.judge_connect4(policy, n(24)))):
            t = time.time()
            res[game] = fn()
            print(a.dir, game, f"{time.time() - t:.0f}s", json.dumps(res[game])[:160], flush=True)
    (Path(a.dir) / "judges.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

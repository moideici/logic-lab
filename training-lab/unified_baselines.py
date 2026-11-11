"""Base de mesures figée du modèle unique (P0) : joueur au hasard et professeurs (plafond) contre les juges indépendants, cinq jeux.
Usage : python training-lab/unified_baselines.py --out ../../outputs/verifications/baselines-unifie-2026-11-09.json [--games 20] [--quick]
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.unified import judge  # noqa: E402
from logic_arena.unified.adapters import make_adapter  # noqa: E402


def teacher_policies(engine):
    from logic_arena.zero import c4, c4perfect, dames

    def c4_player(obs, legal):
        pos, mask = c4.from_board(obs["board"], obs["current_player"])
        return {"column": int(c4perfect.choose(pos, mask))}

    def ttt_player(obs, legal):
        b, p = tuple(v for row in obs["board"] for v in row), obs["current_player"]
        return max(legal, key=lambda a: -judge._ttt_value(b[:a["row"] * 3 + a["col"]] + (p,) + b[a["row"] * 3 + a["col"] + 1:], 3 - p))

    def dames_player(obs, legal):
        return dames.search(obs["cells"], obs["next"], obs["quiet"], 6, 100000, 1)[0]

    return {"tictactoe": ttt_player, "connect4": c4_player, "dames": dames_player,
            "gomoku": lambda obs, legal: engine.choose(obs, legal, 100), "hex": lambda obs, legal: engine.choose(obs, legal, 100)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    n = 4 if a.quick else a.games
    out = {"date": "2026-11-09", "games_per_cell": n, "players": {}}
    with judge.JsEngine() as engine:
        teachers = teacher_policies(engine)
        for name in ("random", "teacher"):
            res = {}
            for game in ("tictactoe", "connect4", "hex", "gomoku", "dames"):
                t = time.time()
                policy = judge.random_policy(0) if name == "random" else teachers[game]
                if game == "tictactoe":
                    res[game] = judge.judge_tictactoe(policy, 20 if not a.quick else 6)
                elif game == "connect4":
                    res[game] = judge.judge_connect4(policy, n)
                elif game == "dames":
                    res[game] = {lv: judge.judge_dames(policy, n, lv) for lv in (("normal",) if a.quick else ("normal", "difficile"))}
                else:
                    res[game] = judge.judge_engine_match(game, policy, n, 100, engine=engine)
                print(name, game, "%.0fs" % (time.time() - t), json.dumps(res[game])[:200], flush=True)
            out["players"][name] = res
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

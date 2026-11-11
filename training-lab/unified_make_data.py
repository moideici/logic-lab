"""Génère les jeux de données unifiés (un .npz par jeu) dans training-lab/data/unified/.
Usage : python training-lab/unified_make_data.py [--hex-games 1200] [--gomoku-games 1200] [--workers 14] [--dames-limit 0] [--only hex,gomoku]
Gomoku et Hex : auto-parties du moteur à la main (JS), valeur = résultat réel ; les autres jeux viennent des étiquettes exactes ou de recherche déjà calculées."""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.unified import teachers  # noqa: E402

OUT = Path(__file__).resolve().parent / "data" / "unified"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hex-games", type=int, default=1200)
    ap.add_argument("--gomoku-games", type=int, default=1200)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--dames-limit", type=int, default=0, help="0 = toutes les étiquettes")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--only", default="tictactoe,connect4,dames,hex,gomoku")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    todo = a.only.split(",")
    jobs = {
        "tictactoe": lambda: teachers.ttt_records(),
        "connect4": lambda: teachers.c4_records(),
        "dames": lambda: teachers.dames_records(limit=a.dames_limit or None),
        "hex": lambda: teachers.js_records("hex", max(1, a.hex_games // a.workers), a.workers, a.seed),
        "gomoku": lambda: teachers.js_records("gomoku", max(1, a.gomoku_games // a.workers), a.workers, a.seed),
    }
    for game in todo:
        t = time.time()
        rec = jobs[game]()
        rec.save(OUT / f"{game}-{a.seed}.npz")
        print(f"{game}: {len(rec)} positions en {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()

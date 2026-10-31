"""Inventaire des jeux de multi vus par le pont : joueurs, coups légaux disponibles, bot, vitesse d'une partie au hasard, taille des vues et des coups."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universel.bridge import Bridge  # noqa: E402

rows = []
with Bridge() as b:
    games = b.games()
    for gid, info in games.items():
        t = time.time()
        try:
            res = [b.playout(gid, seed=s, record=True, kinds=["bot"] * 8) for s in range(1, 6)]
        except Exception as e:
            rows.append({"jeu": gid, "erreur": str(e)[:80]})
            continue
        dt = time.time() - t
        plies = sum(r["plies"] for r in res)
        sample = res[0]["trace"][0] if res[0]["trace"] else None
        rows.append({"jeu": gid, "joueurs": f"{info['minPlayers']}-{info['maxPlayers']}", "legal": info["hasLegal"], "bot": info["hasBot"],
                     "demi_coups_par_s": round(plies / dt) if dt else None, "plies_moy": round(plies / 5, 1),
                     "vue_octets": len(json.dumps(sample["view"])) if sample else None, "coups_moy": round(sum(len(x["legal"] or []) for r in res for x in r["trace"]) / max(plies, 1), 1),
                     "fin": all(r["outcome"] is not None for r in res)})
for r in rows:
    print(json.dumps(r, ensure_ascii=False))

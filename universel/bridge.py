"""Client Python du pont Node vers les moteurs de multi (voir bridge.mjs)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


class Bridge:
    def __init__(self, multi_dir=r"C:\Users\gabor\code\multi"):
        self.proc = subprocess.Popen(["node", str(HERE / "bridge.mjs"), multi_dir], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
        self._id = 0

    def call(self, op, **kw):
        self._id += 1
        self.proc.stdin.write(json.dumps({"op": op, "id": self._id, **kw}, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("pont Node arrêté : " + self.proc.stderr.read()[:500])
        out = json.loads(line)
        if "error" in out:
            raise RuntimeError(out["error"])
        return out

    def games(self):
        out = self.call("games")
        out.pop("id", None)
        return out

    def init(self, game, seed=1, players=None, options=None, seat=None):
        return self.call("init", game=game, seed=seed, players=players, options=options, seat=seat)

    def view(self, h, seat=None):
        return self.call("view", h=h, seat=seat)

    def apply(self, h, seat, action, next_seat=None):
        return self.call("apply", h=h, seat=seat, action=action, next_seat=next_seat)

    def bot(self, h, seat, seed=7):
        return self.call("bot", h=h, seat=seat, seed=seed)["action"]

    def uct(self, h, seat, sims=200, seed=11, c=1.4):
        return self.call("uct", h=h, seat=seat, sims=sims, seed=seed, c=c)

    def free(self, hs):
        return self.call("free", hs=list(hs))

    def playout(self, game, seed=1, players=None, kinds=None, record=False, options=None, max_plies=400):
        return self.call("playout", game=game, seed=seed, players=players, kinds=kinds, record=record, options=options, maxPlies=max_plies)

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.terminate()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

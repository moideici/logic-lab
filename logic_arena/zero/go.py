"""Go 9×9 pour Garry Zéro : moteur C++ (compilé à la demande par g++) appelé par ctypes, et règles au format de `rules.py`."""
from __future__ import annotations

import ctypes
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "go9.cpp"
LIB = HERE / "go9.dll"
N, NN, W = 9, 81, 86
_lib = None


def _compiler():
    import shutil
    return shutil.which("g++") or r"C:\Users\gabor\scoop\apps\mingw\current\bin\g++.exe"


def library():
    """Charge (et compile si besoin) le moteur de Go."""
    global _lib
    if _lib is None:
        if not LIB.exists() or LIB.stat().st_mtime < SOURCE.stat().st_mtime:
            r = subprocess.run([_compiler(), "-O2", "-shared", "-o", str(LIB), str(SOURCE)], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError("compilation du moteur de Go impossible : " + r.stderr[:400])
        lib = ctypes.CDLL(str(LIB))
        lib.go9_initial.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.go9_legal.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        lib.go9_step.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        lib.go9_margin.argtypes = [ctypes.c_void_p]
        lib.go9_margin.restype = ctypes.c_float
        _lib = lib
    return _lib


def _ptr(a):
    return a.ctypes.data_as(ctypes.c_void_p)


def margin(state):
    """Noir − blanc − komi sur la position (surface, sans retrait de pierres mortes)."""
    s = np.ascontiguousarray(state, dtype=np.uint8)
    return float(library().go9_margin(_ptr(s)))


_SYMMETRIES = None


def _symmetries():
    global _SYMMETRIES
    if _SYMMETRIES is None:
        idx = np.arange(NN).reshape(N, N)
        maps = []
        for k in range(4):
            for flip in (False, True):
                m = np.rot90(idx, k)
                maps.append((np.fliplr(m) if flip else m).reshape(-1))
        _SYMMETRIES = maps
    return _SYMMETRIES


class GoRules9:
    name = "go9"
    n_actions = 82
    planes_shape = (4, 9, 9)
    max_moves = 160
    dtype = np.uint8
    width = W

    def __init__(self, seed=0):
        library()
        self.rng = np.random.default_rng(seed)

    def initial(self, n):
        st = np.zeros((n, W), dtype=np.uint8)
        library().go9_initial(_ptr(st), n)
        return st

    def legal(self, states):
        s = np.ascontiguousarray(states, dtype=np.uint8)
        out = np.zeros((len(s), 82), dtype=np.uint8)
        library().go9_legal(_ptr(s), len(s), _ptr(out))
        return out.astype(bool)

    def step(self, states, actions):
        s = np.ascontiguousarray(states, dtype=np.uint8).copy()
        a = np.ascontiguousarray(actions, dtype=np.int32)
        terminal = np.zeros(len(s), dtype=np.uint8)
        value = np.zeros(len(s), dtype=np.float32)
        library().go9_step(_ptr(s), _ptr(a), len(s), _ptr(terminal), _ptr(value))
        return s, terminal.astype(bool), value

    def encode(self, states):
        board = states[:, :NN].reshape(-1, N, N)
        mover = states[:, 81][:, None, None]
        own = (board == mover).astype(np.float32)
        opp = ((board != 0) & (board != mover)).astype(np.float32)
        last = np.zeros((len(states), NN), dtype=np.float32)
        have = states[:, 85] < NN
        last[np.flatnonzero(have), states[have, 85]] = 1.0
        color = np.broadcast_to((states[:, 81] == 1).astype(np.float32)[:, None, None], (len(states), N, N))
        return np.stack([own, opp, last.reshape(-1, N, N), color], axis=1)

    def mirror(self, x, pi):
        """Une des 8 symétries du plateau, appliquée à l'entrée (4,9,9) et à la politique (82)."""
        m = _symmetries()[int(self.rng.integers(8))]
        x2 = x.reshape(x.shape[0], NN)[:, m].reshape(x.shape)
        p2 = np.concatenate([pi[:NN][m], pi[NN:]])
        return x2.copy(), p2.copy()

    def from_observation(self, obs):
        board = obs["board"]
        st = np.zeros((1, W), dtype=np.uint8)
        for r in range(N):
            for c in range(N):
                st[0, r * N + c] = board[r][c]
        st[0, 81] = obs["current_player"]
        st[0, 82] = 255
        st[0, 83] = obs["go_state"]["passes"]
        st[0, 84] = min(255, len(obs["go_state"]["seen"]) - 1)
        st[0, 85] = 255
        return st

    def action_to_garry(self, action):
        return {"pass": True} if action == 81 else {"row": int(action) // N, "col": int(action) % N}

    def garry_index(self, a):
        """Indice d'action de Zéro pour une action de Garry ; None si elle n'existe pas pour Zéro (abandon, marquage des morts...)."""
        if a.get("pass"):
            return 81
        return a["row"] * N + a["col"] if "row" in a else None

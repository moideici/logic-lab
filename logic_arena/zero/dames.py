"""Dames de multi pour Garry : génération des coups en C++ (ctypes) et règles de partie identiques au moteur TypeScript (`dames/index.ts`)."""
from __future__ import annotations

import ctypes
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "dames.cpp"
LIB = HERE / "dames.dll"
_lib = None
REC = 72


def library():
    global _lib
    if _lib is None:
        if not LIB.exists() or LIB.stat().st_mtime < SOURCE.stat().st_mtime:
            cxx = shutil.which("g++") or r"C:\Users\gabor\scoop\apps\mingw\current\bin\g++.exe"
            r = subprocess.run([cxx, "-O2", "-static", "-shared", "-o", str(LIB), str(SOURCE)], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError("compilation des dames impossible : " + r.stderr[:400])
        lib = ctypes.CDLL(str(LIB))
        lib.dames_moves.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        lib.dames_moves.restype = ctypes.c_int
        _lib = lib
    return _lib


def owner(piece):
    return -1 if piece == 0 else (0 if piece <= 2 else 1)


def is_king(piece):
    return piece in (2, 4)


def crown(piece, cell):
    return 2 if piece == 1 and cell < 8 else 4 if piece == 3 and cell >= 56 else piece


def initial_cells():
    return [0 if (i // 8 + i % 8) % 2 == 0 else (3 if i < 24 else 1 if i >= 40 else 0) for i in range(64)]


def legal_moves(cells, seat):
    """Coups légaux sous forme (chemin, prises), dans l'ordre du moteur C++."""
    buf = np.zeros(256 * REC, dtype=np.int8)
    arr = np.asarray(cells, dtype=np.int8)
    n = library().dames_moves(arr.ctypes.data_as(ctypes.c_void_p), int(seat), buf.ctypes.data_as(ctypes.c_void_p))
    out = []
    for i in range(n):
        rec = buf[i * REC:(i + 1) * REC]
        plen, ncaps = int(rec[0]), int(rec[1])
        out.append((tuple(int(x) for x in rec[2:2 + plen]), tuple(int(x) for x in rec[35:35 + ncaps])))
    return out


def moved(cells, path, captures):
    result = list(cells)
    piece = result[path[0]]
    result[path[0]] = 0
    for cell in path[1:]:
        piece = crown(piece, cell)
    for cell in captures:
        result[cell] = 0
    result[path[-1]] = piece
    return result


def position_key(cells, nxt):
    return (nxt, tuple(cells[r * 8 + c] for r in range(8) for c in range(8) if (r + c) % 2))


@dataclass
class State:
    cells: list
    next: int = 0
    quiet: int = 0
    status: str = "playing"
    winner: int | None = None
    repeats: dict = field(default_factory=dict)

    @staticmethod
    def new():
        cells = initial_cells()
        return State(cells, 0, 0, "playing", None, {position_key(cells, 0): 1})

    def moves(self):
        return legal_moves(self.cells, self.next) if self.status == "playing" else []

    def advance(self, path, captures):
        cells = moved(self.cells, path, captures)
        nxt = 1 - self.next
        quiet = 0 if captures or not is_king(self.cells[path[0]]) else self.quiet + 1
        repeats = {} if quiet == 0 else dict(self.repeats)
        key = position_key(cells, nxt)
        repeats[key] = repeats.get(key, 0) + 1
        lost = not any(owner(p) == nxt for p in cells) or not legal_moves(cells, nxt)
        status = "won" if lost else "draw" if quiet >= 20 or repeats[key] >= 3 else "playing"
        return State(cells, nxt, quiet, status, self.next if lost else None, repeats)


def _bind_search():
    lib = library()
    if not getattr(lib, "_search_bound", False):
        lib.dames_search.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_int, ctypes.c_void_p]
        lib.dames_search.restype = ctypes.c_int
        lib._search_bound = True
    return lib


def search(cells, seat, quiet=0, depth=7, budget=20000, mode=0):
    """Meilleur coup (chemin, prises) et score. mode 0 : bot de multi (profondeur et budget donnés) ; mode 1 : recherche renforcée."""
    lib = _bind_search()
    arr = np.asarray(cells, dtype=np.int8)
    score = ctypes.c_int(0)
    i = lib.dames_search(arr.ctypes.data_as(ctypes.c_void_p), int(seat), int(quiet), int(depth), int(budget), int(mode), ctypes.byref(score))
    if i < 0:
        return None, 0
    return legal_moves(cells, seat)[i], score.value


def scores(cells, seat, quiet=0, depth=6, budget=2_000_000, mode=1):
    """Score (point de vue de `seat`) de chaque coup légal, dans l'ordre de `legal_moves`."""
    lib = library()
    if not getattr(lib, "_scores_bound", False):
        lib.dames_scores.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_int, ctypes.c_void_p]
        lib.dames_scores.restype = ctypes.c_int
        lib._scores_bound = True
    arr = np.asarray(cells, dtype=np.int8)
    out = np.zeros(256, dtype=np.int32)
    n = lib.dames_scores(arr.ctypes.data_as(ctypes.c_void_p), int(seat), int(quiet), int(depth), int(budget), int(mode), out.ctypes.data_as(ctypes.c_void_p))
    return out[:n].copy()

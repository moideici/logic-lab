"""2048 pour Garry Optimus : professeur expectimax C++ (compilé à la demande par g++, appelé par ctypes). Pas de limite à 2048.
Grille = entier 64 bits, un quartet par case (log2 de la tuile), ligne r = bits 16r.., colonne c = bits 4c.
Coups : 0 haut, 1 bas, 2 gauche, 3 droite."""
from __future__ import annotations

import ctypes
import os
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE, LIB = HERE / "t2048.cpp", HERE / "t2048.dll"
DIRECTIONS = ("up", "down", "left", "right")
_lib = None


def library():
    global _lib
    if _lib is None:
        if not LIB.exists() or LIB.stat().st_mtime < SOURCE.stat().st_mtime:
            import shutil
            cxx = shutil.which("g++") or r"C:\Users\gabor\scoop\apps\mingw\current\bin\g++.exe"
            r = subprocess.run([cxx, "-O3", "-march=x86-64-v2", "-static", "-shared", "-o", str(LIB), str(SOURCE)], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError("compilation de t2048 impossible : " + r.stderr[:500])
        lib = ctypes.CDLL(str(LIB))
        lib.t_values.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        lib.t_step.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        lib.t_new.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        lib.t_legal_batch.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        lib.t_move.argtypes = [ctypes.c_uint64, ctypes.c_int]
        lib.t_move.restype = ctypes.c_uint64
        lib.t_legal_mask.argtypes = [ctypes.c_uint64]
        lib.t_legal_mask.restype = ctypes.c_int
        _lib = lib
    return _lib


def pack(board) -> int:
    """Grille 4×4 de tuiles (0, 2, 4, …) → entier 64 bits."""
    b = 0
    for r in range(4):
        for c in range(4):
            v = int(board[r][c])
            b |= (v.bit_length() - 1 if v else 0) << (4 * (r * 4 + c))
    return b


def exponents(boards) -> np.ndarray:
    """uint64 (N,) → exposants (N, 4, 4) uint8."""
    b = np.asarray(boards, dtype=np.uint64)
    shifts = np.arange(16, dtype=np.uint64) * np.uint64(4)
    return ((b[:, None] >> shifts) & np.uint64(15)).reshape(-1, 4, 4).astype(np.uint8)


def pack_exponents(e) -> np.ndarray:
    e = np.asarray(e, dtype=np.uint64).reshape(-1, 16)
    return (e << (np.arange(16, dtype=np.uint64) * np.uint64(4))).sum(axis=1, dtype=np.uint64)


def values(boards, depth=3, threads=None) -> np.ndarray:
    """Valeurs expectimax des 4 coups (−1e30 si illégal), forme (N, 4)."""
    b = np.ascontiguousarray(boards, dtype=np.uint64)
    out = np.empty((len(b), 4), dtype=np.float32)
    library().t_values(b.ctypes.data, len(b), int(depth), out.ctypes.data, threads or max(1, (os.cpu_count() or 4) - 2))
    return out


def step(boards, dirs, seeds) -> np.ndarray:
    """Un coup par grille puis une tuile qui apparaît. `seeds` (uint64) est modifié en place. Renvoie les nouvelles grilles."""
    b = np.ascontiguousarray(boards, dtype=np.uint64)
    d = np.ascontiguousarray(dirs, dtype=np.int32)
    assert seeds.dtype == np.uint64 and seeds.flags.c_contiguous and len(seeds) == len(b)
    out = np.empty_like(b)
    library().t_step(b.ctypes.data, d.ctypes.data, len(b), seeds.ctypes.data, out.ctypes.data)
    return out


def new_boards(n, seeds) -> np.ndarray:
    """N grilles de départ (deux tuiles). `seeds` (uint64) est modifié en place."""
    out = np.zeros(n, dtype=np.uint64)
    library().t_new(n, seeds.ctypes.data, out.ctypes.data)
    return out


def legal_mask(board: int) -> int:
    return library().t_legal_mask(board)


def move(board: int, direction: int) -> int:
    return int(library().t_move(board, direction))


def legal_masks(boards) -> np.ndarray:
    """Masque de coups légaux (bits 0 à 3 = haut, bas, gauche, droite) pour chaque grille."""
    b = np.ascontiguousarray(boards, dtype=np.uint64)
    out = np.empty(len(b), dtype=np.int32)
    library().t_legal_batch(b.ctypes.data, len(b), out.ctypes.data)
    return out

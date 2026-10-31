"""Solveur exact de Puissance 4 : oracle de jeu parfait pour Garry (compilé à la demande par g++, appelé par ctypes)."""
from __future__ import annotations

import ctypes
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "c4solver.cpp"
LIB = HERE / "c4solver.dll"
_lib = None


def library():
    global _lib
    if _lib is None:
        if not LIB.exists() or LIB.stat().st_mtime < SOURCE.stat().st_mtime:
            import shutil
            cxx = shutil.which("g++") or r"C:\Users\gabor\scoop\apps\mingw\current\bin\g++.exe"
            r = subprocess.run([cxx, "-O3", "-march=x86-64-v2", "-static", "-shared", "-o", str(LIB), str(SOURCE)], capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError("compilation du solveur impossible : " + r.stderr[:400])
        lib = ctypes.CDLL(str(LIB))
        lib.c4s_solve.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int]
        lib.c4s_solve.restype = ctypes.c_int
        lib.c4s_scores.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int, ctypes.c_void_p]
        lib.c4s_nodes.restype = ctypes.c_longlong
        _lib = lib
    return _lib


def reset():
    library().c4s_reset()


def nodes():
    return int(library().c4s_nodes())


def solve(pos, mask, weak=False):
    """Score exact (ou seulement le signe si `weak`) pour le joueur au trait. Convention de Pons : > 0 gain, < 0 perte, 0 nul."""
    return int(library().c4s_solve(int(pos), int(mask), 1 if weak else 0))


def scores(pos, mask, weak=False):
    """Score de chacune des 7 colonnes (point de vue du joueur au trait) ; -1000 si la colonne est pleine."""
    out = np.zeros(7, dtype=np.int32)
    library().c4s_scores(int(pos), int(mask), 1 if weak else 0, out.ctypes.data_as(ctypes.c_void_p))
    return out


def tactical(pos, mask, depth=10):
    """Verdict par colonne d'une recherche à profondeur limitée : 1 gain forcé, -1 perte forcée, 0 inconnu ; -1000 si la colonne est pleine."""
    out = np.zeros(7, dtype=np.int32)
    lib = library()
    lib.c4s_tactical.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int, ctypes.c_void_p]
    lib.c4s_tactical(int(pos), int(mask), int(depth), out.ctypes.data_as(ctypes.c_void_p))
    return out


def optimal_columns(pos, mask, weak=True):
    """Colonnes qui préservent le meilleur résultat théorique (gain si possible, sinon nul, sinon la défaite la plus longue si pas `weak`)."""
    s = scores(pos, mask, weak)
    best = s.max()
    if weak:
        outcome = np.sign(s)
        best = outcome.max()
        return [c for c in range(7) if s[c] != -1000 and outcome[c] == best]
    return [c for c in range(7) if s[c] == best]

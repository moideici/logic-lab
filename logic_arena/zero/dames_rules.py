"""Dames de multi au format de jeu de Garry Zéro (`rules.py`) : états par lots (n, 66) int8 = 64 cases, joueur au trait, compteur de coups de dame sans prise."""
from __future__ import annotations

import ctypes

import numpy as np

from . import dames, dames_net


def _bind():
    lib = dames.library()
    if not getattr(lib, "_batch_bound", False):
        lib.dames_legal_batch.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        lib.dames_step_batch.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        lib._batch_bound = True
    return lib


class DamesRules:
    name = "dames"
    n_actions = dames_net.N_ACTIONS
    planes_shape = dames_net.PLANES
    max_moves = 160  # au-delà, la partie est adjugée nulle
    dtype = np.int8
    width = 66

    def initial(self, n):
        row = np.zeros(66, dtype=np.int8)
        row[:64] = dames.initial_cells()
        return np.tile(row, (n, 1))

    def legal(self, states):
        lib = _bind()
        states = np.ascontiguousarray(states, dtype=np.int8)
        mask = np.zeros((len(states), 1024), dtype=np.uint8)
        lib.dames_legal_batch(states.ctypes.data_as(ctypes.c_void_p), len(states), mask.ctypes.data_as(ctypes.c_void_p))
        return mask.astype(bool)

    def step(self, states, actions):
        lib = _bind()
        states = np.ascontiguousarray(states, dtype=np.int8)
        acts = np.ascontiguousarray(actions, dtype=np.int32)
        out = np.zeros_like(states)
        term = np.zeros(len(states), dtype=np.uint8)
        value = np.zeros(len(states), dtype=np.float32)
        lib.dames_step_batch(states.ctypes.data_as(ctypes.c_void_p), acts.ctypes.data_as(ctypes.c_void_p), len(states),
                             out.ctypes.data_as(ctypes.c_void_p), term.ctypes.data_as(ctypes.c_void_p), value.ctypes.data_as(ctypes.c_void_p))
        return out, term.astype(bool), value

    def encode(self, states):
        states = np.asarray(states)
        cells = states[:, :64].astype(np.int8)
        flip = states[:, 64] == 1
        rotated = dames_net._SWAP[cells[:, ::-1]]
        cells = np.where(flip[:, None], rotated, cells).reshape(-1, 8, 8)
        planes = np.zeros((len(states), *self.planes_shape), dtype=np.float32)
        for k, piece in enumerate((1, 2, 3, 4)):
            planes[:, k] = cells == piece
        planes[:, 4] = (np.minimum(states[:, 65], 20) / 20.0)[:, None, None]
        return planes

    def from_state(self, state):
        """Ligne (1, 66) à partir d'un `dames.State`."""
        row = np.zeros((1, 66), dtype=np.int8)
        row[0, :64] = state.cells
        row[0, 64] = state.next
        row[0, 65] = min(state.quiet, 100)
        return row

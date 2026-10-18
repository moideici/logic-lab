"""Interface commune des jeux pour Garry Zéro, et son implémentation pour Puissance 4.

Un jeu travaille sur des lots d'états : tableau numpy (n, W) de type fixe. Les méthodes sont vectorisées et sans état interne.
  initial(n)          -> (n, W) états de départ
  legal(states)       -> (n, A) booléen, actions légales
  step(states, acts)  -> (nouveaux états, terminal (n,), valeur (n,)) ; la valeur est du point de vue du joueur au trait dans le
                         NOUVEL état (−1 s'il vient de perdre, 0 nul) et n'a de sens que là où `terminal` est vrai
  encode(states)      -> (n, C, H, W) float32 : entrée du réseau, toujours du point de vue du joueur au trait
  mirror(x, pi)       -> augmentation de symétrie (x, pi) ou None
"""
from __future__ import annotations

import numpy as np

from . import c4


class Connect4Rules:
    name = "connect4"
    n_actions = 7
    planes_shape = (2, 6, 7)
    max_moves = 42
    dtype = np.uint64
    width = 2  # (pos, mask)

    def initial(self, n):
        return np.zeros((n, 2), dtype=np.uint64)

    def legal(self, states):
        return c4.legal(states[:, 1])

    def step(self, states, actions):
        pos, mask, won = c4.play(states[:, 0], states[:, 1], actions)
        new = np.stack([pos, mask], axis=1)
        draw = (~won) & (c4.legal(mask).sum(1) == 0)  # plateau plein sans alignement
        terminal = won | draw
        value = np.where(won, -1.0, 0.0).astype(np.float32)
        return new, terminal, value

    def encode(self, states):
        return c4.planes(states[:, 0], states[:, 1])

    def mirror(self, x, pi):
        return x[..., ::-1].copy(), pi[..., ::-1].copy()

    def from_observation(self, obs):
        pos, mask = c4.from_board(obs["board"], obs["current_player"])
        return np.array([[pos, mask]], dtype=np.uint64)

    def action_to_garry(self, action):
        return {"column": int(action)}

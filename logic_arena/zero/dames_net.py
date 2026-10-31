"""Réseau de dames pour Garry : encodage (toujours du point de vue du joueur au trait), indice de coup (case de départ, case d'arrivée) et joueur réseau."""
from __future__ import annotations

import numpy as np

from .net import PolicyValueNet

DARK = [i for i in range(64) if (i // 8 + i % 8) % 2 == 1]
SQ32 = np.full(64, -1, dtype=np.int16)
for k, cell in enumerate(DARK):
    SQ32[cell] = k
N_ACTIONS = 1024
PLANES = (5, 8, 8)
_SWAP = np.array([0, 3, 4, 1, 2], dtype=np.int8)


def canonical(cells, nxt):
    """Plateau vu du point de vue du joueur au trait : pour le joueur 1 on tourne de 180 degrés et on échange les camps."""
    cells = np.asarray(cells, dtype=np.int8)
    if nxt == 1:
        cells = _SWAP[cells[::-1]]
    return cells


def encode(cells, nxt, quiet):
    """(5, 8, 8) : pions à moi, dames à moi, pions adverses, dames adverses, compteur de coups de dame sans prise."""
    c = canonical(cells, nxt).reshape(8, 8)
    planes = np.zeros(PLANES, dtype=np.float32)
    for k, piece in enumerate((1, 2, 3, 4)):
        planes[k] = (c == piece)
    planes[4] = min(quiet, 20) / 20.0
    return planes


def action_index(path, nxt):
    a, b = path[0], path[-1]
    if nxt == 1:
        a, b = 63 - a, 63 - b
    return int(SQ32[a]) * 32 + int(SQ32[b])


def build_net(channels=64, blocks=6):
    return PolicyValueNet(PLANES, N_ACTIONS, channels, blocks)


class NetPlayer:
    """Joue le coup légal dont l'indice a la plus forte probabilité selon le réseau (sans recherche)."""

    def __init__(self, net, device="cpu"):
        import torch
        self.torch, self.net, self.device = torch, net.to(device).eval(), device

    def policy(self, state, moves):
        torch = self.torch
        x = torch.tensor(encode(state.cells, state.next, state.quiet))[None].to(self.device)
        with torch.no_grad():
            logits, value = self.net(x)
        idx = [action_index(m[0], state.next) for m in moves]
        return logits[0, idx].cpu().numpy(), float(value[0])

    def choose(self, state):
        moves = state.moves()
        logits, _ = self.policy(state, moves)
        return moves[int(np.argmax(logits))]

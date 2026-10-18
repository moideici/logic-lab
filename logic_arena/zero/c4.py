"""Puissance 4 vectorisé (numpy, bitboards) pour des milliers de parties en parallèle.

Représentation par partie : `pos` = pierres du joueur au trait, `mask` = toutes les pierres. Bit d'une case : colonne * 7 + rangée
(rangée 0 = en bas, la 7e rangée est une sentinelle toujours vide). Après un coup, `pos` devient l'ensemble des pierres de l'adversaire
(celui qui est maintenant au trait) : la position est toujours vue du point de vue du joueur au trait.
"""
from __future__ import annotations

import numpy as np

ROWS, COLS = 6, 7
U = np.uint64
BOTTOM = np.array([1 << (c * 7) for c in range(COLS)], dtype=U)
TOP = np.array([1 << (c * 7 + ROWS - 1) for c in range(COLS)], dtype=U)
FULL_MASK = U(sum(((1 << ROWS) - 1) << (c * 7) for c in range(COLS)))
_BIT = np.array([[1 << (c * 7 + r) for c in range(COLS)] for r in range(ROWS)], dtype=U)  # (rangée, colonne)


def new_games(count):
    return np.zeros(count, dtype=U), np.zeros(count, dtype=U)


def legal(mask):
    """(G, 7) booléen : colonnes non pleines."""
    return (mask[:, None] & TOP[None, :]) == 0


def has_won(x):
    """Le bitboard `x` contient-il quatre pierres alignées ? (vectorisé)"""
    x = x.astype(U, copy=False)
    out = np.zeros(x.shape, dtype=bool)
    for shift in (U(1), U(7), U(6), U(8)):
        pairs = x & (x >> shift)
        out |= (pairs & (pairs >> (shift * U(2)))) != 0
    return out


def play(pos, mask, cols):
    """Joue la colonne `cols[g]` dans chaque partie (coup supposé légal). Retourne (nouveau_pos, nouveau_mask, a_gagné).

    Le nouveau `pos` est du point de vue du joueur qui est maintenant au trait (l'adversaire de celui qui vient de jouer).
    """
    cols = np.asarray(cols)
    new_mask = mask | (mask + BOTTOM[cols])
    mover = pos | (new_mask ^ mask)
    won = has_won(mover)
    return mover ^ new_mask, new_mask, won


def planes(pos, mask):
    """Entrée du réseau : (G, 2, 6, 7), plan 0 = pierres du joueur au trait, plan 1 = pierres de l'adversaire. Rangée 0 = haut du plateau."""
    own = ((pos[:, None, None] & _BIT[None, ::-1, :]) != 0).astype(np.float32)
    other = (((mask ^ pos)[:, None, None] & _BIT[None, ::-1, :]) != 0).astype(np.float32)
    return np.stack([own, other], axis=1)


def move_count(mask):
    return np.array([bin(int(m)).count("1") for m in mask])


def from_board(board, current_player):
    """Bitboards (pos, mask) à partir de `obs['board']` de Garry (6×7, rangée 0 en haut, joueurs 1 et 2) et du joueur au trait."""
    pos = mask = 0
    for r in range(ROWS):
        for c in range(COLS):
            v = board[r][c]
            if v:
                bit = 1 << (c * 7 + (ROWS - 1 - r))
                mask |= bit
                if v == current_player:
                    pos |= bit
    return U(pos), U(mask)

"""Encodage commun des cinq jeux : observation → (plans, annexe), action → indice. Toujours du point de vue du joueur au trait."""
from __future__ import annotations

import numpy as np

from .spec import CANVAS, CHOOSE_BLACK, CHOOSE_WHITE, DIMS, EXTRA, GAME_ID, N_ACTIONS, PLANES, SWAP

PHASES = ("opening_three", "choose_or_extend", "opening_two", "choose_color", "play")


def _offset(game):
    h, w = DIMS[game]
    return (CANVAS - h) // 2, (CANVAS - w) // 2


def _cell(game, r, c):
    oy, ox = _offset(game)
    return (r + oy) * CANVAS + c + ox


def _own_color(obs):
    p = obs["current_player"]
    if obs["game"] == "hex":
        return obs["hex_state"]["colors"][p - 1]
    if obs["game"] == "gomoku":
        s = obs["gomoku_state"]
        return s["colors"][p - 1] if s["phase"] == "play" else 1 if s["placed"] % 2 == 0 else 2
    return p


def _landing_row(board, column):
    return max(r for r in range(len(board)) if board[r][column] == 0)


def _canon_hex(r, c, own):
    """Le joueur de couleur 2 relie gauche-droite : on transpose pour que « mes » pierres relient toujours haut-bas
    (la transposition préserve le pavage hexagonal)."""
    return (r, c) if own == 1 else (c, r)


def encode(obs):
    """(plans uint8 (8, 15, 15), annexe float32 (8,))."""
    game = obs["game"]
    planes = np.zeros((PLANES, CANVAS, CANVAS), dtype=np.uint8)
    extra = np.zeros(EXTRA, dtype=np.float32)
    oy, ox = _offset(game)
    h, w = DIMS[game]
    planes[0, oy:oy + h, ox:ox + w] = 1
    if game == "dames":
        from ..zero import dames_net
        c = dames_net.canonical(obs["cells"], obs["next"]).reshape(8, 8)
        for plane, piece in ((1, 1), (3, 2), (2, 3), (4, 4)):
            planes[plane, oy:oy + 8, ox:ox + 8] = c == piece
        extra[7] = min(obs["quiet"], 20) / 20.0
        return planes, extra
    board = np.asarray(obs["board"], dtype=np.int8)
    own = _own_color(obs)
    if game == "hex":
        if own == 2:
            board = board.T
        planes[1, oy:oy + h, ox:ox + w] = board == own
        planes[2, oy:oy + h, ox:ox + w] = board == 3 - own
        planes[5, oy:oy + h, ox:ox + w] = board == 0
        planes[6, oy, ox:ox + w] = 1
        planes[6, oy + h - 1, ox:ox + w] = 1
        planes[7, oy:oy + h, ox] = 1
        planes[7, oy:oy + h, ox + w - 1] = 1
        extra[0] = float(obs["hex_state"]["swap_available"])
        return planes, extra
    planes[1, oy:oy + h, ox:ox + w] = board == own
    planes[2, oy:oy + h, ox:ox + w] = board == 3 - own
    if game == "connect4":
        for col in range(w):
            if board[0][col] == 0:
                planes[5, oy + _landing_row(board, col), ox + col] = 1
    elif game == "gomoku":
        s = obs["gomoku_state"]
        extra[1 + PHASES.index(s["phase"])] = 1
        extra[6] = float(own == 1)
        if s["phase"] != "choose_color":
            planes[5, oy:oy + h, ox:ox + w] = board == 0
    else:
        planes[5, oy:oy + h, ox:ox + w] = board == 0
    return planes, extra


def action_index(obs, action):
    game = obs["game"]
    if game == "dames":
        from ..zero import dames_net
        return dames_net.action_index(action[0], obs["next"])
    if game == "tictactoe":
        return _cell(game, action["row"], action["col"])
    if game == "connect4":
        return _cell(game, _landing_row(obs["board"], action["column"]), action["column"])
    if action.get("swap"):
        return SWAP
    if "choose" in action:
        return CHOOSE_BLACK if action["choose"] == "black" else CHOOSE_WHITE
    r, c = action["row"], action["col"]
    if game == "hex":
        r, c = _canon_hex(r, c, _own_color(obs))
    return _cell(game, r, c)


def legal_indices(obs, legal):
    return np.array([action_index(obs, a) for a in legal], dtype=np.int16)


def n_actions(game):
    return N_ACTIONS[game]


def game_id(game):
    return GAME_ID[game]

"""Interface unique de partie pour les cinq jeux : `observation`, `legal`, `step`, `done`, `winner` (1 ou 2, 0 nul), `player`."""
from __future__ import annotations

import copy

from ..games import make_game


class EnvAdapter:
    """tictactoe, connect4, hex, gomoku : règles de Garry (`logic_arena.games`)."""

    def __init__(self, game, seed=0, env=None):
        self.game = game
        self.env = env if env is not None else make_game(game, seed)

    def observation(self):
        return self.env.observation()

    def legal(self):
        return self.env.legal_actions()

    def step(self, action):
        self.env.step(action)

    @property
    def done(self):
        return bool(self.env.done)

    @property
    def winner(self):
        return self.env.winner

    @property
    def player(self):
        return self.env.current_player

    def copy(self):
        return EnvAdapter(self.game, env=copy.deepcopy(self.env))


class DamesAdapter:
    """Dames de `multi` portées en C++ (`logic_arena.zero.dames`). Joueurs 1 et 2 = sièges 0 et 1."""
    game = "dames"

    def __init__(self, state=None):
        from ..zero import dames
        self._d = dames
        self.state = state if state is not None else dames.State.new()

    def observation(self):
        s = self.state
        return {"game": "dames", "cells": list(s.cells), "next": s.next, "quiet": s.quiet, "current_player": s.next + 1,
                "done": s.status != "playing", "winner": self.winner}

    def legal(self):
        return list(self.state.moves())

    def step(self, action):
        self.state = self.state.advance(*action)

    @property
    def done(self):
        return self.state.status != "playing"

    @property
    def winner(self):
        s = self.state
        return None if s.status == "playing" else (s.winner + 1 if s.status == "won" else 0)

    @property
    def player(self):
        return self.state.next + 1

    def copy(self):
        return DamesAdapter(copy.copy(self.state))


def make_adapter(game, seed=0):
    return DamesAdapter() if game == "dames" else EnvAdapter(game, seed)

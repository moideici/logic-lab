"""Positions légales et oracles fondés sur les règles, sans le solveur testé."""
import copy
import json
from pathlib import Path
import unittest

import numpy as np

from logic_arena.agents import Budget, ReferenceAgent
from logic_arena.connect4 import search
from logic_arena.games import make_game
from logic_arena.neural import NeuralAgent, NeuralPolicy
from unittest.mock import patch


POSITIONS = json.loads((Path(__file__).parent / "fixtures" / "connect4-positions.json").read_text())


def winning_columns(env, player=None):
    player = env.current_player if player is None else player
    wins = []
    for action in env.legal_actions():
        child = copy.deepcopy(env)
        child.current_player = player
        child.step(action)
        if child.winner == player:
            wins.append(action["column"])
    return wins


class Connect4TacticsTests(unittest.TestCase):
    def test_endgame_choice_matches_exhaustive_rules_search(self):
        env = make_game("connect4")
        for c in [4,2,0,4,6,4,1,2,2,5,1,0,6,0,4,6,2,4,0,5,5,1,2,0,1,2,5,4,6,6,1,1,0,5]:
            env.step({"column": c})
        root = env.current_player

        def value(state):
            if state.done:
                return 0 if not state.winner else 1 if state.winner == root else -1
            scores = []
            for action in state.legal_actions():
                child = copy.deepcopy(state)
                child.step(action)
                scores.append(value(child))
            return (max if state.current_player == root else min)(scores)

        expected = value(env)
        action, info = search(env.observation(), env.legal_actions(), Budget(100000, 10000))
        child = copy.deepcopy(env)
        child.step(action)
        self.assertEqual(value(child), expected)
        self.assertGreater(info["depth"], 1)

    def test_safe_fallback_wins_and_forks_even_with_exhausted_search(self):
        for position in POSITIONS:
            env = make_game("connect4")
            for column in position["history"]:
                env.step({"column": column})
            before = env.observation()
            legal = env.legal_actions()
            # Reconstruire les attentes avec le moteur de règles indépendant.
            wins, safe, forks = winning_columns(env), [], []
            for action in legal:
                child = copy.deepcopy(env)
                child.step(action)
                if child.winner == env.current_player or not winning_columns(child):
                    safe.append(action["column"])
                    if not child.done and len(winning_columns(child, env.current_player)) >= 2:
                        forks.append(action["column"])
            self.assertEqual(wins, position["immediate"])
            self.assertEqual(safe, position["safe"])
            self.assertEqual(forks, position["forks"])
            for nodes in (0, 150):
                with self.subTest(category=position["category"], history=position["history"], nodes=nodes):
                    # Un a priori extrême ne doit pas contourner la tactique.
                    logits = np.arange(7) * 1e12
                    action, info = search(before, legal, Budget(nodes, 10000), logits)
                    self.assertIn(action, legal)
                    column = action["column"]
                    if wins:
                        self.assertIn(column, wins)
                        self.assertEqual(info["remaining_moves"], 1)
                    elif forks:
                        self.assertIn(column, forks)
                        self.assertEqual(info["remaining_moves"], 3)
                        # Chaque réponse adverse laisse une victoire immédiate.
                        child = copy.deepcopy(env)
                        child.step(action)
                        for reply in child.legal_actions():
                            response = copy.deepcopy(child)
                            response.step(reply)
                            self.assertFalse(response.done)
                            self.assertTrue(winning_columns(response))
                    elif safe:
                        self.assertIn(column, safe)
                    else:
                        self.assertFalse(info["optimal"])
                    self.assertEqual(env.observation(), before)

    def test_neural_and_reference_use_tactical_protection(self):
        position = next(p for p in POSITIONS if p["category"] == "support_trap")
        env = make_game("connect4")
        for column in position["history"]:
            env.step({"column": column})
        with patch.object(NeuralPolicy, "logits", return_value=np.arange(7) * 1e12):
            action = NeuralAgent(level=1).choose(env.observation(), env.legal_actions()).action
        self.assertIn(action["column"], position["safe"])
        reference = ReferenceAgent(level=10, time_ms=.000001)
        self.assertIn(reference.choose(env.observation(), env.legal_actions()).action["column"], position["safe"])


if __name__ == "__main__":
    unittest.main()

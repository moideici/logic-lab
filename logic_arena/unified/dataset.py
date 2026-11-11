"""Jeu de données unifié : une position = plans + annexe + (coups, scores) du professeur + valeur. Un fichier .npz par jeu."""
from __future__ import annotations

import numpy as np

from .encode import action_index, encode
from .spec import CANVAS, EXTRA, GAMES, PLANES


class Records:
    def __init__(self, game, k):
        self.game, self.k = game, k
        self.planes, self.extra, self.moves, self.scores, self.value, self.value_search = [], [], [], [], [], []

    def __len__(self):
        return len(self.value)

    def add(self, obs, actions, scores, value, value_search=None):
        """`actions` : coups du professeur (objets d'action du jeu) ; `scores` : leurs qualités (plus grand = meilleur)."""
        p, e = encode(obs)
        idx = np.full(self.k, -1, dtype=np.int16)
        sc = np.full(self.k, np.nan, dtype=np.float32)
        order = np.argsort(-np.asarray(scores, dtype=np.float64), kind="stable")[:self.k]
        seen = set()
        j = 0
        for i in order:
            a = int(action_index(obs, actions[i]))
            if a in seen:
                continue
            seen.add(a)
            idx[j], sc[j] = a, scores[i]
            j += 1
        self.planes.append(p)
        self.extra.append(e)
        self.moves.append(idx)
        self.scores.append(sc)
        self.value.append(value)
        self.value_search.append(value if value_search is None else value_search)

    def save(self, path):
        np.savez_compressed(path, game=np.array(GAMES.index(self.game), dtype=np.int8), planes=np.stack(self.planes), extra=np.stack(self.extra),
                            moves=np.stack(self.moves), scores=np.stack(self.scores), value=np.array(self.value, dtype=np.float32),
                            value_search=np.array(self.value_search, dtype=np.float32))


def load(path):
    d = np.load(path)
    out = {k: d[k] for k in d.files}
    out["game"] = GAMES[int(out["game"])]
    assert out["planes"].shape[1:] == (PLANES, CANVAS, CANVAS) and out["extra"].shape[1] == EXTRA
    return out


def policy_target(moves, scores, temperature=1.0, n_actions=228):
    """Distribution d'apprentissage : softmax(score / T) sur les coups étiquetés. moves (K,), scores (K,) avec -1 / NaN de remplissage."""
    ok = moves >= 0
    z = scores[ok].astype(np.float64) / temperature
    z = np.exp(z - z.max())
    target = np.zeros(n_actions, dtype=np.float32)
    target[moves[ok]] = z / z.sum()
    return target

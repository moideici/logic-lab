"""Garry étendu aux Dames de multi : un emplacement de plus dans le MLP global, sans toucher à un seul coefficient des autres jeux.

Garry 0.6 est un MLP unique : entrée = caractéristiques de tous les jeux (une tranche par jeu) + une étiquette de jeu, couche cachée 48 (tanh),
noyau partagé 48x48 (tanh), sortie = actions de tous les jeux (une tranche par jeu). Ajouter un jeu = ajouter une tranche d'entrée (129 caractéristiques
+ 1 étiquette) et une tranche de sortie (1 024 coups départ-arrivée) à la fin. Les anciens jeux voient exactement les mêmes calculs.

Option d'élargissement (`extra_hidden`) : des unités cachées en plus, dont toutes les connexions vers les anciens jeux sont nulles et restent gelées :
les dames y gagnent de la capacité sans modifier les anciens jeux (vérifié par `old_game_logits`).
"""
from __future__ import annotations

import copy

import numpy as np

from .general import FEATURES, GAMES, INPUT, INPUT_OFFSETS, OUTPUT, OUTPUT_OFFSETS, SPECS, GarryPolicy, general_encode
from .zero import dames_net as dn

DAMES_FEATURES = 129  # 4 types de pièces sur les 32 cases foncées + compteur de coups de dame sans prise
DAMES_OUTPUT = dn.N_ACTIONS
DAMES_IN = INPUT  # première ligne d'entrée des dames
DAMES_TAG = INPUT + DAMES_FEATURES
TOTAL_INPUT = INPUT + DAMES_FEATURES + 1
DAMES_OUT = OUTPUT
TOTAL_OUTPUT = OUTPUT + DAMES_OUTPUT


def dames_features(cells, nxt, quiet):
    """(129,) : plateau vu du joueur au trait, 32 cases foncées x 4 types de pièces, puis le compteur."""
    c = dn.canonical(cells, nxt)
    out = np.zeros(DAMES_FEATURES, dtype=np.float32)
    dark = c[dn.DARK]
    for k, piece in enumerate((1, 2, 3, 4)):
        out[k * 32:(k + 1) * 32] = dark == piece
    out[128] = min(quiet, 20) / 20.0
    return out


def dames_features_batch(cells, nxt, quiet):
    cells = np.asarray(cells, dtype=np.int8)
    flip = np.asarray(nxt) == 1
    rotated = dn._SWAP[cells[:, ::-1]]
    canon = np.where(flip[:, None], rotated, cells)[:, dn.DARK]
    out = np.zeros((len(cells), DAMES_FEATURES), dtype=np.float32)
    for k, piece in enumerate((1, 2, 3, 4)):
        out[:, k * 32:(k + 1) * 32] = canon == piece
    out[:, 128] = np.minimum(np.asarray(quiet), 20) / 20.0
    return out


class GarryDames:
    """Garry 0.6 + une tranche d'entrée et de sortie pour les dames (+ unités cachées optionnelles réservées aux dames)."""

    def __init__(self, base: GarryPolicy, extra_hidden=0, seed=0):
        h0 = base.hidden
        h = h0 + extra_hidden
        rng = np.random.default_rng(seed)
        self.h0, self.hidden = h0, h
        self.w1 = np.zeros((TOTAL_INPUT, h), dtype=np.float32)
        self.b1 = np.zeros(h, dtype=np.float32)
        self.core_w = np.zeros((h, h), dtype=np.float32)
        self.core_b = np.zeros(h, dtype=np.float32)
        self.w2 = np.zeros((h, TOTAL_OUTPUT), dtype=np.float32)
        self.b2 = np.zeros(TOTAL_OUTPUT, dtype=np.float32)
        self.w1[:INPUT, :h0] = base.w1
        self.b1[:h0] = base.b1
        self.core_w[:h0, :h0] = base.core['w']
        self.core_b[:h0] = base.core['b']
        self.w2[:h0, :OUTPUT] = base.w2
        self.b2[:OUTPUT] = base.b2
        # Tranche des dames : petite initialisation aléatoire (comme les autres jeux), y compris vers les unités ajoutées.
        self.w1[INPUT:, :] = rng.standard_normal((DAMES_FEATURES + 1, h)).astype(np.float32) * np.sqrt(2 / (DAMES_FEATURES + h))
        self.w2[:, OUTPUT:] = rng.standard_normal((h, DAMES_OUTPUT)).astype(np.float32) * np.sqrt(2 / (h + DAMES_OUTPUT))
        if extra_hidden:
            # unités ajoutées : nourries par les anciennes unités, sans effet sur les anciens jeux (leurs poids vers les anciennes sorties restent nuls)
            self.core_w[:h0, h0:] = rng.standard_normal((h0, extra_hidden)).astype(np.float32) * 0.15
            self.core_w[h0:, h0:] = rng.standard_normal((extra_hidden, extra_hidden)).astype(np.float32) * 0.15
        # masques des paramètres entraînables par les dames sans toucher aux anciens jeux
        self.mask_w1 = np.zeros_like(self.w1)
        self.mask_w1[INPUT:, :] = 1
        self.mask_core_w = np.zeros_like(self.core_w)
        self.mask_core_b = np.zeros_like(self.core_b)
        if extra_hidden:
            self.mask_core_w[:h0, h0:] = 1
            self.mask_core_w[h0:, h0:] = 1
            self.mask_core_b[h0:] = 1
        self.mask_w2 = np.zeros_like(self.w2)
        self.mask_w2[:, OUTPUT:] = 1
        self.mask_b2 = np.zeros_like(self.b2)
        self.mask_b2[OUTPUT:] = 1
        self.base_hidden = h0
        self.position_head = copy.deepcopy(base.position_head)

    # --- calcul -----------------------------------------------------------------------------------------------------------------
    def forward(self, x):
        e = np.tanh(x @ self.w1 + self.b1)
        return np.tanh(e @ self.core_w + self.core_b) @ self.w2 + self.b2

    def old_game_logits(self, obs):
        """Sorties d'un ancien jeu (même entrée que GarryPolicy)."""
        x = np.zeros(TOTAL_INPUT, dtype=np.float32)
        x[:INPUT] = general_encode(obs)
        g = obs['game']
        return self.forward(x)[OUTPUT_OFFSETS[g]:OUTPUT_OFFSETS[g] + SPECS[g][1]]

    def dames_logits_batch(self, feats):
        x = np.zeros((len(feats), TOTAL_INPUT), dtype=np.float32)
        x[:, DAMES_IN:DAMES_IN + DAMES_FEATURES] = feats
        x[:, DAMES_TAG] = 1
        return self.forward(x)[:, DAMES_OUT:]

    def dames_logits(self, cells, nxt, quiet):
        return self.dames_logits_batch(dames_features(cells, nxt, quiet)[None])[0]

    def parameter_count(self):
        return int(self.w1.size + self.b1.size + self.core_w.size + self.core_b.size + self.w2.size + self.b2.size)

    def save(self, path):
        np.savez_compressed(path, w1=self.w1, b1=self.b1, core_w=self.core_w, core_b=self.core_b, w2=self.w2, b2=self.b2, h0=self.h0,
                            hidden=self.hidden)

    @classmethod
    def load(cls, path, base):
        d = np.load(path)
        extra = int(d['hidden']) - int(d['h0'])
        m = cls(base, extra)
        for name in ('w1', 'b1', 'core_w', 'core_b', 'w2', 'b2'):
            setattr(m, name, d[name].astype(np.float32))
        return m


class DamesGarryPlayer:
    """Joue aux dames avec le MLP de Garry (politique seule, sans recherche) : coup légal de plus haut logit."""

    def __init__(self, model: GarryDames):
        self.model = model

    def choose(self, state):
        moves = state.moves()
        logits = self.model.dames_logits(state.cells, state.next, state.quiet)
        idx = [dn.action_index(m[0], state.next) for m in moves]
        return moves[int(np.argmax(logits[idx]))]

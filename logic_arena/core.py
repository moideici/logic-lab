"""Garry Core : le réseau de Garry sous forme de couches nommées, observables et modifiables.

C'est le même calcul que `GarryPolicy.logits` (tanh(x·w1+b1) → tanh(h·W+b) → ·w2+b2), mais exposé couche par couche :
activations capturables, neurones éteignables ou supprimables, comparaison de deux versions. Le test de parité
(`tests/test_core.py`) exige l'égalité exacte avec les poids 0.6.0 sur les 14 jeux ; le Core ne remplace pas
l'entraînement, il sert d'instrument au Lab.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import numpy as np

ACTIVATIONS = {"tanh": np.tanh, "linear": lambda z: z}


@dataclass
class Dense:
    name: str
    w: np.ndarray
    b: np.ndarray
    activation: str = "tanh"

    def __post_init__(self):
        if self.w.ndim != 2 or self.b.shape != (self.w.shape[1],):
            raise ValueError(f"Couche {self.name} : dimensions incohérentes")
        if self.activation not in ACTIVATIONS:
            raise ValueError(f"Activation inconnue : {self.activation}")

    @property
    def n_in(self):
        return self.w.shape[0]

    @property
    def n_out(self):
        return self.w.shape[1]

    def __call__(self, x):
        return ACTIVATIONS[self.activation](x @ self.w + self.b)


@dataclass
class Net:
    layers: list[Dense]
    # neurones éteints : nom de couche -> indices dont la sortie est forcée à 0
    muted: dict[str, set] = field(default_factory=dict)

    def __post_init__(self):
        for a, b in zip(self.layers, self.layers[1:]):
            if a.n_out != b.n_in:
                raise ValueError(f"{a.name} → {b.name} : {a.n_out} sorties pour {b.n_in} entrées")

    # ---- calcul ----------------------------------------------------------------
    def forward(self, x, trace=None):
        """Sorties du réseau. `trace` (dict) reçoit l'activation de chaque couche si fourni."""
        h = np.asarray(x, dtype=np.float32)
        for layer in self.layers:
            h = layer(h)
            idx = self.muted.get(layer.name)
            if idx:
                h = h.copy()
                h[..., sorted(idx)] = 0
            if trace is not None:
                trace[layer.name] = h
        return h

    def layer(self, name):
        for layer in self.layers:
            if layer.name == name:
                return layer
        raise KeyError(name)

    @property
    def shape(self):
        return [self.layers[0].n_in] + [layer.n_out for layer in self.layers]

    def parameter_count(self):
        return sum(l.w.size + l.b.size for l in self.layers)

    # ---- chirurgie -------------------------------------------------------------
    def mute(self, name, indices):
        """Éteint des neurones sans toucher aux poids (réversible)."""
        layer = self.layer(name)
        if layer is self.layers[-1]:
            raise ValueError("On n'éteint pas la couche de sortie")
        bad = [i for i in indices if not 0 <= i < layer.n_out]
        if bad:
            raise ValueError(f"Neurones inexistants : {bad}")
        self.muted.setdefault(name, set()).update(int(i) for i in indices)

    def unmute_all(self):
        self.muted.clear()

    def prune(self, name, indices):
        """Supprime physiquement des neurones : colonnes de la couche, lignes de la suivante.
        À qualité égale, c'est équivalent à `mute` (vérifié par test) mais le réseau devient plus petit."""
        position = [l.name for l in self.layers].index(name)
        if position == len(self.layers) - 1:
            raise ValueError("On ne supprime pas de neurone de sortie")
        drop = sorted({int(i) for i in indices})
        layer, following = self.layers[position], self.layers[position + 1]
        if any(not 0 <= i < layer.n_out for i in drop) or len(drop) >= layer.n_out:
            raise ValueError("Indices invalides ou couche vidée")
        keep = [i for i in range(layer.n_out) if i not in drop]
        layer.w, layer.b = layer.w[:, keep].copy(), layer.b[keep].copy()
        following.w = following.w[keep, :].copy()
        self.muted.pop(name, None)
        return keep

    def grow(self, name, count=1, scale=0.01, rng=None):
        """Ajoute des neurones quasi muets (poids sortants nuls) : la sortie du réseau ne change pas."""
        rng = rng or np.random.default_rng(0)
        position = [l.name for l in self.layers].index(name)
        if position == len(self.layers) - 1:
            raise ValueError("On n'ajoute pas de neurone de sortie")
        layer, following = self.layers[position], self.layers[position + 1]
        fresh = (rng.standard_normal((layer.n_in, count)) * scale).astype(np.float32)
        layer.w = np.concatenate([layer.w, fresh], axis=1)
        layer.b = np.concatenate([layer.b, np.zeros(count, dtype=np.float32)])
        following.w = np.concatenate([following.w, np.zeros((count, following.n_out), dtype=np.float32)], axis=0)
        return list(range(layer.n_out - count, layer.n_out))

    # ---- analyse ---------------------------------------------------------------
    def copy(self):
        return Net([Dense(l.name, l.w.copy(), l.b.copy(), l.activation) for l in self.layers], copy.deepcopy(self.muted))

    def weight_change(self, other):
        """Pour chaque couche : norme du changement de poids par neurone de sortie, entre deux versions de même forme."""
        if self.shape != other.shape:
            raise ValueError("Formes différentes : comparaison impossible")
        out = {}
        for a, b in zip(self.layers, other.layers):
            out[a.name] = np.sqrt(((a.w - b.w) ** 2).sum(axis=0) + (a.b - b.b) ** 2)
        return out


# ---- passerelle avec les poids Garry existants ------------------------------------
LAYERS = ("encodeur", "coeur", "sortie")


def from_garry(policy):
    """Net exactement équivalent à `GarryPolicy` (partage les valeurs, pas la mémoire : copies)."""
    return Net([
        Dense("encodeur", policy.w1.copy(), policy.b1.copy(), "tanh"),
        Dense("coeur", policy.core["w"].copy(), policy.core["b"].copy(), "tanh"),
        Dense("sortie", policy.w2.copy(), policy.b2.copy(), "linear"),
    ])


def encode_observation(obs):
    """Entrée du réseau pour une observation, identique à celle de GarryPolicy."""
    from .general import general_encode
    return general_encode(obs)

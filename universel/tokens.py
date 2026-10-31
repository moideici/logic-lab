"""Encodeur universel : une vue JSON et une liste de coups légaux deviennent des jetons, sans aucune connaissance du jeu.

Un jeton = une feuille du JSON : (nom du champ, un ou deux indices de tableau, type et valeur). Les entiers (indices et valeurs) partagent la même table
d'embeddings : un coup `{"cell": 4}` et la case d'indice 4 de la vue se rejoignent par attention. Deux jetons spéciaux donnent le siège et le nombre de joueurs.

Colonnes entières d'un jeton : 0 clé (hachage du nom de champ), 1 indice 1, 2 indice 2, 3 type de valeur, 4 valeur, 5 segment (0 vue, 1 coup, 2 méta), 6 numéro de coup.
Colonne flottante : amplitude de la valeur (pour les grands nombres).
"""
from __future__ import annotations

import hashlib
import math

import numpy as np

KEY_BUCKETS = 4096
STR_BUCKETS = 4096
NUM = 256  # entiers 0..254 ; 255 = « grand ou absent »
NONE_IDX = 255
MAX_VIEW_TOKENS = 256
MAX_ACTION_TOKENS = 8
MAX_ACTIONS = 64
T_BOOL, T_INT, T_NEG, T_FLOAT, T_STR, T_NULL, T_NONE = range(7)
SEG_VIEW, SEG_ACTION, SEG_META = 0, 1, 2
_hash_cache: dict = {}


def bucket(text, size):
    v = _hash_cache.get((text, size))
    if v is None:
        v = int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=4).digest(), "little") % size
        _hash_cache[(text, size)] = v
    return v


def _value(v):
    """(type, valeur entière 0..255 ou bucket, amplitude flottante)."""
    if v is None:
        return T_NULL, 0, 0.0
    if isinstance(v, bool):
        return T_BOOL, int(v), 0.0
    if isinstance(v, int):
        if v >= 0:
            return T_INT, min(v, NONE_IDX), (math.log1p(v) / 8.0 if v >= NONE_IDX else 0.0)
        return T_NEG, min(-v, 254), math.log1p(-v) / 8.0
    if isinstance(v, float):
        return T_FLOAT, int(min(max(v, 0), 254)), float(np.clip(v / 10.0, -10, 10))
    if isinstance(v, str):
        return T_STR, bucket(v, STR_BUCKETS), 0.0
    return T_NULL, 0, 0.0


def leaves(obj, limit):
    """Feuilles (clé, indice1, indice2, valeur) d'un JSON, dans l'ordre de parcours."""
    out = []

    def walk(o, keys, idx):
        if len(out) >= limit:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, keys + (k,), idx)
        elif isinstance(o, (list, tuple)):
            if not o:
                out.append((".".join(keys) + "[]", NONE_IDX, NONE_IDX, None))
            for i, v in enumerate(o):
                walk(v, keys, idx + (min(i, 254),))
        else:
            i1 = idx[0] if idx else NONE_IDX
            i2 = idx[-1] if len(idx) > 1 else NONE_IDX
            out.append((".".join(keys), i1, i2, o))

    walk(obj, (), ())
    return out[:limit]


def token_rows(items, segment, slot):
    rows = []
    for key, i1, i2, v in items:
        t, val, f = _value(v)
        rows.append(((bucket(key, KEY_BUCKETS), i1, i2, t, val, segment, slot), f))
    return rows


def encode(view, legal, seat, nplayers, max_actions=MAX_ACTIONS):
    """-> dict de tableaux : ints (L,7), floats (L,), n_view, n_actions. Les jetons de vue/méta d'abord, puis ceux de chaque coup."""
    meta = [("__seat__", NONE_IDX, NONE_IDX, int(seat)), ("__joueurs__", NONE_IDX, NONE_IDX, int(nplayers))]
    rows = token_rows(meta, SEG_META, 0) + token_rows(leaves(view, MAX_VIEW_TOKENS), SEG_VIEW, 0)
    n_view = len(rows)
    legal = list(legal)[:max_actions]
    for a, action in enumerate(legal):
        rows += token_rows(leaves(action, MAX_ACTION_TOKENS), SEG_ACTION, a)
    ints = np.array([r[0] for r in rows], dtype=np.int16)
    floats = np.array([r[1] for r in rows], dtype=np.float32)
    return {"ints": ints, "floats": floats, "n_view": n_view, "n_actions": len(legal)}


def collate(samples, device=None):
    """Remplit un lot de jetons : ints (B,L,7), floats (B,L), mask (B,L), nombre d'actions (B,)."""
    import torch
    L = max(len(s["ints"]) for s in samples)
    B = len(samples)
    ints = np.zeros((B, L, 7), dtype=np.int64)
    floats = np.zeros((B, L), dtype=np.float32)
    mask = np.zeros((B, L), dtype=bool)
    for b, s in enumerate(samples):
        n = len(s["ints"])
        ints[b, :n] = s["ints"]
        floats[b, :n] = s["floats"]
        mask[b, :n] = True
    n_actions = np.array([s["n_actions"] for s in samples], dtype=np.int64)
    out = {"ints": torch.tensor(ints), "floats": torch.tensor(floats), "mask": torch.tensor(mask), "n_actions": torch.tensor(n_actions)}
    return {k: (v.to(device) if device else v) for k, v in out.items()}

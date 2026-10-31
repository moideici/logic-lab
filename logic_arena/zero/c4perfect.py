"""Joueur parfait de Puissance 4 : livre d'ouverture du premier joueur (plis 0 à 4) puis solveur exact.

`choose(pos, mask)` renvoie une colonne qui conserve le résultat théorique (gain, sinon nul, sinon défaite la plus longue).
Le livre ne couvre que les positions atteintes en suivant la stratégie gagnante du premier joueur ; ailleurs on appelle le solveur
(moins d'une seconde dès le 6e coup, jusqu'à ~30 s avant).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import c4solver

BOOK_PATH = Path(__file__).with_name("c4_book.json")
_book = None


def book():
    global _book
    if _book is None:
        _book = json.loads(BOOK_PATH.read_text(encoding="utf-8")) if BOOK_PATH.exists() else {}
    return _book


def choose(pos, mask, exact=True):
    cols = book().get(f"{int(pos)},{int(mask)}")
    if cols:
        return min(cols, key=lambda c: abs(c - 3))
    weak = not (exact and bin(int(mask)).count("1") >= 12)  # score exact seulement quand c'est rapide
    s = c4solver.scores(pos, mask, weak)
    if weak:
        s = np.where(s == -1000, -1000, np.sign(s))
    best = max(x for x in s if x != -1000)
    return min((c for c in range(7) if s[c] == best), key=lambda c: abs(c - 3))

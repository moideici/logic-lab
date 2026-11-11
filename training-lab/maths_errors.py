"""Analyse des erreurs d'un point de contrôle sur la VALIDATION (jamais le test) : où le réseau se trompe, de combien, et pourquoi.

Usage : python training-lab/maths_errors.py curriculum-s0 [--n 2000]
Classe chaque erreur d'étape : forme invalide, valeur fausse, ou étape valide mais différente de la référence. Pour les erreurs de
valeur, donne l'écart au bon résultat et le nombre de chiffres communs.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.maths.arith import ArithError, is_canonical, value, verify_step  # noqa: E402
from logic_arena.maths.data import LEVELS, LEVELS2, LEVELS3, make_steps  # noqa: E402
from logic_arena.maths.model import MathLM, generate, load_compatible  # noqa: E402

HERE = Path(__file__).resolve().parent


def classify(inp, ref, pred):
    if pred == ref:
        return "juste"
    if not is_canonical(pred):
        return "forme invalide"
    if verify_step(inp, pred):
        return "valide mais autre étape"
    try:
        if "=" not in inp and "=" not in pred and value(pred)[0] == value(inp)[0]:
            return "bonne valeur, mauvaise progression"
    except ArithError:
        pass
    return "valeur fausse"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--wave", type=int, choices=(1, 2, 3), default=1)
    ap.add_argument("--show", type=int, default=6)
    a = ap.parse_args()
    torch.set_num_threads(2)
    blob = torch.load(HERE / "models" / "maths" / f"{a.tag}.pt", map_location="cpu", weights_only=True)
    model = MathLM(**blob["config"])
    load_compatible(model, blob["state"])
    for i, lv in enumerate({1: LEVELS, 2: LEVELS2, 3: LEVELS3}[a.wave]):
        pairs = make_steps(lv, a.n, 9000 + i, "val", distinct=True)
        preds = generate(model, [p for p, _ in pairs])
        kinds = Counter(classify(p, r, q) for (p, r), q in zip(pairs, preds))
        print(f"\n{lv} ({len(pairs)} états de validation) : " + ", ".join(f"{k} {v}/{len(pairs)}" for k, v in kinds.most_common()))
        wrong = [(p, r, q) for (p, r), q in zip(pairs, preds) if q != r][:a.show]
        for p, r, q in wrong:
            print(f"   {p:>16}  attendu {r:<14} obtenu {q}")

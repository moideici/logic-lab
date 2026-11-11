"""Mesures du protocole : étape exacte, étape valide, problème résolu (réseau rappelé jusqu'à l'état terminal).

« Exacte » : la sortie égale l'étape de la règle de référence. « Valide » : l'évaluateur indépendant confirme la forme, la valeur
et la progression (`arith.verify_step`). « Résolu » : toutes les étapes sont valides et le résultat final est exact.
"""
from __future__ import annotations

from collections import Counter

from .arith import ArithError, final_state, next_state, verify_step
from .data import make_starts, make_steps
from .model import beam_generate, generate

MAX_STEPS = 12


def step_metrics(model, pairs, device="cpu"):
    preds = generate(model, [i for i, _ in pairs], device)
    n = len(pairs)
    exact = sum(p == o for p, (_, o) in zip(preds, pairs))
    valid = sum(verify_step(i, p) for p, (i, _) in zip(preds, pairs))
    return {"n": n, "exacte": exact / n, "valide": valid / n}


def _terminal(s):
    try:
        return next_state(s, True) is None  # rational : `(5/6)` est un nombre, donc terminal
    except ArithError:
        return False


def solve_metrics(model, starts, device="cpu", max_steps=MAX_STEPS):
    n = len(starts)
    targets = [final_state(s) for s in starts]
    states, ok, steps, why = list(starts), [None] * n, [0] * n, Counter()
    active = list(range(n))
    for _ in range(max_steps):
        if not active:
            break
        preds = generate(model, [states[i] for i in active], device)
        still = []
        for i, p in zip(active, preds):
            if not verify_step(states[i], p):
                ok[i] = False
                why["étape invalide"] += 1
                continue
            states[i] = p
            steps[i] += 1
            if _terminal(p):
                ok[i] = p == targets[i]
                if not ok[i]:
                    why["résultat faux"] += 1
            else:
                still.append(i)
        active = still
    for i in active:
        ok[i] = False
        why["trop d'étapes"] += 1
    good = [steps[i] for i in range(n) if ok[i]]
    return {"n": n, "resolu": sum(ok) / n, "etapes_moy": (sum(good) / len(good)) if good else None, "echecs": dict(why)}


def evaluate_level(model, level, split="val", n_steps=500, n_starts=300, seed=0, ood=False, device="cpu"):
    pairs = make_steps(level, n_steps, seed, split, ood, distinct=True)
    starts = make_starts(level, n_starts, seed + 1, split, ood)
    return {"etape": step_metrics(model, pairs, device), "probleme": solve_metrics(model, starts, device)}


def solve_verified(model, starts, beam=8, device="cpu", max_steps=MAX_STEPS):
    """Proposer puis vérifier : à chaque pas, le réseau propose `beam` étapes (faisceau) et le vérificateur exact garde la plus probable
    qui soit valide. Ce n'est PAS le réseau seul : le vérificateur contrôle la valeur. `sauvetages` = pas où la première proposition
    (celle du décodage glouton, ou presque) était fausse et une autre a été acceptée ; `echecs` = pas où aucune des `beam` propositions
    n'était valide."""
    n = len(starts)
    targets = [final_state(s) for s in starts]
    states, ok, steps, why = list(starts), [None] * n, [0] * n, Counter()
    rescued = total = 0
    active = list(range(n))
    for _ in range(max_steps):
        if not active:
            break
        cands = beam_generate(model, [states[i] for i in active], beam, device)
        still = []
        for i, cl in zip(active, cands):
            pick = next(((r, c) for r, c in enumerate(cl) if verify_step(states[i], c)), None)
            if pick is None:
                ok[i] = False
                why["aucune proposition valide"] += 1
                continue
            total += 1
            rescued += pick[0] > 0
            states[i] = pick[1]
            steps[i] += 1
            if _terminal(pick[1]):
                ok[i] = pick[1] == targets[i]
                if not ok[i]:
                    why["résultat faux"] += 1
            else:
                still.append(i)
        active = still
    for i in active:
        ok[i] = False
        why["trop d'étapes"] += 1
    return {"n": n, "beam": beam, "resolu": sum(ok) / n, "etapes": total, "sauvetages": rescued, "echecs": dict(why)}

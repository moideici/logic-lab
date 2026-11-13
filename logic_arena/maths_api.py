"""Page Maths du Lab : poser un calcul à un modèle de la famille Maths et voir les étapes, vérifiées une à une par l'évaluateur indépendant.
Le réseau écrit l'étape suivante ; `arith.verify_step` (évaluateur écrit séparément de la règle de référence) la juge ; la réponse finale est
comparée à la réponse exacte. Poids locaux (training-lab/models/maths/)."""
from __future__ import annotations

import re
import time
from pathlib import Path

import torch

from .maths.arith import ArithError, final_state, next_state, verify_step
from .maths.data import MAX_LEN
from .maths.model import MathLM, beam_generate, generate, load_compatible

MODELS = Path(__file__).resolve().parents[1] / "training-lab" / "models" / "maths"
MAX_STEPS = 30
# id, fichier, libellé, rationnels (vague 2 et suivantes : fractions, puissances, racines, équations)
CATALOG = [
    ("vague4", "vague4-1", "Vague 4 · 12 couches", True),
    ("vague3", "vague3-1", "Vague 3 · 12 couches", True),
    ("vague2b", "vague2a-2", "Vague 2 · 8 couches", True),
    ("vague2a", "vague2a-1", "Vague 2 · 4 couches", True),
    ("recetteD", "recette-D", "Vague 1 · recette D (812 k)", False),
    ("recetteC", "recette-C", "Vague 1 · recette C", False),
    ("recetteB", "recette-B", "Vague 1 · recette B", False),
    ("recetteA", "recette-A", "Vague 1 · recette A", False),
    ("plat", "flat-s0", "Vague 1 · plat (v1)", False),
    ("curriculum", "curriculum-s0", "Vague 1 · curriculum (v1)", False),
]
_cache: dict = {}
torch.set_num_threads(4)


def models():
    out = []
    for mid, fname, label, rational in CATALOG:
        path = MODELS / f"{fname}.pt"
        if path.exists():
            cfg = _cfg(path)
            out.append({"id": mid, "label": label, "layers": cfg["layers"], "rational": rational,
                        "params": _params(cfg)})
    return out


def _cfg(path):
    key = ("cfg", str(path))
    if key not in _cache:
        _cache[key] = torch.load(path, map_location="cpu", weights_only=False)["config"]
    return _cache[key]


def _params(cfg):
    key = ("params", cfg["layers"])
    if key not in _cache:
        _cache[key] = MathLM(**cfg).parameter_count()
    return _cache[key]


def _load(mid):
    if mid not in _cache:
        for m, fname, _, rational in CATALOG:
            if m == mid:
                blob = torch.load(MODELS / f"{fname}.pt", map_location="cpu", weights_only=False)
                net = MathLM(**blob["config"])
                load_compatible(net, blob["state"])
                net.eval()
                _cache[mid] = (net, rational)
                break
        else:
            raise ValueError(f"modèle inconnu : {mid}")
    return _cache[mid]


def normalize(text: str) -> str:
    s = text.strip()
    for a, b in (("×", "*"), ("·", "*"), ("÷", "/"), (":", "/"), ("−", "-"), ("–", "-"), ("**", "^"), ("sqrt", "√"), ("cbrt", "∛"), ("²", "^2"), ("³", "^3")):
        s = s.replace(a, b)
    return re.sub(r"\s+", "", s)


def _terminal(s, rational):
    try:
        return next_state(s, rational) is None
    except ArithError:
        return False


def solve(expression: str, model_id: str, verified: bool = False) -> dict:
    expr = normalize(expression)
    if not expr or len(expr) > 60:
        raise ValueError("Écrivez un calcul de 60 caractères au plus.")
    try:
        reference = final_state(expr)
    except (ArithError, ZeroDivisionError, ValueError, RecursionError):
        raise ValueError("Expression non reconnue. Essayez par exemple (3+4)*2-5, 2^3+√16, (1/2)+(1/3) ou 2x+6=20.")
    net, rational = _load(model_id)
    t0 = time.time()
    state, steps, status = expr, [], "ok"
    for _ in range(MAX_STEPS):
        if _terminal(state, True) or (not rational and _terminal(state, False)):
            break
        if len(state) + 4 >= MAX_LEN:
            status = "trop long"
            break
        if verified:
            cands = beam_generate(net, [state], beam=8)[0]
            pick = next((c for c in cands if verify_step(state, c)), None)
            nxt = pick if pick is not None else cands[0]
            valid = pick is not None
        else:
            nxt = generate(net, [state])[0]
            valid = verify_step(state, nxt)
        steps.append({"from": state, "to": nxt, "valid": bool(valid)})
        if not valid:
            status = "étape invalide"
            break
        state = nxt
    else:
        status = "trop d'étapes"
    done = status == "ok"
    return {"input": expression, "expression": expr, "model": model_id, "verified": verified, "steps": steps, "final": state if done else None,
            "reference": reference, "correct": bool(done and state == reference), "status": status, "ms": round((time.time() - t0) * 1000)}


def solve_all(expression: str, verified: bool = False) -> list:
    out = []
    for m in models():
        try:
            out.append(solve(expression, m["id"], verified) | {"label": m["label"]})
        except ValueError as error:
            if "Expression" in str(error) or "Écrivez" in str(error):
                raise
            out.append({"model": m["id"], "label": m["label"], "error": str(error)})
    return out


def solve_best(expression: str) -> dict:
    """Essaie les modèles du plus récent au plus ancien, chacun avec proposer + vérifier ; renvoie le premier dont la chaîne entière est valide.
    La réponse vient alors des étapes du réseau, chacune contrôlée par l'évaluateur exact (ce n'est pas le réseau seul)."""
    attempts = []
    for m in models():
        r = solve(expression, m["id"], True) | {"label": m["label"]}
        attempts.append({"model": m["id"], "label": m["label"], "ok": r["correct"], "status": r["status"]})
        if r["correct"]:
            return r | {"attempts": attempts}
    return solve(expression, models()[0]["id"], True) | {"label": models()[0]["label"], "attempts": attempts}

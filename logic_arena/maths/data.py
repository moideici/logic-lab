"""Données de la vague 1 : six niveaux de problèmes, séparation par hachage, encodage caractère par caractère.

Un exemple est (état, étape suivante) : on tire un problème de départ, on déroule sa chaîne de référence (`arith.chain`) et on garde
une étape au hasard. Les états sont répartis entre apprentissage, validation et test par un hachage stable de leur texte, donc un état
de test n'apparaît jamais à l'entraînement, quel que soit le niveau qui l'a produit. Le hors distribution (`ood=True`) dépasse
strictement les bornes de l'entraînement. Protocole : `outputs/verifications/maths-protocole.md`.
"""
from __future__ import annotations

import hashlib
import re
from fractions import Fraction
from math import gcd

import numpy as np

from .arith import ArithError, _lhs2, chain, is_canonical, render

LEVELS = ("N1", "N2", "N3", "N4", "N5", "N6")
LEVELS2 = LEVELS + ("N7", "N8", "N9")  # vague 2, étape 2a
LEVELS3 = LEVELS2 + ("N10",)  # vague 2, étape 2b : équations de puissances, de fractions et de racines
WAVE2 = frozenset(("N7", "N8", "N9", "N10"))
# Les caractères de la vague 2 sont AJOUTÉS en queue : les identifiants de la vague 1 (donc les anciens points de contrôle) ne bougent pas.
VOCAB = ["<pad>"] + list("0123456789+-*/()x=") + [">", "$"] + list("^√∛ ouacnesilt")
CH2ID = {c: i for i, c in enumerate(VOCAB)}
PAD, SEP, EOS = 0, CH2ID[">"], CH2ID["$"]
VOCAB_SIZE = len(VOCAB)
MAX_LEN = 128

_INTS = re.compile(r"\d+")


# ---- séparation ----------------------------------------------------------------------------------------------------------
def split_of(state):
    """'test' (5 %), 'val' (5 %) ou 'train' (90 %), selon un hachage stable (jamais `hash`, qui change d'un lancement à l'autre)."""
    h = int.from_bytes(hashlib.blake2b(state.encode(), digest_size=4).digest(), "big") % 20
    return "test" if h == 0 else "val" if h == 1 else "train"


# ---- tirages -------------------------------------------------------------------------------------------------------------
def rand_num(rng, lo, hi):
    """Entier de [lo, hi] : on tire d'abord le nombre de chiffres, puis le nombre, pour que les petits nombres ne soient pas noyés."""
    dl, dh = len(str(lo)), len(str(hi))
    d = int(rng.integers(dl, dh + 1))
    a, b = max(lo, 10 ** (d - 1) if d > 1 else 0), min(hi, 10 ** d - 1)
    return int(rng.integers(a, b + 1))


def _signed(rng, a, op, b, p=0.3):
    """`a op b` avec chaque opérande négatif avec probabilité p (entraînement élargi : ces cas n'arrivent sinon qu'au détour des étapes de N4 et N5)."""
    a = -a if rng.random() < p else a
    b = -b if rng.random() < p else b
    return render([a, op, b])


def _gen_n1(rng, ood, wide=False):
    lo, hi = (1000, 9999) if ood else (0, 999) if wide else (0, 99)
    a = rand_num(rng, lo, hi)
    op = "+-"[int(rng.integers(2))]
    b = rand_num(rng, lo, hi)
    return _signed(rng, a, op, b, 0.35) if wide else f"{a}{op}{b}"


def _gen_n2(rng, ood, wide=False):
    if wide and rng.random() < 0.5:  # deux facteurs à 2 chiffres : n'existent sinon que dans les étapes de N4 et N5
        return _signed(rng, rand_num(rng, 0, 99), "*", rand_num(rng, 0, 99), 0.25)
    big = rand_num(rng, *((1000, 9999) if ood else (0, 999) if wide else (0, 99)))
    small = rand_num(rng, 0, 12)
    a, b = (big, small) if rng.integers(2) else (small, big)
    return _signed(rng, a, "*", b, 0.25) if wide else f"{a}*{b}"


def _gen_n3(rng, ood, wide=False):
    if wide and rng.random() < 0.5:  # diviseurs jusqu'à 99, dividende jusqu'à 999
        b = rand_num(rng, 1, 99)
        q = rand_num(rng, 0, 999 // b)
    else:
        b = rand_num(rng, 1, 12)
        q = rand_num(rng, *((1000, 9999) if ood else (0, 999) if wide else (0, 99)))
    if not wide:
        return f"{b * q}/{b}"
    a = -b * q if rng.random() < 0.25 else b * q
    return render([a, "/", -b if rng.random() < 0.25 else b])


_OPS = np.array(list("+-*/"))
_OP_P = [0.3, 0.3, 0.25, 0.15]


def _draft(rng, nl, hi, ood):
    """Nombres et opérateurs. Une division sur deux a un dividende multiple du diviseur (sinon elle serait presque toujours rejetée)."""
    lits = [rand_num(rng, 0, hi) for _ in range(nl)]
    ops = [str(rng.choice(_OPS, p=_OP_P)) for _ in range(nl - 1)]
    for i, op in enumerate(ops):
        if op == "/" and rng.random() < 0.6:
            r = rand_num(rng, 2, 12)
            lits[i + 1] = r
            if i == 0 or ops[i - 1] in "+-":
                lits[i] = r * rand_num(rng, 0, max(1, (500 if ood else 99) // r))
    return lits, ops


def _spans(rng, nl, groups):
    """Groupes de parenthèses sur les indices de nombres : emboîtés ou disjoints, jamais croisés, jamais l'expression entière."""
    chosen = []
    for _ in range(40):
        if len(chosen) == groups:
            break
        i = int(rng.integers(0, nl - 1))
        j = int(rng.integers(i + 1, nl))
        if (i, j) == (0, nl - 1) or (i, j) in chosen:
            continue
        if all(j2 < i or j < i2 or (i <= i2 and j2 <= j) or (i2 <= i and j <= j2) for i2, j2 in chosen):
            chosen.append((i, j))
    return chosen


def _render(lits, ops, spans):
    out = []
    for idx, v in enumerate(lits):
        out.append("(" * sum(1 for i, _ in spans if i == idx))
        out.append(str(v))
        out.append(")" * sum(1 for _, j in spans if j == idx))
        if idx < len(ops):
            out.append(ops[idx])
    return "".join(out)


def _gen_expr(rng, ood, parens):
    if parens:
        nl = int(rng.integers(6, 9)) if ood else int(rng.integers(3, 6))
        groups = int(rng.integers(2, 4)) if ood else int(rng.integers(1, 3))
    else:
        nl = int(rng.integers(5, 8)) if ood else int(rng.integers(3, 5))
        groups = 0
    lits, ops = _draft(rng, nl, 50 if ood else 20, ood)
    return _render(lits, ops, _spans(rng, nl, groups) if groups else [])


def _gen_n6(rng, ood):
    if ood:
        a, x, k = rand_num(rng, 13, 30), int(rng.integers(-99, 100)), rand_num(rng, 51, 99)
    else:
        a = 1 if rng.random() < 0.25 else rand_num(rng, 2, 12)
        x, k = int(rng.integers(-20, 21)), rand_num(rng, 1, 50)
    form = ["plus", "minus", "lead"] + (["none"] if a > 1 else [])
    form = form[int(rng.integers(len(form)))]
    ax = "x" if a == 1 else f"{a}x"
    if form == "none":
        return f"{ax}={a * x}"
    if form == "plus":
        return f"{ax}+{k}={a * x + k}"
    if form == "minus":
        return f"{ax}-{k}={a * x - k}"
    return f"{k}+{ax}={k + a * x}"


# ---- vague 2 : puissances, fractions, racines ----------------------------------------------------------------------------
def _build(operands, ops, spans):
    """Jetons d'une expression : opérandes (nombres ou listes de jetons), opérateurs, groupes sur les indices d'opérandes."""
    toks = []
    for idx, v in enumerate(operands):
        toks += ["("] * sum(1 for i, _ in spans if i == idx)
        toks += v if isinstance(v, list) else [v]
        toks += [")"] * sum(1 for _, j in spans if j == idx)
        if idx < len(ops):
            toks.append(ops[idx])
    return toks


def _gen_n7(rng, ood, wide=False):
    """Puissances : seules (40 %) ou dans une expression de 3 à 4 nombres (OOD : 4 à 5) avec `+ - * ^` ; base négative toujours parenthésée."""
    lo, hi = (13, 30) if ood else (0, 12)
    if rng.random() < 0.4:
        base = rand_num(rng, lo, hi) * (-1 if rng.random() < 0.35 else 1)
        return render([base, "^", int(rng.integers(0, 5 if ood else 7))])
    nl = int(rng.integers(4, 6)) if ood else int(rng.integers(3, 5))
    ops = [str(rng.choice(["+", "-", "*", "^"], p=[0.2, 0.2, 0.2, 0.4])) for _ in range(nl - 1)]
    if "^" not in ops:
        ops[int(rng.integers(len(ops)))] = "^"
    operands = []
    for i in range(nl):
        if i > 0 and ops[i - 1] == "^":
            v = int(rng.integers(0, 5))  # exposant littéral
        else:
            v = rand_num(rng, lo, hi)
            if i < len(ops) and ops[i] == "^" and v > 0 and rng.random() < 0.3:
                v = -v
        operands.append(v)
    return render(_build(operands, ops, _spans(rng, nl, 1) if rng.random() < 0.35 else []))


def _rand_frac(rng, ood):
    """Fraction irréductible : numérateur 1 à 12 (OOD 13 à 30), dénominateur 2 à 12 (OOD 13 à 30), négative une fois sur trois."""
    while True:
        p, q = rand_num(rng, *((13, 30) if ood else (1, 12))), rand_num(rng, *((13, 30) if ood else (2, 12)))
        if gcd(p, q) == 1:
            return Fraction(-p if rng.random() < 0.3 else p, q)


def _frac_operand(rng, ood, p_frac=0.65):
    if rng.random() < p_frac:
        return _rand_frac(rng, ood)
    return rand_num(rng, *((13, 30) if ood else (1, 12))) * (-1 if rng.random() < 0.25 else 1)


def _gen_n8(rng, ood, wide=False):
    r = rng.random()
    if r < 0.15:  # division nue : entiers non divisibles donnent un atome
        return render([rand_num(rng, *((100, 999) if ood else (1, 99))), "/", rand_num(rng, *((13, 30) if ood else (2, 12)))])
    if r < 0.4:
        a, b = _frac_operand(rng, ood), _frac_operand(rng, ood)
        if not (isinstance(a, Fraction) or isinstance(b, Fraction)):
            a = _rand_frac(rng, ood)
        return render([a, str(rng.choice(["+", "-", "*", "/"])), b])
    if r < 0.95:
        nl = 4 if ood and rng.random() < 0.5 else 3
        ops = [str(rng.choice(["+", "-", "*", "/"])) for _ in range(nl - 1)]
        operands = [_frac_operand(rng, ood) for _ in range(nl)]
        if not any(isinstance(v, Fraction) for v in operands):
            operands[int(rng.integers(nl))] = _rand_frac(rng, ood)
        return render(_build(operands, ops, _spans(rng, nl, 1) if rng.random() < 0.4 else []))
    return render([_rand_frac(rng, ood), "^", int(rng.integers(2, 4))])


def _root_term(rng, ood):
    """Jetons d'un terme avec racine dont le résultat est exact : `√n`, `√(a+b)`, `√(a*b)`, `∛n`, `∛(-n)`, ou racine d'une fraction."""
    kind = rng.random()
    if kind < 0.7:  # racine carrée d'un carré parfait, écrit tel quel ou comme groupe
        k = rand_num(rng, *((21, 30) if ood else (0, 20)))
        n = k * k
        form = rng.random()
        if form < 0.4:
            return ["√", n]
        if form < 0.7:
            a = int(rng.integers(0, n + 1))
            return ["√", "(", a, "+", n - a, ")"]
        if form < 0.85:
            a = int(rng.integers(0, 31))
            return ["√", "(", n + a, "-", a, ")"]
        divisors = [d for d in range(1, n + 1) if n % d == 0] if n else [1]
        d = divisors[int(rng.integers(len(divisors)))]
        return ["√", "(", d, "*", n // d if n else 0, ")"]
    if kind < 0.9:  # racine cubique, cube positif ou négatif
        c = rand_num(rng, *((11, 15) if ood else (0, 10))) * (-1 if rng.random() < 0.4 else 1)
        return ["∛", c ** 3]
    while True:  # racine carrée d'une fraction parfaite
        p, q = rand_num(rng, 1, 12), rand_num(rng, 2, 12)
        if gcd(p, q) == 1:
            return ["√", Fraction(p * p, q * q)]


def _gen_n9(rng, ood, wide=False):
    r = rng.random()
    if r < 0.35:
        return render(_root_term(rng, ood))
    nt = int(rng.integers(3, 5)) if ood else int(rng.integers(2, 4))
    operands = [_root_term(rng, ood) if rng.random() < 0.6 else rand_num(rng, 0, 20) for _ in range(nt)]
    if not any(isinstance(o, list) for o in operands):
        operands[0] = _root_term(rng, ood)
    ops = [str(rng.choice(["+", "-", "*", "/"], p=[0.35, 0.3, 0.25, 0.1])) for _ in range(nt - 1)]
    return render(_build(operands, ops, []))


def _eq_const(rng, ood):
    """(constante signée, en tête ?) : 0 = pas de constante, sinon `+k`, `-k` ou `k+...`."""
    form = ("none", "plus", "minus", "lead")[int(rng.integers(4))]
    k = rand_num(rng, *((31, 99) if ood else (1, 30)))
    return {"none": (0, False), "plus": (k, False), "minus": (-k, False), "lead": (k, True)}[form]


def _gen_n10(rng, ood, wide=False):
    """Équations à une inconnue : puissances (`3x^2+5=53`, `x^3=-27`), fractions (`x/3+2=5`, `(2/3)x=4`), racines (`2√x+1=9`, `√(x+3)=5`).
    Solutions entières ; environ 15 % des équations n'ont pas de solution (carré ou racine égale à un négatif)."""
    fam = rng.random()
    nosol = rng.random() < 0.15
    if fam < 0.4:  # puissances
        n = 3 if rng.random() < 0.2 else 2
        a = 1 if rng.random() < 0.3 else rand_num(rng, *((10, 20) if ood else (2, 9)))
        k, lead = _eq_const(rng, ood)
        if n == 2 and nosol:
            v = -a * rand_num(rng, 1, 30)
        elif n == 2:
            v = a * rand_num(rng, *((13, 30) if ood else (0, 12))) ** 2
        else:
            v = a * rand_num(rng, *((7, 12) if ood else (0, 6))) ** 3 * (-1 if rng.random() < 0.5 else 1)
        return f"{_lhs2('pow', {'a': a, 'n': n}, k, lead)}={v + k}"
    if fam < 0.7:  # fractions
        k, lead = _eq_const(rng, ood)
        m = int(rng.integers(13, 31) if ood else rng.integers(-12, 13)) * (1 if not ood or rng.random() < 0.5 else -1)
        if rng.random() < 0.5:
            a = rand_num(rng, *((13, 20) if ood else (2, 12)))
            return f"{_lhs2('div', {'a': a}, k, lead)}={m + k}"
        while True:
            p, q = rand_num(rng, *((10, 20) if ood else (1, 9))), rand_num(rng, *((10, 20) if ood else (2, 9)))
            if gcd(p, q) == 1:
                break
        p *= -1 if rng.random() < 0.3 else 1
        return f"{_lhs2('frc', {'p': p, 'q': q}, k, lead)}={p * m + k}"
    if rng.random() < 0.35:  # racine d'un groupe : √(x+b)=c
        b = rand_num(rng, 1, 30) * (-1 if rng.random() < 0.5 else 1)
        c = -rand_num(rng, 1, 15) if nosol else rand_num(rng, *((16, 30) if ood else (0, 15)))
        return f"{_lhs2('rgrp', {'b': b}, 0, False)}={c}"
    a = 1 if rng.random() < 0.5 else rand_num(rng, 2, 9)
    k, lead = _eq_const(rng, ood)
    if nosol:
        k, lead = 0, False
        v = -a * rand_num(rng, 1, 15)
    else:
        v = a * rand_num(rng, *((16, 30) if ood else (0, 15)))
    return f"{_lhs2('root', {'a': a}, k, lead)}={v + k}"


_GEN = {"N1": _gen_n1, "N2": _gen_n2, "N3": _gen_n3, "N6": lambda rng, ood, wide: _gen_n6(rng, ood),
        "N4": lambda rng, ood, wide: _gen_expr(rng, ood, False), "N5": lambda rng, ood, wide: _gen_expr(rng, ood, True),
        "N7": _gen_n7, "N8": _gen_n8, "N9": _gen_n9, "N10": _gen_n10}
# plus grand nombre admis dans toute la chaîne (entraînement, hors distribution) ; N1 à N3 et N6 ne sont pas bornés
BOUNDS = {"N4": (999, 9999), "N5": (999, 9999), "N7": (9999, 999999), "N8": (999, 9999), "N9": (999, 9999), "N10": (9999, 99999)}
RATIONAL = frozenset(("N8", "N9", "N10"))  # division non exacte admise : elle donne un atome fraction


def _bounded(traj, bound):
    return all(int(m) <= bound for s in traj for m in _INTS.findall(s))


def gen_problem(rng, level, ood=False, wide=False):
    """(départ, chaîne de référence). Rejette les divisions inexactes (hors N8 et N9), les nombres trop grands et les écritures non canoniques.

    `wide` n'élargit que l'ENTRAÎNEMENT de N1, N2 et N3 (opérandes, facteurs et quotients jusqu'à 999, deux facteurs à 2 chiffres, diviseurs jusqu'à 99, opérandes négatifs) : l'espace d'entrée de N2 et N3 est
    minuscule, et les opérandes à 3 chiffres de N1 servent aux étapes de N4 et N5. Validation et test gardent les plages du protocole, et leurs états restent exclus de l'entraînement par le hachage."""
    for _ in range(2000):
        start = _GEN[level](rng, ood, wide)
        try:
            traj = chain(start, rational=level in RATIONAL)
        except ArithError:
            continue
        if level in BOUNDS and not _bounded(traj, BOUNDS[level][int(ood)]):
            continue
        if level in WAVE2 and not is_canonical(start):
            continue
        return start, traj
    raise RuntimeError(f"aucun problème valide pour {level}")


def sample_step(rng, level, ood=False, split=None, wide=False):
    """(état, étape suivante) ; `split` impose la séparation de l'état d'entrée."""
    for _ in range(400):
        _, traj = gen_problem(rng, level, ood, wide)
        t = int(rng.integers(len(traj) - 1))
        if split is None or ood or split_of(traj[t]) == split:
            return traj[t], traj[t + 1]
    raise RuntimeError(f"aucun exemple {split} pour {level}")


def sample_start(rng, level, ood=False, split=None):
    """(départ, chaîne) dont le texte de départ est dans `split`."""
    for _ in range(400):
        start, traj = gen_problem(rng, level, ood)
        if split is None or ood or split_of(start) == split:
            return start, traj
    raise RuntimeError(f"aucun départ {split} pour {level}")


def make_steps(level, n, seed, split="train", ood=False, distinct=False, wide=False):
    """n couples (état, étape). `distinct` : états tous différents (évaluation) ; s'arrête avant n si l'espace est plus petit."""
    rng = np.random.default_rng(seed)
    out, seen, misses = [], set(), 0
    while len(out) < n and misses < 3000:
        inp, nxt = sample_step(rng, level, ood, split, wide)
        if distinct and inp in seen:
            misses += 1
            continue
        seen.add(inp)
        out.append((inp, nxt))
    return out


def make_starts(level, n, seed, split="test", ood=False):
    rng = np.random.default_rng(seed)
    out, seen, misses = [], set(), 0
    while len(out) < n and misses < 3000:
        start, _ = sample_start(rng, level, ood, split)
        if start in seen:
            misses += 1
            continue
        seen.add(start)
        out.append(start)
    return out


# ---- encodage ------------------------------------------------------------------------------------------------------------
def encode_prompt(inp):
    return [CH2ID[c] for c in inp] + [SEP]


def encode_pair(inp, out):
    return encode_prompt(inp) + [CH2ID[c] for c in out] + [EOS]


def decode(ids):
    """Texte jusqu'au premier `$` (exclu)."""
    out = []
    for i in ids:
        if i == EOS:
            break
        if i != PAD:
            out.append(VOCAB[i])
    return "".join(out)


def encode_pairs(pairs, max_len=MAX_LEN):
    """(X, plen) : X (n, max_len) uint8 rempli de PAD ; plen = longueur de « état> » (la sortie commence à cet indice)."""
    X = np.zeros((len(pairs), max_len), dtype=np.uint8)
    plen = np.zeros(len(pairs), dtype=np.int16)
    for r, (inp, out) in enumerate(pairs):
        ids = encode_pair(inp, out)
        if len(ids) > max_len:
            raise ValueError(f"exemple trop long : {inp} -> {out}")
        X[r, :len(ids)] = ids
        plen[r] = len(inp) + 1
    return X, plen

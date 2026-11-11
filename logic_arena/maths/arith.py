"""Arithmétique pas à pas : réécriture de référence, évaluateur indépendant et vérification d'une étape.

Un état est une chaîne : une expression (`2+3*4`, `(2+3)*4`, `2^3+√16`, `(1/2)+(1/3)`) ou une équation à une inconnue (`3x+5=20`).
`next_state` réduit **une seule opération** selon la règle de référence : parenthèses d'abord ; dans une suite sans parenthèse, la première
racine dont l'argument est un nombre, puis la première puissance dont l'exposant est un nombre non suivi d'un `^` (associativité à droite),
puis `*` et `/` de gauche à droite, puis `+` et `-`. `chain` donne la suite complète jusqu'à l'état terminal (un nombre ou `x=nombre`).

Notation (vague 2) : un nombre non entier est un **atome fraction** `(p/q)` irréductible, q au moins 2, toujours entre parenthèses ; une
base négative devant `^` est toujours entre parenthèses (`(-2)^3`). Avec `rational=False` (vague 1), une division non exacte est une erreur ;
avec `rational=True`, elle donne l'atome (`3/4` → `(3/4)`).

La règle de référence (jetons, `step`) et l'évaluateur (`value`, `solve_eq`, descente récursive sur les caractères) sont écrits
séparément : `verify_step` juge une étape proposée par un réseau avec l'évaluateur, pas avec la règle de référence. Une étape
valide conserve la valeur (ou la solution) et retire exactement une opération, sans imposer le choix de la référence. Seule la notation
des atomes fractions (`_frac_atom`) est partagée, parce qu'elle fait partie de la définition de la langue.
"""
from __future__ import annotations

import re
from fractions import Fraction
from math import gcd

BIN = "+-*/^"
ROOTS = "√∛"
ROOT_SET = frozenset(ROOTS)
DIGITS = frozenset("0123456789")
MAX_EXPONENT = 12
_LHS = re.compile(r"^(?:(\d+)\+)?(\d*)x(?:([+-])(\d+))?$")
_NEG = re.compile(r"-(\d+)")
_NEG_PAREN = re.compile(r"\(-(\d+)\)")
_FRAC_ATOM = re.compile(r"\((-?\d+)/(\d+)\)")


class ArithError(ValueError):
    pass


def _isop(t):
    return isinstance(t, str) and t in BIN


def _isroot(t):
    return isinstance(t, str) and t in ROOT_SET


def _isnum(t):
    return isinstance(t, (int, Fraction)) and not isinstance(t, bool)


def _frac_atom(s, i):
    """(Fraction, fin) si `s[i:]` commence par un atome fraction `(p/q)` irréductible avec q au moins 2, sinon None."""
    m = _FRAC_ATOM.match(s, i)
    if not m:
        return None
    p, q = int(m.group(1)), int(m.group(2))
    if q < 2 or gcd(abs(p), q) != 1:
        return None
    return Fraction(p, q), m.end()


# ---- jetons --------------------------------------------------------------------------------------------------------------
def _check(toks):
    depth, want = 0, True
    for t in toks:
        if want:
            if _isnum(t):
                want = False
            elif t == "(":
                depth += 1
            elif _isroot(t):
                pass
            else:
                raise ArithError("opérande attendu")
        elif _isop(t):
            want = True
        elif t == ")":
            depth -= 1
            if depth < 0:
                raise ArithError("parenthèse fermante en trop")
        else:
            raise ArithError("opérateur attendu")
    if want or depth:
        raise ArithError("expression incomplète")


def tokenize(s):
    """Chaîne -> jetons (entiers, fractions, opérateurs, racines, parenthèses).

    `-` est un signe au début ou après `(` ; `(-n)` est un entier négatif après un opérateur ou une racine, ou devant `^` ;
    `(p/q)` irréductible est un atome fraction."""
    toks, i, n = [], 0, len(s)
    while i < n:
        ch = s[i]
        if ch in DIGITS:
            j = i
            while j < n and s[j] in DIGITS:
                j += 1
            toks.append(int(s[i:j]))
            i = j
            continue
        if ch in "+*/^" or ch in ROOT_SET:
            toks.append(ch)
        elif ch == "-":
            if not toks or toks[-1] == "(":
                m = _NEG.match(s, i)
                if not m:
                    raise ArithError("signe sans nombre")
                toks.append(-int(m.group(1)))
                i = m.end()
                continue
            toks.append("-")
        elif ch == "(":
            fa = _frac_atom(s, i)
            if fa:
                toks.append(fa[0])
                i = fa[1]
                continue
            m = _NEG_PAREN.match(s, i)
            if m and ((toks and (_isop(toks[-1]) or _isroot(toks[-1]))) or s[m.end():m.end() + 1] == "^"):
                toks.append(-int(m.group(1)))
                i = m.end()
                continue
            toks.append("(")
        elif ch == ")":
            toks.append(")")
        else:
            raise ArithError(f"caractère inconnu : {ch!r}")
        i += 1
    _check(toks)
    return toks


def render(toks):
    """Jetons -> chaîne canonique. Un négatif s'écrit `(-n)` après un opérateur ou une racine, et devant `^` ; une fraction `(p/q)`."""
    out, prev = [], None
    for k, t in enumerate(toks):
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        if isinstance(t, Fraction):
            out.append(f"({t.numerator}/{t.denominator})")
        elif isinstance(t, int):
            out.append(f"(-{-t})" if t < 0 and (_isop(prev) or _isroot(prev) or nxt == "^") else str(t))
        else:
            out.append(t)
        prev = t
    return "".join(out)


# ---- calcul exact --------------------------------------------------------------------------------------------------------
def _norm(v):
    v = Fraction(v)
    return int(v) if v.denominator == 1 else v


def _iroot(m, n):
    r = round(m ** (1.0 / n))
    for c in (r - 1, r, r + 1):
        if c >= 0 and c ** n == m:
            return c
    return None


def _root_val(sym, v):
    v = Fraction(v)
    n = 2 if sym == "√" else 3
    if n == 2 and v < 0:
        raise ArithError("racine carrée d'un négatif")
    sign = -1 if v < 0 else 1
    v = abs(v)
    p, q = _iroot(v.numerator, n), _iroot(v.denominator, n)
    if p is None or q is None:
        raise ArithError("racine non exacte")
    return Fraction(sign * p, q)


def _pow_val(a, b):
    a, b = Fraction(a), Fraction(b)
    if b.denominator != 1 or b < 0 or b > MAX_EXPONENT:
        raise ArithError("exposant non admis")
    if a == 0 and b == 0:
        raise ArithError("0^0")
    return a ** int(b)


def _apply(a, op, b, rational):
    if isinstance(a, int) and isinstance(b, int) and op in "+-*":
        return a + b if op == "+" else a - b if op == "-" else a * b
    if op == "+":
        r = Fraction(a) + Fraction(b)
    elif op == "-":
        r = Fraction(a) - Fraction(b)
    elif op == "*":
        r = Fraction(a) * Fraction(b)
    elif op == "/":
        if b == 0:
            raise ArithError("division par zéro")
        r = Fraction(a) / Fraction(b)
        if not rational and r.denominator != 1:
            raise ArithError("division non exacte")
    else:
        r = _pow_val(a, b)
    return _norm(r)


# ---- gabarits des opérations sur fractions (amendement du protocole vague 2) --------------------------------------------------
# Une opération dont un opérande est une fraction non entière n'est plus faite en un seul pas : elle est d'abord RÉÉCRITE en un groupe
# `(numérateur/dénominateur)` d'opérations sur des entiers (aucun calcul, seulement recopier), puis réduite par les pas ordinaires.
# Le groupe entoure toujours le gabarit : il se lit comme un seul opérande quel que soit le voisinage (`2/(1^2/3^2)`).
def _is_frac(t):
    return isinstance(t, Fraction) and t.denominator != 1


def _template(a, op, b):
    """Jetons du gabarit de `a op b` (op dans `+-*/^`), ou de la racine `a` si `op` est un symbole de racine (`b` ignoré)."""
    x = Fraction(a)
    na, da = x.numerator, x.denominator
    if op in ROOT_SET:
        return ["(", op, na, "/", op, da, ")"]
    y = Fraction(b)
    nc, dc = y.numerator, y.denominator
    if op in "+-":
        if da > 1 and dc > 1:
            return ["(", "(", na, "*", dc, op, nc, "*", da, ")", "/", "(", da, "*", dc, ")", ")"]
        if da > 1:
            return ["(", "(", na, op, nc, "*", da, ")", "/", da, ")"]
        return ["(", "(", na, "*", dc, op, nc, ")", "/", dc, ")"]
    if op == "*":
        if da > 1 and dc > 1:
            return ["(", na, "*", nc, "/", "(", da, "*", dc, ")", ")"]
        return ["(", na, "*", nc, "/", da * dc, ")"]
    if op == "/":  # a/b : c/d = a·d / b·c ; le dénominateur est rendu positif en changeant le signe du numérateur
        sg = -1 if nc < 0 else 1
        if da > 1 and dc > 1:
            return ["(", sg * na, "*", dc, "/", "(", da, "*", abs(nc), ")", ")"]
        if da > 1:
            return ["(", sg * na, "/", "(", da, "*", abs(nc), ")", ")"]
        return ["(", sg * na, "*", dc, "/", abs(nc), ")"]
    return ["(", na, "^", int(y), "/", da, "^", int(y), ")"]


# ---- règle de référence --------------------------------------------------------------------------------------------------
def _reduce_one(seg, rational=False):
    for k, t in enumerate(seg):  # 1. première racine dont l'argument est un nombre
        if _isroot(t) and k + 1 < len(seg) and _isnum(seg[k + 1]):
            v = _norm(_root_val(t, seg[k + 1]))
            return seg[:k] + (_template(seg[k + 1], t, None) if _is_frac(seg[k + 1]) else [v]) + seg[k + 2:]
    for k, t in enumerate(seg):  # 2. première puissance dont l'exposant est un nombre non suivi d'un `^`
        if t == "^" and _isnum(seg[k + 1]) and not (k + 2 < len(seg) and seg[k + 2] == "^"):
            v = _apply(seg[k - 1], "^", seg[k + 1], rational)
            return seg[:k - 1] + (_template(seg[k - 1], "^", seg[k + 1]) if _is_frac(seg[k - 1]) else [v]) + seg[k + 2:]
    k = next((i for i, t in enumerate(seg) if t == "*" or t == "/"), None)  # 3. `*` et `/`, 4. `+` et `-`
    if k is None:
        k = next(i for i, t in enumerate(seg) if t == "+" or t == "-")
    v = _apply(seg[k - 1], seg[k], seg[k + 1], rational)  # valide l'opération (division par zéro, exposant, exactitude)
    if _is_frac(seg[k - 1]) or _is_frac(seg[k + 1]):
        return seg[:k - 1] + _template(seg[k - 1], seg[k], seg[k + 1]) + seg[k + 2:]
    return seg[:k - 1] + [v] + seg[k + 2:]


def _omega(g):
    """Nombre de facteurs premiers de `g`, avec multiplicité."""
    k, p = 0, 2
    while g > 1:
        while g % p == 0:
            g //= p
            k += 1
        p += 1
    return k


def _prime_step(seg, rational):
    """Amendement 2 : un groupe `(N/D)` d'entiers, non entier et réductible, se simplifie par UN facteur premier commun à la fois (le plus
    petit) : `(405/324)` -> `(135/108)` -> `(45/36)` -> `(15/12)` -> `(5/4)`. Division exacte et dénominateur négatif : inchangés."""
    if not rational or len(seg) != 3 or seg[1] != "/" or not all(isinstance(t, int) for t in (seg[0], seg[2])):
        return None
    n, d = seg[0], seg[2]
    if d < 2 or n % d == 0:
        return None
    g = gcd(abs(n), d)
    if g == 1:
        return None
    p = next(q for q in range(2, g + 1) if g % q == 0)
    return [n // p, "/", d // p]


def _close_of(toks, i):
    depth = 0
    for j in range(i, len(toks)):
        if toks[j] == "(":
            depth += 1
        elif toks[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return -1


def step(toks, rational=False):
    """Une opération de moins. None si `toks` est déjà un nombre."""
    if len(toks) == 1:
        return None
    if ")" in toks:
        j = toks.index(")")
        i = j - 1 - toks[:j][::-1].index("(")
        seg = toks[i + 1:j]
        if len(seg) > 1:
            pr = _prime_step(seg, rational)
            if pr is not None:
                return toks[:i + 1] + pr + toks[j:]
            seg = _reduce_one(seg, rational)
            if seg[0] == "(" and _close_of(seg, 0) == len(seg) - 1:  # le gabarit remplit tout le groupe : on garde une seule paire
                seg = seg[1:-1]
        if len(seg) == 1:
            return toks[:i] + seg + toks[j + 1:]
        return toks[:i + 1] + seg + toks[j:]
    return _reduce_one(toks, rational)


# ---- équations -----------------------------------------------------------------------------------------------------------
def parse_eq(s):
    """`ax+b=c` -> (a, k, constante_en_tête, jetons du membre droit) avec membre gauche = a·x + k."""
    if s.count("=") != 1:
        raise ArithError("une seule égalité attendue")
    left, right = s.split("=")
    m = _LHS.match(left)
    if not m:
        raise ArithError("membre gauche non reconnu")
    lead, coef, sign, tail = m.groups()
    if lead is not None and tail is not None:
        raise ArithError("deux constantes")
    a = int(coef) if coef else 1
    if a < 1:
        raise ArithError("coefficient nul")
    if lead is not None:
        k = int(lead)
    elif tail is not None:
        k = int(tail) if sign == "+" else -int(tail)
    else:
        k = 0
    return a, k, lead is not None, tokenize(right)


def _fmt_lhs(a, k, lead):
    ax = "x" if a == 1 else f"{a}x"
    if k == 0:
        return ax
    if lead:
        return f"{k}+{ax}"
    return f"{ax}{'+' if k > 0 else '-'}{abs(k)}"


def _no_fractions(toks, rational):
    """Mode vague 1 : `(27/11)` après une réduction est une division non exacte, pas un nombre."""
    if not rational and any(isinstance(t, Fraction) for t in toks):
        raise ArithError("division non exacte")


def _eq_step(s, rational=False):
    a, k, lead, rhs = parse_eq(s)
    _no_fractions(rhs, rational)
    if len(rhs) > 1:
        return f"{_fmt_lhs(a, k, lead)}={render(step(rhs, rational))}"
    c = rhs[0]
    if k != 0:
        return f"{_fmt_lhs(a, 0, False)}={render([c, '-' if k > 0 else '+', abs(k)])}"
    if a != 1:
        return f"x={render([c, '/', a])}"
    return None


# ---- équations de la vague 2 : puissances, fractions, racines -------------------------------------------------------------
NO_SOLUTION = "aucune solution"
_P = r"(?:(\d+)\+)?"        # constante en tête : `b+...`
_T = r"(?:([+-])(\d+))?"     # constante en queue : `...+b`, `...-b`
_EQ2 = {
    "pow": re.compile(rf"^{_P}(\d*)x\^([23]){_T}$"),
    "div": re.compile(rf"^{_P}x/(\d+){_T}$"),
    "frc": re.compile(rf"^{_P}\((-?\d+)/(\d+)\)x{_T}$"),
    "root": re.compile(rf"^{_P}(\d*)√x{_T}$"),
    "rgrp": re.compile(r"^√\(x([+-])(\d+)\)$"),
}


def _parse_lhs2(left):
    """(genre, paramètres, k, constante_en_tête) pour `ax^2+b`, `x/a+b`, `(p/q)x+b`, `a√x+b`, `√(x+b)`, sinon None."""
    for kind in ("pow", "div", "frc", "root"):
        m = _EQ2[kind].match(left)
        if not m:
            continue
        g = m.groups()
        lead, tail = g[0], (g[-2], g[-1])
        if lead is not None and tail[1] is not None:
            raise ArithError("deux constantes")
        k = int(lead) if lead is not None else (int(tail[1]) * (1 if tail[0] == "+" else -1) if tail[1] is not None else 0)
        if kind == "pow":
            par = {"a": int(g[1]) if g[1] else 1, "n": int(g[2])}
            if par["a"] < 1:
                raise ArithError("coefficient nul")
        elif kind == "div":
            par = {"a": int(g[1])}
            if par["a"] < 2:
                raise ArithError("diviseur trivial")
        elif kind == "frc":
            p, q = int(g[1]), int(g[2])
            if q < 2 or gcd(abs(p), q) != 1:
                raise ArithError("coefficient fraction non réduit")
            par = {"p": p, "q": q}
        else:
            par = {"a": int(g[1]) if g[1] else 1}
            if par["a"] < 1:
                raise ArithError("coefficient nul")
        return kind, par, k, lead is not None
    m = _EQ2["rgrp"].match(left)
    if m:
        return "rgrp", {"b": int(m.group(2)) * (1 if m.group(1) == "+" else -1)}, 0, False
    return None


def _lhs2(kind, par, k, lead):
    if kind == "rgrp":
        return f"√(x{'+' if par['b'] > 0 else '-'}{abs(par['b'])})"
    core = {"pow": lambda: ("x" if par["a"] == 1 else f"{par['a']}x") + f"^{par['n']}",
            "div": lambda: f"x/{par['a']}",
            "frc": lambda: f"({par['p']}/{par['q']})x",
            "root": lambda: ("" if par["a"] == 1 else str(par["a"])) + "√x"}[kind]()
    if k == 0:
        return core
    return f"{k}+{core}" if lead else f"{core}{'+' if k > 0 else '-'}{abs(k)}"


def _fmt_val(v):
    return render([_norm(v)])


def _fmt_solutions(sols):
    if not sols:
        return NO_SOLUTION
    return " ou ".join(f"x={_fmt_val(v)}" for v in sorted(sols, reverse=True))


def _eq2_step(s, parsed):
    left, right = s.split("=")
    kind, par, k, lead = parsed
    rhs = tokenize(right)
    if len(rhs) > 1:
        return f"{left}={render(step(rhs, True))}"
    c = rhs[0]
    if kind == "rgrp":
        if c < 0:
            return NO_SOLUTION
        return f"x{'+' if par['b'] > 0 else '-'}{abs(par['b'])}={render([c, '^', 2])}"
    if k != 0:
        return f"{_lhs2(kind, par, 0, False)}={render([c, '-' if k > 0 else '+', abs(k)])}"
    if kind == "pow" and par["a"] != 1:
        return f"x^{par['n']}={render([c, '/', par['a']])}"
    if kind == "div":
        return f"x={render([c, '*', par['a']])}"
    if kind == "frc":
        return f"x={render([c, '/', Fraction(par['p'], par['q'])])}"
    if kind == "root" and par["a"] != 1:
        return f"√x={render([c, '/', par['a']])}"
    if kind == "pow":
        if par["n"] == 3:
            return f"x={_fmt_val(_root_val('∛', c))}"
        if c < 0:
            return NO_SOLUTION
        if c == 0:
            return "x=0"
        r = _root_val("√", c)
        return f"x={_fmt_val(r)} ou x={_fmt_val(-r)}"
    if c < 0:  # racine : √x = c
        return NO_SOLUTION
    return f"x={render([c, '^', 2])}"


def next_state(s, rational=False):
    """État suivant (une opération réduite), None si `s` est terminal. Lève ArithError sur une entrée invalide ou une opération non admise."""
    if s == NO_SOLUTION or " ou " in s:
        return None
    if "=" in s:
        parsed = _parse_lhs2(s.split("=")[0]) if s.count("=") == 1 else None
        return _eq2_step(s, parsed) if parsed else _eq_step(s, rational)
    toks = tokenize(s)
    _no_fractions(toks, rational)
    t = step(toks, rational)
    return None if t is None else render(t)


def chain(s, limit=60, rational=False):
    out = [s]
    while True:
        n = next_state(out[-1], rational)
        if n is None:
            return out
        out.append(n)
        if len(out) > limit:
            raise ArithError("trop d'étapes")


def _trivial_group(toks):
    """Groupe réduit à un seul nombre, `(12)` : la règle de référence ne le produit jamais."""
    return any(toks[i] == "(" and _isnum(toks[i + 1]) and toks[i + 2] == ")" for i in range(len(toks) - 2))


def _canon_rhs(right):
    toks = tokenize(right)
    return not _trivial_group(toks) and render(toks) == right


def _canon_eq(s):
    if s == NO_SOLUTION:
        return True
    if " ou " in s:
        parts = s.split(" ou ")
        if len(parts) != 2 or not all(p.startswith("x=") and _canon_rhs(p[2:]) and len(tokenize(p[2:])) == 1 for p in parts):
            return False
        return " ou ".join(parts) == _fmt_solutions(solset(s))
    if s.count("=") != 1:
        return False
    left, right = s.split("=")
    parsed = _parse_lhs2(left)
    if parsed:
        return _lhs2(*parsed) == left and _canon_rhs(right)
    a, k, lead, rhs = parse_eq(s)
    return not _trivial_group(rhs) and f"{_fmt_lhs(a, k, lead)}={render(rhs)}" == s


def is_canonical(s):
    try:
        if "=" in s or s == NO_SOLUTION:
            return _canon_eq(s)
        toks = tokenize(s)
        return not _trivial_group(toks) and render(toks) == s
    except ArithError:
        return False


# ---- évaluateur indépendant (descente récursive sur les caractères) --------------------------------------------------------
def _cost(op, x, y=None):
    """Nombre de pas que coûte une opération selon l'amendement des fractions : 1 si les opérandes sont entiers ; sinon 1 (la réécriture
    en gabarit) + les opérations du gabarit + 1 si le groupe `(N/D)` obtenu n'est pas déjà un atome irréductible (alors la division finale
    est un pas à part ; sinon elle disparaît à la fermeture de la parenthèse). Calculé ici sur les VALEURS des opérandes, sans la règle de
    référence."""
    x = Fraction(x)
    if y is not None:
        y = Fraction(y)
    if x.denominator == 1 and (y is None or y.denominator == 1):
        return 1
    a, b = x.numerator, x.denominator
    if op in ROOT_SET:
        inner, num, den = 2, _iroot(abs(a), 2 if op == "√" else 3) * (-1 if a < 0 else 1), _iroot(b, 2 if op == "√" else 3)
    else:
        c, d = y.numerator, y.denominator
        if op in "+-":
            s = 1 if op == "+" else -1
            inner = 4 if b > 1 and d > 1 else 2
            num, den = a * d + s * c * b, b * d
        elif op == "*":
            inner, num, den = (2 if b > 1 and d > 1 else 1), a * c, b * d
        elif op == "/":
            inner = 2 if b > 1 and d > 1 else 1
            num, den = a * d * (-1 if c < 0 else 1), b * abs(c)
        else:
            inner, num, den = 2, a ** int(y), b ** int(y)
    return 1 + inner + _tail(num, den)


def _tail(num, den):
    """Pas restants une fois le groupe `(num/den)` formé : 0 si c'est déjà un atome irréductible, 1 si la division est exacte, sinon un
    pas par facteur premier du pgcd (amendement 2)."""
    if den >= 2 and gcd(abs(num), den) == 1:
        return 0
    if num % den == 0:
        return 1
    return _omega(gcd(abs(num), den))


class _Calc:
    """Évalue en Fractions exactes ; `lin=True` autorise `x` et renvoie des formes a·x + b sous forme de couples.

    Grammaire : expr = ['-'] terme (('+'|'-') terme)* ; terme = puissance (('*'|'/') puissance)* ; puissance = atome ['^' puissance] ;
    atome = nombre | atome fraction | '(' expr ')' | racine atome."""

    def __init__(self, s, lin=False):
        self.s, self.i, self.ops, self.lin = s, 0, 0, lin
        self.div = None  # dernière division d'entiers non entière : (début, fin, numérateur, dénominateur), pour l'absorption par le groupe

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def _num(self, v):
        return (Fraction(0), v) if self.lin else v

    def _const(self, p):
        if not self.lin:
            return p
        if p[0] != 0:
            raise ArithError("équation non linéaire")
        return p[1]

    def _add(self, p, q, sign):
        return (p[0] + sign * q[0], p[1] + sign * q[1]) if self.lin else p + sign * q

    def _mul(self, p, q):
        if not self.lin:
            return p * q
        if p[0] != 0 and q[0] != 0:
            raise ArithError("équation non linéaire")
        return (p[0] * q[1] + q[0] * p[1], p[1] * q[1])

    def _div(self, p, q):
        if self.lin:
            if q[0] != 0 or q[1] == 0:
                raise ArithError("division invalide")
            return (p[0] / q[1], p[1] / q[1])
        if q == 0:
            raise ArithError("division par zéro")
        return p / q

    def expr(self):
        neg = self.peek() == "-"
        if neg:
            self.i += 1
        v = self.term()
        if neg:
            v = self._add(self._num(Fraction(0)), v, -1)
        while self.peek() in ("+", "-"):
            sign = 1 if self.peek() == "+" else -1
            self.i += 1
            w = self.term()
            if not self.lin:
                self.ops += _cost("+" if sign == 1 else "-", v, w)
            v = self._add(v, w, sign)
        return v

    def term(self):
        start = self.i
        v = self.power()
        while self.peek() in ("*", "/"):
            op = self.peek()
            self.i += 1
            w = self.power()
            if not self.lin:
                if op == "/" and w == 0:
                    raise ArithError("division par zéro")
                self.ops += _cost(op, v, w)
                if op == "/" and v.denominator == 1 and w.denominator == 1 and (v / w).denominator != 1:
                    self.div = (start, self.i, v.numerator, w.numerator)
            v = self._mul(v, w) if op == "*" else self._div(v, w)
        return v

    def power(self):
        v = self.atom()
        if self.peek() == "^":
            self.i += 1
            e = self.power()
            r = _pow_val(self._const(v), self._const(e))
            if not self.lin:
                self.ops += _cost("^", v, e)
            v = self._num(r)
        return v

    def atom(self):
        c = self.peek()
        if c != "" and c in ROOT_SET:
            self.i += 1
            v = self.atom()
            r = _root_val(c, self._const(v))
            if not self.lin:
                self.ops += _cost(c, v)
            return self._num(r)
        if c == "(":
            fa = _frac_atom(self.s, self.i)
            if fa:
                self.i = fa[1]
                return self._num(fa[0])
            self.i += 1
            first = self.i
            v = self.expr()
            if self.peek() != ")":
                raise ArithError("parenthèse manquante")
            # `(N/D)` avec N, D entiers, D au moins 2 et N/D irréductible est l'atome fraction : la division disparaît à la fermeture
            if not self.lin and self.div and self.div[1] == self.i and self.div[0] in (first, first + 1):
                n, d = self.div[2], self.div[3]
                if d >= 2:
                    self.ops += _tail(n, d) - 1
            self.i += 1
            return v
        if self.lin and c == "x":
            self.i += 1
            return (Fraction(1), Fraction(0))
        if c != "" and c in DIGITS:
            j = self.i
            while self.peek() != "" and self.peek() in DIGITS:
                self.i += 1
            n = Fraction(int(self.s[j:self.i]))
            if self.lin and self.peek() == "x":
                self.i += 1
                return (n, Fraction(0))
            return self._num(n)
        raise ArithError("facteur attendu")

    def run(self):
        v = self.expr()
        if self.i != len(self.s):
            raise ArithError("caractères en trop")
        return v


class _Tree:
    """Analyse en arbre (même grammaire que `_Calc`, plus la multiplication implicite `3x^2`, `(1/2)x`, `3√x`) pour résoudre par inversion."""

    def __init__(self, s):
        self.s, self.i = s, 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def expr(self):
        neg = self.peek() == "-"
        if neg:
            self.i += 1
        t = self.term()
        if neg:
            t = ("neg", t)
        while self.peek() in ("+", "-"):
            op = self.peek()
            self.i += 1
            t = ("bin", op, t, self.term())
        return t

    def term(self):
        t = self.power()
        while self.peek() in ("*", "/"):
            op = self.peek()
            self.i += 1
            t = ("bin", op, t, self.power())
        return t

    def power(self):
        base = self.atom()
        if self.peek() == "^":
            self.i += 1
            return ("pow", base, self.power())
        return base

    def _implicit(self, node):
        c = self.peek()
        if c == "x" or (c != "" and c in ROOT_SET):
            return ("bin", "*", node, self.power())
        return node

    def atom(self):
        c = self.peek()
        if c != "" and c in ROOT_SET:
            self.i += 1
            return ("root", c, self.atom())
        if c == "(":
            fa = _frac_atom(self.s, self.i)
            if fa:
                self.i = fa[1]
                return self._implicit(("num", fa[0]))
            self.i += 1
            t = self.expr()
            if self.peek() != ")":
                raise ArithError("parenthèse manquante")
            self.i += 1
            return t
        if c == "x":
            self.i += 1
            return ("x",)
        if c != "" and c in DIGITS:
            j = self.i
            while self.peek() != "" and self.peek() in DIGITS:
                self.i += 1
            return self._implicit(("num", Fraction(int(self.s[j:self.i]))))
        raise ArithError("facteur attendu")

    def run(self):
        t = self.expr()
        if self.i != len(self.s):
            raise ArithError("caractères en trop")
        return t


def _has_x(t):
    return t[0] == "x" or (t[0] != "num" and any(_has_x(c) for c in t[1:] if isinstance(c, tuple)))


def _eval(t, x0=None):
    k = t[0]
    if k == "num":
        return t[1]
    if k == "x":
        if x0 is None:
            raise ArithError("inconnue non remplacée")
        return x0
    if k == "neg":
        return -_eval(t[1], x0)
    if k == "pow":
        return _pow_val(_eval(t[1], x0), _eval(t[2], x0))
    if k == "root":
        return _root_val(t[1], _eval(t[2], x0))
    a, b = _eval(t[2], x0), _eval(t[3], x0)
    if t[1] == "+":
        return a + b
    if t[1] == "-":
        return a - b
    if t[1] == "*":
        return a * b
    if b == 0:
        raise ArithError("division par zéro")
    return a / b


def _nth_root(v, n):
    """Racine n-ième exacte d'un rationnel (None si elle n'est pas rationnelle ; un négatif n'a de racine que pour n impair)."""
    if v < 0:
        r = _nth_root(-v, n) if n % 2 else None
        return None if r is None else -r
    p, q = _iroot(v.numerator, n), _iroot(v.denominator, n)
    return None if p is None or q is None else Fraction(p, q)


def _invert(t, targets):
    """Remonte de l'arbre `t` (qui contient `x` une seule fois) jusqu'à `x` : ensemble des valeurs de `x` candidates."""
    while t != ("x",):
        if not targets:
            return set()
        k = t[0]
        if k == "neg":
            targets, t = {-v for v in targets}, t[1]
        elif k == "root":
            targets = {v ** (2 if t[1] == "√" else 3) for v in targets if t[1] == "∛" or v >= 0}
            t = t[2]
        elif k == "pow":
            if _has_x(t[2]):
                raise ArithError("inconnue en exposant")
            n = _eval(t[2])
            if n.denominator != 1 or n < 1:
                raise ArithError("exposant non admis")
            n, new = int(n), set()
            for v in targets:
                if n % 2 == 0 and v < 0:
                    continue
                r = _nth_root(v, n)
                if r is None:
                    raise ArithError("solution irrationnelle")
                new |= {r, -r} if n % 2 == 0 else {r}
            targets, t = new, t[1]
        else:
            op, a, b = t[1], t[2], t[3]
            if _has_x(a):
                c = _eval(b)
                if op == "+":
                    targets = {v - c for v in targets}
                elif op == "-":
                    targets = {v + c for v in targets}
                elif op == "*":
                    if c == 0:
                        raise ArithError("équation indéterminée")
                    targets = {v / c for v in targets}
                else:
                    if c == 0:
                        raise ArithError("division par zéro")
                    targets = {v * c for v in targets}
                t = a
            else:
                c = _eval(a)
                if op == "+":
                    targets = {v - c for v in targets}
                elif op == "-":
                    targets = {c - v for v in targets}
                elif op == "*":
                    if c == 0:
                        raise ArithError("équation indéterminée")
                    targets = {v / c for v in targets}
                else:
                    targets = {c / v for v in targets if v != 0}
                t = b
    return targets


def solset(s):
    """Ensemble des solutions rationnelles, calculé par inversion de l'arbre puis vérifié par substitution (aucune solution parasite)."""
    if s == NO_SOLUTION:
        return frozenset()
    if " ou " in s:
        return frozenset().union(*(solset(part) for part in s.split(" ou ")))
    if s.count("=") != 1:
        raise ArithError("une seule égalité attendue")
    if sum(1 for ch in s if ch == "x") != 1:
        raise ArithError("une seule occurrence de l'inconnue attendue")
    left, right = s.split("=")
    L, R = _Tree(left).run(), _Tree(right).run()
    if _has_x(L) == _has_x(R):
        raise ArithError("l'inconnue doit figurer d'un seul côté")
    if _has_x(R):
        L, R = R, L
    out = set()
    for x0 in _invert(L, {_eval(R)}):
        try:
            if _eval(L, x0) == _eval(R):
                out.add(x0)
        except ArithError:
            pass
    return frozenset(out)


def final_state(s):
    """État terminal canonique attendu pour `s` : `x=5`, `x=7 ou x=-7`, `aucune solution`, un nombre ou `(p/q)`."""
    if "=" in s or s == NO_SOLUTION:
        return _fmt_solutions(solset(s))
    return final_text(value(s)[0], False)


def _remaining(s):
    return len(chain(s, rational=True)) - 1


def value(s):
    """(valeur exacte, nombre d'opérations) d'une expression : opérations binaires, puissances et racines."""
    c = _Calc(s)
    v = c.run()
    return v, c.ops


def solve_eq(s):
    """Solution exacte de `gauche=droite` (formes linéaires), indépendamment de la règle de référence."""
    if s.count("=") != 1:
        raise ArithError("une seule égalité attendue")
    left, right = s.split("=")
    (la, lb), (ra, rb) = _Calc(left, True).run(), _Calc(right, True).run()
    if la == ra:
        raise ArithError("pas de solution unique")
    return (rb - lb) / (la - ra)


def answer(s):
    return solve_eq(s) if "=" in s else value(s)[0]


def final_text(ans, equation):
    """Écriture canonique d'une réponse : entier, ou atome fraction `(p/q)` ; `x=...` pour une équation."""
    ans = Fraction(ans)
    body = str(int(ans)) if ans.denominator == 1 else f"({ans.numerator}/{ans.denominator})"
    return f"x={body}" if equation else body


def _progress(s):
    """Nombre d'étapes restantes selon la règle : opérations ; pour une équation, 2 par constante à déplacer, 2 par coefficient."""
    if "=" in s:
        a, k, _, rhs = parse_eq(s)
        return (2 if k else 0) + (2 if a > 1 else 0) + sum(1 for t in rhs if _isop(t) or _isroot(t))
    return value(s)[1]


def _is_eq(t):
    return "=" in t or t == NO_SOLUTION


def verify_step(inp, out):
    """Étape valide : forme canonique, même valeur (ou même ensemble de solutions) et exactement une opération de moins."""
    try:
        if _is_eq(inp) != _is_eq(out) or not is_canonical(out):
            return False
        if _is_eq(inp):
            return solset(inp) == solset(out) and _remaining(out) == _remaining(inp) - 1
        return bool(value(inp)[0] == value(out)[0] and _progress(out) == _progress(inp) - 1)
    except (ArithError, ZeroDivisionError):
        return False

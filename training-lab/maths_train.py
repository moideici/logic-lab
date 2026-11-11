"""Entraîne le Transformer de la vague 1 des maths (six niveaux, un seul modèle) et le mesure selon le protocole.

Protocole : outputs/verifications/maths-protocole.md. Usage :
    python training-lab/maths_train.py --regime curriculum --steps 30000 --seed 0 --tag curriculum-s0
Régimes : `curriculum` (les niveaux s'ajoutent un par un pendant les 60 % premiers pas, puis tous) ou `flat` (tous dès le début).
Le point de contrôle est choisi sur la validation. Le test et le hors distribution sont mesurés une seule fois, à la fin ; le script
refuse de les remesurer pour un `--tag` déjà évalué (sauf `--rerun-test`). Rien n'est écrit dans les poids de Garry.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic_arena.maths.data import LEVELS, LEVELS2, LEVELS3, encode_pairs, make_starts, make_steps  # noqa: E402
from logic_arena.maths.evaluate import evaluate_level, solve_verified, step_metrics  # noqa: E402
from logic_arena.maths.model import MathLM, load_compatible, loss_on_outputs  # noqa: E402

HERE = Path(__file__).resolve().parent
POOL = {"N1": 60000, "N2": 100000, "N3": 60000, "N4": 300000, "N5": 300000, "N6": 200000, "N7": 300000, "N8": 300000, "N9": 300000, "N10": 300000}
ACTIVE = list(LEVELS)  # niveaux de la vague choisie (`--wave`) ; fixé dans main()
CURRICULUM_SHARE = 0.6  # part des pas pendant laquelle les niveaux arrivent un par un


def load_pool(level, idx, wide=False):
    wide = wide and level in ("N1", "N2", "N3")  # seuls N1, N2 et N3 ont une plage d'entraînement élargie
    rev = "-fr3" if level in ("N8", "N9", "N10") else ""  # fr3 : gabarits (amendement 1) + réduction facteur premier par facteur premier (amendement 2) ; anciens réservoirs obsolètes
    path = HERE / "data" / f"maths-pool-{level}{'-wide2' if wide else ''}{rev}-{POOL[level]}.npz"
    if path.exists():
        d = np.load(path)
        return d["X"], d["plen"]
    X, plen = encode_pairs(make_steps(level, POOL[level], 1000 + idx, "train", wide=wide))
    path.parent.mkdir(exist_ok=True)
    np.savez_compressed(path, X=X, plen=plen)
    return X, plen


def level_weights(regime, step, steps, fixed=None):
    n = len(ACTIVE)
    if fixed is not None:
        return fixed
    if regime == "flat" or step >= CURRICULUM_SHARE * steps:
        return np.full(n, 1 / n)
    k = min(n - 1, int(step / (CURRICULUM_SHARE * steps / n)))
    w = np.zeros(n)
    if k == 0:
        w[0] = 1.0
    else:
        w[:k] = 0.25 / k
        w[k] = 0.75
    return w


def lr_at(step, steps, peak, warmup=500):
    if step < warmup:
        return peak * (step + 1) / warmup
    t = (step - warmup) / max(1, steps - warmup)
    return peak * (0.1 + 0.9 * 0.5 * (1 + np.cos(np.pi * t)))


class HardBuffer:
    """Anneau des exemples d'entraînement les plus mal prédits (pire jeton) : on les rejoue en priorité, c'est la technique contre les
    erreurs rares (une retenue sur un couple de chiffres précis) que le tirage uniforme ne revoit presque jamais."""

    def __init__(self, cap, width):
        self.X = np.zeros((cap, width), dtype=np.uint8)
        self.plen = np.zeros(cap, dtype=np.int64)
        self.cap, self.n, self.ptr = cap, 0, 0

    def add(self, X, plen):
        for x, p in zip(X, plen):
            self.X[self.ptr], self.plen[self.ptr] = x, p
            self.ptr = (self.ptr + 1) % self.cap
            self.n = min(self.n + 1, self.cap)

    def sample(self, k, rng):
        idx = rng.integers(0, self.n, size=k)
        return self.X[idx], self.plen[idx]


def batch_from(pools, w, size, rng, device, hard=None, hard_frac=0.0):
    nh = int(size * hard_frac) if hard is not None and hard.n >= 1000 else 0
    lv = rng.choice(len(ACTIVE), size=size - nh, p=w)
    X = np.zeros((size, pools[0][0].shape[1]), dtype=np.uint8)
    plen = np.zeros(size, dtype=np.int64)
    for k in range(len(ACTIVE)):
        rows = np.flatnonzero(lv == k)
        if len(rows):
            idx = rng.integers(0, len(pools[k][0]), size=len(rows))
            X[rows], plen[rows] = pools[k][0][idx], pools[k][1][idx]
    if nh:
        X[size - nh:], plen[size - nh:] = hard.sample(nh, rng)
    L = int((X != 0).sum(1).max())
    return torch.as_tensor(X[:, :L].astype(np.int64), device=device), torch.as_tensor(plen, device=device), X, plen


def val_score(model, val_sets, device):
    per = {lv: step_metrics(model, val_sets[lv], device)["exacte"] for lv in ACTIVE}
    return float(np.mean(list(per.values()))), per


def final_eval(model, res_path, device, chosen_step):
    """Test et hors distribution, une seule fois par point de contrôle."""
    result = json.loads(res_path.read_text(encoding="utf-8"))
    result["pas_choisi"] = chosen_step
    result["parametres"] = model.parameter_count()
    result["test"] = {lv: evaluate_level(model, lv, "test", 1000, 500, 5000 + i, False, device) for i, lv in enumerate(ACTIVE)}
    result["ood"] = {lv: evaluate_level(model, lv, "test", 1000, 500, 6000 + i, True, device) for i, lv in enumerate(ACTIVE)}
    result["verifie"] = {lv: solve_verified(model, make_starts(lv, 500, 5000 + i + 1, "test", False), 8, device) for i, lv in enumerate(ACTIVE)}
    res_path.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("\nniveau   test: étape exacte / valide / résolu    |   OOD: étape exacte / valide / résolu    |   avec vérificateur (faisceau 8) : résolu")
    for lv in ACTIVE:
        t, o = result["test"][lv], result["ood"][lv]
        print(f"{lv}     {t['etape']['exacte']:.3f} / {t['etape']['valide']:.3f} / {t['probleme']['resolu']:.3f}"
              f"        |   {o['etape']['exacte']:.3f} / {o['etape']['valide']:.3f} / {o['probleme']['resolu']:.3f}"
              f"        |   {result['verifie'][lv]['resolu']:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", choices=("curriculum", "flat"), default="curriculum")
    ap.add_argument("--steps", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--wave", type=int, choices=(1, 2, 3), default=1, help="1 : N1 à N6 ; 2 : N1 à N9 (étape 2a) ; 3 : N1 à N10 (étape 2b, équations)")
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--eval-every", type=int, default=2000)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--weights", default=None, help="poids d'échantillonnage des six niveaux, séparés par des virgules (régime plat)")
    ap.add_argument("--wide", action="store_true", help="entraîne N1, N2 et N3 sur des plages élargies (opérandes, grand facteur et quotient jusqu'à 999)")
    ap.add_argument("--init", default=None, help="repart des poids d'un point de contrôle (affinage) ; utiliser avec un taux plus bas")
    ap.add_argument("--layers", type=int, default=4, help="nombre de couches ; avec --init, les couches en plus sont ajoutées sans changer la fonction")
    ap.add_argument("--bigpool", action="store_true", help="réservoirs de N7 à N10 doublés (600 000 états chacun) pour réduire l'écart entre entraînement et validation")
    ap.add_argument("--gpu-gb", type=float, default=0.0, help="plafond dur de mémoire GPU pour ce processus, en Go (0 : aucun plafond)")
    ap.add_argument("--hard-frac", type=float, default=0.0, help="part de chaque lot rejouée depuis les exemples les plus mal prédits")
    ap.add_argument("--hard-top", type=float, default=0.06, help="part des exemples d'un lot ajoutée à la mémoire des difficiles")
    ap.add_argument("--hard-min", type=float, default=0.3, help="perte minimale du pire jeton pour entrer dans la mémoire des difficiles")
    ap.add_argument("--grad-ckpt", action="store_true", help="recalcule les activations à la rétropropagation (mémoire GPU bien plus faible)")
    ap.add_argument("--eval-only", action="store_true", help="mesure le test et le hors distribution d'un point de contrôle déjà entraîné (`--tag`)")
    ap.add_argument("--rerun-test", action="store_true")
    ap.add_argument("--no-final", action="store_true", help="n'évalue ni le test ni le hors distribution (essais de mise au point)")
    a = ap.parse_args()
    ACTIVE[:] = list({1: LEVELS, 2: LEVELS2, 3: LEVELS3}[a.wave])
    tag = a.tag or f"{a.regime}-s{a.seed}"
    out_dir, res_dir = HERE / "models" / "maths", HERE / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(exist_ok=True)
    res_path, ckpt_path = res_dir / f"maths-{tag}.json", out_dir / f"{tag}.pt"
    if res_path.exists() and "test" in json.loads(res_path.read_text(encoding="utf-8")) and not a.rerun_test and not a.no_final:
        sys.exit(f"{tag} a déjà son test : le test sert une seule fois (--rerun-test pour passer outre)")

    torch.set_num_threads(a.threads)
    if a.gpu_gb and a.device.startswith("cuda"):
        torch.cuda.set_per_process_memory_fraction(min(1.0, a.gpu_gb / (torch.cuda.get_device_properties(0).total_memory / 2 ** 30)))
    if a.eval_only:
        blob = torch.load(ckpt_path, map_location=a.device, weights_only=True)
        model = MathLM(**blob["config"]).to(a.device)
        load_compatible(model, blob["state"])
        final_eval(model, res_path, a.device, blob["pas_choisi"])
        return
    torch.manual_seed(a.seed)
    rng = np.random.default_rng(a.seed)
    t0 = time.time()
    if a.bigpool:
        for lv in ("N7", "N8", "N9", "N10"):
            POOL[lv] = 600000
        POOL["N8"] = 1200000  # le niveau des fractions : le plus grand espace d'états, le plus grand écart entraînement/validation
    fixed = None
    if a.weights:
        fixed = np.array([float(x) for x in a.weights.split(",")])
        assert len(fixed) == len(ACTIVE) and a.regime == "flat", f"--weights : {len(ACTIVE)} valeurs, régime plat"
        fixed = fixed / fixed.sum()
    pools = [load_pool(lv, i, a.wide) for i, lv in enumerate(ACTIVE)]
    val_sets = {lv: make_steps(lv, 1000, 2000 + i, "val", distinct=True) for i, lv in enumerate(ACTIVE)}
    print(f"données prêtes en {time.time() - t0:.0f} s ({sum(len(p[0]) for p in pools)} exemples)", flush=True)

    init_blob = torch.load(out_dir / f"{a.init}.pt", map_location=a.device, weights_only=True) if a.init else None
    model = MathLM(layers=a.layers).to(a.device)
    model.grad_ckpt = a.grad_ckpt
    if a.init:
        added = load_compatible(model, init_blob["state"])
        print(f"départ : {a.init} ({init_blob['config']['layers']} couches), {added} couche(s) ajoutée(s)", flush=True)
    print(f"{tag} : {model.parameter_count()} paramètres, {a.device}, {a.steps} pas", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, betas=(0.9, 0.98), weight_decay=0.05)
    hard = HardBuffer(60000, pools[0][0].shape[1]) if a.hard_frac > 0 else None
    log, best = [], (-1.0, None)
    t0, run_loss = time.time(), 0.0
    for step in range(1, a.steps + 1):
        for g in opt.param_groups:
            g["lr"] = lr_at(step - 1, a.steps, a.lr)
        X, plen, Xnp, pnp = batch_from(pools, level_weights(a.regime, step - 1, a.steps, fixed), a.batch, rng, a.device, hard, a.hard_frac)
        with torch.autocast(device_type=a.device.split(":")[0], dtype=torch.bfloat16, enabled=a.device != "cpu"):
            loss, worst = loss_on_outputs(model, X, plen, per_row=True)
        if hard is not None:
            top = torch.topk(worst, max(1, int(a.hard_top * len(worst)))).indices
            top = top[worst[top] > a.hard_min].cpu().numpy()
            if len(top):
                hard.add(Xnp[top], pnp[top])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        run_loss += float(loss)
        if step % 500 == 0:
            print(f"pas {step:6d}  perte {run_loss / 500:.4f}  {time.time() - t0:.0f} s", flush=True)
            run_loss = 0.0
        if step % a.eval_every == 0 or step == a.steps:
            score, per = val_score(model, val_sets, a.device)
            log.append({"pas": step, "val_exacte_moy": score, "par_niveau": per, "secondes": round(time.time() - t0)})
            mem = f"  [GPU max {torch.cuda.max_memory_allocated() / 2 ** 30:.2f} Go, difficiles {hard.n if hard else 0}]" if a.device.startswith("cuda") else ""
            print(f"  validation {score:.4f}  " + " ".join(f"{k}={v:.3f}" for k, v in per.items()) + mem, flush=True)
            if score > best[0]:
                best = (score, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}, step)
            res_path.write_text(json.dumps({"tag": tag, "regime": a.regime, "graine": a.seed, "pas": a.steps, "poids_niveaux": None if fixed is None else fixed.round(4).tolist(), "couches": a.layers, "recalcul_activations": a.grad_ckpt, "lot": a.batch, "exemples_difficiles": a.hard_frac, "plafond_gpu_go": a.gpu_gb, "vague": a.wave, "niveaux": list(ACTIVE), "entrainement_elargi": a.wide, "init": a.init, "lr": a.lr, "validation": log}, indent=1), encoding="utf-8")

    model.load_state_dict(best[1])
    torch.save({"config": model.cfg, "state": best[1], "regime": a.regime, "graine": a.seed, "pas_choisi": best[2], "pas_total": a.steps}, ckpt_path)
    print(f"point de contrôle retenu : pas {best[2]} (validation {best[0]:.4f}) -> {ckpt_path.name}", flush=True)
    if a.no_final:
        return
    final_eval(model, res_path, a.device, best[2])


if __name__ == "__main__":
    main()

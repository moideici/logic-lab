"""Entraînement en direct pour le Lab : une tâche à la fois, lancée dans un fil, état lisible par le navigateur.

Ne touche jamais aux poids du site. Les données doivent déjà être en cache (`training-lab/data`) : le Lab ne lance pas de
génération longue (Puissance 4 demande plusieurs minutes de professeur).
"""
from __future__ import annotations

import threading
import time

import numpy as np
import torch

from .labtrain import CACHE, TEACHERS, VARIANTES, TorchMLP, build_dataset, evaluate, train
from .neural import SPECS

EPISODES = {"tictactoe": (3000, 500, 500), "nim": (3000, 500, 500), "connect4": (300, 80, 80)}
JEUX = tuple(EPISODES)


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.thread = None
        self.stop_flag = False
        self.state = {"etat": "inactif"}
        self.runs = []  # résumés des entraînements terminés, pour comparer

    def status(self):
        with self.lock:
            return dict(self.state, comparaison=list(self.runs))

    def _set(self, **kw):
        with self.lock:
            self.state.update(kw)

    def start(self, game, mode, steps=3000, pause_ms=4, seed=0):
        if game not in JEUX:
            raise ValueError("Jeu non pris en charge par l'entraînement du Lab")
        if self.thread is not None and self.thread.is_alive():
            raise ValueError("Un entraînement est déjà en cours")
        if type(steps) is not int or not 200 <= steps <= 20000:
            raise ValueError("Nombre de pas entre 200 et 20 000")
        if mode.startswith("graine-"):
            if mode[7:] not in VARIANTES:
                raise ValueError("Variante de Graine inconnue")
        elif mode.startswith("fixe-"):
            try:
                h = int(mode[5:])
            except ValueError:
                raise ValueError("Taille fixe invalide") from None
            if not 2 <= h <= 128:
                raise ValueError("Taille fixe entre 2 et 128")
        else:
            raise ValueError("Mode inconnu (graine-A, graine-B, graine-C ou fixe-N)")
        tr, va, te = EPISODES[game]
        lvl, ms = TEACHERS[game]
        for split, n in (("train", tr), ("val", va), ("test", te)):
            if not (CACHE / f"{game}-{split}-{n}-L{lvl}-{ms}-e35.npz").exists() and game == "connect4":
                raise ValueError("Données de Puissance 4 en préparation : lancer d'abord training-lab/generer_donnees.py")
        self.stop_flag = False
        self.state = {"etat": "preparation", "jeu": game, "mode": mode, "pas": 0, "pas_total": steps, "historique": [], "evenements": [], "activations": {}}
        self.thread = threading.Thread(target=self._run, args=(game, mode, steps, pause_ms, seed), daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_flag = True

    def _run(self, game, mode, steps, pause_ms, seed):
        try:
            torch.set_num_threads(2)
            tr, va, te = EPISODES[game]
            train_d, val_d, test_d = build_dataset(game, "train", tr), build_dataset(game, "val", va), build_dataset(game, "test", te)
            n_in, n_out = SPECS[game]
            probe = torch.as_tensor(val_d[0][:1])
            if mode.startswith("graine-"):
                rules = VARIANTES[mode[7:]]
                model = TorchMLP(n_in, n_out, 2, 2, seed=seed)
            else:
                rules = None
                h = int(mode[5:])
                model = TorchMLP(n_in, n_out, h, h, seed=seed)
            self._set(etat="en cours", tailles=list(model.sizes), parametres=model.parameter_count())

            def on_event(ev):
                with self.lock:
                    if ev["type"] == "point":
                        self.state["historique"].append(ev)
                        self.state["pas"] = ev["step"]
                    else:
                        self.state["evenements"].append(ev)
                    trace = {}
                    with torch.no_grad():
                        model(probe, trace=trace)
                    self.state["activations"] = {k: [round(float(v), 3) for v in trace[k][0]] for k in ("encodeur", "coeur")}
                    self.state["tailles"] = list(model.sizes)
                    self.state["parametres"] = model.parameter_count()
                if pause_ms:
                    time.sleep(pause_ms * 100 / 1000)  # une évaluation tous les 100 pas

            result = train(model, train_d, val_d, steps=steps, seed=seed, graine=rules, on_event=on_event, stop=lambda: self.stop_flag)
            t_loss, t_acc = evaluate(model, test_d)
            run = {"mode": mode, "jeu": game, "tailles": list(model.sizes), "parametres": model.parameter_count(), "test_accord": round(t_acc, 4),
                   "pas": self.state.get("pas", 0), "arrete": bool(self.stop_flag)}
            with self.lock:
                self.runs.append(run)
                self.state.update(etat="arrete" if self.stop_flag else "termine", resume=run)
        except Exception as error:  # l'erreur est montrée dans la page
            self._set(etat="erreur", erreur=str(error)[:300])


JOB = Job()

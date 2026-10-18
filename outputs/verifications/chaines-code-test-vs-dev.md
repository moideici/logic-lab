# Confirmation sur test : quelle chaîne Input → cœur de code ? (18 octobre 2026)

Le split test du banc de code v1.1.0 a été lu **une seule fois**, avec des configurations figées sur dev (script `projets/code/bench/lancer_test.ps1`). Résultats bruts : `projets/code/bench/results/*test*.json`. Le split test est désormais **consommé** pour ces configurations : toute nouvelle comparaison exige un nouveau banc (v2, tâches inédites).

## Résultats (réussites sur 23 tâches par split)

| Chaîne | dev | test | **Total /46** |
|---|---|---|---|
| Cœur de base, demande directe | 13 | 13 | **26** |
| Cœur de base, consigne exacte du banc (« précis ») | 13 | 12 | 25 |
| Cœur de base, Input reformule | 12 | 12 | 24 |
| Cœur de base, extraction Qwen3-0.6B + règle de langage | 13 | 10 | 23 |
| Cœur de base, extraction Input (adapté) + règle de langage | 12 | 7 | 19 |
| Cœur Instruct, demande directe, 1er essai | 14 | 9 | 23 |
| **Cœur Instruct, demande directe, après 3 corrections** | 15 | 13 | **28** |
| Cœur Instruct + extraction, après 3 corrections | 15 | 11 | 26 |
| Cœur Instruct + extraction + début imposé | 15 | **9** | 24 |

Livrables propres (réussis et sans répétition ni bavardage) : Instruct direct après corrections : 12 sur 13 sur test ; Instruct + extraction : 11 sur 11 ; Instruct + extraction + début imposé : 8 sur 9.

## Ce que dit la confirmation

- **La « meilleure chaîne » de dev (Instruct + extraction + début imposé, 15/23) tombe à 9/23 sur test.** Je l'avais choisie en regardant les échecs de dev, sur 23 tâches : c'était du surajustement à dev, pas un gain réel.
- **Rien ne bat nettement la chaîne la plus simple.** Le cœur de base avec la demande telle quelle fait 13 sur dev et 13 sur test. Les écarts entre chaînes sont de 1 à 4 tâches sur 23 : ils ne sont pas significatifs.
- **L'extraction par Input est neutre à négative** : 23 contre 26 (cœur de base), et l'extracteur adapté d'Input est le pire (19). Le début de réponse imposé a aidé le HTML sur dev (4/6) mais pas sur test (2/6) et dégrade C++ et Python.
- **Seul effet qui se confirme : la boucle de retour avec le cœur Instruct.** Elle répare 1 cas sur dev (14 → 15) et **4 cas sur test (9 → 13)**, soit +5 sur 46. Le modèle de base ne répare rien. C'est la meilleure chaîne sur le total (28/46, 61 %), devant le cœur de base direct (26/46, 57 %), sans que l'écart de 2 tâches soit significatif. La boucle suppose un retour d'information (tests, erreurs) que l'utilisateur ne fournit pas toujours.
- **Ce que ça implique pour Input.** Dans ce montage, Input n'améliore ni la réussite ni la propreté. L'interface entre les modèles n'est pas le goulot : c'est la capacité du cœur de 0,5 G. Le canal interne n'a donc de la marge que s'il fait aussi bien que la demande directe en y gagnant autre chose (vitesse, simplicité, robustesse), pas en la dépassant.

## Limites

- 46 tâches au total, une graine par configuration, 6 HTML et 5 C++ par split ; ces chiffres servent à écarter les pistes qui ne marchent pas, pas à classer finement.
- Demandes écrites par moi, tests générés par moi ; retour d'information fondé sur nos tests.
- Le split test est maintenant utilisé : ne plus s'en servir pour choisir.

## Décisions et suite proposée

1. **Chaîne de référence retenue : demande directe → cœur Instruct, avec boucle de retour quand des tests existent.** C'est simple, et c'est la meilleure sur les deux splits.
2. **Abandonner l'extraction par Input comme canal texte** ; garder seulement la règle de langage par défaut (Python sans mention de C++).
3. **Avant d'investir dans un canal interne**, mesurer ce qui borne le cœur : (a) Qwen2.5-Coder-1.5B (plafond hors communication, ≈ 3 Go à télécharger), (b) adaptation du cœur (LoRA) sur des paires demande française → code vérifiées par nos tests, ce qui améliore le cœur lui-même, (c) un banc v2 avec des tâches nouvelles pour trancher sans surajustement.

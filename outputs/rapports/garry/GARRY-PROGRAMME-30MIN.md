# Garry 0.6.0 — programme ciblé de 30 minutes

Programme réellement lancé le **17 octobre 2026 à 23 h 01 min 05 s (Paris)**, fin prévue **23 h 31 min 05 s**. Identifiant `8a996a3b756d469aa0ff2be307fb554b`, processus **12444**. Le suivi et le plateau sont visibles dans l’onglet **Apprendre** de http://127.0.0.1:8765.

Le calcul cible **Go, Hex et Gomoku**. Les coefficients utilisés par les **onze autres jeux**, les biais communs, le module central, l’évaluateur et la mémoire de Puissance 4 restent identiques. Un contrôle des poids actifs après la première promotion l’a confirmé. Le modèle reste en version **0.6.0**, avec les mêmes dimensions. Garry utilise le CPU avec un seul fil de calcul actif ; le GPU reste disponible pour le projet de français séparé.

## Déroulement

1. **3 minutes de diversité** : départs vides, exploration, réseau et professeur borné ; Go en 9 × 9, 13 × 13 et 19 × 19, avec des parties 9 × 9 pouvant atteindre le comptage.
2. **22 min 30 de renforcement** : erreurs réévaluées selon les poids courants, au moins 60 % des places du lot réservées aux erreurs quand elles sont assez nombreuses, puis rejeu équilibré par catégories. Certains départs reprennent une position difficile du lot d’apprentissage et poursuivent légalement. Les ataris et fins de plateau du Go ainsi que les victoires et défenses urgentes du Gomoku sont distingués. Le jeu le plus faible sur la validation reçoit un créneau supplémentaire.
3. **4 min 30 de consolidation** : davantage de rejeu général, moins d’exploration et taux d’apprentissage réduit.

Les gradients ne changent que les entrées et sorties propres au jeu travaillé. La validation combine les réserves fixes et un échantillon de l’ancienne session protégée : **200 positions Go, 220 Hex et 220 Gomoku**, plus les nouvelles familles réservées. Les accords initiaux avec le professeur sont respectivement **24,5 %, 40 % et 19,55 %**. Ces pourcentages sont des accords de décisions, pas des taux de victoire.

Un candidat doit préserver les taux d’accord et la perte d’imitation sur les deux validations, avec une amélioration effective. Sinon, les poids précédents restent actifs. Les tests servent uniquement au bilan après la sélection ; ils ne choisissent ni les poids ni les hyperparamètres.

## Protection et premier contrôle réel

**126 042 états historiques sont exclus des nouvelles épreuves**, en plus des ensembles fixes. Le rejeu n’accepte que des exemples marqués apprentissage provenant de sessions antérieures protégées ; leurs validations restent des validations et leurs tests ne sont pas rejoués. Les reprises à partir de positions difficiles sont elles aussi limitées au lot d’apprentissage.

Après environ cinq minutes : **84 cycles, 17 398 coups et une promotion**. L’audit de **4 053 nouvelles positions**, dont **357 continuations de positions d’apprentissage**, n’a trouvé **aucun recoupement historique**. Les onze autres jeux étaient préservés exactement. L’interface affichait le temps restant et un plateau réel en cours, sans erreur JavaScript.

Exemple de contrôle effectif : un candidat Gomoku améliore la validation récente de 17,98 % à 22,47 %, mais recule sur la validation fixe de 19,55 % à 15,91 %. Il est donc rejeté.

**114 tests Python réussis**, incluant sélection d’erreurs actuelles, exclusion des tests du rejeu, restauration d’un départ légal, lancement du profil et vérification des promotions et des autres jeux. Les premiers cycles sont actifs ; les résultats définitifs seront écrits automatiquement dans le dossier de la session à sa fin. Cette session n’établit aucune invincibilité ni une amélioration des quatorze jeux.

Pièces : `verification-garry-30min.json`, `verification-garry-30min-interface.json`, `garry-targeted-python.log`. Les statuts et journaux de calcul restent dans `training/continuous/8a996a3b756d469aa0ff2be307fb554b/`.

# Changelog

Toutes les évolutions notables de ce projet. Les versions suivent [SemVer](https://semver.org/lang/fr/).

## [0.6.0] : première version publique

Instantané du dépôt au moment de son ouverture au public. Détail de l'historique ci-dessous, par mois.

### 2026-11
- Maths (vagues 1-2), moteurs Gomoku/Hex a la main, modele unique multi-jeux (P0-P1, Garry Optimus 0.1), bancs et tests

### 2026-10
- Dames: regles par lots et auto-apprentissage; Garry etendu aux dames; Garry Universel (pont Node, jetons, transformeur, protocole)
- Dames: etiquetage par la recherche, distillation dans un reseau, duels reseau
- Dames de multi: moteur C++, parite avec le TypeScript, recherche renforcee et duels
- Mesure de Garry contre la theorie exacte au Nim et au morpion
- Livre de Puissance 4 jusqu'au 12e coup et fixture de parite pour le port TypeScript
- Livre d'ouverture, joueur parfait et recherche tactique pour Puissance 4
- Distillation du solveur de Puissance 4: generation d'etiquettes, entrainement, mesure
- Solveur exact de Puissance 4 et mesure de l'ecart a la perfection
- Garry 0.6: session de 60 min (16 promotions), arene avec ouvertures aleatoires
- Ignore la bibliotheque compilee du moteur de Go
- Zero: Go 9x9 (moteur C++ ctypes), entraineur zero_train, arene generale
- Zero: Puissance 4 (bitboards numpy, MCTS par lots, reseau politique-valeur), arene, tests
- Retire les dossiers de parties de test des jeux reels
- Jeux reels: PLAYWRIGHT_BROWSERS_PATH par defaut vers work/browsers, famille coloration de graphe, entrainement multi-familles
- Loop: solveur recurrent (sudoku 4x4/6x6), experiences, service Lab, tests
- Lab: entrainement en direct (Graine et reseaux fixes), entraineur PyTorch, donnees variees, experience Graine
- Lab v1: API /api/lab/*, page lab.html (reseau en direct, extinction, importance, courbe qualite/cout), tests
- Garry Core: reseau en couches observable (traces, extinction, elagage, croissance) + test de parite exact sur 14 jeux
- Garry 0.6.0: 14 jeux, niveaux, entrainement continu, harnais et docs (etat du regroupement du 18/10/2026)
- Improve 2048 search, share neural evaluations, and make inference cancellation reliable
- Optimize fast completion with exact paths and worker inference
- Build neural logic arena with shared learning across six games
- Build neural logic arena with shared learning across six games

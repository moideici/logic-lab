# Logic Lab — bilan et plan global

Mis à jour le 18 octobre 2026 (fin de journée). Ce document est le plan principal de la conversation et remplace l’ordre des priorités des anciens rapports. **Priorité actuelle : la famille Garry et le Lab (Core entraînable, Graine, Loop), puis un modèle de raisonnement entraîné de zéro. Input est en veille (lot 4 à reprendre) et le projet de cœur de code est mis de côté, avec ses résultats.** Les sections 1 à 8 décrivent l’état de départ ; les sections 9 et suivantes sont l’état à jour.

## 1. Organisation et état réel

Deux projets principaux restent distincts, regroupés sous le même dossier de travail :

- `projets/garry/` : Playi / Logic Lab, les jeux, Garry, ses versions, entraînements, tests et harnais de sites réels.
- `projets/input/` : compréhension et conversation françaises, corpus, modèles, adaptations, contrats JSON et interface Input.
- `recherche/hrm/` et `recherche/trm/` : essais de raisonnement récursif, séparés des modèles en production.
- `outputs/` : rapports et preuves de vérification de cette conversation.
- `work/` : environnement Python local, dépendances et fichiers préparatoires historiques.

Les copies originales sont conservées sous `C:\Users\gabor\code`. La vérification du regroupement et les adaptations de chemins sont décrites dans `docs/regroupement/REGROUPEMENT.json` et `docs/GUIDE.md`. Regrouper les dossiers ne fusionne pas les poids, les jeux de données ou les historiques d’expériences.

### Garry 0.6.0

- Architecture 4 872 → 48 → 48 → 4 259, 444 979 paramètres. La version décrit le code et l’architecture ; les performances et empreintes des poids sont suivies séparément.
- Quatorze jeux : morpion, Puissance 4, 2048, sudoku, démineur, taquin, Reversi 6×6, Nim, Lights Out, dames internationales, Percée, Hex 7×7, Gomoku 15×15 Swap2 et Go 9/13/19.
- Niveaux 0–10, niveaux indépendants en arène, transitions visibles, modes humains, difficultés et tailles de puzzles, sudoku à trois vies pour l’IA.
- Dernière session de trente minutes terminée le 17 octobre à 23 h 31 : 102 762 coups, 540 cycles, dix promotions. Les onze autres jeux sont préservés lorsque Go, Hex et Gomoku sont entraînés.
- Tests réservés de cette session, accord du réseau avec un professeur borné : Go 15,41 → 17,29 % sur 2 388 positions ; Hex 40,83 → 42,92 % sur 240 ; Gomoku 17,40 → 22,06 % sur 408. Ce ne sont pas des taux de victoire.
- Harnais réel : Go 19×19 terminé avec 396 transitions vérifiées, défaite de 285,5 points contre COSUMI niveau 1 avec des poids antérieurs aux derniers entraînements. Dernier 2048 complet archivé : 71 092 points, tuile 4096, 3 243 transitions vérifiées ; ce score isolé ne mesure pas un progrès contrôlé.
- Vérifications archivées : 114 tests Python et 65 JavaScript. Elles ne remplacent pas une nouvelle recette de l’ensemble du site.
- Limites : niveau Go faible, tactiques inégales, recherches bornées, grandes grilles non certifiées, absence d’une récente campagne complète de duels. L’invincibilité et le « meilleur coup » sur tout jeu ne sont pas démontrés. L’origine des poids réellement chargés dans le navigateur doit être rendue explicite.

### Input 0.2.0

- Modèle génératif local Qwen3-0.6B, adapté par LoRA. Il ne s’agit pas d’un modèle de conversation entraîné intégralement de zéro.
- Adaptation active : `focus-20261017-210925/checkpoint-1000`. Dernier cycle : 4 896 présentations d’exemples et 272 971 tokens supervisés ; les présentations peuvent inclure des répétitions.
- Validation de sélection : 7/28 ensembles de valeurs exacts avant adaptation, 25/28 après, 28/28 JSON complets des deux côtés.
- Tests réservés : 36/36 JSON complets et 29/36 ensembles de valeurs exacts. Contexte 12/12, structure 12/12, calculs 5/12. Ce petit diagnostic ne mesure ni les connaissances générales ni les justifications.
- Corpus importés : environ 2,56 millions d’articles Wikipédia français, OpenAssistant et un premier lexique de 161 mots / 2 261 sens. Importer un corpus ne signifie pas l’avoir appris. Les expériences initiales CamemBERT et modèle de zéro sont des comparaisons de classification limitées, conservées séparément.
- Contexte : jusqu’à 21 messages récents et 2 400 tokens de prompt. Les conversations enregistrées dans le navigateur ne constituent pas une mémoire illimitée du modèle.
- Format conversationnel actuel : `texte` et `valeurs`. La syntaxe est contrôlée, mais les affirmations et les nombres peuvent être faux. Une erreur JSON contrôlée ne compte pas comme une réponse utile réussie.
- Limites observées : hallucinations, réponses génériques ou répétitives, phrases parfois tronquées, calculs fragiles et débit encore faible. Les mesures antérieures de génération sont de l’ordre de 6–16 tokens/s selon le contexte, le chargement, l’adaptation et les calculs simultanés ; elles ne sont pas un benchmark homogène à 30–40 tokens/s.
- Une première refonte de conversation et de diffusion progressive a été entamée avant la demande « plan d’abord ». Elle reste à recetter et stabiliser avant d’être déclarée livrée. Aucun nouvel entraînement ne doit être présenté comme améliorant les décisions générales sans nouvelles mesures.

### Recherche sur le cœur de raisonnement

HRM symbolique et ses poids officiels sudoku sont disponibles. Une entrée continue par tenseurs et des adaptateurs entraînables ont été préparés. Trois tests techniques passent ; un des deux contrôles publics de sudoku réussit, l’autre échoue. Le pont depuis Input et son retour ne sont pas entraînés. TRM reste une référence inspectée. Aucun de ces prototypes n’est choisi comme cœur général définitif.

## 2. Objectifs retenus

Input doit comprendre une demande française, distinguer objectif, faits, préférences, contraintes et inconnues, prendre une décision appropriée et fournir une justification fondée. Trois usages sont retenus :

1. Résoudre des problèmes à contraintes.
2. Préparer et réviser des plans réalisables.
3. Comparer des scénarios en conservant leurs hypothèses.

La communication par représentations internes reste une piste à développer et à mesurer. Le JSON demeure le contrat de sortie et de contrôle. La qualité réelle, le temps et les ressources décident du choix du cœur et du canal.

### Périmètre actif des chantiers (mis à jour le 18 octobre 2026)

| Statut | Chantier |
|---|---|
| **Actif** | Famille Garry et Lab : Core entraînable, Graine (croissance et élagage), Loop (cœur récurrent), Lab en direct. Modèle de raisonnement de zéro qui s’appuie sur la même infrastructure. |
| **En veille** | Input : interface prête (lot 1), banc de régression gelé (lot 2), contrat v2 prêt mais non activé (lot 3) ; il reste le lot 4 (données ciblées). Qwen3-0.6B reste la base : Pleias a été essayé et écarté. |
| **Mis de côté (projet séparé)** | Cœur de code relié à Input (`projets/code`) : banc, mesures et conclusions conservés, reprise possible (voir §11). |
| **Références** | HRM et TRM servent de références pour le modèle de raisonnement ; aucun entraînement dédié. |

Le canal latent et le « rapport qualité/coût par neurone » restent des hypothèses à tester, pas des objectifs de livraison.

## 3. Périmètre : apprendre ce qui sert

Priorités : français, vocabulaire, grammaire, logique, mathématiques, fonctionnement réel d’Input et informations nécessaires de la conversation.

- Recentrer les futurs corpus sur ces compétences et sur des tâches contextualisées vérifiables.
- Retirer Wikipédia généraliste du mélange d’entraînement par défaut tant qu’un usage linguistique précis, filtré et évalué n’est pas défini. Conserver les fichiers comme archives ne signifie pas continuer leur utilisation.
- Enseigner la différence entre information fournie, résultat calculé, fait vérifié et information inconnue. Les faits donnés par l’utilisateur peuvent être analysés « selon le texte » sans être déclarés vrais dans le monde.
- Pour une question factuelle non vérifiée ou hors du périmètre, demander une source, une précision ou reconnaître la limite.
- Les informations sur son propre fonctionnement doivent venir de la configuration et de l’état réellement servis, pas de souvenirs improvisés du modèle.
- La base préentraînée connaît déjà des faits généraux. Une restriction d’usage n’est pas une preuve d’effacement de ces faits. Étudier un modèle plus spécialisé ou une autre base seulement avec une comparaison qualité/coût et sans promettre une suppression parfaite des connaissances inutiles.

L’exemple erroné sur Emmanuel Macron devient un cas de régression contre les inventions factuelles, accompagné de reformulations et d’autres sujets inédits pour éviter de simplement mémoriser sa correction.

## 4. Ordre d’exécution

### Lot 1 — interface et utilisation, priorité immédiate

- Lecture naturelle par défaut ; JSON consultable et copiable à la demande.
- Affichage progressif réel, état de chargement explicite, arrêt qui interrompt effectivement le calcul, nouvelle tentative et erreurs compréhensibles.
- Conversations conservées, nouvelle conversation et limites de contexte visibles. Les réponses interrompues ne deviennent pas des réponses validées dans le contexte.
- Distinguer « format JSON conforme », « résultat vérifié » et « contenu non vérifié ». Supprimer les badges qui donnent une confiance injustifiée dans le fond.
- Afficher le modèle et les poids réellement employés ; rendre la navigation Garry/Input/Bilan cohérente.
- Recette sur ordinateur et mobile : chaque bouton utile, copie correcte, reprise après erreur, rechargement, annulation et préservation de l’historique.

**Sortie du lot :** parcours de conversation utilisable et preuves de recette, sans présenter la qualité du modèle comme déjà résolue.

### Lot 2 — utilisation fiable et respect du périmètre

Définir les compétences autorisées, les demandes de clarification et l’abstention. Préparer un petit banc de régression : questions hors périmètre, faits absents, contradictions, négations, changements d’avis, chiffres et fonctionnement du modèle. L’objectif est de réduire les inventions sans obtenir un modèle qui refuse toutes les demandes : publier aussi la couverture et les clarifications justifiées.

### Lot 3 — JSON, Markdown et justifications

Contrat cible à implémenter :

| Champ | Rôle | Markdown interprété |
|---|---|---|
| `etat` | Solution, clarification ou impossibilité démontrée | Non |
| `decision` | Choix bref | Non |
| `texte` | Réponse lisible | Oui |
| `justification` | Faits, contraintes, raisons et limites | Oui |
| `valeurs` | Nombres, booléens, null et chaînes brutes | Non |

Définir un profil Markdown limité et un rendu contrôlé. Échapper correctement guillemets et retours à la ligne. Un échec de recherche ne suffit pas à déclarer un problème impossible. Une justification doit correspondre au résultat et aux vérifications réellement effectuées, sans sources ou calculs inventés ; elle n’a pas à exposer toute la trace interne du modèle.

### Lot 4 — données et entraînement ciblés

Construire des exemples français de décisions et de justifications, avec contextes, ambiguïtés et contre-exemples. Priorité aux calculs, aux contraintes et à la cohérence entre texte et valeurs. Utiliser des vérifications déterministes quand elles sont disponibles. Séparer les situations, transformations et reformulations entre apprentissage, validation et tests. Ne pas réentraîner automatiquement sur un test que l’on veut continuer à présenter comme réservé.

### Lot 5 — les trois usages et le cœur de raisonnement

Préparer un premier banc de 300 situations, 100 par usage. Vérifier faisabilité, dépendances, ressources, hypothèses, décisions et qualité des raisons. Choisir ensuite le cœur adapté à ces problèmes. Pour le canal latent, figer les checkpoints, entraîner les adaptateurs et comparer aux canaux de référence, ainsi qu’aux canaux coupés et permutés. Mesurer l’information utile effectivement transportée, pas seulement la compatibilité des dimensions.

### Lot 6 — progression de Garry

Pour les jeux à deux joueurs, duels depuis le plateau vide contre l’ancienne version, dans les deux camps, conformément au choix de l’utilisateur. Pour 2048 et les puzzles, mesurer scores, réussite, erreurs et temps avec des épreuves adaptées. Priorité Go, tactiques et nouvelle évaluation des poids courants sur les sites réels. Conserver les références, les séparations de données et les contrôles de non-régression entre jeux.

## 5. Efficacité : objectif transversal dès le lot 1

Mesurer le coût d’une réponse ou décision correcte et utile : temps de chargement à froid, premier texte visible, temps total à chaud, tokens/s, mémoire CPU/GPU maximale et énergie lorsque mesurable. Comparer sur le même matériel, les mêmes entrées et les mêmes critères de qualité.

Optimiser d’abord les attentes, les longueurs inutiles, le cache, le fonctionnement de l’adaptation à l’inférence et la concurrence entre entraînement et conversation. Ensuite seulement comparer quantification, distillation, réduction de dimensions ou élagage. Toute optimisation doit démontrer une économie et son effet sur les erreurs. La fréquence d’activation d’un neurone ne suffit pas à prouver son inutilité.

L’objectif « chaque neurone rentable à 100 % » devient une exigence expérimentale de meilleur rapport qualité/coût. Il ne se confond ni avec une charge GPU maximale, ni avec le plus petit nombre de paramètres, ni avec une propriété que l’on peut certifier pour tout message possible.

## 6. Critères de réussite et limites

- Toute réponse publiée respecte le contrat JSON ; publier séparément réponses complètes, erreurs et refus.
- Le Markdown respecte le profil des champs autorisés ; cela ne prouve pas la justesse des affirmations.
- Viser tous les critères de décision et de justification sur les épreuves définies ; ne pas promettre 100 % de vérité sur tout message libre.
- Chaque nouvelle version est choisie sur validation, puis mesurée sur des tests réservés. Garder les anciens poids et les empreintes des modèles.
- Les numéros de version reflètent les changements de code et d’architecture, pas les scores.
- Aucun nouvel agent producteur de code, nouveau jeu ou projet annexe dans ces lots sans changement explicite de priorité.

## 7. Reprise du travail

La prochaine action de développement est de finir la recette du lot 1 et de présenter l’interface utilisable. Le présent regroupement des fichiers ne constitue pas une reprise des entraînements ou l’activation d’un nouveau cœur. Les anciens rapports dans `outputs/` restent des archives et peuvent décrire des orientations désormais remplacées par ce plan.

## 8. Points ajoutés après revue (18 octobre 2026)

Le plan ci-dessus est cohérent dans l'ordre et honnête sur les limites, mais il lui manquait de quoi décider qu'un lot est terminé et de quoi ne pas perdre le travail. Ajouts :

1. **Sauvegarde externe avant tout nouvel entraînement.** Les poids (~14 Go) ne sont pas dans Git et ce dossier est la seule copie. Copier `projets/*/models` et les caches vers un autre support, avec les empreintes déjà consignées.
2. **Banc de référence figé avant de changer le modèle.** Geler les tests réservés (liste et empreinte) et mesurer l'état actuel : c'est la ligne de base de toute comparaison. Le banc de régression du lot 2 doit exister avant le lot 4, pas après.
3. **Seuils chiffrés par lot.** « Utilisable » doit se mesurer. Lot 1 : premier texte visible en moins de 3 s à chaud, arrêt effectif en moins de 1 s, 0 erreur JavaScript sur le parcours complet, reprise après erreur et rechargement sans perte d'historique. Lots suivants : seuils fixés avant la mesure, jamais après.
4. **Justifier la taille du modèle.** Comparer Qwen3-0.6B à au moins une base plus grande et une plus petite sur le même banc, matériel et coût, avant d'investir dans de nouveaux entraînements.
5. **Provenance et licences des données.** Consigner pour chaque corpus (Wikipédia, OpenAssistant, lexique) licence, date d'import et filtrage ; vérifier l'absence de recouvrement avec les tests réservés.
6. **Sécurité locale d'Input.** Écoute sur 127.0.0.1 uniquement, tailles de requête bornées, aucune donnée de conversation envoyée hors de la machine.
7. **Reproductibilité.** Graines, version des dépendances (`work/requirements.lock.txt`) et journal d'expériences (données, configuration, mesures, décision) pour chaque entraînement.
8. **Règle d'arrêt.** Un cycle d'entraînement sans gain mesuré sur validation après deux essais est abandonné et documenté, pas prolongé.

## 9. État d'avancement (18 octobre 2026)

| Chantier | Statut | Résultat clé | Preuve |
|---|---|---|---|
| Input, lot 1 (interface) | Fait | Premier texte en 0,5 à 1 s à chaud, arrêt en 53 ms, 0 erreur JavaScript, mobile correct | `outputs/verifications/recette-lot1-input-2026-10-18.md` |
| Input, lot 2 (banc de régression) | Fait | Banc v1.0.0 gelé (2 × 51 cas). Baseline : 54,2 % (dev), 47,7 % (test) ; 86 % de réponses affirmées sans réponse possible | `outputs/verifications/baseline-lot2-input-0.2.0.md` |
| Input, lot 3 (contrat v2) | Prêt, non activé | Sans entraînement, 61,4 % en dev mais 17 erreurs, 26 s de latence médiane et un biais de mesure | `outputs/verifications/contrat2-lot3-input.md` |
| Input, base alternative | Écartée | Pleias-350M adapté : 24,8 % contre 54,2 % pour Qwen3-0.6B | `outputs/rapports/input/COMPARATIF-10-MODELES.md` |
| Input, lot 4 (données) | À faire | Cibles chiffrées fixées au lot 2 (global ≥ 80 %, contexte ≥ 90 %, limite reconnue ≥ 80 %) | rapport du lot 2 |
| Garry Core | Fait | Parité exacte avec les poids 0.6.0 sur 14 jeux | `projets/garry/tests/test_core.py` |
| Lab v1 | Fait | Réseau en direct, extinction, importance par neurone, courbe qualité/coût (`/lab.html`) | `projets/garry/web/lab.html` |
| Core entraînable (PyTorch) | Fait | `labtrain.py` : réseau à deux couches cachées, croissance et élagage, données de professeur variées ; 6 tests | `projets/garry/logic_arena/labtrain.py` |
| Graine | Fait (résultat négatif) | À taille égale, un réseau fixe fait aussi bien ou mieux (§10) | `outputs/verifications/graine-resultats.md` |
| Garry Loop (cœur récurrent) | Premier résultat positif | Sudoku 6×6 : 99,8 % (moyen) et 75 à 89 % (plus dur que l'entraînement) avec 53 254 paramètres ; la récurrence est ce qui compte | `outputs/verifications/loop-sudoku6-resultats.md` |
| Projet code | Mis de côté | Voir §11 | `outputs/verifications/chaines-code-test-vs-dev.md` |
| Modèle de raisonnement | Démarré (famille 1) | Voir §12 | `projets/garry/logic_arena/reason/` |

Garry : 130 tests Python verts (dont Core et Lab), puis 6 tests de l’entraîneur du Lab.

## 10. Famille Garry et Lab

Un **Garry Core** propre (couches nommées, activations capturables, neurones éteignables ou supprimables) et des variantes qui en sont des configurations, observables dans l’onglet **Lab** du site.

| Variante | Définition retenue | Statut |
|---|---|---|
| **Garry Games** | Le Garry actuel, 14 jeux | Existant (0.6.0) |
| **Graine** | Croissance et élagage de neurones pendant l’apprentissage | Fait : gain non confirmé, conservée comme visualisation |
| **Garry Loop** | Cœur récurrent : un bloc repassé plusieurs fois sur son état, arrêt appris | Fait pour le sudoku 6×6 (arrêt encore par vérification) |
| **Garry Mind** | Amélioration du schéma de boucle des modèles existants pour qu’ils réfléchissent plus, et à plus de choses (budget de calcul adaptatif, proposer-vérifier-corriger) | À faire |
| **Garry Input** | Input rebaptisé dans la famille ; reste Qwen3-0.6B + adaptation | En veille |
| **Garry Prime** | Routeur plus distillation des variantes ; compromis force/taille mesuré, pas de promesse « le plus fort partout » | Plus tard |
| **Règles** | Jouer un jeu jamais vu à partir de ses règles | Plus tard (pari) |

### Graine : résultat (18 octobre 2026)
Rapport : `outputs/verifications/graine-resultats.md`. Trois jeux, trois graines, trois règles de croissance et d'élagage, comparées à des réseaux fixes de même taille finale.
- **Hypothèse non confirmée** : à taille égale, Graine perd 1 à 6 points d'accord avec le professeur contre un réseau fixe (morpion : 0,812 / 0,924 / 0,940 contre 0,873 / 0,939 / 0,981 ; Nim : 0,711 / 0,911 / 0,941 contre 0,787 / 0,920 / 0,961). Elle trouve une taille raisonnable seule, mais une recherche sur quelques tailles fixes donne autant.
- **Puissance 4 inconclusif** (accord 0,35 à 0,39 pour toutes les tailles) : jeu trop dur pour 6 129 positions et un professeur borné en temps.
- **Données** : un professeur parfait rejoue toujours la même partie (un premier essai avec 9 positions distinctes donnait 100 % à un réseau de 71 paramètres, résultat sans valeur) ; correction : coups aléatoires avec probabilité 0,35, étiquettes du professeur.
- **Décision proposée** : garder Graine dans le Lab comme visualisation, ne pas insister sur le gain, passer à Loop et au modèle de raisonnement.
- **Lab en direct** : entraînement visible dans `/lab.html` (réseau, courbe d'accord et de taille, événements, comparaison de la session), API `/api/lab/train/*`, 11 tests.

### Garry : entraînement relancé et orientation (18 octobre 2026)

- **Décision de l'utilisateur :** Garry est le modèle phare ; les autres expériences (Graine, Loop, Pleias, projet code) n'ont pas la même ambition. L'effort se concentre sur Garry.
- **Entraînement relancé** : session continue de 60 minutes, profil « points faibles » (Go, Hex, Gomoku), par imitation gardée : un candidat n'est promu que s'il fait au moins aussi bien que le champion sur validation et sur positions fraîches. Poids de départ : Garry 0.6.0, empreinte `ae54c06d…`, sauvegardés dans `projets/garry/training-runs/sauvegardes/` et `work/`. Résultats à consigner à la fin de la session.
- **Jeux réels réparés** : le serveur désigne maintenant le navigateur Playwright du projet (`work/browsers`) ; 2048 (12 coups vérifiés) et Go 9×9 contre COSUMI niveau 1 (10 étapes) fonctionnent depuis l'onglet « Jeux réels ».
- **Trois modèles ambitieux proposés** (`outputs/rapports/garry/PROPOSITIONS-3-MODELES-AMBITIEUX.md`) : **Garry Zéro** (auto-apprentissage avec recherche, sans professeur, pour dépasser les références ; jalon Puissance 4 puis Hex 7×7), **Garry Règles** (joueur universel qui lit les règles, test sur des jeux écartés), **Garry Délibération** (cœur récurrent dont le niveau est le nombre de passes, appuyé sur le Loop validé). Ordre recommandé : Zéro, Délibération, Règles. Aucune n'est lancée.

## 11. Projet code (mis de côté, résultats conservés)

Un cœur de code relié à Input (`projets/code`, dépôt Git séparé, banc de code v1.1.0 : Python exécuté, C++ compilé, HTML vérifié).
- **Cœur retenu :** Qwen2.5-Coder-0.5B (base, puis Instruct). Seuls 10 candidats comparés : `outputs/rapports/input/COMPARATIF-10-MODELES-CODE.md`.
- **Mesures :** cœur de base seul 17/23 (dev) et 15/23 (test) avec la signature dans l’invite ; chaîne texte avec Input qui reformule 12/23, avec extracteur 12 à 13/23, boucle de retour sans effet avec le cœur de base ; avec le cœur Instruct, la boucle de retour répare des cas (+1 en dev, +4 en test).
- **Surajustement constaté :** la meilleure chaîne de dev (15/23) fait 9/23 sur test. Chaîne retenue : demande directe → cœur Instruct + boucle de retour (28/46). L’extraction par Input est abandonnée comme canal texte. Le split test est consommé.
- **Conclusion :** le goulot est le cœur de 0,5 G, pas la communication ; le canal interne n’a de marge que s’il égale la demande directe en gagnant ailleurs.
- **Reprise possible :** banc v2 (tâches inédites), cœur 1,5 G pour le plafond, adaptation du cœur sur paires vérifiées, puis canal interne. Rapports : `outputs/verifications/` (`canal-texte-*`, `boucle-de-retour-dev.md`, `coeur-instruct-chaine-dev.md`, `chaines-code-test-vs-dev.md`).

## 12. Modèle de raisonnement entraîné de zéro (idée de l’utilisateur)

« Modèle de calcul » = modèle qui résout des problèmes et raisonne (pas une calculatrice). Souhait exprimé : **un seul modèle** qui fasse énigmes logiques, découverte de règles et comparaison de scénarios, plutôt que trois.
- **Piste :** un cœur récurrent (Loop) entraîné de zéro sur une famille de petits problèmes générés à l’infini et vérifiables exactement, avec un format d’entrée commun (grille ou ensemble d’entités et de contraintes) et des têtes ou encodeurs par famille.
- **Familles, de la plus simple à la plus ambitieuse :** (1) contraintes sur grille (sudoku réduit, n-reines, coloration de graphe) ; (2) planification (ordonnancement, labyrinthes) ; (3) énigmes logiques en tableau (type zèbre) ; (4) règles de grille type ARC simplifié ; (5) comparaison de scénarios avec hypothèses.
- **Mesures :** exactitude selon la difficulté, nombre de passes de réflexion selon la difficulté, transfert vers une famille jamais vue (tenue en réserve), grille de chaque passe visible dans le Lab.
- **Risques :** interférence entre tâches (déjà vue avec les 14 jeux de Garry : vérifier la préservation à chaque ajout), et le format commun, qui est le vrai travail ; la comparaison de scénarios exige des nombres et du langage et vient en dernier.
- **Ordre :** après Graine et la boucle récurrente ; commencer par une ou deux familles qui partagent la même représentation (grilles).

### Premier résultat (18 octobre 2026) : sudoku 6×6
Rapport : `outputs/verifications/loop-sudoku6-resultats.md`. Un bloc d'attention limité aux voisines de contrainte, repassé avec les mêmes poids (53 254 paramètres), entraîné de zéro sur des sudokus à solution unique générés à l'infini.
- **La récurrence fait le travail** : une seule passe ne résout presque rien ; un réseau à huit blocs distincts (8× plus gros) fait un peu moins bien sur le dur (0,735 contre 0,749).
- **Réfléchir plus longtemps qu'à l'entraînement aide** : de 8 à 32 passes à l'inférence, les problèmes durs passent de 0,749 à 0,841 (0,893 pour le Loop entraîné à 16 passes).
- **La durée de réflexion suit la difficulté** : 1,8 passe (facile), 3,0 (moyen), 6,0 (dur), mesurée avec arrêt par vérificateur exact.
- **Limite principale** : l'attention ne voit que les voisines de contrainte, la règle est donc dans la structure ; la généralité reste à prouver sur une autre famille de problèmes (coloration de graphe, n-reines) et un transfert vers une famille jamais vue.
- **Lab** : section « Réflexion en direct » (`/lab.html`), grille proposée à chaque passe avec confiance et cases fausses, API `/api/lab/reason/*`. Modèle régénérable par `training-lab/entrainer_loop.py` (4 minutes).
- Tests : 155 verts (dont problèmes, modèle, service).

## 13. Prochaines étapes (ordre)

1. Graine, Lab en direct, Loop sur sudoku 6×6 : faits.
2. **Deuxième famille sur le même modèle** (coloration de graphe ou n-reines, autre graphe de contraintes) et **test de transfert** vers une famille jamais vue : c'est la question centrale du modèle unique.
3. Arrêt appris (tête de décision d'arrêt) comparé à l'arrêt par vérificateur ; Mind.
4. Sudoku 9×9 pour une difficulté réelle ; autres familles (planification, énigmes logiques, règles de grille).
5. Reprendre Input (lot 4) et, si l'utilisateur le souhaite, le projet code (§11).

Règles d’hygiène retenues : jamais de sélection sur un split réservé ; toute nouvelle sélection sur un banc neuf ; données de professeur variées ; rapports écrits avant d’annoncer un résultat ; limites et incertitudes annoncées avec les chiffres.
- **Modèle de raisonnement : deuxième famille et transfert** (`outputs/verifications/loop-transfert-resultats.md`). Un seul Loop fait aussi bien que deux spécialistes sur sudoku 6×6 et coloration de graphe (1,00 / 0,94 et 0,99 / 0,95), généralise aux graphes plus grands (0,95) ; transfert sudoku vers coloration partiel (0,51), inverse nul, en partie à cause du vocabulaire de valeurs.
- **Garry Zéro lancé (18 octobre 2026)** : moteur Puissance 4 vectorisé (identique aux règles de Garry sur 60 parties), MCTS par lots, réseau politique-valeur de 304 300 paramètres, auto-apprentissage sans professeur ; première session de 60 minutes en cours. Puis Go 9×9 (moteur de règles rapide à écrire).

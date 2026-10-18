# Logic Lab — bilan et plan global

Mis à jour le 18 octobre 2026. Ce document est le plan principal de la conversation et remplace l’ordre des priorités des anciens rapports. L’exécution commence par l’interface et l’utilisation. Le projet d’agent producteur de code est écarté.

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

### Périmètre actif des chantiers (proposé le 18 octobre 2026, à valider)

Pour ne pas disperser un petit modèle et un seul GPU :

| Statut | Chantier |
|---|---|
| **Actif** | Input : interface (lot 1), puis fiabilité et périmètre (lot 2), contrat JSON/Markdown (lot 3). |
| **En veille, non lancé** | Garry : maintenance et tests uniquement ; pas de nouvelle campagne avant le lot 6. |
| **Gelé** | HRM, TRM et canal latent : aucun entraînement avant que les lots 1 à 4 donnent une base mesurée. Le choix du cœur se fait au lot 5, sur le banc de 300 situations. |

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

## 9. État d'avancement

- **Lot 1 (interface Input) : recette faite le 18 octobre 2026**, voir `outputs/verifications/recette-lot1-input-2026-10-18.md`. Seuils du §8 atteints ; l'attente à froid est corrigée par le préchargement. Reste non couvert : migration des anciennes conversations, page Bilan, copie réelle.
- **Constat décisif pour la suite :** l'interface est utilisable, le modèle ne l'est pas encore. Il ignore le contexte (prénom), s'effondre sur un gabarit « commande » et rate un planning simple. Le lot 2 (banc de régression) et le lot 4 (données) passent donc avant toute autre piste.
- **Lot 2 (banc de régression) : fait le 18 octobre 2026**, voir `outputs/verifications/baseline-lot2-input-0.2.0.md`. Banc v1.0.0 gelé (2 × 51 cas, empreintes vérifiées par le lanceur). Baseline Input 0.2.0 : 54,2 % sur dev, 47,7 % sur test ; 86 % de réponses affirmées sur des questions sans réponse. Cibles du lot 4 fixées dans le rapport. Le lot 3 (contrat JSON/Markdown) reste à faire.

## 10. Famille Garry et Lab (décidé le 18 octobre 2026)

Direction « laboratoire » à côté du lot 4 d'Input. Principe : un **Garry Core** propre (entrées et sorties typées, crochets pour capturer les activations, éteindre un neurone, sauvegarder un checkpoint) et des variantes qui sont des configurations de ce Core, observables dans un onglet **Lab** du site.

| Variante | Définition retenue |
|---|---|
| **Garry Games** | Le Garry actuel, 14 jeux. |
| **Garry Loop** | Le cœur récurrent : un bloc repassé plusieurs fois sur son propre état, avec arrêt appris. |
| **Garry Mind** | Pas un modèle séparé : une amélioration du schéma de boucle sur les modèles existants pour qu'ils réfléchissent plus, et à plus de choses (budget de calcul adaptatif, proposer-vérifier-corriger, auto-cohérence). |
| **Garry Input** | Fork avancé d'un petit modèle de langage (Qwen3-0.6B ou autre, à départager sur le banc de régression), pas un réseau minuscule de zéro. |
| **Garry Prime** | Routeur plus distillation des variantes : compromis force/taille mesuré, pas de promesse « le plus fort partout ». |
| **Graine** (B) | Croissance et élagage des neurones, d'abord sur Garry (morpion, Puissance 4, Nim), visible dans le Lab. |
| **Règles** (C) | Exploration : jouer un jeu jamais vu à partir de ses règles ; en pari, après Loop et Graine. |

Ordre : (1) Garry Core avec **test de parité** exact sur les 14 jeux contre les poids 0.6.0 ; (2) Lab v1 (réseau en direct, chirurgie, retour dans le temps, banc en direct) ; (3) Graine ; (4) Loop et Mind ; (5) Règles ; (6) Prime. Le lot 4 d'Input continue en parallèle ; le Lab y sert à voir ce que l'adaptation change.

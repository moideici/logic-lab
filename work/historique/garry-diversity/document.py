from pathlib import Path
import json
ROOT=Path(r'C:\Users\gabor\code\playi');OUT=Path(__file__).parent/'documentation'
def write(p,s):
    f=OUT/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8',newline='\n')
r=json.loads((ROOT/'web/models/garry-diversity-evaluation.json').read_text());solo=json.loads((ROOT/'web/models/garry-diversity-solo-evaluation.json').read_text())
names={'tictactoe':'Morpion','connect4':'Puissance 4','2048':'2048','sudoku':'Sudoku','minesweeper':'Démineur','sliding_puzzle':'Taquin'}
doc='''# Garry 3.1.0 : un répertoire plus varié

Travail appliqué le 16 octobre 2026 dans `C:\\Users\\gabor\\code\\playi`.

Garry dispose maintenant d’un magasin de **2 523 épreuves d’entraînement** couvrant les six jeux. Il les rejoue automatiquement pendant l’entraînement dans l’application, en mélangeant les catégories et en donnant davantage de place aux erreurs. Les exemples peuvent enseigner plusieurs bons coups dans une même position.

Le numéro **3.1.0** correspond à cette fonctionnalité d’apprentissage et de contrôle. Les dimensions et l’architecture restent celles de 3.0.0 ; les performances ne déterminent pas le numéro de version. Un seul Garry est toujours chargé et exporté.

## De la variété vérifiable

Le lot principal contient **8 051 positions distinctes après déduplication** : 6 130 pour apprendre, 963 pour choisir les checkpoints et 958 pour les épreuves finales. Les familles de parties et de puzzles sont séparées ; aucun identifiant de position ni de famille ne traverse ces trois ensembles. Les symétries pertinentes sont dédupliquées, puis les orientations équivalentes des exemples d’entraînement sont ajoutées dans leur propre ensemble. Le taquin n’est pas simplement retourné : cela changerait son but.

| Jeu | Variété ajoutée |
|---|---|
| Morpion | États jouables regroupés par symétrie ; victoire, maintien du nul et résistance dans une position perdante |
| Puissance 4 | Huit profils de génération, plusieurs associations d’adversaires, débuts, milieux, fins, blocages, fourchettes et pièges de support ; trajectoires légales prolongées pour atteindre des fins de partie |
| 2048 | Parties jouées avec plusieurs stratégies et plateaux synthétiques explicitement identifiés, encombrés ou proches d’une fusion importante |
| Sudoku | Nouvelles grilles créées par recherche aléatoire, à solution unique vérifiée ; déduction, réparation d’une mauvaise hypothèse et fin de résolution |
| Démineur | Ouvertures au centre, aux bords et aux coins ; frontières sûres et décisions sous incertitude, à partir des indices publics |
| Taquin | Mélanges courts et permutations solvables variées ; distances courtes, moyennes et longues vérifiées par la table exacte |

La génération est plus variée sans prétendre être uniforme sur toutes les positions possibles. Les professeurs de Puissance 4, 2048 et démineur sont bornés ou probabilistes : leurs étiquettes ne sont pas des preuves universelles du meilleur coup. Les familles de sudoku sont séparées par puzzle, avec normalisation des chiffres et des symétries utilisées ; il ne s’agit pas d’une classification exhaustive de toutes les équivalences de sudoku.

## Ce que Garry a appris et ce qui a été installé

La nouvelle méthode apprend une distribution de bonnes réponses, au lieu d’imiter systématiquement un seul coup. Les catégories et les erreurs d’entraînement influencent la fréquence de répétition. Le module commun et l’évaluateur de Puissance 4 sont gelés pendant cette adaptation ; seules les zones privées des jeux sont modifiées. Le candidat de chaque jeu est choisi sur la validation avant d’ouvrir ses tests.

Résultats du **réseau seul sur les positions finales réservées aux tests**, avant et après l’installation. Ces pourcentages désignent un choix de coup conforme au professeur, pas un taux de parties gagnées.

| Jeu | Positions de test | Avant | Modèle actif | Poids nouveaux retenus |
|---|---:|---:|---:|---|
'''
for g in names:
    before=r['selection'][g]['before_test']['optimal_choice_rate'];after=r['active_test_metrics'][g]['optimal_choice_rate'];n=r['active_test_metrics'][g]['samples']
    doc+=f"| {names[g]} | {n} | {before*100:.1f} % | {after*100:.1f} % | {'Oui' if g in r['installed_games'] else 'Non'} |\n"
doc+='''
Les poids installés concernent **sudoku, démineur et taquin**. Ceux du morpion, de Puissance 4 et de 2048 restent identiques au modèle 3.0.0 conservé.

Les candidats de morpion et Puissance 4 ont échoué à certains contrôles de compétences, même lorsque leur erreur d’imitation baissait. Pour la sélection de Puissance 4, une mesure supplémentaire reconnaît aussi les coups à moins de 24 points du meilleur score borné, sans sacrifier un résultat prouvé ; les victoires et défenses critiques restent contrôlées séparément. Ce candidat n’a malgré tout pas été installé.

Le candidat 2048 semblait meilleur sur les positions et les parties arrêtées après 500 coups. En prolongeant jusqu’à 2 000 coups, il obtenait les mêmes quatre victoires sur huit, avec un score total légèrement inférieur : 145 596 contre 146 320. Il a été écarté et les poids précédents ont été rétablis. Le nouveau magasin d’exemples de 2048 reste disponible pour les prochaines séances.

## Des épreuves de parties différentes

Une ligue comprend **sept adversaires** : aléatoire, préférence pour le centre, préférence pour les bords, tactique, anciennes versions 1.0 et 2.0, et champion 3.0 conservé. Chaque duel est rejoué dans les deux camps ; les départs incluent le plateau vide, des préfixes légaux variés et des positions des familles finales réservées aux tests.

Il y a 168 duels par modèle, soit 336 parties de comparaison. Au Puissance 4, avant et après obtiennent chacun **109 victoires, 35 défaites, 24 nuls**. Les poids de ce mode n’ont pas changé : aucun progrès de force au Puissance 4 n’est revendiqué dans ce cycle. Les adversaires de recherche utilisent 50 000 nœuds, sauf la référence 1.0 limitée à 5 000 ; le joueur tactique n’explore pas d’arbre. Ce lot, plus difficile et différent, ne se compare pas directement aux 40 parties du rapport précédent. Aucune défaite n’est retirée.

Le modèle effectivement installé a également été testé sur huit parties ou puzzles par jeu solo, avec les mêmes graines et des budgets de nœuds fixes :

| Jeu | Avant | Modèle actif | Précision |
|---|---|---|---|
'''
for g,v in solo['games'].items():
    b=v['before'];a=v['after'];precision='Parties complètes, aucune troncature' if g in ('2048','minesweeper') else 'Familles de puzzles inédites dans ce lot'
    doc+=f"| {names[g]} | {b['wins']}/8 réussites | {a['wins']}/8 réussites | {precision} |\n"
doc+='''
Au sudoku et au taquin, la planification exacte était déjà déterminante ; l’amélioration du réseau ne change pas leurs huit résolutions sur huit dans ce contrôle. Au démineur, le passage de six à sept réussites sur huit reste un petit échantillon et ne démontre pas une supériorité statistique générale. Les apparitions de tuiles et les mines sont simulées par les règles ; les agents ne reçoivent jamais les mines cachées.

## Un magasin durable et des erreurs utiles

- `web/models/garry-repertoire.json` contient les 2 523 exemples compacts, uniquement issus de l’entraînement. Les catégories sont mélangées et les exemples difficiles sont rejoués plus souvent.
- `training-runs/garry-diversity-balanced-20261016/training-errors.json` conserve 3 340 erreurs de la politique initiale sur les exemples d’entraînement ; elles sont réutilisables.
- Les 35 trajectoires perdantes des épreuves finales sont conservées à part dans `quarantined-errors.json`. Elles ne sont pas réinjectées dans l’entraînement pendant que ces épreuves servent de test. Leur réutilisation future exige de retirer ces épreuves du contrôle et d’en créer de nouvelles.
- L’entraînement dans le navigateur combine encore des parties nouvelles avec le magasin et des rappels des autres jeux. Son statut affiche combien d’épreuves distinctes ont été rejouées. Il ne change pas la priorité du niveau 10 : rechercher le meilleur coup disponible.

La validation du magasin refuse les exemples marqués test/validation, les distributions de coups invalides, les doublons et les champs d’état privé. Les familles des autres jeux ne sont pas modifiées par une adaptation protégée ; l’entraînement interactif général reste, lui, capable de modifier le module commun.

## Vérifications et reproduction

**77 tests passent** : 52 Python et 25 JavaScript. Ils couvrent les contrôles précédents, les nouvelles grilles à solution unique, les transformations, les distributions de bons coups, les gradients privés, la protection des autres modes et l’exclusion des données réservées aux tests.

Le navigateur a été vérifié sur les six jeux, aux niveaux 0 et 10, avec export unique, stockage et rechargement. Un entraînement de trois épisodes a réellement chargé les 2 523 épreuves et en a rejoué neuf distinctes. Aucun message d’erreur de page.

Commandes depuis le dépôt :

```text
python examples/build_garry_repertoire.py --source versions/3.0.0/garry.json --output training-runs/nouveau-lot --seed 16036100 --c4-train 4096 --c4-heldout 512 --solo-train 384 --solo-heldout 96
python examples/train_garry_repertoire.py --source versions/3.0.0/garry.json --dataset training-runs/nouveau-lot/dataset.json --output training-runs/nouveau-lot/training --epochs 120
node examples/benchmark_garry_league.mjs --after training-runs/nouveau-lot/training/candidate.json --dataset training-runs/nouveau-lot/dataset.json --output training-runs/nouveau-lot/league.json
node examples/benchmark_garry_solo_trials.mjs training-runs/nouveau-lot/training/candidate.json training-runs/nouveau-lot/dataset.json training-runs/nouveau-lot/solo-trials.json
python -m unittest discover -s tests
node --test tests/garry.test.mjs tests/web.test.mjs tests/levels.test.mjs tests/repertoire.test.mjs
```

La construction et l’entraînement produisent des candidats séparés ; ils n’écrasent pas automatiquement le modèle actif. Les rapports livrés sont `web/models/garry-diversity-evaluation.json` et `garry-diversity-solo-evaluation.json`. Le modèle 3.0.0 précédent est conservé avec ses empreintes dans `versions/3.0.0/`.
'''
write('docs/GARRY-DIVERSITE.md',doc)
outputs=Path(r'C:\Users\gabor\code\logic-lab\outputs');(outputs/'Garry-repertoire-diversite.md').write_text(doc,encoding='utf-8');(outputs/'Garry-diversite-resultats.json').write_text(json.dumps({'evaluation':r,'active_solo':solo},indent=2),encoding='utf-8')
s=(ROOT/'README.md').read_text(encoding='utf-8').replace('# Logic Lab — Garry 3.0.0','# Logic Lab — Garry 3.1.0').replace('version **3.0.0** pour les six modes','version **3.1.0** pour les six modes').replace('`garry-3.0.0.json`','`garry-3.1.0.json`').replace('formats Garry 2.0.0 et 3.0.0','formats Garry 2.0.0, 3.0.0 et 3.1.0')
section='''## Un répertoire varié pour apprendre

La version **3.1.0** ajoute un magasin de **2 523 épreuves** pour les six jeux, sans changer l’architecture. Elles viennent d’un lot de 8 051 positions séparées entre apprentissage, validation et test. La génération varie les adversaires, les phases, les pièges et les puzzles ; les nouvelles grilles de sudoku ont une solution unique vérifiée. L’application rejoue ces exemples pendant l’entraînement, en privilégiant les catégories peu représentées et les erreurs.

Le nouveau modèle retient les poids de sudoku, démineur et taquin qui passent les contrôles. Les candidats de morpion et Puissance 4 sont écartés ; celui de 2048 est aussi écarté après prolongation des parties complètes. Les poids de ces trois modes sont conservés. Le module commun et l’évaluateur de Puissance 4 ne changent pas.

La ligue de sept adversaires et les épreuves solo sont détaillées dans [le rapport de diversité](docs/GARRY-DIVERSITE.md). Les progrès sur les choix du réseau seul sont distingués des victoires avec planification. L’entraînement enseigne plusieurs bonnes réponses quand elles existent ; il n’ajoute pas de coups inférieurs au niveau 10 pour faire varier artificiellement le jeu.

'''
s=s.replace('## Niveau 10 : recherche renforcée',section+'## Niveau 10 : recherche renforcée')
s=s.replace('Les résultats d\'évaluation sont indépendants de cette numérotation', 'L’ajout du répertoire et des nouvelles méthodes d’entraînement justifie 3.1.0 sans changement d’architecture. Les résultats d’évaluation sont indépendants de cette numérotation')
s=s.replace('`versions/2.0.0/` conserve aussi', '`versions/3.0.0/` conserve les poids et le moteur avant ce cycle de diversité. `versions/2.0.0/` conserve aussi')
write('README.md',s.rstrip()+'\n')
historic=(ROOT/'docs/GARRY-3-PROGRESSION.md').read_text(encoding='utf-8');write('docs/GARRY-3-PROGRESSION.md','> Rapport historique de Garry 3.0.0. Voir [le cycle de diversité 3.1.0](GARRY-DIVERSITE.md) pour les changements suivants.\n\n'+historic)
historic=(ROOT/'docs/GARRY-PROGRESSION.md').read_text(encoding='utf-8');write('docs/GARRY-PROGRESSION.md',historic.replace('pour l’état actuel.','pour cette étape ; voir aussi [le cycle de diversité 3.1.0](GARRY-DIVERSITE.md).',1))

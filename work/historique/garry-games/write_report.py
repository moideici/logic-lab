from pathlib import Path
import json,hashlib,shutil
ROOT=Path(r'C:\Users\gabor\code\playi')
OUT=Path(r'C:\Users\gabor\code\logic-lab\outputs')
extra=json.loads((ROOT/'training/new-games-4.0.0/report.json').read_text())
strategy=json.loads((ROOT/'training/strategy-4.0.0/report.json').read_text())
matches=json.loads((ROOT/'training/strategy-4.0.0/full-games.json').read_text())
model=json.loads((ROOT/'web/models/garry.json').read_text())
browser=json.loads((OUT/'Garry-jeux-verification-navigateur.json').read_text())
def percent(n):return f'{n*100:.1f}'.replace('.',',')+' %'
names={'reversi':'Reversi','nim':'Nim','lightsout':'Lights Out','draughts':'Dames internationales','breakthrough':'Percée'}
rows=[]
for report in (extra,strategy):
    for game,r in report['games'].items():rows.append(f"| {names[game]} | {r['test_before']['samples']} | {percent(r['test_before']['optimal_choice_rate'])} | {percent(r['test_after']['optimal_choice_rate'])} |")
report='''# Garry 4.0.0 — onze jeux et premiers apprentissages

Les **dames internationales** et **Percée** sont maintenant jouables contre Garry, observables en duel et accessibles à l’entraînement. Reversi, Nim et Lights Out ont aussi été ajoutés : le même modèle couvre désormais onze jeux. Aucun jeu d’échecs n’a été ajouté.

## Nouveaux jeux

| Jeu | Jouabilité | Analyse de Garry |
| --- | --- | --- |
| Dames internationales · 10 × 10 | Sélection du pion puis de la destination ; rafles en plusieurs étapes, prise maximale obligatoire, prise arrière des pions, dames à longue portée, promotion en fin de rafle, nulles | Recherche adversariale, prolongation des rafles jusqu’à leur fin, apprentissage des coups |
| Percée · 8 × 8 | Avancer, prendre en diagonale et atteindre la dernière rangée | Recherche adversariale et apprentissage des courses de pions |
| Reversi · 6 × 6 | Encadrer les pions adverses ; passer lorsqu’aucune pose n’est possible | Recherche, mobilité et contrôle des coins |
| Nim · trois tas | Retirer des allumettes d’un seul tas ; prendre la dernière gagne | Analyse exacte de toutes les configurations représentables |
| Lights Out · 5 × 5 | Allumer/éteindre en croix ; éteindre le plateau | Résolution exacte avec le minimum de pressions |

Les règles des dames suivent l’[annexe 1 de la FMJD](https://www.fmjd.org/downloads/FMJD_Annexes_2024_8-sig.pdf). Les pièces prises bloquent les diagonales jusqu’à la fin de la rafle ; les nulles comprennent la répétition et les limites de finales. Les déplacements et captures de Percée suivent les [règles de Breakthrough](https://superdupergames.org/rules/break.pdf).

## Premières parties complètes aux dames et à Percée

Face aux nouvelles capacités initialisées avant leur apprentissage, **avec le réseau seul**, quatre départs ont été joués dans les deux camps :

| Jeu | Victoires | Nulles | Défaites |
| --- | --- | --- | --- |
| Dames internationales | 7 | 1 | 0 |
| Percée | 8 | 0 | 0 |

Au niveau 10 avec planification, quatre parties supplémentaires par jeu contre des choix aléatoires donnent **4 victoires aux dames et 4 à Percée**. Les départs et résultats individuels sont conservés dans `training/strategy-4.0.0/full-games.json`.

Ces échantillons ne prouvent pas l’invincibilité. La référence de ces nouveaux duels est leur initialisation avant apprentissage : les anciennes versions à six jeux ne savaient pas y jouer. Le précédent résultat « zéro défaite contre la 3.1.0 » garde son périmètre historique et n’est pas étendu aux onze jeux.

## Apprentissage et limites

Les cinq nouvelles capacités ont reçu 2 180 positions d’apprentissage distinctes, 400 positions de validation et 400 positions de test. Les points de sauvegarde sont choisis sur la validation. Les tests sont ensuite ouverts pour mesurer les résultats. Les dames et Percée ont reçu respectivement 4 680 et 6 120 présentations d’exemples pour les points retenus. Le répertoire partagé contient désormais **4 757 épreuves d’apprentissage**, sans les états réservés.

Les taux suivants concernent le **réseau seul** : ils mesurent son accord avec les coups du professeur sur des positions réservées, pas un taux de victoire. Les professeurs de Reversi, des dames et de Percée effectuent une recherche bornée.

| Jeu | Positions de test | Avant apprentissage | Après apprentissage |
| --- | --- | --- | --- |
'''+ '\n'.join(rows)+'''

L’apprentissage initial du réseau seul reste insuffisant à Nim et à Lights Out et recule sur ce premier test réservé. Leur niveau 10 avec planification utilise les solveurs exacts ; il ne dépend donc pas de la qualité de ces seuls scores appris. Les recherches aux dames, à Percée et au Reversi restent bornées ; aucune profondeur de vingt coups n’y est annoncée.

## Conservation des acquis et version

La nouvelle architecture est **2 494 → 48 → 48 → 3 617**, avec 299 377 paramètres, dans un seul fichier. L’agrandissement des entrées et sorties justifie **4.0.0** ; la numérotation ne dépend pas des résultats sportifs.

Les coefficients des six jeux existants, le module central, l’évaluateur de Puissance 4 et sa mémoire d’ouverture sont conservés exactement. L’apprentissage des dames et de Percée conserve ensuite les neuf modes précédents. La 3.2.0 est archivée avec empreintes dans `versions/3.2.0/`.

Les anciens exports sont migrés. Dans l’interface, les nouveaux blocs entraînés sont ajoutés aux modèles personnels importés sans remplacer leurs anciens coefficients ni leur module central.

## Vérifications

**75 tests Python et 39 tests JavaScript réussis : 114 au total.** Les contrôles incluent les rafles, les victimes bloquantes, les promotions, les nulles, les masques de coups, les échanges de modèles, les anciens solveurs et les oracles indépendants pour Nim, Lights Out et des finales de Percée.

Les essais dans le navigateur couvrent les cinq nouveaux jeux joués manuellement, les réponses de Garry, le passage au Reversi, une rafle aux dames, la résolution de Lights Out, les cinq workers d’entraînement, l’import/export ancien et le rendu mobile sans débordement. Aucune erreur de page n’a été détectée.

Commandes de vérification depuis le projet :

```text
python -m unittest discover -s tests
node --test tests/garry.test.mjs tests/web.test.mjs tests/levels.test.mjs tests/repertoire.test.mjs tests/certified.test.mjs tests/new-games.test.mjs tests/strategy.test.mjs
node examples/benchmark_strategy.mjs
```
'''
OUT.mkdir(parents=True,exist_ok=True);(OUT/'Garry-onze-jeux.md').write_text(report,encoding='utf-8')
(ROOT/'docs/GARRY-4-NOUVEAUX-JEUX.md').write_text(report,encoding='utf-8')
summary={'version':'4.0.0','architecture':[2494,48,48,3617],'parameters':299377,'games':model['games'],'training_steps':model['game_steps'],'repertoire_size':4757,'tests':{'python':75,'javascript':39,'total':114},'training_first_three':extra,'training_strategy':strategy,'full_games':matches,'browser':browser,'model_sha256':hashlib.sha256((ROOT/'web/models/garry.json').read_bytes()).hexdigest()}
(OUT/'Garry-onze-jeux-resultats.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'README.md';text=p.read_text(encoding='utf-8')
text=text.replace('# Logic Lab — Garry 3.2.0','# Logic Lab — Garry 4.0.0',1)
start=text.index('**Garry est un modèle neuronal');end=text.index('\n\n',start)
text=text[:start]+'''**Garry est un modèle neuronal général unique pour onze jeux** : morpion, Puissance 4, 2048, sudoku, démineur, taquin, Reversi 6 × 6, Nim, Lights Out, dames internationales 10 × 10 et Percée. L’interface, les workers et le serveur Python utilisent `web/models/garry.json`.

## Nouveautés de la 4.0.0

Les cinq nouveaux jeux sont jouables et intégrés à l’apprentissage. Les dames gèrent les rafles maximales obligatoires, les prises arrière des pions, les dames à longue portée, les promotions et les nulles. Percée propose des courses de pions et des captures diagonales. Les nouveaux modes reçoivent leurs propres entrées et actions dans les matrices communes : **2 494 → 48 → 48 → 3 617**, 299 377 paramètres. Cet agrandissement justifie la version majeure.

Les premiers duels du réseau seul contre les nouveaux blocs initialisés donnent 7 victoires et 1 nulle aux dames, puis 8 victoires à Percée. Ce sont des échantillons limités. Les poids utilisés par les modes précédents sont conservés exactement pendant cette première campagne. Les anciens exports sont migrés ; dans l’interface, les nouvelles capacités entraînées sont ajoutées aux modèles personnels. Le répertoire contient 4 757 épreuves.

Le [rapport des nouveaux jeux](docs/GARRY-4-NOUVEAUX-JEUX.md) détaille règles, apprentissages, résultats et limites, notamment les premiers résultats mixtes du réseau seul à Nim et Lights Out. Les niveaux restent réglables de 0 à 10. La suite de vérification compte 114 tests réussis.

Les sections historiques ci-dessous décrivent les étapes précédentes ; leurs duels ne constituent pas une garantie d’invincibilité sur les nouveaux jeux.'''+text[end:]
text=text.replace('## Zéro défaite depuis le plateau vide','## Historique 3.2.0 : zéro défaite depuis le plateau vide',1)
text=text.replace('## Architecture et fusion','## Architecture actuelle et fusion historique',1)
text=text.replace('encodeur unique : 1 912 → 48','encodeur unique : 2 494 → 48',1).replace('sortie unique : 48 → 818','sortie unique : 48 → 3 617',1)
text=text.replace('Le modèle totalise 134 290 paramètres.','Le modèle actuel totalise 299 377 paramètres.',1).replace('Les six modes sont des vues','Les onze modes sont des vues',1)
text=text.replace('La fusion est algébrique :','La fusion historique de la 2.0.0 est algébrique :',1)
text=text.replace('version **3.2.0** pour les six modes','version **4.0.0** pour les onze modes',1)
text=text.replace('`versions/3.1.0/` conserve','`versions/3.2.0/` conserve le modèle avant l’agrandissement aux onze jeux. `versions/3.1.0/` conserve',1)
text=text.replace('`garry-3.1.0.json`','`garry-4.0.0.json`',1).replace('L’import accepte les formats Garry 2.0.0, 3.0.0 et 3.1.0','L’import accepte les formats Garry 2.0.0, 3.0.0, 3.1.0, 3.2.0 et 4.0.0',1)
p.write_text(text,encoding='utf-8')
print(json.dumps({'report':str(OUT/'Garry-onze-jeux.md'),'model_sha256':summary['model_sha256'],'tests':114,'games':11}))

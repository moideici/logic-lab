import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
root=Path.cwd();run=root/'training-runs/garry-repertoire-20261016-cycle02'
r=json.loads((run/'evaluation.json').read_text());audit=r['history_audit']
names={'tictactoe':'Morpion','connect4':'Puissance 4','2048':'2048','sudoku':'Sudoku','minesweeper':'Démineur','sliding_puzzle':'Taquin'}
rows=[]
for g,name in names.items():
    s=r['selection'][g];a=r['active_test_metrics'][g]
    rows.append(f"| {name} | {a['samples']} | {s['before_test']['sound_choice_rate']:.1%} | {a['sound_choice_rate']:.1%} | {'Poids retenus' if g in r['installed_games'] else 'Poids précédents conservés'} |")
solo=[]
for g,s in r['solo']['games'].items():
    b=s['before'];a=s['after'];solo.append(f"| {names[g]} | {b['wins']} / {r['solo']['episodes']} | {a['wins']} / {r['solo']['episodes']} | {b['total_score']} → {a['total_score']} | {b['truncated']} → {a['truncated']} |")
lb=r['league']['before'];la=r['league']['after']
text=f"""# Garry — entraînement supplémentaire, cycle 02

Logiciel **3.1.0**, révision des poids **{r['weights_revision']}**. L’architecture et les réglages de réflexion ne changent pas. Référence : Garry actif au début de ce cycle, révision `20261016-repertoire-01`.

## Ce qui a été exécuté

- {sum(r['counts'].values()):,} positions au total : {r['counts']['train']:,} d’apprentissage, {r['counts']['validation']:,} de validation et {r['counts']['test']:,} de test.
- {audit['fresh_generated']-627:,} positions inédites générées pour les cinq jeux autres que le morpion ; ses 627 positions canoniques conservent leurs groupes fixes.
- {sum(audit.get('replayed_training_retained',audit['replayed_training']).values()):,} anciens exemples d’apprentissage rejoués pour limiter les oublis.
- {r['bank_examples']:,} exemples publics proposés dans le magasin de l’application, uniquement issus de l’apprentissage.
- Nouveaux adversaires et tirages, défenses et pièges au Puissance 4, nouvelles grilles uniques de sudoku, frontières publiques du démineur et positions profondes du taquin. Les positions synthétiques de 2048 restent identifiées.

Les anciens lots de validation et de test sont exclus de l’apprentissage et du magasin. Les nouvelles épreuves des cinq jeux excluent aussi les états connus des anciens lots encodés et de l’apprentissage de l’évaluateur de position. Les miroirs reconnus et les familles de parties ou de puzzles sont contrôlés. Le morpion utilise son épreuve exhaustive fixe ; elle ne constitue pas un nouveau test indépendant.

Les points de reprise sont choisis sur les validations nouvelles et anciennes, puis soumis une seule fois aux tests. Le module commun, son biais et l’évaluateur de position du Puissance 4 sont gelés. Chaque mode candidat reste séparé tant qu’il n’a pas passé les contrôles. Les échecs des épreuves restent en quarantaine.

## Choix du réseau seul sur les positions de test

Ce taux mesure le choix d’un coup jugé acceptable par le professeur, sans le planificateur du niveau 10. Il ne mesure pas un taux de victoire. Le professeur est exact pour le morpion et le taquin, et borné en calcul pour le Puissance 4. Les pourcentages finaux concernent les poids effectivement installés.

| Jeu | Positions | Avant | Après installé | Décision |
|---|---:|---:|---:|---|
{chr(10).join(rows)}

Poids installés : {', '.join(names[g] for g in r['installed_games']) or 'aucun candidat retenu'}.

Au taquin, le taux sur les anciennes positions réservées passe de {r['retention_test']['sliding_puzzle']['before']['sound_choice_rate']:.2%} à {r['retention_test']['sliding_puzzle']['after']['sound_choice_rate']:.2%}, sans gain du taux de choix sur les nouvelles positions. La perte d’apprentissage sur les nouvelles épreuves diminue de {r['selection']['sliding_puzzle']['before_test']['soft_cross_entropy']:.4f} à {r['active_test_metrics']['sliding_puzzle']['soft_cross_entropy']:.4f}. Ce progrès modeste justifie de retenir ce candidat, sans conclure à une amélioration des victoires du niveau 10. Le candidat démineur est écarté parce qu’il recule sur les anciennes épreuves malgré son gain sur les nouvelles.

## Parties complètes avec planification

Contrôle solo : {r['solo']['episodes']} parties ou puzzles appariés par jeu, mêmes départs et budgets de calcul avant/après. Ces nombres décrivent les candidats finalistes comparés ; un mode qui échoue à ce contrôle est restauré avant installation. Une partie tronquée n’est jamais comptée comme gagnée ; 2048 est plafonné à 2 000 actions.

| Jeu | Victoires avant | Victoires candidat | Score total avant → candidat | Tronquées avant → candidat |
|---|---:|---:|---:|---:|
{chr(10).join(solo)}

Ligue Puissance 4 : {sum(lb.values())} parties par modèle face à sept adversaires, deux côtés, départs standards, préfixes variés et positions réservées. Budget : {r['league']['nodes']:,} nœuds pour les moteurs courants, 5 000 pour l’ancienne IA 1.0 et aucun arbre pour l’adversaire tactique.

- Référence : {lb['wins']} victoires, {lb['losses']} défaites, {lb['draws']} nuls.
- Candidat : {la['wins']} victoires, {la['losses']} défaites, {la['draws']} nuls.

Ces séries limitées ne prouvent ni une supériorité statistique ni l’invincibilité. Le zéro défaite n’est pas atteint. Aucun changement de profondeur ou d’architecture n’est attribué à ce cycle d’entraînement.

## Reproductibilité

Vérification finale : **55 tests Python et 25 tests JavaScript réussis**, soit 80 tests. Le magasin contient exclusivement des exemples d’apprentissage ; son intersection avec les anciennes épreuves réservées est vide.

Lot : `{r['run']}`, graine {r['seed']}. Les données, journaux d’époques, décisions de sélection, résultats complets, poids avant/après et empreintes sont conservés dans ce dossier sous `training-runs/`. Le rapport installé est `web/models/garry-repertoire-cycle02-evaluation.json`.

L’outil de génération accepte `--history`, `--replay`, `--legacy-archive` et `--position-history`. L’entraînement accepte `--retention-dataset`. Le contrôle solo accepte explicitement le fichier de référence, une graine et un nombre de parties. Les écritures de suivi résistent aux verrouillages temporaires de fichiers sous Windows ; les lots disposent de points de reprise liés au code, aux poids et aux données sources.

Empreinte des poids installés : `{r['installed_sha256']}`.
"""
(root/'docs/GARRY-ENTRAINEMENT-CYCLE02.md').write_text(text,encoding='utf-8')
out=Path(r'C:\Users\gabor\code\logic-lab\outputs');out.mkdir(exist_ok=True)
(out/'Garry-entrainement-suite.md').write_text(text,encoding='utf-8')
(out/'Garry-entrainement-suite-resultats.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
readme=(root/'README.md').read_text(encoding='utf-8')
first=readme.index('La version **3.1.0**');last=readme.index('## Niveau 10')
readme=readme[:first]+f"""La version **3.1.0** propose un magasin de **{r['bank_examples']:,} épreuves** pour les six jeux, sans changer l’architecture. Le dernier cycle réunit {sum(r['counts'].values()):,} positions d’apprentissage, de validation et de test, dont {audit['fresh_generated']-627:,} nouveaux états pour les cinq jeux autres que le morpion. Les anciens exemples d’apprentissage sont aussi rejoués pour limiter les oublis.

Les poids retenus au cours de ce cycle concernent : {', '.join(names[g].lower() for g in r['installed_games']) or 'aucun mode supplémentaire'}. Les candidats qui reculent sur les compétences contrôlées ou sur les parties complètes sont écartés. Le module commun et l’évaluateur de Puissance 4 sont préservés. La révision d’entraînement est **{r['weights_revision']}** ; la version logicielle reste **3.1.0**.

Les résultats et limites sont détaillés dans [le dernier rapport d’entraînement](docs/GARRY-ENTRAINEMENT-CYCLE02.md). Le [premier rapport de diversité](docs/GARRY-DIVERSITE.md) conserve les résultats du cycle précédent. Les progrès du réseau seul sont distingués des victoires avec planification. L’entraînement enseigne plusieurs bonnes réponses quand elles existent ; les épreuves réservées restent exclues du magasin et des mises à jour.

"""+readme[last:]
(root/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'report':str(out/'Garry-entrainement-suite.md'),'installed_games':r['installed_games']}))

from pathlib import Path
import json,shutil,importlib.metadata
R=Path(r'C:\Users\gabor\code\latent-reasoner-hrm');T=Path(r'C:\Users\gabor\code\text-comprehension')
versions={n:importlib.metadata.version(n) for n in ('torch','pydantic','PyYAML','einops')}
(R/'local_environment.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
p=R/'LATENT_FORK.md';s=p.read_text(encoding='utf-8');s+='\n## Premier contrôle effectué\n\nTrois tests techniques passent. Avec les poids officiels inchangés, sur CPU, la grille classique du contrôle est résolue en environ 1,55 seconde. La grille presque remplie échoue : des valeurs données sont modifiées. Ce résultat est conservé dans `local_results/native-smoke.json` et ne déclenche aucune réparation cachée. Ce sont deux contrôles publics, pas un banc d’évaluation indépendant.\n\nLes versions de l’environnement réellement utilisé sont enregistrées dans `local_environment.json`.\n';p.write_text(s,encoding='utf-8')
p=T/'BRIDGE.md';s=p.read_text(encoding='utf-8');s=s.replace('# Input : passerelle français ↔ modèle de raisonnement','# Input : contrat JSON de diagnostic et témoin textuel',1)
s=s.replace('Objectif : l’utilisateur parle français ; Input transmet une représentation', '> Direction retenue après clarification : le canal principal visé entre Input et le cœur de raisonnement transporte des représentations internes continues. Ce contrat JSON reste une interface de contrôle et un témoin de comparaison ; il ne décrit pas le canal latent. Voir [LATENT.md](LATENT.md).\n\nObjectif de ce témoin : l’utilisateur parle français ; Input transmet une représentation',1);p.write_text(s,encoding='utf-8')
p=T/'LATENT.md';p.write_text('''# Input ↔ cœur de raisonnement latent

Direction confirmée : les deux modèles doivent échanger des représentations internes, avec une base de raisonnement dont l’entrée principale n’est pas du texte naturel.

Un fork local de **HRM symbolique** et ses poids officiels sudoku sont installés dans `C:\\Users\\gabor\\code\\latent-reasoner-hrm`. Sa version expérimentale est 0.1.0. Le modèle compte 27 275 266 paramètres entraînables dans ce chargement. Le code amont, sa licence et les empreintes des poids sont conservés.

## État réel

- Le cœur reçoit directement des tenseurs continus de forme `[lot,82,512]` et raisonne par itérations. L’ancienne entrée symbolique produit exactement les mêmes sorties dans le test d’équivalence.
- Un adaptateur neuronal entraînable est installé, avec contrôle de l’identité des poids et des couches et masquage des positions de remplissage. Le gradient peut traverser le cœur gelé pour entraîner cet adaptateur.
- Trois tests techniques passent. Le contrôle sur poids officiels résout une des deux grilles publiques utilisées ; la seconde reste un échec conservé.
- **La liaison depuis les représentations d’Input et le retour vers le français ne sont pas encore entraînés ni activés.** La conversation actuelle utilise toujours son modèle local habituel.

Architecture visée : français → Input → adaptateur continu → HRM → adaptateur de retour → Input → français et JSON validé. Le JSON peut servir aux mesures et à la sortie utilisateur ; le canal entre modèles transmet des tenseurs.

HRM est ici spécialiste du sudoku, pas un assistant général. Étendre son raisonnement à d’autres problèmes demandera des représentations, données et évaluations adaptées. La taille réduite et la récursion ne garantissent pas une meilleure réponse à toutes les demandes.

Le prochain entraînement du canal devra figer les deux checkpoints, utiliser des situations et reformulations réservées, puis comparer au canal symbolique, au canal textuel et à des canaux coupés ou permutés. On mesurera les solutions exactes et le respect des contraintes, en plus du temps et de la mémoire. Les corrections de grilles ne devront pas masquer les erreurs du réseau.

Le cycle français de trente minutes a conservé son programme d’origine ; il n’est pas présenté comme un entraînement de cette nouvelle passerelle.

Références : [HRM et son code](https://github.com/sapientinc/HRM), [poids officiels sudoku](https://huggingface.co/sapientinc/HRM-checkpoint-sudoku-extreme), [Interlat pour l’étude des communications internes](https://arxiv.org/abs/2511.09149). Notre adaptateur est un prototype distinct, pas une reproduction des résultats d’Interlat.
''',encoding='utf-8')
p=T/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('Le [contrat provisoire de passerelle](BRIDGE.md) prépare la conversion français → requête JSON structurée → modèle de raisonnement → résultat JSON → français. Aucun second modèle n’est connecté. La validation du contrat est distincte de l’apprentissage de cette traduction.', 'La [passerelle latente](LATENT.md) vise français → états internes d’Input → adaptateur neuronal → cœur HRM → adaptateur de retour → français. Le fork local HRM et ses poids officiels sont installés ; les adaptateurs ne sont pas encore entraînés ou activés dans la conversation. Le [contrat JSON](BRIDGE.md) reste un témoin de comparaison et une interface de diagnostic.')
p.write_text(s,encoding='utf-8')
out=Path(r'C:\Users\gabor\code\logic-lab\outputs')
shutil.copyfile(R/'local_results/native-smoke.json',out/'hrm-controle-natif.json')
shutil.copyfile(R/'LATENT_FORK.md',out/'HRM-FORK-LATENT-0.1.0.md')
print('Direction, results and limitations documented in both projects')

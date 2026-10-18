from pathlib import Path
import shutil
R=Path(r'C:\Users\gabor\code\text-comprehension');S=Path(__file__).parent
shutil.copyfile(S/'test_chat.py',R/'tests/test_chat.py')
p=R/'serve.py';t=p.read_text(encoding='utf-8').replace('if not 0<n<=20000:',"if not 0<n<=(256000 if self.path=='/api/chat' else 20000):");p.write_text(t,encoding='utf-8')
p=R/'README.md';t=p.read_text(encoding='utf-8');t=t.replace('# Compréhension du français — prototype 0.1.0','# Logic Lab Input — prototype 0.2.0');t=t.replace('Première tâche : lire un court texte français et classer une affirmation comme **confirmée**, **contredite** ou **indéterminée**. Il ne s’agit pas encore d’un assistant conversationnel.','La page locale permet maintenant une conversation en français avec historique et sorties JSON contraintes. Le premier classifieur d’affirmations et sa comparaison 0.1.0 sont conservés.');t+='''

## Conversation et bilan

- Conversation : http://127.0.0.1:8766/ ; lien Input dans Logic Lab.
- Bilan en direct : http://127.0.0.1:8766/bilan ; mesures GPU, données importées, exemples vus, courbes et comparaisons avant/après.
- `python serve.py --port 8766` sert les pages et les API. `POST /api/chat` reçoit `messages` : liste alternée user/assistant terminant par une demande. `POST /analyse` conserve le premier classifieur.

Le dialogue utilise **Qwen3-0.6B**, révision figée dans `sources.json`, exécuté localement. Il ne s’agit pas du petit modèle initialisé au hasard de la première expérience. Le modèle produit `texte` et `valeurs`. Le décodage suit un schéma JSON, puis la réponse est validée et sérialisée. Une génération incomplète renvoie une erreur JSON contrôlée. Les valeurs chiffrées restent à évaluer séparément de la validité du format.

Le contexte récent est transmis à chaque demande : au plus 21 messages et 2 400 tokens de prompt. Les plus anciens échanges sont retirés par paires quand nécessaire. Le navigateur conserve la conversation localement ; une nouvelle conversation réinitialise l’historique. Ce n’est pas une mémoire illimitée.

## Corpus et adaptation française

`python prepare_large.py` importe les 17 fichiers de Wikipédia français (édition 20231101) et OpenAssistant2, en Parquet. Les révisions et licences sont figées dans `sources.json` ; `corpus/manifest.json` conserve les fichiers, volumes et nombres d’articles. L’import complet contient 2 564 646 articles français. Les données sont disponibles ; cela ne signifie pas qu’elles ont toutes servi à l’apprentissage.

`python build_chat_data.py` prépare les dialogues français, définitions et exercices de contexte/JSON, séparés par conversation et situation. `python train_language.py` lance un cycle borné de 400 étapes, mêlant un lot de textes encyclopédiques et les réponses supervisées. L’adaptation apprend uniquement des matrices LoRA ; les poids de base sont préservés. Les lots dépassant 512 tokens sont comptés comme ignorés. Les exemples et tokens réellement vus sont publiés dans le bilan.

La cadence vise environ 80 % de charge GPU moyenne ; ce n’est pas un plafond matériel exact. La charge et la mémoire sont mesurées séparément. Pendant l’apprentissage, la conversation utilise le CPU pour laisser la mémoire graphique au cycle. La validation mesure la perte de prédiction et les valeurs structurées ; un candidat n’est activé que si ces critères ne régressent pas. Les tests finaux restent distincts de la sélection. Les adaptations conservées sont dans `models/chat/` et le pointeur actif dans `models/chat/active.json`.

Sources : [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), [Wikipédia](https://huggingface.co/datasets/wikimedia/wikipedia), [OpenAssistant2](https://huggingface.co/datasets/OpenAssistant/oasst2), [contrainte JSON](https://github.com/noamgat/lm-format-enforcer). Les corpus gardent leurs licences et provenances propres. Le modèle reste expérimental ; une réponse grammaticale ou un JSON valide ne prouve pas sa vérité.
''';p.write_text(t,encoding='utf-8')
print('Context, JSON contracts, dataset separation tests and documentation installed')

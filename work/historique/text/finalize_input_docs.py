from pathlib import Path
R=Path(r'C:\Users\gabor\code\text-comprehension');O=Path(r'C:\Users\gabor\code\logic-lab\outputs')
p=R/'OUTPUT.md';t=p.read_text(encoding='utf-8');t=t.replace('# Priorité : sortie JSON stricte','# Sortie JSON stricte — versions 0.1 et 0.2');t=t.replace('Cette garantie appartient au programme complet : **le classifieur actuel prédit trois scores ; il ne rédige pas encore librement du JSON**.','Dans la première expérience 0.1.0, cette garantie appartient au programme complet : le classifieur prédit trois scores ; il ne rédige pas librement du JSON.');t+='''

## Conversation 0.2.0

La page Logic Lab Input utilise désormais un modèle génératif local (Qwen3-0.6B). `POST /api/chat` reçoit une liste `messages` user/assistant avec le contexte récent. Le modèle génère réellement un objet `{"texte":"…","valeurs":{}}`. Les valeurs peuvent être des chaînes françaises, nombres, booléens ou null, avec des clés normalisées et contrôlées.

Le décodage est contraint par JSON Schema et chaque résultat est ensuite validé. Si la génération s’interrompt avant de terminer l’objet, le service renvoie une erreur JSON contrôlée. La phrase précédente concernant le classifieur s’applique toujours à `/analyse`, conservé pour comparer les approches initiales.

Le bilan `/bilan` publie séparément la proportion de réponses complètes et la justesse des valeurs. Une réponse complète ne prouve pas la compréhension du contenu.
''';p.write_text(t,encoding='utf-8')
p=R/'LEXICON.md';t=p.read_text(encoding='utf-8')+'\nLe cycle génératif 0.2.0 utilise maintenant les définitions de la partition d’apprentissage parmi ses exemples supervisés. La comparaison 0.1.0 reste inchangée.\n';p.write_text(t,encoding='utf-8')
p=R/'README.md';t=p.read_text(encoding='utf-8')+'''

Pour reconstruire l’ensemble du prototype 0.2.0 après installation : `python prepare_large.py --model`, `python prepare_large.py`, `python build_chat_data.py`, puis `python -m unittest discover -s tests`. Les corpus volumineux restent hors Git ; les manifestes sont régénérés avec les chemins de la machine. L’ancien banc d’essai est produit séparément par `build_benchmark.py` et le lexique par `import_dictionary.py`.
''';p.write_text(t,encoding='utf-8')
p=R/'serve.py';t=p.read_text(encoding='utf-8').replace('Local JSON API for the trained French classifier. No remote inference.','Local Input pages, contextual JSON dialogue and legacy classifier. No remote inference.');p.write_text(t,encoding='utf-8')
(O/'LOGIC-LAB-INPUT-0.2.0.md').write_text('''# Logic Lab Input 0.2.0

Conversation : http://127.0.0.1:8766/ ; bilan : http://127.0.0.1:8766/bilan. Un lien Input est disponible dans Logic Lab. Le projet texte reste distinct de Garry.

La page permet de dialoguer en français avec l’historique récent, de consulter le JSON validé, de conserver la conversation dans le navigateur et de recommencer sans contexte. Elle utilise Qwen3-0.6B localement ; le modèle de zéro et CamemBERT de la première comparaison sont conservés.

Le corpus complet importé contient 2 564 646 articles français, OpenAssistant2 et leurs métadonnées, soit 4,68 Go de fichiers. Le lexique comporte 161 mots et 2 261 sens. Un premier cycle de 400 étapes utilise un lot de 5 100 articles préparés et 3 019 exemples supervisés compatibles avec sa fenêtre. Le bilan distingue les textes disponibles des exemples et tokens réellement traités. Une cible de charge GPU moyenne de 80 % est appliquée ; les mesures instantanées varient. La mémoire graphique est affichée séparément.

L’adaptation n’est activée qu’après sélection sur validation et contrôle des valeurs structurées. Les tests finaux sont ouverts après sélection. Les poids de base restent conservés. La perte de validation, la complétude JSON et l’exactitude des valeurs constituent des mesures différentes.

Vérifications : 12 tests Python réussis, dont séparation des situations/conversations, types JSON, rejets des sorties incorrectes et contexte. Parcours réel depuis Logic Lab, conversation en deux tours avec prénom retrouvé, conservation/réinitialisation de l’historique, bilan et affichage mobile vérifiés sans erreur JavaScript ni débordement. Captures et résultats dans ce dossier outputs.

Les scores du cycle en cours se trouvent dans le bilan local. La qualité des réponses reste expérimentale : le contexte est borné et les valeurs demandées peuvent être erronées malgré un JSON valide.
''',encoding='utf-8')

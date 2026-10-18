# Logic Lab Input 0.2.0

Conversation : http://127.0.0.1:8766/ ; bilan : http://127.0.0.1:8766/bilan. Un lien Input est disponible dans Logic Lab. Le projet texte reste distinct de Garry.

La page permet de dialoguer en français avec l’historique récent, de consulter le JSON validé, de conserver la conversation dans le navigateur et de recommencer sans contexte. Elle utilise Qwen3-0.6B localement ; le modèle de zéro et CamemBERT de la première comparaison sont conservés.

Le corpus complet importé contient 2 564 646 articles français, OpenAssistant2 et leurs métadonnées, soit 4,68 Go de fichiers. Le lexique comporte 161 mots et 2 261 sens. Un premier cycle de 400 étapes utilise un lot de 5 100 articles préparés et 3 019 exemples supervisés compatibles avec sa fenêtre. Le bilan distingue les textes disponibles des exemples et tokens réellement traités. Une cible de charge GPU moyenne de 80 % est appliquée ; les mesures instantanées varient. La mémoire graphique est affichée séparément.

L’adaptation n’est activée qu’après sélection sur validation et contrôle des valeurs structurées. Les tests finaux sont ouverts après sélection. Les poids de base restent conservés. La perte de validation, la complétude JSON et l’exactitude des valeurs constituent des mesures différentes.

Vérifications : 12 tests Python réussis, dont séparation des situations/conversations, types JSON, rejets des sorties incorrectes et contexte. Parcours réel depuis Logic Lab, conversation en deux tours avec prénom retrouvé, conservation/réinitialisation de l’historique, bilan et affichage mobile vérifiés sans erreur JavaScript ni débordement. Captures et résultats dans ce dossier outputs.

Les scores du cycle en cours se trouvent dans le bilan local. La qualité des réponses reste expérimentale : le contexte est borné et les valeurs demandées peuvent être erronées malgré un JSON valide.

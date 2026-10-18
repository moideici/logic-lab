# Input — programme ciblé et direction passerelle

Session locale `focus-20261017-210925` : **17 octobre 2026, 23 h 09 min 25 s → environ 23 h 39 min 25 s**, heure de Paris. Processus Python de calcul : 19244. La mesure initiale, l’apprentissage, la sélection et les contrôles finaux sont inclus dans ce budget.

Le programme travaille les nombres et les champs JSON, puis renforce le contexte, avec rappel de dialogues français et un lot de Wikipédia. Il utilise des exemples supervisés, une pondération renforcée des valeurs et de la fin de réponse, et une adaptation LoRA des poids existants. Les performances ne déterminent pas les numéros de version.

Le corpus ciblé comprend 4 424 exemples d’apprentissage, 104 de validation et 104 de test ; les situations historiques et les nouvelles partitions sont séparées. Le manifeste et les données sont figés. Les tests finaux ne choisissent pas le candidat. Les quantités réellement vues figurent dans le bilan, séparément des millions d’articles disponibles.

La référence sur les 28 épreuves de validation retenues donne **28/28 JSON complets et 7/28 ensembles de valeurs exacts**. Ce diagnostic limité montre le travail restant sur le sens, même quand la syntaxe est correcte. Un candidat doit conserver la complétude et ne pas régresser dans chaque catégorie, avec contrôle de la perte sur les acquis, avant activation.

Le dialogue reste sur GPU pendant l’apprentissage. Les premières mesures après correction se situent autour de **11–12 tokens/s en génération simultanée**, avec chargement séparé ; les 30–40 tokens/s ne sont pas atteints dans cette configuration. Des réponses génériques, des valeurs inventées et une réponse interrompue subsistent sur les essais conversationnels de la base. Le contrôle JSON renvoie alors une erreur structurée ; la nouvelle adaptation n’est pas encore validée.

La direction du projet devient la passerelle français → requête structurée → modèle de raisonnement → résultat → français. Le contrat provisoire `input.bridge/0.1` est dans `BRIDGE.md` et `bridge.py` du dépôt. Il valide le transport et copie les valeurs du résultat dans la sortie française. **Aucun second modèle n’est connecté et l’apprentissage de cette traduction n’est pas encore mesuré.** Le programme déjà lancé n’a pas été modifié pour y introduire ce nouveau contrat.

19 tests locaux passent, dont la conservation des valeurs et des types, les identifiants de requête, les clarifications et l’arrêt du décodage sur un objet complet. Ces tests portent sur le code et le protocole ; ils ne sont pas un score de compréhension du modèle.

[Conversation](http://127.0.0.1:8766/) · [Bilan en direct](http://127.0.0.1:8766/bilan)

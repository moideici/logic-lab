# Première comparaison du français — 0.1.0

Trois entraînements par approche. Exactitude moyenne sur quatre tests réservés de 600 exemples chacun ; toutes les sélections ont utilisé la validation. Les textes sont synthétiques et reposent sur les conventions du protocole.

| Épreuve | De zéro | CamemBERT adapté | Témoin sans texte |
|---|---:|---:|---:|
| Situations nouvelles, même forme | 41.3% | 100.0% | 35.3% |
| Reformulations inédites | 32.9% | 89.1% | 34.8% |
| Prénoms inédits | 33.7% | 100.0% | 34.7% |
| Chaînes spatiales plus longues | 34.1% | 80.1% | 34.5% |

Le petit modèle de zéro reste proche du hasard sur les reformulations, nouveaux noms et compositions. Il ne maîtrise pas encore ces tâches. CamemBERT adapté réussit les situations simples de ce générateur, mais perd des points sur les reformulations et les chaînes plus longues. Ces scores ne mesurent pas la compréhension générale du français. Le témoin sans texte montre aussi les indices exploitables dans les affirmations.

| Approche | Paramètres | Apprentissage total (3 graines) |
|---|---:|---:|
| Transformer en octets de zéro | 298,467 | 64.7 s |
| CamemBERT adapté | 110,624,259 | 240.8 s |

Appareil : NVIDIA GeForce RTX 4060. Leurs tailles et préentraînements sont différents : la comparaison porte sur deux voies pratiques, pas sur l’effet causal isolé du préentraînement.

## Sortie prioritaire : JSON valide

Le service local `http://127.0.0.1:8766/analyse` accepte texte et affirmation en français et renvoie des clés courtes, des scores numériques et une phrase française dans un JSON strict. Sérialisation et validation sont assurées par le programme ; le modèle actuel classe les affirmations et ne génère pas encore de réponses libres ni d’extractions numériques arbitraires. Les scores ne sont pas calibrés.

## Dictionnaire pour le prochain cycle

Import : 161 mots, 2261 sens du Wiktionnaire français via Kaikki, sans échec de téléchargement. Sources, licences et partitions par mot sont conservées. Ce corpus n’a pas été injecté dans la comparaison initiale. Les citations d’exemples attribuées à des sources externes sont écartées.

Prochaine étape : construire l’apprentissage lexical en contexte et des tâches de sortie structurée, avec des tests distincts pour la syntaxe JSON, les types et la justesse des valeurs. Un préentraînement sur des textes français diversifiés sera nécessaire pour apprendre davantage depuis zéro.

Sources : [CamemBERT](https://huggingface.co/almanach/camembert-base), [Wiktionnaire français via Kaikki](https://kaikki.org/frwiktionary/Fran%C3%A7ais/index.html), [protocole local](../PROTOCOL.md).

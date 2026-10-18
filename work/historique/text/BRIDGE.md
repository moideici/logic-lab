# Input : passerelle français ↔ modèle de raisonnement

Objectif : l’utilisateur parle français ; Input transmet une représentation
explicite au modèle de raisonnement puis reformule sa réponse en français.
Le modèle destinataire et son interface ne sont pas encore définis.

Le contrat provisoire `input.bridge/0.1` utilise du JSON, des clés simples,
des codes de tâche et des nombres typés. `goal` et `answer` sont prévus en
anglais pour le premier adaptateur textuel. Si le destinataire attend un
autre format, un adaptateur devra traduire ce contrat vers son interface.
Des vecteurs internes ne sont pas présumés compatibles entre modèles.

## Exemple de requête

Demande française : « Trois cahiers à 2,50 € chacun : quel est le total ? »

```json
{"protocol":"input.bridge/0.1","id":"request_001","type":"request","status":"ready","task":"calculate","goal":"Compute total price from quantity and unit_price.","data":{"quantity":3,"unit_price":2.5,"unit":"eur"},"constraints":[{"key":"unit","op":"eq","value":"eur"}],"context":{},"missing":[]}
```

Réponse attendue du modèle de raisonnement :

```json
{"protocol":"input.bridge/0.1","id":"request_001","type":"result","status":"ok","answer":"The total is 7.5 EUR.","values":{"total":7.5,"unit":"eur"},"missing":[]}
```

Affichage français :

```json
{"texte":"Le total est de 7,50 €.","valeurs":{"total":7.5,"unit":"eur"}}
```

## Règles du contrat

- Tâches initiales : `answer`, `calculate`, `summarize`, `compare`, `plan`.
- Une information inconnue reste `null` et figure dans `missing` quand elle
  empêche la tâche. `status: clarify` empêche l’envoi au modèle destinataire.
- Les contraintes sont explicites : clé, opérateur `eq/lte/gte/in`, valeur.
- `context` contient les faits pertinents pour la demande courante. Un futur
  gestionnaire de contexte devra conserver les corrections et leur provenance.
- Un résultat doit porter le même identifiant que la demande. Les champs,
  versions et nombres non finis invalides sont refusés, sans réparation cachée.
- Les valeurs du résultat sont copiées dans la sortie française, sans être
  régénérées. Cela protège les valeurs structurées ; la fidélité du texte
  reformulé doit être évaluée séparément.
- Ce contrat ne déclenche aucune action et ne définit aucune connexion réseau.

## État réel et prochaines épreuves

`bridge.py` valide le transport et prépare la sortie française. Les tests
vérifient les types, les identifiants, les clarifications et la conservation
des valeurs. Ils **ne prouvent pas** que le modèle sait déjà traduire toute
demande française vers ce protocole. Aucun second modèle n’est connecté.

Le cycle de 30 minutes déjà lancé conserve son programme figé : nombres,
JSON complet, contexte et conservation du français. Il n’a pas reçu ce
nouveau protocole en cours de route.

Le prochain jeu d’apprentissage devra associer demande française, contexte,
requête canonique, résultat externe et réponse française. Épreuves réservées :
reformulations inconnues, négations, changements d’avis, unités, nombres
décimaux, ambiguïtés et informations manquantes. Mesures : tâche correcte,
arguments et contraintes exacts, demande de clarification justifiée, absence
d’invention et conservation des résultats dans le retour français. Le JSON
valide seul ne suffit pas.

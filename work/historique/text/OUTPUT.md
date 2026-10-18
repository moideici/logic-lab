# Priorité : sortie JSON stricte

L’interface renvoie un document JSON unique : aucun texte hors du JSON, aucune balise Markdown. Les clés sont courtes, en minuscules, sans accents, avec `_` comme séparateur. Les valeurs texte conservent leur français et leurs accents. Les nombres sont de vrais nombres JSON : `12`, `98.5`, et non `"12"`. Les décimales utilisent un point. Booléens, `null`, tableaux et objets sont pris en charge.

`json_output.py` sérialise les valeurs typées avec `allow_nan=False`, refuse les clés qui entrent en collision après simplification et vérifie le contrat de réponse. Le parseur refuse également les clés dupliquées, NaN, Infinity et les nombres débordant vers l’infini. Une valeur invalide provoque une erreur contrôlée, jamais une sortie partielle présentée comme valide.

Cette garantie appartient au programme complet : **le classifieur actuel prédit trois scores ; il ne rédige pas encore librement du JSON**. Le texte de réponse est un modèle de phrase français lié à la classe prédite. Le prochain modèle génératif devra produire une structure conforme à un schéma, avec décodage contraint et validation finale. Le taux de validité et l’exactitude des valeurs devront rester deux mesures distinctes.

Lancer `python serve.py --port 8766`, puis envoyer à `http://127.0.0.1:8766/analyse` :

```json
{"texte":"Lina donne le livre à Malo.","affirmation":"Malo reçoit le livre.","modele":"pretrained"}
```

Réponse : champs `etat`, `type` (confirme, contredit ou indetermine), `texte` français, `score` numérique, `scores` des trois classes, `modele`. Les scores ne sont pas calibrés et ne constituent pas une garantie de vérité. Le modèle de démonstration est choisi sur la validation, jamais sur les tests.

Exemple de structure générale supportée par le sérialiseur :

```json
{"nom":"Lina","age":12,"score":98.5,"texte":"Elle a terminé l’exercice."}
```

Ce dernier objet illustre les types supportés ; l’extraction libre d’âge ou de score à partir de n’importe quel texte reste à entraîner et évaluer.

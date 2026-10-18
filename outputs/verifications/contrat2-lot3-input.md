# Contrat de réponse v2 sur Input 0.2.0 : mesure sur le banc dev (18 octobre 2026)

Même modèle (Qwen3-0.6B + adaptation `focus-20261017-210925/checkpoint-1000`, jamais entraîné sur `etat`, `decision` ni `justification`), même banc v1.0.0 (séparation dev, 51 cas, 3 essais), servi avec `INPUT_CONTRACT=2`. Comparé à la baseline en contrat 1.

| Mesure (dev) | Contrat 1 | Contrat 2 |
|---|---|---|
| Réussite globale | 54,2 % (83/153) | 61,4 % (94/153) |
| Erreurs d'API (génération non terminée ou refusée) | 0 | **17** |
| Latence médiane | 4,5 s | **26 s** |
| Abstention sur questions répondables (à garder bas) | 6 % | 26,5 % |
| Réponse affirmée sur questions non répondables (invention) | 83 % | 56 % |

| Catégorie | Contrat 1 | Contrat 2 |
|---|---|---|
| contexte : prénom | 100 % | 100 % |
| contexte : préférence | 17 % | 75 % |
| contexte : correction | 75 % | 50 % |
| calcul | 88 % | 67 % |
| planning | 28 % | 61 % |
| comparaison | 33 % | 25 % |
| selon un texte donné | 67 % | 89 % |
| information absente du texte | 22 % | 67 % |
| fait non vérifiable | 22 % | 50 % |
| fonctionnement du modèle | 50 % | 58 % |
| demande vague : demander une précision | 67 % | 11 % |

## Lecture prudente

- **Le contrat 2 améliore la prudence sans entraînement** : les états `limite` et `clarification` incitent le modèle à reconnaître ce qu'il ne sait pas (abstention utile 22 % → 67 % pour l'information absente, 22 % → 50 % pour les faits non vérifiables). Prix : il s'abstient aussi sur 26 % des questions répondables, et le calcul baisse de 88 % à 67 %.
- **Il est trop lent et trop fragile en l'état** : 26 s en médiane et 17 erreurs. Une partie vient de la mesure (la carte GPU était partagée avec un entraînement, un autre serveur et d'autres mesures) ; la génération de cinq champs sur un budget de 560 tokens est de toute façon plus longue. À remesurer sur une carte libre avant de conclure sur la vitesse.
- **Biais de mesure à connaître** : les vérificateurs lisent maintenant aussi `decision` et `justification`. Une réponse plus longue a plus de chances de contenir le bon nombre ou un mot attendu, sans que sa décision soit juste : le gain en planning est en partie artificiel. Exemple observé hors banc : décision « 401 », texte « 391 ». Il faut un contrôle de cohérence entre champs avant de créditer le contrat 2.
- **Les erreurs comptent comme des échecs** : sans les 17 erreurs, la réussite serait plus haute ; elles sont rapportées à part.
- 51 cas, 3 essais corrélés : un écart de moins de 5 points globaux n'est pas une preuve, et les catégories ont 3 à 8 cas.

## Conclusion

Le contrat v2 n'est pas activé en production : le gain de prudence est réel mais s'accompagne de lenteur, d'erreurs et d'un biais de mesure. La décision d'activation attend une adaptation entraînée pour ce format (lot 4) et un contrôle de cohérence dans le banc. Résultats bruts : `projets/input/bench/results/contrat2-dev-0.2.0.json`.

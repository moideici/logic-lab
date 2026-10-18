# Input : décisions, justifications et sorties structurées

Bilan du 17 octobre 2026. Ce document définit le travail à faire ; il ne décrit pas des fonctions déjà toutes disponibles. Le projet d’agent producteur de code est écarté.

## Objectif produit

À partir d’un message français et de son contexte, Input identifie le besoin, recueille les informations manquantes, choisit une démarche, sollicite le raisonnement nécessaire et expose une décision justifiée. Trois usages sont retenus : résoudre un problème à contraintes, construire un plan, comparer des scénarios.

La réponse utilisateur reste un objet JSON unique. Le Markdown est permis uniquement dans les champs rédactionnels définis par le contrat. Aucune explication ne doit être ajoutée à l’extérieur du JSON.

## État vérifié

Input 0.2.0 utilise Qwen3-0.6B avec l’adaptation locale `focus-20261017-210925/checkpoint-1000`. Le cycle de trente minutes a traité 4 896 exemples et 272 971 tokens supervisés. Ces exemples peuvent inclure des répétitions ; ils ne sont pas tous des documents uniques.

Sur la validation de sélection : 7/28 ensembles de valeurs exacts avant adaptation, 25/28 après, avec 28/28 réponses JSON complètes des deux côtés. Sur les tests réservés : 36/36 JSON complets et 29/36 ensembles de valeurs exacts, dont contexte 12/12, structure 12/12, calculs 5/12. Ces petits tests ne mesurent ni les décisions générales ni la qualité des justifications.

Le service contrôle déjà la syntaxe JSON et les types. Une génération interrompue produit une erreur JSON contrôlée et ne compte pas comme une réponse réussie. Le format conversationnel actuel contient seulement `texte` et `valeurs`. Le contrat Markdown par champ et son rendu ne sont pas encore installés.

Le fork HRM symbolique reste une expérience sur le sudoku. Les adaptateurs continus sont des prototypes non entraînés. HRM n’est pas choisi comme cœur définitif des trois usages et aucune communication latente depuis Input n’est activée.

## Signification des objectifs à 100 %

- **JSON** : toute réponse publiée doit respecter le schéma, les types et la sérialisation stricte. Mesurer séparément les réponses complètes, les erreurs et les refus ; une erreur structurée ne vaut pas une décision correcte.
- **Markdown** : définir un profil précis, un analyseur et un rendu contrôlé. La conformité au profil peut être imposée. La beauté ou la clarté d’une présentation demande une autre évaluation.
- **Décision et justification** : viser tous les critères sur un ensemble d’épreuves défini. La justesse de toute réponse à tout message libre ne peut pas être garantie universellement. Pour les cas vérifiables, utiliser des contrôles exacts. Pour les situations ambiguës, demander une précision peut être la bonne décision.

Une bonne explication décrit les faits pertinents, les contraintes et les raisons qui soutiennent le choix. Sa fluidité ne prouve pas sa vérité. Elle doit correspondre à la décision et aux résultats vérifiés, sans inventer de faits, de calculs ou de contrôles réussis. Elle n’a pas à exposer une trace exhaustive du calcul interne.

## Contrat de sortie proposé, à implémenter

Champs simples :

| Champ | Fonction | Markdown interprété |
|---|---|---|
| `etat` | `solution`, `clarification` ou `impossible` | Non |
| `decision` | Choix formulé simplement | Non |
| `texte` | Réponse courte lisible | Oui |
| `justification` | Raisons, contraintes et limites du choix | Oui |
| `valeurs` | Nombres, booléens, valeurs nulles et chaînes brutes | Non |

`impossible` doit être justifié par une contradiction vérifiée ou une impossibilité démontrée. L’échec d’un modèle ou d’une recherche ne suffit pas ; prévoir un état d’erreur contrôlée distinct au niveau du service.

Le profil Markdown initial pourra couvrir les paragraphes, listes, emphases, titres et code en ligne. Le rendu doit utiliser une liste de nœuds autorisés, sans HTML actif ni liens exécutables. Les champs de données s’affichent comme du texte brut, même si une valeur contient des caractères de Markdown. Les guillemets et retours à la ligne sont échappés par la sérialisation JSON. Les nombres ne deviennent pas des chaînes décorées.

## Ordre d’exécution proposé

1. **Définir les épreuves et critères.** Préparer d’abord 300 cas de référence, 100 par usage, avec des contraintes et critères de réussite vérifiables. Réserver des situations et formulations inédites pour les tests. Évaluer les réponses acceptables plutôt qu’une phrase unique. Publier exactitude, taux de clarification justifiée, erreurs et couverture des demandes.
2. **Implémenter le contrat et l’affichage.** Ajouter les champs de décision et justification, le décodage contraint, la validation et le Markdown limité aux champs prévus. Préserver la compatibilité des anciennes conversations et tester les chaînes avec accents, guillemets, retours à la ligne, listes et nombres.
3. **Renforcer la compréhension du contexte.** Représenter objectif, faits, contraintes, préférences et inconnues avec leur provenance dans les messages. Traiter négations, corrections, changements d’avis et contradictions. Décider quand demander une précision.
4. **Construire le raisonnement vérifiable.** Pour les contraintes : vérifier la faisabilité et les règles. Pour les plans : vérifier les prérequis, dépendances, ressources et délais. Pour les scénarios : conserver les hypothèses communes, recalculer ce qui change et signaler les inconnues. Les résultats transmis à Input doivent inclure les vérifications réellement effectuées.
5. **Entraîner conjointement décision et explication.** Utiliser des exemples français contextualisés avec plusieurs décisions possibles, de bonnes raisons, de fausses justifications plausibles et des cas incomplets. Corriger en priorité les calculs et la cohérence entre texte et valeurs. Conserver du français naturel. Les corpus encyclopédiques complètent cette supervision ; ils ne la remplacent pas.
6. **Évaluer le cœur et le canal latent.** Choisir le modèle d’après les trois usages. Figer les poids et entraîner les adaptateurs sur des paires appropriées. Comparer canal latent, canal symbolique/textuel, canal coupé et messages permutés, avec qualité, mémoire et temps mesurés. Le canal latent doit montrer qu’il transporte l’information utile ; la taille correcte des tenseurs ne le prouve pas.
7. **Activer avec un bilan lisible.** Ajouter au suivi les erreurs par usage, l’exactitude des décisions et calculs, la conformité Markdown, la qualité des raisons et les temps de réponse. Choisir sur la validation, ouvrir les tests après sélection, et conserver la version précédente en cas de régression.

## Premier jalon

Un utilisateur formule un problème court dans chacun des trois usages. Input obtient les informations nécessaires, fournit une décision accompagnée d’une justification fondée, conserve les nombres exacts et affiche les champs rédactionnels en Markdown dans un JSON valide. Les vérifications et limites réelles sont accessibles dans le bilan.

Ce jalon doit précéder la généralisation à des tâches longues, à une mémoire étendue et à des domaines ouverts. Le choix du cœur final et le calendrier détaillé restent à établir à partir des premières épreuves.

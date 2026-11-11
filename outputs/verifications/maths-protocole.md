# Maths : protocole de la vague 1, fixé avant les résultats (31 octobre 2026)

Question : un petit Transformer (moins d'un million de paramètres) entraîné de zéro apprend-il à calculer, du `a+b` jusqu'aux équations à une inconnue, en passant par la priorité des opérations et les parenthèses ? Et jusqu'où généralise-t-il au-delà de ce qu'il a vu ?

## Tâche : l'étape suivante d'un calcul
Le réseau ne donne pas la réponse d'un coup. Il reçoit un état (`2+3*4`, `(2+3)*4`, `3x+5=20`) et écrit l'état suivant, **une seule opération réduite à la fois** : `2+3*4` → `2+12` → `14`. On le rappelle en boucle jusqu'à un état terminal (un nombre, ou `x=nombre`). Raisons : la priorité opératoire devient un comportement mesurable, chaque étape est vérifiable exactement, et la multiplication de deux grands nombres en une seule sortie n'est pas demandée au réseau.

Règle de réécriture de référence (le réseau doit l'apprendre, il ne la reçoit pas) :
1. Parenthèses : on traite le premier groupe sans parenthèse intérieure ; un groupe réduit à un seul nombre perd ses parenthèses.
2. Dans le groupe (ou l'expression) : première opération `*` ou `/` en lisant de gauche à droite, sinon première `+` ou `-`.
3. Un nombre négatif placé après un opérateur s'écrit `(-3)`. Au début d'une expression ou après `(`, `-3`.
4. Divisions exactes seulement (résultat entier). Tous les nombres intermédiaires restent entiers.
5. Équations (`ax+b=c`, `ax-b=c`, `b+ax=c`, `ax=c`, `x+b=c`, `x-b=c`) : si le membre de droite n'est pas un nombre, on réduit une opération ; sinon on déplace la constante (`3x+5=20` → `3x=20-5`) ; sinon on divise par le coefficient (`3x=15` → `x=15/3`) ; terminal : `x=5`. Solution entière, éventuellement négative.

## Niveaux
| Niveau | Contenu | Entraînement | Hors distribution (OOD) |
|---|---|---|---|
| N1 | `a+b`, `a-b` | opérandes 0 à 99 | opérandes 1000 à 9999 |
| N2 | `a*b` | un facteur 0 à 99, l'autre 0 à 12 | grand facteur 1000 à 9999 |
| N3 | `a/b` exacte | diviseur 1 à 12, quotient 0 à 99 | quotient 1000 à 9999 |
| N4 | priorité sans parenthèses | 3 à 4 nombres de 0 à 20, 2 à 3 opérations | 5 à 7 nombres, 0 à 50 |
| N5 | parenthèses | 3 à 5 nombres de 0 à 20, 1 à 2 groupes | 6 à 8 nombres, 0 à 50 |
| N6 | équations à une inconnue | a 1 à 12, solution -20 à 20, constante 1 à 50 | a 13 à 30, solution -99 à 99, constante 51 à 99 |

Précisions de réalisation (fixées avant tout entraînement) :
- N4 et N5 : tous les nombres qui apparaissent dans la chaîne restent au plus 999 à l'entraînement, 9999 en OOD. N1 à N3 ne sont pas bornés par 999 (produits jusqu'à 1188, dividendes jusqu'à 1188).
- Dans N4 et N5, une division sur deux a un dividende multiple du diviseur, jusqu'à 99 (500 en OOD), sinon elle serait presque toujours rejetée ; les autres divisions sont tirées au hasard et rejetées si elles ne tombent pas juste. Opérateurs tirés à 30 % `+`, 30 % `-`, 25 % `*`, 15 % `/`.
- Les nombres sont tirés en choisissant d'abord leur nombre de chiffres, pour que les petits ne soient pas noyés.
- Le hors distribution dépasse strictement les bornes (plus de chiffres, expressions plus longues) : il mesure l'extrapolation, pas la mémoire. Les nombres à 4 chiffres existent à l'entraînement seulement comme produits ou dividendes de N2 et N3 (au plus 1188).
- Les séquences font au plus 60 caractères à l'entraînement ; les positions apprises vont jusqu'à 128.

## Séparation des données
Chaque état d'entrée est assigné à l'apprentissage (90 %), à la validation (5 %) ou au test (5 %) par un hachage stable (BLAKE2b) de sa chaîne. Aucun état de validation ou de test n'apparaît à l'entraînement. Pour les évaluations de problèmes entiers, le **départ** est tiré dans le test ; les états intermédiaires peuvent, eux, avoir été vus : on le dit dans les résultats. Le test sert une seule fois, à la fin ; les points de contrôle sont choisis sur la validation.

## Modèle et entraînement
Transformer décodeur, caractère par caractère, `état>étape$`, perte sur la sortie seulement. d=128, 4 couches, 4 têtes, moins d'un million de paramètres. AdamW, taux cosinus, bf16. Graine fixée. Deux régimes à même budget de pas :
- **Curriculum** : N1 seul, puis N1-N2, N1-N3, ... jusqu'à N6, avec 25 % de rejeu des niveaux précédents.
- **Mélange plat** : tous les niveaux dès le début.
Un seul modèle pour les six niveaux (pas un spécialiste par niveau).

## Mesures (par niveau, test et OOD)
1. **Étape exacte** : la sortie en décodage glouton égale l'étape de référence.
2. **Étape valide** : la sortie est bien formée et conserve la valeur (ou la solution) selon un évaluateur indépendant de la règle de référence.
3. **Problème résolu** : en rappelant le réseau jusqu'à un état terminal (au plus 12 étapes pour les expressions, 8 pour les équations), toutes les étapes sont valides et le résultat final est exact.
4. Nombre moyen d'étapes ; premier niveau où la précision chute.

## Critères annoncés avant
- Un niveau est dit **appris** si la précision d'étape exacte sur le test est d'au moins 0,99 et le problème résolu d'au moins 0,95.
- Toute différence inférieure à 0,02 sur 1 000 exemples est considérée comme du bruit.
- Curriculum et mélange plat ne sont déclarés différents que si l'écart dépasse 0,05 sur le problème résolu moyen des niveaux N4 à N6, avec au moins deux graines.
- Règle d'arrêt du plan : un régime sans gain mesuré sur la validation après deux essais est abandonné et documenté.

## Hors périmètre de cette vague
Problèmes en texte, fractions et nombres décimaux, plusieurs inconnues, équations avec `x` des deux côtés ou entre parenthèses, puissances et racines, réponse directe sans étapes (comparaison à prévoir ensuite pour mesurer ce que les étapes apportent).

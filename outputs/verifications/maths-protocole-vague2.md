# Maths, vague 2 : exposants, fractions, racines, équations (protocole figé le 31 octobre 2026)

**Figé le 31 octobre 2026**, après que la vague 1 a atteint le 1/1 sur ses plages (`maths-vague1-fin.md`) et sur accord de l'utilisateur (« Oui, vague 2 ») avec les quatre choix par défaut ci-dessous. Toute modification ultérieure sera un amendement daté. Même tâche que la vague 1 : le réseau écrit l'état suivant, une opération à la fois ; même vérificateur indépendant ; même séparation par hachage ; même règle « le test sert une fois par candidat ». Un seul modèle pour tous les niveaux, N1 à N6 inclus (non-régression : ils doivent rester à leur score).

## Notation (choix retenus)
- **Puissance** `a^b`, exposant entier de 0 à 6. Priorité au-dessus de `*` et `/`, associativité à droite (`2^3^2` = `2^9`). Une base négative est toujours écrite `(-2)^3` ; la forme `-2^2` est interdite (ambiguë), ni générée ni acceptée comme sortie valide. Un groupe `(-2)` suivi de `^` n'est jamais défait.
- **Fractions** : les valeurs sont des rationnels. Un atome fraction s'écrit **toujours entre parenthèses**, irréductible, dénominateur au moins 2 : `(3/4)`, `(-1/2)`. Un `/` nu reste l'opérateur de division : `3/4` se réduit en `(3/4)`, `6/4` en `(3/2)`, `6/3` en `2` (comme en vague 1). `(1/2)+(1/3)` → `(5/6)`. Un résultat entier s'écrit sans fraction. Ordre des opérations de la vague 1 inchangé.
- **Racines** : `√n` (carrée) et `∛n` (cubique) d'un nombre ou d'un groupe : `√16`, `√(9+16)`. Résultats exacts seulement (carrés et cubes parfaits, y compris fractions parfaites `√((1/4))` → `(1/2)`). Le radical s'applique à l'atome qui le suit ; un `^` juste après un radical est évité par le générateur (écrit `(√16)^2`). Les racines irrationnelles (`√2`, `2√3`) sont hors de cette vague.
- **Équations** (une inconnue `x`, solution rationnelle) :
  - puissances : `x^2=c` (deux solutions écrites `x=7 ou x=-7`, ou `aucune solution` si c < 0), `ax^2+b=c`, `x^3=c` ;
  - fractions : `x/a+b=c`, `(p/q)x=c`, `(p/q)x+b=c` ;
  - racines : `√x=c`, `√(x+b)=c`, `a√x=c` ; `aucune solution` si c < 0 ; la solution est vérifiée par remplacement (pas de solution parasite acceptée).
  - États terminaux : `x=nombre`, `x=(p/q)`, `x=r ou x=s`, `aucune solution`.

## Niveaux
| Niveau | Contenu | Entraînement |
|---|---|---|
| N7 | puissances | base -12 à 12, exposant 0 à 6 (résultat au plus 9999), puis dans des expressions comme N4 |
| N8 | fractions | quatre opérations entre entiers et fractions de numérateur et dénominateur au plus 12 ; réduction ; puissances de fractions |
| N9 | racines | carrés parfaits jusqu'à 400, cubes parfaits jusqu'à 1000, dans des expressions |
| N10 | équations de puissances, de fractions et de racines | plages ci-dessus, solutions entières ou rationnelles simples |
Chaque niveau est aussi mélangé à des expressions de N4/N5 pour que les priorités entre `^`, radicaux, fractions et parenthèses soient apprises ensemble. Plages précises, tailles d'ensembles de test (au moins 1 000 états distincts, sauf si l'espace est plus petit, ce qui sera annoncé) et poids d'échantillonnage : à fixer au gel.

## Mesures et critères
Identiques à la vague 1 : étape exacte, étape valide (évaluateur indépendant en rationnels exacts), problème résolu, par niveau, sur test puis hors distribution. Objectif : 1,000 partout dans les plages avant d'augmenter la difficulté ; non-régression de N1 à N6 obligatoire.

## Points ouverts à trancher au gel
1. Syntaxe des fractions par atomes parenthésés (ci-dessus) contre une notation distincte de l'opérateur.
2. Interdiction de `-2^2` (choix de sûreté) contre convention mathématique `-(2^2)`.
3. Équations à deux solutions et `aucune solution` : états terminaux supplémentaires.
4. Racines irrationnelles et simplification de radicaux : vague 3.

## Précisions de réalisation (ajoutées au gel, avant tout entraînement de la vague 2)
- **Deux étapes** : 2a = N7 puissances, N8 fractions, N9 racines (expressions) ; 2b = N10 équations. Chaque étape a sa validation, son test unique et son rapport. N1 à N6 restent dans l'entraînement et leur test (mêmes états, mêmes graines que la vague 1) sert de non-régression : référence `recette-D` (problème résolu 1,000 partout ; étape exacte 0,999 en N1, 0,998 en N5, 1,000 ailleurs).
- **Règle de réécriture étendue** (la vague 1 est inchangée) : parenthèses d'abord ; dans une suite sans parenthèse, d'abord la première racine dont l'argument est un nombre, puis la première puissance dont l'exposant est un nombre non suivi d'un `^` (donc `2^3^2` → `2^9`), puis `*` et `/` de gauche à droite, puis `+` et `-`. `√16^2` se lit `(√16)^2`.
- **Fraction atome** : `(p/q)` avec p, q entiers, pgcd 1, q au moins 2, est un nombre (aucune opération). `(6/4)` est un groupe avec une division et se réduit en `(3/2)`. Le `/` nu sur entiers non divisibles donne l'atome (`3/4` → `(3/4)`). Division exacte inchangée (`6/3` → `2`). Dans N1 à N6 la division inexacte reste une erreur de génération (les distributions de la vague 1 ne changent pas).
- **Base négative d'une puissance** : toujours entre parenthèses, même en tête (`(-2)^3`). `-2^2` n'est pas canonique.
- **Racines** : `√` et `∛` suivis d'un nombre, d'un atome `(p/q)` ou d'un groupe. Racine d'un négatif : `∛(-27)` valide, `√` d'un négatif invalide. Racine non exacte : invalide (hors vague).
- **Plages d'entraînement** : N7, base -12 à 12, exposant 0 à 6 (0^0 exclu), exposants littéraux 0 à 4 dans les expressions, tous nombres au plus 9999 ; N8, numérateurs de -12 à 12, dénominateurs 2 à 12, tous entiers de la chaîne au plus 999 ; N9, carrés parfaits jusqu'à 400, cubes (positifs ou négatifs) jusqu'à 1000, carrés de fractions parfaites, arguments de racine écrits comme des groupes (`√(9+16)`), tous nombres au plus 999.
- **Hors distribution** : N7 base 13 à 30 et exposant 0 à 4 ; N8 numérateurs et dénominateurs de 13 à 30 ; N9 carrés jusqu'à 900 et cubes jusqu'à 3375.
- **Mêmes séparations par hachage** (90/5/5), mêmes mesures, même règle « le test sert une seule fois par candidat ». Vocabulaire étendu par ajout en queue (`^`, `√`, `∛`, espace et lettres de « ou » et « aucune solution ») ; le modèle de la vague 2 est affiné à partir de `recette-D` (lignes de vocabulaire ajoutées).

## Amendement 1 (31 octobre 2026) : opérations sur fractions en pas plus fins
**Pourquoi.** Premier candidat de la vague 2 (12 couches, `vague3-1`, validation seulement) : tout à 0,985 ou plus sauf N8 (fractions) à 0,930 (meilleur point, pas 52 500). Les erreurs de N8 sont presque toutes du même type, un chiffre faux dans le numérateur d'une addition ou soustraction de fractions écrite en un seul pas (`(31/7)+(4/9)` donné `(297/63)` au lieu de `(307/63)`). L'écart entre états d'entraînement (0,995) et de validation (0,903) montre que le réseau mémorise ce pas trop gros au lieu de calculer ; passer de 8 à 12 couches n'a rapporté que 3,5 points. Accord de l'utilisateur : « Oui, découper ».

**Ce qui change** (N8, N9 et N10 seulement ; N1 à N7 inchangés, mêmes états, mêmes chaînes). Une opération dont un opérande est une fraction non entière n'est plus calculée en un pas : elle est d'abord **réécrite** en un groupe `(numérateur/dénominateur)` d'opérations sur entiers, sans aucun calcul (on recopie), puis réduite par les pas ordinaires de la vague 1.

| Opération | Réécriture (a/b, c/d, entiers n) |
|---|---|
| `(a/b)+(c/d)`, `-` | `((a*d+c*b)/(b*d))` |
| `(a/b)+n`, `n+(c/d)` | `((a+n*b)/b)`, `((n*d+c)/d)` |
| `(a/b)*(c/d)` ; avec entier | `(a*c/(b*d))` ; `(a*n/b)`, `(n*c/d)` |
| `(a/b)/(c/d)` ; avec entier | `(a*d/(b*c))` ; `(a/(b*n))`, `(n*d/c)` ; le signe passe au numérateur |
| `(a/b)^n` | `(a^n/b^n)` |
| `√(a/b)`, `∛(a/b)` | `(√a/√b)`, `(∛a/∛b)` |
Le groupe extérieur est toujours présent : le gabarit se lit comme un seul opérande dans n'importe quel voisinage (`3/(1/2)^2` → `3/(1^2/2^2)`). Quand le gabarit remplit tout un groupe existant, une seule paire de parenthèses reste. Le groupe `(N/D)` devient l'atome fraction dès que N et D sont des entiers avec N/D irréductible et D au moins 2 : la division finale ne coûte alors aucun pas ; si N/D est réductible ou entier, c'est un pas de plus (`(-717/189)` → `(-239/63)`, `(4/4)` → `1`). Exemple : `(31/7)+(4/9)` → `((31*9+4*7)/(7*9))` → `((279+4*7)/(7*9))` → `((279+28)/(7*9))` → `(307/(7*9))` → `(307/63)`.

**Vérificateur.** Toujours indépendant de la règle de référence et toujours « même valeur, forme canonique, exactement un pas de moins », mais le coût d'une opération sur fraction est calculé par l'évaluateur à partir des valeurs des opérandes : 1 (réécriture) + opérations du gabarit (addition ou soustraction de deux fractions 4, d'une fraction et d'un entier 2, multiplication 2 ou 1, division 2 ou 1, puissance 2, racine 2) + 1 si le groupe n'est pas déjà un atome irréductible. Vérifié sur 2 500 problèmes par niveau (N7 à N10, dans la distribution et hors distribution) : plus de 75 000 pas de référence sont tous acceptés et la dernière valeur égale celle de l'évaluateur. Longueur d'état maximale 43 caractères (limite du modèle 128).

**Inchangé.** Niveaux, plages, séparations par hachage, mesures, critères, règle « le test sert une fois par candidat », non-régression de N1 à N6. Les équations (N10) gardent leurs pas propres ; seules leurs expressions de membre droit utilisent les gabarits (`x=4/(2/3)` → `x=(4*3/2)`). Conséquence sur les comparaisons : les chiffres de N8 à N10 d'avant cet amendement (`vague2a-*`, `vague3-1`) portent sur une autre tâche (pas plus gros) ; ils ne sont comparables ni en étape exacte ni en problème résolu. Les réservoirs d'entraînement de N8 à N10 sont régénérés (suffixe `fr2`).

## Amendement 2 (31 octobre 2026) : réduction d'une fraction facteur premier par facteur premier

**Pourquoi.** Après l'amendement 1, le modèle `vague4-1` (12 couches, point retenu au pas 22 500) atteint 0,993 en étape exacte sur la validation de N8 (0,930 avant). Analyse des erreurs sur 1 000 états de validation de N8 (jamais le test) : 12 erreurs, dont 7 sont des réductions par pgcd faites d'un coup (`(405/324)` → `(5/4)` demande de trouver le pgcd 81 et de diviser deux nombres à trois chiffres). Les autres niveaux n'ont que quelques erreurs de chiffres isolées (N1 3, N5 2, N6 2, N7 7, N9 3, N10 1 sur environ 1 000 états chacun). Le point retenu est celui de meilleure validation sur 16 mesures : son score (0,998) est optimiste ; sur un échantillon neuf de 1 000 états par niveau il donne environ 0,995.

**Règle.** Un groupe `(N/D)` d'entiers, D au moins 2, non entier et réductible (pgcd g > 1) se simplifie par UN facteur premier commun à la fois, le plus petit : `(405/324)` → `(135/108)` → `(45/36)` → `(15/12)` → `(5/4)`. Une division exacte (`(12/4)` → `3`, `(4/4)` → `1`, `(0/12)` → `0`), une division sans parenthèses (`48/36` → `(4/3)`) et un dénominateur négatif (`(10/(0-4))` → `(10/(-4))` → `(-5/2)`) ne changent pas. Coût dans le vérificateur : le nombre de facteurs premiers de g avec multiplicité (`(405/324)` coûte 4, `(135/108)` 3), au lieu de 1 ; le vérificateur accepte donc aussi un autre facteur premier, mais refuse de diviser par un composé (deux pas) ou d'aller jusqu'au bout.

**Contrôles avant entraînement.** 12 tests de `test_maths_fracsteps.py` (dont les chaînes ci-dessus) et les 94 tests maths passent. Balayage de 2 500 problèmes par niveau (N6 à N10, dans la distribution et hors distribution) : 93 178 pas de référence, tous canoniques et acceptés par le vérificateur, dernière valeur égale à celle de l'évaluateur ; état le plus long 43 caractères, chaîne la plus longue 23 états. Les réservoirs de N8 à N10 sont régénérés (suffixe `fr3`) ; les chiffres de N8 à N10 d'avant cet amendement ne sont pas comparables en étape exacte.

**Entraînement.** `vague5-1` : affinage de `vague4-1`, 12 couches, 40 000 pas, taux 2e-4, mêmes poids de niveaux que `vague4-1`, graine 11 (même budget, GPU plafonné à 0,85 Go, 4 threads).

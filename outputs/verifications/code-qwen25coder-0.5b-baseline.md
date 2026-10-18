# Cœur de code : baseline de Qwen2.5-Coder-0.5B (18 octobre 2026)

Modèle : `Qwen/Qwen2.5-Coder-0.5B` (base, Apache 2.0, révision 8123ea2, 0,49 G de paramètres). Banc de code `projets/code/bench` **v1.1.0** (23 tâches par séparation : 12 Python, 5 C++, 6 HTML). Génération gloutonne, 700 tokens maximum, une seule exécution par tâche, consignes en français.

| Langage | dev | test |
|---|---|---|
| Python (tests exécutés) | 9/12 (75 %) | 7/12 (58 %) |
| C++ (compilé et exécuté, g++ 17) | 5/5 (100 %) | 3/5 (60 %) |
| HTML (structure vérifiée) | 3/6 (50 %) | 5/6 (83 %) |
| **Total** | **17/23 (73,9 %)** | **15/23 (65,2 %)** |

Total des deux séparations : 32/46 (69,6 %). Résultats bruts : `projets/code/bench/results/qwen25c-05b-{dev,test}-v1.1.json`.

## Historique du banc (pourquoi v1.1.0)

La première mesure (v1.0.0, dev) donnait 16/23. Elle a révélé deux défauts **du banc**, corrigés avant toute décision :
- le test C++ `fibonacci(50)` faisait expirer une récursion naïve pourtant correcte : remplacé par `fibonacci(30)` ;
- en HTML, le modèle de base prenait la consigne pour du contenu à afficher : l'invite contient maintenant un exemple complet hors banc.
Le banc dev v1.0.0 avait été regardé pour ces corrections ; test n'a été lu qu'après le gel de la v1.1.0.

## Lecture

- **Un modèle de 0,5 G sait déjà écrire du code correct pour des fonctions courtes** (Python, C++) à partir d'une consigne en français, sans qu'on l'ait adapté.
- **Échecs typiques :** HTML avec structure demandée précise (sections, script, nav) où le modèle écrit une page générique ; Python quand la consigne détaille un cas limite (chiffres romains, fréquences de mots) ; boucles de répétition en génération gloutonne.
- Les échecs HTML varient beaucoup d'un split à l'autre (50 % contre 83 %) : 6 tâches par split ne permettent pas de conclure sur ce langage.
- **Limites :** 23 tâches par séparation, une graine (gloutonne), vérificateurs HTML structurels (ils ne jugent pas le rendu). Un écart de moins de 15 points entre deux modèles n'est pas significatif sur ce banc.
- Ce chiffre est le **plancher à battre** pour le cœur de code. Il servira de témoin quand Input lui parlera : par texte puis par canal interne.

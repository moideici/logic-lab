# Cœur de code (HTML, Python, C++) : dix candidats (18 octobre 2026)

But : un modèle qui sait produire du code, sans qu'on lui demande de bien converser, relié à Input par un canal interne (vecteurs, pas des phrases) pour qu'Input n'ait qu'à communiquer. Contrainte : une RTX 4060 de 8 Go qui doit contenir le cœur, Input (Pleias ≈ 0,7 Go) et l'entraînement des adaptateurs de liaison. Je privilégie donc ≤ 2 B de paramètres.

Les faits marqués (v) viennent des cartes Hugging Face officielles consultées le 18 octobre 2026. **Aucun modèle n'a été mesuré sur notre machine** ; les notes sont un jugement de départ.

## Grille (note /10 par critère, pondérée, total /100)

| Critère | Poids | Question |
|---|---|---|
| Code | 30 | Python, HTML et C++ : niveau et couverture connus ? |
| Taille et coût | 20 | Tient-il à côté d'Input avec marge d'entraînement sur 8 Go ? |
| Forkabilité | 15 | Architecture standard, outillage Hugging Face/PEFT, accès aux états internes ? |
| Liaison interne | 15 | Décodeur dense standard (entrées par `inputs_embeds`, états cachés lisibles) ? |
| Licence | 10 | Usage et modification libres ? |
| Contexte et complétion | 10 | Fenêtre utile pour une page HTML entière, remplissage au milieu ? |

## Tableau

| # | Modèle | Paramètres | Licence | Contexte | Ce que dit la carte | Code | Taille | Fork | Liais. | Lic. | Ctx | **Note** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen2.5-Coder-1.5B** | 1,54 G (v) | Apache 2.0 (v) | 32 768 (v) | Base, 28 couches, GQA 12/2, entraînement « 5,5 T tokens » pour la série, FIM recommandé (v). Pas de chiffres ni de liste de langages sur la carte | 8 | 7 | 10 | 9 | 10 | 10 | **86,5** |
| 2 | **Qwen2.5-Coder-0.5B** | 0,49 G (v) | Apache 2.0 (v) | 32 768 (v) | Même famille, 24 couches (v) | 5 | 10 | 10 | 9 | 10 | 10 | **83,5** |
| 3 | **Yi-Coder-1.5B** | ~1,5 G (la carte dit 1 G) | Apache 2.0 (v) | 128 K (v) | 52 langages (v) ; pas de score HumanEval/MBPP sur la carte | 7 | 7 | 9 | 8 | 10 | 10 | **80,5** |
| 4 | **Qwen3-1.7B** (généraliste de référence) | ~1,7 G | Apache 2.0 | grand | Pas un modèle de code ; niveau code non vérifié ici | 6 | 6 | 10 | 9 | 10 | 10 | **78,5** |
| 5 | **DeepSeek-Coder-1.3B-base** | 1,3 G (v) | Licence DeepSeek, usage commercial permis (v) | 16 K (v) | FIM, 87 % de code (v) ; pas de score chiffré sur la carte | 6 | 8 | 9 | 8 | 7 | 8 | **74,5** |
| 6 | **OpenCoder-1.5B-Base** | ~1,5 G (2 G annoncés par les métadonnées) | « inf », permissive selon le dépôt (v) | **4 K** (v) | **HumanEval 54,3 ; MBPP 70,6 ; BigCodeBench 24,5** (v) ; données ouvertes, anglais et chinois | 8 | 7 | 8 | 8 | 6 | 4 | **72,0** |
| 7 | **Granite-3B-Code-base-2k** | 3 G (v) | Apache 2.0 (v) | 2 K (déduit du nom) | 116 langages, **C++ 35,4, Python 36,6** (v) ; **carte : « non recommandé pour de nouveaux projets »** | 6 | 4 | 8 | 6 | 10 | 3 | **60,0** |
| 8 | **StarCoder2-3B** | 3 G (v) | BigCode OpenRAIL-M v1 (v) | 16 K, fenêtre 4 K (v) | HumanEval 31,7 (v) ; 6,3 Go en bf16 (v) | 5 | 4 | 9 | 6 | 6 | 8 | **59,5** |
| 9 | **CodeGemma-2B** | 2 G (3 G annoncés) | Conditions Gemma, accès restreint (v) | non indiqué | HumanEval 31,1 ; MBPP 43,6 ; C++ évalué (v) ; conçu pour la complétion | 5 | 6 | 7 | 6 | 5 | 5 | **56,5** |
| 10 | **Mify-Coder** (2,5 G, article de décembre 2025) | 2,5 G | **non vérifiée** | non vérifié | Annonce MBPP 91 %, HumanEval 54 % (article, non reproduit) ; poids et licence à confirmer | 7 | 5 | 4 | 5 | 3 | 5 | **52,5** |

Détail des notes pondérées : Code ×30, Taille ×20, Fork ×15, Liaison ×15, Licence ×10, Contexte ×10.

## Lecture

- **Le trio de tête est homogène (même famille Qwen2.5-Coder, puis Yi-Coder)** : Apache 2.0, décodeurs denses standard, longs contextes. Je prendrais **Qwen2.5-Coder-0.5B pour prototyper** (peu de mémoire, itérations rapides) et **1.5B pour viser la qualité**. Ils partagent le même tokenizer et la même architecture, donc une liaison entraînée sur le petit se transpose au grand.
- **OpenCoder est le seul avec des scores publiés sur sa carte**, et ses données sont ouvertes, mais son contexte de 4 K est court pour du HTML et sa licence est à lire.
- **Les 3 B (Granite, StarCoder2) sont trop gros** pour cohabiter avec Input pendant l'entraînement sur 8 Go, sauf quantification.
- **Aucune carte ne donne de score par langage pour HTML.** HTML est un langage de balisage : on ne trouvera pas de benchmark public convaincant. Il faudra notre propre épreuve (la page se génère-t-elle, est-elle valide, contient-elle les éléments demandés ?). C++ se vérifie en compilant, Python en exécutant des tests.
- Les licences OpenRAIL-M, Gemma et DeepSeek imposent des conditions d'usage : à lire avant toute diffusion.

## Justification des notes

Principe : une note de 0 à 10 par critère, attribuée d'après ce que dit la carte officielle quand elle existe, et d'après mon jugement quand elle se tait. **Ce sont des notes d'ordre**, pas des mesures : elles servent à ouvrir la liste des modèles à tester, pas à conclure. Les chiffres de la carte sont marqués (v).

Barèmes :
- **Code (30)** : 8-10 = score public élevé ou reproduit ; 6-7 = bon niveau annoncé sans chiffre sur la carte ; 4-5 = score publié faible (HumanEval ≈ 31) ou modèle conçu pour la complétion ; il n'y a aucun 9-10 car personne n'est mesuré chez nous. HTML n'a de benchmark nulle part : tous les modèles sont notés surtout sur Python et C++.
- **Taille et coût (20)** : mémoire en bf16 à côté d'Input (≈ 0,7 Go) et d'un entraînement d'adaptateurs sur 8 Go. 10 = moins de 1 Go ; 7 = environ 3 Go ; 4 = 6 Go ou plus.
- **Forkabilité (15)** : architecture standard, accès libre, outillage Hugging Face/PEFT. Pénalités : accès restreint (gated), architecture ou poids non vérifiés.
- **Liaison interne (15)** : décodeur dense standard, états cachés lisibles et entrée par vecteurs possible. Tous les candidats sont des décodeurs ; la note baisse pour les modèles dont l'architecture n'est pas détaillée ou qui sont plus gros que ce que la liaison peut utiliser.
- **Licence (10)** : 10 = Apache 2.0 ; 6-7 = licence avec conditions d'usage (OpenRAIL-M, DeepSeek, « inf ») ; 3-5 = licence restrictive ou inconnue.
- **Contexte et complétion (10)** : 10 = 32 K ou plus ; 8 = 16 K ; 4 = 4 K ; 3 = 2 K (une page HTML entière ne tient pas).

| Modèle | Pourquoi ces notes |
|---|---|
| **Qwen2.5-Coder-1.5B** (86,5) | Code 8 : modèle spécialisé, 5,5 T tokens pour la série (v), FIM prévu (v) ; mais la carte ne donne **aucun** score ni liste de langages, donc pas plus. Taille 7 : 1,54 G, environ 3 Go en bf16. Fork 10 et liaison 9 : Qwen standard, 28 couches, GQA 12/2 (v), même famille que l'outillage déjà utilisé pour Input. Licence 10 (Apache 2.0, v). Contexte 10 (32 768, v). |
| **Qwen2.5-Coder-0.5B** (83,5) | Code **5** : 0,49 G (v) ; un si petit modèle écrit des fonctions simples mais pas des programmes cohérents (jugement, pas mesure). Taille 10 : environ 1 Go. Reste identique au 1.5B pour fork, licence, contexte. Sa place tient à la taille : il passe devant Yi-Coder uniquement parce qu'on pondère la mémoire. |
| **Yi-Coder-1.5B** (80,5) | Code 7 : 52 langages (v), mais aucun HumanEval/MBPP sur la carte du 1.5B (le seul chiffre, LiveCodeBench 23 %, concerne le 9B). Taille 7. Fork 9 et liaison 8 : standard, mais moins documenté que Qwen. Licence 10 (Apache 2.0, v). Contexte 10 (128 K, v). Incohérence de la carte : « 1,5 B » dans le nom, « 1 B » dans les métadonnées : à vérifier. |
| **Qwen3-1.7B** (78,5) | Ce n'est **pas** un modèle de code : je le garde comme référence généraliste. Code 6 : non vérifié ici, je suppose un niveau correct mais inférieur à un spécialiste. Taille 6 (~1,7 G). Fork 10, liaison 9, licence 10 : même écosystème que Qwen3-0.6B, que nous utilisons déjà. |
| **DeepSeek-Coder-1.3B** (74,5) | Code 6 : 87 % de code dans l'entraînement et FIM (v), mais la carte affirme « état de l'art » **sans chiffre**. Taille 8 (1,3 G). Licence 7 : licence propre « deepseek-license », usage commercial permis (v), conditions à lire. Contexte 8 (16 K, v). La carte est incohérente sur les tokens (1 T ou 2 T). |
| **OpenCoder-1.5B-Base** (72,0) | Code 8 : seul candidat avec des **scores publiés sur la carte** : HumanEval 54,3, MBPP 70,6, BigCodeBench 24,5 (v), entraîné sur 2,5 T tokens dont 90 % de code (v). Mais contexte **4 K** (note 4 : une page HTML longue ne tient pas) et licence « inf » dont les termes sont ailleurs (note 6). Données ouvertes, anglais et chinois. |
| **Granite-3B-Code-base-2k** (60,0) | Code 6 : C++ 35,4, Python 36,6, JavaScript 37,2 (v), 116 langages (v), HTML non mentionné. Taille 4 : 3 G (~6 Go en bf16). Contexte 3 (2 K). Licence 10 (Apache 2.0). **La carte dit « non recommandé pour de nouveaux projets »** : j'ai baissé le fork à 8. |
| **StarCoder2-3B** (59,5) | Code 5 : HumanEval 31,7 (v), 17 langages listés (v). Taille 4 : 6,3 Go en bf16 (v). Licence 6 : OpenRAIL-M, avec clauses d'usage. Contexte 8 (16 K, fenêtre glissante de 4 K, v). |
| **CodeGemma-2B** (56,5) | Code 5 : HumanEval 31,1, MBPP 43,6 (v), C++ évalué (v), mais conçu pour la **complétion** (v), pas la génération de programmes entiers. Taille 6. Fork 7 : accès restreint, il faut accepter les conditions de Google (v). Licence 5 : conditions Gemma. Contexte non indiqué sur la carte : note par défaut 5. |
| **Mify-Coder 2,5 G** (52,5) | Je l'ai trouvé par un article de décembre 2025 (MBPP 91 %, HumanEval 54 % annoncés). **Poids, licence et contexte non vérifiés** : fork 4, licence 3, contexte 5 par prudence. C'est une note d'ignorance, pas de qualité : si les poids sont libres, il remonterait. |

## Sensibilité au choix des poids

J'ai recalculé le classement en changeant les poids pour voir ce qui est robuste :

| Variante | Quatre premiers |
|---|---|
| Poids de base | Qwen2.5-Coder-1.5B (86,5) · Qwen2.5-Coder-0.5B (83,5) · Yi-Coder (80,5) · Qwen3-1.7B (78,5) |
| Code ×2 | Qwen2.5-Coder-1.5B (85,0) · **Yi-Coder (78,1)** · Qwen2.5-Coder-0.5B (75,8) · Qwen3-1.7B (74,2) |
| Taille ×2 | **Qwen2.5-Coder-0.5B (86,2)** · Qwen2.5-Coder-1.5B (83,8) · Yi-Coder (78,8) · Qwen3-1.7B (75,4) |
| Licence ×3 | Qwen2.5-Coder-1.5B (88,8) · Qwen2.5-Coder-0.5B (86,2) · Yi-Coder (83,8) · Qwen3-1.7B (82,1) |

Robuste : les deux Qwen2.5-Coder et Yi-Coder restent dans les trois premiers, quel que soit le poids. Fragile : l'ordre entre le 0,5 B et Yi-Coder dépend de la place donnée au code et à la mémoire. Les modèles 6 à 10 restent derrière dans toutes les variantes.

## Sources (cartes consultées le 18 octobre 2026)

[Qwen2.5-Coder-1.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B) · [Qwen2.5-Coder-0.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B) · [Yi-Coder-1.5B](https://huggingface.co/01-ai/Yi-Coder-1.5B) · [OpenCoder-1.5B-Base](https://huggingface.co/infly/OpenCoder-1.5B-Base) · [DeepSeek-Coder-1.3B-base](https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-base) · [Granite-3B-Code-base-2k](https://huggingface.co/ibm-granite/granite-3b-code-base-2k) · [StarCoder2-3B](https://huggingface.co/bigcode/starcoder2-3b) · [CodeGemma-2B](https://huggingface.co/google/codegemma-2b) · [Mify-Coder](https://arxiv.org/pdf/2512.23747)

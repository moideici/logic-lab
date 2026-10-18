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

## Sources (cartes consultées le 18 octobre 2026)

[Qwen2.5-Coder-1.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B) · [Qwen2.5-Coder-0.5B](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B) · [Yi-Coder-1.5B](https://huggingface.co/01-ai/Yi-Coder-1.5B) · [OpenCoder-1.5B-Base](https://huggingface.co/infly/OpenCoder-1.5B-Base) · [DeepSeek-Coder-1.3B-base](https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-base) · [Granite-3B-Code-base-2k](https://huggingface.co/ibm-granite/granite-3b-code-base-2k) · [StarCoder2-3B](https://huggingface.co/bigcode/starcoder2-3b) · [CodeGemma-2B](https://huggingface.co/google/codegemma-2b) · [Mify-Coder](https://arxiv.org/pdf/2512.23747)

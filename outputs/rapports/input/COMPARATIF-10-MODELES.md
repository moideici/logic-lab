# Garry Input : dix bases candidates (18 octobre 2026)

Objectif : choisir la base du fork avancé (réduction de vocabulaire, couches liées, distillation, quantification) sur une RTX 4060 de 8 Go, pour du français. **Aucun de ces modèles n'a encore été mesuré sur notre banc** : les notes ci-dessous sont un jugement de départ, pas un résultat. Les faits marqués (v) ont été relevés dans des sources web du 18 octobre 2026 (secondaires pour la plupart : à recouper avec la fiche officielle avant de s'y fier) ; les autres viennent de ma connaissance générale ou de nos propres fichiers.

## Grille de notation

Note sur 10 par critère, pondérée, total sur 100.

| Critère | Poids | Question posée |
|---|---|---|
| Français | 25 | Le français est-il une langue d'entraînement revendiquée et crédible ? |
| Qualité de base | 20 | Que sait-il faire avant notre adaptation ? |
| Taille et coût | 20 | Tient-il largement en 8 Go pour inférence, LoRA et expériences ? |
| Forkabilité | 15 | Architecture standard, outillage Hugging Face/PEFT, pas de noyau spécial ? |
| Licence | 10 | Usage et modification libres ? |
| Optimisabilité | 10 | Marge pour réduire le vocabulaire, lier des couches, élaguer ? |

## Tableau

| # | Modèle | Paramètres | Architecture / vocabulaire | Licence | FR | Qual. | Taille | Fork | Lic. | Opt. | **Note /100** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen3-1.7B** | ~1,7 G | Transformeur dense, grand vocabulaire Qwen (~152 k) | Apache 2.0 (nos fichiers : Qwen3-0.6B Apache 2.0) | 8 | 8 | 4 | 10 | 10 | 9 | **78,0** |
| 2 | **Qwen3-0.6B** (actuel) | ~0,6 G | Transformeur dense, ~152 k tokens, embeddings ≈ un quart du total | Apache 2.0 | 7 | 6 | 7 | 10 | 10 | 9 | **77,5** |
| 3 | **Qwen3.5-0.8B** | 0,8 G (v) | Hybride Gated DeltaNet / attention 3:1, ~248 k tokens, 24 couches, multimodal, 201 langues (v) | Apache 2.0 (v ; une source dit licence Qwen) | 8 | 8 | 6 | 6 | 10 | 8 | **75,0** |
| 4 | **Qwen2.5-0.5B** | ~0,5 G | Transformeur dense, ~152 k tokens | Apache 2.0 | 6 | 4 | 8 | 10 | 10 | 9 | **73,0** |
| 5 | **Gemma 3 270M** | 270 M, dont ~170 M d'embeddings et ~100 M de blocs (v) | Transformeur, ~262 k tokens, 18 couches, texte seul, contexte 32 k (v) | Conditions Gemma, accès restreint sur HF (v ; une source dit Apache) | 7 | 4 | 9 | 8 | 5 | 8 | **68,5** |
| 6 | **Pleias-350M (aperçu)** | 350 M (v) | Entraîné sur données ouvertes, français pris en charge (v) | Non confirmée | 8 | 3 | 9 | 7 | 7 | 6 | **67,5** |
| 7 | **LFM2-700M** | 742 M (v) | Hybride convolutions courtes (10) + attention (6), 16 couches, contexte 32 k (v) | LFM Open License v1.0 (v) | 7 | 5 | 8 | 5 | 5 | 6 | **62,0** |
| 8 | **SmolLM2-360M** | 360 M (v) | Transformeur, vocabulaire 49 152 (v, indirect), 4 T tokens (v) | Apache 2.0 (v) | 3 | 4 | 9 | 9 | 10 | 5 | **62,0** |
| 9 | **LFM2-350M** | 354 M (v) | Même hybride, 16 couches (v) | LFM Open License v1.0 (v) | 6 | 4 | 9 | 5 | 5 | 6 | **59,5** |
| 10 | **SmolLM2-135M** | 135 M (v) | Transformeur, vocabulaire 49 152 (v, indirect), 2 T tokens (v) | Apache 2.0 (v) | 2 | 2 | 10 | 9 | 10 | 4 | **56,5** |

## Lecture

- **Le classement reflète mes pondérations.** Changer le poids du français ou de la taille le remanie ; un écart de moins de 5 points n'est pas significatif. Les notes « Qual. » et « FR » sont des estimations, à remplacer par des mesures.
- **Qwen3-1.7B en tête est trompeur pour notre but** : il est moins « faible » que ce que tu veux forker. Je le vois plutôt comme **professeur** pour distiller vers un élève plus petit.
- **Gemma 3 270M est le plus fort levier de réduction** : environ 63 % de ses paramètres sont des embeddings. En ne gardant que le vocabulaire utile au français, on retire une très grande part du modèle sans toucher aux blocs. Sa licence est le principal frein.
- **Qwen3.5-0.8B et LFM2 sont les paris** : architectures hybrides, plus rares et plus intéressantes à visualiser dans le Lab, mais l'outillage de fine-tuning sur Windows et sur 8 Go est moins sûr (noyaux spéciaux possibles : à vérifier avant tout engagement).
- **Pleias est le seul pensé pour le français et les données ouvertes**, mais c'est un aperçu : qualité de base probablement faible, licence à confirmer.
- **SmolLM2 est le plus simple à forker**, mais il est conçu surtout pour l'anglais : mauvais candidat pour du français.

## Proposition de sélection

Passer sur notre banc de régression (même recette d'adaptation, mêmes données, même matériel) :

1. **Qwen3-0.6B** : élève et référence actuelle.
2. **Qwen3-1.7B** : professeur de distillation et plafond de qualité.
3. **Gemma 3 270M** : test du réducteur de vocabulaire extrême.
4. **Qwen3.5-0.8B** : test de l'hybride.
5. **Pleias-350M** : test du « français natif » sur données ouvertes.

Chaque candidat reçoit la même adaptation puis passe le banc dev (le test reste réservé). La décision se fait sur qualité, temps et mémoire mesurés, pas sur ce tableau.

## Sources

- [Luth : spécialisation française de petits modèles (LFM2 et Qwen3)](https://arxiv.org/pdf/2510.05846)
- [Fiche Gemma 3 270M](https://huggingface.co/google/gemma-3-270m) et [synthèse tierce](https://apxml.com/models/gemma-3-270m)
- [Pleias-350M Preview](https://huggingface.co/PleIAs/Pleias-350m-Preview)
- [Qwen3.5 petits modèles (Artificial Analysis)](https://artificialanalysis.ai/articles/qwen3-5-small-models), [Qwen3.5-0.8B (ApX)](https://apxml.com/models/qwen35-08b)
- [LFM2-350M](https://featherless.ai/models/LiquidAI/LFM2-350M), [LFM2-1.2B (fiche de la famille)](https://huggingface.co/LiquidAI/LFM2-1.2B)
- [SmolLM2-135M](https://huggingface.co/HuggingFaceTB/SmolLM2-135M)

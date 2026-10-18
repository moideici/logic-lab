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
| 1 | **Pleias-350M (aperçu)** | ~350 M (carte) | Llama, 26 couches, 1024 de large, vocabulaire 65 536 (v), contexte **2 048** (v), base sans chat, 1 T tokens de données ouvertes (v) | **Apache 2.0 (v, confirmé sur la carte)** | 9 | 4 | 10 | 9 | 10 | 5 | **79,0** |
| 2 | **Qwen3-1.7B** | ~1,7 G | Transformeur dense, grand vocabulaire Qwen (~152 k) | Apache 2.0 (nos fichiers : Qwen3-0.6B Apache 2.0) | 8 | 8 | 4 | 10 | 10 | 9 | **78,0** |
| 3 | **Qwen3-0.6B** (actuel) | ~0,6 G | Transformeur dense, ~152 k tokens, embeddings ≈ un quart du total | Apache 2.0 | 7 | 6 | 7 | 10 | 10 | 9 | **77,5** |
| 4 | **Qwen3.5-0.8B** | 0,8 G (v) | Hybride Gated DeltaNet / attention 3:1, ~248 k tokens, 24 couches, multimodal, 201 langues (v) | Apache 2.0 (v ; une source dit licence Qwen) | 8 | 8 | 6 | 6 | 10 | 8 | **75,0** |
| 5 | **Qwen2.5-0.5B** | ~0,5 G | Transformeur dense, ~152 k tokens | Apache 2.0 | 6 | 4 | 8 | 10 | 10 | 9 | **73,0** |
| 6 | **Gemma 3 270M** | 270 M, dont ~170 M d'embeddings et ~100 M de blocs (v) | Transformeur, ~262 k tokens, 18 couches, texte seul, contexte 32 k (v) | Conditions Gemma, accès restreint sur HF (v ; une source dit Apache) | 7 | 4 | 9 | 8 | 5 | 8 | **68,5** |
| 7 | **LFM2-700M** | 742 M (v) | Hybride convolutions courtes (10) + attention (6), 16 couches, contexte 32 k (v) | LFM Open License v1.0 (v) | 7 | 5 | 8 | 5 | 5 | 6 | **62,0** |
| 8 | **SmolLM2-360M** | 360 M (v) | Transformeur, vocabulaire 49 152 (v, indirect), 4 T tokens (v) | Apache 2.0 (v) | 3 | 4 | 9 | 9 | 10 | 5 | **62,0** |
| 9 | **LFM2-350M** | 354 M (v) | Même hybride, 16 couches (v) | LFM Open License v1.0 (v) | 6 | 4 | 9 | 5 | 5 | 6 | **59,5** |
| 10 | **SmolLM2-135M** | 135 M (v) | Transformeur, vocabulaire 49 152 (v, indirect), 2 T tokens (v) | Apache 2.0 (v) | 2 | 2 | 10 | 9 | 10 | 4 | **56,5** |

## Lecture

- **Le classement reflète mes pondérations.** Changer le poids du français ou de la taille le remanie ; un écart de moins de 5 points n'est pas significatif. Les notes « Qual. » et « FR » sont des estimations, à remplacer par des mesures.
- **Qwen3-1.7B en tête est trompeur pour notre but** : il est moins « faible » que ce que tu veux forker. Je le vois plutôt comme **professeur** pour distiller vers un élève plus petit.
- **Gemma 3 270M est le plus fort levier de réduction** : environ 63 % de ses paramètres sont des embeddings. En ne gardant que le vocabulaire utile au français, on retire une très grande part du modèle sans toucher aux blocs. Sa licence est le principal frein.
- **Qwen3.5-0.8B et LFM2 sont les paris** : architectures hybrides, plus rares et plus intéressantes à visualiser dans le Lab, mais l'outillage de fine-tuning sur Windows et sur 8 Go est moins sûr (noyaux spéciaux possibles : à vérifier avant tout engagement).
- **Pleias est le seul pensé pour le français et les données ouvertes.** Fiche vérifiée le 18 octobre 2026 (voir plus bas) : licence Apache 2.0 confirmée, architecture Llama standard, mais base sans chat, contexte limité à 2 048 tokens et aucun benchmark publié.
- **SmolLM2 est le plus simple à forker**, mais il est conçu surtout pour l'anglais : mauvais candidat pour du français.

## Pleias-350M : fiche vérifiée (18 octobre 2026)

Source : [carte officielle](https://huggingface.co/PleIAs/Pleias-350m-Preview) et son `config.json`.

| Point | Constat | Conséquence pour nous |
|---|---|---|
| Licence | Apache 2.0 | Aucun obstacle. Entraînement uniquement sur données ouvertes ou du domaine public. |
| Architecture | `LlamaForCausalLM`, 26 couches, 1024 de large, 16 têtes, MLP 2560, embeddings liés | La plus standard : Transformers, PEFT, GGUF, décodage contraint fonctionnent tels quels. |
| Vocabulaire | 65 536 tokens (embeddings ≈ 67 M) | Déjà compact : **peu à gagner** en réduisant le vocabulaire (contrairement à Qwen3 ou Gemma). Le levier devient les couches liées. |
| Contexte | **2 048 tokens** | Notre fenêtre actuelle (2 400 tokens de prompt) doit descendre sous environ 1 700 pour garder la place de la réponse. |
| Type | Modèle **de base**, aperçu : continuation de texte, aucun gabarit de chat | Il faut lui apprendre le dialogue et le JSON : plus d'exemples qu'avec Qwen3-0.6B, déjà post-entraîné. |
| Qualité | Aucun benchmark chiffré publié ; la carte promet un post-entraînement futur | Inconnue : seul notre banc tranchera. |
| Adaptation | La carte recommande le **fine-tuning complet** plutôt que LoRA | ~350 M de paramètres : faisable sur 8 Go (optimiseur 8 bits ou états en bf16), mais pas pendant que les serveurs Qwen occupent la carte (5,6 Go libres au relevé). |
| Langues | Anglais, français, espagnol, allemand, italien, néerlandais, latin, portugais | Bon signe pour le français ; qualité réelle non mesurée. |

**Variante à regarder : Pleias-Pico (Pleias-RAG-350M)**, dérivé du même modèle, Apache 2.0, entraîné pour répondre **à partir de sources, avec raisonnement et citations**, en français entre autres (Pleias annonce des résultats supérieurs aux petits modèles sur HotPotQA et 2wiki en mode « trivial » ; je n'ai pas vérifié). C'est exactement notre faiblesse : « selon le texte », reconnaître l'absence d'information, ne pas inventer. Son format de sortie est un raisonnement suivi d'une réponse avec sources, pas notre JSON.

### Mesures sur notre machine (18 octobre 2026)

`projets/input/bench/probe_model.py`, résultats dans `bench/results/sonde-*.json`. Fichiers téléchargés depuis Hugging Face : `PleIAs/Pleias-350m-Preview` (révision f175e52, 707 Mo) et `PleIAs/Pleias-RAG-350M` (révision db001b2, 707 Mo), tous deux Apache 2.0 selon l'API du dépôt, chargés en safetensors sans code distant.

| Mesure | Qwen3-0.6B (actuel) | Pleias-350m-Preview | Pleias-RAG-350M |
|---|---|---|---|
| Paramètres | 596 M | **353 M** | 353 M |
| Mémoire GPU (bf16) | 1 137 Mo | **700 Mo** | 700 Mo |
| Chargement | 1,5 s | **0,9 s** | 0,9 s |
| Vitesse de génération (gloutonne, 128 tokens) | 13,9 tokens/s | **20,0 tokens/s** | 20,0 tokens/s |
| Bits par caractère sur 8 passages français | 0,965 | **0,872** | 1,015 |
| Caractères par token (français) | 3,61 | **4,03** | 4,03 |
| Contexte | 40 960 | 2 048 | 4 096 |
| Gabarit de chat | oui | non | non |

Lecture honnête : la vitesse a été mesurée avec les serveurs Input et Garry actifs sur la même carte, séquentiellement et dans les mêmes conditions ; l'ordre de grandeur (×1,4) compte plus que la valeur. Les bits par caractère portent sur huit courts passages que j'ai rédigés (≈ 3 000 caractères) : indicatif, pas un benchmark. Qwen3-0.6B est la version post-entraînée, ce qui défavorise un peu sa perte sur du texte brut ; la comparaison équitable serait avec Qwen3-0.6B-Base, non téléchargé.

Continuations (base, sans consigne) : Pleias écrit un français fluide et naturel mais invente des faits (« La capitale de la France est un lieu d'attraction… », une omelette « cuite dans un mortier de marbre »). Sur « côtés 3 et 4, angle droit, le troisième côté mesure », il donne bien « 5 » puis divague. Qwen3-0.6B dérive vers un QCM en anglais. Pleias-RAG est un moins bon modèle de langue brut (1,015) car il est spécialisé ; son intérêt est ailleurs (voir plus haut) et ne se juge que sur des cas avec sources.

**Avis :** possible et prometteur. Il est plus petit, plus rapide et meilleur en français brut, mais c'est un modèle de base : tout le comportement de dialogue, de format et de prudence reste à apprendre, et son contexte de 2 048 tokens est une contrainte. Note révisée de 67,5 à **79,0** (français mesuré, taille et vitesse, licence confirmée). Écart avec Qwen3-1.7B (78,0) et Qwen3-0.6B (77,5) non significatif : seule l'adaptation sur notre banc départagera. À tester en deux temps : (1) le modèle de base, fine-tuning complet sur notre format et nos données ; (2) Pleias-Pico comme point de départ pour les cas fondés sur des sources.

## Résultat de l'adaptation de Pleias-350m-Preview (18 octobre 2026)

Même données et même format que l'adaptation de Qwen (7 598 exemples, perte pondérée identique), même banc dev (51 cas, 3 essais, contrat 1). Pleias est un modèle de base : il faut lui apprendre le dialogue en plus du format. `train_sft.py`, `prompting.py`, résultats dans `projets/input/bench/results/pleias-*-dev.json`.

| Mesure (dev) | Qwen3-0.6B + LoRA (actuel) | Pleias LoRA r=8, attention | Pleias LoRA r=32, toutes couches |
|---|---|---|---|
| Réussite globale | **54,2 %** | 15,0 % | 24,8 % |
| Paramètres entraînés | 1,1 M (r=8) | 1,5 M | 14,9 M |
| Perte de validation (format) | non comparable | 0,740 | 0,689 (pas 1600 ; remonte ensuite) |
| Durée d'entraînement | 30 min (plusieurs cycles) | 11 min | 57 min |
| Latence médiane | 4,5 s | **2,0 s** | 8,6 s (carte en partage) |
| Prénom retenu | 100 % | 56 % | 100 % |
| Préférence retenue | 17 % | 42 % | **58 %** |
| Correction d'une valeur | 75 % | 17 % | 8 % |
| Calcul | **88 %** | 0 % | 0 % |
| Planning, comparaison | 28 %, 33 % | 0 %, 0 % | 0 %, 0 % |
| Selon un texte donné | 67 % | 44 % | 33 % |
| Information absente, fait non vérifiable | 22 %, 22 % | 0 %, 0 % | 0 %, 11 % |
| Réponse affirmée sans réponse possible (invention) | 83 % | 89 % | 89 % |

**Diagnostic** (essai hors banc, génération libre sans décodage contraint) : sur une consigne identique à celles de l'entraînement (« Calcule 679 × 3… »), Pleias r=32 écrit exactement le bon JSON avec `a`=679, `b`=3 et un résultat de **2147 au lieu de 2037**. Il a donc appris le format, mais ni l'arithmétique ni la généralisation : sur « Combien font 17 fois 23 ? », il produit un texte creux et `valeurs` vide. Un modèle de base de 350 M n'a pas, à ce niveau d'adaptation, le calcul que Qwen3-0.6B (post-entraîné) apporte déjà.

**Conclusion :** à données égales, Pleias est nettement moins bon que Qwen3-0.6B sur ce banc, et plus rapide seulement quand la carte n'est pas partagée. Il n'est pas retenu pour Input dans l'état. Son bon français brut (0,872 bit/caractère contre 0,965) ne se transforme pas en réponses justes avec nos données, qui sont pauvres et très gabaritées (aucun exemple de prudence, de planning ni de comparaison). Les fichiers et les scripts sont conservés : si le cœur de code prend en charge le raisonnement (voir `COMPARATIF-10-MODELES-CODE.md`), Input n'aura plus à calculer ni à raisonner et la question se reposera sur une tâche plus simple (comprendre une demande, la reformuler, répondre en français), où Pleias pourrait suffire. À refaire alors, avec de meilleures données.

Limites : une graine, 51 cas, 3 essais corrélés ; r=32 mesuré au meilleur point de validation (pas 1600), non au dernier ; pas d'entraînement complet (non LoRA), que la carte recommande et que nous n'avons pas essayé.

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

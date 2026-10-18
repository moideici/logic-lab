# Premier corpus lexical français

Source : [édition française du Wiktionnaire, extraction Kaikki](https://kaikki.org/frwiktionary/Fran%C3%A7ais/index.html). Les définitions sont en français. La sélection initiale porte sur des mots courants, des verbes, des relations spatiales et temporelles et plusieurs mots polysémiques.

`python import_dictionary.py` télécharge les petites entrées structurées et construit `lexicon/senses.jsonl`, un manifeste et trois partitions. Tous les sens et formes d’un mot restent dans la même partition. Les citations d’exemples attribuées à des ouvrages externes sont écartées. Les relations non désambiguïsées sont conservées comme telles : elles ne sont pas automatiquement considérées comme vraies pour tous les sens.

Chaque entrée indique sa page d’origine, son historique d’auteurs, son extraction, son empreinte et les transformations effectuées. Les données dérivées sont sous [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) ; attribution aux contributeurs du Wiktionnaire, extraction par Kaikki/Wiktextract. Voir les [conditions du Wiktionnaire](https://fr.wiktionary.org/wiki/Wiktionnaire:R%C3%A9utilisation_du_contenu_du_Wiktionnaire). Le code de ce prototype est distinct du corpus.

Ces données préparent le prochain cycle : vocabulaire, définitions et choix du sens dans une phrase. Elles ne modifient pas la comparaison initiale déjà lancée. Lire un dictionnaire ne suffit pas à apprendre les dialogues, le raisonnement ou toutes les nuances du français. L’extraction peut contenir des erreurs ; le manifeste publie les échecs de téléchargement.

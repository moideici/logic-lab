# Décisions et justifications

État au 18 octobre 2026. Les demandes ultérieures de l’utilisateur peuvent modifier ces décisions ; conserver alors la raison et l’effet du changement.

| Décision | Pourquoi | Conséquence et limite |
|---|---|---|
| Regrouper les projets dans la conversation | L’utilisateur veut un dossier de travail unique, complet et documenté. | Copie des sources, données, poids et Git ; originaux conservés. Ne pas continuer à éditer alternativement les deux emplacements. |
| Conserver deux projets principaux | Garry et Input ont des architectures, données et objectifs différents. | Navigation commune possible ; aucune fusion implicite des poids ou métriques. |
| Faire le plan avant la suite | L’utilisateur a explicitement demandé de fixer les priorités avant de poursuivre. | Regroupement et documentation autorisés ; la prochaine étape produit reste la recette de l’interface. |
| Interface et utilisation en premier | L’attente opaque, le JSON brut et les badges trompeurs empêchent une utilisation claire. | Rendre l’application cohérente avant d’accumuler de nouveaux entraînements. La première ébauche n’est pas déclarée intégralement validée. |
| Séparer format et vérité | Une réponse sur Macron avait un JSON valide mais un contenu faux. | Aucun badge syntaxique ne doit présenter le fond comme vérifié. Mesures séparées. |
| Recentrer Input sur les compétences utiles | L’utilisateur privilégie français, maths, vocabulaire, contexte et fonctionnement réel. | Pas de reprise automatique du mélange encyclopédique généraliste. Une restriction d’usage n’efface pas toutes les connaissances préentraînées. |
| Conserver Wikipédia comme archive | Les corpus importés font partie de la provenance et coûtent à télécharger. | Conservation des fichiers, sans obligation de les réutiliser. Ne pas compter les articles importés comme des articles appris. |
| Autoriser Markdown par champ | L’utilisateur veut une mise en forme lisible tout en conservant les données typées. | `texte` et `justification` dans le futur contrat ; `etat`, `decision`, `valeurs` restent bruts. Rendu et validation à implémenter. |
| Exiger des justifications fondées | Une explication fluide peut soutenir une décision fausse. | Vérifier faits, contraintes et cohérence avec les résultats. Évaluer les explications séparément de la syntaxe. |
| Contrat v2 prêt mais non activé | Le décodage contraint garantit la forme, pas le fond ; l'adaptation 0.2.0 n'a jamais vu `etat`, `decision` ni `justification`. | Activation par `INPUT_CONTRACT=2` ou `"contrat": 2` dans `active.json`, après entraînement (lot 4). Un état `limite` s'ajoute aux trois du plan. |
| Réintroduire un cœur de code relié à Input (18 octobre 2026) | L'utilisateur veut qu'Input n'ait plus à réfléchir mais à communiquer, un petit modèle de code (HTML, Python, si possible C++) faisant le travail, relié par un canal interne et non par des phrases. Cela annule l'abandon antérieur de l'agent producteur de code. | Hypothèse à mesurer, pas acquise : le canal latent doit battre un canal texte de référence (Input écrit une consigne en texte au cœur de code) sur nos épreuves, avec canaux coupé et permuté comme témoins. Candidats : `outputs/rapports/input/COMPARATIF-10-MODELES-CODE.md`. |
| Retenir trois usages | Contraintes, plans et comparaisons plaisent à l’utilisateur. | Les épreuves de référence précèdent le choix définitif du cœur général. |
| Étudier une communication interne continue | L’utilisateur souhaite un échange de représentations, sans imposer une traduction intermédiaire en français ou anglais. | Adaptateurs à entraîner et comparer ; aucune compatibilité universelle des états internes présumée. |
| Garder HRM comme expérience sudoku | Ses poids officiels et une interface continue permettent des essais concrets. | Un succès sur une grille et trois tests techniques ne prouvent pas un raisonnement général. |
| Garder TRM comme référence | Architecture récursive pertinente pour comparer les pistes. | Référence de code seulement dans l’état téléchargé ; pas un modèle actif ou déjà entraîné localement. |
| Abandonner l’agent producteur de code | L’utilisateur a retiré cette idée. | Aucun cœur spécialisé code à introduire comme priorité actuelle. |
| Optimiser le rapport qualité/coût | L’utilisateur veut le modèle le plus rentable possible. | Mesurer bonnes réponses, temps, mémoire et énergie disponible. Pas de promesse de rentabilité certifiée de chaque connexion. |
| Ne réduire les modèles qu’avec comparaison | Quantification, distillation ou élagage peuvent changer les erreurs. | Mesurer qualité et économies sur les mêmes cas ; ne pas conclure depuis la seule taille. |
| Garder Garry en 0.6.0 | Version demandée par l’utilisateur ; les performances ne déterminent pas les numéros. | Changements de code et d’architecture justifient les versions ; empreintes séparées pour les poids. |
| Cibler zéro défaite sur un protocole précis | L’utilisateur a choisi départ vide, ancienne version et deux camps. | Applicable aux duels ; scores et réussite adaptés aux jeux solo. Aucune promesse d’invincibilité universelle. |
| Garder les références et échecs archivés | Reproduction, comparaison et compréhension des erreurs de protocole. | Les reprises invalidées ne servent pas de preuves de progrès. Tests et apprentissage restent séparés. |

## Ce qui reste à décider

- Le cœur définitif pour les trois usages et la représentation des problèmes.
- Le profil Markdown exact et le futur schéma versionné.
- Le programme d’entraînement spécialisé après la recette de l’interface.
- Les critères chiffrés qualité/coût et les budgets des expériences suivantes.
- La politique de mémoire longue, à distinguer du contexte récent et des poids appris.

Ces sujets sont ouverts : les exemples du plan ne sont pas des fonctions déjà disponibles ou des performances garanties.

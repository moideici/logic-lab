# Recette du lot 1 : interface Input (18 octobre 2026)

Serveur : `projets/input/serve.py` sur le port 8766, lancé depuis le dossier regroupé. Base Qwen/Qwen3-0.6B (révision c1899de), adaptation `focus-20261017-210925/checkpoint-1000`, version 0.2.0, GPU RTX 4060. Navigateur intégré, parcours scripté.

## Mesures

| Critère (seuil du plan §8) | Résultat | Verdict |
|---|---|---|
| Premier texte visible < 3 s à chaud | 0,45 à 1,1 s | OK |
| Premier texte à froid | 11,8 s avant correction (chargement au premier message) ; modèle maintenant préchargé au démarrage (~6 s), pastille « Chargement du modèle… » puis « Modèle prêt · GPU » | Corrigé |
| Arrêt effectif < 1 s | 53 ms ; texte partiel marqué « Arrêté », exclu du contexte | OK |
| Erreurs JavaScript sur le parcours | 0 (envoi, arrêt, JSON, copie, erreur réseau, nouvelle tentative) | OK |
| Reprise après erreur | Réseau coupé simulé : message « Réponse non terminée » + bouton Réessayer ; la nouvelle tentative aboutit | OK |
| Rechargement sans perte d'historique | 6 messages restaurés, conversation et titre conservés | OK |
| Mobile 375 px | Aucun débordement horizontal (largeur 375/375), lisible | OK |
| Poids réellement servis affichés | Base, révision, adaptation, version et matériel lus depuis le serveur (`/api/modele`) | Corrigé |
| Tests Python Input | 21 réussis | OK |

## Corrections apportées

1. La pastille « Modèle disponible » ne testait que l'existence d'un fichier. Elle reflète désormais l'état réel (non chargé, chargement, prêt, erreur).
2. Le modèle se charge en arrière-plan au démarrage du serveur.
3. Le détail « Modèle et mémoire » affiche les poids réellement chargés, plus un texte fixe.
4. Une erreur réseau affiche un message compréhensible au lieu de « Failed to fetch ».

## Constats hors lot 1 (qualité du modèle, à traiter aux lots 2 à 4)

- Contexte : après « Je m'appelle Lina… » puis « Quel est mon prénom ? », la réponse est « En 391 » (reprise de la réponse précédente). Le contexte est transmis (« 3 message(s) utilisés ») mais le modèle ne l'exploite pas.
- Effondrement sur un gabarit : plusieurs demandes sans rapport (planning, test d'erreur) donnent une réponse sur « effectuer votre commande ».
- Planning de trois tâches : réponse sans rapport (« J'llaie bien enfin ! »).
- Calcul : 17 × 23 → 391, correct, mais formulé « En 391 ».
- Débit mesuré : 6 à 9 tokens/s.

Ces constats sont des cas de régression pour le banc du lot 2. La recette ne valide pas la qualité des réponses.

## Non couvert

Migration des anciennes conversations (clé `logic-lab-input-v1`) vérifiée seulement par lecture du code ; navigation vers Garry ; page Bilan ; copie dans le presse-papiers (boutons présents, contenu non lu) ; plusieurs onglets simultanés.

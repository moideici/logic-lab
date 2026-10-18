# Maintenance Garry 0.6.0

La version courante du logiciel et des nouveaux exports est **0.6.0**, conformément à la demande. Il s’agit d’un changement de numérotation avant version stable, sans changement des dimensions **4 872 → 48 → 48 → 4 259**, des coefficients ou du nombre de jeux (**14**).

Les importeurs Python et JavaScript acceptent **0.6.0** et l’ancien alias **6.0.0**, avec les mêmes contrôles de dimensions et de poids. Les anciennes migrations produisent désormais 0.6.0. Les références figées dans `versions/`, rapports et dossiers d’entraînement gardent leur nom historique. L’entraînement déjà lancé conserve ses propres sauvegardes 6.0.0 compatibles ; aucune écriture concurrente des poids n’a été faite pour changer leur étiquette.

Les corrections précédentes restent en place : trois vies au sudoku en mode IA, absence de répétition du même chiffre refusé, progression effective des niveaux intermédiaires du taquin et fin automatique des duels Go par passes et acceptation du comptage. La difficulté de la grille reste distincte du niveau de l’IA.

Validation après maintenance : **105 tests Python et 63 tests JavaScript réussis**. Les nouveaux tests vérifient que l’alias 6.0.0 conserve exactement les poids et prédictions à l’import puis s’exporte en 0.6.0 ; une version inconnue ou des dimensions fausses restent refusées. Le parcours navigateur confirme la version du bandeau, des décisions et des quatorze jeux de l’API, sur ordinateur et mobile, sans erreur JavaScript.

Le serveur reste disponible à **http://127.0.0.1:8765**. Son actualisation a préservé le processus d’entraînement indépendant. Au relevé du 17 octobre 2026 vers 20 h 03 (Paris), la session cumulait environ **97 000 coups et 34 promotions**, avec environ 36 minutes restantes. Ces promotions contrôlent l’accord avec un professeur borné ; elles ne prouvent pas une invincibilité.

Le harnais COSUMI a été vérifié sur la confirmation d’une passe. La nouvelle partie réelle 19 × 19 a toutefois été **arrêtée après 252 coups vérifiés**, sans résultat final publié par le site : elle ne compte ni comme victoire ni comme partie complète.

Pièces de vérification : `verification-version-0.6.0.json`, `garry-maintenance-python.log`, `garry-maintenance-js.log`, `verification-corrections-jeux.json`, `verification-go-passe-site.json`. Les résultats ultérieurs des sessions restent dans leurs dossiers d’origine et doivent être lus à leur fin.

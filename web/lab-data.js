// Données du Lab. Chaque chiffre vient d'un rapport du dépôt (champ `src`). Rien n'est inventé :
// quand une mesure est bruitée ou non démontrée, `conf` le dit (ok = établi, mid = indicatif, low = non établi).
export const CONF = {
  ok: ['Établi', 'mesuré, écart supérieur au bruit'],
  mid: ['Indicatif', 'mesuré, mais petit échantillon ou bruit comparable à l’écart'],
  low: ['Non établi', 'hypothèse ou résultat négatif'],
};

export const MODELS = [
  {
    id: 'garry', short: 'Garry', name: 'Garry', version: '0.6.0', page: 'modele-garry.html', scene: 'garry', hue: 218,
    role: 'Le joueur généraliste',
    tagline: 'Un seul réseau, quatorze jeux, une recherche qui prouve ce qu’elle peut.',
    summary: 'Garry est le modèle historique de Logic Lab : un perceptron à deux couches cachées de 48 neurones, partagé entre quatorze jeux, qui propose des coups ; une recherche (alpha-bêta, expectimax, solveurs de fin de partie) les confirme ou les corrige. Il apprend en imitant un professeur borné et n’est promu que s’il ne régresse sur aucun jeu.',
    stats: [{ v: 444979, l: 'paramètres' }, { v: 14, l: 'jeux' }, { v: 11, l: 'niveaux (0 à 10)' }, { v: 16, l: 'promotions (session 60 min)' }],
    system: [
      ['Observation', 'Le plateau est encodé en un vecteur de 4 872 entrées ; chaque jeu a sa zone.'],
      ['Réseau', '4 872 → 48 → 48 → 4 259. Le module central de 48 neurones est commun aux quatorze jeux.'],
      ['Masque légal', 'Les logits sont masqués : le réseau ne peut jamais proposer un coup illégal.'],
      ['Recherche', 'Au niveau 10, alpha-bêta ou expectimax selon le jeu, solveurs exacts en fin de partie.'],
      ['Promotion', 'Un candidat n’est installé que s’il égale le champion sur validation fixe et positions fraîches.'],
    ],
    args: [
      ['Un seul modèle pour quatorze jeux', 'Les onze jeux non entraînés sont préservés exactement lors des cycles Go, Hex et Gomoku (contrôle de non-régression).', 'ok'],
      ['La recherche compense le réseau', 'Au Puissance 4 niveau 10, 2,4 % de coups fautifs face au solveur exact ; zéro défaite contre la 3.1.0 figée depuis le plateau vide.', 'ok'],
      ['L’imitation plafonne', 'Go : 14,62 % → 14,46 % d’accord après 60 min. Hex +1,6 point, Gomoku +3,5 points. C’est ce plateau qui a motivé Zéro.', 'ok'],
      ['Invincibilité', 'Non démontrée. Le Go reste faible : défaite de 285,5 points contre COSUMI niveau 1.', 'low'],
    ],
    bench: [
      { title: 'Accord avec le professeur, positions réservées (session 60 min)', note: 'Part des positions où le réseau choisit le coup du professeur. Ce n’est pas un taux de victoire.', unit: '%', max: 60, rows: [['Hex · avant', 43.36], ['Hex · après', 44.92, 1], ['Gomoku · avant', 19.12], ['Gomoku · après', 22.65, 1], ['Go · avant', 14.62], ['Go · après', 14.46, 1]] },
      { title: 'Puissance 4 contre le solveur exact : coups fautifs', note: 'Plus bas est mieux. Mesure P0, 20 parties par cellule.', unit: '%', max: 10, lower: true, rows: [['Hasard', 7.3], ['Garry 0.6.0 niveau 10', 2.4, 1], ['Professeur niveau 10', 1.6]] },
    ],
    duels: [
      ['Garry 0.6.0 niv. 10', 'Solveur exact Puissance 4', 'Puissance 4', '2,4 % de coups fautifs'],
      ['Garry 0.6.0 (poids antérieurs)', 'COSUMI niveau 1 (site réel)', 'Go 19×19', 'défaite de 285,5 points'],
      ['Garry 3.2.0 niv. 10', 'Garry 3.1.0 figé', 'Puissance 4', '1 victoire, 1 nulle, 0 défaite'],
    ],
    limits: ['Les gains sont des accords avec un professeur borné, pas des forces de jeu certifiées.', 'Les grandes grilles (Go 19×19, taquin 5×5) ne sont pas certifiées.', 'Le « meilleur coup sur tout jeu » n’est pas démontré.'],
    src: ['entrainements-garry-zero-2026-10-19.md', 'baselines-unifie-2026-11-09.json', 'README.md'],
    games: ['Morpion', '2048', 'Sudoku', 'Puissance 4', 'Démineur', 'Taquin', 'Reversi', 'Nim', 'Lights Out', 'Dames', 'Percée', 'Hex', 'Gomoku', 'Go'],
  },
  {
    id: 'optimus', short: 'Optimus', name: 'Garry Optimus', version: '0.1', page: 'modele-optimus.html', scene: 'optimus', hue: 232,
    role: 'Le modèle unique multi-jeux',
    tagline: 'Un tronc partagé, des professeurs écrits à la main : la compacité avant la force.',
    summary: 'Optimus est le projet d’un seul grand modèle pour tous les jeux, entraîné par distillation de professeurs exacts ou de recherche (solveur de Puissance 4, moteurs Gomoku et Hex, recherche aux dames). Le pilote P1 montre qu’un réseau multi-jeux tient avec la moitié des paramètres de cinq réseaux séparés ; il n’a pas encore démontré qu’il améliore les jeux.',
    stats: [{ v: 1705306, l: 'paramètres (multi)' }, { v: 5, l: 'jeux au pilote' }, { v: 6, l: 'blocs résiduels × 64 canaux' }, { v: 1, l: 'moitié des paramètres', fmt: '÷ 2' }],
    system: [
      ['Plateau commun', '15 × 15, 8 plans + un vecteur annexe ; toujours du point de vue du joueur au trait.'],
      ['Professeurs', 'Solveur exact (Puissance 4), minimax (morpion), moteurs à la main (Gomoku, Hex), recherche renforcée (dames).'],
      ['Tronc partagé', 'Tronc résiduel 6 × 64, entrées propres à chaque jeu, têtes de politique par case, tête de valeur par jeu.'],
      ['Symétries', 'Huit pour morpion et Gomoku, miroir pour Puissance 4, rotation 180° pour Hex.'],
      ['Juges indépendants', 'Le réseau seul, sans recherche, joue contre des juges qu’il n’a pas vus comme professeurs.'],
    ],
    args: [
      ['Compact', 'Multi-jeux : 1,7 M de paramètres contre 3,5 M pour cinq réseaux séparés, à budget égal d’exemples par jeu.', 'ok'],
      ['Pas moins bon que les réseaux séparés', 'Devant sur 3 jeux sur 5, derrière aux dames, égal ailleurs, mais aucun écart n’est significatif.', 'mid'],
      ['Le multi-jeux améliore les jeux', 'Non démontré : l’écart-type d’une mesure est d’environ 0,09 ; la validation hors-ligne ne montre aucun gain.', 'low'],
      ['Sans recherche, égale Garry au Puissance 4', '1,5 à 2,3 % de coups fautifs contre 2,4 % pour Garry 0.6.0 niveau 10.', 'mid'],
    ],
    bench: [
      { title: 'Puissance 4 : coups fautifs (réseau seul)', note: 'Plus bas est mieux. Moyenne de 2 graines, 24 parties.', unit: '%', max: 8, lower: true, rows: [['Hasard', 7.3], ['Garry 0.6.0 niveau 10', 2.4], ['Optimus · mono-jeu', 2.3], ['Optimus · famille', 2.1], ['Optimus · multi-jeux', 1.5, 1]] },
      { title: 'Score contre le juge (1 = victoire, 0,5 = égalité)', note: 'Hex et Gomoku : moteur à la main, 100 ms par coup. Dames : bot normal de multi.', unit: '', max: 1, rows: [['Hex · mono', 0.58], ['Hex · famille', 0.70, 1], ['Hex · multi', 0.62], ['Gomoku · mono', 0.10], ['Gomoku · multi', 0.17, 1], ['Dames normal · multi', 0.39], ['Dames normal · mono', 0.43], ['Dames normal · professeur', 0.93]] },
    ],
    duels: [
      ['Optimus (réseau seul)', 'Solveur exact Puissance 4', 'Puissance 4', '1,5 % de coups fautifs (multi)'],
      ['Optimus (réseau seul)', 'Moteur Hex à la main, 100 ms', 'Hex 7×7', 'score 0,62 (multi), 0,70 (famille)'],
      ['Optimus (réseau seul)', 'Moteur Gomoku à la main', 'Gomoku', 'score 0,17 (multi)'],
      ['Optimus (réseau seul)', 'Bot normal / difficile de multi', 'Dames', '0,39 / 0,20 (multi)'],
      ['Optimus (réseau seul)', 'Minimax parfait', 'Morpion', '0 défaite'],
    ],
    limits: ['Petits échantillons ; une seule taille de réseau (0,5 à 1,7 M) ; dernier pas sans sélection de point de contrôle.', 'Hex et Gomoku n’ont que 33 000 à 35 000 positions : ils sont limités par les données, pas par le réseau.', 'Réseau seul sans recherche ; juges Hex et Gomoku dépendants du temps mural (±0,1).'],
    src: ['GARRY-MODELE-UNIQUE-P0.md', 'GARRY-MODELE-UNIQUE-P1.md', 'GARRY-MODELE-UNIQUE-CADRAGE.md'],
  },
  {
    id: 'zero', short: 'Zéro', name: 'Garry Zéro', version: 'auto-apprentissage', page: 'modele-zero.html', scene: 'zero', hue: 206,
    role: 'L’élève sans professeur',
    tagline: 'Il joue contre lui-même. Aucune partie humaine, aucun coup imité.',
    summary: 'Zéro apprend par auto-jeu : une recherche arborescente (MCTS) guidée par un réseau politique-valeur, qui s’améliore en jouant. Au Puissance 4, il égale en une heure le professeur de niveau 10 sans l’avoir jamais vu.',
    stats: [{ v: 28600, l: 'parties d’auto-jeu (C4)' }, { v: 304300, l: 'paramètres (C4)' }, { v: 149, l: 'itérations' }, { v: 100, l: 'simulations / coup' }],
    system: [
      ['Auto-jeu', 'Le réseau joue contre lui-même, chaque coup choisi par une recherche de 100 simulations.'],
      ['Cibles', 'Politique = visites de la recherche ; valeur = résultat final de la partie.'],
      ['Apprentissage', 'Le réseau est entraîné sur ces parties, puis rejoue : la boucle s’auto-amplifie.'],
      ['Arène', 'Toutes les 10 itérations : duels contre le hasard, le professeur et Garry.'],
      ['Moteur de règles', 'Bitboards (C4) et moteur C++ pour le Go, vérifiés identiques aux règles de Garry.'],
    ],
    args: [
      ['Égale le professeur sans professeur', 'Puissance 4 : 0,500 contre le niveau 10 (43 V, 14 N, 43 D sur 100 parties).', 'ok'],
      ['Reste sous Garry 0.6.0', '0,425 contre Garry niveau 10 (37-11-52), qui combine réseau et alpha-bêta profond.', 'ok'],
      ['Go 9×9 : 20/20 contre Garry niveaux 1 et 4', 'Cela mesure surtout la faiblesse du Go de Garry, pas la force réelle de Zéro.', 'low'],
      ['Première lecture à 100 % : artefact', 'Réseau et professeur déterministes → parties répétées. Corrigé avec des ouvertures aléatoires.', 'ok'],
    ],
    bench: [
      { title: 'Zéro Puissance 4, 100 parties avec ouvertures aléatoires', note: 'Camps échangés par paire de parties. Score = victoires + moitié des nuls.', unit: '', max: 1, rows: [['contre le hasard', 1.0, 1], ['contre le professeur niveau 10', 0.5], ['contre Garry 0.6.0 niveau 10', 0.425]] },
    ],
    duels: [
      ['Zéro C4 (it. 149)', 'Hasard', 'Puissance 4', '100 V · 0 N · 0 D'],
      ['Zéro C4 (it. 149)', 'Professeur niveau 10', 'Puissance 4', '43 V · 14 N · 43 D'],
      ['Zéro C4 (it. 149)', 'Garry 0.6.0 niveau 10', 'Puissance 4', '37 V · 11 N · 52 D'],
      ['Zéro Go 9×9', 'Garry niveaux 1 et 4', 'Go 9×9', '20/20 à chaque point de contrôle'],
    ],
    limits: ['Une graine, une session par jeu.', 'Go : pas de test contre COSUMI (moteur indépendant) ; score de surface sans retrait de pierres mortes.', 'Nuls et ouvertures aléatoires peuvent déséquilibrer des parties (compensé par l’échange des camps).'],
    src: ['entrainements-garry-zero-2026-10-19.md'],
  },
  {
    id: 'maths', short: 'Maths', name: 'Maths', version: 'vague 1', page: 'modele-maths.html', scene: 'maths', hue: 248,
    role: 'Le réseau qui calcule pas à pas',
    tagline: 'Un Transformer de zéro, qui écrit l’étape suivante d’un calcul. Rien de plus.',
    summary: 'Un Transformer décodeur de 812 416 paramètres reçoit un état de calcul et écrit l’étape suivante (une opération à la fois). Un évaluateur indépendant vérifie chaque étape. Sur les six niveaux du test, tous les problèmes sont résolus ; hors distribution, il échoue.',
    stats: [{ v: 812416, l: 'paramètres' }, { v: 6, l: 'niveaux' }, { v: 125000, l: 'pas cumulés (recette D)' }, { v: 2184, l: 'problèmes de test' }],
    system: [
      ['État', 'Une expression partiellement calculée, ex. « 3 + 4 × 2 ».'],
      ['Étape', 'Le réseau écrit l’état suivant : « 3 + 8 ».'],
      ['Vérification', 'Un évaluateur indépendant juge chaque étape et le résultat final.'],
      ['Boucle', 'On rejoue jusqu’au résultat. Un problème est résolu si toutes les étapes sont valides.'],
      ['Recettes A à D', 'Plages élargies, opérandes négatifs, produits à deux chiffres, diviseurs jusqu’à 99.'],
    ],
    args: [
      ['Problème résolu : 1,000 sur 6 niveaux', '500/500 en N1, N4, N5, N6 ; 118/118 en N2 ; 66/66 en N3.', 'ok'],
      ['Étape exacte ≥ 0,998', 'Une faute sur 806 états en N1, deux sur 1 000 en N5.', 'ok'],
      ['N2 et N3 : preuve faible', 'Seulement 118 et 66 états de test : le majorant d’échec à 95 % est 2,5 % et 4,5 %.', 'mid'],
      ['Généralisation', 'Nombres à 4 chiffres : ~0 %. Le test a été regardé plusieurs fois : un banc neuf est nécessaire.', 'low'],
    ],
    bench: [
      { title: 'Problème résolu par niveau (test, recette D)', note: 'Majorant à 95 % du taux d’échec en légende : N2 2,5 %, N3 4,5 %, autres 0,6 %.', unit: '', max: 1, rows: [['N1 · + et −', 1.0, 1], ['N2 · multiplications', 1.0, 1], ['N3 · divisions exactes', 1.0, 1], ['N4 · priorités', 1.0, 1], ['N5 · parenthèses', 1.0, 1], ['N6 · équations', 1.0, 1]] },
      { title: 'Validation moyenne au fil des recettes', note: 'Réglages faits sur la validation seulement.', unit: '', max: 1, min: 0.97, rows: [['v1 · plat', 0.982], ['A · poids + plages', 0.9988], ['B · affinage N1', 0.9992], ['C · négatifs, 2 chiffres', 0.9997], ['D · taux plus doux', 0.9997, 1]] },
    ],
    duels: [['Maths recette-D', 'Évaluateur indépendant', 'Calcul pas à pas', '2 184 problèmes de test, tous résolus']],
    limits: ['Une seule trajectoire de graines pour le modèle final.', 'Hors distribution (nombres à 4 chiffres) : ~0 %.', 'Suite décidée : vague 2 (exposants, fractions, racines), extrapolation, puis carte « Maths en direct ».'],
    src: ['maths-protocole.md', 'maths-vague1-fin.md', 'maths-protocole-vague2.md'],
  },
  {
    id: 'loop', short: 'Loop', name: 'Loop', version: 'cœur récurrent', page: 'modele-loop.html', scene: 'loop', hue: 196,
    role: 'Le réseau qui réfléchit',
    tagline: 'Les mêmes poids, repassés encore et encore : plus c’est dur, plus il pense longtemps.',
    summary: 'Loop est un bloc d’attention limité aux cases voisines, repassé plusieurs fois avec les mêmes poids, entraîné de zéro sur des problèmes à solution unique. Il décide seul du nombre de passes en vérifiant sa grille, et le même modèle sait résoudre sudokus et colorations de graphes.',
    stats: [{ v: 53254, l: 'paramètres' }, { v: 32, l: 'passes max' }, { v: 2, l: 'familles de problèmes' }, { v: 40000, l: 'sudokus d’entraînement' }],
    system: [
      ['Grille', 'Chaque case regarde ses voisines (ligne, colonne, bloc ou arêtes du graphe).'],
      ['Récurrence', 'Le même bloc est appliqué N fois ; chaque passe affine la grille.'],
      ['Supervision', 'Une perte à chaque passe sur les cases vides.'],
      ['Vérification', 'Un vérificateur exact arrête la réflexion à la première grille valide.'],
      ['Transfert', 'Pas d’embedding de position : seule la structure compte, d’où coloration de graphes.'],
    ],
    args: [
      ['Réfléchir plus aide', 'Sudoku dur (plus de vides qu’à l’entraînement) : 0,260 à 4 passes, 0,749 à 8, 0,841 à 32.', 'ok'],
      ['La récurrence est le levier', 'Une seule passe : 0,000 au dur. Un non-lié à 8 blocs (403 142 paramètres) fait 0,735, moins que Loop.', 'ok'],
      ['Un modèle pour deux familles', 'SC égale les deux spécialistes (sudoku dur 0,94, coloration 0,99).', 'mid'],
      ['Durée de réflexion', '1,8 passe (facile), 3,0 (moyen), 6,0 (dur) avant la première grille valide.', 'ok'],
    ],
    bench: [
      { title: 'Sudoku 6×6 dur : exactitude selon les passes à l’inférence', note: 'Grille entière valide, moyenne de 2 graines. Jamais vu à l’entraînement.', unit: '', max: 1, rows: [['Loop · 4 passes', 0.26], ['Loop · 8 passes', 0.749], ['Loop · 16 passes', 0.827], ['Loop · 32 passes', 0.841], ['Loop-16 · 32 passes', 0.893, 1], ['Non lié · 8 blocs', 0.735], ['Une passe', 0.0]] },
      { title: 'Transfert : un modèle, six tests (32 passes)', note: 'S = sudoku seul, C = coloration seule, SC = les deux.', unit: '', max: 1, rows: [['SC · sudoku dur', 0.94, 1], ['SC · coloration', 0.99, 1], ['SC · grands graphes', 0.95, 1], ['SC · 5 couleurs', 0.69, 1], ['S · coloration', 0.51], ['C · sudoku dur', 0.0]] },
    ],
    duels: [['Loop-16', 'Vérificateur exact', 'Sudoku 6×6 dur', '0,893 grilles valides (32 passes)'], ['Loop SC', 'Vérificateur exact', 'Coloration 5 couleurs', '0,69 (couleurs jamais vues)']],
    limits: ['Sudoku 6×6 et graphes de taille modeste ; pas de sudoku 9×9.', 'Deux graines par résultat.'],
    src: ['loop-sudoku6-resultats.md', 'loop-transfert-resultats.md'],
  },
  {
    id: 'graine', short: 'Graine', name: 'Graine', version: 'croissance et élagage', page: 'modele-graine.html', scene: 'graine', hue: 214,
    role: 'L’expérience qui pousse',
    tagline: 'Un réseau qui commence à 2 + 2 neurones, en gagne, en perd. Verdict : le fixe fait mieux.',
    summary: 'Graine fait pousser et élaguer un réseau pendant l’entraînement. L’expérience compare trois règles à des réseaux fixes de même taille finale sur trois jeux. Le résultat est négatif, et c’est une réponse utile.',
    stats: [{ v: 3, l: 'règles de croissance' }, { v: 3, l: 'jeux' }, { v: 3, l: 'graines' }, { v: 3000, l: 'pas' }],
    system: [
      ['Départ', 'Deux couches de 2 neurones.'],
      ['Croissance', 'Règle A : +2 si la validation gagne < 3 % sur deux évaluations. B : < 6 %. C : comme B.'],
      ['Élagage', 'A tous les 400 pas ; B après 60 % des pas ; C jamais.'],
      ['Témoin', 'Un réseau fixe de même taille finale, même graine, même budget.'],
      ['Mesure', 'Accord avec le professeur sur positions de test jamais vues.'],
    ],
    args: [
      ['À taille égale, le fixe gagne', 'Graine perd de 1 à 6 points d’accord sur morpion et Nim.', 'ok'],
      ['Aucun réseau plus petit trouvé', 'Graine ne trouve ni plus petit ni plus précis que ce qu’une simple recherche de taille donnerait.', 'ok'],
      ['Puissance 4', 'Inconclusif : 0,35 à 0,39 pour toutes les tailles (professeur borné).', 'low'],
    ],
    bench: [
      { title: 'Morpion : Graine contre un réseau fixe de même taille', note: 'Accord de test, moyenne de 3 graines.', unit: '', max: 1, min: 0.7, rows: [['Graine A · 206 paramètres', 0.812], ['Fixe · même taille', 0.873, 1], ['Graine B · 546', 0.924], ['Fixe · même taille', 0.939, 1], ['Graine C · 1 900', 0.94], ['Fixe · même taille', 0.981, 1]] },
      { title: 'Nim : Graine contre un réseau fixe de même taille', note: 'Accord de test, moyenne de 3 graines.', unit: '', max: 1, min: 0.6, rows: [['Graine A · 687', 0.711], ['Fixe · même taille', 0.787, 1], ['Graine B · 1 632', 0.911], ['Fixe · même taille', 0.92, 1], ['Graine C · 2 831', 0.941], ['Fixe · même taille', 0.961, 1]] },
    ],
    duels: [['Graine A / B / C', 'Réseau fixe de même taille', 'Morpion, Nim, Puissance 4', 'le fixe égale ou bat Graine']],
    limits: ['Trois jeux seulement, réseaux minuscules.', 'Les neurones ajoutés en cours de route sont moins bien appris que ceux d’un réseau entraîné d’un bloc.'],
    src: ['graine-resultats.md'],
  },
  {
    id: 'moteurs', short: 'Moteurs', name: 'Moteurs à la main', version: 'Gomoku · Hex · solveur', page: 'modele-moteurs.html', scene: 'moteurs', hue: 262,
    role: 'Les professeurs et les juges',
    tagline: 'Pas d’entraînement : des tables de motifs, des ponts, une recherche. Ils enseignent et ils jugent.',
    summary: 'Gomoku, Hex et Puissance 4 ont des moteurs écrits à la main, sans aucun entraînement. Ils servent de professeurs (les positions et les coups) et de juges indépendants (le réseau seul les affronte). Ils sont aussi un adversaire fort dans l’arène.',
    stats: [{ v: 96, l: 'parties Gomoku mesurées' }, { v: 384, l: 'parties Hex mesurées' }, { v: 0, l: 'défaite au Gomoku' }, { v: 51194, l: 'étiquettes exactes C4' }],
    system: [
      ['Gomoku', 'Table de motifs sur 11 cases, alpha-bêta itératif, défense forcée, doubles menaces, extension VCF.'],
      ['Hex', 'Distance de connexion avec ponts et bords virtuels ; 4 Dijkstra par nœud ; faisceau étroit.'],
      ['Puissance 4', 'Solveur exact (C++), livre d’ouverture jusqu’au 12e coup, joueur parfait en TypeScript.'],
      ['Rôle de professeur', 'Les anciens planificateurs restent figés pour que les accords restent comparables.'],
      ['Rôle de juge', 'Le réseau seul joue 100 ms par coup contre ces moteurs.'],
    ],
    args: [
      ['Gomoku : 0,938 contre l’ancien planificateur', '0 défaite sur 96 parties, 200 ms et 100 000 nœuds par coup, camps échangés.', 'ok'],
      ['Hex : ≈ 0,75 sur 384 parties', 'Les ponts, le terme de centre et le faisceau étroit sont les vrais leviers.', 'ok'],
      ['Aucun adversaire tiers', 'Mesuré contre l’ancien planificateur et contre lui-même seulement ; pas un classement Elo.', 'low'],
    ],
    bench: [
      { title: 'Nouveau moteur contre l’ancien planificateur', note: 'Duels à budget égal, camps échangés.', unit: '', max: 1, rows: [['Gomoku · 96 parties', 0.938, 1], ['Hex · 384 parties', 0.75, 1]] },
      { title: 'Hex : contribution de chaque idée (score contre la version complète)', note: 'Plus c’est bas sans l’idée, plus elle compte.', unit: '', max: 1, rows: [['sans ponts', 0.31], ['sans terme de centre', 0.08], ['faisceau large (au lieu d’étroit)', 0.24]] },
    ],
    duels: [['Moteur Gomoku', 'Ancien planificateur', 'Gomoku', '0,938 · 0 défaite sur 96'], ['Moteur Hex', 'Ancien planificateur', 'Hex 7×7', '≈ 0,75 sur 384'], ['Joueur parfait C4', 'Solveur exact', 'Puissance 4', '0 % de coups fautifs']],
    limits: ['Pas de port Python : le navigateur et Python ne choisissent plus les mêmes coups à ces deux jeux.', 'Ouvertures Swap2 du Gomoku non améliorées.', 'Nuls du Gomoku : parties arrêtées à 260 coups.'],
    src: ['GARRY-A-LA-MAIN-GOMOKU-HEX.md', 'GARRY-MULTI-PROGRAMME.md'],
  },
];

// Carte des duels : nœuds = modèles, juges et références ; arêtes = duels réellement mesurés.
export const NODES = [
  { id: 'garry', label: 'Garry 0.6.0', kind: 'model' },
  { id: 'optimus', label: 'Garry Optimus 0.1', kind: 'model' },
  { id: 'zero', label: 'Garry Zéro', kind: 'model' },
  { id: 'moteurs', label: 'Moteurs à la main', kind: 'model' },
  { id: 'solver', label: 'Solveur exact C4', kind: 'judge' },
  { id: 'prof', label: 'Professeur niv. 10', kind: 'judge' },
  { id: 'dames', label: 'Bot de dames (multi)', kind: 'judge' },
  { id: 'old', label: 'Ancien planificateur', kind: 'judge' },
  { id: 'cosumi', label: 'COSUMI (site réel)', kind: 'judge' },
  { id: 'random', label: 'Hasard', kind: 'judge' },
];
export const EDGES = [
  ['zero', 'prof', 'Puissance 4', '0,500 (43-14-43)'],
  ['zero', 'garry', 'Puissance 4', '0,425 (37-11-52)'],
  ['zero', 'random', 'Puissance 4', '1,000'],
  ['garry', 'solver', 'Puissance 4', '2,4 % de coups fautifs'],
  ['optimus', 'solver', 'Puissance 4', '1,5 % de coups fautifs'],
  ['optimus', 'moteurs', 'Hex · Gomoku', 'Hex 0,62 · Gomoku 0,17'],
  ['optimus', 'dames', 'Dames', '0,39 normal · 0,20 difficile'],
  ['moteurs', 'old', 'Gomoku · Hex', '0,938 · ≈ 0,75'],
  ['garry', 'cosumi', 'Go 19×19', 'défaite de 285,5 points'],
];

// Benchmark transversal : Puissance 4, le seul jeu où tous les modèles ont une mesure comparable.
export const C4 = {
  title: 'Puissance 4 : part de coups fautifs face au solveur exact (plus bas = mieux)',
  note: 'Seul jeu mesuré de la même façon pour tous les modèles (P0 et P1). Optimus : réseau seul, moyenne de 2 graines.',
  max: 8,
  rows: [['Hasard', 7.3], ['Garry 0.6.0 niveau 10', 2.4], ['Optimus · mono-jeu', 2.3], ['Optimus · famille', 2.1], ['Garry Zéro', 1.8], ['Professeur niveau 10', 1.6], ['Optimus · multi-jeux', 1.5, 1], ['Solveur exact', 0.0]],
};

// Entraînement d'Optimus : alimenté par training-lab/models/unified/optimus/status.json si disponible.
export const OPTIMUS_STATUS = '/optimus-status.json';

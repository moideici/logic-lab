"""Constantes communes. Plateau commun 15 × 15 (taille du Gomoku) ; les autres jeux y sont centrés.

Plans d'entrée (8) :
  0 case du plateau (masque), 1 mes pierres/pions, 2 pierres/pions adverses, 3 mes dames, 4 dames adverses,
  5 coups légaux (case d'arrivée), 6 bords que je relie (Hex), 7 bords de l'adversaire (Hex).
Vecteur annexe (8) : 0 échange disponible (Hex), 1-5 phase du Swap2 (Gomoku), 6 je joue noir (Gomoku), 7 compteur de coups de dame sans prise.
Actions : jeux de pose = case du plateau commun (0-224) + 3 emplacements spéciaux (225 échange, 226 choisir noir, 227 choisir blanc) ;
dames = indice départ × 32 + arrivée (1 024).
"""
CANVAS = 15
PLANES = 8
EXTRA = 8
GAMES = ("tictactoe", "connect4", "hex", "gomoku", "dames")
GAME_ID = {g: i for i, g in enumerate(GAMES)}
CELLS = CANVAS * CANVAS
SWAP, CHOOSE_BLACK, CHOOSE_WHITE = 225, 226, 227
PLACEMENT_ACTIONS = 228
N_ACTIONS = {"tictactoe": PLACEMENT_ACTIONS, "connect4": PLACEMENT_ACTIONS, "hex": PLACEMENT_ACTIONS, "gomoku": PLACEMENT_ACTIONS, "dames": 1024}
MAX_ACTIONS = max(N_ACTIONS.values())
DIMS = {"tictactoe": (3, 3), "connect4": (6, 7), "hex": (7, 7), "gomoku": (15, 15), "dames": (8, 8)}

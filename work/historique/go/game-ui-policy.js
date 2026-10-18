const multiplayer=new Set(['tictactoe','connect4','reversi','nim','draughts','breakthrough','hex','gomoku','go']);
const strategy=[['balanced','Équilibré'],['aggressive','Offensif'],['defensive','Prudent'],['greedy','Opportuniste'],['positional','Positionnel'],['exploratory','Explorateur']];
const ties={
 tictactoe:[['balanced','Équilibré'],['defensive','Privilégier le centre'],['aggressive','Privilégier les ailes']],
 connect4:[['balanced','Équilibré'],['defensive','Privilégier le centre'],['aggressive','Privilégier les ailes']],
 '2048':[['balanced','Équilibré'],['defensive','Privilégier l’espace libre'],['aggressive','Privilégier les fusions']],
 sudoku:[['balanced','Équilibré'],['defensive','Prudent · cases contraintes'],['aggressive','Offensif · cases ouvertes']],
 minesweeper:[['balanced','Équilibré'],['defensive','Près des indices'],['aggressive','Loin des indices']],
 sliding_puzzle:[['balanced','Équilibré'],['greedy','Réduire la distance'],['positional','Bien placer les tuiles'],['defensive','Préserver les tuiles placées']],
 nim:[],lightsout:[],
};
export function gameUiPolicy({game,mode='watch',planning=true,level=10,levelTwo=10}){
 const multi=multiplayer.has(game),manualSolo=!multi&&mode==='human',duel=multi&&mode==='watch';
 let styles=ties[game]??strategy;
 const fixedConnect=game==='connect4'&&planning&&level===10&&(!duel||levelTwo===10);
 const probabilityPuzzle=['sudoku','sliding_puzzle'].includes(game)&&planning&&level>0&&level<10;
 const networkWithoutBias=!planning&&!ties[game];
 if(fixedConnect||probabilityPuzzle||networkWithoutBias)styles=[];
 const styleHint=!styles.length?(fixedConnect?'Au niveau 10, la recherche de Puissance 4 choisit directement son coup ; aucun style n’intervient.':probabilityPuzzle?'Aux niveaux 1 à 9, ce puzzle varie la fréquence des meilleurs coups ; le style n’intervient pas.':networkWithoutBias?'Le réseau seul ne prend pas en compte le style dans ce jeu.':'Aucun style ne modifie les décisions de ce jeu. Le niveau et la planification restent réglables.'):
 !planning?'Réseau seul : le style départage seulement des scores appris égaux. Il peut donc ne rien changer.':
 game==='connect4'?'Le style départage les coups aux niveaux 0 à 9. Au niveau 10, la recherche choisit directement son coup.':
 ties[game]?'Le style départage les coups de même qualité évaluée. Il peut ne rien changer lorsqu’un coup est préférable.':
 'Le style influe sur l’évaluation stratégique. Les issues prouvées restent prioritaires ; des coups peuvent rester identiques.';
 return {multi,manualSolo,duel,showAi:!manualSolo,showStyles:!manualSolo&&styles.length>0,styles,styleHint,
  humanLabel:multi?'Moi contre l’IA':['sudoku','sliding_puzzle','lightsout'].includes(game)?'Moi · résoudre l’énigme':'Moi · jouer en solo',
  levelTitle:duel?'Niveau IA 1':multi?'Niveau de l’IA':'Niveau de l’IA',
 };
}

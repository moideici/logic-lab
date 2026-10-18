exec((__import__('pathlib').Path(__file__).parent/'integrate.py').read_text(encoding='utf-8').split('# Freeze the last')[0])
edit('examples/train_new_games.py',[("current['optimal_choice_rate']>=best_metric['optimal_choice_rate'] and current['soft_cross_entropy']<before['soft_cross_entropy']", "(current['optimal_choice_rate'],-current['soft_cross_entropy'])>(best_metric['optimal_choice_rate'],-best_metric['soft_cross_entropy'])")])
edit('tests/web.test.mjs',[
("for(const name of Object.keys(NAMES))", "for(const name of LEGACY_GAMES)"),
("observations=Object.keys(NAMES).map", "observations=LEGACY_GAMES.map"),
("from logic_arena.neural import NeuralPolicy,SPECS,encode\\ns=", "from logic_arena.neural import NeuralPolicy,SPECS,encode\\nfrom logic_arena.migration import LEGACY_GAMES\\ns="),
("for g in SPECS}\\na=", "for g in LEGACY_GAMES}\\na=")])
edit('tests/levels.test.mjs',[("assert(compareQuality(a.info.quality,b.info.quality)<=0,game);", "if(a.info.depth===b.info.depth)assert(compareQuality(a.info.quality,b.info.quality)<=0,game); /* Separate time-limited searches can finish at different depths. */")])
print('Training selection and historical tests corrected.')

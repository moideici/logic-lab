#!/bin/sh
# Relance l'expérience Graine sur les trois jeux (3 graines, 3000 pas).
cd "$(dirname "$0")/.."
for g in tictactoe nim connect4; do
  python training-lab/experience_graine.py --game $g --steps 3000 --seeds 3 > training-lab/results/journal-$g.txt 2>&1
done
echo FINI > training-lab/results/experiences.fini

#!/bin/sh
# Garry Optimus 0.1 : donnees Hex/Gomoku x6, fusion, entrainement multi-jeux long, mesure par les juges.
# Reprise possible (relancer). Statut publie dans web/optimus-status.json (page du Lab). Depuis projets/garry.
PY=../../work/text-env/Scripts/python.exe
O=training-lab/models/unified/optimus
S="$PY training-lab/optimus_status.py"
mkdir -p $O
STEPS=${STEPS:-90000}
while [ ! -f training-lab/data/unified/gomoku-2.npz ]; do $S 1 "generation de donnees Hex/Gomoku supplementaires"; sleep 30; done
$S 1 "fusion des donnees"
$PY training-lab/unified_merge_data.py --games hex,gomoku --seeds 1,2 --tag m >> $O/merge.log 2>&1
$S 1 "entrainement multi-jeux : $STEPS pas (log: $O/multi-0.log)"
( while [ ! -f $O/multi-0/report.json ]; do L=$(tail -1 $O/multi-0.log 2>/dev/null | sed 's/.*step/pas/' | cut -c1-120); $S 1 "entrainement : $L"; sleep 60; done ) &
$PY training-lab/unified_train.py --arm multi --seed 0 --steps $STEPS --tag m --out $O >> $O/multi-0.log 2>&1
$S 1 "mesure par les juges independants"
$PY training-lab/unified_eval.py --dir $O/multi-0 >> $O/eval.log 2>&1
$S 0 "termine : voir $O/eval.log"

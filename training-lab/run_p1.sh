#!/bin/sh
# Pilote P1 : 3 bras x 2 graines, UN job à la fois, reprise possible (relancer le script). Pause : créer training-lab/PAUSE ; reprise : le supprimer.
PY=../../work/text-env/Scripts/python.exe
O=training-lab/models/unified/p1
mkdir -p $O
for job in "multi 0" "mono 0" "family 0" "multi 1" "mono 1" "family 1"; do
  set -- $job
  [ -f $O/$1-$2/report.json ] && continue
  $PY training-lab/unified_train.py --arm $1 --seed $2 --steps 30000 --out $O >> $O/$1-$2.log 2>&1
done

#!/bin/sh
# usage : bench/run-parallel.sh <script.mjs> <procs> <games-per-proc> [extra args...]
d=$(mktemp -d); script=$1; procs=$2; games=$3; shift 3
for i in $(seq 1 $procs); do node $script --games $games --seed $i "$@" > $d/duel_$i.json & done; wait
cat $d/duel_*.json | node -e "let w=0,d=0,l=0,n=0;require('fs').readFileSync(0,'utf8').trim().split('\n').forEach(x=>{const j=JSON.parse(x);w+=j.wins;d+=j.draws;l+=j.losses;n+=j.games});console.log(JSON.stringify({games:n,wins:w,draws:d,losses:l,score:((w+d/2)/n).toFixed(3)}))"
rm -rf $d

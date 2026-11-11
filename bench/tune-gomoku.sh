#!/bin/sh
# Compare des variantes de PARAMS (A) aux défauts (B=engine) : 96 parties chacune.
run(){ echo "== $1"; bench/run-parallel.sh bench/gomoku-duel.mjs 12 8 --b engine --params "$1"; }
run '{"breadth":[30,16,12,10,8,8,6,6,5,5,5,5]}'
run '{"breadth":[12,8,6,5,4,4,3,3,3,3,3,3]}'
run '{"opp1":1.25}'
run '{"opp1":0.75}'
run '{"own2":0.15}'
run '{"own2":0.6}'
run '{"vcfDepth":6}'
run '{"vcfDepth":24}'

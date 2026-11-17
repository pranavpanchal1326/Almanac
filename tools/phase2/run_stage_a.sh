#!/usr/bin/env bash
# Stage A runs in the order the amendments fix. Safe to rerun at any time: finished runs are
# skipped and an interrupted run resumes from its last validation check.
#
# Usage: bash tools/phase2/run_stage_a.sh [a1|a2]        (from the repository root; default a2)
#        STOP_AFTER=6 bash tools/phase2/run_stage_a.sh   (stop the current run after 6 checks)
#
# a1: amendment 1 (only B5 is run; model M under amendment 1 was stopped before it started).
# a2: amendment 2: B5, then model M with schedules a and b. Seeds 2 and 3 follow the choice.
set -uo pipefail
RUNS=${RUNS:-D:/almanac-data/runs}
family=${1:-a2}
case "$family" in
  a1) configs=(stage_a_b5) ;;
  a2) configs=(stage_a2_b5 stage_a2_m_a stage_a2_m_b) ;;
  *) echo "unknown family $family"; exit 2 ;;
esac
extra=()
[ -n "${STOP_AFTER:-}" ] && extra=(--stop-after "$STOP_AFTER")
for c in "${configs[@]}"; do
  out="$RUNS/${c}_s1"
  if [ -f "$out/last.pt" ]; then echo "$c: finished"; continue; fi
  echo "$c: running ($(date -u +%FT%TZ))"
  .venv/Scripts/python -u -W ignore tools/phase2/train.py "configs/model/$c.json" --out "$out" "${extra[@]}" >> "$RUNS/${c}_s1.out" 2>&1
  status=$?
  if [ $status -ne 0 ]; then echo "$c: failed with status $status; see $RUNS/${c}_s1.out"; exit $status; fi
  if [ ! -f "$out/last.pt" ]; then echo "$c: paused; run this script again to continue"; exit 0; fi
  echo "$c: done ($(date -u +%FT%TZ))"
done

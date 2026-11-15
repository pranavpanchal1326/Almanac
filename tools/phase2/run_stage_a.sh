#!/usr/bin/env bash
# Stage A runs in the order amendment 1 fixes: B5 first, then model M with schedules a and b.
# Safe to rerun at any time: finished runs are skipped and an interrupted run resumes from its last
# validation check. Seeds 2 and 3 are added once the schedule is chosen.
#
# Usage: bash tools/phase2/run_stage_a.sh            (from the repository root)
#        STOP_AFTER=6 bash tools/phase2/run_stage_a.sh   (stop the current run after 6 checks, about an hour)
set -uo pipefail
RUNS=${RUNS:-D:/almanac-data/runs}
extra=()
[ -n "${STOP_AFTER:-}" ] && extra=(--stop-after "$STOP_AFTER")
for c in stage_a_b5 stage_a_m_a stage_a_m_b; do
  out="$RUNS/${c}_s1"
  if [ -f "$out/last.pt" ]; then echo "$c: finished"; continue; fi
  echo "$c: running ($(date -u +%FT%TZ))"
  .venv/Scripts/python -u -W ignore tools/phase2/train.py "configs/model/$c.json" --out "$out" "${extra[@]}" >> "$RUNS/${c}_s1.out" 2>&1
  status=$?
  if [ $status -ne 0 ]; then echo "$c: failed with status $status; see $RUNS/${c}_s1.out"; exit $status; fi
  if [ ! -f "$out/last.pt" ]; then echo "$c: paused; run this script again to continue"; exit 0; fi
  echo "$c: done ($(date -u +%FT%TZ))"
done

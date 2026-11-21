#!/usr/bin/env bash
# Stage A runs in the order the amendments fix. Safe to rerun at any time: finished runs are
# skipped and an interrupted run resumes from its last validation check.
#
# Usage: bash tools/phase2/run_stage_a.sh [a1|a2]              (from the repository root; default a2)
#        bash tools/phase2/run_stage_a.sh list CONFIG...       (named configs, e.g. seeds 2 and 3)
#        STOP_AFTER=6 bash tools/phase2/run_stage_a.sh         (stop the current run after 6 checks)
#
# a1: amendment 1 (only B5 is run; model M under amendment 1 was stopped before it started).
# a2: amendment 2: B5, then model M with schedules a and b. Seeds 2 and 3 follow the choice.
#
# Supervision. Each run is watched: if the training process fails (for example CUDA out of memory
# because another program took GPU memory) or its heartbeat file stops changing for STALL seconds
# (a hang), the process tree is stopped and the run resumes from its last check, up to
# MAX_RESTARTS times. Resuming is exact, so a restart changes no result; it costs the steps since
# the last check. Time the machine spends asleep is not counted as a stall. Every event is
# appended to $RUNS/queue.log.
set -uo pipefail
RUNS=${RUNS:-D:/almanac-data/runs}
STALL=${STALL:-900}
MAX_RESTARTS=${MAX_RESTARTS:-6}
POLL=${POLL:-30}
TRAIN=${TRAIN:-tools/phase2/train.py}
family=${1:-a2}
case "$family" in
  a1) configs=(stage_a_b5) ;;
  a2) configs=(stage_a2_b5 stage_a2_m_a stage_a2_m_b) ;;
  list) shift; configs=("$@") ;;
  *) echo "unknown family $family"; exit 2 ;;
esac
[ ${#configs[@]} -gt 0 ] || { echo "no configurations given"; exit 2; }
extra=()
[ -n "${STOP_AFTER:-}" ] && extra=(--stop-after "$STOP_AFTER")
# shellcheck disable=SC2206  # TRAIN_ARGS is a list of flags, e.g. "--dry --cpu" for tests
[ -n "${TRAIN_ARGS:-}" ] && extra+=($TRAIN_ARGS)

say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$RUNS/queue.log"; }

# Stop a process and its children (the venv python.exe is a launcher with a child interpreter).
stop_tree() {
  local winpid
  winpid=$(cat "/proc/$1/winpid" 2>/dev/null) && taskkill //F //T //PID "$winpid" > /dev/null 2>&1
  kill -9 "$1" 2> /dev/null
}

# Seconds since the run last showed life: its heartbeat, or the launch if that is newer.
quiet_for() {
  local hb now
  now=$(date +%s)
  hb=$(stat -c %Y "$1/heartbeat" 2> /dev/null || echo 0)
  [ "$hb" -lt "$2" ] && hb=$2
  echo $((now - hb))
}

run_one() {
  local c=$1 out=$2 restarts=0 pid status code started age prev now
  while :; do
    if [ -f "$out/last.pt" ]; then say "$c: finished"; return 0; fi
    say "$c: running"
    started=$(date +%s)
    .venv/Scripts/python -u -W ignore "$TRAIN" "configs/model/$c.json" --out "$out" "${extra[@]}" \
      >> "$RUNS/$(basename "$out").out" 2>&1 &
    pid=$!
    status=""
    prev=$(date +%s)
    while kill -0 "$pid" 2> /dev/null; do
      sleep "$POLL"
      # A poll that took far longer than POLL means the machine was asleep (standby), which pauses
      # training too; that time is not a hang, so the stall clock starts again from now.
      now=$(date +%s)
      if [ $((now - prev)) -gt $((POLL + 120)) ]; then
        say "$c: machine was suspended for about $((now - prev)) s; stall clock restarted"
        started=$now
      fi
      prev=$now
      age=$(quiet_for "$out" "$started")
      if [ "$age" -gt "$STALL" ] && kill -0 "$pid" 2> /dev/null; then
        say "$c: no heartbeat for ${age} s; stopping the hung process"
        stop_tree "$pid"
        status=124
      fi
    done
    wait "$pid" 2> /dev/null
    code=$?
    [ -z "$status" ] && status=$code
    if [ "$status" -eq 0 ]; then
      if [ -f "$out/last.pt" ]; then say "$c: done"; return 0; fi
      say "$c: paused; run this script again to continue"
      return 3
    fi
    restarts=$((restarts + 1))
    if [ "$restarts" -gt "$MAX_RESTARTS" ]; then
      say "$c: failed with status $status after $MAX_RESTARTS restarts; see $RUNS/$(basename "$out").out"
      return "$status"
    fi
    say "$c: failed with status $status; restart $restarts of $MAX_RESTARTS from the last check"
    sleep "${RESTART_WAIT:-60}"
  done
}

for c in "${configs[@]}"; do
  # Output folder: the config name with its seed suffix (seed 1 configs carry none).
  case "$c" in
    *_s[0-9]) out="$RUNS/$c" ;;
    *) out="$RUNS/${c}_s1" ;;
  esac
  run_one "$c" "$out"
  rc=$?
  [ $rc -eq 3 ] && exit 0
  [ $rc -ne 0 ] && exit $rc
done
exit 0

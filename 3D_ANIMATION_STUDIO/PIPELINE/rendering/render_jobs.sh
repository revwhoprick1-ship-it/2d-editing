#!/usr/bin/env bash
# Render a list of jobs of a video module (one Blender per job; finished frames are skipped).
#   PIPELINE/rendering/render_jobs.sh video002 RES SAMPLES OUTROOT [STEP] -- JOB ...
set -u
VIDEO=$1; RES=$2; SAMPLES=$3; OUTROOT=$4; STEP=${5:-1}; shift 5
cd "$(dirname "$0")/../.."
for S in "$@"; do
  [ "$S" = "--" ] && continue
  T0=$(date +%s)
  blender -b --factory-startup --python PIPELINE/rendering/render_shot.py -- --video "$VIDEO" --shot "$S" \
     --res "$RES" --samples "$SAMPLES" --step "$STEP" --out "$OUTROOT/$S" 2>&1 | grep --line-buffered -E "SHOT_DONE|Traceback|Error:|line [0-9]+,"
  echo "JOB $S $(( $(date +%s) - T0 ))s"
done
echo LANE_DONE

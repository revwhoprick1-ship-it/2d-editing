#!/usr/bin/env bash
# Render all (or listed) shots of a video sequentially.
#   PIPELINE/rendering/render_video.sh video001 RES SAMPLES STEP OUTROOT [SHOT ...]
set -u
VIDEO=$1; RES=$2; SAMPLES=$3; STEP=$4; OUTROOT=$5; shift 5
cd "$(dirname "$0")/../.."
SHOTS=${@:-$(python3 -c "import sys; sys.path.insert(0,'PIPELINE/blender_scripts/videos'); import ast,re; src=open('PIPELINE/blender_scripts/videos/${VIDEO}.py').read(); m=re.search(r'SHOTS = \{(.*?)\n\}', src, re.S); print(' '.join(re.findall(r\"'(SH\w+)'\", m.group(1))))")}
for S in $SHOTS; do
  blender -b --factory-startup --python PIPELINE/rendering/render_shot.py -- --video "$VIDEO" --shot "$S" \
     --res "$RES" --samples "$SAMPLES" --step "$STEP" --out "$OUTROOT/$S" 2>&1 | grep -E "FRAME|SHOT_DONE|Error|Traceback|line [0-9]+," 
done
echo ALL_DONE

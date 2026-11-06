#!/bin/bash
# Final render for VIDEO_001 + character deliverables, as two parallel CPU lanes.
cd /home/user/2d-editing/3D_ANIMATION_STUDIO
LOG=VIDEOS/VIDEO_001/render_logs; mkdir -p $LOG
(
  PIPELINE/rendering/render_video.sh video001 540x960 4 1 VIDEOS/VIDEO_001/frames SH01 SH02 SH03 SH04a SH04b SH05a SH05b SH06a SH06b SH07a > $LOG/laneA.txt 2>&1
  PIPELINE/rendering/render_video.sh animtest 540x960 4 1 CHARACTER/animations/anim_test/frames T01 > $LOG/animtest.txt 2>&1
  echo LANE_A_DONE >> $LOG/laneA.txt
) &
(
  PIPELINE/rendering/render_video.sh video001 540x960 4 1 VIDEOS/VIDEO_001/frames SH07b SH08 SH09a SH09b SH10 SH11a SH11b SH11c SH12a SH12b > $LOG/laneB.txt 2>&1
  blender -b CHARACTER/mascot_rig.blend --python PIPELINE/blender_scripts/render_character_sheets.py -- CHARACTER/reference_sheets > $LOG/sheets.txt 2>&1
  python3 PIPELINE/blender_scripts/compose_character_sheets.py >> $LOG/sheets.txt 2>&1
  echo LANE_B_DONE >> $LOG/laneB.txt
) &
wait

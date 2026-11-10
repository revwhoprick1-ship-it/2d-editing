# VIDEO_021 · My Mother Isn't Real (2dEDIT horror choice game, 63.3 s)

Export: `EXPORTS/VIDEO_021_My_Mother_Isnt_Real.mp4` (1080x1920, 30 fps, -14.1 LUFS, TP -1.9). Lore, answer and hidden details:
`VIDEOS/MOTHER_LORE.md` (never contradict).

Hook (frame 0): your hand on the forbidden basement doorknob, Mom far down the dark hallway; on "Sweetie" a hard cut puts her
right there. Then "My mom died two years ago. So who's been making my breakfast?" Narration (N) and dialogue (M/O/P) alternate.
Scares are instant and unannounced (no riser, no music drop): JS1 5 frames mid-word "love"; JS2 on "thirteen" (a hand grabs
your ankle); JS3 in the middle of the choice card. New SFX: scare_slam, scare_shriek, glitch_stab (+ house_night, kitchen_morning).
Voices: all new Qwen VoiceDesign refs (N narrator, M you, O Mom, P basement Mom); Q/X built from O with sox (voice_fx.py).
Sets: one fixed layout per place (hall: basement door right wall z 2.6-3.5, stairs from z 4, photos left, kitchen doorway at the end).

QA fixes: long-hair back-view puppet bug (skin crescent looked like a smile) fixed in flat.py; car wheel/clock placement; grab
hand redrawn; final framing; disk filled during export -> 311 broken frames redrawn; true peak -0.5 -> -1.9 (scare gains -2 dB).

# Narrator identity & free TTS system

## Engine: Kokoro‑82M (official `hexgrad/kokoro`, v0.9.4), run locally
* **Cost:** free. Runs on CPU (≈ real time or faster on this 4‑core VM). No API, no account, no credits, no usage limits.
* **Licence:** model weights **Apache‑2.0** (model card: *"Apache-licensed weights… can be deployed anywhere from production environments to personal projects"*). Voices ship in the same Apache repo. Commercial and monetised use is allowed. Keep the licence notice in `DOCUMENTATION/`.
* **Install:** `/opt/tools/tts312` (Python 3.12 venv: `torch` CPU wheel, `kokoro>=0.9.4`, `soundfile`, `espeak-ng` for OOV words). Model and voices are cached from Hugging Face.
* **Scripts:** `PIPELINE/tts/narrate.py` (script.json → per‑line WAVs, narration WAV, word and phoneme timings), `PIPELINE/tts/qc_narration.py` + `voice_qc.py` (ASR intelligibility, pacing, pitch movement, levels), `PIPELINE/tts/audition.py`.

## How the voice was chosen
I cannot listen to audio, so the audition used **objective proxies** plus Kokoro's published quality grades. Ten American‑English voices each read 4 lines (hook, science terms incl. "neutrophil", suspense, excitement):

| Voice | Kokoro grade (VOICES.md) | ASR WER | Words/s | Pitch range p5–p95 (semitones) |
|---|---|---|---|---|
| **af_heart** | **A** (flagship) | 0.000 | 2.61 | 9.2 |
| af_bella | A‑ | 0.000 | 2.42 | 7.7 |
| af_nicole | B‑ | 0.000 | 1.83 | 6.5 |
| am_michael | C+ | 0.000 | 2.29 | 10.1 |
| am_fenrir | C+ | 0.000 | 2.64 | 13.6 |
| am_puck | C+ | 0.000 | 2.65 | 11.4 |
| am_adam | F+ | 0.000 | 2.56 | 11.5 |
| am_eric | D | 0.015 | 2.74 | 12.7 |
| am_liam | D | 0.000 | 2.70 | 14.4 |
| am_onyx | D | 0.023 | 2.44 | 8.4 |

**Decision: `af_heart` is the permanent narrator.** It has the highest model quality grade (fewest artefacts, most natural), perfect intelligibility, healthy pace and good pitch movement. **Backup / male option: `am_fenrir`** (best grade among male voices, most pitch movement). The male voices' larger pitch ranges may partly be octave errors in the simple pitch tracker, so they are not treated as proof of better acting. Samples are in `AUDIO/narrator/auditions/` for a human listen. **Please audition them yourself. If you prefer a male narrator, change `"voice"` in the video's script.json; nothing else changes.**

## Expressive delivery (Kokoro has no emotion tokens)
Delivery is shaped per line with speed, punctuation (`?`, `!`, `...`), line chunking and scripted pauses (`DELIVERY` presets in narrate.py: hook, curious, calm, suspense, urgent, excited, dramatic, humour). Lines are generated separately so each gets its own pacing, then joined with designed silences.

## QC loop actually run for VIDEO_001
1. Generated all 12 lines. 2. Whisper (small.en, local) transcription → per‑line WER and mismatches. 3. Found **"riding" heard as "writing"** (flap‑T ambiguity) and **"valves" heard as "valve"** (s+s merge). 4. Rewrote those lines ("cushion under you", "the valves behind you slam shut") and slowed the hook from 3.93 to 3.83 words/s. 5. Regenerated only those lines. 6. All 12 lines now WER = 0 (`VIDEOS/VIDEO_001/audio/narration/qc_report.json`). Final narration: 56.5 s.

**Honest limitation:** naturalness and emotional fit were judged by proxies, not by ear. A human listen is the remaining QC step.

## Mascot's own voice (character dialogue, used in the animation test)
`am_puck` (C+, youthful, lively pitch). This is kept separate from the narrator so the two never get confused.

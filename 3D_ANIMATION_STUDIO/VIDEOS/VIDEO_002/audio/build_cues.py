#!/usr/bin/env python3
"""Build VIDEO_002's sound design: cues.json (every SFX timed to a narration word
or an animation frame) + the globe "popcorn" stems synced to the puff frames.

    /opt/tools/tts312/bin/python VIDEOS/VIDEO_002/audio/build_cues.py
    /opt/tools/tts312/bin/python PIPELINE/audio/mix.py VIDEOS/VIDEO_002/audio/cues.json

Times come from edit_video002.py (narration word times + the EDL's frame maps),
so re-timing the edit re-times the sound.
"""
import json
import os
import random
import sys

import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.dirname(HERE)
STUDIO = os.path.abspath(os.path.join(VID, '..', '..'))
sys.path.insert(0, VID)
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'audio'))
import edit_video002 as E  # noqa: E402
from dsp import SR, pan, from_db  # noqa: E402

FX = 'AUDIO/sound_effects/'
COM = FX + 'comedy/'
SEG = {i: s for i, s in enumerate(E.SEGMENTS)}


def seg_time(src, frame):
    """Video time at which segment `src` shows animation frame `frame` (linear map / f0)."""
    for s in E.SEGMENTS:
        if s.get('src') != src:
            continue
        if 'f0' in s:
            t = s['t0'] + (frame - s['f0']) / E.FPS
        else:
            (ta, fa), (tb, fb) = s['map'][0], s['map'][-1]
            if len(s['map']) > 2:
                for (t1, f1), (t2, f2) in zip(s['map'], s['map'][1:]):
                    if f1 <= frame <= f2 and f2 > f1:
                        (ta, fa), (tb, fb) = (t1, f1), (t2, f2)
                        break
            t = ta + (frame - fa) * (tb - ta) / (fb - fa)
        if s['t0'] - 1e-6 <= t <= s['t1'] + 1e-6:
            return round(t, 3)
    raise ValueError((src, frame))


def load(p):
    x, sr = sf.read(os.path.join(STUDIO, p), always_2d=True)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr, axis=0)
    return x.mean(1)


def pitch(x, ratio):
    n = int(len(x) / ratio)
    return np.interp(np.arange(n) * ratio, np.arange(len(x)), x)


def popcorn(events, out, seed):
    """events: [(t_rel, gain_db, pan)] -> stereo file of pitched tiny farts."""
    rng = np.random.default_rng(seed)
    src = [load(COM + 'fart_tiny_pfft.flac'), load(COM + 'fart_squeaker.flac')[:int(0.25 * SR)]]
    n = int((max(e[0] for e in events) + 0.8) * SR)
    buf = np.zeros((n, 2))
    for t, g, p in events:
        x = pitch(src[rng.integers(2)], rng.uniform(0.75, 1.9))
        x = x * np.hanning(len(x) * 2)[len(x):] ** 0.3          # short tail
        y = pan(x, p) * from_db(g)
        i = int(t * SR)
        buf[i:i + len(y)] += y[:n - i]
    buf /= np.max(np.abs(buf)) + 1e-9
    buf *= from_db(-3)
    sf.write(os.path.join(STUDIO, out), buf.astype(np.float32), SR, subtype='PCM_24')
    return out


def globe_events():
    """Replicates video002.build_globe_scene's puff schedule (random.Random(9))."""
    rnd = random.Random(9)
    pop, orbit = [], []
    for i in range(70):
        f = int(rnd.uniform(1, 30)) if i < 45 else int(rnd.uniform(36, 110))
        rnd.uniform(0.035, 0.06)
        rnd.randint(18, 40)
        (pop if i < 45 else orbit).append(f)
    return sorted(pop), sorted(orbit)


def main():
    rng = random.Random(5)
    pop, orbit = globe_events()
    t_pop0 = seg_time('GL_POP', 0)
    t_orb0 = seg_time('GL_ORBIT', 36)
    pop_file = popcorn([(f / 30, rng.uniform(-9, 0), rng.uniform(-0.8, 0.8)) for f in pop],
                       COM + 'v002_globe_popcorn.flac', 1)
    orb_file = popcorn([((f - 36) / 30, rng.uniform(-10, -2), rng.uniform(-0.8, 0.8)) for f in orbit],
                       COM + 'v002_globe_orbit.flac', 2)

    cues = []

    def c(t, name, gain, note, pan_=None, dur=None, fin=0.0, fout=0.0, bus='sfx', path=None):
        p = path or (COM + name + '.flac' if os.path.exists(os.path.join(STUDIO, COM + name + '.flac'))
                     else next(os.path.join('AUDIO', d) for d in [_lib()[name]]))
        d = dict(t=round(t, 3), file=p, gain=gain, bus=bus, note=note)
        if pan_ is not None:
            d['pan'] = pan_
        if dur:
            d['dur'] = dur
        if fin:
            d['fade_in'] = fin
        if fout:
            d['fade_out'] = fout
        cues.append(d)

    J = 77
    # ---------------- E01-E03 the worldwide fart (frame 0) ----------------
    c(0.0, 'fart_chorus', -3, 'E01 frame 0: everyone farts (ELEV jolt f77); 2nd blast lands on the split-screen cut')
    c(0.28, 'crowd_gasp', -13, 'E01 the four passengers gasp')
    c(E.SEGMENTS[1]['t0'], 'impact_soft', -14, 'E02 3-way split slams in')
    c(E.SEGMENTS[1]['t0'] - 0.08, 'swish', -15, 'E02 split transition', 0.0)
    c(2.0, 'elevator_ding', -15, 'E03 awkward elevator ding during the side-eye', 0.35)
    c(E.SEGMENTS[3]['t0'] - 0.28, 'whoosh_short', -12, 'E03->E04 whip pan to the planet (peak on the cut)')
    c(t_pop0, 'fart_rumble', -11, 'E04 the planet rumbles')
    c(t_pop0, None, -7, 'E04 45 puffs pop across the globe: one pitched pfft per puff frame', path=pop_file)
    c(t_pop0 + 0.05, 'counter_ticks', -15, 'E04 counter 0 -> 8,000,000,000')
    # ---------------- E05 elevators: nose pinch + fanning ----------------
    c(E.t_elev - 0.08, 'impact_soft', -18, 'E05 cut')
    c(seg_time('EL_CU_NOSE', 169), 'cartoon_tick', -13, 'E05 nose pinch (f169)')
    for k, f in enumerate(range(169, 186, 4)):
        c(seg_time('EL_CU_NOSE', f), 'swish', -24, f'E05 hand fans the air (f{f})', -0.3 if k % 2 else 0.3)
    # ---------------- E06 live TV ----------------
    c(E.t_live - 0.06, 'tv_static_click', -16, 'E06 cut to the news feed')
    c(seg_time('NW_ANCHOR_CU', 8) - 0.02, 'fart_wet', -8, 'E06 anchor jolts on air (f8)')
    for f in (16, 24, 32):
        c(seg_time('NW_ANCHOR_CU', f), 'cartoon_tick', -13, f'E06 frozen smile, eye twitch (f{f})', 0.2)
    # ---------------- E07 wedding kiss (organ is in the score) ----------------
    t_kiss = seg_time('WD_KISS', 22)
    c(t_kiss - 0.01, 'fart_trumpet', -10, 'E07 the kiss is interrupted (f22, groom side)', -0.25)
    c(t_kiss + 0.03, 'fart_squeaker', -12, 'E07 bride answers (f23)', 0.3)
    c(t_kiss + 0.01, 'record_scratch', -11, 'E07 organ needle-drop: the wedding music dies')
    c(7.30, 'crowd_eww', -12, 'E07 guests react (after "kiss!")', dur=1.0, fout=0.2)
    # ---------------- E08 science (globe orbit) ----------------
    c(E.SEGMENTS[7]['t0'] - 0.12, 'swish', -14, 'E08 whip-in to the globe')
    c(t_orb0, None, -19, 'E08 sparse distant pffts, one per late puff frame (under narration)', path=orb_file)
    c(E.t_relax + 0.4, 'pop', -17, 'E08 "13-21x a day" chip pops in')
    c(E.t_normal, 'positive_chime', -12, 'E08 TOTALLY NORMAL chip')
    # ---------------- E09-E10 sulfur speck, "Tiny.", domino faint ----------------
    c(E.t_smell - 0.05, 'crowd', -27, 'E09 polite wedding murmur that dies before "Tiny."', dur=2.95, fin=0.2, fout=0.45,
      bus='amb', path='AUDIO/ambience/crowd.flac')
    c(E.t_smell + 0.1, 'pop', -19, 'E09 sulfur speck appears')
    c(E.t_sulfur, 'sparkle_o2', -14, 'E09 "SULFUR (TINY)" label')
    c(E.t_tiny_end + 0.02, 'slide_whistle_down', -9, 'E10b guests topple (speed ramp)')
    for i, (f, p) in enumerate(((154, -0.4), (159, 0.0), (164, 0.4))):
        c(seg_time('WD_FAINT', f), 'body_thud', -6 - i % 2, f'E10b guest {i + 1} hits the floor (f{f})', p)
    # ---------------- E11 news ----------------
    c(E.t_who - 0.04, 'news_sting', -9, 'E11 breaking-news sting on the cut')
    c(16.68, 'dun_dun_dun', -11, 'E11 dun / dun / DUNNN on "who / farted / first"')
    # ---------------- E12 CCTV + ENHANCE x3 ----------------
    c(E.t_sec - 0.05, 'tv_static_click', -10, 'E12 cut to security footage')
    for i, t in enumerate(E.t_enh):
        c(t - 0.07, 'enhance_beep', -10, f'E12 ENHANCE #{i + 1}: whoosh on the zoom, beep as the pixels resolve')
    c(E.t_enh[2] + 0.53, 'tv_static_click', -14, 'E12 cut to the face crop')
    c(E.t_enh[2] + 0.6, 'electronic_beep', -12, 'E12 MATCH FOUND')
    c(E.t_enh[2] + 0.72, 'electronic_beep', -12, 'E12 MATCH FOUND (2nd beep)')
    c(20.62, 'riser_2s', -16, 'E12-E13 riser peaks on the freeze frame')
    c(E.t_one + 0.3, 'cloth_rustle', -20, 'E13a everyone slowly turns to stare')
    # ---------------- E13b freeze frame "One guy." ----------------
    c(E.t_guy + 0.21, 'camera_snap', -6, 'E13b freeze-frame shutter (music stops dead)')
    c(E.t_guy + 0.35, 'pop', -14, 'E13b LIKE = GUILTY chip')
    # ---------------- E14-E17 blame chain ----------------
    c(E.t_bl1 - 0.03, 'impact_soft', -15, 'E14 unfreeze')
    c(E.t_bl1 + 0.3, 'pop', -18, 'E14 COMMENT banner')
    c(E.t_bl1 + 0.45, 'pop', -19, 'E14 tag 1 GRANDMA')
    for src, f, side in (('EL_BLAME1', 262, -0.3), ('EL_BLAME2', 308, 0.3), ('EL_BLAME3', 356, -0.2)):
        c(seg_time(src, f), 'swish', -18, f'{src} arm swings up to point (f{f}); stab in the score at f{f + 5}', side)
    for s in E.SEGMENTS:
        if s.get('whip_out') and s['t0'] > 22:
            c(s['t1'] - 0.28, 'whoosh_short', -11, f'{s["src"]} whip pan follows the finger (peak on the cut)')
    c(E.t_bl3 + 0.2, 'pop', -19, 'E16 tag 2 BUSINESSMAN')
    c(E.t_bl3 + 0.6, 'pop', -19, 'E16 tag 3 KID')
    c(E.t_kid + 0.1, 'pop', -19, 'E17 tag 3 KID')
    c(seg_time('EL_BLAME4', 406), 'swish', -15, 'E17 the kid finally points (f406)', 0.3)
    c(seg_time('EL_BLAME4', 411), 'bass_impact', -10, 'E17 the point lands on "him" (f411)')
    # ---------------- E18-E19 shock, innocent whistle ----------------
    c(E.t_him + 0.18, 'comedic_boing', -11, 'E18 mascot shocked (flash + shake)')
    c(E.t_him + 0.30, 'crowd_gasp', -19, 'E18 passengers gasp')
    c(seg_time('EL_WHISTLE', 455) - 0.03, 'whistle_innocent', -13, 'E19 innocent whistle (pucker f454), cut off by "But"',
      dur=round(E.t_but - 0.03 - seg_time('EL_WHISTLE', 455), 3), fout=0.05)
    c(E.t_cont + 0.2, 'sweat_drip', -12, 'E19 sweat drop 1', -0.3)
    c(E.t_cont + 0.65, 'sweat_drip', -13, 'E19 sweat drop 2', 0.3)
    c(E.t_but, 'bass_impact', -9, 'E19 "But this one?" punch-in')
    # ---------------- E20 rewind, E21 calm elevator -> loop ----------------
    t_rw = E.SEGMENTS[-2]['t0']
    c(t_rw - 0.03, 'vhs_rewind', -9, 'E20 VHS rewind back to 3:13:59', dur=round(E.SEGMENTS[-1]['t0'] - t_rw + 0.03, 3), fout=0.04)
    c(E.SEGMENTS[-1]['t0'] - 0.01, 'button_click', -17, 'E21 tape PLAY clunk; muzak tape-starts in the score')
    c(seg_time('EL_WIDE_END', 66) - 0.02, 'fart_tiny_pfft', -6, 'E21 "...one tiny..." pfft (ELEV f66) = Patient Zero; loops into E01')

    C = {
        'duration': E.END, 'loop': True,
        'narration': 'narration/narration_raw.wav', 'narration_offset': E.OFF,
        'music': 'music_score.wav', 'music_gain_db': -3,
        'music_gates': [[12.66, 14.68, 0.06], [E.t_guy + 0.2, E.t_bl1 - 0.04, 0.01]],
        'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 9},
        'cues': sorted(cues, key=lambda d: d['t']),
    }
    out = os.path.join(HERE, 'cues.json')
    json.dump(C, open(out, 'w'), indent=1, ensure_ascii=False)
    print('CUES_OK', len(cues), out)


_LIB = None


def _lib():
    global _LIB
    if _LIB is None:
        _LIB = {d['name']: d['file'] for d in json.load(open(os.path.join(STUDIO, 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
    return _LIB


if __name__ == '__main__':
    main()

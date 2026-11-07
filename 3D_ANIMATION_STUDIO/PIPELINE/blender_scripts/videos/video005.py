"""VIDEO_005 — "What If Toilets Started Fighting Back?"

Two timelines. BATH: timeline frame = P + 30 t; frames 0..P-1 are the ENDING (the tub's eyes open, it tips
and flings him across the room so he lands on his mark), so the last video frame flows straight into video
frame 0, where he reaches for the lid and it slams. STREET: the citywide riot (reuses the VIDEO_004 city).
Look: warm practical bathroom light (overhead key + window sun + cool rim + bounce), porcelain/tile/chrome
materials, AgX Medium-High-Contrast; the boss scene dims the room and backlights a giant red-eyed toilet.
"""
import json
import math
import os
import random

import bpy
from mathutils import Vector

from studio_lib import scene_kit as SK, render_setup as RS, mascot_api as API, bath_kit as BK
from studio_lib.materials import simple
from video002 import key, expr, arms_down, place, cam, recolor
from video003 import talk

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIDEO_DIR = os.path.join(STUDIO, 'VIDEOS', 'VIDEO_005')
GFX = os.path.join(VIDEO_DIR, 'gfx')
TIM = json.load(open(os.path.join(VIDEO_DIR, 'audio', 'narration', 'timing.json')))
LS = {l['id']: (l['start'], l['end']) for l in TIM['lines']}
FPS = 30
END = 32.4
T_PRE = 28.4                       # video time where the ending (prelude frames) starts
P = int(round((END - T_PRE) * FPS))
T_SLAM = 0.1
T_SPRAY = LS['L03'][1] + 0.12
T_FLUSH = LS['L05'][0] - 0.15
T_RUN = LS['L05'][1] + 0.15
T_STREET = 10.7
T_SNEAK = 18.9
T_TURN = LS['L09'][1] + 0.15
T_ROAR = T_TURN + 0.9
T_BLAST = T_ROAR + 1.3
T_TUB = T_BLAST + 0.65
T_LAUNCH = 31.45                   # tub flings him (prelude)
MARK = Vector((0.05, 1.3, 0.0))     # beside the toilet, turned to face it (rotz -127)  # standing in front of the toilet
TOILET = Vector((-0.55, 1.75, 0.0))
TUB_LIE = Vector((-1.25, 0.25, 0.62))


def F(t):
    """Video time -> BATH timeline frame. The ending (t >= T_PRE) lives in the prelude."""
    if t >= T_PRE:
        return int(round((t - T_PRE) * FPS))
    return int(round(P + t * FPS))


def words(lines):
    return [w for w in TIM['words'] if w['line'] in lines]


def kloc(ob, f, v, path='location'):
    setattr(ob, path, v)
    ob.keyframe_insert(path, frame=f)


# ============================================================================== BATH
def build_bath():
    sc = bpy.context.scene
    M = BK.bathroom(GFX)
    vl = bpy.context.view_layer
    T = BK.Toilet('Toilet', tuple(TOILET), M=M)
    G = BK.Toilet('Giant', (-0.4, 1.0, 0.0), scale=2.6, M=M)          # fits in front of the back wall
    for e in G.eyes:
        e.data.materials[0] = M['red']
    m, col = SK.append_mascot()
    vl.active_layer_collection = vl.layer_collection
    tub, face, door = M['tub_root'], M['tub_face'], M['door']
    lights = {o.name: o for o in bpy.data.objects if o.type == 'LIGHT'}

    # ---------- visibility: small toilet until it chases him out; giant from the boss beat (and never in the prelude)
    def vis(objs, pairs):
        for o in objs:
            for f, on in pairs:
                o.hide_render = not on
                o.keyframe_insert('hide_render', frame=f)
    small = [o for o in bpy.data.objects if o.name.startswith('Toilet')]
    giant = [o for o in bpy.data.objects if o.name.startswith('Giant')]
    vis(small, [(0, True), (F(T_RUN + 1.2), False), (F(T_SNEAK - 0.1), False)])
    vis(giant, [(0, False), (F(T_SNEAK + 0.5), True), (F(T_TUB + 3.0), True)])
    # boss lighting: dim the warm key, flood the cool rim, kill the sun
    for name, base, boss in (('KeyOverhead', 260, 60), ('Rim', 120, 900)):
        L = lights[name].data
        for f, v in ((0, base), (F(T_SNEAK + 1.5), base), (F(T_TURN - 0.2), boss), (F(T_TUB + 0.5), boss), (F(T_TUB + 2.5), base)):
            L.energy = v
            L.keyframe_insert('energy', frame=f)
    if 'KeySun' in lights:
        L = lights['KeySun'].data
        for f, v in ((0, 3.0), (F(T_TURN - 0.2), 3.0), (F(T_TURN), 0.2), (F(T_TUB + 2.5), 3.0)):
            L.energy = v
            L.keyframe_insert('energy', frame=f)

    # ---------- the small toilet's performance
    T.lid(0, 70)
    T.mood(0, anger=0.0, squint=1.0)                                   # asleep (eyes shut) in the prelude
    T.mood(F(0.0), anger=0.0, squint=1.0)
    T.lid(F(0.0), 70)
    T.lid(F(T_SLAM), 0)                                                # SLAM
    T.pose(F(0.0), TOILET, squash=0.0)
    T.pose(F(T_SLAM), TOILET, squash=0.18)
    T.pose(F(T_SLAM + 0.15), TOILET, squash=-0.06)
    T.pose(F(T_SLAM + 0.3), TOILET, squash=0.0)
    T.mood(F(T_SLAM + 0.12), anger=0.0, squint=0.0, look=(0.5, 0.2))   # eyes snap open
    T.mood(F(0.9), anger=0.9, squint=0.25, look=(0.6, 0.3))            # glare
    T.blink(F(1.6))
    T.handle.rotation_euler = (0, 0, 0)
    T.handle.keyframe_insert('rotation_euler', frame=F(2.2))
    T.handle.rotation_euler = (0, math.radians(-25), math.radians(20))  # handle slowly turns toward him
    T.handle.keyframe_insert('rotation_euler', frame=F(3.0))
    T.handle.keyframe_insert('rotation_euler', frame=F(T_SPRAY - 0.4))
    T.pose(F(3.2), TOILET, squash=0.05, lean=-4)                       # coils...
    T.mood(F(4.2), anger=1.0, squint=0.55, look=(0.6, 0.4))            # narrowing eyes as he leans in
    T.pose(F(T_SPRAY - 0.1), TOILET, squash=0.15, lean=-6)
    T.lid(F(T_SPRAY - 0.05), 0)
    T.lid(F(T_SPRAY), 95)                                              # spits
    T.pose(F(T_SPRAY + 0.05), TOILET, squash=-0.15, lean=12)
    T.pose(F(T_SPRAY + 0.4), TOILET, squash=0.0, lean=0)
    T.mood(F(T_SPRAY + 0.5), anger=0.3, squint=0.7, look=(0.6, 0.3))  # smug
    T.flush(F(T_FLUSH))
    for k in range(6):                                                 # laughing bounce while it geysers
        f = F(T_FLUSH + 0.2) + k * 5
        T.pose(f, TOILET, squash=0.12 if k % 2 == 0 else -0.08, lean=4 * (-1) ** k)
    T.lid(F(T_FLUSH + 1.4), 95)
    T.chomp(F(T_RUN), F(T_RUN + 1.2), period=5, open_deg=80)          # chases him to the door
    T.hop(F(T_RUN + 0.1), TOILET, Vector((0.2, 0.2, 0)), height=0.3, dur=12)
    T.hop(F(T_RUN + 0.6), Vector((0.2, 0.2, 0)), Vector((0.7, -0.9, 0)), height=0.3, dur=12)
    # water: spray to his face, self-flush geyser
    face_pt = MARK + Vector((-0.12, 0.09, 1.15))
    bowl = TOILET + Vector((0, -0.1, 0.45))
    BK.jet('Spray', F(T_SPRAY), F(T_SPRAY + 0.45), bowl, (face_pt - bowl), (face_pt - bowl).length, 0.02)
    BK.droplets('SprayDrop', F(T_SPRAY), 50, bowl, (face_pt - bowl) * 2.4, 0.5, life=14, seed=3, size=(0.005, 0.014))
    BK.droplets('FaceSplash', F(T_SPRAY + 0.12), 40, face_pt, (0.5, -0.4, 0.6), 1.3, life=16, seed=4, size=(0.004, 0.011))
    BK.jet('Geyser', F(T_FLUSH + 0.15), F(T_FLUSH + 1.3), bowl + Vector((0, 0, 0.05)), (0.15, -0.25, 1), 1.6, 0.04)
    BK.droplets('GeyserDrop', F(T_FLUSH + 0.15), 90, bowl + Vector((0, 0, 0.1)), (0.3, -0.4, 3.6), 1.2, life=26, seed=5, size=(0.006, 0.018))
    for k in range(4):                                                 # drips off his hair while soaked
        BK.droplets(f'Drip{k}_', F(T_SPRAY + 0.5 + 0.9 * k), 5, MARK + Vector((0, 0, 1.38)), (0, 0, -0.2), 0.12, life=14, seed=10 + k,
                    size=(0.008, 0.014))

    # ---------- mascot
    def at(f, v, rotz=None):
        kloc(m.rig, f, v)
        if rotz is not None:
            m.rig.rotation_euler = (0, 0, math.radians(rotz))
            m.rig.keyframe_insert('rotation_euler', frame=f)
    # prelude: lying in the tub ... flung across the room ... lands on his mark at frame P
    m.rig.rotation_mode = 'XYZ'
    lie = (math.radians(-75), 0, math.radians(-90))
    for f in (0, F(T_LAUNCH)):
        kloc(m.rig, f, TUB_LIE)
        m.rig.rotation_euler = lie
        m.rig.keyframe_insert('rotation_euler', frame=f)
    arms_down(m, 0, 0.3)
    key(m, 0, arm_0=dict(side='L', raise_=70, forward=-20, elbow=20), arm_1=dict(side='R', raise_=70, forward=-20, elbow=20))
    expr(m, 0, 'sad', 0.8, eyes=(0.0, 0.2))                            # exhausted
    expr(m, F(28.9), 'confused', 0.8, eyes=(0.35, -0.3), head=(20, -10, 0))   # feels the tub move
    expr(m, F(30.2), 'scared', 1.0, eyes=(0.4, -0.4))
    expr(m, F(T_LAUNCH), 'shocked', 1.0)
    mid = (TUB_LIE + MARK) / 2 + Vector((0, 0, 1.3))
    kloc(m.rig, F(T_LAUNCH) + 6, mid)
    m.rig.rotation_euler = (math.radians(-20), math.radians(180), math.radians(-30))
    m.rig.keyframe_insert('rotation_euler', frame=F(T_LAUNCH) + 6)
    key(m, F(T_LAUNCH) + 6, arm_0=dict(side='L', raise_=160, forward=0, elbow=10), arm_1=dict(side='R', raise_=160, forward=0, elbow=10))
    kloc(m.rig, P - 1, MARK + Vector((0, 0, 0.05)))
    m.rig.rotation_euler = (0, 0, math.radians(-127))
    m.rig.keyframe_insert('rotation_euler', frame=P - 1)
    # video 0: landed, reaching for the lid (half asleep)... SLAM
    at(P, MARK, -127)
    key(m, P, spine_pose=dict(bend=14), loc=('hips', 0, -0.05, 0),
        arm_0=dict(side='R', raise_=20, forward=70, elbow=40, wrist=-20), hand_0=dict(side='R', curl=0.3),
        arm_1=dict(side='L', raise_=-25, forward=10, elbow=20))
    expr(m, P, 'neutral', 1.0, eyes=(0.0, -0.35), head=(0, -18, 0))
    key(m, P, lids=dict(up=-25, lo=8))                                 # sleepy
    key(m, F(T_SLAM + 0.05), arm_0=dict(side='R', raise_=40, forward=30, elbow=110), spine_pose=dict(bend=-6), loc=('hips', 0, 0, 0))
    expr(m, F(T_SLAM + 0.08), 'shocked', 1.0, eyes=(0.0, -0.3), head=(0, -10, 0))   # jerk back
    key(m, F(T_SLAM + 0.08), lids=dict(up=14, lo=-8))
    key(m, F(0.8), arm_0=dict(side='R', raise_=-25, forward=15, elbow=40))
    expr(m, F(1.7), 'confused', 1.0, eyes=(0.25, -0.3), head=(14, -12, 12))         # "Wait... what?" head tilt
    API.blink(m, F(2.6))
    key(m, F(3.1), spine_pose=dict(bend=18), loc=('hips', 0, -0.03, 0))             # cautiously leans in
    expr(m, F(3.2), 'curious', 0.9, eyes=(0.0, -0.4), head=(0, -20, 0))
    key(m, F(4.2), spine_pose=dict(bend=24), arm_0=dict(side='R', raise_=10, forward=55, elbow=60), hand_0=dict(side='R', point=True))
    expr(m, F(4.5), 'happy', 0.5, eyes=(0.0, -0.45), head=(0, -24, 0))             # "maybe it's just tired" ...
    # SPRAY: recoil, stagger back
    key(m, F(T_SPRAY + 0.05), spine_pose=dict(bend=-22), loc=('hips', 0, 0.02, 0),
        arm_0=dict(side='R', raise_=80, forward=30, elbow=90), arm_1=dict(side='L', raise_=80, forward=30, elbow=90))
    expr(m, F(T_SPRAY + 0.05), 'disgusted', 1.0, eyes=(0, 0))
    key(m, F(T_SPRAY + 0.05), lids=dict(up=-45, lo=20), shape=('cheek_puff', 0.8))
    at(F(T_SPRAY + 0.05), MARK, -127)
    at(F(T_SPRAY + 0.35), MARK + Vector((0.25, -0.2, 0)), -127)
    key(m, F(T_SPRAY + 0.35), shape=('cheek_puff', 0.0))
    # "Bro, seriously?!" — dripping, outraged, arms out
    key(m, F(LS['L04'][0]), spine_pose=dict(bend=0), arm_0=dict(side='L', raise_=35, forward=35, elbow=40), hand_0=dict(side='L', spread=1.0),
        arm_1=dict(side='R', raise_=35, forward=35, elbow=40), hand_1=dict(side='R', spread=1.0))
    expr(m, F(LS['L04'][0]), 'angry', 1.0, eyes=(0, 0.0), head=(0, 4, -8))
    expr(m, F(T_FLUSH), 'shocked', 1.0, eyes=(0.0, 0.3), head=(0, 15, 0))            # geyser goes up
    expr(m, F(T_FLUSH + 0.8), 'disgusted', 1.0, eyes=(0, 0.2))
    key(m, F(T_FLUSH + 0.8), arm_0=dict(side='L', raise_=120, forward=20, elbow=110), arm_1=dict(side='R', raise_=120, forward=20, elbow=110))
    # runs for the door
    expr(m, F(T_RUN), 'scared', 1.0, eyes=(0.0, 0.0))
    key(m, F(T_RUN), spine_pose=dict(bend=10), loc=('hips', 0, -0.06, 0))          # anticipation
    at(F(T_RUN), MARK + Vector((0.25, -0.2, 0)), -127)
    # sprint to the door: the run cycle drives the root bone in his local frame (object stays put, rotated -127)
    for fz in (0, F(T_RUN) + 2):                                    # root bone neutral until the run starts
        m.touched = set()
        m.loc('root', 0, 0, 0)
        m.rot('root', 0, 0, 0)
        m.key(fz)
    API.walk(m, F(T_RUN) + 3, F(T_RUN) + 31, speed=3.0, cycle=12, start_pos=(0, 0), heading_deg=137, run=True)
    m.touched = set()
    m.loc('root', 0, 0, 0)
    m.rot('root', 0, 0, 0)
    m.key(F(T_SNEAK) - 2)                                           # root bone back to zero before he sneaks in
    # sneaks back in (backwards, looking out the door), shuts it, relief... then turns around
    at(F(T_SNEAK), Vector((0.75, -1.7, 0)), 0)
    door.rotation_euler = (0, 0, 0)
    door.keyframe_insert('rotation_euler', frame=F(T_SNEAK - 0.3))
    door.rotation_euler = (0, 0, math.radians(-80))
    door.keyframe_insert('rotation_euler', frame=F(T_SNEAK))
    door.keyframe_insert('rotation_euler', frame=F(T_SNEAK + 0.9))
    door.rotation_euler = (0, 0, 0)
    door.keyframe_insert('rotation_euler', frame=F(T_SNEAK + 1.2))
    for k, f in enumerate(range(F(T_SNEAK), F(T_SNEAK + 1.0), 6)):              # tiptoe backwards
        at(f, Vector((0.75 - 0.02 * k, -1.7 + 0.11 * k, 0.02 if k % 2 else 0.0)), 0)
    key(m, F(T_SNEAK), spine_pose=dict(bend=12), arm_0=dict(side='L', raise_=20, forward=40, elbow=80), arm_1=dict(side='R', raise_=20, forward=40, elbow=80))
    expr(m, F(T_SNEAK), 'scared', 0.7, eyes=(0.0, 0.0), head=(0, 0, 0))
    at(F(T_SNEAK + 1.2), Vector((0.5, -0.85, 0)), 0)
    key(m, F(T_SNEAK + 1.3), spine_pose=dict(bend=-6), arm_0=dict(side='R', raise_=40, forward=50, elbow=140))   # wipes forehead
    expr(m, F(T_SNEAK + 1.4), 'happy', 0.8, eyes=(0.0, 0.2))
    expr(m, F(LS['L09'][0]), 'neutral', 1.0, eyes=(0.3, 0.0))                     # "The bathroom." — realises
    at(F(T_TURN - 0.1), Vector((0.5, -0.85, 0)), 0)
    at(F(T_TURN + 0.5), Vector((0.5, -0.85, 0)), 180)                            # slow turn
    expr(m, F(T_TURN + 0.5), 'scared', 1.0, eyes=(0.0, 0.5), head=(0, 25, 0))   # looks UP at the giant
    key(m, F(T_ROAR), arm_0=dict(side='L', raise_=60, forward=30, elbow=120), arm_1=dict(side='R', raise_=60, forward=30, elbow=120))
    expr(m, F(T_ROAR), 'shocked', 1.0, eyes=(0.0, 0.5), head=(0, 25, 0))
    # BLAST: flies into the tub
    at(F(T_BLAST), Vector((0.5, -0.85, 0)), 180)
    arc = (Vector((0.5, -0.85, 0)) + TUB_LIE) / 2 + Vector((0, 0, 1.1))
    at(F(T_BLAST) + 8, arc, 20)
    m.rig.rotation_euler = (math.radians(-40), 0, math.radians(20))
    m.rig.keyframe_insert('rotation_euler', frame=F(T_BLAST) + 8)
    kloc(m.rig, F(T_TUB), TUB_LIE)
    m.rig.rotation_euler = lie
    m.rig.keyframe_insert('rotation_euler', frame=F(T_TUB))
    kloc(m.rig, F(T_PRE) - 1 if False else P + int(T_PRE * FPS) - 1, TUB_LIE)
    m.rig.keyframe_insert('rotation_euler', frame=P + int(T_PRE * FPS) - 1)
    key(m, F(T_BLAST) + 8, arm_0=dict(side='L', raise_=160, forward=0, elbow=10), arm_1=dict(side='R', raise_=160, forward=0, elbow=10))
    expr(m, F(T_BLAST) + 4, 'shocked', 1.0)
    key(m, F(T_TUB), arm_0=dict(side='L', raise_=70, forward=-20, elbow=20), arm_1=dict(side='R', raise_=70, forward=-20, elbow=20))
    expr(m, F(T_TUB + 0.3), 'sad', 0.8, eyes=(0.0, 0.2))
    expr(m, F(LS['L10'][0]), 'angry', 0.7, eyes=(0.0, 0.3))                      # "I'm never using a toilet again!"
    key(m, F(LS['L10'][0]), arm_0=dict(side='R', raise_=110, forward=20, elbow=20), hand_0=dict(side='R', fist=True))
    expr(m, F(LS['L10'][1] + 0.3), 'sad', 0.8, eyes=(0.0, 0.2))
    talk(m, words(('L02', 'L04', 'L10')), 0.0, offset=P)
    # ---------- the giant: roar, chomp, BLAST
    G.lid(0, 0)
    G.mood(F(T_SNEAK), anger=0.0, squint=1.0)
    G.mood(F(T_TURN + 0.3), anger=1.0, squint=0.0, look=(0.6, -0.3))          # red eyes snap open as he turns
    G.pose(F(T_TURN + 0.3), squash=0.0)
    G.pose(F(T_ROAR - 0.15), squash=0.2, lean=-6)
    G.pose(F(T_ROAR), squash=-0.15, lean=10)
    G.chomp(F(T_ROAR), F(T_ROAR + 1.0), period=6, open_deg=85)
    G.lid(F(T_BLAST - 0.2), 20)
    G.pose(F(T_BLAST - 0.2), squash=0.25, lean=-10)
    G.lid(F(T_BLAST), 100)
    G.pose(F(T_BLAST), squash=-0.2, lean=14)
    G.pose(F(T_BLAST + 0.6), squash=0.0, lean=0)
    gb = Vector((-0.4, 1.0 - 0.25, 1.2))
    tgt = Vector((0.5, -0.85, 1.0))
    BK.jet('Blast', F(T_BLAST), F(T_BLAST + 0.7), gb, tgt - gb, (tgt - gb).length + 0.4, 0.12)
    BK.droplets('BlastDrop', F(T_BLAST), 90, gb, (tgt - gb) * 2.5, 1.2, life=18, seed=7, size=(0.02, 0.05))
    BK.droplets('TubSplash', F(T_TUB), 50, TUB_LIE + Vector((0.2, 0, 0.1)), (0.4, 0, 2.5), 1.2, life=20, seed=8, size=(0.015, 0.04))
    # ---------- the tub wakes up (prelude) and flings him
    eyes, pupils, brows, mouth = face['eyes'], face['pupils'], face['brows'], face['mouth']
    t_open = 28.9

    def k_scale(o, f, sz):
        o.scale = (o.scale[0], o.scale[1], sz)
        o.keyframe_insert('scale', frame=f)
    for o in eyes + pupils:
        k_scale(o, 0, 0.01)
        k_scale(o, F(t_open), 0.01)
        k_scale(o, F(t_open) + 4, 1.0)
        k_scale(o, P - 1, 1.0)
        k_scale(o, P, 0.01)
    for bpv, br in brows:
        k_scale(br, 0, 0.01)
        k_scale(br, F(t_open) + 4, 1.0)
        bpv.rotation_euler = (0, 0, 0)
        bpv.keyframe_insert('rotation_euler', frame=F(t_open) + 4)
        bpv.rotation_euler = (math.radians(25) * (1 if bpv.name.endswith('-1') else -1), 0, 0)
        bpv.keyframe_insert('rotation_euler', frame=F(30.4))
        k_scale(br, P - 1, 1.0)
        k_scale(br, P, 0.01)
    for f, sz in ((0, 0.02), (F(29.8), 0.02), (F(30.2), 0.6), (F(30.5), 0.2), (F(30.8), 0.7), (P - 1, 0.7), (P, 0.02)):
        k_scale(mouth, f, sz)                                                     # the drain mouth gurgles open
    for f, rx in ((0, 0), (F(T_LAUNCH) - 6, 0), (F(T_LAUNCH) - 2, -6), (F(T_LAUNCH) + 3, 22), (F(T_LAUNCH) + 12, 0), (P, 0)):
        tub.rotation_euler = (0, math.radians(rx), 0)
        tub.keyframe_insert('rotation_euler', frame=f)
    return {'mascot': m, 'col': col}


def bath_cams():
    cams = {}

    def mk(name, loc, look, lens):
        c, t = cam(name, loc, look, lens)
        cams[name] = (c, t)
        return c, t
    mk('CAM_OPEN', (0.25, -0.9, 1.3), (-0.25, 1.5, 0.8), 24)          # frame 0 = last frame (wide, tub at left)
    mk('CAM_TCU', (-0.85, 0.95, 0.72), (-0.5, 1.75, 0.66), 30)            # toilet's face (off the spray axis)
    mk('CAM_MCU', (-0.95, 1.95, 1.2), (0.0, 1.3, 1.12), 40)           # toilet's POV on his face (door behind him)
    mk('CAM_SIDE', (-0.2, -0.35, 1.0), (-0.2, 1.5, 0.95), 24)            # profile: spray / geyser
    mk('CAM_POV', (-0.5, 1.6, 2.35), (0.6, -1.1, 0.9), 22)               # giant's POV on the door
    c, t = mk('CAM_REVEAL', (1.3, -1.2, 1.25), (-0.4, 1.0, 1.7), 18)    # low angle up at the giant, him in front
    SK.key_cam(c, t, F(T_TURN), (1.3, -1.2, 1.25), (-0.2, 1.0, 1.3), lens=20)
    SK.key_cam(c, t, F(T_ROAR + 0.6), (1.25, -1.15, 1.1), (-0.4, 1.0, 1.9), lens=17)
    mk('CAM_BLAST', (1.55, -1.0, 1.6), (-0.6, 0.9, 0.9), 16)               # wide side: giant, him, tub
    mk('CAM_TUB', (-0.15, -0.95, 1.9), (-1.2, 0.3, 0.55), 24)            # tub + its face
    return cams


# ============================================================================== STREET
def build_street():
    import video004 as V4
    V4.street()
    sc = bpy.context.scene
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sun = bpy.data.lights.new('KeySunStreet', 'SUN')
    sun.energy = 3.5
    sun.angle = math.radians(2)
    sun.color = (1.0, 0.93, 0.82)
    so = bpy.data.objects.new('KeySunStreet', sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    V4.car('Car', (4.5, -5.0, 0), '#2F6FD0')
    cast = {}
    m, col = SK.append_mascot()
    cast['MASCOT'] = (m, col)
    for n in ('GRANDMA', 'BUSINESSMAN', 'KID'):
        mm, cc = SK.append_character(n)
        SK.lean_character(cc, 0)
        cast[n] = (mm, cc)
    vl = bpy.context.view_layer
    vl.active_layer_collection = vl.layer_collection
    M = BK.mats()
    toilets = [BK.Toilet(f'ST{i}', (0, 0, 0), M=M) for i in range(5)]
    rnd = random.Random(2)
    M_, G, B, K = (cast[n][0] for n in ('MASCOT', 'GRANDMA', 'BUSINESSMAN', 'KID'))
    f = lambda t: int(round(P + t * FPS))
    # mascot bursts out of his front door and sprints across (L06)
    API.walk(M_, f(10.7), f(13.0), speed=3.2, cycle=12, start_pos=(-4.0, 1.0), heading_deg=-80, run=True)
    expr(M_, f(10.7), 'scared', 1.0)
    # businessman chased toward camera (L07 'They chase you')
    API.walk(B, f(13.0), f(16.0), speed=2.4, cycle=13, start_pos=(-0.5, 6.0), heading_deg=0, run=True)
    expr(B, f(10.7), 'scared', 1.0, eyes=(0.0, 0.0))
    chaser = toilets[0]
    pos = Vector((-0.5, 7.2, 0))
    for k in range(9):
        t0 = 13.2 + k * 0.36
        nxt = Vector((-0.5, 7.2 - 0.8 * (k + 1), 0))
        chaser.hop(f(t0), pos, nxt, height=0.35, dur=9)
        pos = nxt
    chaser.chomp(f(10.7), f(17.5), period=5, open_deg=80)
    chaser.mood(f(10.7), anger=1.0, look=(0.0, 0.2))
    # kid at the shop door, a toilet hops in front of it and snaps (L07 'They block the exits')
    place(K, 2.4, 3.6, 180)
    arms_down(K, f(10.7), 0.3)
    blocker = toilets[1]
    blocker.hop(f(15.3), Vector((4.0, 4.4, 0)), Vector((2.4, 4.6, 0)), height=0.5, dur=10)
    blocker.pose(f(15.3) + 16, Vector((2.4, 4.6, 0)), squash=0.0, turn=180)
    blocker.chomp(f(15.8), f(17.0), period=4, open_deg=85)
    blocker.mood(f(15.3), anger=1.0)
    expr(K, f(15.6), 'shocked', 1.0, eyes=(0, 0))
    key(K, f(15.7), arm_0=dict(side='L', raise_=80, forward=30, elbow=60), arm_1=dict(side='R', raise_=80, forward=30, elbow=60), spine_pose=dict(bend=-12))
    # grandma vs. toilet-paper missiles (L07 'like missiles')
    place(G, -2.4, 0.6, 30)
    arms_down(G, f(10.7), 0.3)
    gun = toilets[2]
    gun.pose(f(10.7), Vector((-1.2, 3.4, 0)), squash=0.0, turn=150)
    gun.mood(f(10.7), anger=1.0, look=(-0.4, 0.0))
    tp = simple('ToiletPaper', '#FAFAF6', rough=0.9, sheen=0.6)
    for i, t0 in enumerate((16.6, 16.85, 17.1, 17.35, 17.6)):
        gun.lid(f(t0) - 2, 0)
        gun.lid(f(t0), 95)
        gun.pose(f(t0), Vector((-1.2, 3.4, 0)), squash=-0.15, turn=150)
        gun.pose(f(t0) + 3, Vector((-1.2, 3.4, 0)), squash=0.1, turn=150)
        roll = BK.cyl(f'TP{i}', (0, 0, 0), 0.06, 0.11, tp)
        a, b = Vector((-1.2, 3.25, 0.5)), Vector((-2.3 + rnd.uniform(-0.4, 0.4), 0.7, 1.2 + rnd.uniform(-0.2, 0.3)))
        roll.hide_render = True
        roll.keyframe_insert('hide_render', frame=0)
        roll.hide_render = False
        roll.keyframe_insert('hide_render', frame=f(t0))
        for k in range(0, 13):
            u = k / 12
            roll.location = a.lerp(b, u) + Vector((0, 0, 1.2 * math.sin(math.pi * u)))
            roll.keyframe_insert('location', frame=f(t0) + k)
            roll.rotation_euler = (k * 0.9, k * 0.5, 0)
            roll.keyframe_insert('rotation_euler', frame=f(t0) + k)
        roll.hide_render = True
        roll.keyframe_insert('hide_render', frame=f(t0) + 13)
    expr(G, f(16.6), 'shocked', 1.0, eyes=(0.3, 0.0), head=(20, 0, 0))
    for k, t0 in enumerate((16.9, 17.3, 17.7)):                             # dodging
        key(G, f(t0), spine_pose=dict(bend=20 if k % 2 == 0 else -10, side=15 * (-1) ** k),
            arm_0=dict(side='L', raise_=90, forward=40, elbow=100), arm_1=dict(side='R', raise_=90, forward=40, elbow=100))
    # riot background: toilets hopping across the street
    for i, tl in enumerate(toilets[3:]):
        pos = Vector((-6.0 + 3 * i, -3.5 - 1.2 * i, 0))
        for k in range(16):
            nxt = pos + Vector((0.8, 0.1 * (-1) ** k, 0))
            tl.hop(f(10.7 + k * 0.4 + 0.13 * i), pos, nxt, height=0.4, dur=10)
            pos = nxt
        tl.chomp(f(10.7), f(17.5), period=6, open_deg=70)
        tl.mood(f(10.7), anger=1.0)
    cams = {}
    for name, loc, look, lens in (('CAM_RIOT', (1.5, -9.5, 2.6), (-1.0, 2.0, 1.0), 22),
                                  ('CAM_CHASE', (-0.3, -1.5, 1.0), (-0.5, 4.0, 1.0), 30),
                                  ('CAM_EXIT', (3.6, 1.0, 1.2), (2.4, 4.4, 0.8), 26),
                                  ('CAM_TP', (-0.2, -1.6, 1.5), (-1.8, 2.0, 1.0), 22)):
        c, t = cam(name, loc, look, lens)
        cams[name] = (c, t)
    return cast, cams


# ============================================================================== jobs
JOBS = {   # job: (set, camera, visible-cast or 'all', video t0, video t1)
    'OPEN':    ('BATH', 'CAM_OPEN', 'all', 0.0, 1.0),
    'END':     ('BATH', 'CAM_OPEN', 'all', 30.5, END),
    'TCU':     ('BATH', 'CAM_TCU', 'all', 0.0, T_SPRAY + 0.6),
    'MCU':     ('BATH', 'CAM_MCU', 'all', 0.6, T_RUN + 1.0),
    'SIDE':    ('BATH', 'CAM_SIDE', 'all', T_SPRAY - 0.4, T_RUN + 1.3),
    'POV':     ('BATH', 'CAM_POV', 'all', T_SNEAK - 0.2, T_TURN + 0.6),
    'REVEAL':  ('BATH', 'CAM_REVEAL', 'all', T_TURN - 0.2, T_BLAST + 0.3),
    'BLAST':   ('BATH', 'CAM_BLAST', 'all', T_BLAST - 0.3, T_TUB + 0.8),
    'TUB':     ('BATH', 'CAM_TUB', 'all', T_TUB - 0.2, 31.5),
    'RIOT':    ('STREET', 'CAM_RIOT', 'all', 10.7, 14.8),
    'CHASE':   ('STREET', 'CAM_CHASE', 'all', 14.6, 15.8),
    'EXIT':    ('STREET', 'CAM_EXIT', 'all', 15.6, 16.8),
    'TPMISS':  ('STREET', 'CAM_TP', 'all', 16.5, 18.2),
}


def frames_of(job):
    s, _, _, t0, t1 = JOBS[job]
    if s == 'BATH':
        if t0 >= T_PRE:
            return F(t0), F(t1) + 1 if t1 < END else P
        if t1 > T_PRE:
            return F(t0), F(T_PRE) if False else P + int(T_PRE * FPS) + 1
        return F(t0), F(t1) + 1
    return int(round(P + t0 * FPS)), int(round(P + t1 * FPS)) + 1


SHOTS = {j: (JOBS[j][0], JOBS[j][1], frames_of(j), JOBS[j][2], 1.0) for j in JOBS}


def build_shot(sid):
    sc = bpy.context.scene
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 1
    s, camname, visible, _, _ = JOBS[sid]
    if s == 'BATH':
        build_bath()
        cams = bath_cams()
    else:
        cast, cams = build_street()
    sc.camera = cams[camname][0]
    f0, f1 = frames_of(sid)
    sc.frame_start, sc.frame_end = f0, f1 - 1
    return {'frames': (f0, f1), 'step': 1}

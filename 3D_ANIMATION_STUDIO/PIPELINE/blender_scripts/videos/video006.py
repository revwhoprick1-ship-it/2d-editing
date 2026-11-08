"""VIDEO_006 — "The 13th Floor" (2dEDIT style: cel-shaded flat 2D look via studio_lib.toon).

One continuous timeline, frame = 30 t. Places: the elevator (cold fluorescent, flicker), the floor-13 hallway
(dark, dusty, sparse warm sconces), the apartment (warm lamp + TV glow) where his double waits. The final
"reflection" is a mirrored twin behind tinted steel, so it can smile while he stays frozen.
The mascot is positioned through his root bone (the walk helper drives the same bone).
"""
import json
import math
import os

import bpy
from mathutils import Vector

from studio_lib import scene_kit as SK, render_setup as RS, mascot_api as API, sets_v2 as SV, toon
from studio_lib.materials import simple, hex_rgb
from studio_lib.bath_kit import rbox, cyl, sphere, tex_mat, _link
from video002 import key, expr, arms_down, recolor
from video003 import talk, image_plane

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIDEO_DIR = os.path.join(STUDIO, 'VIDEOS', 'VIDEO_006')
GFX = os.path.join(VIDEO_DIR, 'gfx')
TIM = json.load(open(os.path.join(VIDEO_DIR, 'audio', 'narration', 'timing.json')))
LS = {l['id']: (l['start'], l['end']) for l in TIM['lines']}
FPS = 30
END = 38.0


def F(t):
    return int(round(t * FPS))


# key times (video seconds)
T_FLIP = 0.35            # display 12 -> 13 (frame 10)
T_DCLOSE = 1.3
T_DING1 = 7.0            # arrives at 13
T_OUT = 12.0             # steps out
T_PHOTO = 14.6
T_TURN = 16.9
T_SLAM = 17.2            # elevator doors slam shut
T_RUNB = 17.5
T_DOOR13 = 20.4          # end door creaks open
T_WALK2 = 22.4
T_PEEK = 25.3
T_HEAD = 25.7            # double turns his head
T_STAND = 26.9
T_DARK = 29.85           # lights out
T_DING2 = 30.4           # back in the elevator
T_FLIP2 = 32.6           # display 13 -> 12
T_CLOCK = 33.3
T_BTN = 34.3
T_REFL = 35.0
T_SMILE = 36.3
T_BLACK = 37.8


def root(m, f, x, y, h):
    m.touched = set()
    m.loc('root', x, y, 0)
    m.rot('root', 0, 0, h)
    for s in ('L', 'R'):
        m.loc(f'foot_ik.{s}', 0, 0, 0)
        m.rot(f'foot_ik.{s}', 0, 0, 0)
    m.loc('hips', 0, 0, 0)
    m.key(f)


def vis(objs, pairs):
    for o in objs:
        for f, on in pairs:
            o.hide_render = not on
            o.keyframe_insert('hide_render', frame=f)


def energy(light, pairs):
    for f, v in pairs:
        light.data.energy = v
        light.data.keyframe_insert('energy', frame=f)


# ============================================================================== sets
def elevator_set():
    SV.elevator()
    for o in list(bpy.data.objects):
        if o.name.startswith(('ELV_Lobby', 'ELV_Display', 'ELV_Btn', 'ELV_ButtonPlate')) or o.name == 'Fill_Door':
            bpy.data.objects.remove(o, do_unlink=True)
    for name, col in (('SET_Steel', '#5F6872'), ('SET_SteelDark', '#3A414A'), ('SET_Wood', '#3E2C20'), ('SET_ElevFloor', '#1C1D22')):
        m = bpy.data.materials.get(name)
        if m:
            m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = hex_rgb(col)
    lp = bpy.data.materials.get('SET_CeilLight')
    lp.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = hex_rgb('#CFE2FF')
    key = bpy.data.objects['Key_Ceil']
    key.data.color = (0.72, 0.84, 1.0)
    key.data.energy = 120
    # sliding doors
    dm = simple('DoorSteel', '#4A525C', rough=0.4)
    doors = [rbox(f'Door{s}', (0.335 * s, -0.86, 1.1), (0.67, 0.03, 2.2), dm, bevel=0.005) for s in (-1, 1)]
    # LED display above the doors (inside) + tiny clock
    disp = {n: image_plane(f'Disp{n}', os.path.join(GFX, f'disp_{n}.png'), (0.36, 0.135), (0, -0.80, 2.08), rot=(90, 0, 180), emit=3.0)
            for n in ('12', '13')}
    # button panel (right wall) with lit buttons
    p12 = image_plane('Panel12', os.path.join(GFX, 'panel_12.png'), (0.18, 0.5), (0.975, -0.5, 1.25), rot=(90, 0, -90), emit=0.9)
    p13 = image_plane('Panel13', os.path.join(GFX, 'panel_13.png'), (0.18, 0.5), (0.974, -0.5, 1.25), rot=(90, 0, -90), emit=0.9)
    return doors, disp, (p12, p13), key


def hallway_set():
    wall = tex_mat('Wallpaper', os.path.join(GFX, 'wallpaper_old.png'), scale=(0.35, 0.35, 0.35), rough=0.9)
    floor = tex_mat('FloorDust', os.path.join(GFX, 'floor_dusty.png'), scale=(0.5, 0.5, 0.5), rough=0.9)
    dark = simple('HallCeil', '#1A1C1E', rough=0.9)
    trim = simple('HallTrim', '#2B2420', rough=0.7)
    rbox('HallFloor', (0, -6.0, -0.02), (1.8, 10.3, 0.04), floor, bevel=0)
    rbox('HallCeil', (0, -6.0, 2.55), (1.8, 10.3, 0.05), dark, bevel=0)
    for s in (-1, 1):
        rbox(f'HallWall{s}', (0.92 * s, -6.0, 1.25), (0.05, 10.3, 2.6), wall, bevel=0)
        rbox(f'HallBase{s}', (0.89 * s, -6.0, 0.06), (0.03, 10.3, 0.12), trim, bevel=0)
    # end wall with the apartment doorway (x -0.45..0.45)
    for x0, x1 in ((-0.92, -0.45), (0.45, 0.92)):
        rbox(f'EndWall{x0}', ((x0 + x1) / 2, -11.1, 1.25), (x1 - x0, 0.06, 2.6), wall, bevel=0)
    rbox('EndTop', (0, -11.1, 2.3), (0.9, 0.06, 0.5), wall, bevel=0)
    hinge = _link(bpy.data.objects.new('AptHinge', None))
    hinge.location = (-0.45, -11.1, 0)
    rbox('AptDoor', (0.45, 0, 1.03), (0.9, 0.05, 2.06), simple('AptDoorPaint', '#3B3330', rough=0.6), bevel=0.008, parent=hinge)
    # sconces (warm, dim, some flicker)
    sconce_l = []
    for i, y in enumerate((-3.0, -6.2, -9.4)):
        cyl(f'Sconce{i}', (-0.86, y, 1.9), 0.06, 0.14, simple(f'ScGlow{i}', '#FFC07A', emission=('#FFB060', 5.0)))
        L = RS.point_light(f'Key_Sconce{i}', (-0.7, y, 1.9), 25.0, color=(1.0, 0.72, 0.45), radius=0.08)
        sconce_l.append(L)
    # framed photo (left wall) + brass plaque
    frame = rbox('PhotoFrame', (-0.885, -3.6, 1.45), (0.02, 0.46, 0.58), simple('FrameWood', '#5A3A22', rough=0.5), bevel=0.01)
    photo = os.path.join(GFX, 'photo.png')
    if os.path.exists(photo):
        image_plane('Photo', photo, (0.38, 0.5), (-0.872, -3.6, 1.46), rot=(90, 0, -90), emit=0.25)
    image_plane('Plaque', os.path.join(GFX, 'plaque_13.png'), (0.14, 0.07), (-0.872, -3.6, 1.1), rot=(90, 0, -90), emit=0.2)
    # dust motes in the sconce light
    import random
    rnd = random.Random(13)
    dm = simple('Dust', '#E8D8B8', emission=('#E8D8B8', 1.5))
    for i in range(40):
        d = sphere(f'Mote{i}', (rnd.uniform(-0.8, 0.8), rnd.uniform(-10, -1.5), rnd.uniform(0.4, 2.3)), 0.006, dm, segs=6)
        for f in (0, F(END)):
            d.location.z += 0.0 if f == 0 else -0.25
            d.keyframe_insert('location', frame=f)
    return hinge, sconce_l


def apartment_set():
    warm = tex_mat('WallWarm', os.path.join(GFX, 'wallpaper_warm.png'), scale=(0.6, 0.6, 0.6), rough=0.9)
    rbox('AptFloor', (0, -13.0, -0.02), (4.0, 3.8, 0.04), simple('AptWood', '#4A3020', rough=0.6), bevel=0)
    rbox('AptBack', (0, -14.9, 1.3), (4.0, 0.06, 2.6), warm, bevel=0)
    for s in (-1, 1):
        rbox(f'AptSide{s}', (2.0 * s, -13.0, 1.3), (0.06, 3.8, 2.6), warm, bevel=0)
    rbox('AptCeil', (0, -13.0, 2.6), (4.0, 3.8, 0.05), simple('AptCeil', '#2A2018', rough=0.9), bevel=0)
    sofa = simple('Sofa', '#5B2E2A', rough=0.85)
    rbox('SofaBase', (-0.6, -13.4, 0.22), (0.8, 1.7, 0.44), sofa, bevel=0.06)
    rbox('SofaBack', (-0.95, -13.4, 0.65), (0.22, 1.7, 0.6), sofa, bevel=0.06)
    rbox('Rug', (0.3, -13.3, 0.005), (2.0, 1.6, 0.01), simple('Rug', '#3C4A5C', rough=1.0), bevel=0.01)
    rbox('TVStand', (1.75, -13.4, 0.3), (0.4, 1.2, 0.6), simple('Stand', '#2B1E16', rough=0.6), bevel=0.01)
    rbox('TVBody', (1.82, -13.4, 0.95), (0.06, 1.0, 0.6), simple('TVBlack', '#0E0E10', rough=0.3), bevel=0.01)
    image_plane('TVScreen', os.path.join(GFX, 'tv_static.png'), (0.92, 0.52), (1.785, -13.4, 0.95), rot=(90, 0, 90), emit=2.5)
    RS.area_light('Key_TV', (1.7, -13.4, 0.95), (-0.6, -13.4, 0.9), 40, size=0.8, color=(0.7, 0.85, 1.0))
    cyl('LampShade', (-1.6, -14.4, 1.3), 0.2, 0.3, simple('Shade', '#F2C88A', emission=('#FFB870', 2.5)))
    lamp = RS.point_light('Key_Lamp', (-1.5, -14.2, 1.3), 90.0, color=(1.0, 0.7, 0.42), radius=0.15)
    spill = RS.area_light('Spill', (0, -11.6, 1.2), (0, -9.0, 0.8), 0.0, size=0.8, color=(1.0, 0.7, 0.45))
    return lamp, spill


def twin_mirror(m_twin):
    """Tint the right elevator wall into a dark steel 'mirror' and light the twin standing behind it."""
    w = bpy.data.objects.get('ELV_Side1')
    g = simple('MirrorSteel', '#22282E', rough=0.15)
    p = g.node_tree.nodes['Principled BSDF']
    p.inputs['Alpha'].default_value = 0.42
    try:
        g.surface_render_method = 'BLENDED'
    except Exception:
        pass
    if w:
        w.data.materials.clear()
        w.data.materials.append(g)
    RS.area_light('Key_Twin', (1.6, -0.6, 2.0), (1.6, 0.1, 1.1), 0.0, size=0.5, color=(0.72, 0.84, 1.0))


# ============================================================================== the timeline
def build():
    sc = bpy.context.scene
    RS.world_color((0.02, 0.025, 0.035), 1.0)
    doors, disp, (b12, b13), ekey = elevator_set()
    hinge, sconces = hallway_set()
    lamp, spill = apartment_set()
    A, colA = SK.append_mascot()
    B, colB = SK.append_mascot()
    C, colC = SK.append_mascot()
    vl = bpy.context.view_layer
    vl.active_layer_collection = vl.layer_collection
    sil, colS = SK.append_character('BUSINESSMAN')
    SK.lean_character(colS, 0)
    for o in colS.objects:
        if o.type == 'MESH':
            o.data.materials.clear() if False else None
    recolor(colS, {k: '#050506' for k in ('Shirt', 'Denim', 'Hair', 'Skin', 'Shoe', 'Sock')})
    twin_mirror(C)
    # ---------- display + buttons
    vis([disp['12']], [(0, True), (F(T_FLIP), False), (F(T_FLIP2), True), (F(END), True)])
    vis([disp['13']], [(0, False), (F(T_FLIP), True), (F(5.6), True), (F(5.75), False), (F(5.95), True), (F(T_FLIP2), False)])
    vis([b13], [(0, False), (F(T_FLIP), True)])
    vis([b12], [(0, True), (F(T_FLIP), False)])
    # ---------- elevator doors: close, open at 13, slam, open on return, close
    def door(f, opened):
        for s, d in zip((-1, 1), doors):
            d.location.x = (0.335 + (0.62 if opened else 0)) * s
            d.keyframe_insert('location', frame=f)
    door(0, True); door(F(T_DCLOSE), True); door(F(T_DCLOSE + 0.9), False)
    door(F(T_DING1 + 0.1), False); door(F(T_DING1 + 1.3), True)
    door(F(T_SLAM - 0.02), True); door(F(T_SLAM + 0.22), False)
    door(F(T_DING2 + 0.05), False); door(F(T_DING2 + 0.4), True); door(F(31.9), True); door(F(32.5), False)
    # ---------- lights: flicker in the shaft, sconces flicker, lights out at the reveal
    energy(ekey, [(0, 120), (F(4.8), 120), (F(4.9), 20), (F(5.0), 120), (F(5.15), 10), (F(5.3), 120), (F(6.3), 30), (F(6.4), 120),
                  (F(T_DARK - 0.02), 120), (F(T_DARK), 0), (F(T_DING2), 0), (F(T_DING2 + 0.05), 110),
                  (F(34.9), 110), (F(35.2), 70), (F(END), 70)])
    for i, L in enumerate(sconces):
        pts = [(0, 25), (F(9.0 + i), 25), (F(9.1 + i), 4), (F(9.25 + i), 25), (F(T_DARK - 0.02), 25), (F(T_DARK), 0)]
        energy(L, pts)
    energy(lamp, [(0, 90), (F(T_DARK - 0.02), 90), (F(T_DARK), 0)])
    energy(spill, [(0, 0), (F(T_DOOR13), 0), (F(T_DOOR13 + 1.2), 60), (F(T_DARK - 0.02), 60), (F(T_DARK), 0)])
    tw = bpy.data.objects['Key_Twin']
    energy(tw, [(0, 0), (F(T_REFL), 0), (F(T_REFL + 0.4), 60)])
    hinge.rotation_euler = (0, 0, 0)
    hinge.keyframe_insert('rotation_euler', frame=F(T_DOOR13))
    hinge.rotation_euler = (0, 0, math.radians(-75))
    hinge.keyframe_insert('rotation_euler', frame=F(T_DOOR13 + 1.6))
    # ---------- the silhouette at the end of the hall: there... then gone
    place = lambda m, x, y, r: (setattr(m.rig, 'location', (x, y, 0)), setattr(m.rig, 'rotation_euler', (0, 0, math.radians(r))))
    place(sil, 0.15, -10.4, 180)
    arms_down(sil, 0, 0.2)
    vis([o for o in colS.objects], [(0, False), (F(T_DING1), True), (F(T_SLAM), True), (F(T_SLAM + 0.05), False)])
    # ---------- A (protagonist)
    arms_down(A, 0, 0.3)
    root(A, 0, -0.4, 0.3, 0)
    expr(A, 0, 'sad', 0.5, eyes=(0.0, 0.35), head=(0, 12, 0))            # tired, looking up at the display
    key(A, 0, lids=dict(up=-28, lo=8), arm_0=dict(side='R', raise_=10, forward=60, elbow=80), hand_0=dict(side='R', point=True))
    key(A, F(0.7), arm_0=dict(side='R', raise_=-30, forward=5, elbow=12), hand_0=dict(side='R', curl=0.3))
    expr(A, F(1.0), 'confused', 0.8, eyes=(0.0, 0.4), head=(8, 14, 6))
    key(A, F(1.0), lids=dict(up=-5, lo=4))
    API.blink(A, F(1.9))
    expr(A, F(2.4), 'confused', 1.0, eyes=(0.15, 0.3), head=(14, 10, 10))   # "this building only has twelve floors"
    expr(A, F(4.9), 'scared', 0.6, eyes=(0.0, 0.45), head=(0, 18, 0))        # flicker: looks at the lights
    expr(A, F(6.4), 'scared', 0.8, eyes=(0.0, 0.0), head=(0, 0, 0))
    expr(A, F(T_DING1 + 1.3), 'scared', 1.0, eyes=(0.0, 0.0))                 # doors open on the hallway
    key(A, F(T_DING1 + 1.3), spine_pose=dict(bend=-6))
    # steps out, slow and cautious
    end = API.walk(A, F(T_OUT), F(T_PHOTO - 0.2), speed=1.25, cycle=30, start_pos=(-0.4, 0.3), heading_deg=0)
    root(A, F(T_PHOTO), end[0], end[1], 0)
    expr(A, F(T_PHOTO), 'curious', 0.9, eyes=(-0.45, 0.05), head=(-35, 0, 0))   # notices the photo
    expr(A, F(T_PHOTO + 1.0), 'curious', 1.0, eyes=(-0.5, 0.1), head=(-45, 4, 0))
    expr(A, F(15.9), 'shocked', 1.0, eyes=(-0.5, 0.1), head=(-45, 4, 0))      # it's HIM
    API.blink(A, F(16.4))
    root(A, F(T_TURN - 0.05), end[0], end[1], 0)
    root(A, F(T_TURN + 0.25), end[0], end[1], 180)                           # spins round to the elevator
    expr(A, F(T_SLAM + 0.05), 'shocked', 1.0, eyes=(0.0, 0.0))
    back = API.walk(A, F(T_RUNB), F(18.3), speed=2.8, cycle=12, start_pos=end, heading_deg=180, run=True)
    root(A, F(18.35), back[0], -0.98, 180)
    for k in range(5):                                                       # pounds the button / doors
        f = F(18.4) + k * 6
        key(A, f, arm_0=dict(side='R', raise_=60, forward=80, elbow=30), hand_0=dict(side='R', fist=True), spine_pose=dict(bend=8))
        key(A, f + 3, arm_0=dict(side='R', raise_=40, forward=60, elbow=90))
    expr(A, F(18.4), 'scared', 1.0, eyes=(0.0, 0.0))
    talk(A, [w for w in TIM['words'] if w['line'] in ('D1', 'D2')], 0.0)
    expr(A, F(T_DOOR13), 'scared', 0.9, eyes=(0.0, 0.0), head=(0, 0, 0))
    root(A, F(T_DOOR13 + 0.3), back[0], -0.98, 180)
    root(A, F(T_DOOR13 + 0.9), back[0], -0.98, 0)                            # turns: the far door is open
    end2 = API.walk(A, F(T_WALK2), F(T_PEEK - 0.1), speed=2.85, cycle=30, start_pos=(back[0], -0.98), heading_deg=0)
    end2 = (0.05, -10.85)
    root(A, F(T_PEEK), *end2, 0)
    key(A, F(T_PEEK), spine_pose=dict(bend=10), arm_0=dict(side='L', raise_=30, forward=50, elbow=60))
    expr(A, F(T_PEEK), 'scared', 0.8, eyes=(0.2, 0.0))
    expr(A, F(T_STAND), 'scared', 1.0, eyes=(0.0, 0.0))
    # back in the elevator: stumbles in, presses, exhales, then freezes at the mirror
    root(A, F(T_DING2), 0.0, -1.6, 180)
    stumble = API.walk(A, F(T_DING2 + 0.35), F(31.3), speed=2.2, cycle=14, start_pos=(0.0, -1.6), heading_deg=180, run=True)
    root(A, F(31.35), 0.55, -0.35, 90)
    for k in range(4):
        f = F(31.4) + k * 5
        key(A, f, arm_0=dict(side='R', raise_=40, forward=70, elbow=40), hand_0=dict(side='R', point=True), spine_pose=dict(bend=6))
        key(A, f + 2, arm_0=dict(side='R', raise_=30, forward=55, elbow=70))
    expr(A, F(31.4), 'scared', 1.0, eyes=(0.0, 0.0))
    root(A, F(32.6), 0.55, -0.35, 90)
    root(A, F(33.0), 0.45, 0.2, 0)
    key(A, F(32.7), spine_pose=dict(bend=10), arm_0=dict(side='R', raise_=-30, forward=5, elbow=12))   # exhale
    expr(A, F(32.7), 'sad', 0.8, eyes=(0.0, -0.2))
    expr(A, F(T_CLOCK), 'curious', 0.9, eyes=(0.0, 0.45), head=(0, 18, 0))   # the clock: 11:48
    expr(A, F(T_BTN), 'scared', 0.9, eyes=(0.45, 0.0), head=(35, 0, 0))      # the 13 button is still lit
    root(A, F(T_REFL), 0.45, 0.2, 0)
    root(A, F(T_REFL + 0.5), 0.45, 0.2, 90)                                   # faces the steel wall
    expr(A, F(T_REFL + 0.5), 'scared', 0.7, eyes=(0.0, 0.0), head=(0, 0, 0))
    expr(A, F(END), 'scared', 0.7, eyes=(0.0, 0.0), head=(0, 0, 0))         # frozen, does NOT smile
    # ---------- B: the double on the couch
    arms_down(B, 0, 0.3)
    B.rig.location = (-0.45, -13.3, 0)
    B.rig.rotation_euler = (0, 0, math.radians(90))                          # faces the TV (+X)
    key(B, 0, loc=('hips', 0, -0.26, 0), spine_pose=dict(bend=-6), arm_0=dict(side='L', raise_=-20, forward=30, elbow=60),
        arm_1=dict(side='R', raise_=-20, forward=30, elbow=60))
    expr(B, 0, 'neutral', 1.0, eyes=(0.0, 0.0))
    key(B, 0, lids=dict(up=-12, lo=4))
    expr(B, F(T_HEAD), 'neutral', 1.0, eyes=(0.0, 0.0), head=(0, 0, 0))
    expr(B, F(T_HEAD + 1.0), 'neutral', 1.0, eyes=(0.5, 0.0), head=(70, 0, 0))     # slowly turns his head to us
    key(B, F(T_STAND), loc=('hips', 0, -0.26, 0))
    B.rig.keyframe_insert('rotation_euler', frame=F(T_STAND))
    B.rig.keyframe_insert('location', frame=F(T_STAND))
    key(B, F(T_STAND + 0.9), loc=('hips', 0, 0, 0), spine_pose=dict(bend=0))
    B.rig.location = (-0.2, -13.0, 0)
    B.rig.rotation_euler = (0, 0, math.radians(165))                         # stands facing him (+Y)
    B.rig.keyframe_insert('location', frame=F(T_STAND + 0.9))
    B.rig.keyframe_insert('rotation_euler', frame=F(T_STAND + 0.9))
    expr(B, F(T_STAND + 0.9), 'happy', 0.35, eyes=(0.0, 0.0), head=(0, 0, 0))     # calm, faint smile
    key(B, F(T_STAND + 0.9), lids=dict(up=-8, lo=6))
    talk(B, [w for w in TIM['words'] if w['line'] == 'D3'], 0.0, amount=0.6)
    vis([o for o in colB.objects if o.type == 'MESH'], [(0, True), (F(T_DARK), False)])
    # ---------- C: the reflection twin (mirrored, behind the tinted wall)
    arms_down(C, 0, 0.3)
    C.rig.location = (1.59, 0.2, 0)
    C.rig.rotation_euler = (0, 0, math.radians(-90))                          # faces back toward A (mirror)
    C.rig.scale = (-1, 1, 1)
    expr(C, F(T_REFL), 'scared', 0.7, eyes=(0.0, 0.0))
    expr(C, F(T_SMILE - 0.3), 'scared', 0.7, eyes=(0.0, 0.0))
    expr(C, F(T_SMILE + 0.5), 'happy', 1.0, eyes=(0.0, 0.0), head=(0, -4, 6))      # the reflection SMILES
    key(C, F(T_SMILE + 0.5), lids=dict(up=-14, lo=12))
    vis([o for o in colC.objects if o.type == 'MESH'], [(0, False), (F(T_REFL), True)])
    toon.toonify(sc)
    return A, B, C


def cameras():
    cams = {}

    def mk(name, loc, look, lens):
        c, t = SK.cam_rig(name, lens=lens)
        c.location, t.location = loc, look
        cams[name] = (c, t)
        return c, t
    mk('CAM_DISP', (0.0, 0.2, 2.0), (0.0, -0.8, 2.08), 70)                  # LED display CU (hook + flips)
    c, t = mk('CAM_ELEV_MED', (-0.55, -0.7, 1.55), (0.15, 0.3, 1.05), 26)  # him in the elevator (front-left, high)
    c, t = mk('CAM_FACE', (0.05, -0.55, 1.18), (0.1, 0.25, 1.15), 40)      # his face (from the doors)
    c, t = mk('CAM_OUT', (0.35, 0.75, 1.35), (0.0, -6.0, 1.2), 30)         # inside the elevator looking out (reveal)
    SK.key_cam(c, t, F(T_DING1), (0.35, 0.75, 1.35), (0.0, -6.0, 1.2), lens=30)
    SK.key_cam(c, t, F(T_OUT), (0.35, 0.4, 1.35), (0.0, -6.0, 1.2), lens=34)
    c, t = mk('CAM_TRACK', (0.25, 0.6, 1.5), (-0.4, -1.0, 1.1), 28)         # follows him out (behind, OTS)
    SK.key_cam(c, t, F(T_OUT), (0.3, 0.6, 1.5), (-0.4, -1.0, 1.1), lens=28)
    SK.key_cam(c, t, F(T_PHOTO), (0.35, -1.6, 1.5), (-0.6, -3.6, 1.3), lens=28)
    mk('CAM_PHOTO', (-0.35, -3.6, 1.45), (-0.88, -3.6, 1.45), 40)          # the photograph
    mk('CAM_EYES', (-0.75, -3.25, 1.2), (-0.4, -2.65, 1.15), 45)             # his eyes on recognising himself
    c, t = mk('CAM_HALL', (0.35, -2.0, 1.25), (0.0, 0.0, 1.2), 26)         # looks back at the elevator (slam)
    mk('CAM_DOORSIDE', (0.6, -2.2, 1.6), (0.0, -0.95, 1.2), 24)            # him pounding the doors (handheld in edit)
    c, t = mk('CAM_LONG', (0.2, -0.6, 1.5), (0.0, -11.0, 1.1), 30)         # down the hallway: the far door opens
    SK.key_cam(c, t, F(T_DOOR13), (0.2, -0.6, 1.5), (0.0, -11.0, 1.1), lens=30)
    SK.key_cam(c, t, F(T_PEEK), (0.2, -7.0, 1.5), (0.0, -11.0, 1.1), lens=30)
    c, t = mk('CAM_OTS', (0.35, -10.1, 1.5), (-0.2, -13.2, 0.9), 28)       # over his shoulder into the apartment
    SK.key_cam(c, t, F(T_PEEK), (0.35, -10.1, 1.5), (-0.2, -13.2, 0.9), lens=28)
    SK.key_cam(c, t, F(T_STAND), (0.3, -10.4, 1.45), (-0.3, -13.2, 1.0), lens=36)
    mk('CAM_DOUBLE', (0.55, -11.7, 1.18), (-0.2, -13.0, 1.15), 45)         # the double, CU: "You're late... again."
    mk('CAM_IN', (0.0, 0.65, 1.3), (0.0, -1.5, 1.1), 26)                   # inside: he stumbles back in
    mk('CAM_BTN', (0.55, -0.47, 1.44), (0.975, -0.5, 1.41), 45)               # the lit 13 button
    c, t = mk('CAM_MIRROR', (-0.1, 0.75, 1.4), (1.2, -0.05, 1.15), 24)    # over his shoulder at the steel wall: him + reflection
    SK.key_cam(c, t, F(T_REFL), (-0.1, 0.75, 1.4), (1.2, -0.05, 1.15), lens=24)
    SK.key_cam(c, t, F(T_BLACK), (0.15, 0.62, 1.35), (1.45, 0.05, 1.18), lens=32)
    return cams


JOBS = {   # job: (camera, video t0, video t1, hidden: 'B','C' etc.)
    'DISP':    ('CAM_DISP', 0.0, 6.4),
    'ELEV':    ('CAM_ELEV_MED', 0.9, 2.5),
    'FACE':    ('CAM_FACE', 2.3, 7.2),
    'OUT':     ('CAM_OUT', 6.9, 12.2),
    'TRACK':   ('CAM_TRACK', 11.9, 15.2),
    'PHOTO':   ('CAM_PHOTO', 14.9, 16.5),
    'EYES':    ('CAM_EYES', 15.8, 17.0),
    'HALL':    ('CAM_HALL', 16.8, 18.0),
    'DOORSIDE':('CAM_DOORSIDE', 17.9, 20.5),
    'LONG':    ('CAM_LONG', 20.3, 23.4),
    'OTS':     ('CAM_OTS', 23.3, 28.2),
    'DOUBLE':  ('CAM_DOUBLE', 27.9, 30.0),
    'IN':      ('CAM_IN', 30.3, 32.5),
    'DISP2':   ('CAM_DISP', 32.3, 34.4),
    'BTN':     ('CAM_BTN', 34.2, 35.1),
    'MIRROR':  ('CAM_MIRROR', 34.9, 37.9),
    'PHOTOGEN': ('CAM_PHOTOGEN', 0.0, 0.1),
}


def frames_of(job):
    _, t0, t1 = JOBS[job]
    return F(t0), F(t1) + 1


SHOTS = {j: ('MAIN', JOBS[j][0], frames_of(j), 'all', 1.0) for j in JOBS}


def build_shot(sid):
    sc = bpy.context.scene
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 1
    if sid == 'PHOTOGEN':                                                    # the photograph on the wall: him, blue shirt, same hallway
        hallway_set()
        RS.world_color((0.02, 0.025, 0.035), 1.0)
        m, col = SK.append_mascot()
        recolor(col, {'Shirt': '#2F6FD0'})
        arms_down(m, 0, 0.3)
        expr(m, 0, 'neutral', 1.0, eyes=(0.0, 0.0))
        m.rig.location = (0.0, -6.0, 0)
        m.rig.rotation_euler = (0, 0, math.radians(180))                    # faces the camera
        RS.area_light('Key_Flash', (0.0, -4.4, 1.6), (0, -6.0, 1.1), 60, size=0.4)
        c, t = SK.cam_rig('CAM_PHOTOGEN', lens=40)
        c.location, t.location = (0.0, -4.1, 1.35), (0.0, -6.0, 1.0)
        sc.camera = c
        toon.toonify(sc)
        sc.frame_start = sc.frame_end = 0
        return {'frames': (0, 1), 'step': 1}
    build()
    cams = cameras()
    sc.camera = cams[JOBS[sid][0]][0]
    f0, f1 = frames_of(sid)
    sc.frame_start, sc.frame_end = f0, f1 - 1
    return {'frames': (f0, f1), 'step': 1}

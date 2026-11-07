"""VIDEO_004 — "What If Gravity Disappeared for 10 Seconds?"

One continuous STREET timeline. Timeline frame = P + video frame. Frames 0..P-1 are the calm
ending (same street, same camera as video frame 0), so the last video frame flows straight into
frame 0, where everybody's feet leave the ground.
Physics used (story time is slowed: 10 s of zero-g fills video 0 -> T_G):
  * standing people push off gently (legs/spine decompress): ~0.15 m/s up
  * the mascot JUMPS when he shouts "I'm flying": 0.7 m/s, so he's ~16 m up when gravity returns
  * nothing "falls up": loose things keep the velocity they had; fountain jets keep rising
  * gravity back: everything falls together (g slowed in the edit for readability)
Render: EEVEE 1 sample + OpenImageDenoise, AgX (normal colour), only the frames the edit shows.
"""
import json
import math
import os
import random

import bpy
from mathutils import Vector

from studio_lib import scene_kit as SK, render_setup as RS, mascot_api as API
from studio_lib.materials import hex_rgb, simple
from video002 import key, expr, arms_down, recolor, place, cam
from video003 import cylinder, image_plane, talk

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIDEO_DIR = os.path.join(STUDIO, 'VIDEOS', 'VIDEO_004')
GFX = os.path.join(VIDEO_DIR, 'gfx')
TIM = json.load(open(os.path.join(VIDEO_DIR, 'audio', 'narration', 'timing.json')))
LS = {l['id']: (l['start'], l['end']) for l in TIM['lines']}
FPS = 30
P = 100                                   # calm prelude frames = the ending
END = 33.6
T_JUMP = 3.75                             # he pushes off during "I'm flying?!"
T_G = LS['L10'][0] + 0.75                 # gravity returns on "...back"
T_LAND = T_G + 2.6                        # mascot lands on the mattresses
T_BONK = LS['L11'][1] + 0.35              # his phone finally comes down
T_RESET = 30.55                           # jump-cut: standing on his mark again
MARK = Vector((0.0, 0.0, 0.0))
PILE = Vector((2.25, 0.85, 0.0))          # mattress display in front of MATTRESS KING
PILE_TOP = 0.95
G_SLOW = 2 * 16.0 / (T_LAND - T_G) ** 2   # edit-time gravity so a 16 m fall takes 2.6 s


def F(t):
    return int(round(P + t * FPS))


def drift_z(t, v=0.15):
    return v * max(0.0, t)


def fall_z(z0, t):
    return max(0.0, z0 - 0.5 * G_SLOW * max(0.0, t - T_G) ** 2)


def mascot_pos(t):
    """Mascot world position at video time t (rig root)."""
    if t < 0 or t >= T_RESET:
        return MARK.copy()
    zt = drift_z(min(t, T_JUMP)) + 0.7 * max(0.0, min(t, T_G) - T_JUMP)
    u = min(1.0, max(0.0, (min(t, T_G) - T_JUMP) / (T_G - T_JUMP)))
    x = MARK.x + (PILE.x - MARK.x) * (u * u * (3 - 2 * u))
    y = MARK.y + (PILE.y - MARK.y) * (u * u * (3 - 2 * u))
    if t < T_G:
        return Vector((x, y, zt))
    zg = drift_z(T_JUMP) + 0.7 * (T_G - T_JUMP)
    z = max(PILE_TOP + 0.04, zg - 0.5 * G_SLOW * (t - T_G) ** 2)
    return Vector((PILE.x, PILE.y, z))


def mat(name, color, **kw):
    return simple(name, color, **kw)


def box(name, loc, size, m, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.data.materials.append(m)
    if bevel:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bv = o.modifiers.new('bv', 'BEVEL')
        bv.width = bevel
        bv.segments = 3
        bpy.ops.object.shade_smooth()
    return o


def textured_box(name, loc, size, img):
    o = box(name, loc, size, bpy.data.materials.new(name))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)          # object coords in metres -> real window size
    m = o.data.materials[0]
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(img, check_existing=True)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (0.083, 0.083, 0.042)   # one texture tile = 12 m wide, 24 m tall (3 m floors)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    tx.projection = 'BOX'
    nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    nt.links.new(tx.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.8
    return o


def keyz(ob, t_list, fn, path='location'):
    for t in t_list:
        ob.location = fn(t)
        ob.keyframe_insert(path, frame=F(t))


def times(a, b, step=0.2):
    n = max(1, int((b - a) / step))
    return [a + (b - a) * i / n for i in range(n + 1)]


# ============================================================================== street set
def street():
    sc = bpy.context.scene
    vs = sc.view_settings
    vs.view_transform, vs.look, vs.exposure = 'AgX', 'None', 0.0
    RS.world_gradient((0.18, 0.38, 0.78), (0.55, 0.70, 0.90), (0.3, 0.3, 0.32), 0.8)
    walk = mat('Sidewalk', '#9C978F', rough=0.85)
    road = mat('Asphalt', '#3A3B3F', rough=0.9)
    white = mat('Paint', '#ECECE6', rough=0.6)
    box('Sidewalk', (0, 1.5, -0.06), (40, 9, 0.12), walk)
    box('Road', (0, -5.5, -0.12), (40, 6, 0.12), road)
    box('Curb', (0, -2.95, -0.04), (40, 0.18, 0.16), white)
    for i in range(-6, 7):
        box(f'Stripe{i}', (i * 2.0, -5.5, -0.055), (1.0, 0.12, 0.01), white)
    for i, (x, img, h) in enumerate(((-7.5, 'facade_a', 14), (-2.6, 'facade_b', 11), (7.2, 'facade_c', 16))):
        textured_box(f'Bldg{i}', (x, 7.5, h / 2), (4.6, 5, h), os.path.join(GFX, img + '.png'))
    # MATTRESS KING storefront right behind the mattress pile
    shop = textured_box('Shop', (2.4, 7.5, 3.5), (4.8, 5, 7.0), os.path.join(GFX, 'facade_b.png'))
    image_plane('ShopSign', os.path.join(GFX, 'sign_mattress.png'), (3.6, 0.9), (2.4, 4.97, 3.1), rot=(90, 0, 0), emit=0.6)
    glass = mat('ShopGlass', '#7FA7C4', rough=0.1, metallic=0.2)
    box('ShopWindow', (2.4, 4.98, 1.25), (3.8, 0.02, 2.0), glass)
    # streetlight next to the mascot
    pole = mat('Pole', '#2F3A40', rough=0.4, metallic=0.6)
    cylinder('Pole', (-1.0, 0.9, 2.2), 0.06, 4.4, pole)
    box('Arm', (-0.55, 0.9, 4.35), (0.9, 0.06, 0.06), pole)
    cylinder('Lamp', (-0.15, 0.9, 4.25), 0.16, 0.12, mat('LampGlass', '#FFF6D8', emission=('#FFF2C0', 1.5)))
    RS.area_light('KeySun', (-6, -8, 12), (0, 1, 1), 1000, size=6.0, color=(1.0, 0.96, 0.9))
    RS.area_light('Fill', (6, -6, 4), (0, 1, 1.2), 160, size=5.0, color=(0.85, 0.9, 1.0))


def car(name, loc, color):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = loc
    paint = mat(name + 'Paint', color, rough=0.3, coat=0.8)
    dark = mat(name + 'Glass', '#20262C', rough=0.1)
    tire = mat(name + 'Tire', '#151515', rough=0.8)
    parts = [box(name + 'Body', (0, 0, 0.55), (3.9, 1.75, 0.65), paint, bevel=0.12),
             box(name + 'Cabin', (-0.2, 0, 1.1), (2.1, 1.6, 0.55), paint, bevel=0.15),
             box(name + 'Win', (-0.2, 0, 1.12), (2.15, 1.62, 0.42), dark, bevel=0.1)]
    for sx in (-1.3, 1.3):
        for sy in (-0.85, 0.85):
            w = cylinder(name + 'Wheel', (sx, sy, 0.36), 0.36, 0.25, tire)
            w.rotation_euler.x = math.radians(90)
            parts.append(w)
    for p in parts:
        p.parent = root
    return root


def mattress(name, loc, m, rot=0.0):
    o = box(name, loc, (1.9, 1.3, 0.24), m, bevel=0.06, rot=(0, 0, rot))
    return o


# ============================================================================== the scene
def build():
    street()
    cast = {}
    m, col = SK.append_mascot()
    cast['MASCOT'] = (m, col)
    for n in ('GRANDMA', 'BUSINESSMAN', 'KID'):
        mm, cc = SK.append_character(n)
        SK.lean_character(cc, 0)
        cast[n] = (mm, cc)
    M, G, B, K = (cast[n][0] for n in ('MASCOT', 'GRANDMA', 'BUSINESSMAN', 'KID'))
    vl = bpy.context.view_layer
    vl.active_layer_collection = vl.layer_collection      # props go in the scene, not in a cast collection
    homes = {'GRANDMA': (-2.2, 1.8, 15), 'BUSINESSMAN': (-1.9, 1.0, 35), 'KID': (1.0, 2.4, -20)}
    for n, (x, y, r) in homes.items():
        place(cast[n][0], x, y, r)
    place(M, MARK.x, MARK.y, 0)
    rnd = random.Random(7)
    # ---------------- mascot performance
    arms_down(M, 0, 0.3)
    key(M, 0, arm_0=dict(side='R', raise_=-5, forward=55, elbow=95, wrist=-10), hand_0=dict(side='R', curl=0.7, thumb=0.5))
    expr(M, 0, 'happy', 0.3, eyes=(0.0, -0.3), head=(0, -12, 0))            # prelude: rubbing head after the bonk...
    key(M, 2, arm_1=dict(side='L', raise_=60, forward=40, elbow=130), hand_1=dict(side='L', curl=0.4))
    expr(M, 2, 'sad', 0.6, eyes=(0.0, 0.25), head=(0, 10, 0))                 # ...looking up at the sky (L12)
    for f in range(8, 60, 10):
        key(M, f, arm_1=dict(side='L', raise_=60 + (6 if (f // 10) % 2 else -4), forward=40, elbow=130))
    key(M, 70, arm_1=dict(side='L', raise_=-32, forward=4, elbow=12), hand_1=dict(side='L', curl=0.3))
    expr(M, 72, 'neutral', 1.0, eyes=(0.0, -0.3), head=(0, -12, 0))          # back to his phone = frame 0 pose
    expr(M, P - 1, 'neutral', 1.0, eyes=(0.0, -0.3), head=(0, -12, 0))
    # video 0: feet leave the ground, he notices
    expr(M, F(0.5), 'surprised', 0.8, eyes=(0.0, -0.4), head=(0, -18, 0))     # looks at his feet
    key(M, F(0.5), arm_0=dict(side='R', raise_=10, forward=40, elbow=40), hand_0=dict(side='R', spread=1.0))   # phone slips away
    key(M, F(1.2), arm_1=dict(side='L', raise_=35, forward=10, elbow=20), arm_0=dict(side='R', raise_=35, forward=10, elbow=20))
    expr(M, F(1.6), 'scared', 0.8, eyes=(0.2, 0.0))
    expr(M, F(2.9), 'excited', 1.0, eyes=(0.0, 0.1))                        # "Wait... I'm FLYING?!"
    key(M, F(3.45), spine_pose=dict(bend=12), loc=('hips', 0, -0.06, 0))      # crouch...
    key(M, F(T_JUMP), spine_pose=dict(bend=-10), loc=('hips', 0, 0.02, 0),    # ...and the fatal jump
        arm_0=dict(side='L', raise_=150, forward=10, elbow=15), arm_1=dict(side='R', raise_=150, forward=10, elbow=15))
    for k, t in enumerate(times(4.4, 16.0, 0.9)):                            # superhero / swimming joy
        key(M, F(t), arm_0=dict(side='L', raise_=95 + 25 * (k % 2), forward=20, elbow=20),
            arm_1=dict(side='R', raise_=120 - 25 * (k % 2), forward=20, elbow=20), spine_pose=dict(bend=-4 + 6 * (k % 2)))
        expr(M, F(t), 'laughing' if k % 3 == 0 else 'excited', 0.9)
    expr(M, F(LS['L06'][0] + 0.3), 'curious', 0.9, eyes=(0.0, -0.45), head=(0, -25, 0))   # looks down: oh no
    expr(M, F(LS['L06'][1] + 0.1), 'scared', 1.0, eyes=(0.0, -0.5), head=(0, -28, 0))
    for k, t in enumerate(times(LS['L07'][0], 23.4, 0.22)):                # panic air-swim
        key(M, F(t), arm_0=dict(side='L', raise_=60 + 50 * (k % 2), forward=30, elbow=40),
            arm_1=dict(side='R', raise_=110 - 50 * (k % 2), forward=30, elbow=40))
        expr(M, F(t), 'shocked' if k % 2 else 'scared', 1.0, eyes=(0.0, -0.3))
    expr(M, F(LS['L09'][1]), 'scared', 1.0, eyes=(0, 0.0))                     # silence: frozen, eyes wide
    key(M, F(LS['L09'][1]), arm_0=dict(side='L', raise_=20, forward=10, elbow=10), arm_1=dict(side='R', raise_=20, forward=10, elbow=10))
    key(M, F(T_G), arm_0=dict(side='L', raise_=170, forward=0, elbow=5), arm_1=dict(side='R', raise_=170, forward=0, elbow=5))
    expr(M, F(T_G + 0.1), 'shocked', 1.0, eyes=(0, 0.3), head=(0, 15, 0))     # falling, screaming
    # landing: flips onto his back on the pile
    M.rig.rotation_euler = (0, 0, 0)
    M.rig.keyframe_insert('rotation_euler', frame=F(T_LAND - 0.35))
    M.rig.rotation_euler = (math.radians(-80), 0, math.radians(15))
    M.rig.keyframe_insert('rotation_euler', frame=F(T_LAND))
    M.rig.keyframe_insert('rotation_euler', frame=F(T_RESET - 0.04))
    M.rig.rotation_euler = (0, 0, 0)
    M.rig.keyframe_insert('rotation_euler', frame=F(T_RESET))
    for fr in (F(T_RESET - 0.04), F(T_RESET)):
        API.set_interp(M.rig, 'CONSTANT', fr)
    key(M, F(T_LAND), arm_0=dict(side='L', raise_=80, forward=-10, elbow=10), arm_1=dict(side='R', raise_=80, forward=-10, elbow=10))
    expr(M, F(T_LAND), 'shocked', 1.0, eyes=(0, 0))
    expr(M, F(T_LAND + 0.5), 'sad', 0.5, eyes=(0.0, 0.1))
    expr(M, F(LS['L11'][0] + 0.3), 'happy', 0.6, eyes=(0.0, 0.05))            # relieved
    expr(M, F(T_BONK), 'shocked', 1.0, eyes=(0.25, -0.25))                    # BONK
    key(M, F(T_BONK), shape=('cheek_puff', 0.0))
    expr(M, F(T_BONK + 0.4), 'angry', 0.6, eyes=(0.0, 0.3))                   # glares up at the sky
    talk(M, [w for w in TIM['words'] if w['line'] in ('L02', 'L07', 'L08', 'L11')], 0.0, offset=P)
    # mascot root path (prelude + reset = on his mark)
    for t in [-P / FPS, -0.04] + times(0, T_LAND + 0.2, 0.1):
        M.rig.location = mascot_pos(t)
        M.rig.keyframe_insert('location', frame=F(t))
    M.rig.location = PILE + Vector((0, 0, PILE_TOP + 0.04))
    M.rig.keyframe_insert('location', frame=F(T_RESET - 0.04))
    M.rig.location = MARK
    M.rig.keyframe_insert('location', frame=F(T_RESET))
    M.rig.keyframe_insert('location', frame=F(END))
    API.set_interp(M.rig, 'CONSTANT', F(T_RESET - 0.04))
    # ---------------- extras: everyone floats up gently, sneezes, lands with a thud
    def float_path(mm, home, t_sneeze=None):
        x0, y0, _ = home
        def pos(t):
            if t < 0 or t >= T_RESET:
                return Vector((x0, y0, 0))
            z = drift_z(min(t, T_G))
            y = y0 + (0.55 * max(0.0, min(t, T_G) - t_sneeze) if t_sneeze else 0.0)
            return Vector((x0, y, fall_z(z, t) if t > T_G else z))
        for t in [-P / FPS, -0.04] + times(0, T_G + 1.6, 0.15) + [T_RESET - 0.04, T_RESET, END]:
            mm.rig.location = pos(t)
            mm.rig.keyframe_insert('location', frame=F(t))
        for fr in (F(T_RESET - 0.04),):
            API.set_interp(mm.rig, 'CONSTANT', fr)
    for n, mm in (('GRANDMA', G), ('BUSINESSMAN', B), ('KID', K)):
        arms_down(mm, 0, 0.3)
        expr(mm, 0, 'neutral', 0.0)
        float_path(mm, homes[n], 6.35 if n == 'BUSINESSMAN' else None)
        arms_down(mm, P, 0.3)                              # calm until video frame 0
        expr(mm, P, 'neutral', 0.0)
        expr(mm, F(0.8), 'surprised', 0.9, eyes=(0, -0.3))
        key(mm, F(1.5), arm_0=dict(side='L', raise_=70, forward=20, elbow=30), arm_1=dict(side='R', raise_=70, forward=20, elbow=30))
        expr(mm, F(T_G + 0.25), 'shocked', 1.0)
        key(mm, F(T_G + 0.9), loc=('hips', 0, -0.12, 0), spine_pose=dict(bend=20))   # THUD squash
        key(mm, F(T_G + 1.2), loc=('hips', 0, 0, 0), spine_pose=dict(bend=0))
        expr(mm, F(T_G + 1.4), 'confused', 0.9)
        expr(mm, F(T_RESET - 0.04), 'confused', 0.9)
        expr(mm, F(T_RESET), 'neutral', 0.0)
        for fr in (F(T_RESET),):
            API.set_interp(mm.rig, 'CONSTANT', fr)
    # grandma reads the paper upside down, totally unbothered
    expr(G, F(2.0), 'neutral', 1.0, eyes=(0, -0.25))
    key(G, F(2.0), arm_0=dict(side='L', raise_=10, forward=60, elbow=80), arm_1=dict(side='R', raise_=10, forward=60, elbow=80))
    G.rig.rotation_euler = (0, 0, math.radians(15))
    G.rig.keyframe_insert('rotation_euler', frame=F(1.0))
    G.rig.rotation_euler = (math.radians(-150), 0, math.radians(30))
    G.rig.keyframe_insert('rotation_euler', frame=F(T_G))
    G.rig.rotation_euler = (0, 0, math.radians(15))
    G.rig.keyframe_insert('rotation_euler', frame=F(T_G + 0.6))
    paper = image_plane('Paper', os.path.join(GFX, 'sign_mattress.png'), (0.42, 0.3), (0, 0, 0), rot=(0, 0, 0))
    paper.hide_render = True
    # businessman: coffee blob escapes the cup, then the sneeze launches him backwards
    t_sn = 6.35
    expr(B, F(t_sn - 0.5), 'thinking', 1.0, eyes=(0, 0.3), head=(0, 12, 0))   # ah... ah...
    key(B, F(t_sn - 0.5), spine_pose=dict(bend=-12))
    expr(B, F(t_sn), 'shocked', 1.0, eyes=(0, 0))                            # CHOO
    key(B, F(t_sn), spine_pose=dict(bend=25))
    B.rig.rotation_euler = (0, 0, math.radians(35))
    B.rig.keyframe_insert('rotation_euler', frame=F(t_sn))
    B.rig.rotation_euler = (math.radians(-40), 0, math.radians(35))
    B.rig.keyframe_insert('rotation_euler', frame=F(T_G))
    B.rig.rotation_euler = (0, 0, math.radians(35))
    B.rig.keyframe_insert('rotation_euler', frame=F(T_G + 0.7))
    coffee = mat('Coffee', '#5A3418', rough=0.15, coat=0.6)
    cup = cylinder('Cup', (-1.75, 0.78, 1.2), 0.045, 0.12, mat('CupWhite', '#F0EEE8'))
    blob = bpy.data.objects.new('CoffeeBlob', None)
    bpy.context.scene.collection.objects.link(blob)
    for i in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05 - 0.012 * i, location=(0.06 * i, 0.02 * i, 0.05 * i))
        s = bpy.context.object
        s.data.materials.append(coffee)
        bpy.ops.object.shade_smooth()
        s.parent = blob
    keyz(cup, [-P / FPS, 0, T_G, T_G + 0.7, T_RESET - 0.04, T_RESET],
         lambda t: Vector((-1.75, 0.78, 1.2 + drift_z(min(max(t, 0), T_G)) if t < T_RESET else 1.2)) if t <= T_G else Vector((-1.75, 1.2, 0.05)))
    keyz(blob, times(0, T_G, 0.5), lambda t: Vector((-1.75 + 0.05 * t, 0.78 - 0.02 * t, 1.28 + 0.22 * t)))
    keyz(blob, [T_G + 1.2], lambda t: Vector((-1.2, -0.9, 0.0)))
    blob.hide_render = True
    blob.keyframe_insert('hide_render', frame=0)
    blob.hide_render = False
    blob.keyframe_insert('hide_render', frame=F(0.2))
    blob.hide_render = True
    blob.keyframe_insert('hide_render', frame=F(T_G + 1.2))
    # ---------------- phones: one in his hand (prelude/start/end), one flying (flung up when he jumps)
    hand_phone = box('PhoneHand', (0, 0, 0), (0.07, 0.012, 0.14), mat('PhoneBlack', '#111114', rough=0.3), bevel=0.01)
    con = hand_phone.constraints.new('CHILD_OF')
    con.target = M.rig
    con.subtarget = 'hand.R'
    con.inverse_matrix.identity()
    hand_phone.location = (0.0, 0.06, 0.02)
    hand_phone.rotation_euler = (math.radians(-70), 0, 0)
    fly = box('PhoneFly', (0, 0, 0), (0.07, 0.012, 0.14), mat('PhoneBlack2', '#111114', rough=0.3), bevel=0.01)
    for o, on in ((hand_phone, [(0, True), (F(0.4), False), (F(T_RESET), True)]), (fly, [(0, False), (F(0.4), True), (F(T_BONK + 0.4), False)])):
        for fr, vis in on:
            o.hide_render = not vis
            o.keyframe_insert('hide_render', frame=fr)
    head_on_pile = PILE + Vector((0.0, 0.6, PILE_TOP + 0.3))

    def phone_pos(t):
        p0 = Vector((0.18, -0.25, 1.0))
        if t < T_JUMP:
            return p0 + Vector((0.02 * t, -0.01 * t, 0.12 * t))
        zj = (p0 + Vector((0, 0, 0.12 * T_JUMP))).z
        if t < T_G:
            return Vector((0.18 + (head_on_pile.x - 0.18) * (t - T_JUMP) / (T_G - T_JUMP),
                           -0.25 + (head_on_pile.y + 0.25) * (t - T_JUMP) / (T_G - T_JUMP), zj + 3.7 * (t - T_JUMP)))
        ztop = zj + 3.7 * (T_G - T_JUMP)
        g = 2 * (ztop - head_on_pile.z) / (T_BONK - T_G) ** 2
        return Vector((head_on_pile.x, head_on_pile.y, max(head_on_pile.z, ztop - 0.5 * g * (t - T_G) ** 2)))
    keyz(fly, times(0.4, T_BONK + 0.4, 0.1), phone_pos)
    fly.rotation_euler = (0, 0, 0)
    fly.keyframe_insert('rotation_euler', frame=F(0.4))
    fly.rotation_euler = (math.radians(900), math.radians(400), 0)
    fly.keyframe_insert('rotation_euler', frame=F(T_BONK))
    # ---------------- car, fountain, mattresses
    c = car('Car', (4.2, -5.0, 0), '#C8312B')
    keyz(c, [-P / FPS, 0] + times(0, T_G + 1.2, 0.2) + [T_RESET - 0.04, T_RESET],
         lambda t: Vector((4.2, -5.0, 0 if (t <= 0 or t >= T_RESET) else (0.12 * min(t, T_G) if t <= T_G else fall_z(0.12 * T_G, t)))))
    c.rotation_euler = (0, 0, 0)
    c.keyframe_insert('rotation_euler', frame=F(0))
    c.rotation_euler = (math.radians(6), math.radians(-9), math.radians(4))
    c.keyframe_insert('rotation_euler', frame=F(T_G))
    c.rotation_euler = (0, 0, 0)
    c.keyframe_insert('rotation_euler', frame=F(T_G + 1.0))
    basin = cylinder('Basin', (4.6, 2.6, 0.25), 0.9, 0.5, mat('Stone', '#C9C2B6', rough=0.8))
    water = mat('Water', '#4FA3D8', rough=0.05, coat=1.0)
    for i in range(14):                                # fountain jet keeps going up (nothing pulls it back)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=rnd.uniform(0.06, 0.13), location=(4.6, 2.6, 0.6))
        b = bpy.context.object
        b.data.materials.append(water)
        bpy.ops.object.shade_smooth()
        t0 = -1.0 + i * 0.6
        vx, vy = rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08)
        keyz(b, times(0, T_G + 1.2, 0.3), lambda t, t0=t0, vx=vx, vy=vy: Vector((
            4.6 + vx * max(0, t - t0), 2.6 + vy * max(0, t - t0),
            (0.6 + 1.2 * max(0.0, min(t, T_G) - max(t0, -1.0))) if t <= T_G else fall_z(0.6 + 1.2 * (T_G - max(t0, -1.0)), t) + 0.45)))
        b.hide_render = True
        b.keyframe_insert('hide_render', frame=0)
        b.hide_render = False
        b.keyframe_insert('hide_render', frame=F(max(0.0, t0)))
        b.hide_render = True
        b.keyframe_insert('hide_render', frame=F(T_G + 1.2))
    mcols = [mat('MattA', '#F4F1EA', rough=0.7), mat('MattB', '#2F6FD0', rough=0.7)]   # top one blue: reads against the sidewalk
    for i in range(4):
        o = mattress(f'Matt{i}', (PILE.x, PILE.y, 0.12 + i * 0.24), mcols[i % 2], rot=rnd.uniform(-0.15, 0.15))
        z0 = 0.12 + i * 0.24
        keyz(o, [-P / FPS, 0] + times(0, T_G + 1.0, 0.25) + [T_RESET],
             lambda t, z0=z0, i=i: Vector((PILE.x, PILE.y, z0 if (t <= 0 or t >= T_RESET) else (
                 z0 + 0.1 * (i + 1) * min(t, T_G) / T_G * 3 if t <= T_G else max(z0, fall_z(z0 + 0.3 * (i + 1), t))))))
    return cast


# ============================================================================== cameras & jobs
def cameras(cast):
    M = cast['MASCOT'][0]
    cams = {}

    def mk(name, loc, look, lens):
        c, t = cam(name, loc, look, lens)
        cams[name] = (c, t)
        return c, t
    c, t = mk('CAM_HOOK', (0.35, -2.55, 1.25), (0.35, 0.3, 1.0), 30)            # frame 0 = last frame
    c, t = mk('CAM_CU', (0.1, -1.0, 1.15), (0, 0, 1.1), 45)                      # follows his face
    for tt in times(0, T_LAND + 0.3, 0.1):
        p = mascot_pos(tt)
        SK.key_cam(c, t, F(tt), (p.x + 0.12, p.y - 1.05, p.z + 1.18), (p.x, p.y, p.z + 1.1))
    c, t = mk('CAM_BIZ', (-0.9, -2.0, 1.6), (-1.6, -0.2, 1.5), 40)                # sneeze
    for tt in times(4.0, 8.4, 0.2):
        z = drift_z(tt)
        y = 1.0 + 0.55 * max(0.0, tt - 6.35)
        SK.key_cam(c, t, F(tt), (-0.6, -2.9 + 0.4 * max(0.0, tt - 6.35), 1.7 + z), (-1.9, y, 1.25 + z), lens=34)
    mk('CAM_WIDE', (-5.5, -11.0, 3.2), (1.0, 2.0, 3.6), 24)                       # whole street
    c, t = mk('CAM_REVEAL', (1.0, -8.5, 1.2), (1.2, 1.0, 6.0), 22)               # "unless you jumped"
    SK.key_cam(c, t, F(15.9), (1.0, -8.5, 1.2), (0.3, 1.0, 2.2), lens=22)
    SK.key_cam(c, t, F(17.6), (1.0, -8.5, 1.2), (1.4, 0.9, 13.0), lens=22)
    c, t = mk('CAM_DOWN', (2.0, 1.0, 20.0), (2.0, 0.9, 0.0), 26)                  # his point of view: the street far below
    for tt in times(17.0, T_G, 0.2):
        p = mascot_pos(tt)
        SK.key_cam(c, t, F(tt), (p.x - 0.2, p.y - 0.6, p.z + 1.4), (p.x + 0.2, p.y + 0.3, 0.0))
    c, t = mk('CAM_FALL', (2.6, -2.6, 8.0), (2.25, 0.85, 8.0), 30)               # follows the fall
    for tt in times(T_G, T_LAND + 0.4, 0.05):
        p = mascot_pos(tt)
        SK.key_cam(c, t, F(tt), (p.x + 0.6, p.y - 3.2, max(1.2, p.z + 1.0)), (p.x, p.y, p.z + 0.8))
    mk('CAM_GROUND', (-0.9, -2.2, 0.4), (-1.9, 1.4, 1.1), 20)                   # impacts at street level
    mk('CAM_PILE', (3.9, -2.4, 2.4), (2.2, 0.8, 0.75), 30)                        # top-down on the mattress pile
    return cams


JOBS = {  # job: (camera, visible cast or 'all', video t0, video t1)
    'HOOK':     ('CAM_HOOK', 'all', 0.0, 2.95),
    'END':      ('CAM_HOOK', 'all', T_RESET - (P - 1) / FPS - 0.0001 if False else -P / FPS, 0.0),
    'RESET':    ('CAM_HOOK', 'all', T_RESET, END),
    'CU':       ('CAM_CU', ['MASCOT'], 2.6, T_G + 0.2),
    'BIZ':      ('CAM_BIZ', ['BUSINESSMAN', 'MASCOT'], 4.4, 7.6),
    'WIDE':     ('CAM_WIDE', 'all', 7.3, 16.0),
    'REVEAL':   ('CAM_REVEAL', 'all', 15.8, 18.0),
    'DOWN':     ('CAM_DOWN', 'all', 17.6, T_G),
    'FALL':     ('CAM_FALL', ['MASCOT'], T_G - 0.2, T_LAND + 0.5),
    'GROUND':   ('CAM_GROUND', ['GRANDMA', 'BUSINESSMAN', 'KID'], T_G, T_G + 1.8),
    'PILE':     ('CAM_PILE', ['MASCOT'], T_LAND - 0.4, T_RESET),
}


def frames_of(job):
    _, _, t0, t1 = JOBS[job]
    return F(t0), F(t1) + 1


SHOTS = {j: ('STREET', JOBS[j][0], frames_of(j), JOBS[j][1], 1.0) for j in JOBS}


def build_shot(sid):
    sc = bpy.context.scene
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 1
    cast = build()
    cams = cameras(cast)
    camname, visible, _, _ = JOBS[sid]
    for name, (m, col) in cast.items():
        if visible != 'all' and name not in visible:
            for o in col.objects:
                o.hide_render = True
    sc.camera = cams[camname][0]
    f0, f1 = frames_of(sid)
    sc.frame_start, sc.frame_end = f0, f1 - 1
    return {'frames': (f0, f1), 'step': 1}

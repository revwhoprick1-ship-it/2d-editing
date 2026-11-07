"""VIDEO_002 — "What If Everyone On Earth Farted At The Same Time?"

Render architecture (speed first):
  * Four sets, each with ONE master performance timeline (ELEV, NEWS, WED, GLOBE).
  * A render job = (set, camera, local frame range, visible cast).  Only the
    frames the edit actually uses are rendered; characters outside a camera's
    view are hidden; extras render without subdivision.
  * Freeze frames, CCTV zooms, split screens, rewinds and speed ramps are made
    in the 2D edit (PIPELINE/editing/edl_engine.py) from these renders.
The ELEV timeline is continuous across the loop seam: frames 0-76 are the calm
ending (E20), frame 77 is the worldwide fart that opens the video (E01).
"""
import math
import os
import random

import bpy
from mathutils import Vector

from studio_lib import scene_kit as SK, render_setup as RS, mascot_api as API, sets_v2 as SV
from studio_lib.materials import hex_rgb

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIDEO_DIR = os.path.join(STUDIO, 'VIDEOS', 'VIDEO_002')
EARTH = os.path.join(STUDIO, 'ASSETS', 'textures', 'earth', 'earth_stylized_2048.png')
LANDMASK = os.path.join(STUDIO, 'ASSETS', 'textures', 'earth', 'earth_landmask_2048.png')

JOLT = 77  # ELEV local frame of the worldwide fart (loop seam)

# job id: (set, camera, (first, end_exclusive), visible cast, res_scale)
SHOTS = {
    'EL_WIDE_END':   ('ELEV', 'CAM_WIDE', (0, 77), 'all', 1.0),     # E20 (calm, tiny pfft)
    'EL_WIDE_JOLT':  ('ELEV', 'CAM_WIDE', (77, 164), 'all', 1.0),   # E01 + E03
    'EL_CU_MASCOT1': ('ELEV', 'CAM_CU_MASCOT', (92, 130), ['MASCOT'], 0.67),   # E02 tile (1/3 screen)
    'EL_CU_GMA1':    ('ELEV', 'CAM_CU_GRANDMA', (92, 130), ['GRANDMA'], 0.67),  # E02 tile
    'EL_CU_BIZ1':    ('ELEV', 'CAM_CU_BIZ', (92, 130), ['BUSINESSMAN'], 0.67),  # E02 tile
    'EL_CU_NOSE':    ('ELEV', 'CAM_CU_MASCOT', (164, 194), ['MASCOT'], 1.0),   # E05
    'EL_CCTV':       ('ELEV', 'CAM_CCTV', (140, 141), 'all', 2.0),             # E12 still (hi-res)
    'EL_CCTV_FACE':  ('ELEV', 'CAM_CCTV_FACE', (140, 141), ['MASCOT'], 2.0),   # E12 final 'enhanced'
    'EL_STARE':      ('ELEV', 'CAM_STARE', (200, 230), 'all', 1.0),            # E13a heads turn
    'EL_GUILTY':     ('ELEV', 'CAM_CU_MASCOT', (230, 254), ['MASCOT'], 1.0),   # E13b freeze source
    'EL_BLAME1':     ('ELEV', 'CAM_BLAME_M', (260, 306), ['MASCOT', 'GRANDMA'], 1.0),
    'EL_BLAME2':     ('ELEV', 'CAM_BLAME_G', (306, 354), ['GRANDMA', 'BUSINESSMAN'], 1.0),
    'EL_BLAME3':     ('ELEV', 'CAM_BLAME_B', (354, 404), ['BUSINESSMAN', 'KID'], 1.0),
    'EL_BLAME4':     ('ELEV', 'CAM_BLAME_K', (404, 434), ['KID', 'MASCOT'], 1.0),
    'EL_SHOCK':      ('ELEV', 'CAM_CU_MASCOT', (434, 450), ['MASCOT'], 1.0),
    'EL_WHISTLE':    ('ELEV', 'CAM_ECU_MASCOT', (450, 530), ['MASCOT'], 1.0),  # E17-E18
    'NW_ANCHOR_CU':  ('NEWS', 'CAM_ANCHOR_CU', (0, 38), ['ANCHOR'], 1.0),      # E06
    'NW_WIDE':       ('NEWS', 'CAM_NEWS_WIDE', (40, 136), ['ANCHOR'], 1.0),    # E11
    'WD_KISS':       ('WED', 'CAM_KISS', (0, 47), ['BRIDE', 'GROOM'], 1.0),    # E07
    'WD_GUESTS':     ('WED', 'CAM_GUESTS', (50, 142), ['G1', 'G2', 'G3'], 1.0),  # E09
    'WD_FAINT':      ('WED', 'CAM_GUESTS_WIDE', (142, 180), ['G1', 'G2', 'G3'], 1.0),  # E10
    'GL_POP':        ('GLOBE', 'CAM_GLOBE', (0, 36), [], 1.0),                 # E04
    'GL_ORBIT':      ('GLOBE', 'CAM_GLOBE', (36, 116), [], 1.0),               # E08
}
ORDER = list(SHOTS)
# slow/subtle shots are rendered on twos and frame-blended in the edit (saves ~25% of renders)
STEP = {'EL_WIDE_END': 2, 'EL_WHISTLE': 2, 'NW_WIDE': 2, 'WD_GUESTS': 2, 'GL_ORBIT': 2}


# ============================================================================== helpers
def key(m, f, **calls):
    m.touched = set()
    for name, args in calls.items():
        fn = getattr(m, name.rstrip('_0123456789'))
        if isinstance(args, dict):
            fn(**args)
        else:
            fn(*args)
    m.key(f)


def expr(m, f, name, w=1.0, eyes=(0, 0), head=None):
    m.touched = set()
    m.expression(name, w, keep_body=True)
    m.eyes(*eyes)
    if head is not None:
        m.head_pose(*head)
    m.key(f)


def jolt(m, f, s=1.0):
    """Everybody-farts reaction: tiny squash down, then a stiff upward jolt."""
    key(m, f - 1, loc=('hips', 0, 0, 0))
    key(m, f + 1, loc=('hips', 0, -0.035 * s, 0), spine_pose=dict(bend=6))
    key(m, f + 4, loc=('hips', 0, 0.025 * s, 0), spine_pose=dict(bend=-8))
    key(m, f + 9, loc=('hips', 0, 0.0, 0), spine_pose=dict(bend=-3))


def arms_down(m, f, curl=0.3):
    m.touched = set()
    for s in ('L', 'R'):
        m.arm(s, raise_=-32, forward=4, elbow=12)
        m.hand(s, curl=curl)
    m.key(f)


def point(m, f, side, raise_, forward, elbow=6, twist=0, hold=None):
    m.touched = set()
    m.arm(side, raise_=raise_ * 0.6, forward=forward * 0.6, elbow=40)
    m.hand(side, curl=0.4)
    m.key(f)
    m.touched = set()
    m.arm(side, raise_=raise_, forward=forward, elbow=elbow, twist=twist)
    m.hand(side, point=True)
    m.key(f + 5)
    if hold:
        m.touched = set()
        m.arm(side, raise_=raise_ - 2, forward=forward + 2, elbow=elbow + 3, twist=twist)
        m.key(f + hold)


def lipflap(m, f0, f1, seed=1, amount=1.0):
    rnd = random.Random(seed)
    f = f0
    while f < f1:
        m.touched = set()
        m.viseme(rnd.choice(['AA', 'EE', 'OH', 'TH', 'MBP', 'SS']), amount)
        m.key(f)
        f += rnd.choice((2, 3, 3, 4))
    m.touched = set()
    m.viseme('rest')
    m.key(f1)


def recolor(col, mapping):
    """Duplicate materials of a cast copy and recolour shirt/denim/hair/shoe/skin."""
    done = {}
    for o in col.objects:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            m = slot.material
            if not m:
                continue
            if m.name not in done:
                done[m.name] = m.copy()
            slot.link = 'OBJECT'
            slot.material = done[m.name]
    for m in done.values():
        part = m.name.split('_', 1)[-1].split('.')[0]
        if part not in mapping:
            continue
        cval = hex_rgb(mapping[part])
        nt = m.node_tree
        for n in nt.nodes:
            if n.type == 'MIX' and getattr(n, 'data_type', '') == 'RGBA' and not n.inputs['A'].is_linked:
                n.inputs['A'].default_value = cval
            if n.type == 'VALTORGB':
                els = n.color_ramp.elements
                if part in ('Denim', 'Hair'):
                    els[0].color = tuple(c * 0.7 for c in cval[:3]) + (1,)
                    els[-1].color = cval
            if n.type == 'BSDF_PRINCIPLED' and not n.inputs['Base Color'].is_linked:
                n.inputs['Base Color'].default_value = cval


def place(m, x, y, rotz=0.0, z=0.0):
    m.rig.location = (x, y, z)
    m.rig.rotation_euler = (0, 0, math.radians(rotz))


def hide_cast(cast, visible):
    for name, (m, col) in cast.items():
        show = visible == 'all' or name in visible
        for o in col.objects:
            o.hide_render = not show or o.hide_render if not show else o.hide_render
            if not show:
                o.hide_render = True


def cam(name, loc, look, lens, fstop=None):
    c, t = SK.cam_rig(name, lens=lens, fstop=fstop)
    c.location = loc
    t.location = look
    return c, t


# ============================================================================== ELEVATOR
def build_elev():
    SV.elevator()
    cast = {}
    m, col = SK.append_mascot()
    cast['MASCOT'] = (m, col)
    for n in ('GRANDMA', 'BUSINESSMAN', 'KID'):
        mm, cc = SK.append_character(n)
        SK.lean_character(cc, 0)
        cast[n] = (mm, cc)
    for n, (x, y, r) in SV.ELEVATOR_SPOTS.items():
        place(cast[n][0], x, y, r)
    M, G, B, K = (cast[n][0] for n in ('MASCOT', 'GRANDMA', 'BUSINESSMAN', 'KID'))
    for mm in (M, G, B, K):
        arms_down(mm, 0, 0.35)
        expr(mm, 0, 'neutral', 0)
    # ---- E20 calm 0-76: muzak, everyone bored; the mascot's eyes dart; tiny pfft at 66
    expr(G, 0, 'neutral', eyes=(0.0, 0.08))
    expr(B, 0, 'neutral', eyes=(0.0, 0.18))      # watching the floor display
    expr(K, 0, 'neutral', eyes=(-0.05, -0.12))   # looking at phone (down)
    expr(M, 0, 'neutral', eyes=(0, 0.02))
    expr(M, 30, 'curious', 0.4, eyes=(0.22, 0.02))
    expr(M, 44, 'curious', 0.4, eyes=(-0.22, 0.02))
    expr(M, 56, 'thinking', 0.5, eyes=(0.0, 0.18))
    key(M, 60, shape=('lips_press', 0.9))
    key(M, 66, shape=('lips_press', 0.9))
    expr(M, 70, 'happy', 0.35, eyes=(0, 0.1))       # tiny relief
    API.blink(M, 14)
    API.blink(G, 22)
    API.blink(B, 48)
    SV.gas_puff('Puff_Tiny', (0.03, 0.06, 0.55), 0.07, 66, grow=6, hold=8, fade=10, drift=(0.0, 0.05, 0.1), seed=3, lumps=4)
    # ---- JOLT at 77: everyone on Earth farts
    for i, (mm, (x, y, r)) in enumerate(zip((M, G, B, K), [SV.ELEVATOR_SPOTS[n] for n in ('MASCOT', 'GRANDMA', 'BUSINESSMAN', 'KID')])):
        sc = mm.rig.scale[0]
        jolt(mm, JOLT, sc)
        side = -1 if x < 0.1 else 1
        SV.gas_puff(f'Puff_J{i}', (x + side * 0.22 * sc, y + 0.12, 0.62 * sc), 0.24 * sc, JOLT, grow=6, hold=40,
                    fade=30, drift=(side * 0.1, 0.25, 0.35), seed=10 + i)
    for mm in (M, G, B, K):
        expr(mm, JOLT, 'neutral')
        expr(mm, JOLT + 2, 'shocked', 1.0, eyes=(0, 0.05))
    # slow awkward side-eye (no head motion)
    expr(M, 100, 'disgusted', 0.8, eyes=(0.28, 0.0))
    expr(G, 100, 'disgusted', 0.7, eyes=(0.28, -0.02))
    expr(B, 100, 'angry', 0.5, eyes=(-0.28, -0.04))
    expr(K, 100, 'confused', 0.9, eyes=(-0.3, 0.0))
    expr(M, 125, 'disgusted', 1.0, eyes=(-0.28, 0.0))
    expr(G, 128, 'disgusted', 1.0, eyes=(0.3, -0.04))
    expr(B, 126, 'disgusted', 0.9, eyes=(-0.3, -0.06))
    expr(K, 124, 'disgusted', 1.0, eyes=(-0.3, 0.02))
    # ---- E05 164-193: mascot pinches his nose and fans the air
    key(M, 164, arm_0=dict(side='R', raise_=-32, forward=4, elbow=12))
    m_ = M
    m_.touched = set(); m_.arm('R', raise_=20, forward=70, elbow=118, wrist=10); m_.hand('R', curl=0.7, thumb=0.6); m_.key(169)
    for k, f in enumerate(range(169, 194, 4)):
        a = 1 if k % 2 == 0 else -1
        m_.touched = set(); m_.arm('L', raise_=40, forward=50, elbow=60, wrist_side=25 * a); m_.hand('L', spread=0.8); m_.key(f)
    expr(M, 166, 'disgusted', 1.0, eyes=(0, 0.0))
    key(M, 170, shape=('cheek_puff', 0.9))
    API.blink(M, 182, base_up=-14)
    # ---- E13a 200-229: everyone slowly turns to stare at him
    for mm in (G, B, K):
        expr(mm, 200, 'neutral', eyes=(0, 0), head=(0, 0, 0))
    expr(M, 200, 'scared', 0.6, eyes=(0, 0.05))
    expr(G, 222, 'angry', 0.6, eyes=(0.2, -0.15), head=(32, 12, 0))
    expr(B, 222, 'angry', 0.7, eyes=(-0.2, -0.2), head=(-30, 16, 0))
    expr(K, 222, 'thinking', 0.5, eyes=(-0.3, 0.0), head=(-55, 4, 0))
    expr(M, 214, 'scared', 0.9, eyes=(0.25, 0.05))
    expr(M, 224, 'scared', 0.9, eyes=(-0.25, 0.05))
    # ---- E13b 230-253: guilty face (freeze source)
    expr(M, 232, 'scared', 1.0, eyes=(0.15, 0.1), head=(4, -4, 4))
    expr(M, 244, 'shocked', 0.7, eyes=(0.0, 0.05), head=(0, -6, 0))
    # ---- blame chain
    expr(M, 260, 'angry', 0.8, eyes=(-0.25, 0.05), head=(-28, 0, 0))
    key(M, 260, spine_pose=dict(twist=-22))
    point(M, 262, 'R', raise_=70, forward=-35, elbow=8, hold=40)
    expr(G, 262, 'surprised', 1.0, eyes=(0.25, -0.12), head=(25, 8, 0))
    expr(G, 306, 'angry', 1.0, eyes=(0.3, -0.05), head=(38, 0, 0))
    key(G, 306, spine_pose=dict(twist=22))
    point(G, 308, 'L', raise_=78, forward=-10, elbow=8, hold=42)
    expr(B, 312, 'shocked', 0.9, eyes=(-0.25, -0.1), head=(-28, 6, 0))
    expr(B, 354, 'angry', 0.9, eyes=(0.05, -0.3), head=(-15, 18, 0))
    point(B, 356, 'L', raise_=28, forward=58, elbow=10, hold=44)
    expr(K, 360, 'surprised', 0.9, eyes=(0.1, 0.3), head=(-20, -12, 0))
    expr(K, 404, 'neutral', 1.0, eyes=(-0.3, 0.0), head=(-45, 0, 0))   # deadpan
    point(K, 406, 'R', raise_=82, forward=12, elbow=6, hold=26)
    expr(M, 410, 'angry', 0.4, eyes=(0.3, 0.0), head=(25, 0, 0))
    expr(M, 434, 'shocked', 1.0, eyes=(0.2, 0.05), head=(18, -8, 0))
    key(M, 434, spine_pose=dict(bend=-10, twist=10))
    # ---- E17 450-529: innocent whistle, sweating
    key(M, 450, spine_pose=dict(bend=0, twist=0))
    arms_down(M, 450, 0.3)
    expr(M, 452, 'thinking', 0.8, eyes=(0.25, 0.25), head=(10, -8, 4))
    key(M, 454, shape=('pucker', 1.0))
    for k, f in enumerate(range(462, 530, 9)):
        a = 1 if k % 2 == 0 else -1
        expr(M, f, 'thinking', 0.8, eyes=(0.25 * a, 0.2), head=(10 * a, -8, 4 * a))
        key(M, f + 1, shape=('pucker', 1.0))
    # ---- cameras
    cams = {}
    cams['CAM_WIDE'] = cam('CAM_WIDE', (0, -2.15, 1.30), (0, 0.15, 1.0), 22)
    c, t = cams['CAM_WIDE']
    SK.key_cam(c, t, 0, (0, -2.15, 1.30), (0, 0.15, 1.0), lens=22)
    SK.key_cam(c, t, JOLT - 1, (0, -2.10, 1.30), (0, 0.15, 1.0), lens=22)      # slow creep before the seam
    SK.key_cam(c, t, JOLT + 3, (0, -2.05, 1.30), (0, 0.12, 1.02), lens=27)     # impact punch-in
    SK.key_cam(c, t, JOLT + 14, (0, -2.05, 1.30), (0, 0.12, 1.02), lens=25)
    SK.key_cam(c, t, 163, (0, -1.85, 1.32), (0, 0.15, 1.05), lens=30)          # slow push during side-eye
    SK.shake(c, JOLT, JOLT + 10, amp=0.025, seed=2)
    cams['CAM_CU_MASCOT'] = cam('CAM_CU_MASCOT', (0.06, -0.86, 1.16), (0.0, -0.1, 1.12), 50, fstop=2.8)
    cams['CAM_ECU_MASCOT'] = cam('CAM_ECU_MASCOT', (0.26, -0.80, 1.17), (0.0, -0.1, 1.12), 55, fstop=2.8)   # 3/4 so it never jump-cuts from CU
    cams['CAM_CU_GRANDMA'] = cam('CAM_CU_GRANDMA', (-0.42, -0.46, 1.30), (-0.58, 0.20, 1.24), 50, fstop=2.8)
    cams['CAM_CU_BIZ'] = cam('CAM_CU_BIZ', (0.38, -0.36, 1.43), (0.52, 0.30, 1.37), 50, fstop=2.8)
    cams['CAM_CCTV'] = cam('CAM_CCTV', (0.92, -0.80, 2.22), (-0.15, 0.25, 0.70), 11)
    cams['CAM_CCTV_FACE'] = cam('CAM_CCTV_FACE', (0.42, -0.62, 1.62), (0.0, -0.12, 1.12), 50)
    cams['CAM_STARE'] = cam('CAM_STARE', (0.0, -1.55, 1.48), (0.0, 0.1, 1.05), 24)
    cams['CAM_BLAME_M'] = cam('CAM_BLAME_M', (-0.62, -1.05, 1.22), (-0.22, 0.08, 1.12), 24, fstop=4)
    cams['CAM_BLAME_G'] = cam('CAM_BLAME_G', (0.10, -0.62, 1.34), (-0.30, 0.32, 1.22), 30, fstop=4)
    cams['CAM_BLAME_B'] = cam('CAM_BLAME_B', (-0.10, -0.62, 1.55), (0.52, 0.12, 1.28), 30, fstop=4)
    cams['CAM_BLAME_K'] = cam('CAM_BLAME_K', (0.82, -0.78, 1.18), (0.25, -0.18, 1.08), 22, fstop=4)
    return cast, cams


# ============================================================================== NEWS
def news_screen_image():
    from PIL import Image  # noqa: only available in system python; fall back to a plain colour
    return None


def build_news():
    scr = os.path.join(VIDEO_DIR, 'gfx', 'news_screen.png')
    SV.news_studio(scr if os.path.exists(scr) else None)
    a, col = SK.append_character('BUSINESSMAN')
    SK.lean_character(col, 1)
    recolor(col, {'Shirt': '#1E3F7A', 'Denim': '#1B2A44', 'Hair': '#C8A060'})
    place(a, 0, 0.42, 0)
    cast = {'ANCHOR': (a, col)}
    arms_down(a, 0, 0.3)
    key(a, 0, arm_0=dict(side='L', raise_=-8, forward=45, elbow=70), arm_1=dict(side='R', raise_=-8, forward=45, elbow=70))
    expr(a, 0, 'happy', 0.5, eyes=(0, 0.0))
    lipflap(a, 1, 8, seed=2)
    jolt(a, 8, 1.2)
    SV.gas_puff('Puff_News', (0.35, 0.65, 0.95), 0.32, 8, grow=6, hold=30, fade=20, drift=(0.2, 0.2, 0.3), seed=4)
    expr(a, 10, 'happy', 0.9, eyes=(0, 0.0))       # smile frozen on air
    for k, f in enumerate(range(16, 38, 4)):          # eye twitch
        key(a, f, lids=dict(up=-20 if k % 2 == 0 else 0, lo=12 if k % 2 == 0 else 6))
    key(a, 30, shape=('sneer.L', 0.6))
    # E11 40-135: composed, dramatic delivery with gestures
    expr(a, 40, 'neutral', 1.0, eyes=(0, 0.0))
    key(a, 40, shape=('sneer.L', 0.0))
    lipflap(a, 44, 72, seed=5)
    key(a, 50, arm_0=dict(side='R', raise_=30, forward=55, elbow=35))
    expr(a, 74, 'surprised', 0.8, eyes=(0, 0.05))
    lipflap(a, 78, 108, seed=6)
    key(a, 86, arm_0=dict(side='L', raise_=10, forward=70, elbow=40), arm_1=dict(side='R', raise_=10, forward=70, elbow=40))
    expr(a, 110, 'angry', 0.6, eyes=(0, 0.0), head=(0, 6, 0))
    lipflap(a, 112, 134, seed=7)
    cams = {
        'CAM_ANCHOR_CU': cam('CAM_ANCHOR_CU', (0.15, -1.25, 1.55), (0, 0.42, 1.42), 50, fstop=2.8),
        'CAM_NEWS_WIDE': cam('CAM_NEWS_WIDE', (0.0, -2.4, 1.62), (0.0, 1.0, 1.70), 28),
    }
    c, t = cams['CAM_ANCHOR_CU']
    SK.key_cam(c, t, 0, (0.15, -1.25, 1.55), (0, 0.42, 1.42), lens=50)
    SK.key_cam(c, t, 9, (0.15, -1.25, 1.55), (0, 0.42, 1.42), lens=50)
    SK.key_cam(c, t, 12, (0.13, -1.15, 1.55), (0, 0.42, 1.44), lens=66)      # punch-in on the frozen smile
    SK.key_cam(c, t, 37, (0.12, -1.10, 1.55), (0, 0.42, 1.44), lens=70)
    SK.shake(c, 8, 14, amp=0.02, seed=3)
    c, t = cams['CAM_NEWS_WIDE']
    SK.key_cam(c, t, 40, (0.0, -2.4, 1.62), (0.0, 1.0, 1.70), lens=28)
    SK.key_cam(c, t, 135, (0.0, -2.0, 1.60), (0.0, 1.0, 1.62), lens=32)
    return cast, cams


# ============================================================================== WEDDING
def build_wed():
    SV.wedding()
    cast = {}
    bride, cb = SK.append_character('KID', scale=1.12)
    SK.lean_character(cb, 1)
    recolor(cb, {'Shirt': '#FBFBF8', 'Denim': '#F2EFEA', 'ShoeUpper': '#F4F1EC'})
    for o in cb.objects:
        if 'Head' in o.name and ('Band' in o.name or 'Cups' in o.name):
            o.hide_render = True        # the bride doesn't wear the kid's headphones
    groom, cg = SK.append_character('BUSINESSMAN')
    SK.lean_character(cg, 1)
    recolor(cg, {'Shirt': '#15161A', 'Denim': '#15161A'})
    # veil for the bride
    from studio_lib import extras_build as EB, mascot_rig as MR, mascot_config as CC
    s = bride.rig.scale[0]
    bride.rig.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    for v in EB.veil(cb, Vector(CC.HEAD_CENTER)):
        MR.parent_to_bone(v, bride.rig, 'head')
    bride.rig.scale = (s, s, s)
    place(bride, -0.19, 0.5, 70)
    place(groom, 0.21, 0.5, -70)
    cast['BRIDE'] = (bride, cb)
    cast['GROOM'] = (groom, cg)
    for mm in (bride, groom):
        arms_down(mm, 0, 0.3)
        expr(mm, 0, 'happy', 0.6, eyes=(0, 0.1))
        key(mm, 0, spine_pose=dict(bend=0))
        key(mm, 20, spine_pose=dict(bend=12), head_pose=dict(nod=-6))
        API.blink(mm, 12)
    key(groom, 2, arm_0=dict(side='R', raise_=10, forward=40, elbow=50), arm_1=dict(side='L', raise_=10, forward=40, elbow=50))
    expr(bride, 18, 'happy', 0.8, eyes=(0, 0.12))
    key(bride, 18, lids=dict(up=-36, lo=10))
    key(groom, 18, lids=dict(up=-36, lo=10))
    key(bride, 18, shape=('pucker', 0.8))
    key(groom, 18, shape=('pucker', 0.8))
    for mm in (bride, groom):
        jolt(mm, 22, 1.0)
        expr(mm, 24, 'shocked', 1.0, eyes=(0, 0.0))
        key(mm, 24, shape=('pucker', 0.0))
        key(mm, 30, spine_pose=dict(bend=-16), head_pose=dict(nod=-10))
        expr(mm, 32, 'disgusted', 1.0, eyes=(0.0, 0.0))
    SV.gas_puff('Puff_W1', (-0.6, 0.75, 0.7), 0.28, 22, grow=6, hold=24, fade=16, seed=21)
    SV.gas_puff('Puff_W2', (0.62, 0.75, 0.75), 0.30, 23, grow=6, hold=24, fade=16, seed=22)
    key(bride, 34, arm_0=dict(side='L', raise_=40, forward=60, elbow=70, wrist_side=20))
    key(bride, 40, arm_0=dict(side='L', raise_=40, forward=60, elbow=70, wrist_side=-20))
    # guests (row stage left of the aisle, facing the couple / camera)
    g1, c1 = SK.append_character('GRANDMA')
    g2, c2 = SK.append_character('BUSINESSMAN')
    g3, c3 = SK.append_character('KID')
    for cc in (c1, c2, c3):
        SK.lean_character(cc, 0)
    recolor(c1, {'Shirt': '#F07FA6'})
    recolor(c2, {'Shirt': '#6F7684', 'Denim': '#555B66'})
    recolor(c3, {'Shirt': '#F5C842'})
    for i, (mm, x) in enumerate(((g1, -2.6), (g2, -1.9), (g3, -1.25))):
        place(mm, x, -1.4, 10)
        arms_down(mm, 0, 0.4)
        expr(mm, 50, 'happy', 0.7, eyes=(0.1, 0.05))
        API.blink(mm, 70 + i * 13)
    cast.update({'G1': (g1, c1), 'G2': (g2, c2), 'G3': (g3, c3)})
    # polite smiles stiffen as the tiny bit of sulfur arrives
    for i, mm in enumerate((g1, g2, g3)):
        expr(mm, 104 + i * 4, 'happy', 0.4, eyes=(0.0, 0.2))
        key(mm, 120 + i * 3, shape=('sneer.L', 0.5))
        expr(mm, 138, 'disgusted', 0.6, eyes=(0, 0.25))
    # domino faint: each guest tips backwards (rig rotates about the heels)
    for i, mm in enumerate((g1, g2, g3)):
        f = 143 + i * 5
        expr(mm, f - 1, 'shocked', 1.0, eyes=(0, 0.3))
        mm.rig.keyframe_insert('rotation_euler', frame=f)
        key(mm, f, arm_0=dict(side='L', raise_=-32, forward=4, elbow=12), arm_1=dict(side='R', raise_=-32, forward=4, elbow=12))
        mm.rig.rotation_euler.x = math.radians(-12)
        mm.rig.keyframe_insert('rotation_euler', frame=f + 4)
        mm.rig.rotation_euler.x = math.radians(-88)
        mm.rig.keyframe_insert('rotation_euler', frame=f + 11)
        mm.rig.rotation_euler.x = math.radians(-82)
        mm.rig.keyframe_insert('rotation_euler', frame=f + 14)
        mm.rig.rotation_euler.x = math.radians(-86)
        mm.rig.keyframe_insert('rotation_euler', frame=f + 17)
        key(mm, f + 8, arm_0=dict(side='L', raise_=95, forward=20, elbow=10), arm_1=dict(side='R', raise_=95, forward=20, elbow=10))
        key(mm, f + 12, lids=dict(up=-48, lo=8))
    cams = {
        'CAM_KISS': cam('CAM_KISS', (0.05, -1.55, 1.38), (0.0, 0.5, 1.30), 40, fstop=2.2),
        'CAM_GUESTS': cam('CAM_GUESTS', (-1.9, -3.3, 1.42), (-1.9, -1.4, 1.30), 40, fstop=2.8),
        'CAM_GUESTS_WIDE': cam('CAM_GUESTS_WIDE', (-0.4, -3.9, 1.30), (-1.9, -1.2, 0.9), 26),
    }
    c, t = cams['CAM_GUESTS']
    SK.key_cam(c, t, 50, (-1.9, -3.4, 1.42), (-1.9, -1.4, 1.30), lens=36)
    SK.key_cam(c, t, 141, (-1.9, -3.0, 1.42), (-1.9, -1.4, 1.30), lens=46)
    c, t = cams['CAM_GUESTS_WIDE']
    SK.shake(c, 150, 162, amp=0.03, seed=8)
    return cast, cams


# ============================================================================== GLOBE
def build_globe():
    earth, atmos = SV.globe(EARTH)
    from PIL import Image  # bundled? fall back to a fixed list if not
    return {}, {}


def _land_points(n, seed=1):
    rnd = random.Random(seed)
    try:
        import numpy as np
        img = bpy.data.images.load(LANDMASK, check_existing=True)
        w, h = img.size
        px = np.array(img.pixels[:]).reshape(h, w, -1)[..., 0]
        pts = []
        while len(pts) < n:
            lat = math.degrees(math.asin(rnd.uniform(-0.85, 0.85)))
            lon = rnd.uniform(-180, 180)
            row = int((lat + 90) / 180 * (h - 1))       # blender pixels are bottom-up
            colx = int((lon + 180) / 360 * (w - 1))
            if px[row, colx] > 0.5:
                pts.append((lat, lon))
        return pts
    except Exception:
        return [(rnd.uniform(-40, 60), rnd.uniform(-120, 140)) for _ in range(n)]


def build_globe_scene():
    earth, atmos = SV.globe(EARTH)
    root = bpy.data.objects.new('GLB_Root', None)
    bpy.context.scene.collection.objects.link(root)
    earth.parent = root
    atmos.parent = root
    pts = _land_points(70, seed=4)
    rnd = random.Random(9)
    for i, (lat, lon) in enumerate(pts):
        f = int(rnd.uniform(1, 30)) if i < 45 else int(rnd.uniform(36, 110))
        p = SV.latlon_to_vec(lat, lon, 1.01)
        SV.gas_puff(f'GPuff{i}', p, rnd.uniform(0.035, 0.06), f, grow=5, hold=rnd.randint(18, 40), fade=14,
                    drift=tuple(p.normalized() * 0.04), seed=100 + i, parent=root, lumps=4)
    # spin: fast whip-in then slow orbit
    root.rotation_euler = (math.radians(15), 0, math.radians(-120))
    root.keyframe_insert('rotation_euler', frame=0)
    root.rotation_euler = (math.radians(15), 0, math.radians(-25))
    root.keyframe_insert('rotation_euler', frame=10)
    root.rotation_euler = (math.radians(15), 0, math.radians(-5))
    root.keyframe_insert('rotation_euler', frame=36)
    root.rotation_euler = (math.radians(15), 0, math.radians(45))
    root.keyframe_insert('rotation_euler', frame=116)
    cams = {'CAM_GLOBE': cam('CAM_GLOBE', (0, -4.6, 0.3), (0, 0, 0.05), 40)}
    c, t = cams['CAM_GLOBE']
    SK.key_cam(c, t, 0, (0, -4.0, 0.3), (0, 0, 0.05), lens=40)
    SK.key_cam(c, t, 36, (0, -4.6, 0.3), (0, 0, 0.05), lens=40)
    SK.key_cam(c, t, 116, (0, -4.0, 0.6), (0, 0, 0.1), lens=46)
    return {}, cams


BUILDERS = {'ELEV': build_elev, 'NEWS': build_news, 'WED': build_wed, 'GLOBE': build_globe_scene}


def build_shot(sid):
    setname, camname, (f0, f1), visible, rs = SHOTS[sid]
    sc = bpy.context.scene
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 1
    cast, cams = BUILDERS[setname]()
    for name, (m, col) in cast.items():
        show = visible == 'all' or name in visible
        if not show:
            for o in col.objects:
                o.hide_render = True
    sc.camera = cams[camname][0]
    sc.frame_start, sc.frame_end = f0, f1 - 1
    if rs != 1.0:
        sc.render.resolution_percentage = int(100 * rs)
    return {'frames': (f0, f1), 'step': STEP.get(sid, 1)}

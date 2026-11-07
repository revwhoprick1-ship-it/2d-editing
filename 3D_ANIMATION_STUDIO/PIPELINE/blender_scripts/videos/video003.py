"""VIDEO_003 — "What If ALL Drugs Became Legal?"

One saturated "pop studio" set (a cyclorama whose colour changes per shot) + the globe.
Each render job has its own local timeline; local frame 0 = video time JOBS[id][1], so the
edit maps video time t -> frame (t - t0) * 30 and lip-sync comes straight from the narration
word times.  PINK is one continuous take across the loop seam: frames 0..SEAM-1 are the
ending (L11-L13), frame SEAM is video frame 0 (L01).
Render: EEVEE 1 sample + OpenImageDenoise (no grain), only the frames the edit shows.
"""
import json
import math
import os
import random

import bpy
from mathutils import Vector, Quaternion

from studio_lib import scene_kit as SK, render_setup as RS, mascot_api as API, sets_v2 as SV
from studio_lib.materials import hex_rgb, simple
from video002 import key, expr, arms_down, recolor, place, cam, lipflap

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIDEO_DIR = os.path.join(STUDIO, 'VIDEOS', 'VIDEO_003')
GFX = os.path.join(VIDEO_DIR, 'gfx')
EARTH = os.path.join(STUDIO, 'ASSETS', 'textures', 'earth', 'earth_stylized_2048.png')
TIMING = json.load(open(os.path.join(VIDEO_DIR, 'audio', 'narration', 'timing.json')))
FPS = 30
END = 33.0                                   # video length (s)
PINK_T0 = 25.2                               # video time of PINK local frame 0
SEAM = int(round((END - PINK_T0) * FPS))     # 234: PINK local frame shown on video frame 0

# job: (builder, video t0, video t1)      local frame = (t - t0) * 30
JOBS = {
    'PINK_END':  ('pink', PINK_T0, END),          # L11-L13 phone + loop line
    'PINK_START': ('pink', -SEAM / FPS + PINK_T0 - PINK_T0, 2.2),   # placeholder, fixed below
    'GRANDMA':   ('grandma', 2.15, 5.75),
    'DEALER':    ('dealer', 5.75, 11.05),
    'PODCAST':   ('podcast', 11.05, 14.65),
    'GLOBE':     ('globe', 14.65, 19.95),
    'ZOMBIE':    ('zombie', 19.95, 21.5),
    'LUNGS':     ('lungs', 21.5, 25.2),
}


def frames_of(job):
    b, t0, t1 = JOBS[job]
    if job == 'PINK_START':
        return SEAM, SEAM + int(round(2.2 * FPS)) + 1
    if job == 'PINK_END':
        return 0, SEAM
    return 0, int(round((t1 - t0) * FPS)) + 1


def words_between(t0, t1):
    return [w for w in TIMING['words'] if t0 - 0.05 <= w['start'] < t1]


def talk(m, words, t0, amount=1.0, seed=3, offset=0):
    """Viseme per word from the narration word times (local frame = (t - t0) * 30 + offset)."""
    rnd = random.Random(seed)
    for w in words:
        a = int(round((w['start'] - t0) * FPS)) + offset
        b = int(round((w['end'] - t0) * FPS)) + offset
        letters = [c for c in w['text'].lower() if c.isalpha()]
        vis = [API.PHONEME_TO_VISEME.get(c, 'AA') for c in letters[::2]] or ['AA']
        n = max(1, min(len(vis), (b - a) // 2))
        for i in range(n):
            m.touched = set()
            m.viseme(vis[i * len(vis) // n], amount * rnd.uniform(0.75, 1.0))
            m.key(a + i * max(2, (b - a) // n))
        m.touched = set()
        m.viseme('rest')
        m.key(b + 1)


# ============================================================================== set
def pop_set(color, glow='#FFFFFF', floor=None):
    """Cyclorama sweep (floor curving into the wall) in one loud colour + a glow pool behind the star."""
    import bmesh
    bm = bmesh.new()
    prof = [(y, 0.0) for y in (-6.0, -2.0, 0.0, 1.2)]
    for k in range(1, 9):
        a = math.pi / 2 * k / 8
        prof.append((1.2 + 1.6 * math.sin(a), 1.6 - 1.6 * math.cos(a)))
    prof.append((2.8, 7.0))
    rows = []
    for x in (-8.0, 8.0):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new('POP_Cyc')
    bm.to_mesh(me)
    ob = bpy.data.objects.new('POP_Cyc', me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(simple('POP_Cyc', color, rough=0.75))
    RS.world_color(tuple(c * 0.25 for c in hex_rgb(color)[:3]), 1.0)
    # lights: warm key (shadows), saturated rim, soft fill, glow pool on the wall
    RS.area_light('Key', (-1.4, -2.2, 2.6), (0, 0, 1.0), 170, size=1.6, color=(1.0, 0.95, 0.88))
    RS.area_light('Rim', (1.6, 0.8, 2.0), (0, 0, 1.1), 160, size=0.8, color=hex_rgb(glow)[:3])
    RS.area_light('Fill', (1.8, -2.4, 1.3), (0, 0, 1.0), 40, size=2.0, color=(0.9, 0.95, 1.0))
    RS.area_light('Glow', (0, -0.6, 3.2), (0, 2.2, 1.4), 260, size=2.5, color=hex_rgb(glow)[:3])
    punchy()


def punchy():
    """Standard view transform = saturated colours (AgX desaturates brights to pastel)."""
    vs = bpy.context.scene.view_settings
    vs.view_transform = 'Standard'
    try:
        vs.look = 'Medium High Contrast'
    except TypeError:
        vs.look = 'None'
    vs.exposure = -0.35


def mat(name, color, **kw):
    return simple(name, color, **kw)


def cylinder(name, loc, r, h, m, verts=24, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


def pill_bottle(name, loc, rot=0.0, s=1.0):
    body = cylinder(name, loc, 0.032 * s, 0.085 * s, PILL_ORANGE)
    cap = cylinder(name + '_cap', (loc[0], loc[1], loc[2] + 0.048 * s), 0.035 * s, 0.014 * s, PILL_CAP)
    lab = cylinder(name + '_lab', (loc[0], loc[1], loc[2] - 0.012 * s), 0.0325 * s, 0.026 * s, PILL_LABEL)
    for o in (body, cap, lab):
        o.rotation_euler.z = rot
    return body


def image_plane(name, img, size, loc, rot=(90, 0, 0), emit=0.0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=tuple(math.radians(r) for r in rot))
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(img, check_existing=True)
    nt.links.new(tx.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.9
    if emit:
        nt.links.new(tx.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emit
    o.data.materials.append(m)
    return o


def setup_mats():
    global PILL_ORANGE, PILL_CAP, PILL_LABEL, BLACK, METAL
    PILL_ORANGE = mat('PillBody', '#F08A1C', rough=0.25, coat=0.6)
    PILL_CAP = mat('PillCap', '#F7F7F2', rough=0.4)
    PILL_LABEL = mat('PillLabel', '#FFFFFF', rough=0.6)
    BLACK = mat('MicBlack', '#15151A', rough=0.35)
    METAL = mat('Metal', '#B8BCC6', rough=0.25, metallic=1.0)


def camset(name, loc, look, lens):
    c, t = cam(name, loc, look, lens)
    bpy.context.scene.camera = c
    return c, t


# ============================================================================== builders
def b_pink(job):
    """Mascot: L11 thinking -> L12 phone -> L13 looks at us -> SEAM -> L01 'everything legal!' jump."""
    pop_set('#FF3D9A', glow='#FFD23F')
    m, col = SK.append_mascot()
    arms_down(m, 0, 0.3)
    expr(m, 0, 'thinking', 0.9, eyes=(0.25, 0.25), head=(8, -6, 4))
    key(m, 0, arm_0=dict(side='R', raise_=-10, forward=55, elbow=110), hand_0=dict(side='R', curl=0.6))   # hand on chin
    # phone in the left hand (screen faces him, then us)
    phone = bpy.data.objects.new('Phone', None)
    bpy.context.scene.collection.objects.link(phone)
    body = cylinder('PhoneBody', (0, 0, 0), 1, 1, BLACK, verts=4)
    body.scale = (0.045, 0.005, 0.09)
    body.rotation_euler = (0, 0, math.radians(45))
    body.parent = phone
    scr = image_plane('PhoneScreen', os.path.join(GFX, 'phone_screen.png'), (0.058, 0.118), (0, -0.0055, 0), rot=(90, 0, 0), emit=2.5)
    scr.parent = phone
    con = phone.constraints.new('CHILD_OF')
    con.target = m.rig
    con.subtarget = 'hand.L'
    con.inverse_matrix.identity()
    phone.location = (0.0, 0.06, 0.03)
    phone.rotation_euler = (math.radians(-80), math.radians(10), math.radians(180))
    f12 = int(round((27.6 - PINK_T0) * FPS))

    def vis(f, on):
        for o in (body, scr):
            o.hide_render = not on
            o.keyframe_insert('hide_render', frame=f)
    vis(0, False)
    vis(f12 - 4, True)
    vis(SEAM - 1, True)
    vis(SEAM, False)
    # L12 (27.8-30.6): pulls the phone up, stares, smiles, screen glow on his face
    key(m, f12 - 6, arm_0=dict(side='R', raise_=-32, forward=4, elbow=12))
    key(m, f12, arm_0=dict(side='L', raise_=15, forward=62, elbow=128, wrist=-10), hand_0=dict(side='L', curl=0.75, thumb=0.4))
    expr(m, f12, 'happy', 0.6, eyes=(0.0, -0.35), head=(0, -14, 0))
    expr(m, f12 + 30, 'excited', 0.7, eyes=(0.0, -0.4), head=(0, -16, 2))
    # L13 (30.85-32.6): looks up at the viewer, sly smile, leans in
    f13 = int(round((30.85 - PINK_T0) * FPS))
    expr(m, f13, 'happy', 0.9, eyes=(0, 0.02), head=(0, 4, -4))
    key(m, f13 + 10, spine_pose=dict(bend=10))
    expr(m, SEAM - 2, 'curious', 0.8, eyes=(0, 0.02), head=(0, 6, -6))
    # SEAM (video frame 0, L01): phone flies away, jump, arms up, huge excited face
    key(m, SEAM, spine_pose=dict(bend=-8), loc=('hips', 0, 0.05, 0),
        arm_0=dict(side='L', raise_=150, forward=10, elbow=15), arm_1=dict(side='R', raise_=150, forward=10, elbow=15),
        hand_0=dict(side='L', spread=1.0), hand_1=dict(side='R', spread=1.0))
    expr(m, SEAM, 'excited', 1.0, eyes=(0, 0.1), head=(0, 8, 0))
    for k, f in enumerate(range(SEAM + 6, SEAM + 66, 8)):     # bouncing celebration
        key(m, f, loc=('hips', 0, 0.035 if k % 2 == 0 else -0.01, 0),
            arm_0=dict(side='L', raise_=140 + 12 * (k % 2), forward=10, elbow=20), arm_1=dict(side='R', raise_=152 - 12 * (k % 2), forward=10, elbow=20))
    talk(m, words_between(25.2, END), PINK_T0)
    talk(m, words_between(0, 2.2), 0.0, offset=SEAM)
    c, t = camset('CAM', (0.05, -1.25, 1.12), (0, 0, 1.0), 40)
    SK.key_cam(c, t, 0, (0.10, -1.30, 1.15), (0, 0, 1.05), lens=42)
    SK.key_cam(c, t, f12, (0.05, -1.05, 1.12), (0, 0, 1.08), lens=42)
    SK.key_cam(c, t, SEAM - 1, (0.0, -0.90, 1.14), (0, 0, 1.10), lens=42)      # slow push to his face
    SK.key_cam(c, t, SEAM, (0.0, -1.55, 1.10), (0, 0, 1.05), lens=32)          # cut-wide on the jump
    SK.key_cam(c, t, SEAM + 66, (0.0, -1.40, 1.10), (0, 0, 1.05), lens=32)
    return [m]


def b_grandma(job):
    pop_set('#18C4B8', glow='#FFE066')
    g, col = SK.append_character('GRANDMA')
    SK.lean_character(col, 0)
    t0 = JOBS['GRANDMA'][1]
    arms_down(g, 0, 0.3)
    key(g, 0, arm_0=dict(side='L', raise_=-12, forward=45, elbow=70), arm_1=dict(side='R', raise_=-12, forward=45, elbow=70))
    expr(g, 0, 'neutral', 1.0, eyes=(0.0, 0.0))
    key(g, 0, lids=dict(up=-22, lo=6))                                         # unbothered half-lids
    expr(g, int((3.58 - t0) * FPS), 'happy', 0.55, eyes=(0.0, 0.02), head=(0, 4, 6))   # smug on "fourteen"
    talk(g, words_between(t0, 5.75), t0, amount=0.8)
    # mountain of pill bottles on a table in front of her
    mat_t = mat('Table', '#7A3BE0', rough=0.5)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.42, 0.42))
    tb = bpy.context.object
    tb.scale = (1.1, 0.5, 0.84)
    tb.data.materials.append(mat_t)
    rnd = random.Random(4)
    for i in range(34):
        r = rnd.random()
        x = rnd.uniform(-0.42, 0.42)
        y = rnd.uniform(-0.6, -0.25)
        z = 0.885 + 0.09 * int(r * 3 * (1 - abs(x) * 1.6) if r > 0.35 else 0)
        pill_bottle(f'Pill{i}', (x, y, z), rot=rnd.uniform(0, 6.28), s=rnd.uniform(0.9, 1.25))
    c, t = camset('CAM', (0.0, -1.95, 1.40), (0, 0, 1.15), 40)
    SK.key_cam(c, t, 0, (0.0, -2.05, 1.38), (0, 0, 1.12), lens=38)
    SK.key_cam(c, t, frames_of(job)[1], (0.0, -1.80, 1.36), (0, 0, 1.18), lens=46)
    return [g]


def b_dealer(job):
    pop_set('#7B2FF7', glow='#3DF2FF')
    d, col = SK.append_character('BUSINESSMAN')
    SK.lean_character(col, 0)
    recolor(col, {'Shirt': '#2A2A33', 'Denim': '#1C1C24'})
    for o in col.objects:
        if any(k in o.name for k in ('Tie', 'Collar')):
            o.hide_render = True
    t0 = JOBS['DEALER'][1]
    # holds a cardboard sign at chest height
    pose = dict(arm_0=dict(side='L', raise_=-8, forward=62, elbow=55), arm_1=dict(side='R', raise_=-8, forward=62, elbow=55),
                hand_0=dict(side='L', curl=0.8), hand_1=dict(side='R', curl=0.8))
    key(d, 0, **pose)
    expr(d, 0, 'sad', 1.0, eyes=(0.0, -0.2), head=(0, -10, 0))
    f5 = int(round((8.1 - t0) * FPS))
    expr(d, f5 - 2, 'sad', 1.0, eyes=(0.0, -0.2), head=(0, -10, 0))
    expr(d, f5 + 8, 'happy', 0.9, eyes=(0.0, 0.05), head=(0, 6, 4))           # proud of the new job title
    key(d, f5 + 8, spine_pose=dict(bend=-6))
    image_plane('Sign', os.path.join(GFX, 'sign.png'), (0.62, 0.42), (0, -0.33, 0.98), rot=(85, 0, 0))
    c, t = camset('CAM', (0.0, -2.3, 1.40), (0, 0, 1.15), 36)
    SK.key_cam(c, t, 0, (0.0, -2.4, 1.38), (0, 0, 1.15), lens=34)
    SK.key_cam(c, t, f5, (0.0, -2.0, 1.45), (0, 0, 1.25), lens=40)
    SK.key_cam(c, t, frames_of(job)[1], (0.0, -1.9, 1.48), (0, 0, 1.30), lens=46)
    return [d]


def b_podcast(job):
    pop_set('#FF6A1A', glow='#FF2E63')
    t0 = JOBS['PODCAST'][1]
    cast = []
    for i, (x, rz, shirt, hair) in enumerate(((-0.30, -24, '#F5C518', '#1A120E'), (0.30, 24, '#F4F4F4', '#3A2A1C'))):
        b, col = SK.append_character('BUSINESSMAN')
        SK.lean_character(col, 0)
        recolor(col, {'Shirt': shirt, 'Hair': hair})
        place(b, x, 0.0, rz)
        key(b, 0, arm_0=dict(side='L', raise_=-15, forward=40, elbow=80), arm_1=dict(side='R', raise_=-15, forward=40, elbow=80))
        expr(b, 0, 'happy', 0.7, eyes=(-0.25 if x < 0 else 0.25, 0.0), head=((-15 if x < 0 else 15), 0, 0))
        cast.append(b)
        # big podcast mic on a boom
        mx = x * 0.62
        cylinder(f'MicStand{i}', (mx, -0.42, 1.10), 0.008, 0.5, METAL)
        cylinder(f'Mic{i}', (mx, -0.42, 1.40), 0.035, 0.14, BLACK)
    a, b = cast
    # the gold guy pitches the "pivot", the other nods along
    talk(a, words_between(t0, 14.65), t0, amount=0.9)
    for f in range(4, 100, 14):
        key(b, f, spine_pose=dict(bend=5))
        key(b, f + 7, spine_pose=dict(bend=-2))
    key(a, 30, arm_0=dict(side='R', raise_=40, forward=50, elbow=40), hand_0=dict(side='R', spread=1.0))
    mat_t = mat('Desk', '#141418', rough=0.4)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.55, 0.40))
    tb = bpy.context.object
    tb.scale = (1.6, 0.55, 0.8)
    tb.data.materials.append(mat_t)
    c, t = camset('CAM', (0.0, -1.9, 1.55), (0, 0, 1.38), 32)
    SK.key_cam(c, t, 0, (0.0, -1.95, 1.55), (0, 0, 1.38), lens=30)
    SK.key_cam(c, t, frames_of(job)[1], (0.0, -1.65, 1.55), (0, 0, 1.40), lens=34)
    return cast


def b_globe(job):
    earth, atmos = SV.globe(EARTH)
    RS.world_color((0.01, 0.0, 0.04), 1.0)
    root = bpy.data.objects.new('GLB_Root', None)
    bpy.context.scene.collection.objects.link(root)
    earth.parent = root
    atmos.parent = root
    p = SV.latlon_to_vec(39.5, -8.0 + 180.0, 1.0)             # Portugal (this sphere's u=0 is at +X: lon + 180, checked on a render)
    for o in bpy.data.objects:
        if o.name.startswith('GLB_Star'):
            o.hide_render = True
    punchy()
    pin = bpy.data.objects.new('Pin', None)
    bpy.context.scene.collection.objects.link(pin)
    pin.parent = root
    head = cylinder('PinHead', (0, 0, 0), 0.025, 0.05, mat('PinRed', '#FF2340', emission=('#FF2340', 2.0)))
    head.parent = root
    head.location = p * 1.03
    root.rotation_mode = 'QUATERNION'
    face = p.rotation_difference(Vector((0, -1, 0.25)).normalized())
    start = Quaternion((0, 0, 1), math.radians(-140)) @ face
    n = frames_of(job)[1]
    root.rotation_quaternion = start
    root.keyframe_insert('rotation_quaternion', frame=0)
    root.rotation_quaternion = face
    root.keyframe_insert('rotation_quaternion', frame=40)
    root.keyframe_insert('rotation_quaternion', frame=n)
    c, t = camset('CAM', (0, -4.4, 0.4), (0, 0, 0.1), 40)
    SK.key_cam(c, t, 0, (0, -4.4, 0.4), (0, 0, 0.1), lens=40)
    SK.key_cam(c, t, 40, (0, -3.6, 0.45), (0, 0, 0.2), lens=40)
    SK.key_cam(c, t, n, (0, -2.6, 0.55), (0, 0, 0.25), lens=55)               # dive to Portugal
    RS.area_light('Key', (-3, -4, 3), (0, 0, 0), 900, size=3.0)
    return []


def b_zombie(job):
    pop_set('#36D35A', glow='#E8FF3A')
    m, col = SK.append_mascot()
    zpose = dict(arm_0=dict(side='L', raise_=5, forward=88, elbow=8), arm_1=dict(side='R', raise_=5, forward=88, elbow=8),
                 hand_0=dict(side='L', curl=0.3), hand_1=dict(side='R', curl=0.3))
    key(m, 0, spine_pose=dict(bend=10, side=6), **zpose)
    expr(m, 0, 'angry', 0.6, eyes=(0, 0.3), head=(0, -12, 14))
    key(m, 0, lids=dict(up=-30, lo=10))
    key(m, 14, spine_pose=dict(bend=12, side=-6), **zpose)
    # snaps out of it: totally normal, shrug + thumbs-up energy
    key(m, 22, spine_pose=dict(bend=0, side=0), arm_0=dict(side='L', raise_=10, forward=30, elbow=70, shrug=1.0),
        arm_1=dict(side='R', raise_=10, forward=30, elbow=70, shrug=1.0), hand_0=dict(side='L', spread=1.0), hand_1=dict(side='R', spread=1.0))
    expr(m, 22, 'happy', 1.0, eyes=(0, 0.0), head=(0, 4, -6))
    c, t = camset('CAM', (0.0, -1.6, 1.15), (0, 0, 1.0), 35)
    SK.key_cam(c, t, 0, (0.0, -1.7, 1.15), (0, 0, 1.0), lens=35)
    SK.key_cam(c, t, frames_of(job)[1], (0.0, -1.45, 1.15), (0, 0, 1.0), lens=38)
    return [m]


def b_lungs(job):
    pop_set('#FF2340', glow='#FFB0C8')
    m, col = SK.append_mascot()
    t0 = JOBS['LUNGS'][1]
    arms_down(m, 0, 0.3)
    expr(m, 0, 'thinking', 0.7, eyes=(0.0, 0.05))
    talk(m, [w for w in words_between(t0, 23.6)], t0)
    # "Ask your lungs." -> coughing fit
    fc = int(round((24.2 - t0) * FPS))
    for k in range(3):
        f = fc + k * 9
        key(m, f, spine_pose=dict(bend=4), arm_0=dict(side='R', raise_=0, forward=70, elbow=120), hand_0=dict(side='R', fist=True))
        expr(m, f, 'disgusted', 1.0, eyes=(0, 0.0))
        key(m, f, shape=('cheek_puff', 0.9), lids=dict(up=-45, lo=20))
        key(m, f + 3, spine_pose=dict(bend=22))
        key(m, f + 3, shape=('cheek_puff', 0.0))
    c, t = camset('CAM', (0.0, -1.3, 1.15), (0, 0, 1.05), 40)
    SK.key_cam(c, t, 0, (0.0, -1.35, 1.15), (0, 0, 1.05), lens=40)
    SK.key_cam(c, t, fc, (0.0, -1.15, 1.12), (0, 0, 1.05), lens=44)
    SK.shake(c, fc, fc + 28, amp=0.02, seed=3)
    return [m]


BUILDERS = {'pink': b_pink, 'grandma': b_grandma, 'dealer': b_dealer, 'podcast': b_podcast, 'globe': b_globe,
            'zombie': b_zombie, 'lungs': b_lungs}
SHOTS = {j: (JOBS[j][0], 'CAM', frames_of(j), 'all', 1.0) for j in JOBS}


def build_shot(sid):
    sc = bpy.context.scene
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 1
    setup_mats()
    BUILDERS[JOBS[sid][0]](sid)
    f0, f1 = frames_of(sid)
    sc.frame_start, sc.frame_end = f0, f1 - 1
    return {'frames': (f0, f1), 'step': 1}

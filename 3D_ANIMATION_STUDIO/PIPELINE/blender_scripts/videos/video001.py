"""VIDEO_001 — "What If You Were Shrunk Inside Your Own Body?"

Every shot is built procedurally from the studio libraries.  Shot frame ranges
are GLOBAL frames (30 fps); narration starts at 0.2 s (frame 6).
See VIDEOS/VIDEO_001/07_storyboard.md for the shot-by-shot plan.
"""
import math
import os
import random

import bpy
from mathutils import Vector, Euler

from studio_lib import bio_assets as BA, scene_kit as SK, render_setup as RS, mascot_api as API
from studio_lib.materials import hex_rgb
from studio_lib.geo import lerp, smoothstep

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIDEO_DIR = os.path.join(STUDIO, 'VIDEOS', 'VIDEO_001')
FPS = 30

SHOTS = {  # id: (first global frame, end frame exclusive)
    'SH01': (0, 144), 'SH02': (144, 237), 'SH03': (237, 329), 'SH04a': (329, 383), 'SH04b': (383, 438),
    'SH05a': (438, 507), 'SH05b': (507, 585), 'SH06a': (585, 640), 'SH06b': (640, 745),
    'SH07a': (745, 875), 'SH07b': (875, 1003), 'SH08': (1003, 1077), 'SH09a': (1077, 1155),
    'SH09b': (1155, 1290), 'SH10': (1290, 1341), 'SH11a': (1341, 1392), 'SH11b': (1392, 1434),
    'SH11c': (1434, 1512), 'SH12a': (1512, 1600), 'SH12b': (1600, 1710),
}
ORDER = list(SHOTS)

# palette / fog
VEIN_FOG = ((0.075, 0.008, 0.012), 4.0, 55.0, 1.1)
HEART_FOG = ((0.05, 0.004, 0.008), 5.0, 40.0, 1.2)
CAP_FOG = ((0.16, 0.05, 0.06), 3.0, 22.0, 1.2)
AORTA_FOG = ((0.22, 0.05, 0.04), 6.0, 70.0, 1.0)

HEARTBEATS = [18, 38, 491, 540, 550, 1415]   # global frames of strong beats used for visual pulses


# ===================================================================================== helpers
def mascot():
    m, col = SK.append_mascot()
    return m, col


def hero(name='HERO'):
    h = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(h)
    return h


def move_linear(ob, f0, f1, p0, p1):
    ob.location = p0
    ob.keyframe_insert('location', frame=f0)
    ob.location = p1
    ob.keyframe_insert('location', frame=f1)
    BA.linear_keys(ob)


def hero_rbc(parent, rbc_mesh, oxy=0.0, wobble=(0, 0)):
    ob = bpy.data.objects.new('HeroRBC', rbc_mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    ob['oxy'] = oxy
    return ob


def place_rig(m, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    rig = m.rig
    rig.parent = parent
    rig.location = loc
    rig.rotation_euler = [math.radians(a) for a in rot]
    return rig


def pose_sit(m, f, grip=0.6, lean=8, feet=(0.42, 0.17), arms='side'):
    m.loc('hips', 0, -0.44, -0.04)
    for s in ('L', 'R'):
        m.loc(f'foot_ik.{s}', 0, feet[0], feet[1])
        m.rot(f'foot_ik.{s}', -10, 0, 0)
    m.spine_pose(bend=lean)
    if arms == 'side':
        for s in ('L', 'R'):
            m.arm(s, raise_=-22, forward=12, elbow=28, wrist=-10)
            m.hand(s, curl=grip, thumb=0.4)
    m.key(f)


def lights_rig(parent, key=(1.0, 0.85, 0.8), key_e=900, rim=(1.0, 0.45, 0.35), rim_e=1400, fill=(0.9, 0.5, 0.55),
               fill_e=250, scale=1.0):
    k = RS.area_light('Key', Vector((-2.2, -3.2, 2.6)) * scale, (0, 0, 0.6), key_e, 2.5 * scale, key)
    r = RS.area_light('Rim', Vector((2.0, 3.0, 2.2)) * scale, (0, 0, 0.8), rim_e, 2.0 * scale, rim)
    fl = RS.area_light('Fill', Vector((3.0, -2.0, 0.2)) * scale, (0, 0, 0.6), fill_e, 3.0 * scale, fill)
    for l in (k, r, fl):
        l.parent = parent
    r.data.use_shadow = False
    fl.data.use_shadow = False
    return k, r, fl


def expr_key(m, f, name, w=1.0, eyes=None, head=None):
    m.touched = set()
    m.expression(name, w, keep_body=True)
    if eyes is not None:
        m.eyes(*eyes)
    if head is not None:
        m.head_pose(*head)
    m.key(f)


def body_key(m, f, **kw):
    m.touched = set()
    for k, v in kw.items():
        getattr(m, k)(*v) if isinstance(v, tuple) else getattr(m, k)(**v)
    m.key(f)


def pulse(ob, frames, amt=0.04, axis=(1, 0, 1), dur=6):
    base = ob.scale.copy()
    for f in frames:
        ob.scale = base
        ob.keyframe_insert('scale', frame=f - 1)
        ob.scale = Vector([b * (1 + amt * a) for b, a in zip(base, axis)])
        ob.keyframe_insert('scale', frame=f + 2)
        ob.scale = base
        ob.keyframe_insert('scale', frame=f + dur)


# ===================================================================================== sets
def set_vein(f0, f1, speed=3.0, radius=9.0, n_cells=260, seed=1, start_y=30.0, hero_on=True):
    """Big vein: fog-filled tunnel, flowing deoxygenated RBCs, hero empty that
    travels with the flow."""
    RS.world_color(VEIN_FOG[0], 1.0)
    wall = BA.vessel_material('BIO_VeinWall', base='#6E1824', cell='#9A3440', fog=VEIN_FOG)
    tun = BA.vessel_tunnel('Vein', radius, 260, wall, segs=56, curve_amp=0.0, seed=seed, bumps=0.07, y0=130)
    rmesh = BA.rbc_mesh('RBC_mesh')
    rmat = BA.rbc_material('BIO_RBC', fog=VEIN_FOG)
    rmesh.materials.append(rmat)
    dur = (f1 - f0) / FPS
    h = hero()
    p0 = Vector((0, start_y, 0))
    p1 = Vector((0, start_y - speed * dur, 0))
    move_linear(h, f0, f1, p0, p1)
    span = (start_y - speed * dur - 50, start_y + 30)
    cells = BA.flow_cells(rmesh, rmat, n_cells, radius * 0.85, span, speed, f0, f1, seed=seed + 2,
                          keep_out=(Vector((0, start_y - speed * dur * 0.5, 0)), 0.0), min_r=0.0)
    # keep a clear bubble around the hero path
    for c in cells:
        loc0 = c.location
    _clear_around_hero(cells, h, f0, f1, 3.2)
    BA.specks(140, radius * 0.9, span, speed * 1.05, f0, f1, color='#FF9C8C', strength=1.5, size=(0.015, 0.05))
    hr = hero_rbc(h, rmesh, 0.0) if hero_on else None
    return dict(hero=h, tunnel=tun, cells=cells, rbc_mesh=rmesh, rbc_mat=rmat, hero_rbc=hr, wall=wall)


def _clear_around_hero(cells, h, f0, f1, r):
    """Delete flow cells that would intersect the hero RBC/camera during the shot."""
    sc = bpy.context.scene
    kill = set()
    for f in range(f0, f1, 6):
        sc.frame_set(f)
        hp = h.matrix_world.translation
        for c in cells:
            if c in kill:
                continue
            if (c.matrix_world.translation - hp).length < r:
                kill.add(c)
    for c in kill:
        cells.remove(c)
        bpy.data.objects.remove(c)


def set_capillary(f0, f1, radius=1.25, length=80, speed=0.9, oxy_keys=None, n_cells=14, alveolus_side=1,
                  wall_alpha=0.0, hero_y=0.0):
    """Lung capillary next to an alveolus.  Cells travel single file along -Y."""
    RS.world_color(CAP_FOG[0], 1.0)
    wall = BA.vessel_material('BIO_CapWall', base='#C0606A', cell='#E09098', fog=CAP_FOG, emission=('#FF9A8A', 0.15))
    tun = BA.vessel_tunnel('Capillary', radius, length, wall, segs=40, seed=7, bumps=0.06, y0=length / 2,
                           curve_amp=0.0)
    if wall_alpha:
        # only the side facing the air sac is see-through (cheaper than a fully transparent tube):
        # cut that side out of the opaque wall and close it with a thin translucent membrane panel
        import bmesh
        bm = bmesh.new(); bm.from_mesh(tun.data)
        kill = [f for f in bm.faces if f.calc_center_median().x * alveolus_side > radius * 0.45]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        bm.to_mesh(tun.data); bm.free()
        mem = BA.vessel_material('BIO_CapMembrane', base='#E8A0A8', cell='#F4C0C4', fog=CAP_FOG,
                                 translucent=wall_alpha, emission=('#FFC0B0', 0.25))
        bmm = bmesh.new()
        segs, rings = 12, 60
        rows = []
        for i in range(rings + 1):
            y = length / 2 - length * i / rings
            row = []
            for k in range(segs + 1):
                a = math.radians(-65 + 130 * k / segs)
                row.append(bmm.verts.new((alveolus_side * math.cos(a) * radius * 0.99, y, math.sin(a) * radius * 0.99)))
            rows.append(row)
        for i in range(rings):
            for k in range(segs):
                bmm.faces.new((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]))
        me = bpy.data.meshes.new('CapMembrane'); bmm.to_mesh(me); bmm.free()
        pan = bpy.data.objects.new('CapMembrane', me); bpy.context.scene.collection.objects.link(pan)
        me.materials.append(mem)
        for poly in me.polygons:
            poly.use_smooth = True
    alv = BA.alveolus('Alveolus', (alveolus_side * (radius + 4.2), 0, 0.6), 3.6)
    rmesh = BA.rbc_mesh('RBC_mesh')
    rmesh.shape_keys.key_blocks['parachute'].value = 0.85   # cells fold into cups in capillaries
    rmat = BA.rbc_material('BIO_RBC', fog=CAP_FOG)
    rmesh.materials.append(rmat)
    rnd = random.Random(4)
    cells = []
    dur = (f1 - f0) / FPS
    for i in range(n_cells):
        y = hero_y + 3.0 + i * 2.6 if i < n_cells // 2 else hero_y - 3.4 - (i - n_cells // 2) * 2.6
        ob = bpy.data.objects.new(f'CapRBC_{i}', rmesh)
        bpy.context.scene.collection.objects.link(ob)
        ob.rotation_euler = (math.radians(90), rnd.uniform(-0.2, 0.2), rnd.uniform(0, 6))
        s = 0.92
        ob.scale = (s * 0.8, s * 0.8, s)
        ob['oxy'] = 0.0
        move_linear(ob, f0, f1, Vector((rnd.uniform(-0.1, 0.1), y, rnd.uniform(-0.1, 0.1))),
                    Vector((rnd.uniform(-0.1, 0.1), y - speed * dur, rnd.uniform(-0.1, 0.1))))
        cells.append(ob)
    # lights: airy alveolar glow on the alveolus side + warm key
    a = RS.area_light('AlvGlow', (alveolus_side * 6.5, 0, 2.5), (0, 0, 0), 2500, 6.0, (1.0, 0.92, 0.88))
    b = RS.point_light('CapWarm', (-alveolus_side * 1.5, -2.0, 1.5), 120, (1.0, 0.6, 0.55), 0.5)
    return dict(tunnel=tun, alveolus=alv, cells=cells, rbc_mesh=rmesh, rbc_mat=rmat, wall=wall, lights=(a, b))


def set_heart_chamber(f0, f1, radius=11.0, left=False):
    fog = HEART_FOG
    RS.world_color(fog[0], 1.0)
    cav, rid, mat = BA.heart_interior('Ventricle', radius, fog=fog, seed=5 if left else 4)
    vmat = BA.muscle_material('BIO_Valve', '#E8B0A8', '#F4CCC4', fog=fog)
    # valve plane at y = -radius*0.9 (outflow) -- built per shot
    return dict(cavity=cav, ridges=rid, mat=mat, valve_mat=vmat)


# ===================================================================================== shots
CLOSEUPS = {'SH01', 'SH04b', 'SH05b', 'SH08', 'SH12a', 'SH02'}


def build_shot(sid):
    f0, f1 = SHOTS[sid]
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = f0, f1 - 1
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 1
    fn = globals()['shot_' + sid]
    fn(f0, f1)
    return {'frames': (f0, f1)}


# ---------------------------------------------------------------- SH01  hook: eyes open, pull back, reveal
def shot_SH01(f0, f1):
    S = set_vein(f0, f1, speed=3.0)
    h = S['hero']
    m, col = mascot()
    rig = place_rig(m, h, loc=(0, 0.15, 0.13), rot=(0, 0, 0))
    # slumped asleep in the dimple of a red blood cell
    m.touched = set()
    pose_sit(m, f0, grip=0.2, lean=24)
    m.touched = set(); m.head_pose(0, 28, 6); m.key(f0)
    m.touched = set(); m.head_pose(0, 26, 6); m.key(f0 + 7)
    expr_key(m, f0, 'neutral', eyes=(0, -0.1))
    m.touched = set(); m.lids(-48, 8); m.key(f0)
    m.touched = set(); m.lids(-48, 8); m.key(f0 + 7)
    # wakes: head snaps up, eyes pop open
    expr_key(m, f0 + 10, 'surprised', eyes=(0.0, 0.05))
    m.touched = set(); m.head_pose(0, -8, 0); m.spine_pose(bend=4); m.key(f0 + 11)
    m.touched = set(); m.head_pose(0, -4, 0); m.key(f0 + 16)
    expr_key(m, f0 + 24, 'surprised', 0.8, eyes=(0.24, 0.05))
    m.touched = set(); m.head_pose(18, -4, 0); m.key(f0 + 26)
    expr_key(m, f0 + 38, 'surprised', 0.8, eyes=(-0.24, 0.05))
    m.touched = set(); m.head_pose(-18, -4, 0); m.key(f0 + 40)
    expr_key(m, f0 + 56, 'curious', eyes=(0.0, 0.12))
    m.touched = set(); m.head_pose(0, -10, 0); m.key(f0 + 58)
    API.blink(m, f0 + 66, base_up=4)
    # spots the pale shape gliding by (camera-right background) on "attack you"
    expr_key(m, f0 + 100, 'scared', eyes=(0.28, 0.08), head=(30, -6, 0))
    m.touched = set(); m.spine_pose(bend=-6, twist=12); m.key(f0 + 102)
    for s in ('L', 'R'):
        m.touched = set(); m.arm(s, raise_=-30, forward=40, elbow=45, wrist=-20); m.hand(s, curl=0.85, thumb=0.6); m.key(f0 + 104)
    expr_key(m, f1 - 1, 'scared', 1.0, eyes=(0.3, 0.06), head=(34, -6, 0))
    body, ctrl, nuc = BA.neutrophil('Shadow', radius=3.4, fog=VEIN_FOG, alpha=0.75)
    body.parent = h
    move_linear(body, f0 + 70, f1, Vector((13, -14, 3)), Vector((5, -13, 2.5)))
    # camera: ECU on the face, then crane up and back to reveal the tunnel
    cam, tgt = SK.cam_rig('Cam', lens=50, fstop=2.2)
    cam.parent = h
    tgt.parent = h
    face = Vector((0, 0.02, 0.80))
    SK.key_cam(cam, tgt, f0, face + Vector((0.06, -0.62, 0.02)), face, lens=50)
    SK.key_cam(cam, tgt, f0 + 18, face + Vector((0.07, -0.66, 0.04)), face, lens=50)
    SK.key_cam(cam, tgt, f0 + 70, Vector((1.4, -2.6, 1.9)), Vector((0, 0.0, 0.6)), lens=32)
    SK.key_cam(cam, tgt, f1 - 1, Vector((2.4, -4.4, 2.3)), Vector((1.2, -2.6, 0.9)), lens=28)
    lights_rig(h)


# ---------------------------------------------------------------- SH02  "That squishy cushion under you?"
def shot_SH02(f0, f1):
    S = set_vein(f0, f1, speed=3.0, seed=2)
    h = S['hero']
    hr = S['hero_rbc']
    m, col = mascot()
    rig = place_rig(m, h, loc=(0, 0.15, 0.13), rot=(0, 0, 20))
    pose_sit(m, f0)
    expr_key(m, f0, 'curious', eyes=(0, -0.2), head=(0, 20, 0))
    # pats with the right hand
    for k, ff in enumerate((f0 + 14, f0 + 28)):
        m.touched = set(); m.arm('R', raise_=-5, forward=30, elbow=55, wrist=20); m.hand('R', curl=0.1); m.key(ff - 6)
        m.touched = set(); m.arm('R', raise_=-24, forward=18, elbow=30, wrist=-15); m.hand('R', curl=0.1); m.key(ff)
        hr.scale = (1, 1, 1); hr.keyframe_insert('scale', frame=ff - 1)
        hr.scale = (1.03, 1.03, 0.90); hr.keyframe_insert('scale', frame=ff + 2)
        hr.scale = (0.99, 0.99, 1.04); hr.keyframe_insert('scale', frame=ff + 6)
        hr.scale = (1, 1, 1); hr.keyframe_insert('scale', frame=ff + 11)
    expr_key(m, f0 + 40, 'happy', 0.7, eyes=(0, -0.15), head=(0, 18, 4))
    m.touched = set(); m.arm('R', raise_=-22, forward=12, elbow=28, wrist=-10); m.hand('R', curl=0.6); m.key(f0 + 52)
    expr_key(m, f0 + 62, 'excited', 0.6, eyes=(0.1, 0.05), head=(10, -4, 0))
    API.blink(m, f0 + 70, base_up=4)
    expr_key(m, f1 - 1, 'excited', 0.7, eyes=(0.12, 0.05), head=(12, -6, 0))
    cam, tgt = SK.cam_rig('Cam', lens=35, fstop=2.8)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((1.9, -1.7, 1.55)), Vector((0, 0.05, 0.62)), lens=38)
    SK.key_cam(cam, tgt, f1 - 1, Vector((1.5, -1.4, 1.45)), Vector((0, 0.05, 0.66)), lens=42)
    lights_rig(h)


# ---------------------------------------------------------------- SH03  wide: millions per drop
def shot_SH03(f0, f1):
    S = set_vein(f0, f1, speed=3.0, seed=3, n_cells=420)
    h = S['hero']
    m, col = mascot()
    place_rig(m, h, loc=(0, 0.15, 0.13), rot=(0, 0, 0))
    pose_sit(m, f0)
    expr_key(m, f0, 'excited', 0.6, eyes=(0.2, 0.15), head=(20, -10, 0))
    expr_key(m, f0 + 45, 'excited', 0.8, eyes=(-0.2, 0.15), head=(-25, -10, 0))
    expr_key(m, f1 - 1, 'happy', 0.8, eyes=(-0.1, 0.2), head=(-15, -14, 0))
    cam, tgt = SK.cam_rig('Cam', lens=24)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((-5.5, 9.0, 5.5)), Vector((0, -2, 0)), lens=24)
    SK.key_cam(cam, tgt, f1 - 1, Vector((-4.0, 6.0, 4.2)), Vector((0, -2.5, 0)), lens=24)
    lights_rig(h, scale=1.6, key_e=2200, rim_e=2500)
    RS.point_light('FarGlow', (0, -40, 0), 40000, (1.0, 0.35, 0.3), 3.0)


# ---------------------------------------------------------------- SH04a  exterior heart beating (map shot)
def shot_SH04a(f0, f1):
    RS.world_gradient((0.02, 0.0, 0.01), (0.06, 0.008, 0.012), (0.01, 0.0, 0.0), 1.0)
    heart, vessels = BA.heart_exterior('Heart')
    heart.rotation_euler = (0, math.radians(-15), math.radians(-20))
    beats = list(range(f0 + 4, f1, 22))
    pulse(heart, beats, amt=-0.06, axis=(1, 1, 1), dur=10)
    # glowing dot (you) sliding down the superior vena cava into the right atrium
    dot = bpy.data.objects.new('YouDot', bpy.data.meshes.new('dot'))
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.03); bm.to_mesh(dot.data); bm.free()
    dm = bpy.data.materials.new('YouDot'); p = dm.node_tree.nodes['Principled BSDF']
    p.inputs['Emission Color'].default_value = hex_rgb('#FFB347'); p.inputs['Emission Strength'].default_value = 40
    dot.data.materials.append(dm)
    bpy.context.scene.collection.objects.link(dot)
    dot.parent = heart
    for k, (f, pos) in enumerate(((f0, (-0.40, 0.14, 0.95)), (f0 + 30, (-0.38, 0.12, 0.60)), (f1 - 1, (-0.35, 0.08, 0.28)))):
        dot.location = pos; dot.keyframe_insert('location', frame=f)
    gl = RS.point_light('DotLight', (0, 0, 0), 15, (1.0, 0.7, 0.3), 0.02); gl.parent = dot
    RS.area_light('Key', (-2.5, -3.5, 2.0), (0, 0, 0), 900, 3.0, (1.0, 0.85, 0.8))
    RS.area_light('Rim', (2.5, 3.0, 1.5), (0, 0, 0), 1800, 2.0, (1.0, 0.4, 0.35))
    RS.area_light('Rim2', (-2.5, 3.0, -1.0), (0, 0, 0), 700, 2.0, (0.5, 0.6, 1.0))
    cam, tgt = SK.cam_rig('Cam', lens=50, fstop=4.0)
    SK.key_cam(cam, tgt, f0, Vector((0.6, -3.6, 0.5)), Vector((-0.12, 0, 0.12)), lens=50)
    SK.key_cam(cam, tgt, f1 - 1, Vector((-0.2, -3.0, 0.65)), Vector((-0.25, 0, 0.30)), lens=58)


# ---------------------------------------------------------------- SH04b  gripping, tunnel pulsing, heart ahead
def shot_SH04b(f0, f1):
    S = set_vein(f0, f1, speed=4.0, seed=4, n_cells=160, start_y=-20)
    h = S['hero']
    tun = S['tunnel']
    beats = [f0 + 6, f0 + 15, f0 + 34, f0 + 43]
    pulse(tun, beats, amt=0.05, axis=(1, 0, 1), dur=7)
    # dark heart opening ahead: a dark glowing ring at the tunnel end
    import bmesh
    ring = bpy.data.objects.new('HeartMouth', bpy.data.meshes.new('hm'))
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=7.5); bm.to_mesh(ring.data); bm.free()
    rm = bpy.data.materials.new('HeartMouth'); p = rm.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0, 0, 0, 1); p.inputs['Emission Color'].default_value = hex_rgb('#3A0208')
    p.inputs['Emission Strength'].default_value = 0.6
    ring.data.materials.append(rm)
    bpy.context.scene.collection.objects.link(ring)
    ring.rotation_euler = (math.radians(90), 0, 0)
    ring.location = (0, -20 - 4.0 * (f1 - f0) / FPS - 22, 0)
    m, col = mascot()
    place_rig(m, h, loc=(0, 0.25, 0.13), rot=(0, 0, 0))
    m.touched = set()
    m.loc('hips', 0, -0.40, 0.02)
    for s in ('L', 'R'):
        m.loc(f'foot_ik.{s}', 0, 0.30, 0.22)
        m.arm(s, raise_=-30, forward=45, elbow=40, wrist=-25)
        m.hand(s, curl=0.85, thumb=0.6)
    m.spine_pose(bend=22)
    m.key(f0)
    expr_key(m, f0, 'scared', 0.7, eyes=(0, 0.0), head=(0, -6, 0))
    for b in beats:
        m.touched = set(); m.spine_pose(bend=26); m.key(b + 1)
        m.touched = set(); m.spine_pose(bend=22); m.key(b + 5)
    expr_key(m, f0 + 30, 'scared', 1.0, eyes=(0, 0.02), head=(0, -8, 0))
    expr_key(m, f1 - 1, 'shocked', 0.7, eyes=(0, 0.02), head=(0, -10, 0))
    cam, tgt = SK.cam_rig('Cam', lens=32, fstop=2.8)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((0.85, 1.7, 1.75)), Vector((0, -1.5, 0.9)), lens=30)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.7, 1.3, 1.65)), Vector((0, -2.5, 0.8)), lens=30)
    for b in beats:
        SK.shake(cam, b, b + 5, amp=0.03, seed=b)
    lights_rig(h, key_e=380, rim_e=1600)
    RS.point_light('AheadGlow', (0, -60, 0), 15000, (1.0, 0.2, 0.15), 4.0)


# ---------------------------------------------------------------- heart interior shots
def _chamber_with_valve(f0, f1, valve_keys, left=False, valve_y=-6.0, radius=11.0, cusps=3):
    H = set_heart_chamber(f0, f1, radius, left)
    root, leaves = BA.valve('Valve', 5.2, cusps=cusps, mat=H['valve_mat'], thickness=0.14)
    root.location = (0, valve_y, 0)
    BA.animate_valve(leaves, valve_keys)
    # chordae from papillary muscles below to the leaflet tips (AV valves)
    if not left:
        anchors = [(math.cos(a) * 3.5, valve_y + 6.5, -6.5) for a in (0.3, 2.4, 4.4)]
        tips = [(math.cos(a) * 1.2, valve_y + 1.0, math.sin(a) * 1.2 - 0.6) for a in (0.3, 2.4, 4.4)]
        BA.chordae('Chordae', anchors, tips, H['mat'], r=0.06)
    return H, root, leaves


def shot_SH05a(f0, f1):
    slam = 491
    H, root, leaves = _chamber_with_valve(f0, f1, [(f0, 1.0), (slam - 3, 0.95), (slam + 1, 0.0), (f1, 0.0)],
                                          valve_y=-2.0)
    pulse(H['cavity'], [slam], amt=0.03, axis=(1, 1, 1), dur=10)
    h = hero()
    move_linear(h, f0, f1, Vector((0, 1.5, -0.6)), Vector((0, 7.5, -0.4)))  # moving away from the valve
    rmesh = BA.rbc_mesh('RBC_mesh'); rmat = BA.rbc_material('BIO_RBC', fog=HEART_FOG); rmesh.materials.append(rmat)
    hr = hero_rbc(h, rmesh)
    hr.rotation_euler = (0, 0, 0)
    BA.flow_cells(rmesh, rmat, 90, 9.0, (-10, 14), -2.0, f0, f1, seed=5)
    m, col = mascot()
    place_rig(m, h, loc=(0, 0.1, 0.13), rot=(0, 0, 180))   # facing the valve (looking back)
    pose_sit(m, f0)
    expr_key(m, f0, 'curious', eyes=(0, 0.1), head=(0, -6, 0))
    expr_key(m, slam - 2, 'curious', eyes=(0, 0.1), head=(0, -6, 0))
    expr_key(m, slam + 2, 'shocked', eyes=(0, 0.05), head=(0, -12, 0))
    m.touched = set(); m.spine_pose(bend=-14); m.arm('L', raise_=10, forward=40, elbow=70); m.arm('R', raise_=10, forward=40, elbow=70); m.key(slam + 3)
    m.touched = set(); m.spine_pose(bend=-6); m.arm('L', raise_=-10, forward=30, elbow=60); m.arm('R', raise_=-10, forward=30, elbow=60); m.key(f1 - 1)
    expr_key(m, f1 - 1, 'scared', eyes=(0, 0.05), head=(0, -8, 0))
    cam, tgt = SK.cam_rig('Cam', lens=26, fstop=5.6)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((1.1, 2.3, 1.6)), Vector((0, -4.0, 0.2)), lens=26)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.9, 2.0, 1.5)), Vector((0, -5.0, 0.4)), lens=26)
    SK.shake(cam, slam, slam + 12, amp=0.10, seed=3)
    RS.area_light('Key', (-4, 10, 5), (0, 4, 0), 3000, 5, (1.0, 0.8, 0.75))
    RS.area_light('ValveLight', (0, -6, 4), (0, -2, 0), 2500, 6, (1.0, 0.5, 0.45))
    RS.point_light('Under', (3, 5, -4), 900, (1.0, 0.3, 0.25), 1.0)


def shot_SH05b(f0, f1):
    lub, dub = 540, 550
    H, root, leaves = _chamber_with_valve(f0, f1, [(f0, 0.0), (f1, 0.0)], valve_y=-4.0)
    pulse(H['cavity'], [lub, dub], amt=0.04, axis=(1, 1, 1), dur=6)
    h = hero()
    move_linear(h, f0, f1, Vector((0, 7.5, -0.4)), Vector((0, 10.5, -0.2)))
    rmesh = BA.rbc_mesh('RBC_mesh'); rmat = BA.rbc_material('BIO_RBC', fog=HEART_FOG); rmesh.materials.append(rmat)
    hero_rbc(h, rmesh)
    BA.flow_cells(rmesh, rmat, 60, 9.0, (-4, 20), -1.2, f0, f1, seed=6)
    m, col = mascot()
    place_rig(m, h, loc=(0, 0.1, 0.13), rot=(0, 0, 180))
    pose_sit(m, f0)
    expr_key(m, f0, 'scared', eyes=(0, 0.05), head=(0, -6, 0))
    for b in (lub, dub):
        m.touched = set(); m.spine_pose(bend=-4); m.head_pose(0, -4, 0); m.key(b - 1)
        m.touched = set(); m.spine_pose(bend=10); m.head_pose(0, 8, 0); m.key(b + 2)
        m.touched = set(); m.lids(-46, 10); m.key(b + 1)
        m.touched = set(); m.lids(8, -6); m.key(b + 5)
    expr_key(m, dub + 8, 'shocked', 0.8, eyes=(0, 0.05), head=(0, -4, 0))
    expr_key(m, f1 - 1, 'surprised', 0.9, eyes=(-0.2, 0.0), head=(-12, -4, 0))
    cam, tgt = SK.cam_rig('Cam', lens=50, fstop=2.0)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((0.32, 1.75, 0.98)), Vector((0, 0.12, 0.86)), lens=55)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.24, 1.45, 0.96)), Vector((0, 0.12, 0.86)), lens=55)
    SK.shake(cam, lub, lub + 8, amp=0.035, seed=5)
    SK.shake(cam, dub, dub + 10, amp=0.045, seed=6)
    lights_rig(h, key_e=700, rim_e=1600)


def shot_SH06a(f0, f1):
    H, root, leaves = _chamber_with_valve(f0, f1, [(f0, 0.0), (f0 + 14, 0.0), (f0 + 20, 1.0), (f1, 1.0)],
                                          valve_y=-8.0)
    cav = H['cavity']
    for ob in (cav, H['ridges']):
        ob.keyframe_insert('scale', frame=f0)
        ob.scale = (0.84, 0.92, 0.84)
        ob.keyframe_insert('scale', frame=f0 + 16)
    h = hero()
    h.location = (0, 2.0, 0); h.keyframe_insert('location', frame=f0 + 8)
    h.location = (0, -4.5, 0); h.keyframe_insert('location', frame=f1 - 1)
    rmesh = BA.rbc_mesh('RBC_mesh'); rmat = BA.rbc_material('BIO_RBC', fog=HEART_FOG); rmesh.materials.append(rmat)
    hero_rbc(h, rmesh)
    BA.flow_cells(rmesh, rmat, 80, 8.0, (-30, 10), 14.0, f0 + 10, f1, seed=8)
    m, col = mascot()
    place_rig(m, h, loc=(0, 0.1, 0.13), rot=(0, 0, 0))
    m.touched = set()
    m.loc('hips', 0, -0.40, 0.0)
    for s in ('L', 'R'):
        m.loc(f'foot_ik.{s}', 0, 0.30, 0.22)
        m.arm(s, raise_=-30, forward=45, elbow=40, wrist=-25)
        m.hand(s, curl=0.9, thumb=0.6)
    m.spine_pose(bend=24)
    m.key(f0)
    expr_key(m, f0, 'scared', eyes=(0, 0.05))
    expr_key(m, f0 + 16, 'shocked', 1.0, eyes=(0, 0.1), head=(0, -14, 0))
    m.touched = set(); m.spine_pose(bend=-10); m.key(f0 + 20)
    cam, tgt = SK.cam_rig('Cam', lens=24)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((1.4, 2.6, 1.2)), Vector((0, -1, 0.6)), lens=24)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.9, 3.4, 1.0)), Vector((0, -2, 0.6)), lens=18)
    SK.shake(cam, f0 + 14, f1 - 1, amp=0.06, seed=7, decay=False)
    lights_rig(h)
    RS.area_light('ValveLight', (0, -12, 3), (0, -8, 0), 3000, 6, (1.0, 0.6, 0.5))


# ---------------------------------------------------------------- capillary shots
def shot_SH06b(f0, f1):
    C = set_capillary(f0, f1, speed=0.8, n_cells=0)
    h = hero()
    move_linear(h, f0, f1, Vector((0, 0.0, 0)), Vector((0, -0.8 * (f1 - f0) / FPS, 0)))
    # two folded cells squeezing him: one pushing from behind, one just ahead
    pm = C['rbc_mesh']
    for nm, y in (('PushCell', 2.05), ('AheadCell', -1.15)):
        c = bpy.data.objects.new(nm, pm); bpy.context.scene.collection.objects.link(c)
        c.parent = h; c['oxy'] = 0.0
        c.location = (0.0, y, -0.15); c.rotation_euler = (math.radians(90), 0, 0); c.scale = (0.75, 0.75, 0.95)
        c.keyframe_insert('location', frame=f0)
        c.location = (0.0, y - 0.15, -0.15); c.keyframe_insert('location', frame=f1 - 1)
    m, col = mascot()
    # squeezing forward between two folded cells, body pitched forward (crawling)
    place_rig(m, h, loc=(0, 0.6, -0.95), rot=(-35, 0, 0))
    m.touched = set()
    m.loc('hips', 0, -0.10, 0.0)
    for s in ('L', 'R'):
        m.arm(s, raise_=45, forward=90, elbow=30)
        m.hand(s, curl=0.2, spread=0.5)
    m.spine_pose(bend=10)
    m.key(f0)
    for k, ff in enumerate(range(f0, f1, 16)):
        a = 1 if k % 2 == 0 else -1
        m.touched = set()
        m.arm('L', raise_=45 + 10 * a, forward=90 + 15 * a, elbow=30 + 20 * a)
        m.arm('R', raise_=45 - 10 * a, forward=90 - 15 * a, elbow=30 - 20 * a)
        m.loc('foot_ik.L', 0, 0.05 * a, 0.08 * max(0, a))
        m.loc('foot_ik.R', 0, -0.05 * a, 0.08 * max(0, -a))
        m.key(ff)
    expr_key(m, f0, 'angry', 0.6, eyes=(0, 0.1))
    m.touched = set(); m.shape('cheek_puff', 0.9); m.shape('lips_press', 0.6); m.key(f0 + 30)
    expr_key(m, f0 + 60, 'disgusted', 0.6, eyes=(0.1, 0.1))
    expr_key(m, f1 - 1, 'angry', 0.5, eyes=(0, 0.1))
    # a cell pressing against him from the front (comic squash)
    front = [c for c in C['cells'] if abs(c.location.y - (-3.4)) < 0.3]
    cam, tgt = SK.cam_rig('Cam', lens=20, fstop=4.0)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((0.62, -0.55, -0.15)), Vector((0, 0.75, -0.45)), lens=20)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.55, -0.45, -0.12)), Vector((0, 0.8, -0.45)), lens=20)
    RS.area_light('Key', (-0.5, -1.6, 0.6), (0, 0.5, -0.5), 260, 1.0, (1.0, 0.85, 0.8)).parent = h
    fl = RS.area_light('Fill', (0.9, -0.8, -0.6), (0, 0.6, -0.5), 90, 1.0, (1.0, 0.7, 0.75)); fl.parent = h
    fl.data.use_shadow = False


def _cap_gas(C, f0, f1, side=1, o2=True, co2=True, n=60):
    if o2:
        BA.gas_particles('O2', n, ((side * 2.5, -6, -1.5), (side * 5.5, 6, 2.5)), ((-0.6, -6, -0.6), (0.6, 6, 0.6)),
                         f0, f1, '#5AB8FF', 6.0, 0.05, seed=12)
    if co2:
        BA.gas_particles('CO2', int(n * 0.6), ((-0.6, -6, -0.6), (0.6, 6, 0.6)), ((side * 2.5, -6, -1.0), (side * 6, 6, 3.0)),
                         f0, f1, '#B9B3C2', 2.5, 0.045, seed=13)


def shot_SH07a(f0, f1):
    C = set_capillary(f0, f1, speed=0.5, wall_alpha=0.5)
    _cap_gas(C, f0, f1, co2=False, n=90)
    for c in C['cells']:
        c['oxy'] = 0.0
        c.keyframe_insert('["oxy"]', frame=f0 + 10)
        c['oxy'] = 1.0
        c.keyframe_insert('["oxy"]', frame=f1 - 20)
    h = hero()
    move_linear(h, f0, f1, Vector((0, 0.0, 0)), Vector((0, -0.5 * (f1 - f0) / FPS, 0)))
    m, col = mascot()
    place_rig(m, h, loc=(-0.25, 0.4, -1.1), rot=(0, 0, 70))   # standing, turned towards the alveolus
    m.touched = set(); m.loc('hips', 0, -0.06, 0)
    for s in ('L', 'R'):
        m.arm(s, raise_=-6, forward=10, elbow=20); m.hand(s, curl=0.2)
    m.key(f0)
    expr_key(m, f0, 'curious', eyes=(0.0, 0.05))
    expr_key(m, f0 + 30, 'surprised', 0.8, eyes=(0.15, 0.08), head=(10, -6, 0))
    API.point_at(m, 'R', f0 + 45, raise_=55, forward=70, hold=40)
    expr_key(m, f0 + 60, 'excited', 0.9, eyes=(0.2, 0.1), head=(14, -8, 0))
    API.blink(m, f0 + 92, base_up=6)
    expr_key(m, f1 - 1, 'happy', 0.9, eyes=(0.1, 0.05), head=(8, -4, 0))
    cam, tgt = SK.cam_rig('Cam', lens=24, fstop=3.2)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((-0.75, -1.9, -0.35)), Vector((0.25, 0.5, -0.5)), lens=22)
    SK.key_cam(cam, tgt, f1 - 1, Vector((-0.65, -1.55, -0.3)), Vector((0.35, 0.55, -0.45)), lens=24)
    RS.area_light('Key', (-1.2, -2.0, 0.8), (0, 0.5, -0.4), 160, 1.0, (1.0, 0.88, 0.85)).parent = h


def shot_SH07b(f0, f1):
    C = set_capillary(f0, f1, speed=0.5, wall_alpha=0.5)
    _cap_gas(C, f0, f1, o2=True, co2=True, n=50)
    for c in C['cells']:
        c['oxy'] = 1.0
    h = hero()
    move_linear(h, f0, f1, Vector((0, 0.0, 0)), Vector((0, -0.5 * (f1 - f0) / FPS, 0)))
    m, col = mascot()
    place_rig(m, h, loc=(-0.25, 0.4, -1.1), rot=(0, 0, 70))
    m.touched = set(); m.loc('hips', 0, -0.06, 0)
    for s in ('L', 'R'):
        m.arm(s, raise_=-6, forward=10, elbow=20); m.hand(s, curl=0.2)
    m.key(f0)
    expr_key(m, f0, 'happy', 0.8, eyes=(0.1, 0.05))
    expr_key(m, f0 + 50, 'curious', 0.9, eyes=(0.25, 0.25), head=(12, -10, 0))
    # the planted shadow: something big glides past on the far side
    body, ctrl, nuc = BA.neutrophil('Shadow', radius=1.7, fog=CAP_FOG, alpha=0.9)
    move_linear(body, f1 - 45, f1, Vector((0.0, 9.0, 0.0)), Vector((0.0, 4.2, 0.0)))
    expr_key(m, f1 - 12, 'curious', 0.9, eyes=(-0.25, 0.0), head=(-20, -2, 0))
    expr_key(m, f1 - 1, 'scared', 0.5, eyes=(-0.3, 0.0), head=(-28, -2, 0))
    cam, tgt = SK.cam_rig('Cam', lens=22, fstop=4.0)
    SK.key_cam(cam, tgt, f0, Vector((-0.75, -1.9, -0.3)), Vector((0.3, 0.5, -0.45)), lens=22)
    SK.key_cam(cam, tgt, f0 + 60, Vector((-0.4, -2.4, -0.1)), Vector((1.2, 0.2, -0.1)), lens=22)
    SK.key_cam(cam, tgt, f1 - 1, Vector((-0.9, -2.6, -0.2)), Vector((0.2, 0.8, -0.3)), lens=22)
    RS.area_light('Key', (-1.2, -2.5, 1.0), (0, 0, -0.4), 160, 1.0, (1.0, 0.88, 0.85))


def _capillary_with_neutrophil(f0, f1, n_pos0, n_pos1, alpha=0.6):
    C = set_capillary(f0, f1, speed=0.0, n_cells=10)
    for c in C['cells']:
        c['oxy'] = 1.0
    body, ctrl, nuc = BA.neutrophil('Neutrophil', radius=1.65, fog=CAP_FOG, alpha=alpha)
    body.scale = (0.78, 1.35, 0.78)       # squeezed into the narrow capillary
    move_linear(body, f0, f1, n_pos0, n_pos1)
    ctrl.location = (0, 0, 0); ctrl.keyframe_insert('location', frame=f0)
    ctrl.location = (0.6, 0.9, 0.4); ctrl.keyframe_insert('location', frame=f1)
    BA.linear_keys(ctrl)
    # remove cells that overlap the neutrophil path
    for c in list(C['cells']):
        if n_pos1.y - 3 < c.location.y < n_pos0.y + 3:
            bpy.data.objects.remove(c)
    return C, body, ctrl, nuc


def shot_SH08(f0, f1):
    C, body, ctrl, nuc = _capillary_with_neutrophil(f0, f1, Vector((0, 7.5, -0.1)), Vector((0, 4.6, -0.1)), alpha=0.7)
    m, col = mascot()
    place_rig(m, None, loc=(0.0, 0.0, -1.12), rot=(0, 0, 0))
    m.touched = set(); m.loc('hips', 0, -0.05, 0)
    for s in ('L', 'R'):
        m.arm(s, raise_=-8, forward=8, elbow=18); m.hand(s, curl=0.25)
    m.key(f0)
    expr_key(m, f0, 'happy', 0.5, eyes=(0, 0.05))
    expr_key(m, f0 + 30, 'curious', 0.8, eyes=(0.0, 0.05))
    expr_key(m, f0 + 48, 'curious', 1.0, eyes=(0.25, 0.0), head=(8, 0, 0))   # eyes slide sideways
    expr_key(m, f1 - 8, 'scared', 0.9, eyes=(0.3, 0.0), head=(10, 0, 0))
    cam, tgt = SK.cam_rig('Cam', lens=35, fstop=1.8)
    cam.data.dof.focus_object = None
    cam.data.dof.focus_distance = 1.6
    SK.key_cam(cam, tgt, f0, Vector((0.25, -2.6, -0.05)), Vector((0, 0.0, -0.05)), lens=35)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.12, -1.25, -0.02)), Vector((0, 0.0, -0.02)), lens=45)
    cam.data.dof.focus_distance = 2.6
    cam.data.dof.keyframe_insert('focus_distance', frame=f0)
    cam.data.dof.focus_distance = 1.2
    cam.data.dof.keyframe_insert('focus_distance', frame=f1 - 1)
    RS.area_light('Key', (-0.8, -2.0, 0.8), (0, 0, 0), 140, 1.0, (1.0, 0.88, 0.85))
    RS.point_light('Rim', (0.6, 1.5, 0.6), 60, (0.85, 0.75, 1.0), 0.3)


def shot_SH09a(f0, f1):
    C, body, ctrl, nuc = _capillary_with_neutrophil(f0, f1, Vector((0, 4.3, -0.1)), Vector((0, 3.4, -0.1)), alpha=0.6)
    m, col = mascot()
    place_rig(m, None, loc=(0.0, 0.0, -1.12), rot=(0, 0, 0))
    m.touched = set(); m.loc('hips', 0, -0.10, 0)
    for s in ('L', 'R'):
        m.arm(s, raise_=20, forward=30, elbow=60); m.hand(s, curl=0.1, spread=0.8)
    m.spine_pose(bend=-10)
    m.key(f0)
    expr_key(m, f0, 'scared', 1.0, eyes=(0.2, 0.2), head=(35, -14, 0))
    m.touched = set(); m.spine_pose(bend=-10, twist=25); m.key(f0 + 10)
    expr_key(m, f1 - 1, 'shocked', 0.9, eyes=(0.25, 0.25), head=(45, -18, 0))
    cam, tgt = SK.cam_rig('Cam', lens=18)
    SK.key_cam(cam, tgt, f0, Vector((0.7, -1.9, -1.0)), Vector((0, 2.4, 0.3)), lens=17)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.6, -1.5, -1.05)), Vector((0, 2.8, 0.6)), lens=17)
    RS.area_light('Key', (-0.9, -2.0, 0.5), (0, 0.5, -0.3), 140, 1.0, (1.0, 0.88, 0.85))
    RS.point_light('CellGlow', (0, 3.0, 0.8), 250, (0.8, 0.7, 1.0), 0.5)


def shot_SH09b(f0, f1):
    grab = 1240
    C, body, ctrl, nuc = _capillary_with_neutrophil(f0, f1, Vector((0, 3.4, -0.1)), Vector((0, 2.5, -0.1)), alpha=0.6)
    m, col = mascot()
    rig = place_rig(m, None, loc=(0.0, 0.0, -1.12), rot=(0, 0, 0))
    # backs away (towards -Y), bumps the cell behind, then gets grabbed by the leg
    rig.keyframe_insert('location', frame=f0)
    rig.location = (0.0, -0.9, -1.12); rig.keyframe_insert('location', frame=f0 + 50)
    rig.location = (0.0, -0.75, -1.12); rig.keyframe_insert('location', frame=f0 + 56)
    rig.location = (0.0, -0.45, -1.12); rig.keyframe_insert('location', frame=grab + 20)
    rig.location = (0.0, -0.2, -1.05); rig.keyframe_insert('location', frame=f1 - 1)
    for k, ff in enumerate(range(f0, f0 + 50, 10)):
        a = 1 if k % 2 == 0 else -1
        m.touched = set()
        m.loc('foot_ik.L', 0, 0.12 * a, 0.05 * max(0, a)); m.loc('foot_ik.R', 0, -0.12 * a, 0.05 * max(0, -a))
        m.arm('L', raise_=25, forward=35, elbow=55); m.arm('R', raise_=25, forward=35, elbow=55)
        m.spine_pose(bend=-8)
        m.key(ff)
    expr_key(m, f0, 'scared', 1.0, eyes=(0, 0.2), head=(0, -14, 0))
    expr_key(m, f0 + 52, 'shocked', 1.0, eyes=(-0.25, 0.0), head=(-25, 0, 0))   # bumped: looks behind
    expr_key(m, f0 + 66, 'scared', 1.0, eyes=(0, 0.2), head=(0, -14, 0))
    # pseudopods reach for the left leg
    pm = bpy.data.materials['BIO_NeutrophilMembrane']
    pods = []
    for i, (st, en) in enumerate((((0.25, 1.7, -1.3), (0.15, 0.25, -1.75)), ((-0.25, 1.6, -1.1), (0.05, 0.15, -1.45)))):
        pod = BA.pseudopod(f'Pod{i}', Vector(st), Vector(en), 0.42, pm)
        pod.scale = (1, 0.05, 1); pod.keyframe_insert('scale', frame=grab - 25)
        pod.scale = (1, 1.1, 1); pod.keyframe_insert('scale', frame=grab)
        pod.scale = (1, 1.0, 1); pod.keyframe_insert('scale', frame=f1 - 1)
        pods.append(pod)
    m.touched = set()
    m.loc('foot_ik.L', 0, -0.25, 0.15); m.loc('foot_ik.R', 0, 0.1, 0.0)
    m.arm('L', raise_=80, forward=20, elbow=40); m.arm('R', raise_=70, forward=50, elbow=30)
    m.spine_pose(bend=18)
    m.key(grab + 4)
    for k, ff in enumerate(range(grab + 8, f1, 8)):
        a = 1 if k % 2 == 0 else -1
        m.touched = set()
        m.arm('L', raise_=80 + 25 * a, forward=20 + 20 * a, elbow=40)
        m.arm('R', raise_=70 - 25 * a, forward=50 - 20 * a, elbow=30)
        m.key(ff)
    expr_key(m, grab, 'shocked', 1.0, eyes=(0, -0.2), head=(0, 18, 0))
    expr_key(m, f1 - 1, 'scared', 1.0, eyes=(0, -0.25), head=(0, 22, 0))
    cam, tgt = SK.cam_rig('Cam', lens=20)
    SK.key_cam(cam, tgt, f0, Vector((0.9, -2.6, -0.4)), Vector((0, 1.0, -0.4)), lens=20)
    SK.key_cam(cam, tgt, grab - 10, Vector((1.0, -2.2, -0.6)), Vector((0, 0.0, -0.6)), lens=20)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.8, -1.5, -0.9)), Vector((0, 0.2, -1.1)), lens=22)
    SK.shake(cam, grab, grab + 10, amp=0.04, seed=11)
    RS.area_light('Key', (-1.0, -2.2, 0.6), (0, 0, -0.5), 150, 1.0, (1.0, 0.88, 0.85))
    RS.point_light('CellGlow', (0, 3.0, 0.8), 250, (0.8, 0.7, 1.0), 0.5)


def _sneaker_prop(col):
    src = [o for o in col.objects if o.name.startswith('MSC_Shoe_L')][0]
    prop = src.copy()
    prop.data = src.data.copy()
    prop.modifiers.remove(prop.modifiers['Armature'])
    prop.parent = None
    prop.vertex_groups.clear()
    bpy.context.scene.collection.objects.link(prop)
    prop.name = 'LostSneaker'
    prop.hide_render = False
    return prop


def shot_SH10(f0, f1):
    kick = 1310
    C, body, ctrl, nuc = _capillary_with_neutrophil(f0, f1, Vector((0, 2.5, -0.1)), Vector((0, 2.3, -0.1)), alpha=0.6)
    pm = bpy.data.materials['BIO_NeutrophilMembrane']
    pod = BA.pseudopod('Pod0', Vector((0.25, 1.7, -1.3)), Vector((0.15, 0.05, -1.75)), 0.42, pm)
    pod.scale = (1, 1.0, 1); pod.keyframe_insert('scale', frame=kick)
    pod.scale = (1, 0.75, 1); pod.keyframe_insert('scale', frame=kick + 6)
    m, col = mascot()
    rig = place_rig(m, None, loc=(0.0, -0.2, -1.05), rot=(0, 0, 0))
    rig.keyframe_insert('location', frame=kick)
    rig.keyframe_insert('rotation_euler', frame=kick)
    rig.location = (0.3, -4.5, -0.6); rig.rotation_euler = (math.radians(-60), math.radians(40), math.radians(30))
    rig.keyframe_insert('location', frame=f1 - 1); rig.keyframe_insert('rotation_euler', frame=f1 - 1)
    m.touched = set()
    m.loc('foot_ik.L', 0, -0.25, 0.15); m.loc('foot_ik.R', 0, 0.1, 0.0)
    m.arm('L', raise_=80, forward=20, elbow=40); m.arm('R', raise_=70, forward=50, elbow=30)
    m.spine_pose(bend=18); m.key(f0)
    m.touched = set(); m.loc('foot_ik.L', 0, -0.05, 0.30); m.spine_pose(bend=28); m.key(kick - 6)  # anticipation
    m.touched = set(); m.loc('foot_ik.L', 0, 0.35, 0.10); m.spine_pose(bend=-10)
    m.arm('L', raise_=110, forward=-20, elbow=20); m.arm('R', raise_=100, forward=-10, elbow=20); m.key(kick + 2)
    m.touched = set(); m.loc('foot_ik.L', 0, 0.2, 0.2); m.arm('L', raise_=60, forward=40, elbow=50)
    m.arm('R', raise_=50, forward=60, elbow=60); m.key(f1 - 1)
    expr_key(m, f0, 'angry', 1.0, eyes=(0, -0.2), head=(0, 14, 0))
    expr_key(m, kick, 'angry', 1.0, eyes=(0, -0.2), head=(0, 14, 0))
    expr_key(m, kick + 6, 'shocked', 1.0, eyes=(0, 0.0), head=(0, -10, 0))
    SK.set_shoe_visible(col, 'L', True, frame=kick)
    SK.set_shoe_visible(col, 'L', False, frame=kick + 1)
    sneaker = _sneaker_prop(col)
    sneaker.hide_render = True; sneaker.keyframe_insert('hide_render', frame=kick)
    sneaker.hide_render = False; sneaker.keyframe_insert('hide_render', frame=kick + 1)
    sneaker.location = (0.12, -0.15, -1.62); sneaker.keyframe_insert('location', frame=kick + 1)
    sneaker.location = (0.10, 0.25, -1.45); sneaker.keyframe_insert('location', frame=f1 - 1)
    cam, tgt = SK.cam_rig('Cam', lens=20)
    SK.key_cam(cam, tgt, f0, Vector((0.7, -2.0, -0.55)), Vector((0, 0.0, -1.1)), lens=20)
    SK.key_cam(cam, tgt, kick + 4, Vector((0.75, -2.4, -0.45)), Vector((0, -0.6, -0.95)), lens=20)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.7, -6.8, -0.1)), Vector((0.2, -4.3, -0.6)), lens=22)
    SK.shake(cam, kick, kick + 10, amp=0.06, seed=12)
    RS.area_light('Key', (-1.0, -2.5, 0.6), (0, -1, -0.5), 170, 1.2, (1.0, 0.88, 0.85))
    RS.point_light('CellGlow', (0, 3.0, 0.8), 250, (0.8, 0.7, 1.0), 0.5)


def shot_SH11a(f0, f1):
    S = set_vein(f0, f1, speed=9.0, seed=5, n_cells=220, hero_on=False)
    h = S['hero']
    m, col = mascot()
    rig = place_rig(m, h, loc=(0, 0, 0), rot=(0, 0, 0))
    SK.set_shoe_visible(col, 'L', False)
    for k, ff in enumerate(range(f0, f1, 6)):
        rig.rotation_euler = (math.radians(-60 - 55 * k), math.radians(25 * math.sin(k)), math.radians(15 * k))
        rig.keyframe_insert('rotation_euler', frame=ff)
        a = 1 if k % 2 == 0 else -1
        m.touched = set()
        m.arm('L', raise_=100 + 30 * a, forward=20 * a, elbow=30); m.arm('R', raise_=100 - 30 * a, forward=-20 * a, elbow=30)
        m.loc('foot_ik.L', 0, 0.1 * a, 0.2); m.loc('foot_ik.R', 0, -0.1 * a, 0.15)
        m.hand('L', spread=1.0); m.hand('R', spread=1.0)
        m.key(ff)
    expr_key(m, f0, 'shocked', 1.0)
    expr_key(m, f1 - 1, 'scared', 1.0)
    cam, tgt = SK.cam_rig('Cam', lens=24)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((1.5, -3.0, 1.2)), Vector((0, 0, 0.6)), lens=24)
    SK.key_cam(cam, tgt, f1 - 1, Vector((-1.2, -2.6, 1.0)), Vector((0, 0, 0.6)), lens=24)
    SK.shake(cam, f0, f1 - 1, amp=0.05, seed=13, decay=False)
    lights_rig(h)


def shot_SH11b(f0, f1):
    burst = 1420
    H, root, leaves = _chamber_with_valve(f0, f1, [(f0, 0.0), (burst - 3, 0.0), (burst + 3, 1.0), (f1, 1.0)],
                                          left=True, valve_y=-7.0)
    for ob in (H['cavity'], H['ridges']):
        ob.keyframe_insert('scale', frame=f0 + 2)
        ob.scale = (0.82, 0.90, 0.82)
        ob.keyframe_insert('scale', frame=burst)
    h = hero()
    h.location = (0.2, 2.5, 0.3); h.keyframe_insert('location', frame=f0)
    h.location = (0.1, -3.0, 0.1); h.keyframe_insert('location', frame=burst)
    h.location = (0.0, -16.0, 0.0); h.keyframe_insert('location', frame=f1 - 1)
    m, col = mascot()
    place_rig(m, h, loc=(0, 0.6, -0.5), rot=(78, 0, 0))    # superman pose, head-first towards the valve
    SK.set_shoe_visible(col, 'L', False)
    m.touched = set()
    for s_ in ('L', 'R'):
        m.arm(s_, raise_=150, forward=10, elbow=10); m.hand(s_, spread=0.8)
        m.loc(f'foot_ik.{s_}', 0, -0.1, 0.1)
    m.key(f0)
    expr_key(m, f0, 'scared', 1.0, eyes=(0, 0.25), head=(0, -40, 0))
    expr_key(m, burst, 'shocked', 1.0, eyes=(0, 0.25), head=(0, -40, 0))
    cam, tgt = SK.cam_rig('Cam', lens=24)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((1.1, 2.6, 0.9)), Vector((0, -2.5, -0.1)), lens=24)
    SK.key_cam(cam, tgt, burst, Vector((0.9, 2.3, 0.8)), Vector((0, -3.0, -0.1)), lens=24)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.7, 2.0, 0.6)), Vector((0, -4.0, -0.1)), lens=20)
    SK.shake(cam, burst, f1 - 1, amp=0.07, seed=14)
    lights_rig(h)
    RS.area_light('ValveLight', (0, -14, 4), (0, -7, 0), 6000, 8, (1.0, 0.7, 0.55))


def set_aorta(f0, f1, speed=12.0, radius=14.0, n=300, seed=6):
    RS.world_color(AORTA_FOG[0], 1.0)
    wall = BA.vessel_material('BIO_AortaWall', base='#9A2A30', cell='#D05A5E', fog=AORTA_FOG, emission=('#FF6A50', 0.05))
    tun = BA.vessel_tunnel('Aorta', radius, 400, wall, segs=64, seed=seed, bumps=0.05, y0=150)
    rmesh = BA.rbc_mesh('RBC_mesh'); rmat = BA.rbc_material('BIO_RBC', fog=AORTA_FOG); rmesh.materials.append(rmat)
    h = hero()
    dur = (f1 - f0) / FPS
    move_linear(h, f0, f1, Vector((0, 0, 0)), Vector((0, -speed * dur, 0)))
    cells = BA.flow_cells(rmesh, rmat, n, radius * 0.85, (-speed * dur - 60, 40), speed, f0, f1, seed=seed, oxy=1.0)
    _clear_around_hero(cells, h, f0, f1, 3.0)
    BA.specks(200, radius * 0.9, (-speed * dur - 60, 40), speed * 0.4, f0, f1, color='#FFD0A0', strength=3.0,
              size=(0.02, 0.06))
    RS.point_light('AortaGlow', (0, -speed * dur - 80, 0), 120000, (1.0, 0.75, 0.55), 8.0)
    return dict(hero=h, tunnel=tun, cells=cells, rbc_mesh=rmesh, rbc_mat=rmat)


def shot_SH11c(f0, f1):
    A = set_aorta(f0, f1, speed=14.0)
    h = A['hero']
    m, col = mascot()
    rig = place_rig(m, h, loc=(0, 0.7, 0), rot=(80, 0, 0))
    SK.set_shoe_visible(col, 'L', False)
    for k, ff in enumerate(range(f0, f1, 10)):
        a = 1 if k % 2 == 0 else -1
        m.touched = set()
        m.arm('L', raise_=145 + 8 * a, forward=10, elbow=12); m.arm('R', raise_=145 - 8 * a, forward=10, elbow=12)
        m.loc('foot_ik.L', 0, -0.1, 0.12 + 0.05 * a); m.loc('foot_ik.R', 0, -0.1, 0.12 - 0.05 * a)
        m.hand('L', spread=0.6); m.hand('R', spread=0.6)
        m.key(ff)
    rig.rotation_euler = (math.radians(80), 0, 0); rig.keyframe_insert('rotation_euler', frame=f0)
    rig.rotation_euler = (math.radians(80), math.radians(25), math.radians(-10)); rig.keyframe_insert('rotation_euler', frame=f1 - 1)
    expr_key(m, f0, 'shocked', 1.0, eyes=(0, 0.3), head=(0, -42, 0))
    expr_key(m, f0 + 30, 'excited', 1.0, eyes=(0, 0.3), head=(0, -42, 0))
    expr_key(m, f1 - 1, 'laughing', 0.8, eyes=(0, 0.25), head=(0, -40, 0))
    cam, tgt = SK.cam_rig('Cam', lens=18)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((0.35, -2.1, 0.25)), Vector((0, 0.2, 0.0)), lens=26)
    SK.key_cam(cam, tgt, f0 + 35, Vector((1.6, -1.1, 0.6)), Vector((0, 0.0, 0.1)), lens=26)
    SK.key_cam(cam, tgt, f1 - 1, Vector((2.0, 2.4, 1.1)), Vector((0, -1.5, 0)), lens=22)
    SK.shake(cam, f0, f0 + 20, amp=0.08, seed=15)
    lights_rig(h, key_e=1200, rim_e=2200)


def shot_SH12a(f0, f1):
    A = set_aorta(f0, f1, speed=4.0, n=220, seed=7)
    h = A['hero']
    hr = hero_rbc(h, A['rbc_mesh'], oxy=1.0)
    m, col = mascot()
    rig = place_rig(m, h, loc=(0, 0.15, 0.13), rot=(0, 0, -25))
    SK.set_shoe_visible(col, 'L', False)
    # slumps, exhausted relief, then lifts his socked foot and looks at it
    m.touched = set()
    m.loc('hips', 0, -0.46, -0.06)
    for s in ('L', 'R'):
        m.loc(f'foot_ik.{s}', 0, 0.42, 0.22); m.arm(s, raise_=-20, forward=5, elbow=15); m.hand(s, curl=0.3)
    m.spine_pose(bend=-6)
    m.key(f0)
    expr_key(m, f0, 'sad', 0.6, eyes=(0, 0.1), head=(0, -8, 0))
    expr_key(m, f0 + 20, 'happy', 0.5, eyes=(0, 0.15), head=(0, -10, 0))
    m.touched = set(); m.loc('foot_ik.L', 0, 0.40, 0.45); m.rot('foot_ik.L', 15, 0, 0); m.spine_pose(bend=14); m.key(f0 + 42)
    m.touched = set(); m.rot('foot_ik.L', -10, 0, 0); m.key(f0 + 50)
    m.touched = set(); m.rot('foot_ik.L', 15, 0, 0); m.key(f0 + 56)
    expr_key(m, f0 + 44, 'confused', 1.0, eyes=(0, -0.3), head=(0, 22, 0))
    expr_key(m, f1 - 12, 'laughing', 0.8, eyes=(0, -0.2), head=(0, 10, 0))
    expr_key(m, f1 - 1, 'laughing', 1.0, eyes=(0, -0.1), head=(0, 0, 0))
    cam, tgt = SK.cam_rig('Cam', lens=35, fstop=2.8)
    cam.parent = h; tgt.parent = h
    SK.key_cam(cam, tgt, f0, Vector((2.8, -2.2, 1.2)), Vector((0, 0, 0.55)), lens=35)
    SK.key_cam(cam, tgt, f1 - 1, Vector((2.0, -1.6, 1.0)), Vector((0, -0.2, 0.5)), lens=38)
    lights_rig(h, key_e=1100, rim_e=1800, key=(1.0, 0.9, 0.82))


def shot_SH12b(f0, f1):
    C, body, ctrl, nuc = _capillary_with_neutrophil(f0, f1, Vector((0, 0.6, -0.1)), Vector((0, 0.2, -0.1)), alpha=0.32)
    m, col = mascot()
    for o in list(col.objects):
        if o.name.startswith('MSC_Shoe_L'):
            continue
        o.hide_render = True
    sneaker = _sneaker_prop(col)
    for o in list(col.objects):
        o.hide_render = True
    sneaker.parent = body
    # shoe mesh lives in mascot space (ankle ~ (0.08,-0.05,0.05)); recentre it on the cell
    sneaker.data.transform(__import__('mathutils').Matrix.Translation((-0.084, 0.05, -0.045)))
    sneaker.location = (0.0, -0.95, 0.05)
    sneaker.scale = (4.6, 4.6 / 1.35, 4.6)
    sneaker.rotation_euler = (0.4, 0.2, 0.0); sneaker.keyframe_insert('rotation_euler', frame=f0)
    sneaker.rotation_euler = (0.9, 1.1, 0.8); sneaker.keyframe_insert('rotation_euler', frame=f1 - 1)
    pulse(body, [f0 + 70], amt=0.06, axis=(1, 1, 1), dur=14)   # a little "gulp"
    cam, tgt = SK.cam_rig('Cam', lens=35, fstop=2.8)
    cam.data.dof.focus_object = sneaker
    SK.key_cam(cam, tgt, f0, Vector((0.45, -3.6, 0.25)), Vector((0.0, -0.4, -0.05)), lens=30)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.32, -2.7, 0.18)), Vector((0.0, -0.5, -0.05)), lens=34)
    RS.area_light('Key', (-0.6, -3.2, 0.8), (0, -0.5, 0), 260, 1.2, (1.0, 0.9, 0.88))
    RS.point_light('Inside', (0.4, -1.9, 0.5), 60, (1.0, 0.85, 0.95), 0.3)

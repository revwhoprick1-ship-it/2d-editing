"""Supporting cast built from the same procedural character system as the mascot.

Each variant overrides colours, eye size, hair style and adds accessories, so
extras share the studio look but never read as copies of the protagonist (the
orange tee + side-swept brown hair are reserved for the mascot).
"""
import importlib
import math

import bmesh
import bpy
from mathutils import Vector, Matrix

from . import mascot_config as C
from . import materials as MAT
from .geo import obj_from_bm, tube_along, add_subsurf, quad_sphere

BASE_COLORS = dict(C.COLORS)
BASE = {k: getattr(C, k) for k in ('HEAD_RADII', 'EYE_RADIUS', 'IRIS_RATIO', 'PUPIL_RATIO')}

VARIANTS = {
    'GRANDMA': dict(prefix='GMA_', scale=1.10,
                    colors={'skin': '#EDC2A4', 'skin_blush': '#E9A08E', 'lip': '#C98A84', 'hair': '#B9B5B0',
                            'hair_tip': '#E4E2DE', 'brow': '#8E8984', 'iris': '#4F5A66', 'iris_light': '#7A8A99',
                            'shirt': '#8B66B5', 'shirt_rib': '#76549E', 'jeans': '#6B5A4C', 'jeans_dark': '#57483C',
                            'shoe': '#4A3428', 'shoe_accent': '#2E2019', 'sole': '#2E2620', 'lace': '#4A3428'},
                    eye=0.0300, hair=dict(lift=0.55, fringe_up=15, bun=True), acc=['glasses']),
    'BUSINESSMAN': dict(prefix='BIZ_', scale=1.22,
                        colors={'skin': '#8A563A', 'skin_blush': '#9A5A44', 'lip': '#7A4434', 'hair': '#1A120E',
                                'hair_tip': '#2A1E16', 'brow': '#160E0A', 'iris': '#2A1A10', 'iris_light': '#4A3020',
                                'shirt': '#2E3442', 'shirt_rib': '#252A36', 'jeans': '#2B313D', 'jeans_dark': '#20252F',
                                'shoe': '#18181C', 'shoe_accent': '#0E0E10', 'sole': '#101012', 'lace': '#18181C'},
                        eye=0.0290, hair=dict(lift=0.38, fringe_up=17), acc=['tie', 'collar']),
    'KID': dict(prefix='KID_', scale=0.95,
                colors={'skin': '#C9895E', 'skin_blush': '#D6785F', 'lip': '#B06A5A', 'hair': '#15111A',
                        'hair_tip': '#2C2433', 'brow': '#15111A', 'iris': '#3E5B3A', 'iris_light': '#6D8A55',
                        'shirt': '#3DBE9E', 'shirt_rib': '#2FA084', 'jeans': '#3C3E55', 'jeans_dark': '#2E3044',
                        'shoe': '#EE5A7A', 'shoe_accent': '#FFFFFF', 'sole': '#F5F2EE', 'lace': '#FFFFFF'},
                eye=0.0330, hair=dict(lift=0.75, long=48), acc=['headphones']),
}


def apply_variant(name):
    v = VARIANTS[name]
    C.COLORS.clear()
    C.COLORS.update(BASE_COLORS)
    C.COLORS.update(v['colors'])
    C.EYE_RADIUS = v['eye']
    C.HAIR = v['hair']
    from . import mascot_build, mascot_rig
    importlib.reload(mascot_build)
    importlib.reload(mascot_rig)
    return v


def reset_mascot_config():
    C.COLORS.clear()
    C.COLORS.update(BASE_COLORS)
    for k, val in BASE.items():
        setattr(C, k, val)
    C.HAIR = {}


# ----------------------------------------------------------------------------- accessories
def _mat(name, color, rough=0.4, metal=0.0, coat=0.0, alpha=1.0):
    m = MAT.simple(name, color, rough, metallic=metal, coat=coat)
    if alpha < 1.0:
        m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    return m


def glasses(col, HC, eye_off, eye_r):
    frame = _mat('ACC_GlassFrame', '#5A3A2A', 0.35, coat=0.6)
    lens = _mat('ACC_Lens', '#DDE8F0', 0.05, alpha=0.18)
    bm = bmesh.new()
    for side in (1, -1):
        c = HC + Vector((eye_off[0] * side, eye_off[1] - eye_r * 1.55, eye_off[2]))
        pts = [c + Vector((math.cos(a) * eye_r * 1.25, 0, math.sin(a) * eye_r * 1.05))
               for a in [2 * math.pi * i / 24 for i in range(25)]]
        tube_along(bm, pts, [(0.0028, 0.0028)] * len(pts), segs=6, cap_start=False, cap_end=False)
        # temple arm back to the ear
        t0 = c + Vector((eye_r * 1.25 * side, 0, 0.004))
        t1 = HC + Vector((0.118 * side, 0.02, -0.002))
        tube_along(bm, [t0, t0.lerp(t1, 0.5) + Vector((0.006 * side, 0, 0.004)), t1], [(0.0022, 0.0022)] * 3, segs=6)
    b0 = HC + Vector((eye_off[0] - eye_r * 1.25, eye_off[1] - eye_r * 1.55, eye_off[2] + 0.004))
    b1 = Vector((-b0.x, b0.y, b0.z))
    tube_along(bm, [b0, (b0 + b1) / 2 + Vector((0, -0.006, 0.006)), b1], [(0.0022, 0.0022)] * 3, segs=6)
    fr = obj_from_bm('ACC_Glasses', bm, [frame], col)
    bm = bmesh.new()
    for side in (1, -1):
        c = HC + Vector((eye_off[0] * side, eye_off[1] - eye_r * 1.55, eye_off[2]))
        ring = [bm.verts.new(c + Vector((math.cos(a) * eye_r * 1.22, 0, math.sin(a) * eye_r * 1.02)))
                for a in [2 * math.pi * i / 24 for i in range(24)]]
        bm.faces.new(ring)
    ln = obj_from_bm('ACC_Lenses', bm, [lens], col)
    return [fr, ln]


def tie_and_collar(col, color='#C0262D', collar=True):
    tm = _mat('ACC_Tie', color, 0.45, coat=0.2)
    bm = bmesh.new()
    # knot + blade on the chest front (shirt front surface ~ y=-0.10 .. -0.115)
    pts = [Vector((0, -0.118, 0.975)), Vector((0, -0.128, 0.93)), Vector((0, -0.132, 0.86)),
           Vector((0, -0.130, 0.78)), Vector((0, -0.124, 0.73))]
    rad = [(0.014, 0.006), (0.012, 0.004), (0.018, 0.004), (0.024, 0.004), (0.002, 0.003)]
    tube_along(bm, pts, rad, segs=8, normals=[Vector((0, -1, 0))] * 5)
    out = [obj_from_bm('ACC_Tie', bm, [tm], col)]
    if collar:
        cm = _mat('ACC_Collar', '#F2F2EE', 0.6)
        bm = bmesh.new()
        for side in (1, -1):
            v = [bm.verts.new(p) for p in (Vector((0.006 * side, -0.118, 0.99)), Vector((0.050 * side, -0.090, 1.0)),
                                            Vector((0.040 * side, -0.108, 0.94)))]
            bm.faces.new(v if side > 0 else list(reversed(v)))
        ob = obj_from_bm('ACC_Collar', bm, [cm], col)
        sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
        sol.thickness = 0.004
        out.append(ob)
    return out


def headphones(col, HC):
    band = _mat('ACC_Headphone', '#F4F4F6', 0.35, coat=0.5)
    cup = _mat('ACC_HeadphoneCup', '#EE5A7A', 0.4, coat=0.4)
    bm = bmesh.new()
    pts = [HC + Vector((math.cos(a) * 0.150, 0.018, math.sin(a) * 0.205 + 0.004))
           for a in [math.radians(d) for d in range(-5, 186, 10)]]
    tube_along(bm, pts, [(0.009, 0.005)] * len(pts), segs=8, normals=[(p - HC).normalized() for p in pts])
    b = obj_from_bm('ACC_HeadBand', bm, [band], col)
    add_subsurf(b, 1, 1)
    bm = bmesh.new()
    for side in (1, -1):
        c = HC + Vector((0.150 * side, 0.018, -0.006))
        tube_along(bm, [c - Vector((0.012 * side, 0, 0)), c + Vector((0.014 * side, 0, 0))],
                   [(0.034, 0.040), (0.030, 0.036)], segs=16, normals=[Vector((0, 0, 1))] * 2)
    cups = obj_from_bm('ACC_HeadCups', bm, [cup], col)
    add_subsurf(cups, 1, 1)
    return [b, cups]


def veil(col, HC):
    m = _mat('ACC_Veil', '#FFFFFF', 0.6, alpha=0.45)
    bm = bmesh.new()
    rows = []
    for i in range(10):
        t = i / 9
        row = []
        for k in range(13):
            a = math.radians(-80 + 160 * k / 12)
            r = 0.135 + 0.10 * t
            row.append(bm.verts.new(HC + Vector((math.sin(a) * r, 0.03 + math.cos(a) * r * 0.9, 0.10 - 0.45 * t))))
        rows.append(row)
    for i in range(9):
        for k in range(12):
            bm.faces.new((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]))
    ob = obj_from_bm('ACC_Veil', bm, [m], col)
    add_subsurf(ob, 1, 1)
    return [ob]


def build_variant(name):
    """Build one rigged extra into collection `name`; returns (rig, collection)."""
    v = apply_variant(name)
    from . import mascot_build as MB, mascot_rig as MR, mascot_config as CC
    parts, M = MB.build_all(name)
    col = bpy.data.collections[name]
    rig = MR.rig_mascot(parts, col)
    HC = Vector(CC.HEAD_CENTER)
    acc_head, acc_chest = [], []
    for a in v['acc']:
        if a == 'glasses':
            acc_head += glasses(col, HC, CC.EYE_OFFSET, CC.EYE_RADIUS)
        elif a == 'headphones':
            acc_head += headphones(col, HC)
        elif a == 'tie':
            acc_chest += tie_and_collar(col, collar='collar' in v['acc'])
        elif a == 'veil':
            acc_head += veil(col, HC)
    for o in acc_head:
        MR.parent_to_bone(o, rig, 'head')
    for o in acc_chest:
        MR.parent_to_bone(o, rig, 'chest')
    pre = v['prefix']
    for o in list(col.objects):
        o.name = pre + (o.name[4:] if o.name.startswith('MSC_') else o.name)
    for m in bpy.data.materials:
        if m.name.startswith('MSC_'):
            m.name = pre + m.name[4:]
    rig['char_scale'] = v['scale']
    rig['char_name'] = name
    reset_mascot_config()
    return rig, col

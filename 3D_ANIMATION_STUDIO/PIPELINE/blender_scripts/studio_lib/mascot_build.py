"""Procedural construction of the permanent mascot.

Not primitives: the head is a sculpted spherified-cube with jaw, cheeks, brow
ridge, nose, lips, a real mouth opening with an inner mouth bag, teeth and a
tongue.  Eyes are separate eyeballs with procedural irises inside sculpted
sockets, covered by rotating lid shells.  Hair is ~50 hand-placed tapered
clumps over a scalp shell.  Arms + hands (5 fingers, nails) are one organic
skin-modifier mesh; the T-shirt is lofted with set-in sleeves, collar rib, hem,
seams and folds; jeans have side-seam topstitching and cuffs; sneakers have a
sole, toe cap, tongue and laces.

All geometry is created in world space with object origins at the world
origin (except eyes / lids which pivot around the eye centre), so the rig can
be built directly on top of it.
"""
import math
import random
import bmesh
import bpy
from mathutils import Vector, Matrix, Quaternion

from . import mascot_config as C
from . import materials as MAT
from .geo import (smoothstep, gauss, lerp, obj_from_bm, quad_sphere, tube_along,
                  add_subsurf, apply_modifiers, skin_mesh, mirror_object_x, set_color_attr)

HC = Vector(C.HEAD_CENTER)
MZ = C.MOUTH_Z
MHW = C.MOUTH_HALF_WIDTH


# =====================================================================================
#  HEAD SHAPE FUNCTION (shared by head, scalp, hair placement and brows)
# =====================================================================================
def head_shape(n):
    """Map a unit direction (head local) to a point on the sculpted skull/face."""
    rx, ry, rz = C.HEAD_RADII
    n = n.normalized()
    p = Vector((n.x * rx, n.y * ry, n.z * rz))
    # --- cranium: fuller back and top
    back = smoothstep(0.0, 0.9, n.y)
    p.y += 0.014 * back * smoothstep(-0.6, 0.3, n.z)
    p.x *= 1.0 + 0.045 * smoothstep(-0.3, 0.8, n.z)
    p.z += 0.006 * smoothstep(0.5, 1.0, n.z)
    # --- lower face: narrow jaw towards a soft chin
    low = smoothstep(-0.12, -0.98, n.z)
    p.x *= 1.0 - 0.20 * low * (0.55 + 0.45 * smoothstep(0.3, -0.8, n.y))
    p.z *= 1.0 - 0.10 * low
    # under-jaw / skull base pulled up so the head sits on the neck
    p.z += 0.030 * low * smoothstep(-0.4, 0.6, n.y)
    p.y -= 0.022 * low * smoothstep(-0.1, 0.8, n.y)
    # flatten the face plane slightly
    front = smoothstep(-0.2, -0.9, n.y)
    p.y *= 1.0 - 0.04 * front * (1 - low)
    return p


def face_features(p, front):
    """Additional sculpt displacement (returns a vector) for facial landmarks."""
    x, y, z = p
    d = Vector((0, 0, 0))
    if front <= 0.0:
        return d
    ax = abs(x)
    ex, ey, ez = C.EYE_OFFSET
    out = Vector((math.copysign(1, x) * 0.35, -1.0, 0.0)).normalized()
    # eye sockets (push in)
    d.y += 0.013 * gauss((ax - ex) ** 2 + (z - ez) ** 2, 0.021)
    # brow ridge
    d.y -= 0.0055 * gauss((ax - ex) ** 2 / 1.8 + (z - 0.046) ** 2 * 3.0, 0.016)
    # cheeks (out and slightly down)
    ck = gauss((ax - 0.060) ** 2 + (z + 0.036) ** 2, 0.024)
    d += out * (0.016 * ck)
    # nose: bridge + tip ball + alae
    bridge = gauss(x * x, 0.0075) * smoothstep(0.022, -0.004, z) * smoothstep(-0.040, -0.016, z)
    tip = gauss(x * x + (z + 0.028) ** 2, 0.0115)
    alae = gauss((ax - 0.0145) ** 2 + (z + 0.033) ** 2, 0.0072)
    d.y -= 0.0065 * bridge + 0.024 * tip + 0.0085 * alae
    # lips
    d.y -= 0.0042 * gauss(x * x / 1.0 + (z - (MZ + 0.0065)) ** 2 * 6.0, 0.016)
    d.y -= 0.0058 * gauss(x * x / 1.3 + (z - (MZ - 0.0095)) ** 2 * 5.0, 0.016)
    # mouth corners tuck in
    d.y += 0.0042 * gauss((ax - (MHW + 0.003)) ** 2 + (z - MZ) ** 2, 0.006)
    # mentolabial fold + chin
    d.y += 0.0028 * gauss(x * x / 2.5 + (z - (MZ - 0.024)) ** 2 * 4, 0.012)
    d.y -= 0.0045 * gauss(x * x / 1.2 + (z + 0.108) ** 2, 0.016)
    # nasolabial softness
    d.y += 0.0018 * gauss((ax - 0.036) ** 2 + (z + 0.045) ** 2 * 0.6, 0.008)
    return d * front


def head_point(n):
    p = head_shape(n)
    front = smoothstep(-0.25, -0.75, n.normalized().y)
    return p + face_features(p, front)


# =====================================================================================
#  HEAD
# =====================================================================================
def build_head(M, col):
    bm = bmesh.new()
    quad_sphere(bm, 29)
    cube_front = {}
    for v in bm.verts:
        cube_front[v.index] = v.co.y < -0.70 and abs(v.co.x) < 0.75 and abs(v.co.z) < 0.75
        v.co = head_point(v.co.copy())
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # ---------- cut the mouth (one grid row, spanning the mouth width)
    cand = []
    for f in bm.faces:
        if not all(cube_front[v.index] for v in f.verts):
            continue
        c = f.calc_center_median()
        zs = [v.co.z for v in f.verts]
        if abs(c.x) < MHW and min(zs) <= MZ <= max(zs):
            cand.append(f)
    bmesh.ops.delete(bm, geom=cand, context='FACES')
    bnd_edges = [e for e in bm.edges if e.is_boundary]
    bnd_verts = list({v for e in bnd_edges for v in e.verts})
    lipside = {}
    xmax = max(abs(v.co.x) for v in bnd_verts)
    for v in bnd_verts:
        upper = v.co.z > MZ
        t = (v.co.x / xmax) ** 2
        corner_lift = 0.0016 * t
        v.co.z = MZ + corner_lift + (0.0007 if upper else -0.0007)
        lipside[v] = 1 if upper else -1
    # lips roll inward
    r1 = bmesh.ops.extrude_edge_only(bm, edges=bnd_edges)
    v1 = [g for g in r1['geom'] if isinstance(g, bmesh.types.BMVert)]
    f1 = [g for g in r1['geom'] if isinstance(g, bmesh.types.BMFace)]
    for v in v1:
        v.co.y += 0.0075
        lipside[v] = 1 if v.co.z > MZ else -1
    e1 = [g for g in r1['geom'] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary]
    # mouth bag walls
    r2 = bmesh.ops.extrude_edge_only(bm, edges=e1)
    v2 = [g for g in r2['geom'] if isinstance(g, bmesh.types.BMVert)]
    f2 = [g for g in r2['geom'] if isinstance(g, bmesh.types.BMFace)]
    for v in v2:
        up = v.co.z > MZ
        lipside[v] = 1 if up else -1
        v.co.y += 0.026
        v.co.x *= 1.05
        v.co.z += 0.011 if up else -0.016
    e2 = [g for g in r2['geom'] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary]
    r3 = bmesh.ops.extrude_edge_only(bm, edges=e2)
    v3 = [g for g in r3['geom'] if isinstance(g, bmesh.types.BMVert)]
    f3 = [g for g in r3['geom'] if isinstance(g, bmesh.types.BMFace)]
    for v in v3:
        up = v.co.z > MZ - 0.003
        lipside[v] = 1 if up else -1
        v.co.y += 0.022
        v.co.x *= 0.72
        v.co.z = lerp(v.co.z, MZ - 0.004, 0.45)
    e3 = [g for g in r3['geom'] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary]
    fill = bmesh.ops.holes_fill(bm, edges=e3, sides=0)
    mouth_faces = set(f2) | set(f3) | set(fill['faces'])
    for f in bm.faces:
        f.material_index = 1 if f in mouth_faces else 0
    lip_inner = set(v1)

    # translate to world
    for v in bm.verts:
        v.co += HC
    bm.verts.index_update()
    side_list = [lipside.get(v, 0) for v in bm.verts]
    inner_list = [1 if v in lip_inner else 0 for v in bm.verts]
    mouth_vert = set()
    for f in mouth_faces:
        for v in f.verts:
            mouth_vert.add(v.index)
    ob = obj_from_bm('MSC_Head', bm, [M['skin'], M['mouth']], col)
    ob['lipside'] = side_list  # kept for rigging (shape keys / jaw weights)
    ob['mouthvert'] = sorted(mouth_vert)
    # vertex colour masks for skin shading
    blush, lipm = [], []
    for i, v in enumerate(ob.data.vertices):
        p = v.co - HC
        ax = abs(p.x)
        fr = smoothstep(-0.05, -0.10, p.y)
        b = 0.75 * gauss((ax - 0.062) ** 2 + (p.z + 0.035) ** 2, 0.018) + 0.35 * gauss(p.x ** 2 + (p.z + 0.031) ** 2, 0.010)
        blush.append(min(1.0, b * fr))
        lm = gauss(p.x ** 2 / 1.0 + (p.z - MZ) ** 2 * 3.2, 0.0185 if ax < MHW else 0.008) * fr
        lm = smoothstep(0.35, 0.75, lm)
        if inner_list[i]:
            lm = 1.0
        lipm.append(lm)
    set_color_attr(ob, 'blush', blush)
    set_color_attr(ob, 'lipmask', lipm)
    add_subsurf(ob, 1, 2)
    return ob


def build_mouth_parts(M, col, head_front_y):
    """Teeth rows and tongue (local to world)."""
    parts = {}
    for name, zc, rows_mat, is_lower in (('MSC_TeethUpper', MZ + 0.0055, M['teeth'], False),
                                         ('MSC_TeethLower', MZ - 0.0085, M['teeth'], True)):
        bm = bmesh.new()
        pts, rad, nrm = [], [], []
        R = 0.034
        for i in range(15):
            a = math.radians(-62 + 124 * i / 14)
            x = math.sin(a) * R * 0.9
            y = head_front_y + 0.0115 + (1 - math.cos(a)) * R * 0.95
            pts.append(HC + Vector((x, y, zc)))
            rad.append((0.0026, 0.0048))
            nrm.append(Vector((math.sin(a), -math.cos(a), 0)))
        tube_along(bm, pts, rad, segs=8, normals=nrm)
        ob = obj_from_bm(name, bm, [rows_mat], col)
        add_subsurf(ob, 1, 2)
        parts[name] = ob
    bm = bmesh.new()
    quad_sphere(bm, 4)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.021, v.co.y * 0.024, v.co.z * 0.0065))
        v.co += HC + Vector((0, head_front_y + 0.03, MZ - 0.0135))
        # front of tongue slightly lower and rounded
    ob = obj_from_bm('MSC_Tongue', bm, [M['tongue']], col)
    add_subsurf(ob, 1, 2)
    parts['MSC_Tongue'] = ob
    return parts


# =====================================================================================
#  EYES, LIDS, LASHES, BROWS
# =====================================================================================
LID_REST = {'up': -44.0, 'lo': 54.0}   # degrees around the eye's X axis (open, relaxed)


def eye_center(side=1):
    ex, ey, ez = C.EYE_OFFSET
    return HC + Vector((ex * side, ey, ez))


def build_eyes(M, col):
    out = {}
    R = C.EYE_RADIUS
    for side, tag in ((1, 'L'), (-1, 'R')):
        c = eye_center(side)
        # eyeball: UV sphere whose poles are on the Y axis (iris at -Y)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
        rot = Matrix.Rotation(math.radians(90), 4, 'X')
        bmesh.ops.transform(bm, matrix=rot, verts=bm.verts[:])
        # gentle corneal bulge
        for v in bm.verts:
            if v.co.y < -0.6:
                k = smoothstep(-0.6, -1.0, v.co.y)
                v.co.y -= 0.07 * k
        ob = obj_from_bm(f'MSC_Eye_{tag}', bm, [M['eye']], col)
        ob.location = c
        ob.scale = (R, R, R)
        add_subsurf(ob, 1, 1)
        out[f'eye_{tag}'] = ob
        # lids: hemispherical shells (upper covers +Z half, lower covers -Z half)
        for lid, sgn in (('up', 1), ('lo', -1)):
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
            kill = [v for v in bm.verts if v.co.z * sgn < -0.02]
            bmesh.ops.delete(bm, geom=kill, context='VERTS')
            for v in bm.verts:
                v.co *= 1.085
            ob = obj_from_bm(f'MSC_Lid_{lid}_{tag}', bm, [M['skin'], M['lash']], col)
            ob.location = c
            ob.scale = (R, R, R)
            sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
            sol.thickness = 0.06
            sol.offset = 1.0
            sol.material_offset_rim = 1 if lid == 'up' else 0
            sol.use_rim = True
            add_subsurf(ob, 1, 2)
            ob.rotation_euler.x = math.radians(LID_REST[lid])
            out[f'lid_{lid}_{tag}'] = ob
        # upper lash: a thin tapered strip along the front arc of the upper lid rim
        bm = bmesh.new()
        pts, rad, nrm = [], [], []
        for i in range(13):
            a = math.radians(-75 + 150 * i / 12)  # around the rim in the lid's XY plane
            p = Vector((math.sin(a), -math.cos(a), 0.0)) * 1.12
            w = math.sin(math.pi * (i / 12)) ** 0.5
            # outer corner (side=+1 is the character's left -> +x) gets a flick
            flick = smoothstep(0.55, 1.0, (i / 12) if side > 0 else (1 - i / 12))
            p += Vector((0, -0.05, 0.10 * flick + 0.02))
            pts.append(p)
            rad.append((0.035 * w + 0.01, 0.10 * w + 0.03))
            nrm.append(Vector((math.sin(a) * 0.3, -math.cos(a) * 0.3, 1.0)))
        tube_along(bm, pts, rad, segs=6, normals=nrm)
        ob = obj_from_bm(f'MSC_Lash_{tag}', bm, [M['lash']], col)
        ob.location = c
        ob.scale = (R, R, R)
        ob.rotation_euler.x = math.radians(LID_REST['up'])
        out[f'lash_{tag}'] = ob
    return out


def build_brows(M, col):
    out = {}
    for side, tag in ((1, 'L'), (-1, 'R')):
        pts, rad, nrm = [], [], []
        N = 12
        for i in range(N):
            t = i / (N - 1)
            x = lerp(0.016, 0.082, t)
            z = 0.050 + 0.0075 * math.sin(math.pi * t ** 0.85) - 0.006 * t
            # find surface y by sampling head_point along direction
            n = Vector((x / C.HEAD_RADII[0], -0.9, z / C.HEAD_RADII[2]))
            sp = head_point(n)
            # project to exact x/z by small iterative correction
            for _ in range(6):
                n.x += (x - sp.x) / C.HEAD_RADII[0]
                n.z += (z - sp.z) / C.HEAD_RADII[2]
                sp = head_point(n)
            nn = (head_point(n * 1.0) - Vector((0, 0, 0))).normalized()
            p = sp + nn * 0.0035
            pts.append(HC + Vector((p.x * side, p.y, p.z)))
            w = lerp(0.0062, 0.0024, t ** 1.2)
            h = lerp(0.0026, 0.0013, t)
            rad.append((w, h))
            nrm.append(Vector((nn.x * side, nn.y, nn.z)))
        bm = bmesh.new()
        tube_along(bm, pts, rad, segs=8, normals=nrm)
        ob = obj_from_bm(f'MSC_Brow_{tag}', bm, [M['brow']], col)
        add_subsurf(ob, 1, 2)
        out[f'brow_{tag}'] = ob
    return out


# =====================================================================================
#  EARS
# =====================================================================================
def build_ears(M, col):
    bm = bmesh.new()
    quad_sphere(bm, 9)
    for v in bm.verts:
        n = v.co.normalized()
        y, z = n.y, n.z
        # outline: C-shaped ear, wider at top
        wy = 0.025 * (1.0 + 0.12 * smoothstep(-0.2, 0.8, z))
        hz = 0.037
        x = n.x * 0.010
        r = math.sqrt(y * y + z * z)
        if n.x > 0:  # outer face
            concha = gauss((y + 0.10) ** 2 + (z + 0.12) ** 2, 0.33)
            scapha = gauss((r - 0.80) ** 2, 0.07) * smoothstep(-0.5, 0.2, z)
            antihelix = gauss((r - 0.58) ** 2, 0.08) * smoothstep(-0.7, 0.1, z)
            lobe = smoothstep(-0.45, -0.85, z)
            x -= 0.0105 * concha * (1 - lobe)
            x -= 0.0035 * scapha * (1 - lobe)
            x += 0.0028 * antihelix * (1 - lobe)
            x += 0.002 * lobe
        else:
            x *= 0.6
        v.co = Vector((x, y * wy, z * hz))
    ob = obj_from_bm('MSC_Ear_L', bm, [M['skin']], col)
    ob.rotation_euler = (math.radians(-8), math.radians(0), math.radians(-22))
    ob.location = HC + Vector(C.EAR_OFFSET) + Vector((0.006, 0, 0))
    _apply_transform(ob)
    add_subsurf(ob, 1, 2)
    obr = mirror_object_x(ob, 'MSC_Ear_R')
    add_subsurf(obr, 1, 2)
    return {'ear_L': ob, 'ear_R': obr}


def _apply_transform(ob):
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.data.transform(mw)
    ob.matrix_world = Matrix.Identity(4)


# =====================================================================================
#  HAIR
# =====================================================================================
def _dir(az_deg, el_deg):
    az, el = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))


def _slerp(a, b, t):
    a, b = a.normalized(), b.normalized()
    d = max(-1.0, min(1.0, a.dot(b)))
    th = math.acos(d)
    if th < 1e-5:
        return a
    return (a * math.sin((1 - t) * th) + b * math.sin(t * th)) / math.sin(th)


def hairline_el(az_deg):
    a = abs(az_deg)
    keys = [(0, 30), (40, 28), (70, 16), (95, 6), (120, -14), (150, -32), (180, -40)]
    for (a0, e0), (a1, e1) in zip(keys, keys[1:]):
        if a0 <= a <= a1:
            return lerp(e0, e1, (a - a0) / (a1 - a0))
    return -40


def hair_clump(bm, uv, d0, d1, lift, width, thick, base_off=0.004, curl=None, segs=8, N=14,
               droop=0.0, tip_out=0.0):
    pts, rad, nrm = [], [], []
    for i in range(N):
        t = i / (N - 1)
        d = _slerp(d0, d1, t)
        sp = head_shape(d)
        out = sp.normalized()
        hump = math.sin(math.pi * min(1.0, t * 1.05)) ** 0.8
        p = sp + out * (base_off + lift * hump + tip_out * smoothstep(0.6, 1.0, t))
        p.z -= droop * smoothstep(0.5, 1.0, t)
        if curl is not None:
            p += curl * smoothstep(0.65, 1.0, t)
        pts.append(HC + p)
        w = width * (1.0 - smoothstep(0.50, 1.0, t) ** 1.3) * (0.80 + 0.20 * math.sin(math.pi * min(1, t * 1.6)))
        h = thick * (1.0 - t) ** 0.7 + 0.0006
        rad.append((max(w, 0.0008), h))
        nrm.append(out)
    tube_along(bm, pts, rad, segs=segs, normals=nrm, cap_start=True, cap_end=False, tip_point=True,
               uv_layer=uv)


def build_hair(M, col, seed=7):
    rnd = random.Random(seed)
    # --- scalp shell
    bm = bmesh.new()
    quad_sphere(bm, 22)
    kill = []
    for v in bm.verts:
        n = v.co.normalized()
        az = math.degrees(math.atan2(n.x, -n.y))
        el = math.degrees(math.asin(max(-1, min(1, n.z))))
        if el < hairline_el(az) - 1.5:
            kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    for v in bm.verts:
        p = head_shape(v.co.normalized())
        v.co = HC + p + p.normalized() * 0.0025
    scalp = obj_from_bm('MSC_Scalp', bm, [M['hair']], col)
    sol = scalp.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = 0.004
    sol.offset = 1.0
    add_subsurf(scalp, 1, 2)

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    clump_ranges = []

    def clump(*a, **k):
        start = len(bm.verts)
        hair_clump(bm, uv, *a, **k)
        clump_ranges.append((start, len(bm.verts)))

    # back + sides: from crown flowing down past the hairline
    for row, el0 in enumerate((74, 56, 38)):
        step = 15 if row < 2 else 20
        for az in range(-180, 181, step):
            if abs(az) < 62 + row * 6:
                continue
            j = rnd.uniform(-4, 4)
            d0 = _dir(az * 0.9 + j, el0 + rnd.uniform(-3, 3))
            end_el = hairline_el(az) - 4 + rnd.uniform(-2, 2)
            if el0 - end_el < 12:
                continue
            d1 = _dir(az + rnd.uniform(-5, 5), end_el)
            clump(d0, d1, lift=0.018 + 0.006 * rnd.random() - 0.004 * row, width=0.050 - 0.006 * row,
                  thick=0.012, base_off=0.004 + 0.002 * row, tip_out=0.004 + 0.004 * rnd.random())
    # top volume sweeping forward into a side-swept fringe (towards the character's right, -x)
    for i in range(14):
        u = i / 13.0
        d0 = _dir(180 + lerp(-50, 50, u) + rnd.uniform(-5, 5), 76 + rnd.uniform(-3, 3))
        az1 = lerp(-62, 48, u) - 14 + rnd.uniform(-4, 4)
        el1 = 19 + 7 * (abs(az1) / 60.0) + rnd.uniform(-2, 2)
        d1 = _dir(az1, el1)
        curl = Vector((-0.010 - 0.006 * rnd.random(), -0.010, 0.006 + 0.006 * rnd.random()))
        clump(d0, d1, lift=0.042 + 0.014 * math.sin(math.pi * u) + rnd.uniform(-0.004, 0.004),
              width=0.064, thick=0.017, base_off=0.007, curl=curl, tip_out=0.006)
    # temples: cover the side hairline in front of the ears
    for side in (1, -1):
        for i in range(3):
            az = side * (52 + i * 14)
            d0 = _dir(az * 0.7, 66)
            d1 = _dir(az + side * 4, hairline_el(az) - 5)
            clump(d0, d1, lift=0.022, width=0.046, thick=0.012, base_off=0.006, tip_out=0.004)
    # fringe overlay strands over the forehead
    for i in range(7):
        u = i / 6.0
        d0 = _dir(lerp(-30, 42, u), 58)
        d1 = _dir(lerp(-46, 22, u) + rnd.uniform(-4, 4), 15 + rnd.uniform(-2, 3) + 6 * abs(u - 0.4))
        curl = Vector((-0.008, -0.012, 0.004 + 0.006 * rnd.random()))
        clump(d0, d1, lift=0.026, width=0.044, thick=0.012, base_off=0.010, curl=curl, tip_out=0.006)
    ob = obj_from_bm('MSC_Hair', bm, [M['hair']], col)
    var = [0.0] * len(ob.data.vertices)
    for (a, b) in clump_ranges:
        r = rnd.uniform(0.0, 0.45)
        for i in range(a, b):
            var[i] = r
    set_color_attr(ob, 'clump_var', var)
    add_subsurf(ob, 1, 1)
    return {'hair': ob, 'scalp': scalp}


# =====================================================================================
#  NECK, ARMS + HANDS
# =====================================================================================
def build_neck(M, col):
    bm = bmesh.new()
    a, b = Vector(C.NECK_BASE) + Vector((0, 0, -0.04)), Vector(C.NECK_TOP) + Vector((0, 0, 0.03))
    pts = [a.lerp(b, t) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    rad = [(0.066, 0.061), (0.062, 0.058), (0.060, 0.057), (0.061, 0.058), (0.066, 0.061)]
    tube_along(bm, pts, rad, segs=16, normals=[Vector((0, -1, 0))] * 5)
    ob = obj_from_bm('MSC_Neck', bm, [M['skin']], col)
    add_subsurf(ob, 1, 2)
    return ob


def hand_frame():
    sh, el, wr = Vector(C.SHOULDER), Vector(C.ELBOW), Vector(C.WRIST)
    f = (wr - el).normalized()
    t = Vector((0, -1, 0))
    t = (t - f * t.dot(f)).normalized()
    pn = f.cross(t).normalized()   # palm normal (towards body) for the left hand
    return f, t, pn


FINGERS = {  # knuckle offset along forearm f, thumb-side t ; segment lengths ; radius
    'index':  (0.080, 0.0205, (0.030, 0.021, 0.018), 0.0084),
    'middle': (0.083, 0.0068, (0.033, 0.023, 0.019), 0.0086),
    'ring':   (0.081, -0.0072, (0.031, 0.021, 0.018), 0.0081),
    'pinky':  (0.075, -0.0205, (0.024, 0.017, 0.016), 0.0072),
}
FINGER_CURL = (10, 14, 10)  # degrees per segment in rest pose (relaxed hand)


def finger_chain(name):
    """Return list of joint positions for a finger (left hand, world space)."""
    f, t, pn = hand_frame()
    wr = Vector(C.WRIST)
    if name == 'thumb':
        base = wr + f * 0.024 + t * 0.016 + pn * 0.008
        d = (f * 0.80 + t * 0.48 + pn * 0.36).normalized()
        lens = (0.032, 0.024, 0.021)
        pts = [base]
        ax = (t.cross(d)).normalized()
        for i, L in enumerate(lens):
            pts.append(pts[-1] + d * L)
            d = Quaternion(ax, math.radians(-12)) @ d
            d = Quaternion(f, math.radians(6)) @ d
        return pts
    u, s, lens, r = FINGERS[name]
    k = wr + f * u + t * s
    d = (f + t * (s * 1.4)).normalized()
    pts = [k]
    ax = d.cross(pn).normalized()  # bending axis
    for i, L in enumerate(lens):
        d = Quaternion(ax, math.radians(-FINGER_CURL[i])) @ d
        pts.append(pts[-1] + d * L)
    return pts


def build_arm(M, col):
    sh, el, wr = Vector(C.SHOULDER), Vector(C.ELBOW), Vector(C.WRIST)
    f, t, pn = hand_frame()
    verts, edges, radii = [], [], []

    def add(p, r):
        verts.append(tuple(p))
        radii.append((r, r))
        return len(verts) - 1

    a0 = add(sh + Vector((-0.03, 0, -0.025)), 0.034)
    a1 = add(sh.lerp(el, 0.45), 0.044)
    a2 = add(el, 0.037)
    a3 = add(el.lerp(wr, 0.35), 0.038)
    a4 = add(el.lerp(wr, 0.75), 0.032)
    a5 = add(wr, 0.027)
    p0 = add(wr + f * 0.032, 0.030)
    p1 = add(wr + f * 0.062, 0.031)
    for a, b in ((a0, a1), (a1, a2), (a2, a3), (a3, a4), (a4, a5), (a5, p0), (p0, p1)):
        edges.append((a, b))
    for name in ('index', 'middle', 'ring', 'pinky'):
        pts = finger_chain(name)
        r = FINGERS[name][3]
        prev = p1
        for i, p in enumerate(pts):
            rr = r * (1.0 - 0.07 * i)
            vi = add(p, rr if i < 3 else rr * 0.92)
            edges.append((prev, vi))
            prev = vi
    tpts = finger_chain('thumb')
    prev = p0
    for i, p in enumerate(tpts):
        vi = add(p, 0.0115 * (1 - 0.09 * i))
        edges.append((prev, vi))
        prev = vi
    ob = skin_mesh('MSC_Arm_L', verts, edges, radii, root=0, collection=col)
    # flatten the palm and wrist along the palm normal; shape forearm
    me = ob.data
    palm_c = wr + f * 0.05
    for v in me.vertices:
        p = v.co.copy()
        rel = p - wr
        along = rel.dot(f)
        if -0.01 < along < 0.09:
            # distance from the hand's central axis
            k = smoothstep(-0.01, 0.02, along) * (1 - smoothstep(0.075, 0.095, along))
            off = rel.dot(pn)
            v.co = p - pn * off * 0.42 * k
        if -0.25 < along < -0.005:
            # forearm slightly flatter (radius/ulna)
            off = rel.dot(pn)
            v.co = v.co - pn * off * 0.12
    me.materials.append(M['skin'])
    for poly in me.polygons:
        poly.use_smooth = True
    add_subsurf(ob, 1, 2)
    # fingernails
    bm = bmesh.new()
    for name in ('index', 'middle', 'ring', 'pinky', 'thumb'):
        pts = finger_chain(name)
        d = (pts[-1] - pts[-2]).normalized()
        if name == 'thumb':
            back = (d.cross(t) * -1).normalized()
            back = (-pn).normalized()
        else:
            back = (-pn - d * (-pn).dot(d)).normalized()
        r = (FINGERS[name][3] if name != 'thumb' else 0.0105) * 0.86
        c = pts[-1] - d * 0.0065 + back * r * 0.80
        nb = bmesh.new()
        quad_sphere(nb, 2)
        side = d.cross(back).normalized()
        mtx = Matrix((side * r * 0.68, d * 0.0072, back * 0.0016)).transposed()
        for v in nb.verts:
            v.co = c + mtx @ v.co
        tmp = bpy.data.meshes.new('tmpnail')
        nb.to_mesh(tmp)
        nb.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    nails = obj_from_bm('MSC_Nails_L', bm, [M['nail']], col)
    add_subsurf(nails, 1, 1)
    obr = mirror_object_x(ob, 'MSC_Arm_R')
    add_subsurf(obr, 1, 2)
    nr = mirror_object_x(nails, 'MSC_Nails_R')
    add_subsurf(nr, 1, 1)
    return {'arm_L': ob, 'arm_R': obr, 'nails_L': nails, 'nails_R': nr}


# =====================================================================================
#  T-SHIRT
# =====================================================================================
TORSO_PROFILE = [  # z, half width, half depth, front bulge
    (0.522, 0.148, 0.106, 0.004),
    (0.560, 0.145, 0.104, 0.004),
    (0.620, 0.140, 0.101, 0.004),
    (0.680, 0.139, 0.101, 0.005),
    (0.750, 0.147, 0.105, 0.008),
    (0.820, 0.157, 0.109, 0.012),
    (0.875, 0.158, 0.108, 0.012),
    (0.915, 0.150, 0.102, 0.008),
    (0.945, 0.143, 0.094, 0.004),
    (0.962, 0.128, 0.085, 0.0),
    (0.977, 0.108, 0.072, 0.0),
    (0.988, 0.080, 0.062, 0.0),
]


def _ring(z, a, b, bulge, N=48, neck_dip=0.0, ex=2.3):
    pts = []
    for s in range(N):
        th = 2 * math.pi * s / N
        c, sn = math.cos(th), math.sin(th)
        x = math.copysign(abs(c) ** (2 / ex), c) * a
        y = math.copysign(abs(sn) ** (2 / ex), sn) * b
        if y < 0:
            y -= bulge * (abs(sn) ** 2)
        front = max(0.0, -sn)
        pts.append(Vector((x, y, z - neck_dip * front ** 2)))
    return pts


def build_shirt(M, col):
    N = 48
    bm = bmesh.new()
    rings = []
    # hem fold (inside) -> outside up to the neck -> collar rib rolled inside
    prof = [(0.540, 0.141, 0.100, 0.004, 0)] + [(z, a, b, bl, 0) for (z, a, b, bl) in TORSO_PROFILE]
    prof += [(0.996, 0.072, 0.059, 0.0, 0.020), (0.999, 0.066, 0.055, 0.0, 0.022),
             (0.990, 0.061, 0.051, 0.0, 0.022)]
    for i, (z, a, b, bl, dip) in enumerate(prof):
        dip_z = dip
        if i >= len(prof) - 4 and dip == 0:
            dip_z = 0.010
        pts = _ring(z, a, b, bl, N, neck_dip=dip_z)
        rings.append([bm.verts.new(p + Vector((0, 0.008, 0))) for p in pts])
    for i in range(len(rings) - 1):
        for s in range(N):
            bm.faces.new((rings[i][s], rings[i][(s + 1) % N], rings[i + 1][(s + 1) % N], rings[i + 1][s]))
    # sleeves: loft from the armhole (vertical plane) to the arm axis
    sh, el = Vector(C.SHOULDER), Vector(C.ELBOW)
    ad = (el - sh).normalized()
    sleeve_rings_all = []
    for side in (1,):
        root_c = Vector((0.140, 0.010, 0.872))
        end_c = sh + ad * 0.125
        S = 24
        srings = []
        steps = 7
        for k in range(steps):
            u = k / (steps - 1)
            c = root_c.lerp(end_c, smoothstep(0, 1, u) * 0.85 + u * 0.15)
            ax = Vector((1, 0, 0)).lerp(ad, 0.45 + 0.55 * smoothstep(0.0, 0.6, u)).normalized()
            up = Vector((0, 0, 1))
            up = (up - ax * up.dot(ax)).normalized()
            bi = ax.cross(up).normalized()
            ry = lerp(0.062, 0.056, u)
            rz = lerp(0.078, 0.057, smoothstep(0, 0.6, u))
            ring = []
            for s in range(S):
                th = 2 * math.pi * s / S
                p = c + up * (math.cos(th) * rz) + bi * (math.sin(th) * ry)
                ring.append(bm.verts.new(p))
            srings.append(ring)
        # hem fold inside
        last = srings[-1]
        fold = []
        cend = end_c - ad * 0.012
        for s, v in enumerate(last):
            p = cend + (v.co - end_c) * 0.93
            fold.append(bm.verts.new(p))
        srings.append(fold)
        for i in range(len(srings) - 1):
            for s in range(S):
                bm.faces.new((srings[i][s], srings[i][(s + 1) % S], srings[i + 1][(s + 1) % S], srings[i + 1][s]))
        sleeve_rings_all.append(srings)
    # mirror sleeve for right side
    mirror_geom = []
    srings = sleeve_rings_all[0]
    mr = [[bm.verts.new(Vector((-v.co.x, v.co.y, v.co.z))) for v in ring] for ring in srings]
    S = len(mr[0])
    for i in range(len(mr) - 1):
        for s in range(S):
            bm.faces.new((mr[i][s], mr[i + 1][s], mr[i + 1][(s + 1) % S], mr[i][(s + 1) % S]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = obj_from_bm('MSC_Shirt', bm, [M['shirt']], col)
    # folds + seams
    me = ob.data
    seam = []
    rnd = random.Random(3)
    for v in me.vertices:
        p = v.co
        ax_ = abs(p.x)
        # waist bunching folds (horizontal, broken up)
        wz = gauss((p.z - 0.62) ** 2, 0.05)
        fold = math.sin(p.z * 210 + math.sin(p.x * 40) * 2.0) * 0.0018 * wz
        # diagonal pull folds from armpit towards chest
        dz = gauss((ax_ - 0.12) ** 2 + (p.z - 0.86) ** 2, 0.035)
        fold += math.sin((p.z + ax_ * 0.9) * 260) * 0.0012 * dz
        nrm = Vector((p.x, p.y - 0.008, 0)).normalized() if p.z < 0.99 else Vector((0, 0, 0))
        v.co = p + nrm * fold
        # seams: side seams, shoulder seam, sleeve hem and collar rib band
        s = 0.0
        if p.z < 0.95 and ax_ < 0.17:
            ang = math.atan2(p.y - 0.008, p.x)
            s = max(s, gauss((abs(ang) - math.pi / 2 + 0.0) ** 2 * 0, 1) * 0)
            side = gauss((abs(abs(ang) - 0.0) if p.x > 0 else abs(abs(ang) - math.pi)) ** 2, 0.03)
            s = max(s, side * smoothstep(0.88, 0.85, p.z))
        if p.z > 0.975:
            s = max(s, smoothstep(0.978, 0.985, p.z))
        if p.z < 0.548:
            s = max(s, smoothstep(0.548, 0.540, p.z) * 0.6)
        seam.append(min(1.0, s))
    set_color_attr(ob, 'seam', seam)
    sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = 0.004
    sol.offset = -1.0
    add_subsurf(ob, 1, 2)
    return ob


# =====================================================================================
#  JEANS
# =====================================================================================
def build_jeans(M, col):
    hip, knee, ank = Vector(C.HIP), Vector(C.KNEE), Vector(C.ANKLE)
    verts, edges, radii = [], [], []

    def add(p, r):
        verts.append(tuple(p))
        radii.append((r, r))
        return len(verts) - 1

    w0 = add((0, 0.004, 0.70), 0.132)
    w1 = add((0, 0.004, 0.60), 0.136)
    prev_side = {}
    for side in (1, -1):
        h = Vector((hip.x * side, hip.y, hip.z - 0.03))
        k = Vector((knee.x * side, knee.y, knee.z))
        a = Vector((ank.x * side, ank.y, ank.z))
        i0 = add(h, 0.080)
        i1 = add(h.lerp(k, 0.5), 0.066)
        i2 = add(k, 0.059)
        i3 = add(k.lerp(a, 0.5), 0.057)
        i4 = add(a + Vector((0, 0, 0.0)), 0.058)
        edges += [(w1, i0), (i0, i1), (i1, i2), (i2, i3), (i3, i4)]
    edges.append((w0, w1))
    ob = skin_mesh('MSC_Jeans', verts, edges, radii, root=0, collection=col)
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    # open the cuffs, drop the hidden top cap
    kill = [f for f in bm.faces if f.calc_center_median().z < ank.z + 0.004]
    kill += [f for f in bm.faces if f.calc_center_median().z > 0.69]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    # pelvis depth + seat
    for v in bm.verts:
        p = v.co
        if p.z > 0.45:
            k = smoothstep(0.45, 0.58, p.z)
            p.y = lerp(p.y, p.y * 0.80, k)
            p.y += 0.010 * k * gauss(p.x ** 2 + (p.z - 0.56) ** 2, 0.06) * (1 if p.y > 0 else 0)
    # rolled cuffs
    bnd = [e for e in bm.edges if e.is_boundary and e.verts[0].co.z < 0.2]
    r = bmesh.ops.extrude_edge_only(bm, edges=bnd)
    for g in r['geom']:
        if isinstance(g, bmesh.types.BMVert):
            g.co.z += 0.03
            c = Vector((math.copysign(ank.x, g.co.x), ank.y, g.co.z))
            g.co = c + (g.co - c) * 0.95
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M['denim'])
    for p in me.polygons:
        p.use_smooth = True
    # outer/inner seams + cuff hem topstitch + knee wrinkles
    seam = []
    for v in me.vertices:
        p = v.co
        s = 0.0
        if p.z < 0.52:
            lx = math.copysign(ank.x, p.x) if p.x != 0 else ank.x
            rel = Vector((p.x - lx, p.y - 0.0))
            ang = math.atan2(rel.y, rel.x)
            outer = gauss((ang if p.x > 0 else (abs(ang) - math.pi)) ** 2, 0.06)
            s = max(s, outer)
        if p.z < ank.z + 0.04:
            s = max(s, gauss((p.z - (ank.z + 0.022)) ** 2, 0.002))
        seam.append(min(1.0, s))
        # knee/ankle stacking wrinkles
        if p.z < 0.45:
            wr = math.sin(p.z * 160 + p.x * 30) * 0.0016 * (gauss((p.z - 0.32) ** 2, 0.03) + gauss((p.z - 0.13) ** 2, 0.03))
            lx = math.copysign(ank.x, p.x)
            n = Vector((p.x - lx, p.y, 0)).normalized()
            v.co = p + n * wr
    set_color_attr(ob, 'seam', seam)
    sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = 0.004
    sol.offset = -1.0
    add_subsurf(ob, 1, 2)
    return ob


# =====================================================================================
#  SNEAKERS
# =====================================================================================
def build_shoe(M, col):
    ank = Vector(C.ANKLE)
    bm = bmesh.new()
    quad_sphere(bm, 7)
    L0, L1 = 0.062, -0.165   # heel, toe (y)
    mats = []
    for v in bm.verts:
        n = v.co.normalized()
        u = (n.y + 1) / 2   # 0 toe .. 1 heel
        y = lerp(L1, L0, u)
        width = 0.047 * (0.82 + 0.18 * math.sin(math.pi * min(1, (1 - u) * 1.25))) * (0.88 + 0.12 * (1 - u))
        top = 0.040 + 0.050 * smoothstep(0.45, 0.82, u)
        z = (n.z * 0.5 + 0.5) * top
        x = n.x * width
        # flatten bottom
        if n.z < -0.4:
            z = 0.0 + 0.004 * (n.z + 1)
        # toe spring
        z += 0.008 * smoothstep(0.25, 0.0, u) * (1 if n.z < 0 else 0.5)
        v.co = Vector((ank.x + x, y + ank.y - 0.012, z))
    for f in bm.faces:
        c = f.calc_center_median()
        u = (c.y - L1) / (L0 - L1)
        if c.z < 0.019:
            f.material_index = 1  # sole
        elif u > 0.86 and c.z < 0.07:
            f.material_index = 2  # heel counter accent
        elif u < 0.10 and c.z < 0.032:
            f.material_index = 2  # toe bumper accent
        else:
            f.material_index = 0
    shoe = obj_from_bm('MSC_Shoe_L', bm, [M['shoe'], M['sole'], M['shoe_accent']], col)
    add_subsurf(shoe, 2, 2)
    # laces + tongue
    bm = bmesh.new()
    for i in range(4):
        y = -0.075 + i * 0.022
        z = 0.050 + 0.035 * smoothstep(-0.08, 0.0, y) + 0.004
        pts = [Vector((ank.x - 0.022, y + 0.004, z - 0.006)), Vector((ank.x, y, z + 0.003)),
               Vector((ank.x + 0.022, y + 0.004, z - 0.006))]
        tube_along(bm, pts, [(0.003, 0.0016)] * 3, segs=6)
    lace = obj_from_bm('MSC_Laces_L', bm, [M['lace']], col)
    # sock foot (shown only if the sneaker is lost)
    sock_mat = MAT.fabric('MSC_Sock', '#E8E4DC', '#D8D2C8', scale=1800.0, bump=0.08, sheen=0.6)
    sme = shoe.data.copy()
    sme.name = 'MSC_Sock_L'
    sbm = bmesh.new()
    sbm.from_mesh(sme)
    for v in sbm.verts:
        v.co.x = ank.x + (v.co.x - ank.x) * 0.80
        v.co.y = ank.y - 0.04 + (v.co.y - (ank.y - 0.04)) * 0.86
        v.co.z = v.co.z * 0.78 + 0.004
    sbm.to_mesh(sme)
    sbm.free()
    sme.materials.clear()
    sme.materials.append(sock_mat)
    for poly in sme.polygons:
        poly.material_index = 0
    sock = bpy.data.objects.new('MSC_Sock_L', sme)
    col.objects.link(sock)
    add_subsurf(sock, 2, 2)
    sock.hide_render = True
    sock.hide_viewport = True
    shoes = {'shoe_L': shoe, 'laces_L': lace, 'sock_L': sock}
    shoes['shoe_R'] = mirror_object_x(shoe, 'MSC_Shoe_R')
    add_subsurf(shoes['shoe_R'], 2, 2)
    shoes['laces_R'] = mirror_object_x(lace, 'MSC_Laces_R')
    shoes['sock_R'] = mirror_object_x(sock, 'MSC_Sock_R')
    add_subsurf(shoes['sock_R'], 2, 2)
    shoes['sock_R'].hide_render = True
    shoes['sock_R'].hide_viewport = True
    return shoes


# =====================================================================================
#  ASSEMBLY
# =====================================================================================
def build_all(collection_name='MASCOT'):
    col = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    M = MAT.character_set(C.COLORS, C.IRIS_RATIO, C.PUPIL_RATIO)
    parts = {}
    head = build_head(M, col)
    parts['head'] = head
    front_y = min(v.co.y for v in head.data.vertices if abs(v.co.x) < 0.01 and abs(v.co.z - (HC.z + MZ)) < 0.004) - HC.y
    parts.update(build_mouth_parts(M, col, front_y))
    parts.update(build_eyes(M, col))
    parts.update(build_brows(M, col))
    parts.update(build_ears(M, col))
    parts.update(build_hair(M, col))
    parts['neck'] = build_neck(M, col)
    parts.update(build_arm(M, col))
    parts['shirt'] = build_shirt(M, col)
    parts['jeans'] = build_jeans(M, col)
    parts.update(build_shoe(M, col))
    return parts, M

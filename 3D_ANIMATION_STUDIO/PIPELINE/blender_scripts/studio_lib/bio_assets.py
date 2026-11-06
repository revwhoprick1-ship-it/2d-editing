"""Procedural biology asset library (micro-world scale).

Scale convention for "inside the body" videos: the shrunk mascot (1.5 BU tall)
stands ~5 micrometres tall, so 1 micrometre = 0.3 BU.
  red blood cell 7.8 um  -> 2.34 BU diameter (Evans & Fung 1972 biconcave profile)
  capillary 5-10 um      -> 1.5-3 BU
  neutrophil 10-12 um    -> 3.0-3.6 BU
Big vessels are shown as enormous fog-filled tunnels (they would be mm-scale).
"""
import math
import random
import bmesh
import bpy
from mathutils import Vector, Matrix, Euler, noise

from .geo import smoothstep, gauss, lerp, obj_from_bm, quad_sphere, tube_along, add_subsurf
from .materials import hex_rgb, _node, _link, _ramp, _bump

UM = 0.3  # blender units per micrometre


# ==================================================================================== fog
def add_fog(mat, color, near, far, power=1.3, max_mix=1.0):
    """Blend a material towards a flat fog colour with camera distance."""
    nt = mat.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs['Surface'].links[0].from_socket
    cam = _node(nt, 'ShaderNodeCameraData', (out.location.x - 600, out.location.y - 300))
    mr = _node(nt, 'ShaderNodeMapRange', (out.location.x - 400, out.location.y - 300))
    mr.inputs['From Min'].default_value = near
    mr.inputs['From Max'].default_value = far
    mr.inputs['To Max'].default_value = max_mix
    _link(nt, cam.outputs['View Distance'], mr.inputs['Value'])
    pw = _node(nt, 'ShaderNodeMath', (out.location.x - 250, out.location.y - 300), operation='POWER')
    pw.inputs[1].default_value = power
    _link(nt, mr.outputs['Result'], pw.inputs[0])
    em = _node(nt, 'ShaderNodeEmission', (out.location.x - 250, out.location.y - 150))
    em.inputs['Color'].default_value = (*color[:3], 1)
    em.inputs['Strength'].default_value = 1.0
    mix = _node(nt, 'ShaderNodeMixShader', (out.location.x - 100, out.location.y))
    _link(nt, pw.outputs[0], mix.inputs['Fac'])
    _link(nt, src, mix.inputs[1])
    _link(nt, em.outputs['Emission'], mix.inputs[2])
    _link(nt, mix.outputs['Shader'], out.inputs['Surface'])
    return mat


def mat_new(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']


# ==================================================================================== red blood cell
def evans_fung(r, R=1.0):
    """Half-thickness / diameter of an RBC at radius r (Evans & Fung 1972:
    D = 7.82 um, C0 = 0.81 um, C2 = 7.83 um, C4 = -4.39 um, normalised by D)."""
    x = min(1.0, r / R)
    c0, c2, c4 = 0.81 / 7.82, 7.83 / 7.82, -4.39 / 7.82
    return 0.5 * math.sqrt(max(0.0, 1 - x * x)) * (c0 + c2 * x * x + c4 * x ** 4)


def rbc_mesh(name='RBC_mesh', diameter=7.8 * UM):
    R = diameter / 2.0
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=18, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        rho = math.sqrt(x * x + y * y)
        r = rho * R
        h = evans_fung(r, R) * diameter
        # keep a rounded rim
        h = max(h, 0.035 * diameter * math.sqrt(max(0.0, 1 - rho ** 8)))
        v.co = Vector((x * R, y * R, math.copysign(h, z) if abs(z) > 1e-6 else 0.0))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    # shape key: 'parachute' - the cup shape RBCs take while squeezing through capillaries
    tmp = bpy.data.objects.new('tmp_rbc', me)
    bpy.context.scene.collection.objects.link(tmp)
    tmp.shape_key_add(name='Basis')
    sk = tmp.shape_key_add(name='parachute')
    for i, v in enumerate(me.vertices):
        p = v.co
        rr = math.sqrt(p.x ** 2 + p.y ** 2) / R
        sk.data[i].co = Vector((p.x * 0.78, p.y * 0.78, p.z + 0.55 * R * (1 - rr * rr) - 0.15 * R))
    sk.value = 0.0   # Blender 5 creates new keys at 1.0
    bpy.data.objects.remove(tmp)
    return me


def rbc_material(name='BIO_RBC', fog=None):
    m, nt, p = mat_new(name)
    oxy = _node(nt, 'ShaderNodeAttribute', (-900, 300), attribute_name='oxy', attribute_type='OBJECT')
    mix = _node(nt, 'ShaderNodeMix', (-600, 300), data_type='RGBA')
    mix.inputs['A'].default_value = hex_rgb('#6E0A14')   # deoxygenated: darker red
    mix.inputs['B'].default_value = hex_rgb('#C8141E')   # oxygenated: brighter red
    _link(nt, oxy.outputs['Fac'], mix.inputs['Factor'])
    tc = _node(nt, 'ShaderNodeTexCoord', (-1100, -100))
    n = _node(nt, 'ShaderNodeTexNoise', (-900, -100))
    n.inputs['Scale'].default_value = 3.0
    n.inputs['Detail'].default_value = 3.0
    _link(nt, tc.outputs['Object'], n.inputs['Vector'])
    mm = _node(nt, 'ShaderNodeMix', (-350, 250), data_type='RGBA', blend_type='MULTIPLY')
    mm.inputs['Factor'].default_value = 0.15
    _link(nt, mix.outputs['Result'], mm.inputs['A'])
    _link(nt, n.outputs['Color'], mm.inputs['B'])
    _link(nt, mm.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.38
    p.inputs['Subsurface Weight'].default_value = 0.45
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.15, 0.1)
    p.inputs['Subsurface Scale'].default_value = 0.25
    p.inputs['Coat Weight'].default_value = 0.18
    p.inputs['Coat Roughness'].default_value = 0.2
    p.inputs['Specular IOR Level'].default_value = 0.42
    b = _bump(nt, n.outputs['Fac'], 0.15, 0.02, (-350, -200))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    if fog:
        add_fog(m, *fog)
    return m


# ==================================================================================== vessel tunnel
def vessel_material(name, base='#8A2430', cell='#B4404A', fog=None, translucent=0.0, emission=None):
    m, nt, p = mat_new(name)
    tc = _node(nt, 'ShaderNodeTexCoord', (-1400, 0))
    mp = _node(nt, 'ShaderNodeMapping', (-1200, 0))
    mp.inputs['Scale'].default_value = (1.0, 0.45, 1.0)   # cells elongated along the flow (Y)
    _link(nt, tc.outputs['Object'], mp.inputs['Vector'])
    vor = _node(nt, 'ShaderNodeTexVoronoi', (-950, 100), feature='DISTANCE_TO_EDGE')
    vor.inputs['Scale'].default_value = 0.9
    _link(nt, mp.outputs['Vector'], vor.inputs['Vector'])
    vor2 = _node(nt, 'ShaderNodeTexVoronoi', (-950, 400), feature='F1')
    vor2.inputs['Scale'].default_value = 0.9
    _link(nt, mp.outputs['Vector'], vor2.inputs['Vector'])
    edge = _ramp(nt, [(0.0, (1, 1, 1, 1)), (0.03, (0, 0, 0, 1))], (-700, 100))
    _link(nt, vor.outputs['Distance'], edge.inputs['Fac'])
    col = _ramp(nt, [(0.0, hex_rgb(base)), (1.0, hex_rgb(cell))], (-700, 400))
    _link(nt, vor2.outputs['Color'], col.inputs['Fac'])
    nuc = _ramp(nt, [(0.0, hex_rgb('#5A1220')), (0.12, hex_rgb('#5A1220')), (0.2, (1, 1, 1, 1))], (-700, 650))
    _link(nt, vor2.outputs['Distance'], nuc.inputs['Fac'])
    mul = _node(nt, 'ShaderNodeMix', (-450, 450), data_type='RGBA', blend_type='MULTIPLY')
    mul.inputs['Factor'].default_value = 0.55
    _link(nt, col.outputs['Color'], mul.inputs['A'])
    _link(nt, nuc.outputs['Color'], mul.inputs['B'])
    edgecol = _node(nt, 'ShaderNodeMix', (-250, 300), data_type='RGBA')
    _link(nt, edge.outputs['Color'], edgecol.inputs['Factor'])
    _link(nt, mul.outputs['Result'], edgecol.inputs['A'])
    edgecol.inputs['B'].default_value = hex_rgb('#B85A64')
    _link(nt, edgecol.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.28
    p.inputs['Subsurface Weight'].default_value = 0.35
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.25, 0.2)
    p.inputs['Subsurface Scale'].default_value = 0.6
    p.inputs['Coat Weight'].default_value = 0.5
    p.inputs['Coat Roughness'].default_value = 0.1
    inv = _node(nt, 'ShaderNodeMath', (-450, -200), operation='SUBTRACT')
    inv.inputs[0].default_value = 1.0
    _link(nt, vor.outputs['Distance'], inv.inputs[1])
    b = _bump(nt, edge.outputs['Color'], 0.22, 0.05, (-250, -200))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    if translucent:
        p.inputs['Alpha'].default_value = 1.0 - translucent
        try:
            m.surface_render_method = 'BLENDED'
            m.use_transparency_overlap = False
        except Exception:
            pass
    if emission:
        p.inputs['Emission Color'].default_value = hex_rgb(emission[0])
        p.inputs['Emission Strength'].default_value = emission[1]
    if fog:
        add_fog(m, *fog)
    return m


def vessel_tunnel(name, radius, length, mat, segs=48, rings=None, curve_amp=0.0, curve_len=60.0, seed=1,
                  bumps=0.08, inward=True, collection=None, y0=None):
    rings = rings or max(24, int(length / (radius * 0.35)))
    rnd = random.Random(seed)
    off = Vector((rnd.random() * 100, rnd.random() * 100, rnd.random() * 100))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    y0 = length / 2 if y0 is None else y0
    allr = []
    for i in range(rings):
        y = y0 - length * i / (rings - 1)
        cx = curve_amp * math.sin(y / curve_len * 2 * math.pi)
        cz = curve_amp * 0.5 * math.sin(y / curve_len * 1.3 * math.pi + 1.0)
        ring = []
        for s in range(segs):
            a = 2 * math.pi * s / segs
            d = Vector((math.cos(a), 0, math.sin(a)))
            p = Vector((cx, y, cz)) + d * radius
            n1 = noise.noise(p * (1.4 / radius) + off)
            n2 = noise.noise(p * (4.0 / radius) + off * 2)
            rr = radius * (1 + bumps * n1 + bumps * 0.35 * n2)
            ring.append(bm.verts.new(Vector((cx, y, cz)) + d * rr))
        allr.append(ring)
    for i in range(rings - 1):
        for s in range(segs):
            a, b = allr[i][s], allr[i][(s + 1) % segs]
            c, d = allr[i + 1][(s + 1) % segs], allr[i + 1][s]
            f = bm.faces.new((a, d, c, b) if inward else (a, b, c, d))
    ob = obj_from_bm(name, bm, [mat], collection)
    add_subsurf(ob, 1, 1)
    return ob


def tunnel_center(y, curve_amp=0.0, curve_len=60.0):
    return Vector((curve_amp * math.sin(y / curve_len * 2 * math.pi), y,
                   curve_amp * 0.5 * math.sin(y / curve_len * 1.3 * math.pi + 1.0)))


# ==================================================================================== flowing cells
def linear_keys(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    from .mascot_api import _fcurves
    for fc in _fcurves(ad.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.extrapolation = 'LINEAR'


def flow_cells(mesh, mat, count, radius, y_range, speed, f0, f1, fps=30, seed=3, oxy=0.0, curve=(0.0, 60.0),
               collection=None, scale=(0.9, 1.1), keep_out=None, parachute=0.0, axis_align=False,
               min_r=0.0):
    """Scatter `count` cells in a tube and animate them along -Y with a
    parabolic (Poiseuille-like) speed profile and slow tumbling."""
    rnd = random.Random(seed)
    obs = []
    dur = (f1 - f0) / fps
    for i in range(count):
        for _ in range(30):
            r = radius * math.sqrt(rnd.uniform((min_r / radius) ** 2 if radius else 0, 1.0))
            a = rnd.uniform(0, 2 * math.pi)
            y = rnd.uniform(*y_range)
            local = Vector((r * math.cos(a), 0, r * math.sin(a)))
            if keep_out is None or (Vector((local.x, y, local.z)) - keep_out[0]).length > keep_out[1]:
                break
        ob = bpy.data.objects.new(f'RBC_{i:03d}', mesh)
        if mat and not mesh.materials:
            mesh.materials.append(mat)
        (collection or bpy.context.scene.collection).objects.link(ob)
        s = rnd.uniform(*scale)
        ob.scale = (s, s, s)
        ob['oxy'] = oxy
        v = speed * (1.15 - 0.6 * (r / max(radius, 1e-6)) ** 2) * rnd.uniform(0.9, 1.1)
        c0 = tunnel_center(y, *curve)
        c1 = tunnel_center(y - v * dur, *curve)
        ob.location = c0 + local
        rot0 = Euler((rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)))
        if axis_align:
            rot0 = Euler((math.radians(90) + rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(0, 6.3)))
        ob.rotation_euler = rot0
        ob.keyframe_insert('location', frame=f0)
        ob.keyframe_insert('rotation_euler', frame=f0)
        ob.location = c1 + local
        spin = rnd.uniform(-1.2, 1.2) * dur * (0.2 if axis_align else 1.0)
        ob.rotation_euler = Euler((rot0.x + spin, rot0.y + spin * 0.6, rot0.z + spin * 0.3))
        ob.keyframe_insert('location', frame=f1)
        ob.keyframe_insert('rotation_euler', frame=f1)
        linear_keys(ob)
        obs.append(ob)
    return obs


def specks(count, radius, y_range, speed, f0, f1, color='#FFB0A0', strength=2.0, seed=9, size=(0.02, 0.06),
           collection=None, fps=30):
    """Tiny plasma specks (proteins/platelet-scale debris) for parallax and depth."""
    rnd = random.Random(seed)
    m, nt, p = mat_new('BIO_Speck')
    p.inputs['Base Color'].default_value = hex_rgb(color)
    p.inputs['Emission Color'].default_value = hex_rgb(color)
    p.inputs['Emission Strength'].default_value = strength
    me = bpy.data.meshes.new('speck')
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    dur = (f1 - f0) / fps
    out = []
    for i in range(count):
        ob = bpy.data.objects.new(f'Speck_{i:03d}', me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        s = rnd.uniform(*size)
        ob.scale = (s, s, s)
        r = radius * math.sqrt(rnd.random())
        a = rnd.uniform(0, 6.283)
        y = rnd.uniform(*y_range)
        ob.location = (r * math.cos(a), y, r * math.sin(a))
        ob.keyframe_insert('location', frame=f0)
        ob.location = (r * math.cos(a), y - speed * rnd.uniform(0.8, 1.2) * dur, r * math.sin(a))
        ob.keyframe_insert('location', frame=f1)
        linear_keys(ob)
        out.append(ob)
    return out


# ==================================================================================== neutrophil
def neutrophil(name='Neutrophil', radius=11 * UM / 2, seed=5, collection=None, fog=None, alpha=0.55):
    rnd = random.Random(seed)
    col = collection or bpy.context.scene.collection
    # membrane: ruffled sphere
    bm = bmesh.new()
    quad_sphere(bm, 22)
    off = Vector((rnd.random() * 50, rnd.random() * 50, rnd.random() * 50))
    for v in bm.verts:
        n = v.co.normalized()
        ruff = 0.06 * noise.noise(n * 3.0 + off) + 0.03 * noise.noise(n * 9.0 + off) + 0.012 * noise.noise(n * 24 + off)
        v.co = n * radius * (1 + ruff)
    m, nt, p = mat_new('BIO_NeutrophilMembrane')
    tc = _node(nt, 'ShaderNodeTexCoord', (-1000, 0))
    nz = _node(nt, 'ShaderNodeTexNoise', (-800, 0))
    nz.inputs['Scale'].default_value = 2.5
    nz.inputs['Detail'].default_value = 6.0
    _link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    ramp = _ramp(nt, [(0.3, hex_rgb('#D9CFE6')), (0.7, hex_rgb('#F4EEF7'))], (-550, 150))
    _link(nt, nz.outputs['Fac'], ramp.inputs['Fac'])
    _link(nt, ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.25
    p.inputs['Subsurface Weight'].default_value = 0.6
    p.inputs['Subsurface Radius'].default_value = (0.8, 0.75, 1.0)
    p.inputs['Subsurface Scale'].default_value = 0.4
    p.inputs['Coat Weight'].default_value = 0.6
    p.inputs['Alpha'].default_value = alpha
    p.inputs['Emission Color'].default_value = hex_rgb('#B8A8D8')
    p.inputs['Emission Strength'].default_value = 0.08
    b = _bump(nt, nz.outputs['Fac'], 0.35, 0.05, (-300, -200))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    try:
        m.surface_render_method = 'BLENDED'
        m.use_transparency_overlap = False
    except Exception:
        pass
    if fog:
        add_fog(m, *fog)
    body = obj_from_bm(name, bm, [m], col)
    add_subsurf(body, 1, 1)
    # animated undulation: displace with a moving noise texture
    tex = bpy.data.textures.new(name + '_wobble', 'CLOUDS')
    tex.noise_scale = 0.9
    ctrl = bpy.data.objects.new(name + '_wobble_ctrl', None)
    col.objects.link(ctrl)
    ctrl.parent = body
    disp = body.modifiers.new('Wobble', 'DISPLACE')
    disp.texture = tex
    disp.texture_coords = 'OBJECT'
    disp.texture_coords_object = ctrl
    disp.strength = radius * 0.10
    disp.mid_level = 0.5
    # lobed nucleus (3-4 lobes joined by thin bridges)
    mb = bpy.data.metaballs.new(name + '_nucleus_mb')
    mb.resolution = radius * 0.06
    mb.render_resolution = radius * 0.04
    lobes = [Vector((-0.38, 0.05, 0.15)), Vector((-0.05, -0.15, 0.32)), Vector((0.30, 0.0, 0.12)), Vector((0.12, 0.2, -0.25))]
    prev = None
    for c in lobes:
        el = mb.elements.new()
        el.co = c * radius
        el.radius = radius * 0.30
        if prev is not None:
            mid = (prev + c) / 2
            e2 = mb.elements.new()
            e2.co = mid * radius
            e2.radius = radius * 0.11
        prev = c
    nuc_ob = bpy.data.objects.new(name + '_nucleus', mb)
    col.objects.link(nuc_ob)
    nm, nnt, np_ = mat_new('BIO_NeutrophilNucleus')
    np_.inputs['Base Color'].default_value = hex_rgb('#5B3C9E')
    np_.inputs['Roughness'].default_value = 0.35
    np_.inputs['Subsurface Weight'].default_value = 0.5
    np_.inputs['Subsurface Radius'].default_value = (0.6, 0.4, 1.0)
    np_.inputs['Emission Color'].default_value = hex_rgb('#6A48B8')
    np_.inputs['Emission Strength'].default_value = 0.25
    mb.materials.append(nm)
    nuc_ob.parent = body
    # granules
    gm, gnt, gp = mat_new('BIO_Granule')
    gp.inputs['Base Color'].default_value = hex_rgb('#E9D2F0')
    gp.inputs['Emission Color'].default_value = hex_rgb('#F2C8F0')
    gp.inputs['Emission Strength'].default_value = 0.6
    gp.inputs['Roughness'].default_value = 0.3
    gme = bpy.data.meshes.new(name + '_granule')
    gbm = bmesh.new()
    bmesh.ops.create_icosphere(gbm, subdivisions=2, radius=1.0)
    gbm.to_mesh(gme)
    gbm.free()
    for poly in gme.polygons:
        poly.use_smooth = True
    gme.materials.append(gm)
    for i in range(110):
        g = bpy.data.objects.new(f'{name}_gran_{i:03d}', gme)
        col.objects.link(g)
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        g.location = d * radius * rnd.uniform(0.35, 0.85)
        s = radius * rnd.uniform(0.018, 0.035)
        g.scale = (s, s, s)
        g.parent = body
    return body, ctrl, nuc_ob


def pseudopod(name, start, end, radius, mat, collection=None, segs=12):
    """Blobby extension of a phagocyte reaching from start towards end."""
    bm = bmesh.new()
    pts, rad = [], []
    N = 9
    for i in range(N):
        t = i / (N - 1)
        p = start.lerp(end, t)
        w = radius * (1.0 - 0.55 * t) * (1 + 0.15 * math.sin(t * 9))
        pts.append(p)
        rad.append((w, w))
    tube_along(bm, pts, rad, segs=segs, cap_start=True, cap_end=True)
    ob = obj_from_bm(name, bm, [mat], collection)
    add_subsurf(ob, 2, 2)
    return ob


# ==================================================================================== heart valve
def valve(name, radius, cusps=3, mat=None, collection=None, thickness=0.06):
    """Semilunar/atrioventricular style valve: `cusps` curved leaflets hinged on a ring.
    Each leaflet is its own object (hinge at the ring) so it can rotate open/closed.
    Leaflet local: hinge along X at origin, closed state = pointing to the ring centre."""
    col = collection or bpy.context.scene.collection
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    leaves = []
    for k in range(cusps):
        a0 = 2 * math.pi * k / cusps
        bm = bmesh.new()
        nu, nv = 14, 10
        grid = []
        span = 2 * math.pi / cusps
        for i in range(nu + 1):
            row = []
            u = i / nu
            ang = -span / 2 + span * u
            for j in range(nv + 1):
                v = j / nv
                # from the ring (v=0) towards the centre (v=1); belly bulges downstream (-Y)
                edge = Vector((math.cos(ang), 0, math.sin(ang))) * radius
                rr = radius * (1 - v) + radius * 0.02
                p = Vector((math.cos(ang) * rr, 0, math.sin(ang) * rr))
                belly = math.sin(math.pi * v) * math.sin(math.pi * u) * radius * 0.35
                p.y -= belly
                # free edge scallop
                if j == nv:
                    p *= 1.0
                row.append(bm.verts.new(p))
            grid.append(row)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        # rotate so hinge (ring midpoint of this cusp) sits at origin; we keep world placement
        ob = obj_from_bm(f'{name}_cusp{k}', bm, [mat] if mat else [], col)
        sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
        sol.thickness = thickness
        add_subsurf(ob, 1, 2)
        # pivot at the cusp's ring midpoint
        mid = Vector((math.cos(0), 0, math.sin(0))) * radius
        ob.data.transform(Matrix.Rotation(a0, 4, 'Y'))
        hinge = Matrix.Rotation(a0, 4, 'Y') @ Vector((radius, 0, 0))
        ob.data.transform(Matrix.Translation(-hinge))
        ob.location = hinge
        ob.parent = root
        # local hinge axis = tangent of the ring at a0 -> store for animation
        tangent = Vector((-math.sin(-a0), 0, math.cos(-a0)))
        ob['hinge_axis'] = tuple(Matrix.Rotation(a0, 3, 'Y') @ Vector((0, 0, 1)))
        leaves.append(ob)
    return root, leaves


def animate_valve(leaves, keys, open_deg=78):
    """keys: list of (frame, openness 0..1).  Leaflets swing about their hinge
    tangent, bending downstream (-Y) when open."""
    for ob in leaves:
        ax = Vector(ob['hinge_axis'])
        for f, k in keys:
            q = Matrix.Rotation(math.radians(open_deg * k), 4, ax).to_quaternion()
            ob.rotation_mode = 'QUATERNION'
            ob.rotation_quaternion = q
            ob.keyframe_insert('rotation_quaternion', frame=f)


# ==================================================================================== heart
def muscle_material(name='BIO_Myocardium', base='#7A1420', light='#B8323A', fog=None):
    m, nt, p = mat_new(name)
    tc = _node(nt, 'ShaderNodeTexCoord', (-1300, 0))
    mp = _node(nt, 'ShaderNodeMapping', (-1100, 0))
    mp.inputs['Scale'].default_value = (1.0, 1.0, 5.0)
    _link(nt, tc.outputs['Object'], mp.inputs['Vector'])
    w = _node(nt, 'ShaderNodeTexWave', (-850, 0), wave_type='BANDS', bands_direction='Z')
    w.inputs['Scale'].default_value = 3.0
    w.inputs['Distortion'].default_value = 6.0
    w.inputs['Detail'].default_value = 4.0
    _link(nt, mp.outputs['Vector'], w.inputs['Vector'])
    r = _ramp(nt, [(0.2, hex_rgb(base)), (0.8, hex_rgb(light))], (-600, 150))
    _link(nt, w.outputs['Fac'], r.inputs['Fac'])
    _link(nt, r.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.3
    p.inputs['Subsurface Weight'].default_value = 0.4
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.2, 0.15)
    p.inputs['Subsurface Scale'].default_value = 0.5
    p.inputs['Coat Weight'].default_value = 0.6
    p.inputs['Coat Roughness'].default_value = 0.08
    b = _bump(nt, w.outputs['Fac'], 0.3, 0.05, (-350, -200))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    if fog:
        add_fog(m, *fog)
    return m


def heart_exterior(name='Heart', collection=None, seed=2):
    """Stylised anatomical heart built from metaballs (ventricles, atria) and tubes
    (aorta arch, pulmonary trunk, venae cavae, coronary vessels). Units: ~1 BU tall."""
    col = collection or bpy.context.scene.collection
    mb = bpy.data.metaballs.new(name + '_mb')
    mb.resolution = 0.03
    mb.render_resolution = 0.018

    def ball(co, r, typ='BALL', size=None):
        e = mb.elements.new(type=typ)
        e.co = co
        e.radius = r
        if size:
            e.size_x, e.size_y, e.size_z = size
        return e
    # ventricles (apex points down-left of the body = +X screen-left in front view is character's left)
    ball((0.04, 0.0, -0.08), 0.50, 'ELLIPSOID', (1.0, 0.85, 1.0))        # ventricular mass
    ball((0.14, 0.02, -0.34), 0.34, 'ELLIPSOID', (0.9, 0.8, 0.9))
    ball((0.20, 0.03, -0.48), 0.14)                                      # apex
    ball((-0.20, -0.10, -0.10), 0.36, 'ELLIPSOID', (0.9, 0.8, 1.0))    # right ventricle (front)
    ball((-0.34, 0.06, 0.22), 0.26)                                      # right atrium
    ball((0.28, 0.15, 0.24), 0.23)                                       # left atrium
    ob = bpy.data.objects.new(name, mb)
    col.objects.link(ob)
    mm = muscle_material('BIO_HeartExt', '#8C1622', '#C23A3E')
    mb.materials.append(mm)
    # great vessels
    vm, vnt, vp = mat_new('BIO_ArteryExt')
    vp.inputs['Base Color'].default_value = hex_rgb('#C8505A')
    vp.inputs['Roughness'].default_value = 0.3
    vp.inputs['Subsurface Weight'].default_value = 0.3
    vp.inputs['Coat Weight'].default_value = 0.5
    bm_ = bpy.data.materials.get('BIO_VeinExt') or bpy.data.materials.new('BIO_VeinExt')
    bm_.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = hex_rgb('#3B4C9A')
    bm_.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.3
    bm_.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.5
    vessels = []

    def vessel(nm, pts, r0, r1, mat):
        bm = bmesh.new()
        P = [Vector(p) for p in pts]
        # smooth catmull-ish resample
        dense = []
        for i in range(len(P) - 1):
            for t in range(8):
                u = t / 8
                p0 = P[max(0, i - 1)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(len(P) - 1, i + 2)]
                dense.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
        dense.append(P[-1])
        rad = [(lerp(r0, r1, i / (len(dense) - 1)),) * 2 for i in range(len(dense))]
        tube_along(bm, dense, rad, segs=16)
        o = obj_from_bm(nm, bm, [mat], col)
        add_subsurf(o, 1, 2)
        o.parent = ob
        vessels.append(o)
        return o
    vessel(name + '_Aorta', [(0.02, 0.05, 0.15), (0.04, 0.02, 0.55), (-0.05, 0.10, 0.78), (-0.25, 0.25, 0.75), (-0.32, 0.38, 0.45), (-0.30, 0.42, 0.0)], 0.12, 0.10, vm)
    vessel(name + '_PulmTrunk', [(-0.12, -0.18, 0.1), (-0.05, -0.20, 0.42), (0.12, -0.05, 0.55), (0.35, 0.05, 0.52)], 0.11, 0.08, bm_)
    vessel(name + '_SVC', [(-0.36, 0.10, 0.30), (-0.38, 0.12, 0.62), (-0.40, 0.14, 0.90)], 0.085, 0.08, bm_)
    vessel(name + '_IVC', [(-0.34, 0.12, 0.05), (-0.36, 0.16, -0.25), (-0.38, 0.18, -0.45)], 0.09, 0.08, bm_)
    for i, (a, b) in enumerate((((0.0, -0.38, 0.05), (0.25, -0.30, -0.45)), ((-0.12, -0.36, 0.0), (-0.10, -0.30, -0.42)))):
        mid = ((a[0] + b[0]) / 2 + 0.05, (a[1] + b[1]) / 2 - 0.06, (a[2] + b[2]) / 2)
        vessel(f'{name}_Coronary{i}', [a, mid, b], 0.025, 0.012, vm)
    return ob, vessels


def heart_interior(name='Chamber', radius=12.0, collection=None, fog=None, seed=4):
    """Inside a ventricle: an ovoid cavity lined with trabeculae (muscle ridges)
    plus chordae tendineae strings.  Returns (cavity, ridges)."""
    rnd = random.Random(seed)
    col = collection or bpy.context.scene.collection
    mat = muscle_material('BIO_Myocardium', fog=fog)
    bm = bmesh.new()
    quad_sphere(bm, 24)
    off = Vector((rnd.random() * 30,) * 3)
    for v in bm.verts:
        n = v.co.normalized()
        rr = radius * (1 + 0.10 * noise.noise(n * 2 + off) + 0.04 * noise.noise(n * 6 + off))
        v.co = Vector((n.x * rr * 0.9, n.y * rr * 1.25, n.z * rr))
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    cav = obj_from_bm(name, bm, [mat], col)
    add_subsurf(cav, 1, 1)
    ridges = []
    bm = bmesh.new()
    for i in range(46):
        th = rnd.uniform(0, 2 * math.pi)
        z0 = rnd.uniform(-0.8, 0.6)
        pts, rad, nrm = [], [], []
        for k in range(10):
            t = k / 9
            ang = th + 0.6 * t + 0.2 * math.sin(t * 5 + i)
            z = z0 + 0.5 * t
            n = Vector((math.cos(ang) * math.sqrt(max(0, 1 - z * z)), math.sin(ang) * math.sqrt(max(0, 1 - z * z)), z))
            p = Vector((n.x * radius * 0.86, n.y * radius * 1.18, n.z * radius * 0.95))
            pts.append(p)
            w = radius * 0.035 * (0.6 + math.sin(math.pi * t))
            rad.append((w, w))
            nrm.append(-n)
        tube_along(bm, pts, rad, segs=8, normals=nrm)
    rid = obj_from_bm(name + '_Trabeculae', bm, [mat], col)
    add_subsurf(rid, 1, 1)
    ridges.append(rid)
    return cav, rid, mat


def chordae(name, anchors, tips, mat, collection=None, r=0.03):
    bm = bmesh.new()
    for a, b in zip(anchors, tips):
        a, b = Vector(a), Vector(b)
        mid = a.lerp(b, 0.5) + Vector((0, 0, -0.3))
        tube_along(bm, [a, mid, b], [(r * 1.5, r * 1.5), (r, r), (r * 0.8, r * 0.8)], segs=6)
    ob = obj_from_bm(name, bm, [mat], collection)
    add_subsurf(ob, 1, 1)
    return ob


# ==================================================================================== lungs
def alveolus(name, center, radius, collection=None, seed=8):
    """Air sac seen through the capillary wall: a bright, airy cluster of bubbles."""
    rnd = random.Random(seed)
    col = collection or bpy.context.scene.collection
    m, nt, p = mat_new('BIO_AlveolarWall')
    p.inputs['Base Color'].default_value = hex_rgb('#F2B8B8')
    p.inputs['Roughness'].default_value = 0.2
    p.inputs['Subsurface Weight'].default_value = 0.7
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.6, 0.6)
    p.inputs['Coat Weight'].default_value = 0.7
    p.inputs['Emission Color'].default_value = hex_rgb('#FFD8D0')
    p.inputs['Emission Strength'].default_value = 0.35
    obs = []
    for i in range(9):
        bm = bmesh.new()
        quad_sphere(bm, 10)
        r = radius * (1.0 if i == 0 else rnd.uniform(0.45, 0.7))
        c = Vector(center) + (Vector((0, 0, 0)) if i == 0 else Vector((rnd.uniform(-1, 1), rnd.uniform(0.2, 1), rnd.uniform(-1, 1))).normalized() * radius * 1.25)
        for v in bm.verts:
            n = v.co.normalized()
            v.co = c + n * r * (1 + 0.05 * noise.noise(n * 3 + Vector((i, i, i))))
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        ob = obj_from_bm(f'{name}_{i}', bm, [m], col)
        add_subsurf(ob, 1, 1)
        obs.append(ob)
    return obs


def gas_particles(name, count, src_box, dst_box, f0, f1, color, strength, size, seed=11, collection=None,
                  stagger=0.6, wobble=0.15):
    """Particles that drift from a source region to a destination region (diffusion
    visualised): each starts at a random time inside [f0, f0+stagger*(f1-f0)]."""
    rnd = random.Random(seed)
    col = collection or bpy.context.scene.collection
    m, nt, p = mat_new(f'BIO_{name}')
    p.inputs['Base Color'].default_value = hex_rgb(color)
    p.inputs['Emission Color'].default_value = hex_rgb(color)
    p.inputs['Emission Strength'].default_value = strength
    p.inputs['Roughness'].default_value = 0.2
    me = bpy.data.meshes.new(name + '_mesh')
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(m)
    obs = []
    span = f1 - f0
    for i in range(count):
        ob = bpy.data.objects.new(f'{name}_{i:03d}', me)
        col.objects.link(ob)
        s = size * rnd.uniform(0.7, 1.3)
        a = Vector([rnd.uniform(lo, hi) for lo, hi in zip(*src_box)])
        b = Vector([rnd.uniform(lo, hi) for lo, hi in zip(*dst_box)])
        st = f0 + int(rnd.uniform(0, stagger) * span)
        en = min(f1, st + int(span * rnd.uniform(0.35, 0.55)))
        ob.scale = (0, 0, 0)
        ob.location = a
        ob.keyframe_insert('scale', frame=max(f0, st - 1))
        ob.keyframe_insert('location', frame=max(f0, st - 1))
        ob.scale = (s, s, s)
        ob.keyframe_insert('scale', frame=st + 3)
        steps = 4
        for k in range(1, steps + 1):
            t = k / steps
            p_ = a.lerp(b, t) + Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))) * wobble * math.sin(math.pi * t)
            ob.location = p_
            ob.keyframe_insert('location', frame=int(lerp(st, en, t)))
        ob.scale = (s, s, s)
        ob.keyframe_insert('scale', frame=en - 3)
        ob.scale = (0, 0, 0)
        ob.keyframe_insert('scale', frame=en)
        obs.append(ob)
    return obs

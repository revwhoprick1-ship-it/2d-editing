"""Bathroom set + toilet characters (VIDEO_005). Real-world scale, metres; the toilet faces -Y."""
import math
import os

import bmesh
import bpy
from mathutils import Vector

from studio_lib import render_setup as RS
from studio_lib.materials import hex_rgb, simple


def _link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def mesh_obj(name, bm, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = _link(bpy.data.objects.new(name, me))
    for p in me.polygons:
        p.use_smooth = smooth
    me.materials.append(mat)
    return o


def lathe(name, prof, mat, segs=48, sy=1.0):
    """prof: [(radius, z)] spun around Z; sy squashes into an oval (toilet bowls are longer than wide)."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=segs, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    for v in bm.verts:
        v.co.y *= sy
    o = mesh_obj(name, bm, mat)
    sub = o.modifiers.new('sub', 'SUBSURF')
    sub.levels = sub.render_levels = 1
    return o


def rbox(name, loc, size, mat, bevel=0.02, parent=None, segs=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new('bv', 'BEVEL')
        b.width = bevel
        b.segments = segs
        b.limit_method = 'NONE'
        bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def cyl(name, loc, r, h, mat, verts=32, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


def sphere(name, loc, r, mat, parent=None, segs=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=segs // 2, radius=r, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o


def tex_mat(name, img, scale=(1, 1, 1), rough=0.35, coat=0.0, bump=0.0, proj='BOX'):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(img, check_existing=True)
    tx.projection = proj
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    nt.links.new(tx.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    if coat:
        p.inputs['Coat Weight'].default_value = coat
    if bump:
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = bump
        nt.links.new(tx.outputs['Color'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def mats():
    M = {}
    M['porcelain'] = simple('Porcelain', '#F3F3EF', rough=0.12, coat=1.0)
    M['chrome'] = simple('Chrome', '#D8DCE2', rough=0.08, metallic=1.0)
    M['water'] = simple('BowlWater', '#5FB4E6', rough=0.02, coat=1.0)
    M['eye'] = simple('TEyeWhite', '#FFFFFF', rough=0.3)
    M['pupil'] = simple('TPupil', '#101012', rough=0.2, coat=1.0)
    M['brow'] = simple('TBrow', '#2A2A30', rough=0.5)
    M['dark'] = simple('BowlDark', '#1E2A33', rough=0.3)
    M['red'] = simple('TRedEye', '#FF2A2A', emission=('#FF2A2A', 4.0))
    return M


# ============================================================================== toilet character
class Toilet:
    """root (move/squash/hop) -> body; lid on a hinge (its 'mouth'); eyes + brows on the tank."""

    def __init__(self, name, loc=(0, 0, 0), rotz=0.0, scale=1.0, M=None):
        M = M or mats()
        self.name = name
        self.root = _link(bpy.data.objects.new(name, None))
        self.root.location = loc
        self.root.rotation_euler = (0, 0, math.radians(rotz))
        self.root.scale = (scale,) * 3
        R = self.root
        bowl = lathe(name + '_Bowl', [(0.13, 0.0), (0.135, 0.06), (0.16, 0.2), (0.205, 0.33), (0.215, 0.39), (0.205, 0.405),
                                       (0.17, 0.40), (0.15, 0.33), (0.09, 0.22), (0.05, 0.18)], M['porcelain'], sy=1.28)
        bowl.parent = R
        wat = cyl(name + '_Water', (0, 0, 0.25), 0.11, 0.004, M['water'], parent=R)
        wat.scale.y = 1.25
        seat = lathe(name + '_Seat', [(0.175, 0.405), (0.21, 0.41), (0.215, 0.425), (0.19, 0.432), (0.165, 0.425), (0.16, 0.41)],
                     M['porcelain'], sy=1.25)
        seat.parent = R
        self.hinge = _link(bpy.data.objects.new(name + '_Hinge', None))
        self.hinge.parent = R
        self.hinge.location = (0, 0.24, 0.44)
        lid = lathe(name + '_Lid', [(0.0, 0.0), (0.18, 0.0), (0.205, 0.006), (0.21, 0.02), (0.2, 0.03), (0.0, 0.032)],
                    M['porcelain'], sy=1.25)
        lid.parent = self.hinge
        lid.location = (0, -0.24, -0.008)
        tank = rbox(name + '_Tank', (0, 0.33, 0.62), (0.44, 0.19, 0.42), M['porcelain'], bevel=0.035, parent=R)
        rbox(name + '_TankLid', (0, 0.33, 0.845), (0.47, 0.215, 0.04), M['porcelain'], bevel=0.015, parent=R)
        rbox(name + '_Neck', (0, 0.26, 0.38), (0.26, 0.12, 0.14), M['porcelain'], bevel=0.03, parent=R)
        self.handle = _link(bpy.data.objects.new(name + '_HandlePivot', None))
        self.handle.parent = R
        self.handle.location = (-0.17, 0.235, 0.78)
        rbox(name + '_Handle', (0.045, -0.01, 0), (0.09, 0.015, 0.018), M['chrome'], bevel=0.006, parent=self.handle)
        cyl(name + '_HandleBase', (0, 0.0, 0), 0.016, 0.012, M['chrome'], parent=self.handle, rot=(math.radians(90), 0, 0))
        # face on the tank
        self.eyes, self.pupils, self.brows = [], [], []
        for s in (-1, 1):
            e = sphere(f'{name}_Eye{s}', (0.09 * s, 0.25, 0.93), 0.06, M['eye'], parent=R)      # frog-eyes on the tank lid: never hidden by the open lid
            e.scale.y = 0.8
            p = sphere(f'{name}_Pupil{s}', (0.09 * s, 0.205, 0.93), 0.026, M['pupil'], parent=R)
            b = _link(bpy.data.objects.new(f'{name}_BrowPivot{s}', None))
            b.parent = R
            b.location = (0.09 * s, 0.235, 1.01)
            rbox(f'{name}_Brow{s}', (0, 0, 0), (0.1, 0.02, 0.022), M['brow'], bevel=0.008, parent=b)
            self.eyes.append(e)
            self.pupils.append(p)
            self.brows.append(b)
        self.base = {'loc': Vector(loc), 'scale': scale}

    # --- animation helpers (frame-based)
    def lid(self, f, deg):
        self.hinge.rotation_euler = (math.radians(-deg), 0, 0)
        self.hinge.keyframe_insert('rotation_euler', frame=f)

    def chomp(self, f0, f1, period=6, open_deg=75):
        f = f0
        while f < f1:
            self.lid(f, open_deg)
            self.lid(f + period // 2, 0)
            f += period

    def mood(self, f, anger=0.0, look=(0.0, 0.0), squint=0.0):
        """anger 0..1 tilts the brows into a V; look moves the pupils; squint flattens the eyes."""
        for s, b, p, e in zip((-1, 1), self.brows, self.pupils, self.eyes):
            b.rotation_euler = (0, math.radians(-28 * anger * s), 0)
            b.location.z = 1.01 - 0.025 * anger
            b.keyframe_insert('rotation_euler', frame=f)
            b.keyframe_insert('location', frame=f)
            p.location = (0.09 * s + 0.022 * look[0], 0.205, 0.93 + 0.022 * look[1])
            p.keyframe_insert('location', frame=f)
            e.scale.z = 1.0 - 0.55 * squint
            e.keyframe_insert('scale', frame=f)

    def blink(self, f):
        for e in self.eyes:
            e.keyframe_insert('scale', frame=f - 1)
            z = e.scale.z
            e.scale.z = 0.08
            e.keyframe_insert('scale', frame=f + 1)
            e.scale.z = z
            e.keyframe_insert('scale', frame=f + 3)

    def pose(self, f, loc=None, squash=0.0, lean=0.0, turn=None):
        """squash > 0 = squashed (wide/short), < 0 = stretched; lean = forward tilt (deg)."""
        r = self.root
        if loc is not None:
            r.location = loc
            r.keyframe_insert('location', frame=f)
        s = self.base['scale']
        r.scale = (s * (1 + 0.5 * squash), s * (1 + 0.5 * squash), s * (1 - squash))
        r.keyframe_insert('scale', frame=f)
        rz = r.rotation_euler.z if turn is None else math.radians(turn)
        r.rotation_euler = (math.radians(-lean), 0, rz)
        r.keyframe_insert('rotation_euler', frame=f)

    def hop(self, f, a, b, height=0.35, dur=10):
        """Anticipation squash -> stretched airborne arc -> landing squash -> settle."""
        a, b = Vector(a), Vector(b)
        self.pose(f, a, squash=0.0)
        self.pose(f + 2, a, squash=0.25, lean=-8)
        self.pose(f + 4, a.lerp(b, 0.25) + Vector((0, 0, height * 0.75)), squash=-0.2, lean=10)
        self.pose(f + dur // 2 + 2, a.lerp(b, 0.6) + Vector((0, 0, height)), squash=-0.1, lean=5)
        self.pose(f + dur, b, squash=0.3, lean=-4)
        self.pose(f + dur + 3, b, squash=-0.06)
        self.pose(f + dur + 5, b, squash=0.0)

    def flush(self, f):
        self.handle.rotation_euler = (0, 0, 0)
        self.handle.keyframe_insert('rotation_euler', frame=f - 1)
        self.handle.rotation_euler = (0, math.radians(35), 0)
        self.handle.keyframe_insert('rotation_euler', frame=f + 2)
        self.handle.rotation_euler = (0, 0, 0)
        self.handle.keyframe_insert('rotation_euler', frame=f + 8)


# ============================================================================== water effects
def water_mat():
    m = simple('WaterFX', '#BFE6FF', rough=0.0, coat=1.0)
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Transmission Weight'].default_value = 0.9
    p.inputs['IOR'].default_value = 1.33
    p.inputs['Alpha'].default_value = 0.75
    p.inputs['Emission Color'].default_value = hex_rgb('#9FD8FF')
    p.inputs['Emission Strength'].default_value = 0.05
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return m


def droplets(name, f0, n, origin, vel, spread, life=18, size=(0.012, 0.03), seed=1, gravity=4.0, mat=None):
    """n keyframed water drops (stretched along their velocity) fired from origin with velocity vel (m/s)."""
    import random
    rnd = random.Random(seed)
    mat = mat or water_mat()
    origin, vel = Vector(origin), Vector(vel)
    obs = []
    for i in range(n):
        fs = f0 + rnd.randint(0, max(1, life // 3))
        v = vel + Vector((rnd.uniform(-spread, spread), rnd.uniform(-spread, spread), rnd.uniform(-spread, spread)))
        r = rnd.uniform(*size)
        o = sphere(f'{name}{i}', origin, r, mat, segs=10)
        o.scale = (1, 1, 2.2)
        o.hide_render = True
        o.keyframe_insert('hide_render', frame=0)
        o.hide_render = False
        o.keyframe_insert('hide_render', frame=fs)
        for k in range(0, life + 1, 2):
            t = k / 30
            o.location = origin + v * t + Vector((0, 0, -0.5 * gravity * t * t))
            o.keyframe_insert('location', frame=fs + k)
            vv = v + Vector((0, 0, -gravity * t))
            o.rotation_euler = vv.to_track_quat('Z', 'Y').to_euler()
            o.keyframe_insert('rotation_euler', frame=fs + k)
        o.hide_render = True
        o.keyframe_insert('hide_render', frame=fs + life)
        obs.append(o)
    return obs


def jet(name, f0, f1, origin, direction, length, radius, mat=None):
    """A water jet: a tapered tube that grows out of the nozzle, wobbles, and shrinks away."""
    mat = mat or water_mat()
    origin, d = Vector(origin), Vector(direction).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=radius * 0.6, radius2=radius * 1.6, depth=1.0, location=(0, 0, 0.5))
    o = bpy.context.object
    o.name = name
    bpy.ops.object.transform_apply(location=True)
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    o.location = origin
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    w = o.modifiers.new('wave', 'WAVE')
    w.height, w.width, w.speed, w.narrowness = 0.015, 0.25, 0.4, 1.5
    for f, ln in ((f0 - 1, 0.001), (f0 + 3, length), (f1 - 3, length), (f1, 0.001)):
        o.scale = (1, 1, ln)
        o.keyframe_insert('scale', frame=f)
    o.hide_render = True
    o.keyframe_insert('hide_render', frame=0)
    o.hide_render = False
    o.keyframe_insert('hide_render', frame=f0 - 1)
    o.hide_render = True
    o.keyframe_insert('hide_render', frame=f1 + 1)
    return o


# ============================================================================== bathroom
def bathroom(gfx, window_sun=True, boss=False):
    """3.4 x 3.2 m bathroom, camera side open (-Y). Toilet spot (−0.55, 1.15), tub along the left wall."""
    sc = bpy.context.scene
    vs = sc.view_settings
    vs.view_transform, vs.look, vs.exposure = 'AgX', 'AgX - Medium High Contrast', 0.0
    RS.world_color((0.09, 0.08, 0.07), 1.0)
    W, D, H = 3.4, 3.2, 2.7
    tile = tex_mat('TileWall', os.path.join(gfx, 'tile_wall.png'), scale=(0.9, 0.9, 0.9), rough=0.18, coat=0.4, bump=0.25)
    floor = tex_mat('TileFloor', os.path.join(gfx, 'tile_floor.png'), scale=(0.6, 0.6, 0.6), rough=0.3, coat=0.2, bump=0.2)
    paint = simple('PaintUpper', '#7FB9B0' if not boss else '#5E6F8C', rough=0.7)
    ceil = simple('Ceiling', '#EEE9E0', rough=0.8)
    wood = simple('Wood', '#8A5A36', rough=0.45, coat=0.2)
    M = mats()
    rbox('Floor', (0, 0.4, -0.05), (W, D + 1.5, 0.1), floor, bevel=0)
    rbox('Ceil', (0, 0.4, H + 0.05), (W, D + 1.5, 0.1), ceil, bevel=0)
    for name, loc, size in (('WallBack', (0, D / 2 + 0.6, 0.7), (W, 0.1, 1.4)), ('WallL', (-W / 2, 0.4, 0.7), (0.1, D + 1.5, 1.4)),
                            ('WallR', (W / 2, 0.4, 0.7), (0.1, D + 1.5, 1.4))):
        rbox(name + 'Tile', loc, size, tile, bevel=0)
        rbox(name + 'Paint', (loc[0], loc[1], 2.05), (size[0] - 0.01 if size[0] < 1 else size[0], size[1] - 0.01 if size[1] < 1 else size[1], 1.3), paint, bevel=0)
        rbox(name + 'Trim', (loc[0], loc[1], 1.41), (size[0] + 0.03 if size[0] < 1 else size[0], size[1] + 0.03 if size[1] < 1 else size[1], 0.04), wood, bevel=0.005)
    # front wall (behind the camera in wide shots) with the door at x=+0.8
    for name, x0, x1 in (('FrontL', -W / 2, 0.35), ('FrontR', 1.25, W / 2)):
        rbox(name + 'Tile', ((x0 + x1) / 2, -1.3, 0.7), (x1 - x0, 0.1, 1.4), tile, bevel=0)
        rbox(name + 'Paint', ((x0 + x1) / 2, -1.3, 2.05), (x1 - x0, 0.1, 1.3), paint, bevel=0)
    rbox('FrontTop', (0.8, -1.3, 2.45), (0.9, 0.1, 0.5), paint, bevel=0)
    door_h = _link(bpy.data.objects.new('DoorHinge', None))
    door_h.location = (0.37, -1.3, 0)
    d = rbox('Door', (0.43, 0, 1.05), (0.86, 0.05, 2.1), simple('DoorPaint', '#F3EEE4', rough=0.4), bevel=0.01, parent=door_h)
    cyl('DoorKnob', (0.78, -0.05, 1.0), 0.03, 0.06, simple('Brass', '#C9A24A', rough=0.2, metallic=1.0), parent=door_h,
        rot=(math.radians(90), 0, 0))
    rbox('Hall', (0.8, -2.3, 1.2), (2.0, 0.1, 2.4), simple('HallWall', '#D9C4A5', rough=0.8), bevel=0)
    RS.area_light('HallLight', (0.8, -1.9, 2.3), (0.8, -1.9, 0), 80, size=0.6, color=(1.0, 0.85, 0.65))
    # sink cabinet + mirror (right of the toilet)
    rbox('Cabinet', (0.75, 2.0, 0.42), (0.8, 0.45, 0.84), wood, bevel=0.015)
    rbox('Counter', (0.75, 1.98, 0.86), (0.86, 0.5, 0.04), simple('Marble', '#E8E4DC', rough=0.15, coat=0.6), bevel=0.01)
    cyl('Sink', (0.75, 1.95, 0.9), 0.2, 0.06, M['porcelain'])
    cyl('Faucet', (0.75, 2.15, 0.98), 0.015, 0.16, M['chrome'])
    rbox('Spout', (0.75, 2.09, 1.05), (0.025, 0.13, 0.025), M['chrome'], bevel=0.008)
    rbox('MirrorFrame', (0.75, 2.19, 1.75), (0.72, 0.03, 0.9), wood, bevel=0.01)
    rbox('Mirror', (0.75, 2.17, 1.75), (0.64, 0.01, 0.82), simple('Mirror', '#DDE6EE', rough=0.02, metallic=1.0), bevel=0)
    for i, (c, h) in enumerate((('#E4572E', 0.18), ('#29A19C', 0.14), ('#F2C14E', 0.22), ('#A23B72', 0.12))):
        cyl(f'Bottle{i}', (0.45 + i * 0.09, 2.08, 0.88 + h / 2), 0.03, h, simple(f'Bottle{i}', c, rough=0.25, coat=0.6))
    # shelf with towels and a plant above the toilet
    rbox('Shelf', (-0.55, 2.1, 1.72), (0.7, 0.2, 0.03), wood, bevel=0.005)
    for i, c in enumerate(('#F07C5A', '#5A8DF0', '#F4E9D8')):
        rbox(f'TowelStack{i}', (-0.75 + i * 0.2, 2.1, 1.78), (0.18, 0.16, 0.09), simple(f'TowelS{i}', c, rough=0.95, sheen=1.0), bevel=0.03)
    cyl('Pot', (-0.25, 2.1, 1.82), 0.06, 0.12, simple('Pot', '#C46A3C', rough=0.6))
    for i in range(6):
        leaf = sphere(f'Leaf{i}', (-0.25 + 0.05 * math.cos(i), 2.1 + 0.04 * math.sin(i), 1.95 + 0.02 * i), 0.05, simple('Leaf', '#3C8D4A', rough=0.5))
        leaf.scale = (0.5, 1.2, 0.35)
        leaf.rotation_euler = (0.4 * math.sin(i * 2), 0.5 * math.cos(i), i)
    # towel rail with a hanging towel on the right wall
    cyl('Rail', (1.66, 1.0, 1.25), 0.012, 0.7, M['chrome'], rot=(math.radians(90), 0, 0))
    tw = tex_mat('Towel', os.path.join(gfx, 'towel.png'), scale=(1.4, 1.4, 1.4), rough=0.95, proj='BOX')
    t = rbox('Towel', (1.64, 1.0, 0.98), (0.04, 0.55, 0.55), tw, bevel=0.02)
    # bathtub along the left wall (shell + rim + water)
    tub = simple('TubEnamel', '#F7F6F1', rough=0.1, coat=1.0)
    troot = _link(bpy.data.objects.new('TubRoot', None))          # pivot on the floor at the tub's far edge
    troot.location = (-1.65, 0.25, 0.0)
    rbox('TubOuter', (0.4, 0, 0.28), (0.8, 1.7, 0.56), tub, bevel=0.06, parent=troot)
    rbox('TubInner', (0.4, 0, 0.5), (0.62, 1.52, 0.2), simple('TubInside', '#E9EEF2', rough=0.08, coat=1.0), bevel=0.05, parent=troot)
    rbox('TubWater', (0.4, 0, 0.47), (0.6, 1.5, 0.02), M['water'], bevel=0.01, parent=troot)
    cyl('TubTap', (0.1, 0.7, 0.75), 0.02, 0.22, M['chrome'], rot=(0, math.radians(90), 0), parent=troot)
    tface = {'eyes': [], 'brows': [], 'mouth': None}
    for s_ in (-1, 1):                                         # face on the tub's side (faces +X, into the room)
        e = sphere(f'TubEye{s_}', (0.805, 0.22 * s_, 0.36), 0.075, M['eye'], parent=troot)
        e.scale = (0.5, 1, 0.01)
        pu = sphere(f'TubPupil{s_}', (0.84, 0.22 * s_ - 0.02, 0.35), 0.032, M['pupil'], parent=troot)
        pu.scale = (0.6, 1, 0.01)
        tface.setdefault('pupils', []).append(pu)
        bpv = _link(bpy.data.objects.new(f'TubBrowPivot{s_}', None))
        bpv.parent = troot
        bpv.location = (0.82, 0.22 * s_, 0.47)
        br = rbox(f'TubBrow{s_}', (0, 0, 0), (0.02, 0.16, 0.03), M['brow'], bevel=0.01, parent=bpv)
        br.scale = (1, 1, 0.01)
        tface['eyes'].append(e)
        tface['brows'].append((bpv, br))
    mo = sphere('TubMouth', (0.81, 0.0, 0.17), 0.09, M['dark'], parent=troot)
    mo.scale = (0.3, 1.6, 0.02)
    tface['mouth'] = mo
    M['tub_root'] = troot
    M['tub_face'] = tface
    M['door'] = door_h
    # shower curtain rod + curtain (waves gently)
    cyl('CurtainRod', (-0.85, 0.25, 2.2), 0.012, 1.8, M['chrome'], rot=(math.radians(90), 0, 0))
    for i in range(5):                                   # hanging robe hooks + robe instead of a curtain
        pass
    # bath mat
    rbox('BathMat', (-0.6, 0.35, 0.01), (0.6, 0.4, 0.015), simple('Mat', '#3E7CB1', rough=1.0, sheen=1.0), bevel=0.01)
    # window on the right wall: emissive sky + sun shaft
    rbox('Window', (1.69, 0.2, 1.9), (0.02, 0.7, 0.6), simple('WindowSky', '#CFE6FF', emission=('#CFE6FF', 6.0)), bevel=0)
    rbox('WindowFrame', (1.68, 0.2, 1.9), (0.03, 0.78, 0.68), simple('Frame', '#FFFFFF', rough=0.5), bevel=0.01)
    # ---------- lights: warm overhead key, sun through the window, cool rim, bounce fill, ceiling lamp glow
    RS.area_light('KeyOverhead', (0.0, 0.6, 2.6), (0, 0.8, 0.0), 260 if not boss else 120, size=1.0, color=(1.0, 0.86, 0.68))
    if window_sun:
        sun = bpy.data.lights.new('KeySun', 'SUN')
        sun.energy = 3.0 if not boss else 1.0
        sun.angle = math.radians(3)
        sun.color = (1.0, 0.92, 0.8)
        so = _link(bpy.data.objects.new('KeySun', sun))
        so.rotation_euler = (math.radians(55), math.radians(-35), math.radians(-60))
    RS.area_light('Rim', (-1.0, 2.0, 1.9), (0, 0.3, 1.0), 120 if not boss else 500, size=0.8,
                  color=(0.75, 0.85, 1.0) if not boss else (0.4, 0.6, 1.0))
    RS.area_light('Bounce', (0.4, -2.4, 0.4), (0, 0.6, 1.0), 120, size=2.5, color=(1.0, 0.9, 0.8))
    cyl('CeilLamp', (0.0, 0.6, 2.66), 0.22, 0.05, simple('LampGlow', '#FFF1D6', emission=('#FFE7C2', 8.0)))
    eevee = sc.eevee
    for attr, val in (('use_shadows', True), ('shadow_ray_count', 1), ('shadow_step_count', 6), ('use_gtao', True),
                      ('gtao_distance', 0.4)):
        if hasattr(eevee, attr):
            setattr(eevee, attr, val)
    return M

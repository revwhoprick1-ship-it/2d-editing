"""Low-level geometry helpers shared by character, prop and environment builders."""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix


def smoothstep(e0, e1, x):
    if e0 == e1:
        return 1.0 if x >= e1 else 0.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def gauss(d2, sigma):
    return math.exp(-d2 / (2.0 * sigma * sigma))


def lerp(a, b, t):
    return a + (b - a) * t


def obj_from_bm(name, bm, materials=(), collection=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    for m in materials:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def quad_sphere(bm, cuts):
    """Spherified cube: even quad distribution, no poles."""
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        x, y, z = v.co
        sx = x * math.sqrt(max(0.0, 1 - y * y / 2 - z * z / 2 + y * y * z * z / 3))
        sy = y * math.sqrt(max(0.0, 1 - z * z / 2 - x * x / 2 + z * z * x * x / 3))
        sz = z * math.sqrt(max(0.0, 1 - x * x / 2 - y * y / 2 + x * x * y * y / 3))
        v.co = Vector((sx, sy, sz))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    return bm


def frame_from_tangent(t, up_hint=Vector((0, 0, 1))):
    t = t.normalized()
    if abs(t.dot(up_hint)) > 0.95:
        up_hint = Vector((0, 1, 0))
    n = (up_hint - t * up_hint.dot(t)).normalized()
    b = t.cross(n).normalized()
    return t, n, b


def tube_along(bm, points, radii, segs=10, normals=None, flat=None, cap_start=True, cap_end=True,
               uv_layer=None, tip_point=False):
    """Build a tube along a polyline.

    radii: list of (rw, rh) per point (width along binormal, height along normal).
    normals: optional list of preferred 'normal' vectors per point (e.g. away from head).
    Returns list of rings (lists of BMVerts).
    """
    rings = []
    n_pts = len(points)
    total = 0.0
    lens = [0.0]
    for i in range(1, n_pts):
        total += (points[i] - points[i - 1]).length
        lens.append(total)
    for i, p in enumerate(points):
        if i == 0:
            t = points[1] - points[0]
        elif i == n_pts - 1:
            t = points[-1] - points[-2]
        else:
            t = points[i + 1] - points[i - 1]
        hint = normals[i] if normals else Vector((0, 0, 1))
        t, nrm, bi = frame_from_tangent(t, hint)
        rw, rh = radii[i]
        ring = []
        if tip_point and i == n_pts - 1:
            ring = [bm.verts.new(p)] * segs
        else:
            for s in range(segs):
                a = 2 * math.pi * s / segs
                off = bi * (math.cos(a) * rw) + nrm * (math.sin(a) * rh)
                ring.append(bm.verts.new(p + off))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    faces = []
    for i in range(n_pts - 1):
        r0, r1 = rings[i], rings[i + 1]
        for s in range(segs):
            a, b = r0[s], r0[(s + 1) % segs]
            c, d = r1[(s + 1) % segs], r1[s]
            vs = [a, b, c, d]
            uniq = []
            for v in vs:
                if v not in uniq:
                    uniq.append(v)
            if len(uniq) >= 3:
                try:
                    f = bm.faces.new(uniq)
                    faces.append((f, i, s))
                except ValueError:
                    pass
    if uv_layer is not None:
        for f, i, s in faces:
            for loop in f.loops:
                v = loop.vert
                # find ring index / seg index for this vert
                u = lens[i] / total if total else 0
                loop[uv_layer].uv = (u, s / segs)
        # refine per-vertex u by ring membership
        ring_of = {}
        for ri, ring in enumerate(rings):
            for si, v in enumerate(ring):
                ring_of[v] = (ri, si)
        for f, i, s in faces:
            for loop in f.loops:
                ri, si = ring_of.get(loop.vert, (i, s))
                loop[uv_layer].uv = (lens[ri] / total if total else 0, si / segs)
    if cap_start and not (tip_point and n_pts == 1):
        try:
            bm.faces.new(list(reversed(rings[0])))
        except ValueError:
            pass
    if cap_end and not tip_point:
        try:
            bm.faces.new(rings[-1])
        except ValueError:
            pass
    return rings


def add_subsurf(ob, levels=1, render_levels=2):
    m = ob.modifiers.new('Subsurf', 'SUBSURF')
    m.levels = levels
    m.render_levels = render_levels
    return m


def apply_modifiers(ob):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def skin_mesh(name, verts, edges, radii, root=0, collection=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, edges, [])
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.modifiers.new('Skin', 'SKIN')
    for i, d in enumerate(me.skin_vertices[0].data):
        d.radius = radii[i]
        d.use_root = (i == root)
    apply_modifiers(ob)
    return ob


def mirror_object_x(src, name):
    """Duplicate an object mirrored across X (geometry), keeping normals correct."""
    me = src.data.copy()
    me.name = name
    bm = bmesh.new()
    bm.from_mesh(me)
    for v in bm.verts:
        v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    for c in src.users_collection:
        c.objects.link(ob)
    ob.location = src.location.copy()
    ob.location.x = -ob.location.x
    ob.rotation_euler = src.rotation_euler.copy()
    ob.rotation_euler.y = -ob.rotation_euler.y
    ob.rotation_euler.z = -ob.rotation_euler.z
    ob.scale = src.scale.copy()
    return ob


def set_color_attr(ob, name, values_per_vertex):
    """Store a scalar per vertex in a FLOAT_COLOR point attribute (readable by
    the Attribute shader node 'Fac')."""
    me = ob.data
    if name in me.color_attributes:
        me.color_attributes.remove(me.color_attributes[name])
    ca = me.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    for i, val in enumerate(values_per_vertex):
        ca.data[i].color = (val, val, val, 1.0)
    return ca

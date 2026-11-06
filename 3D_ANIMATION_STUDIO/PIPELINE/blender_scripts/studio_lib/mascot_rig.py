"""Armature, skin weights, facial shape keys and constraints for the mascot.

Bone naming: <part>.L / <part>.R.  Every deform bone has its local Z axis
pointing to the character's front (or back-of-hand for fingers) so scripted
rotations are predictable:
    local X rotation  -> bend / nod / pitch / finger curl
    local Y rotation  -> twist / head turn (bone axis)
    local Z rotation  -> side bend / arm raise in the frontal plane
"""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix

from . import mascot_config as C
from . import mascot_build as MB
from .geo import smoothstep, gauss, lerp

HC = Vector(C.HEAD_CENTER)
MZ = C.MOUTH_Z
MHW = C.MOUTH_HALF_WIDTH
FRONT = Vector((0, -1, 0))
UP = Vector((0, 0, 1))


# =====================================================================================
#  ARMATURE
# =====================================================================================
def bone_specs():
    """name -> (head, tail, parent, connected, roll_vector, deform)"""
    S = {}
    sh, el, wr = Vector(C.SHOULDER), Vector(C.ELBOW), Vector(C.WRIST)
    hip, knee, ank = Vector(C.HIP), Vector(C.KNEE), Vector(C.ANKLE)
    nb, nt = Vector(C.NECK_BASE), Vector(C.NECK_TOP)
    f, t, pn = MB.hand_frame()
    S['root'] = (Vector((0, 0, 0)), Vector((0, 0.3, 0)), None, False, UP, False)
    S['hips'] = (Vector((0, 0, 0.60)), Vector((0, 0, 0.70)), 'root', False, FRONT, True)
    S['spine'] = (Vector((0, 0, 0.70)), Vector((0, 0.004, 0.82)), 'hips', True, FRONT, True)
    S['chest'] = (Vector((0, 0.004, 0.82)), Vector((0, 0.006, 0.97)), 'spine', True, FRONT, True)
    S['neck'] = (nb, nt, 'chest', False, FRONT, True)
    S['head'] = (nt, nt + Vector((0, 0, 0.26)), 'neck', True, FRONT, True)
    S['jaw'] = (HC + Vector((0, 0.010, -0.022)), HC + Vector((0, -0.095, -0.115)), 'head', False, UP * -1, True)
    S['eye_target'] = (HC + Vector((0, -0.55, 0.004)), HC + Vector((0, -0.55, 0.05)), 'head', False, FRONT, False)
    for side, tag in ((1, 'L'), (-1, 'R')):
        m = Vector((side, 1, 1))

        def M(v):
            return Vector((v.x * side, v.y, v.z))
        ec = MB.eye_center(side)
        S[f'eye.{tag}'] = (ec, ec + Vector((0, -0.03, 0)), 'head', False, UP, True)
        S[f'lid_up.{tag}'] = (ec, ec + Vector((0, -0.03, 0)), 'head', False, UP, True)
        S[f'lid_lo.{tag}'] = (ec, ec + Vector((0, -0.03, 0)), 'head', False, UP, True)
        brow = MB_brow_points(side)
        for nm, idx in (('brow_in', 1), ('brow_mid', 5), ('brow_out', 10)):
            p = brow[idx]
            S[f'{nm}.{tag}'] = (p, p + Vector((0, -0.018, 0)), 'head', False, UP, True)
        S[f'shoulder.{tag}'] = (M(Vector((0.028, 0.010, 0.95))), M(sh), 'chest', False, FRONT, True)
        S[f'upperarm.{tag}'] = (M(sh), M(el), f'shoulder.{tag}', True, FRONT, True)
        S[f'forearm.{tag}'] = (M(el), M(wr), f'upperarm.{tag}', True, FRONT, True)
        S[f'hand.{tag}'] = (M(wr), M(wr + f * 0.078), f'forearm.{tag}', True, M(-pn), True)
        for fname in ('thumb', 'index', 'middle', 'ring', 'pinky'):
            pts = MB.finger_chain(fname)
            par = f'hand.{tag}'
            for i in range(3):
                bn = f'{fname}_0{i + 1}.{tag}'
                S[bn] = (M(pts[i]), M(pts[i + 1]), par, i > 0, M(-pn) if fname != 'thumb' else M(-pn), True)
                par = bn
        S[f'thigh.{tag}'] = (M(hip), M(knee), 'hips', False, FRONT, True)
        S[f'shin.{tag}'] = (M(knee), M(ank), f'thigh.{tag}', True, FRONT, True)
        ball = Vector((ank.x, -0.095, 0.022))
        toe = Vector((ank.x, -0.168, 0.020))
        S[f'foot_ik.{tag}'] = (M(ank), M(ank + Vector((0, -0.10, 0))), 'root', False, UP, False)
        S[f'foot.{tag}'] = (M(ank), M(ball), f'foot_ik.{tag}', False, UP, True)
        S[f'toe.{tag}'] = (M(ball), M(toe), f'foot.{tag}', True, UP, True)
        S[f'knee_pole.{tag}'] = (M(Vector((knee.x, -0.55, knee.z))), M(Vector((knee.x, -0.62, knee.z))), 'root', False, UP, False)
        S[f'hand_ik.{tag}'] = (M(wr), M(wr + f * 0.078), 'root', False, M(-pn), False)
        S[f'elbow_pole.{tag}'] = (M(Vector((el.x + 0.05, 0.45, el.z))), M(Vector((el.x + 0.05, 0.52, el.z))), 'root', False, UP, False)
    return S


def MB_brow_points(side):
    """Recompute the brow centre-line used by build_brows (world space)."""
    out = []
    N = 12
    for i in range(N):
        tt = i / (N - 1)
        x = lerp(0.016, 0.082, tt)
        z = 0.050 + 0.0075 * math.sin(math.pi * tt ** 0.85) - 0.006 * tt
        n = Vector((x / C.HEAD_RADII[0], -0.9, z / C.HEAD_RADII[2]))
        sp = MB.head_point(n)
        for _ in range(6):
            n.x += (x - sp.x) / C.HEAD_RADII[0]
            n.z += (z - sp.z) / C.HEAD_RADII[2]
            sp = MB.head_point(n)
        nn = sp.normalized()
        p = sp + nn * 0.0035
        out.append(HC + Vector((p.x * side, p.y, p.z)))
    return out


def build_armature(collection):
    arm = bpy.data.armatures.new('MSC_RigData')
    arm.display_type = 'STICK'
    rig = bpy.data.objects.new('MSC_Rig', arm)
    collection.objects.link(rig)
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.selected_objects:
        o.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    specs = bone_specs()
    eb = arm.edit_bones
    for name, (h, tl, par, con, rollv, deform) in specs.items():
        b = eb.new(name)
        b.head, b.tail = h, tl
        b.use_deform = deform
    for name, (h, tl, par, con, rollv, deform) in specs.items():
        b = eb[name]
        if par:
            b.parent = eb[par]
            b.use_connect = con and (eb[par].tail - b.head).length < 1e-4
        b.align_roll(rollv)
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'
    # ---- constraints
    for tag in ('L', 'R'):
        ik = rig.pose.bones[f'shin.{tag}'].constraints.new('IK')
        ik.target, ik.subtarget = rig, f'foot_ik.{tag}'
        ik.pole_target, ik.pole_subtarget = rig, f'knee_pole.{tag}'
        ik.chain_count = 2
        ika = rig.pose.bones[f'forearm.{tag}'].constraints.new('IK')
        ika.name = 'ArmIK'
        ika.target, ika.subtarget = rig, f'hand_ik.{tag}'
        ika.pole_target, ika.pole_subtarget = rig, f'elbow_pole.{tag}'
        ika.chain_count = 2
        ika.influence = 0.0
        cr = rig.pose.bones[f'hand.{tag}'].constraints.new('COPY_ROTATION')
        cr.name = 'ArmIK_rot'
        cr.target, cr.subtarget = rig, f'hand_ik.{tag}'
        cr.influence = 0.0
        dt = rig.pose.bones[f'eye.{tag}'].constraints.new('DAMPED_TRACK')
        dt.target, dt.subtarget = rig, 'eye_target'
        dt.track_axis = 'TRACK_Y'
    _solve_pole_angles(rig)
    rig['msc_rig_version'] = 1
    return rig


def _solve_pole_angles(rig):
    """Pick IK pole angles that keep the rest pose unchanged."""
    dg = bpy.context.evaluated_depsgraph_get()
    for tag in ('L', 'R'):
        for bone, cname in ((f'shin.{tag}', 'IK'), (f'forearm.{tag}', 'ArmIK')):
            pb = rig.pose.bones[bone]
            c = pb.constraints[cname]
            infl = c.influence
            c.influence = 1.0
            rest_head = (rig.matrix_world @ rig.data.bones[bone].head_local)
            best = None
            for ang in range(-180, 181, 5):
                c.pole_angle = math.radians(ang)
                dg.update()
                bpy.context.view_layer.update()
                h = rig.matrix_world @ pb.head
                err = (h - rest_head).length
                if best is None or err < best[0]:
                    best = (err, ang)
            c.pole_angle = math.radians(best[1])
            c.influence = infl
    bpy.context.view_layer.update()


# =====================================================================================
#  SKIN WEIGHTS
# =====================================================================================
def _seg_dist(p, a, b):
    ab = b - a
    tt = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * tt)).length


def weight_by_segments(ob, rig, bones_sigma, power=2.0):
    bones = rig.data.bones
    segs = {n: (bones[n].head_local.copy(), bones[n].tail_local.copy(), s) for n, s in bones_sigma.items()}
    groups = {n: (ob.vertex_groups.get(n) or ob.vertex_groups.new(name=n)) for n in bones_sigma}
    for v in ob.data.vertices:
        p = v.co
        ws = {}
        for n, (a, b, s) in segs.items():
            d = _seg_dist(p, a, b)
            ws[n] = math.exp(-((d / s) ** power))
        tot = sum(ws.values())
        if tot < 1e-12:
            n = min(segs, key=lambda k: _seg_dist(p, segs[k][0], segs[k][1]))
            ws = {n: 1.0}
            tot = 1.0
        for n, w in ws.items():
            w /= tot
            if w > 0.01:
                groups[n].add([v.index], w, 'REPLACE')


def _sleeve_weights(shirt, rig):
    """Sleeves follow the upper arm: blend from shoulder/chest at the armhole to
    100% upperarm at the hem, so lowering or raising the arm never shears the sleeve."""
    sh, el = Vector(C.SHOULDER), Vector(C.ELBOW)
    ad = (el - sh).normalized()
    groups = {n: shirt.vertex_groups.get(n) for n in ('chest', 'shoulder.L', 'shoulder.R', 'upperarm.L', 'upperarm.R',
                                                       'spine', 'hips', 'neck')}
    for v in shirt.data.vertices:
        p = v.co
        side = 1 if p.x > 0 else -1
        s_sh = Vector((sh.x * side, sh.y, sh.z))
        s_ad = Vector((ad.x * side, ad.y, ad.z))
        rel = p - s_sh
        along = rel.dot(s_ad)
        radial = (rel - s_ad * along).length
        if abs(p.x) < 0.11 or radial > 0.095 or along < -0.06:
            continue
        t = smoothstep(-0.05, 0.05, along)
        tag = 'L' if side > 0 else 'R'
        for n, g in groups.items():
            if g is not None:
                g.remove([v.index])
        groups[f'upperarm.{tag}'].add([v.index], 0.35 + 0.65 * t, 'REPLACE')
        if t < 1.0:
            groups[f'shoulder.{tag}'].add([v.index], 0.35 * (1 - t), 'REPLACE')
            groups['chest'].add([v.index], 0.30 * (1 - t), 'REPLACE')


def assign_single(ob, bone):
    g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    g.add([v.index for v in ob.data.vertices], 1.0, 'REPLACE')


def add_armature_mod(ob, rig, preserve_volume=False):
    m = ob.modifiers.new('Armature', 'ARMATURE')
    m.object = rig
    m.use_deform_preserve_volume = preserve_volume
    # armature must evaluate first (before solidify/subsurf)
    idx = list(ob.modifiers).index(m)
    if idx != 0:
        ob.modifiers.move(idx, 0)
    return m


def parent_to_bone(ob, rig, bone):
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    pb = rig.pose.bones[bone]
    bm = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    ob.matrix_parent_inverse = bm.inverted()
    ob.matrix_world = mw


def join_into(target, others):
    bpy.context.view_layer.objects.active = target
    for o in bpy.context.selected_objects:
        o.select_set(False)
    target.select_set(True)
    for o in others:
        o.select_set(True)
    bpy.ops.object.join()
    return target


# =====================================================================================
#  FACIAL SHAPE KEYS
# =====================================================================================
SHAPE_KEYS = ['smile.L', 'smile.R', 'frown.L', 'frown.R', 'wide', 'pucker', 'funnel', 'upper_lip_up',
              'lower_lip_down', 'lips_press', 'lip_tuck', 'cheek_puff', 'cheek_raise.L', 'cheek_raise.R',
              'sneer.L', 'sneer.R', 'mouth_left', 'mouth_right']


def build_shape_keys(head):
    me = head.data
    lipside = list(head['lipside'])
    if not me.shape_keys:
        head.shape_key_add(name='Basis', from_mix=False)
    rest = [v.co.copy() for v in me.vertices]

    def corner(p, sx):
        return gauss((p.x - sx * MHW) ** 2 + (p.z - MZ) ** 2 * 1.3, 0.013)

    def cheek(p, sx):
        return gauss((p.x - sx * 0.058) ** 2 + (p.z + 0.036) ** 2, 0.020)

    def lipw(p):
        return gauss(p.x ** 2 / 1.7 + (p.z - MZ) ** 2 * 2.2, 0.016)

    def disp(name, i, p, side):
        fr = smoothstep(-0.04, -0.09, p.y)
        d = Vector((0, 0, 0))
        if name.startswith('smile.'):
            sx = 1 if name.endswith('L') else -1
            d = Vector((0.005 * sx, 0.005, 0.0135)) * corner(p, sx) + Vector((0.002 * sx, -0.003, 0.006)) * cheek(p, sx)
        elif name.startswith('frown.'):
            sx = 1 if name.endswith('L') else -1
            d = Vector((0.0015 * sx, 0.001, -0.0085)) * corner(p, sx)
        elif name == 'wide':
            d = Vector((0.010, 0.003, 0)) * corner(p, 1) + Vector((-0.010, 0.003, 0)) * corner(p, -1)
        elif name == 'pucker':
            w = lipw(p)
            d = Vector((-p.x * 0.48, -0.008, -(p.z - MZ) * 0.15)) * w
        elif name == 'funnel':
            w = lipw(p)
            s = side if side else (1 if p.z > MZ else -1)
            d = Vector((-p.x * 0.30, -0.005, 0.0045 * s)) * w
        elif name == 'upper_lip_up':
            s = side if side else (1 if p.z > MZ else -1)
            if s > 0:
                d = Vector((0, -0.001, 0.0058)) * gauss(p.x ** 2 / 1.5 + (p.z - (MZ + 0.004)) ** 2, 0.011)
        elif name == 'lower_lip_down':
            s = side if side else (1 if p.z > MZ else -1)
            if s < 0:
                d = Vector((0, -0.002, -0.0062)) * gauss(p.x ** 2 / 1.5 + (p.z - (MZ - 0.006)) ** 2, 0.011)
        elif name == 'lips_press':
            w = lipw(p)
            d = Vector((0, 0.0028, -(p.z - MZ) * 0.35)) * w
        elif name == 'lip_tuck':
            s = side if side else (1 if p.z > MZ else -1)
            if s < 0:
                d = Vector((0, 0.0065, 0.0045)) * gauss(p.x ** 2 / 1.5 + (p.z - (MZ - 0.006)) ** 2, 0.010)
        elif name == 'cheek_puff':
            for sx in (1, -1):
                d += Vector((0.008 * sx, -0.006, 0)) * gauss((p.x - sx * 0.055) ** 2 + (p.z + 0.048) ** 2, 0.022)
        elif name.startswith('cheek_raise.'):
            sx = 1 if name.endswith('L') else -1
            d = Vector((0, -0.0015, 0.0055)) * cheek(p, sx)
        elif name.startswith('sneer.'):
            sx = 1 if name.endswith('L') else -1
            s = side if side else (1 if p.z > MZ else -1)
            d = Vector((0, -0.001, 0.0035)) * gauss((p.x - sx * 0.016) ** 2 + (p.z + 0.032) ** 2, 0.009)
            if s > 0:
                d += Vector((0, -0.0005, 0.005)) * gauss((p.x - sx * 0.018) ** 2 + (p.z - MZ) ** 2 * 2, 0.012)
        elif name in ('mouth_left', 'mouth_right'):
            sx = 1 if name == 'mouth_left' else -1
            d = Vector((0.008 * sx, 0, 0)) * lipw(p)
        return d * fr

    for name in SHAPE_KEYS:
        sk = head.shape_key_add(name=name, from_mix=False)
        sk.slider_min, sk.slider_max = -0.5, 1.5
        sk.value = 0.0
        for i, co in enumerate(rest):
            p = co - HC
            sk.data[i].co = co + disp(name, i, p, lipside[i])
    return head


# =====================================================================================
#  ASSEMBLY
# =====================================================================================
def rig_mascot(parts, collection):
    rig = build_armature(collection)
    H = parts['head']
    # --- head: head + jaw weights
    lipside = list(H['lipside'])
    gh = H.vertex_groups.new(name='head')
    gj = H.vertex_groups.new(name='jaw')
    for i, v in enumerate(H.data.vertices):
        p = v.co - HC
        s = lipside[i]
        if s != 0:
            jw = 1.0 if s < 0 else 0.0
        else:
            below = smoothstep(MZ + 0.002, MZ - 0.014, p.z)
            front = smoothstep(0.045, -0.025, p.y)
            jw = below * front
            # keep the lower back of the head/neck junction on the head
            jw *= 1.0 - smoothstep(-0.10, -0.14, p.z) * smoothstep(-0.02, 0.04, p.y)
        if jw > 0:
            gj.add([i], jw, 'REPLACE')
        if jw < 1:
            gh.add([i], 1 - jw, 'REPLACE')
    build_shape_keys(H)
    add_armature_mod(H, rig)
    # --- neck
    weight_by_segments(parts['neck'], rig, {'chest': 0.05, 'neck': 0.035, 'head': 0.03})
    add_armature_mod(parts['neck'], rig)
    # --- brows
    for tag in ('L', 'R'):
        b = parts[f'brow_{tag}']
        weight_by_segments(b, rig, {f'brow_in.{tag}': 0.010, f'brow_mid.{tag}': 0.011, f'brow_out.{tag}': 0.012})
        add_armature_mod(b, rig)
    # --- rigid head parts
    for key in ('hair', 'scalp', 'ear_L', 'ear_R', 'MSC_TeethUpper'):
        parent_to_bone(parts[key], rig, 'head')
    for key in ('MSC_TeethLower', 'MSC_Tongue'):
        parent_to_bone(parts[key], rig, 'jaw')
    for tag in ('L', 'R'):
        parent_to_bone(parts[f'eye_{tag}'], rig, f'eye.{tag}')
        parent_to_bone(parts[f'lid_up_{tag}'], rig, f'lid_up.{tag}')
        parent_to_bone(parts[f'lash_{tag}'], rig, f'lid_up.{tag}')
        parent_to_bone(parts[f'lid_lo_{tag}'], rig, f'lid_lo.{tag}')
    # --- arms (nails joined in)
    for tag in ('L', 'R'):
        a = join_into(parts[f'arm_{tag}'], [parts[f'nails_{tag}']])
        bs = {f'shoulder.{tag}': 0.045, f'upperarm.{tag}': 0.032, f'forearm.{tag}': 0.030, f'hand.{tag}': 0.016}
        for fn in ('thumb', 'index', 'middle', 'ring', 'pinky'):
            for i in range(3):
                bs[f'{fn}_0{i + 1}.{tag}'] = 0.0085
        weight_by_segments(a, rig, bs, power=2.5)
        add_armature_mod(a, rig, preserve_volume=True)
    # --- shirt
    weight_by_segments(parts['shirt'], rig, {
        'hips': 0.09, 'spine': 0.09, 'chest': 0.10, 'shoulder.L': 0.045, 'shoulder.R': 0.045,
        'upperarm.L': 0.038, 'upperarm.R': 0.038, 'neck': 0.02}, power=2.0)
    _sleeve_weights(parts['shirt'], rig)
    add_armature_mod(parts['shirt'], rig, preserve_volume=True)
    # --- jeans
    weight_by_segments(parts['jeans'], rig, {'hips': 0.075, 'thigh.L': 0.055, 'thigh.R': 0.055,
                                             'shin.L': 0.05, 'shin.R': 0.05, 'spine': 0.05}, power=2.2)
    add_armature_mod(parts['jeans'], rig, preserve_volume=True)
    # --- shoes (laces joined)
    for tag in ('L', 'R'):
        s = join_into(parts[f'shoe_{tag}'], [parts[f'laces_{tag}']])
        weight_by_segments(s, rig, {f'foot.{tag}': 0.05, f'toe.{tag}': 0.035}, power=3.0)
        add_armature_mod(s, rig)
        sk = parts[f'sock_{tag}']
        weight_by_segments(sk, rig, {f'foot.{tag}': 0.05, f'toe.{tag}': 0.035}, power=3.0)
        add_armature_mod(sk, rig)
    # tidy names: everything belongs to the rig hierarchy for easy linking
    for ob in collection.objects:
        if ob is not rig and ob.parent is None:
            ob.parent = rig
    return rig

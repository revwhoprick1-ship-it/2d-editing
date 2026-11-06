"""High-level animation API for the mascot rig.

Sign conventions were measured on the built rig (see DOCUMENTATION/RIG_GUIDE.md):
  jaw +X opens | head +X nods down, +Y turns to character's left, +Z tilts to his right
  spine/chest +X bends forward, +Y twists left | upperarm.L +Z raises sideways, +X swings forward
  forearm +X bends elbow | hand -X flexes wrist (palm side) | finger -X curls
  lid_up +X opens wider, -48 closes | lid_lo +X raises (squint) | lid rotY.L + raises outer corner
  brow bones: location Z (metres) raises | eye_target location (x, up, 0) in head space
For .R bones Y and Z rotations are mirrored automatically by this API.
"""
import json
import math
import os
import bpy
from mathutils import Vector

R = math.radians
HERE = os.path.dirname(os.path.abspath(__file__))
EXPR_JSON = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'CHARACTER', 'expressions', 'expressions.json'))

FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')
SHAPES = ['smile.L', 'smile.R', 'frown.L', 'frown.R', 'wide', 'pucker', 'funnel', 'upper_lip_up',
          'lower_lip_down', 'lips_press', 'lip_tuck', 'cheek_puff', 'cheek_raise.L', 'cheek_raise.R',
          'sneer.L', 'sneer.R', 'mouth_left', 'mouth_right']

# ------------------------------------------------------------------------------------ expressions
EXPRESSIONS = {
    'neutral':   dict(),
    'happy':     dict(brow=(1.5, 2.0, 1.0), lid_up=-4, lid_lo=16, jaw=7,
                      keys={'smile.L': 0.9, 'smile.R': 0.9, 'cheek_raise.L': 0.7, 'cheek_raise.R': 0.7, 'wide': 0.15}),
    'surprised': dict(brow=(5.0, 6.0, 4.0), lid_up=9, lid_lo=-6, jaw=13,
                      keys={'funnel': 0.5, 'upper_lip_up': 0.2}, head=(0, -4, 0)),
    'shocked':   dict(brow=(6.5, 7.5, 5.0), lid_up=13, lid_lo=-9, jaw=22,
                      keys={'wide': 0.35, 'funnel': 0.3, 'lower_lip_down': 0.6, 'upper_lip_up': 0.4}, head=(0, -7, 0)),
    'confused':  dict(brow_L=(5.0, 6.0, 3.0), brow_R=(-2.5, -1.5, 0.0), lid_up_L=4, lid_up_R=-12, lid_lo=4, jaw=2,
                      keys={'mouth_left': 0.6, 'frown.R': 0.45, 'pucker': 0.2}, head=(0, 0, 8)),
    'curious':   dict(brow_L=(3.0, 4.0, 3.0), brow_R=(1.0, 1.5, 1.0), lid_up=4, jaw=2,
                      keys={'pucker': 0.25, 'smile.L': 0.25}, head=(0, 5, -6)),
    'angry':     dict(brow=(-4.5, -2.0, 1.5), lid_up=-13, lid_tilt=12, lid_lo=12, jaw=3,
                      keys={'frown.L': 0.7, 'frown.R': 0.7, 'sneer.L': 0.3, 'sneer.R': 0.3, 'lips_press': 0.4,
                            'upper_lip_up': 0.2}, head=(0, 7, 0)),
    'scared':    dict(brow=(6.5, 3.0, -1.0), lid_up=11, lid_lo=-4, lid_tilt=-8, jaw=10,
                      keys={'wide': 0.7, 'frown.L': 0.5, 'frown.R': 0.5, 'lower_lip_down': 0.4}, head=(0, -4, 0)),
    'sad':       dict(brow=(4.5, 1.0, -2.0), lid_up=-16, lid_tilt=-10, lid_lo=4, jaw=0,
                      keys={'frown.L': 0.8, 'frown.R': 0.8, 'pucker': 0.15, 'lips_press': 0.2},
                      head=(0, 10, 0), eyes=(0.0, -0.08)),
    'disgusted': dict(brow_L=(-3.0, -2.0, -1.0), brow_R=(-1.5, -0.5, 0.0), lid_up=-10, lid_lo=16, jaw=2,
                      keys={'sneer.L': 1.2, 'upper_lip_up': 1.0, 'frown.R': 0.6, 'frown.L': 0.3, 'mouth_left': 0.4},
                      head=(-8, -4, 0)),
    'excited':   dict(brow=(5.0, 6.0, 4.0), lid_up=6, lid_lo=8, jaw=16,
                      keys={'smile.L': 1.0, 'smile.R': 1.0, 'wide': 0.4, 'cheek_raise.L': 0.6, 'cheek_raise.R': 0.6,
                            'upper_lip_up': 0.3}),
    'thinking':  dict(brow_L=(3.0, 2.0, 1.0), brow_R=(-2.0, -2.0, -1.0), lid_up=-6, lid_lo=6,
                      keys={'mouth_right': 0.6, 'pucker': 0.3, 'lips_press': 0.3},
                      head=(8, 0, 6), eyes=(0.24, 0.20)),
    'laughing':  dict(brow=(2.0, 3.0, 2.0), lid_up=-30, lid_lo=30, jaw=18,
                      keys={'smile.L': 1.0, 'smile.R': 1.0, 'wide': 0.5, 'cheek_raise.L': 1.0, 'cheek_raise.R': 1.0,
                            'upper_lip_up': 0.4}, head=(0, -10, 0)),
}

# ------------------------------------------------------------------------------------ visemes
VISEMES = {
    'rest': (0, {}),
    'AA': (14, {'wide': 0.1}),
    'EE': (6, {'wide': 0.6, 'smile.L': 0.2, 'smile.R': 0.2}),
    'OO': (5, {'pucker': 0.9, 'funnel': 0.3}),
    'OH': (10, {'funnel': 0.7, 'pucker': 0.4}),
    'ER': (5, {'pucker': 0.4, 'funnel': 0.3}),
    'MBP': (0, {'lips_press': 0.8}),
    'FV': (3, {'lip_tuck': 0.9, 'upper_lip_up': 0.2}),
    'TH': (5, {'wide': 0.2, 'upper_lip_up': 0.1}),
    'SS': (3, {'wide': 0.4, 'upper_lip_up': 0.2}),
    'SH': (4, {'pucker': 0.45, 'funnel': 0.35, 'upper_lip_up': 0.15}),
    'KK': (7, {'wide': 0.15}),
}
PHONEME_TO_VISEME = {}
for chars, vis in (('aɑæʌɐIWɒ', 'AA'), ('ieɛɪAj', 'EE'), ('uʊw', 'OO'), ('oɔOQY', 'OH'), ('ɜɚəᵊɹrɝ', 'ER'),
                   ('mbp', 'MBP'), ('fv', 'FV'), ('θðtdnlɾʔ', 'TH'), ('szʒ', 'SS'), ('ʃʧʤ', 'SH'),
                   ('kgŋhx', 'KK')):
    for ch in chars:
        PHONEME_TO_VISEME[ch] = vis


def export_expression_library(path=EXPR_JSON):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump({'expressions': EXPRESSIONS, 'visemes': VISEMES,
                   'units': {'brow': 'millimetres up (inner, mid, outer)', 'lid_up': 'deg (+ opens wider)',
                             'lid_lo': 'deg (+ raises lower lid)', 'lid_tilt': 'deg (+ outer corner up)',
                             'jaw': 'deg open', 'head': 'deg (turn, nod, tilt)', 'eyes': 'gaze offset (x, up)'}},
                  f, indent=1, ensure_ascii=False)
    return path


class Mascot:
    """Wraps the rig + head shape keys.  All setters change the current pose;
    call key(frame) to keyframe every controlled channel."""

    def __init__(self, rig=None, head=None):
        self.rig = rig or bpy.data.objects['MSC_Rig']
        self.head = head or bpy.data.objects['MSC_Head']
        self.pb = self.rig.pose.bones
        self.kb = self.head.data.shape_keys.key_blocks
        self.touched = set()

    # ---------------------------------------------------------------- primitives
    def rot(self, bone, x=0.0, y=0.0, z=0.0, add=False):
        pb = self.pb[bone]
        v = Vector((R(x), R(y), R(z)))
        if bone.endswith('.R'):
            v.y, v.z = -v.y, -v.z
        pb.rotation_euler = (Vector(pb.rotation_euler) + v) if add else v
        self.touched.add((bone, 'rotation_euler'))

    def loc(self, bone, x=0.0, y=0.0, z=0.0):
        self.pb[bone].location = (x, y, z)
        self.touched.add((bone, 'location'))

    def shape(self, name, v):
        self.kb[name].value = v
        self.touched.add(('#' + name, 'value'))

    def reset(self, keep_root=True):
        for pb in self.pb:
            if keep_root and pb.name == 'root':
                continue
            if pb.name.startswith(('foot_ik', 'hand_ik')) and keep_root:
                pass
            pb.rotation_euler = (0, 0, 0)
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
            self.touched.add((pb.name, 'rotation_euler'))
            self.touched.add((pb.name, 'location'))
        for n in SHAPES:
            self.shape(n, 0.0)
        for t in ('L', 'R'):
            self.arm_ik(t, 0.0)

    def key(self, frame, interp=None):
        for bone, prop in sorted(self.touched):
            if prop == '#ik':
                side = bone[-1]
                self.pb[bone].constraints['ArmIK'].keyframe_insert('influence', frame=frame)
                self.pb[f'hand.{side}'].constraints['ArmIK_rot'].keyframe_insert('influence', frame=frame)
                continue
            if bone.startswith('#'):
                kb = self.kb[bone[1:]]
                kb.keyframe_insert('value', frame=frame)
            else:
                self.pb[bone].keyframe_insert(prop, frame=frame)
        if interp:
            set_interp(self.rig, interp, frame)
            if self.head.data.shape_keys.animation_data:
                set_interp(self.head.data.shape_keys, interp, frame)

    def key_all(self, frame):
        for pb in self.pb:
            self.touched.add((pb.name, 'rotation_euler'))
            self.touched.add((pb.name, 'location'))
        for n in SHAPES:
            self.touched.add(('#' + n, 'value'))
        self.key(frame)

    # ---------------------------------------------------------------- body helpers
    def head_pose(self, turn=0, nod=0, tilt=0):
        self.rot('neck', nod * 0.35, turn * 0.35, tilt * 0.35)
        self.rot('head', nod * 0.65, turn * 0.65, tilt * 0.65)

    def spine_pose(self, bend=0, twist=0, side=0):
        self.rot('spine', bend * 0.45, twist * 0.4, side * 0.45)
        self.rot('chest', bend * 0.55, twist * 0.6, side * 0.55)

    def arm(self, side, raise_=0, forward=0, twist=0, elbow=0, wrist=0, wrist_side=0, shrug=0):
        """raise_: degrees from the A-pose rest (+ = up/out). elbow: + bends."""
        t = side
        self.rot(f'shoulder.{t}', 0, 0, shrug)
        self.rot(f'upperarm.{t}', forward, twist, raise_)
        self.rot(f'forearm.{t}', elbow, 0, 0)
        self.rot(f'hand.{t}', -wrist, 0, wrist_side)

    def hand(self, side, curl=0.0, spread=0.0, thumb=0.0, point=False, fist=False):
        """curl 0..1 (relaxed rest = 0). point: index straight, others curled."""
        for fn in FINGERS:
            c = curl
            if point:
                c = -0.15 if fn == 'index' else 0.9
            if fist:
                c = 1.0
            if fn == 'thumb':
                c = thumb if not (point or fist) else 0.6
                self.rot(f'{fn}_01.{side}', -25 * c, 0, 0)
                self.rot(f'{fn}_02.{side}', -30 * c, 0, 0)
                self.rot(f'{fn}_03.{side}', -35 * c, 0, 0)
                continue
            sp = {'index': 1, 'middle': 0.3, 'ring': -0.4, 'pinky': -1}[fn] * spread * 8
            self.rot(f'{fn}_01.{side}', -70 * c, 0, sp)
            self.rot(f'{fn}_02.{side}', -85 * c, 0, 0)
            self.rot(f'{fn}_03.{side}', -60 * c, 0, 0)

    def arm_ik(self, side, influence, target=None):
        pb = self.pb[f'forearm.{side}']
        pb.constraints['ArmIK'].influence = influence
        self.pb[f'hand.{side}'].constraints['ArmIK_rot'].influence = influence
        self.touched.add((f'forearm.{side}', '#ik'))
        if target is not None:
            self.loc(f'hand_ik.{side}', *target)

    def eyes(self, x=0.0, up=0.0):
        self.loc('eye_target', x, up, 0)

    def lids(self, up=0.0, lo=0.0, tilt=0.0, up_L=None, up_R=None):
        self.rot('lid_up.L', up if up_L is None else up_L, tilt, 0)
        self.rot('lid_up.R', up if up_R is None else up_R, tilt, 0)
        self.rot('lid_lo.L', lo, 0, 0)
        self.rot('lid_lo.R', lo, 0, 0)

    def brows(self, L=(0, 0, 0), Rr=None):
        Rr = L if Rr is None else Rr
        for vals, t in ((L, 'L'), (Rr, 'R')):
            for v, nm in zip(vals, ('brow_in', 'brow_mid', 'brow_out')):
                self.loc(f'{nm}.{t}', 0, 0, v / 1000.0)

    def jaw(self, deg):
        self.rot('jaw', deg, 0, 0)

    # ---------------------------------------------------------------- face
    def expression(self, name, w=1.0, keep_body=False):
        e = EXPRESSIONS[name]
        b = e.get('brow', (0, 0, 0))
        bl = e.get('brow_L', b)
        br = e.get('brow_R', b)
        self.brows(tuple(v * w for v in bl), tuple(v * w for v in br))
        up = e.get('lid_up', 0)
        self.lids(up * w, e.get('lid_lo', 0) * w, e.get('lid_tilt', 0) * w,
                  up_L=e.get('lid_up_L', up) * w, up_R=e.get('lid_up_R', up) * w)
        self.jaw(e.get('jaw', 0) * w)
        for n in SHAPES:
            self.shape(n, e.get('keys', {}).get(n, 0.0) * w)
        if not keep_body:
            hd = e.get('head', (0, 0, 0))
            self.head_pose(*[v * w for v in hd])
        ex = e.get('eyes', (0, 0))
        self.eyes(ex[0] * w, ex[1] * w)

    def viseme(self, name, w=1.0, base_jaw=0.0, base_keys=None):
        jaw, keys = VISEMES[name]
        self.jaw(base_jaw + jaw * w)
        base_keys = base_keys or {}
        for n in ('wide', 'pucker', 'funnel', 'lips_press', 'lip_tuck', 'upper_lip_up', 'lower_lip_down'):
            self.shape(n, base_keys.get(n, 0.0) + keys.get(n, 0.0) * w)


def set_interp(idblock, interp, frame):
    ad = idblock.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        for kp in fc.keyframe_points:
            if abs(kp.co.x - frame) < 0.01:
                kp.interpolation = interp


def _fcurves(action):
    """Iterate F-curves of a (possibly layered/slotted) action."""
    if hasattr(action, 'fcurves') and action.fcurves is not None:
        try:
            for fc in action.fcurves:
                yield fc
            return
        except Exception:
            pass
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    yield fc


# ====================================================================================
#  REUSABLE MOTION GENERATORS
# ====================================================================================
def blink(m, frame, hold=1, base_up=0.0, base_lo=0.0):
    """5-frame blink with ease: open -> closed -> open."""
    for f, up, lo in ((frame - 1, base_up, base_lo), (frame + 1, -48, 8), (frame + 1 + hold, -48, 8),
                      (frame + 4 + hold, base_up + 2, base_lo), (frame + 6 + hold, base_up, base_lo)):
        m.lids(up, lo)
        m.touched = {t for t in m.touched if t[0].startswith('lid_')}
        m.key(f)


def breathe(m, start, end, period=90, amp=1.0):
    f = start
    while f <= end:
        ph = (f - start) / period * 2 * math.pi
        m.touched = set()
        m.rot('chest', 1.2 * amp * math.sin(ph), 0, 0)
        m.rot('shoulder.L', 0, 0, 1.0 * amp * math.sin(ph))
        m.rot('shoulder.R', 0, 0, 1.0 * amp * math.sin(ph))
        m.key(f)
        f += period // 4


def walk(m, start, end, speed=1.1, cycle=30, start_pos=(0, 0), heading_deg=0.0, run=False, fps=30):
    """Baked foot-planted walk/run.  The root travels along -Y rotated by heading.
    Feet stay planted during stance (no sliding)."""
    stride = speed * (cycle / fps) / 2.0
    lift = 0.06 if not run else 0.12
    bob = 0.018 if not run else 0.035
    lean = 3 if not run else 12
    arm_sw = 18 if not run else 35
    head = R(heading_deg)
    for f in range(start, end + 1):
        t = (f - start) / fps
        dist = speed * t
        m.touched = set()
        # root travel
        m.loc('root', start_pos[0] + math.sin(head) * dist, start_pos[1] - math.cos(head) * dist, 0)
        m.rot('root', 0, 0, heading_deg)
        ph = ((f - start) % cycle) / cycle
        for side, off in (('L', 0.0), ('R', 0.5)):
            p = (ph + off) % 1.0
            if p < 0.5:   # stance: foot moves back linearly (world-fixed)
                u = p / 0.5
                y = lerp(-stride / 2, stride / 2, u)
                z = 0.0
                roll = 0
            else:         # swing: foot moves forward with an arc
                u = (p - 0.5) / 0.5
                y = lerp(stride / 2, -stride / 2, smooth(u))
                z = lift * math.sin(math.pi * u)
                roll = -15 * math.sin(math.pi * u) + (10 * smooth(max(0, u - 0.7) / 0.3))
            m.loc(f'foot_ik.{side}', 0, -y, z)  # foot_ik local Y points forward
            m.rot(f'foot_ik.{side}', roll, 0, 0)
        hip_ph = ph * 4 * math.pi
        m.loc('hips', 0, -bob * 0.5 + bob * 0.5 * math.cos(hip_ph) - (0.03 if run else 0.0), 0)
        m.rot('hips', 0, 8 * math.sin(ph * 2 * math.pi), 2.5 * math.sin(ph * 2 * math.pi))
        m.spine_pose(bend=lean, twist=-10 * math.sin(ph * 2 * math.pi))
        swing = arm_sw * math.sin(ph * 2 * math.pi)
        m.arm('L', raise_=-12, forward=-swing, elbow=(15 if not run else 80) + 8 * max(0, -math.sin(ph * 2 * math.pi)))
        m.arm('R', raise_=-12, forward=swing, elbow=(15 if not run else 80) + 8 * max(0, math.sin(ph * 2 * math.pi)))
        m.head_pose(nod=-lean * 0.5, turn=4 * math.sin(ph * 2 * math.pi))
        m.key(f)
    return start_pos[0] + math.sin(head) * speed * (end - start) / fps, start_pos[1] - math.cos(head) * speed * (end - start) / fps


def jump(m, start, height=0.35, fps=30):
    """Anticipation -> launch -> hang -> land -> recover (about 32 frames)."""
    seq = [  # frame offset, hips_down, root_z, arms_raise, arms_forward, spine_bend, knee_tuck
        (0, 0.0, 0.0, 0, 0, 0, 0),
        (6, -0.10, 0.0, -25, -35, 18, 0),      # crouch / anticipation
        (9, 0.02, 0.05, 70, 40, -6, 0),       # push off
        (14, 0.0, height, 95, 30, -4, 0.10),   # apex
        (19, 0.0, height * 0.55, 60, 25, 4, 0.06),
        (22, -0.02, 0.0, 30, 10, 10, 0),      # contact
        (25, -0.11, 0.0, -10, 20, 22, 0),     # absorb
        (32, 0.0, 0.0, 0, 0, 0, 0),           # recover
    ]
    for off, hd, rz, ar, af, sb, tuck in seq:
        m.touched = set()
        f = start + off
        rx, ry, _ = m.pb['root'].location
        m.loc('root', rx, ry, rz)
        m.loc('hips', 0, hd, 0)
        for s in ('L', 'R'):
            m.loc(f'foot_ik.{s}', 0, 0, tuck)
            m.arm(s, raise_=ar * 0.6, forward=af, elbow=20)
        m.spine_pose(bend=sb)
        m.key(f)


def sit_down(m, start, dur=24, seat_height=0.42):
    drop = 0.60 - seat_height
    for off, k in ((0, 0.0), (int(dur * 0.35), 0.25), (int(dur * 0.8), 0.95), (dur, 1.0)):
        m.touched = set()
        m.loc('hips', 0, -drop * k, -0.16 * k)   # down and back
        m.spine_pose(bend=25 * math.sin(math.pi * min(1, k * 1.1)) + 5 * k)
        for s in ('L', 'R'):
            m.arm(s, raise_=-10, forward=25 * k, elbow=35 * k)
        m.key(start + off)


def wave(m, side, start, cycles=3, period=10):
    m.touched = set()
    m.arm(side, raise_=110, forward=10, elbow=60, twist=-30)
    m.hand(side, curl=0.0, spread=0.6)
    m.key(start)
    for i in range(cycles * 2 + 1):
        m.touched = set()
        a = 22 if i % 2 == 0 else -18
        m.arm(side, raise_=110, forward=10, elbow=60 + a * 0.5, twist=-30, wrist_side=a)
        m.key(start + 6 + i * period // 2)


def point_at(m, side, start, raise_=60, forward=60, hold=20):
    m.touched = set()
    m.arm(side, raise_=raise_ * 0.6, forward=forward * 0.8, elbow=30)
    m.hand(side, curl=0.3)
    m.key(start)
    m.touched = set()
    m.arm(side, raise_=raise_, forward=forward, elbow=6)
    m.hand(side, point=True)
    m.key(start + 6)
    m.touched = set()
    m.arm(side, raise_=raise_ - 3, forward=forward - 2, elbow=8)
    m.key(start + 6 + hold)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ====================================================================================
#  LIP SYNC
# ====================================================================================
def lipsync(m, words, fps=30, offset_frames=0, intensity=1.0, base_jaw=0.0, base_keys=None):
    """words: list of {"phonemes": str, "start": s, "end": s}.  Keys a viseme at
    every phoneme centre and relaxes to rest in gaps longer than 0.18 s."""
    events = []
    for w in words:
        ph = [c for c in w.get('phonemes', '') if c in PHONEME_TO_VISEME]
        if not ph or w.get('start') is None:
            continue
        dur = max(0.04, w['end'] - w['start'])
        for i, c in enumerate(ph):
            tc = w['start'] + dur * (i + 0.5) / len(ph)
            events.append((tc, PHONEME_TO_VISEME[c]))
    events.sort()
    last_f = None
    prev_t = None
    for tc, vis in events:
        f = int(round(tc * fps)) + offset_frames
        if prev_t is not None and tc - prev_t > 0.18:
            m.touched = set()
            m.viseme('rest', base_jaw=base_jaw, base_keys=base_keys)
            m.key(int(round((prev_t + 0.09) * fps)) + offset_frames)
            m.touched = set()
            m.viseme('rest', base_jaw=base_jaw, base_keys=base_keys)
            m.key(f - 2)
        if last_f is not None and f <= last_f:
            continue
        m.touched = set()
        w = intensity * (0.85 if vis in ('TH', 'KK', 'SS') else 1.0)
        m.viseme(vis, w, base_jaw=base_jaw, base_keys=base_keys)
        m.key(f)
        last_f = f
        prev_t = tc
    if prev_t is not None:
        m.touched = set()
        m.viseme('rest', base_jaw=base_jaw, base_keys=base_keys)
        m.key(int(round((prev_t + 0.12) * fps)) + offset_frames)


# ====================================================================================
#  STORE A REUSABLE ACTION LIBRARY INSIDE mascot_rig.blend
# ====================================================================================
def _new_action(rig, name):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    if not rig.animation_data:
        rig.animation_data_create()
    rig.animation_data.action = act
    return act


def store_library_actions(rig):
    export_expression_library()
    m = Mascot(rig)
    builders = {
        'ANIM_walk_cycle': lambda: walk(m, 1, 31, speed=1.1, cycle=30),
        'ANIM_run_cycle': lambda: walk(m, 1, 21, speed=2.6, cycle=20, run=True),
        'ANIM_jump': lambda: jump(m, 1),
        'ANIM_sit': lambda: sit_down(m, 1),
        'ANIM_wave_L': lambda: wave(m, 'L', 1),
        'ANIM_point_R': lambda: point_at(m, 'R', 1),
        'ANIM_idle_breath': lambda: breathe(m, 1, 91),
    }
    for name, fn in builders.items():
        m.reset()
        _new_action(rig, name)
        m.touched = set()
        m.key_all(1)
        fn()
        try:
            rig.animation_data.action.asset_mark()
        except Exception:
            pass
    for name in EXPRESSIONS:
        m.reset()
        act = _new_action(rig, 'EXP_' + name)
        m.expression(name)
        m.touched = {t for t in m.touched if not t[0].startswith('#')}
        m.key(1)
        act['shape_keys'] = json.dumps(EXPRESSIONS[name].get('keys', {}))
    rig.animation_data.action = None
    m.reset(keep_root=False)
    if m.head.data.shape_keys.animation_data:
        m.head.data.shape_keys.animation_data.action = None
    for n in SHAPES:
        m.kb[n].value = 0.0

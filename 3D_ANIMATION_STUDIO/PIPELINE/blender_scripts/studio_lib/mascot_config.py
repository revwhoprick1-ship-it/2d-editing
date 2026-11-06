"""Mascot identity sheet in code.

Every dimension and color of the permanent protagonist lives here, so the
character can be re-calibrated against the uploaded reference image without
touching the modelling code.  Units: metres.  Z up.  The character faces -Y.
Character's LEFT side is +X.
"""

NAME = "Mascot"

# ---------------------------------------------------------------- colours (linear-ish sRGB hex)
COLORS = {
    "skin":        "#E2A983",   # warm tan
    "skin_blush":  "#E8907A",
    "lip":         "#C27466",
    "hair":        "#3E2314",   # medium-dark brown
    "hair_tip":    "#5E3820",
    "brow":        "#2E190E",
    "iris":        "#3A2214",   # large, dark expressive eyes
    "iris_ring":   "#1A0E08",
    "iris_light":  "#6B4228",
    "sclera":      "#F3EEE8",
    "pupil":       "#050302",
    "shirt":       "#F26A0F",   # orange T-shirt (identity colour)
    "shirt_rib":   "#D85A0A",
    "jeans":       "#1E4C9A",
    "jeans_dark":  "#163A78",
    "shoe":        "#F1F0EC",
    "shoe_accent": "#2B2F3A",
    "sole":        "#E9E4DA",
    "lace":        "#FAFAF7",
    "mouth":       "#5A1F1F",
    "teeth":       "#F4F1E8",
    "tongue":      "#C5555A",
    "nail":        "#E8B9A0",
}

# ---------------------------------------------------------------- head
HEAD_CENTER = (0.0, 0.0, 1.138)
HEAD_RADII = (0.126, 0.132, 0.143)          # half width, half depth, half height (skull)
EYE_RADIUS = 0.0335
EYE_OFFSET = (0.05, -0.098, 0.004)          # relative to head centre (left eye; mirrored)
IRIS_RATIO = 0.60                          # iris radius as fraction of the visible eye
PUPIL_RATIO = 0.27
MOUTH_Z = -0.066                            # relative to head centre
MOUTH_HALF_WIDTH = 0.034
EAR_OFFSET = (0.118, 0.006, -0.012)

# ---------------------------------------------------------------- body landmarks (absolute)
NECK_BASE = (0.0, 0.006, 0.985)
NECK_TOP = (0.0, 0.012, 1.040)
SHOULDER = (0.158, 0.012, 0.955)            # left shoulder joint
ELBOW = (0.262, 0.03, 0.775)
WRIST = (0.33, 0.0, 0.60)
HIP = (0.078, 0.0, 0.585)
KNEE = (0.082, -0.012, 0.325)
ANKLE = (0.084, 0.012, 0.085)

TORSO = {  # z, half-width, half-depth (shirt surface)
    "hem":    (0.535, 0.142, 0.102),
    "waist":  (0.66, 0.136, 0.098),
    "chest":  (0.84, 0.158, 0.108),
    "shoulders": (0.95, 0.14, 0.095),
}

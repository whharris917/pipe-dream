import numpy as np

# Window & World
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
UI_HEIGHT = 200
WORLD_SIZE = 200.0  # The "Void" dimensions

# Physics Defaults
DEFAULT_DT = 0.002
DEFAULT_GRAVITY = 0.0
DEFAULT_DAMPING = 1.0 # 1.0 = No Damping
DEFAULT_DRAW_M = 10   # Steps per frame
SKIN_DISTANCE = 0.5

# Rendering
PARTICLE_RADIUS_SCALE = 0.4  # Multiplier for Sigma
BACKGROUND_COLOR = (10, 12, 16)
GRID_COLOR = (30, 30, 40)

# Atom Types Definitions
# Format: ID: (Name, Sigma, Epsilon, Mass, Color_RGB, Is_Static)
ATOM_TYPES = {
    0: {"name": "Gas",    "sigma": 1.0, "epsilon": 1.0, "mass": 1.0,  "color": (90, 200, 255), "static": 0},
    1: {"name": "Heavy",  "sigma": 1.5, "epsilon": 2.0, "mass": 5.0,  "color": (200, 100, 200), "static": 0},
    2: {"name": "Wall",   "sigma": 1.0, "epsilon": 1.0, "mass": 1.0,  "color": (150, 150, 150), "static": 1},
    3: {"name": "Anchor", "sigma": 2.0, "epsilon": 5.0, "mass": 10.0, "color": (200, 50, 50),   "static": 1},
}

# Pre-compile lookup tables for Numba
MAX_TYPES = max(ATOM_TYPES.keys()) + 1
TYPE_SIGMA = np.ones(MAX_TYPES, dtype=np.float32)
TYPE_EPSILON = np.ones(MAX_TYPES, dtype=np.float32)
TYPE_MASS = np.ones(MAX_TYPES, dtype=np.float32)
TYPE_STATIC = np.zeros(MAX_TYPES, dtype=np.int32)
TYPE_COLOR = np.zeros((MAX_TYPES, 3), dtype=np.int32)

for tid, props in ATOM_TYPES.items():
    TYPE_SIGMA[tid] = props["sigma"]
    TYPE_EPSILON[tid] = props["epsilon"]
    TYPE_MASS[tid] = props["mass"]
    TYPE_STATIC[tid] = props["static"]
    TYPE_COLOR[tid] = props["color"]
import numpy as np

# Window & World
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
UI_HEIGHT = 200

# This is now the *Default* size. The actual size is stored in Simulation instance.
DEFAULT_WORLD_SIZE = 600.0  

# Physics Defaults
DEFAULT_DT = 0.002
DEFAULT_GRAVITY = 0.0
DEFAULT_DAMPING = 1.0 # 1.0 = No Damping
DEFAULT_DRAW_M = 10   # Steps per frame
SKIN_DISTANCE = 0.5

# Rendering
PARTICLE_RADIUS_SCALE = 0.4
BACKGROUND_COLOR = (10, 12, 16)
GRID_COLOR = (30, 30, 40)

# Single Atom Definition (Scalar Constants)
ATOM_SIGMA = 1.0
ATOM_EPSILON = 1.0
ATOM_MASS = 1.0

# Visuals
COLOR_DYNAMIC = (90, 200, 255)
COLOR_STATIC = (150, 150, 150)
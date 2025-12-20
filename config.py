import numpy as np

# Window Layout
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 930 
# UPDATED: Equal width for left and right panels to support unified UI
PANEL_LEFT_WIDTH = 350 
PANEL_RIGHT_WIDTH = 350
TOP_MENU_H = 30 # Moved from main.py

# Modes
MODE_SIM = 0
MODE_EDITOR = 1

# Tools
TOOL_BRUSH = 0
TOOL_LINE = 1
TOOL_REF = 2
TOOL_POINT = 3
TOOL_RECT = 4
TOOL_CIRCLE = 5
TOOL_SELECT = 6

# World
DEFAULT_WORLD_SIZE = 50.0

# Physics Defaults
DEFAULT_DT = 0.002
DEFAULT_GRAVITY = 0.0
DEFAULT_DAMPING = 1.0 
DEFAULT_DRAW_M = 10
DEFAULT_SKIN_DISTANCE = 0.5

# Rendering - Modern Dark Theme
PARTICLE_RADIUS_SCALE = 0.4
BACKGROUND_COLOR = (30, 30, 30)      # #1e1e1e (Editor Background)
GRID_COLOR = (50, 50, 50)            # Subtle Grid
PANEL_BG_COLOR = (37, 37, 38)        # #252526 (Side Panel Background)
PANEL_BORDER_COLOR = (60, 60, 60)    # Soft borders

# Single Atom Definition
ATOM_SIGMA = 1.0
ATOM_EPSILON = 1.0
ATOM_MASS = 1.0

# Visuals
COLOR_DYNAMIC = (86, 156, 214)       # #569cd6 (VS Blue)
COLOR_STATIC = (206, 145, 120)       # #ce9178 (VS Orange/Red)
# Screen Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Interaction Settings
SNAP_DISTANCE = 15.0       
INTERACTION_DISTANCE = 40.0 
MIN_PIPE_LENGTH = 4.0      

# Resolution
SEGMENT_LENGTH_PX = 10.0 
SEGMENT_LENGTH_M = 1.0 

# Hydraulic Geometry
PIPE_DIAMETER_M = 0.3  
PIPE_AREA_M2 = 3.14159 * (PIPE_DIAMETER_M / 2)**2

# UI Settings
TOOLBAR_HEIGHT = 60
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 40
BUTTON_MARGIN = 10

# Physics Constants
PIPE_RESISTANCE = 1.0 
VALVE_RESISTANCE = 1.0 

# PHYSICS SIMULATION SETTINGS
# ---------------------------

# High substeps + Softer compression = Smooth, stable flow.
PHYSICS_SUBSTEPS = 60 

# --- COMPRESSIBLE HYDROSTATIC MODEL ---

# How much volume can be squeezed into a pipe before it strictly refuses more?
MAX_COMPRESSION = 2.0

# Base pressure for fluid < 100% full. 
PRESSURE_SENSITIVITY = 400.0   

# The "Spring Stiffness" for fluid > 100% full.
COMPRESSION_PENALTY = 3000.0

# The weight of the fluid.
GRAVITY_SENSITIVITY = 100.0

# Speed limit for flow.
MAX_FLOW_SPEED = 100.0       

# Minimum Energy Delta required to move fluid (Friction).
FLOW_FRICTION = 0.1

# --- ATOMIC COHESION ---
# The energy cost to move into an empty node.
# High values make the fluid "sticky" and reluctant to spread into thin films.
# It forces atoms to clump together or pile up before breaking into new territory.
SURFACE_TENSION = 0.001

# Source settings
DEFAULT_SOURCE_PRESSURE = 1000.0 

# Viscosity Thresholds
VISCOSITIES = {
    'Water': 0.1,
    'Red': 0.1,   
    'Green': 0.5, 
    'Blue': 0.1   
}

# Chemistry Constants
DENSITIES = {
    'Water': 1000.0,
    'Red': 1000.0,   
    'Green': 950.0,
    'Blue': 1000.0   
}

MOLAR_MASSES = {
    'Water': 18.0,
    'Red': 40.0,   
    'Green': 30.0,
    'Blue': 20.0   
}

# WPA Color Palette
C_BACKGROUND = (30, 35, 40)     
C_GRID = (50, 55, 60)           
C_FLOOR = (45, 50, 55)          
C_HIGHLIGHT = (255, 180, 60)    
C_FLUID = (0, 255, 255)         
C_PIPE_EMPTY = (80, 80, 90)     
C_TEXT = (220, 230, 240)        
C_PREVIEW = (255, 255, 255)     

# Chemical Colors
C_FLUID_RED = (255, 80, 80)
C_FLUID_GREEN = (80, 255, 80)
C_FLUID_BLUE = (80, 80, 255)

FLUID_COLORS = {
    'Water': C_FLUID,
    'Red': C_FLUID_RED,
    'Green': C_FLUID_GREEN,
    'Blue': C_FLUID_BLUE
}

# Component Colors
C_VALVE_OPEN = (100, 255, 100)
C_VALVE_CLOSED = (255, 80, 80)
C_VALVE_HOVER = (255, 255, 200)
C_SINK = (100, 100, 100) 

# UI Colors
C_UI_BG = (20, 25, 30)          
C_BUTTON_IDLE = (60, 65, 70)
C_BUTTON_HOVER = (80, 85, 90)
C_BUTTON_ACTIVE = (255, 180, 60)
C_BUTTON_TEXT = (220, 230, 240)
# Screen Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Interaction Settings
SNAP_DISTANCE = 15.0       
INTERACTION_DISTANCE = 40.0 
MIN_PIPE_LENGTH = 4.0      

# Resolution
SEGMENT_LENGTH_PX = 20.0 
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
PIPE_RESISTANCE = 30.0 
VALVE_RESISTANCE = 30.0 

# PERFORMANCE OPTIMIZATION:
# The Implicit Solver is stable at larger time steps.
# Reduced from 40 to 10 for a 4x speedup.
PHYSICS_SUBSTEPS = 10 

# Source settings
DEFAULT_SOURCE_PRESSURE = 300.0 # kPa

# --- ADVANCED PHYSICS PARAMETERS ---

# Implicit Compressibility Solver Settings
BULK_MODULUS = 2000.0          
PRESSURE_TOLERANCE = 0.001     

# PERFORMANCE OPTIMIZATION:
# Reduced from 20 to 8. This is sufficient for visual
# convergence in a game context. Yields 2.5x speedup.
MAX_PRESSURE_ITERATIONS = 8   

PRESSURE_RAMP_START = 0.90     

# Hydrostatic Leveling (Diffusion)
HYDROSTATIC_FORCE = 300.0      

# -----------------------------------

# Viscosity Thresholds
VISCOSITIES = {
    'Water': 0.1,
    'Red': 0.9,   
    'Green': 0.5, 
    'Blue': 0.1   
}

# Chemistry Constants
DENSITIES = {
    'Water': 1000.0,
    'Red': 1050.0,   
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
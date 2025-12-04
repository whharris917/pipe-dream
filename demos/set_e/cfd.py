import pygame
import numpy as np
import matplotlib.cm as cm
import sys

# --- Configuration ---
# Grid parameters
N_POINTS = 400      # Higher resolution for sharper shockwaves
PIPE_LENGTH = 10.0  # Meters

# Physics parameters (Air)
GAMMA = 1.4         # Ratio of specific heats
R_GAS = 287.0       # Specific gas constant

# Initial conditions (Ambient state inside the pipe)
P_INITIAL = 101325.0  # 1 atm (Pa)
T_INITIAL = 300.0     # 300 K
RHO_INITIAL = P_INITIAL / (R_GAS * T_INITIAL)
U_INITIAL = 0.0

# Boundary Conditions
# Left Wall: High Pressure Source (Explosion/Reservoir)
P_LEFT = P_INITIAL * 10.0  # 10x Pressure burst
T_LEFT = 400.0             # Hotter gas
RHO_LEFT = P_LEFT / (R_GAS * T_LEFT)

# Simulation control
CFL = 0.5  # Safety factor for time step (Keep < 1.0)

# Pygame Visualization Settings
WIDTH, HEIGHT = 1200, 500
PIPE_HEIGHT = 300
PIPE_Y_OFFSET = (HEIGHT - PIPE_HEIGHT) // 2
FPS = 60
VIS_VARIABLE = 'pressure' # Default view

# --- Helper Functions ---

def get_initial_state():
    """Resets the grid to ambient conditions."""
    U = np.zeros((3, N_POINTS))
    # Fill with ambient
    U[0, :] = RHO_INITIAL
    U[1, :] = RHO_INITIAL * U_INITIAL
    # Energy = P/(gamma-1) + 0.5*rho*u^2
    U[2, :] = P_INITIAL / (GAMMA - 1) + 0.5 * RHO_INITIAL * U_INITIAL**2
    return U

def update_primitive_vars(U_state):
    """Decode conservative U -> rho, u, p"""
    rho = U_state[0, :]
    # Numerical safety floor for density
    rho[rho < 1e-9] = 1e-9 
    
    u = U_state[1, :] / rho
    E = U_state[2, :]
    
    # p = (gamma - 1) * (E - kinetic_energy)
    p = (GAMMA - 1) * (E - 0.5 * rho * u**2)
    
    # Numerical safety floor for pressure
    p[p < 1e-9] = 1e-9 
    return rho, u, p

def calculate_flux(U_state):
    """F(U) vectors for Euler equations"""
    rho, u, p = update_primitive_vars(U_state)
    
    F = np.zeros_like(U_state)
    F[0, :] = U_state[1, :]          # Mass flux: rho * u
    F[1, :] = U_state[1, :] * u + p  # Momentum flux: rho*u^2 + p
    F[2, :] = u * (U_state[2, :] + p)# Energy flux: u(E + p)
    return F

def apply_boundary_conditions(U_state):
    """
    Enforces Ghost Points.
    Index 0 is the Source Ghost.
    Index -1 is the Wall Ghost.
    """
    
    # --- LEFT BOUNDARY (Index 0): Constant Source ---
    # We force the ghost cell to maintain high pressure/density.
    U_state[0, 0] = RHO_LEFT
    # We set a small inflow velocity or 0 momentum for the ghost cell.
    # Allowing a small velocity helps "feed" the pipe.
    inflow_u = 0.0 
    U_state[1, 0] = RHO_LEFT * inflow_u
    U_state[2, 0] = P_LEFT / (GAMMA - 1) + 0.5 * RHO_LEFT * inflow_u**2

    # --- RIGHT BOUNDARY (Index -1): Reflective Wall ---
    # To simulate a closed wall at the face between -2 and -1:
    
    # 1. Density is symmetric (dRho/dx = 0)
    U_state[0, -1] = U_state[0, -2]
    
    # 2. Velocity is anti-symmetric (u_ghost = -u_inner) 
    # This creates u=0 exactly at the wall face.
    U_state[1, -1] = -U_state[1, -2]
    
    # 3. Energy/Pressure
    # Since rho is symmetric and |u| is symmetric, Energy is symmetric.
    U_state[2, -1] = U_state[2, -2]
    
    return U_state

def solve_step_mac_cormack(U_current, dt, dx):
    """
    MacCormack Predictor-Corrector Step.
    CRITICAL: Only updates indices 1 to N-2 (The fluid interior).
    0 and N-1 are handled exclusively by apply_boundary_conditions.
    """
    U_next = U_current.copy()
    
    # --- Predictor (Forward Difference) ---
    F_current = calculate_flux(U_current)
    U_predictor = U_current.copy()
    
    # Update range: [1:-1] (indices 1 to N-2)
    # Uses F[i+1] - F[i] -> F[2:] - F[1:-1]
    U_predictor[:, 1:-1] = U_current[:, 1:-1] - (dt / dx) * (F_current[:, 2:] - F_current[:, 1:-1])
    
    # Update BCs on predictor so corrector uses valid ghost data
    U_predictor = apply_boundary_conditions(U_predictor)

    # --- Corrector (Backward Difference) ---
    F_predictor = calculate_flux(U_predictor)
    
    # Update range: [1:-1]
    # Uses F_pred[i] - F_pred[i-1] -> F_pred[1:-1] - F_pred[:-2]
    U_next[:, 1:-1] = 0.5 * (U_current[:, 1:-1] + U_predictor[:, 1:-1] - 
                           (dt / dx) * (F_predictor[:, 1:-1] - F_predictor[:, :-2]))
    
    # Final BC application
    U_next = apply_boundary_conditions(U_next)
    
    return U_next

# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CFD: Compressible Flow Shock Tube")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 18)

# Colormaps
cmap_magma = cm.get_cmap('magma')
cmap_seismic = cm.get_cmap('seismic') # Good for velocity (diverging)

def get_color(value, v_min, v_max, cmap_name='magma'):
    """Map value to RGB."""
    if abs(v_max - v_min) < 1e-5: norm = 0.5
    else: norm = (value - v_min) / (v_max - v_min)
    norm = np.clip(norm, 0.0, 1.0)
    
    if cmap_name == 'seismic':
        rgba = cmap_seismic(norm)
    else:
        rgba = cmap_magma(norm)
        
    return int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255)

# --- Initialization ---
dx = PIPE_LENGTH / (N_POINTS - 1)
x_grid = np.linspace(0, PIPE_LENGTH, N_POINTS)
U = get_initial_state()

running = True
sim_time = 0.0

# --- Main Loop ---
while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p: VIS_VARIABLE = 'pressure'
            if event.key == pygame.K_v: VIS_VARIABLE = 'velocity'
            if event.key == pygame.K_d: VIS_VARIABLE = 'density'
            if event.key == pygame.K_r: # Reset Simulation
                U = get_initial_state()
                sim_time = 0.0

    # 2. Physics Logic
    rho, u, p = update_primitive_vars(U)
    
    # Adaptive Time Step (CFL Condition)
    local_sound_speed = np.sqrt(GAMMA * p / rho)
    max_wave_speed = np.max(np.abs(u) + local_sound_speed)
    if max_wave_speed < 1e-5: max_wave_speed = 1e-5
    dt = CFL * dx / max_wave_speed
    
    # Sub-step limitation (don't run too fast for rendering, but good for physics)
    # We can run multiple physics steps per frame if needed, but 1:1 is fine for this demo.
    U = solve_step_mac_cormack(U, dt, dx)
    sim_time += dt

    # 3. Visualization
    screen.fill((30, 30, 30))

    # Recalculate primitives for drawing
    rho, u, p = update_primitive_vars(U)

    # Determine ranges for visualization
    if VIS_VARIABLE == 'pressure':
        data = p
        v_min, v_max = P_INITIAL, P_LEFT * 1.5 # Fixed scale roughly
        label = "Pressure (Pa)"
        active_cmap = 'magma'
    elif VIS_VARIABLE == 'velocity':
        data = u
        # Dynamic range for velocity to see the reflection clearly
        limit = np.max(np.abs(u)) + 10.0
        v_min, v_max = -limit, limit
        label = "Velocity (m/s) - Red=Right, Blue=Left"
        active_cmap = 'seismic'
    elif VIS_VARIABLE == 'density':
        data = rho
        v_min, v_max = RHO_INITIAL, RHO_LEFT * 1.2
        label = "Density (kg/m3)"
        active_cmap = 'magma'

    # Draw strips
    # We iterate 0 to N-2 (Hiding the last ghost point creates a cleaner wall visual)
    strip_w = WIDTH / (N_POINTS - 1)
    
    for i in range(N_POINTS - 1):
        color = get_color(data[i], v_min, v_max, active_cmap)
        # +1 width to prevent black lines between strips
        pygame.draw.rect(screen, color, (i * strip_w, PIPE_Y_OFFSET, strip_w + 1, PIPE_HEIGHT))

    # UI Overlays
    # Draw Wall
    pygame.draw.line(screen, (255, 50, 50), (WIDTH-3, PIPE_Y_OFFSET), (WIDTH-3, PIPE_Y_OFFSET+PIPE_HEIGHT), 6)
    
    # Text
    ui_color = (200, 200, 200)
    screen.blit(font.render(f"Mode: {label} (Press P, V, D)", True, ui_color), (20, 20))
    screen.blit(font.render(f"Time: {sim_time*1000:.2f} ms", True, ui_color), (20, 45))
    screen.blit(font.render("Press 'R' to Reset Explosion", True, (255, 200, 50)), (20, 70))
    
    # Simple Legend Gradient
    grad_rect = pygame.Surface((200, 20))
    for x in range(200):
        val = v_min + (x/200)*(v_max-v_min)
        c = get_color(val, v_min, v_max, active_cmap)
        pygame.draw.line(grad_rect, c, (x, 0), (x, 20))
    screen.blit(grad_rect, (WIDTH - 220, 20))
    screen.blit(font.render("Low", True, ui_color), (WIDTH - 260, 20))
    screen.blit(font.render("High", True, ui_color), (WIDTH - 220 + 205, 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
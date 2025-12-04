import pygame

# --- Configuration ---
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 400
FPS = 60

# Dimensions
PIPE_X = 50
PIPE_Y = 150
PIPE_WIDTH = 1500
PIPE_HEIGHT = 150
PIPE_THICKNESS = 4

# Grid Properties
# Increased cell size slightly to ensure 60FPS with the complex gradient rendering
CELL_SIZE = 5            
NUM_CELLS = int(PIPE_WIDTH / CELL_SIZE) 

# Physics Properties
INJECTION_VELOCITY = 6.0 
FRICTION_LOSS = 0.995     # Global energy loss
SHEAR_DRAG = 0.05         # How fast the Top layer drags the Bottom layer (0.01 = Slow, 0.1 = Fast)

# Spreading Settings
DIFFUSION_RATE_PER_STEP = 0.4
DIFFUSION_STEPS_PER_FRAME = 20

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_WALL = (150, 150, 150)
COLOR_PIPE_INTERIOR = (30, 30, 30)
COLOR_GATE = (255, 50, 50) 

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Iteration 10: Vertical Shear & Horizontal Isovelocity")
clock = pygame.time.Clock()

# --- State Variables ---
h = [0.0] * NUM_CELLS
u_top = [0.0] * NUM_CELLS # Surface velocity (Fast)
u_bot = [0.0] * NUM_CELLS # Bed velocity (Slow)

gate_height = 0.0

def get_velocity_color(velocity):
    """Maps a velocity value to a color (Dark Blue -> Bright Cyan/White)"""
    # Normalize 0.0 -> INJECTION_VELOCITY to 0.0 -> 1.0
    ratio = min(max(velocity / INJECTION_VELOCITY, 0), 1.0)
    
    # Dark Blue (0, 30, 80) to Bright Cyan (180, 255, 255)
    r = int(0 + 180 * ratio)
    g = int(30 + 225 * ratio)
    b = int(80 + 175 * ratio)
    return (r, g, b)

def solve_shear_dynamics(h_arr, u_t, u_b, gate_h, friction, drag):
    """
    Updates velocities based on injection, shear (drag), and advection.
    """
    n = len(h_arr)
    
    # 1. INJECTION
    # New fluid enters at the TOP layer with high velocity.
    if gate_h > 0:
        existing_mass = h_arr[0]
        added_mass = gate_h * 0.2
        total_mass = existing_mass + added_mass
        
        # Momentum Conservation for the TOP layer mainly
        # We assume new inflow sits on top, so it heavily influences u_top
        # but has little immediate impact on u_bot
        current_top_momentum = existing_mass * u_t[0]
        added_momentum = added_mass * INJECTION_VELOCITY
        
        u_t[0] = (current_top_momentum + added_momentum) / total_mass
        h_arr[0] = total_mass

    # 2. SHEAR TRANSFER (The "Drag" effect)
    # The top layer pulls the bottom layer, and the bottom layer slows the top layer.
    for i in range(n):
        if h_arr[i] > 1:
            diff = u_t[i] - u_b[i]
            
            # Newton's law of cooling style transfer
            transfer = diff * drag
            
            u_b[i] += transfer # Bottom speeds up
            u_t[i] -= transfer # Top slows down (Newton's 3rd law)

    # 3. ADVECTION (Transport)
    # We advect mass based on the AVERAGE velocity of the column.
    next_h = list(h_arr)
    next_ut = list(u_t)
    next_ub = list(u_b)
    
    for i in range(n - 1):
        # Average velocity drives the bulk mass transport
        avg_vel = (u_t[i] + u_b[i]) / 2.0
        
        if avg_vel > 0.1 and h_arr[i] > 0.1:
            flux = h_arr[i] * avg_vel * 0.5
            if flux > h_arr[i]: flux = h_arr[i]
            
            if flux > 0:
                # Remove from current
                next_h[i] -= flux
                
                # Add to neighbor (Conservation of Momentum per layer)
                target = i + 1
                
                # Mass mixing ratio
                m_dest = next_h[target]
                m_src = flux
                m_total = m_dest + m_src
                
                # Transport Top Momentum
                p_top_dest = m_dest * next_ut[target]
                p_top_src = m_src * u_t[i]
                next_ut[target] = (p_top_dest + p_top_src) / m_total
                
                # Transport Bottom Momentum
                p_bot_dest = m_dest * next_ub[target]
                p_bot_src = m_src * u_b[i]
                next_ub[target] = (p_bot_dest + p_bot_src) / m_total
                
                next_h[target] = m_total

    # 4. FRICTION (Global Decay)
    for i in range(n):
        next_ut[i] *= friction
        next_ub[i] *= friction * 0.98 # Bottom friction is higher (wall contact)
        
        # Cleanup small values
        if next_h[i] < 0.1: next_h[i] = next_ut[i] = next_ub[i] = 0

    return next_h, next_ut, next_ub

def apply_diffusion_simple(h_arr, rate, iterations):
    temp_h = list(h_arr)
    n = len(h_arr)
    for _ in range(iterations):
        buf = list(temp_h)
        buf[0] = temp_h[0] + rate * (temp_h[1] - temp_h[0])
        buf[n-1] = temp_h[n-1] + rate * (temp_h[n-2] - temp_h[n-1])
        for i in range(1, n-1):
            buf[i] = temp_h[i] + rate * (temp_h[i-1] + temp_h[i+1] - 2*temp_h[i])
        temp_h = buf
    return temp_h

running = True
while running:
    # Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            h = [0.0] * NUM_CELLS
            u_top = [0.0] * NUM_CELLS
            u_bot = [0.0] * NUM_CELLS
            gate_height = 0

    keys = pygame.key.get_pressed()
    target_height = PIPE_HEIGHT * 0.8 if keys[pygame.K_SPACE] else 0.0
    if gate_height < target_height: gate_height += 5
    elif gate_height > target_height: gate_height -= 5

    # Physics
    h, u_top, u_bot = solve_shear_dynamics(h, u_top, u_bot, gate_height, FRICTION_LOSS, SHEAR_DRAG)
    h = apply_diffusion_simple(h, DIFFUSION_RATE_PER_STEP, DIFFUSION_STEPS_PER_FRAME)

    # Rendering
    screen.fill(COLOR_BG)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, (PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT))

    # --- Gradient Rendering Loop ---
    # To draw horizontal isovelocity lines, we split each column into vertical segments.
    SEGMENTS = 5 # Higher number = smoother vertical gradient
    
    for i in range(NUM_CELLS):
        cell_h = h[i]
        if cell_h < 1: continue
        
        # Get colors for Bottom and Top
        c_bot = get_velocity_color(u_bot[i])
        c_top = get_velocity_color(u_top[i])
        
        x = PIPE_X + (i * CELL_SIZE)
        base_y = PIPE_Y + PIPE_HEIGHT
        
        segment_h = cell_h / SEGMENTS
        
        for s in range(SEGMENTS):
            # Calculate Y position for this segment (stacking upwards)
            # s=0 is bottom, s=SEGMENTS-1 is top
            y_pos = base_y - ((s + 1) * segment_h)
            
            # Interpolate Color
            t = s / (SEGMENTS - 1) if SEGMENTS > 1 else 1.0
            r = c_bot[0] + (c_top[0] - c_bot[0]) * t
            g = c_bot[1] + (c_top[1] - c_bot[1]) * t
            b = c_bot[2] + (c_top[2] - c_bot[2]) * t
            
            # Draw segment
            # Note: We use int(segment_h + 1) to overlap slightly and avoid gaps
            pygame.draw.rect(screen, (r,g,b), (x, int(y_pos), CELL_SIZE, int(segment_h + 1)))

    # Walls & Gate
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y), (PIPE_X + PIPE_WIDTH, PIPE_Y), PIPE_THICKNESS)
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y + PIPE_HEIGHT), (PIPE_X + PIPE_WIDTH, PIPE_Y + PIPE_HEIGHT), PIPE_THICKNESS)
    pygame.draw.rect(screen, COLOR_GATE, (PIPE_X - 10, PIPE_Y, 10, PIPE_HEIGHT - gate_height))
    
    # UI
    font = pygame.font.SysFont("Arial", 18)
    label = font.render("Vertical Shear Enabled. Top = Fast (White), Bottom = Slow (Blue). Note the horizontal layers.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
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
CELL_SIZE = 2             # 2px width per cell (Good balance of speed/detail)
NUM_CELLS = int(PIPE_WIDTH / CELL_SIZE) 

# Physics Properties
INJECTION_VELOCITY = 6.0  # Speed of fluid coming out of the gate
FRICTION_LOSS = 0.99      # Velocity decay per frame (1.0 = no friction, 0.9 = sticky)

# Spreading Settings (Gravity)
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
pygame.display.set_caption("Fluid Iteration 9: Momentum Transfer & Friction")
clock = pygame.time.Clock()

# --- State Variables ---
# h: Height of fluid in cell
# u: Horizontal Velocity of fluid in cell
h = [0.0] * NUM_CELLS
u = [0.0] * NUM_CELLS

gate_height = 0.0

def hsv_to_rgb(h, s, v):
    """Simple helper for velocity coloring"""
    return pygame.Color(0).hsva_to_rgba(h, s, v, 100)[:3]

def solve_fluid_dynamics(h_arr, u_arr, gate_h, friction):
    """
    Solves Advection (Transport) and Momentum Conservation.
    """
    n = len(h_arr)
    
    # --- 1. INJECTION (Source) ---
    # The gate injects fluid into the first few cells with high velocity
    if gate_h > 0:
        # Don't just overwrite; blend momentum!
        existing_mass = h_arr[0]
        added_mass = gate_h * 0.2 # Injection rate
        
        total_mass = existing_mass + added_mass
        
        # Weighted average of momentum
        # (Existing * its_speed) + (Added * injection_speed)
        new_momentum = (existing_mass * u_arr[0]) + (added_mass * INJECTION_VELOCITY)
        
        h_arr[0] = total_mass
        u_arr[0] = new_momentum / total_mass if total_mass > 0 else 0

    # --- 2. ADVECTION (Transport Loop) ---
    # We calculate flux from Left to Right.
    # To avoid overwriting data we need for the next cell, we iterate backwards
    # or use a buffer. A buffer is safer.
    
    next_h = list(h_arr)
    next_u = list(u_arr)
    
    # Iterate through all cells
    for i in range(n - 1):
        # Calculate Flux from i to i+1
        # Flux depends on the velocity at i
        velocity = u_arr[i]
        
        if velocity > 0.1 and h_arr[i] > 0.1:
            # How much mass moves?
            # Simple Eulerian step: flux = density * velocity * dt
            # We cap flux so we don't remove more than exists (CFL condition stability)
            flux_mass = h_arr[i] * velocity * 0.5 
            
            # Clamp flux to not exceed cell contents
            if flux_mass > h_arr[i]:
                flux_mass = h_arr[i]
                
            # Perform Transfer
            if flux_mass > 0:
                # Remove from current
                next_h[i] -= flux_mass
                
                # Add to neighbor
                target_idx = i + 1
                old_target_mass = next_h[target_idx]
                old_target_u = next_u[target_idx]
                
                # MOMENTUM BLEND (The Physics You Requested!)
                # Conservation: (m1*v1 + m2*v2) / (m1+m2)
                momentum_incoming = flux_mass * velocity
                momentum_target = old_target_mass * old_target_u
                
                new_target_mass = old_target_mass + flux_mass
                new_target_velocity = (momentum_incoming + momentum_target) / new_target_mass
                
                next_h[target_idx] = new_target_mass
                next_u[target_idx] = new_target_velocity

    # --- 3. FRICTION ---
    # Apply global velocity decay
    for i in range(n):
        next_u[i] *= friction
        # Clean up noise
        if next_u[i] < 0.05: next_u[i] = 0
        if next_h[i] < 0.1: 
            next_h[i] = 0
            next_u[i] = 0

    return next_h, next_u

def apply_diffusion_simple(h_arr, rate, iterations):
    """ Only diffuses height (Gravity), ignoring velocity for simplicity """
    temp_h = list(h_arr)
    n = len(h_arr)
    for _ in range(iterations):
        buf = list(temp_h)
        # Boundaries
        buf[0] = temp_h[0] + rate * (temp_h[1] - temp_h[0])
        buf[n-1] = temp_h[n-1] + rate * (temp_h[n-2] - temp_h[n-1])
        # Interior
        for i in range(1, n-1):
            buf[i] = temp_h[i] + rate * (temp_h[i-1] + temp_h[i+1] - 2*temp_h[i])
        temp_h = buf
    return temp_h

running = True
while running:
    # 1. Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                h = [0.0] * NUM_CELLS
                u = [0.0] * NUM_CELLS
                gate_height = 0

    keys = pygame.key.get_pressed()
    
    # 2. Gate Logic
    target_height = PIPE_HEIGHT * 0.8 if keys[pygame.K_SPACE] else 0.0
    if gate_height < target_height: gate_height += 5
    elif gate_height > target_height: gate_height -= 5

    # 3. Physics Step: Advection & Momentum
    h, u = solve_fluid_dynamics(h, u, gate_height, FRICTION_LOSS)
    
    # 4. Physics Step: Diffusion (Gravity Spreading)
    h = apply_diffusion_simple(h, DIFFUSION_RATE_PER_STEP, DIFFUSION_STEPS_PER_FRAME)

    # 5. Rendering
    screen.fill(COLOR_BG)

    # Pipe Interior
    pipe_rect = pygame.Rect(PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, pipe_rect)

    # Draw Fluid Columns
    # We draw vertical lines for each cell so we can color them individually based on speed
    for i in range(NUM_CELLS):
        cell_h = h[i]
        if cell_h < 1: continue
        
        cell_u = u[i]
        
        # --- COLOR MAPPING ---
        # Map velocity to color to visualize the "Shear/Drag" effect
        # High Speed (u near INJECTION_VELOCITY) -> White/Cyan
        # Low Speed (u near 0) -> Dark Blue
        
        speed_ratio = min(cell_u / (INJECTION_VELOCITY * 0.8), 1.0)
        
        # Interpolate color manually for speed
        # Start: (0, 50, 150) Dark Blue
        # End: (200, 255, 255) Bright Cyan/White
        r = 0 + int(200 * speed_ratio)
        g = 50 + int(205 * speed_ratio)
        b = 150 + int(105 * speed_ratio)
        color = (min(r,255), min(g,255), min(b,255))
        
        x = PIPE_X + (i * CELL_SIZE)
        y = PIPE_Y + (PIPE_HEIGHT - cell_h)
        
        # Draw the column
        pygame.draw.rect(screen, color, (x, y, CELL_SIZE, cell_h))

    # Walls
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y), (PIPE_X + PIPE_WIDTH, PIPE_Y), PIPE_THICKNESS)
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y + PIPE_HEIGHT), (PIPE_X + PIPE_WIDTH, PIPE_Y + PIPE_HEIGHT), PIPE_THICKNESS)

    # Gate
    gate_rect = pygame.Rect(PIPE_X - 10, PIPE_Y, 10, PIPE_HEIGHT - gate_height)
    pygame.draw.rect(screen, COLOR_GATE, gate_rect)
    
    # UI
    font = pygame.font.SysFont("Arial", 18)
    label = font.render("Color = Velocity. WHITE = Fast, BLUE = Stationary. Watch the white wave push the blue puddle.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
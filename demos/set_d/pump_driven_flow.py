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

# Physics Properties
SLICE_WIDTH = 4          # Visual width of one data point
MAX_FLOW_SPEED = 2.0     # How many slices we can inject per frame at max opening
                         # > 1.0 means we might inject multiple slices per frame (fast flow)
                         
# The "Spreading" Settings
DIFFUSION_RATE_PER_STEP = 0.4
DIFFUSION_STEPS_PER_FRAME = 20 

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_WALL = (150, 150, 150)
COLOR_PIPE_INTERIOR = (30, 30, 30)
COLOR_FLUID = (0, 190, 255)
COLOR_GHOST = (60, 60, 60)
COLOR_GATE = (255, 50, 50) 

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Iteration 5: Flow Velocity Linked to Inlet Opening")
clock = pygame.time.Clock()

# --- State Variables ---
fluid_slices = [] 
ghost_slices = [] # For comparison (visualizes advection without diffusion)
gate_height = 0.0

# The Accumulator controls variable speed on a fixed grid
flow_accumulator = 0.0 

def apply_diffusion(slices, rate, iterations):
    """ Standard Laplacian smoothing to simulate spreading/gravity """
    current_slices = list(slices)
    if len(current_slices) < 3: return current_slices

    for _ in range(iterations):
        next_slices = list(current_slices)
        for i in range(1, len(current_slices) - 1):
            left = current_slices[i-1]
            center = current_slices[i]
            right = current_slices[i+1]
            next_slices[i] += rate * (left + right - 2 * center)
        current_slices = next_slices
    return current_slices

running = True
while running:
    # 1. Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                fluid_slices = []
                ghost_slices = []
                gate_height = 0
                flow_accumulator = 0

    keys = pygame.key.get_pressed()
    
    # 2. Logic: The Gate Control
    # Holding space opens the gate; releasing closes it
    target_height = PIPE_HEIGHT * 0.9 if keys[pygame.K_SPACE] else 0.0
    
    # Smooth gate movement
    gate_move_speed = 5
    if gate_height < target_height:
        gate_height += gate_move_speed
        if gate_height > target_height: gate_height = target_height
    elif gate_height > target_height:
        gate_height -= gate_move_speed
        if gate_height < target_height: gate_height = target_height

    # 3. Logic: Variable Speed Advection (The Pump)
    # Velocity is proportional to gate opening.
    # 0 Opening = 0 Speed. 
    # Full Opening = MAX_FLOW_SPEED.
    
    opening_ratio = gate_height / PIPE_HEIGHT
    
    # Add to the "pressure" tank
    flow_accumulator += opening_ratio * MAX_FLOW_SPEED
    
    # If the accumulator overflows, we inject fluid
    while flow_accumulator >= 1.0:
        # Inject into real fluid
        fluid_slices.append(gate_height)
        # Inject into ghost (for visual comparison)
        ghost_slices.append(gate_height)
        
        # Decrement accumulator
        flow_accumulator -= 1.0
        
    # Remove old fluid falling off the right edge
    max_len = int(PIPE_WIDTH / SLICE_WIDTH)
    if len(fluid_slices) > max_len:
        fluid_slices.pop(0)
        ghost_slices.pop(0)

    # 4. Logic: Diffusion (Always Active)
    # Even if flow_accumulator is 0 (stopped), this runs.
    # This causes the "stopped" fluid to settle into a puddle.
    fluid_slices = apply_diffusion(fluid_slices, DIFFUSION_RATE_PER_STEP, DIFFUSION_STEPS_PER_FRAME)

    # 5. Rendering
    screen.fill(COLOR_BG)

    # Draw Pipe Interior
    pipe_rect = pygame.Rect(PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, pipe_rect)

    # --- Draw Ghost (Advection Only) ---
    if len(ghost_slices) > 0:
        ghost_points = []
        ghost_points.append((PIPE_X, PIPE_Y + PIPE_HEIGHT)) 
        for i in range(len(ghost_slices)):
            # Draw from Left (Newest) to Right (Oldest)
            # Logic: i=0 is Left (Newest)
            idx = len(ghost_slices) - 1 - i
            h = ghost_slices[idx]
            x = PIPE_X + (i * SLICE_WIDTH)
            y = PIPE_Y + (PIPE_HEIGHT - h)
            ghost_points.append((x, y))
            ghost_points.append((x + SLICE_WIDTH, y))
        ghost_points.append((PIPE_X + len(ghost_slices)*SLICE_WIDTH, PIPE_Y + PIPE_HEIGHT))
        
        if len(ghost_points) > 2:
            pygame.draw.lines(screen, COLOR_GHOST, False, ghost_points, 2)

    # --- Draw Fluid (Advection + Diffusion) ---
    if len(fluid_slices) > 0:
        points = []
        points.append((PIPE_X, PIPE_Y + PIPE_HEIGHT))
        for i in range(len(fluid_slices)):
            idx = len(fluid_slices) - 1 - i
            h = fluid_slices[idx]
            x = PIPE_X + (i * SLICE_WIDTH)
            y = PIPE_Y + (PIPE_HEIGHT - h)
            points.append((x, y))
            points.append((x + SLICE_WIDTH, y))
        points.append((PIPE_X + len(fluid_slices)*SLICE_WIDTH, PIPE_Y + PIPE_HEIGHT))
        
        pygame.draw.polygon(screen, COLOR_FLUID, points)

    # Draw Pipe Walls
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y), (PIPE_X + PIPE_WIDTH, PIPE_Y), PIPE_THICKNESS)
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y + PIPE_HEIGHT), (PIPE_X + PIPE_WIDTH, PIPE_Y + PIPE_HEIGHT), PIPE_THICKNESS)

    # Draw The Gate
    gate_visual_height = gate_height
    gate_rect = pygame.Rect(PIPE_X - 10, PIPE_Y, 10, PIPE_HEIGHT - gate_visual_height)
    pygame.draw.rect(screen, COLOR_GATE, gate_rect)
    
    # UI
    font = pygame.font.SysFont("Arial", 18)
    label = font.render("Hold SPACE. Release to stop flow (Advection=0), but notice Diffusion continues.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
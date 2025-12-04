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
FLUID_SPEED = 2          # Advection speed (pixels/frame)
SLICE_WIDTH = FLUID_SPEED 
GATE_SPEED = 8           # Fast gate for creating sharp pulses

# The "Spreading" Settings
DIFFUSION_RATE_PER_STEP = 0.4  # Must be <= 0.5 to remain stable
DIFFUSION_STEPS_PER_FRAME = 20 # Run math 20x per frame to speed it up

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_WALL = (150, 150, 150)
COLOR_PIPE_INTERIOR = (30, 30, 30)
COLOR_FLUID = (0, 190, 255)
COLOR_GHOST = (60, 60, 60) # Shows the original "un-spread" shape
COLOR_GATE = (255, 50, 50) 

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Iteration 4: Fast Spreading (Sub-stepping)")
clock = pygame.time.Clock()

# --- State Variables ---
# We now keep two lists:
# 1. fluid_slices: The actual simulation (spreads out)
# 2. ghost_slices: The pure advection (keeps original shape) for comparison
fluid_slices = [] 
ghost_slices = []
gate_height = 0.0

def apply_diffusion(slices, rate, iterations):
    """
    Apply diffusion multiple times to simulate fast spreading
    without breaking the mathematical stability limit.
    """
    # Working on a temporary list
    current_slices = list(slices)
    
    if len(current_slices) < 3:
        return current_slices

    for _ in range(iterations):
        # Create a scratchpad for this iteration so updates don't bleed left-to-right
        next_slices = list(current_slices)
        
        # Iterate through interior
        for i in range(1, len(current_slices) - 1):
            left = current_slices[i-1]
            center = current_slices[i]
            right = current_slices[i+1]
            
            # The diffusion formula
            delta = rate * (left + right - 2 * center)
            next_slices[i] += delta
        
        # Update for next sub-step
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

    keys = pygame.key.get_pressed()
    
    # 2. Logic: The Gate
    target_height = PIPE_HEIGHT * 0.9 if keys[pygame.K_SPACE] else 0.0
    
    if gate_height < target_height:
        gate_height += GATE_SPEED
        if gate_height > target_height: gate_height = target_height
    elif gate_height > target_height:
        gate_height -= GATE_SPEED
        if gate_height < target_height: gate_height = target_height

    # 3. Logic: Advection (Add new fluid)
    # We append to both the real fluid and the ghost fluid
    fluid_slices.append(gate_height)
    ghost_slices.append(gate_height)
    
    # Remove old fluid that fell out the right side
    max_len = int(PIPE_WIDTH / SLICE_WIDTH)
    if len(fluid_slices) > max_len:
        fluid_slices.pop(0)
        ghost_slices.pop(0)

    # 4. Logic: Diffusion (The Fast Spread)
    # Only apply to fluid_slices, leave ghost_slices alone
    fluid_slices = apply_diffusion(fluid_slices, DIFFUSION_RATE_PER_STEP, DIFFUSION_STEPS_PER_FRAME)

    # 5. Rendering
    screen.fill(COLOR_BG)

    # Draw Pipe Interior
    pipe_rect = pygame.Rect(PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, pipe_rect)

    # --- Draw Ghost (The Rigid Shape) ---
    if len(ghost_slices) > 0:
        ghost_points = []
        ghost_points.append((PIPE_X, PIPE_Y + PIPE_HEIGHT)) # Bottom Left
        
        for i in range(len(ghost_slices)):
            idx = len(ghost_slices) - 1 - i
            h = ghost_slices[idx]
            x = PIPE_X + (i * SLICE_WIDTH)
            y = PIPE_Y + (PIPE_HEIGHT - h)
            ghost_points.append((x, y))
            ghost_points.append((x + SLICE_WIDTH, y))
            
        ghost_points.append((PIPE_X + len(ghost_slices)*SLICE_WIDTH, PIPE_Y + PIPE_HEIGHT)) # Bottom Right
        
        # Draw outlines only for ghost
        if len(ghost_points) > 2:
            pygame.draw.lines(screen, COLOR_GHOST, False, ghost_points, 2)

    # --- Draw Fluid (The Spreading Shape) ---
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
    label = font.render(f"Spreading Steps: {DIFFUSION_STEPS_PER_FRAME}x per frame. Grey line = Original Input.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
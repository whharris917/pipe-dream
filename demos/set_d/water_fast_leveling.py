import pygame

# --- Configuration ---
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 400
FPS = 60

# Dimensions
PIPE_X = 50
PIPE_Y = 150
PIPE_WIDTH = 1500  # Visual width (pixels)
PIPE_HEIGHT = 150
PIPE_THICKNESS = 4

# Physics Properties
# ZOOM OUT: Cell size is now 1 pixel. 
# This packs 4x more simulation cells into the same screen width.
CELL_SIZE = 1            
NUM_CELLS = int(PIPE_WIDTH / CELL_SIZE) # ~1500 Cells

MAX_FLOW_SPEED = 4.0     # Increased flow speed so the pump feels powerful enough for this long pipe

# Spreading Settings
DIFFUSION_RATE_PER_STEP = 0.45   
DIFFUSION_STEPS_PER_FRAME = 30   # Tuned for the larger grid size to maintain FPS

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_WALL = (150, 150, 150)
COLOR_PIPE_INTERIOR = (30, 30, 30)
COLOR_FLUID = (0, 190, 255)
COLOR_GATE = (255, 50, 50) 

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Iteration 8: 4x Longer Pipe (Zoomed Out)")
clock = pygame.time.Clock()

# --- State Variables ---
pipe_cells = [0.0] * NUM_CELLS
gate_height = 0.0
flow_accumulator = 0.0 

def apply_diffusion_optimized(cells, rate, iterations):
    """
    Optimized solver.
    """
    buf_A = list(cells)
    buf_B = [0.0] * len(cells)
    n = len(cells)
    
    for _ in range(iterations):
        source = buf_A
        target = buf_B
        
        # Boundaries
        target[0] = source[0] + rate * (source[1] - source[0]) 
        target[n-1] = source[n-1] + rate * (source[n-2] - source[n-1])

        # Interior
        for i in range(1, n - 1):
            target[i] = source[i] + rate * (source[i-1] + source[i+1] - 2*source[i])
            
        buf_A, buf_B = buf_B, buf_A
        
    return buf_A

def shift_array_right(cells, insert_val):
    cells.pop() 
    cells.insert(0, insert_val) 
    return cells

running = True
while running:
    # 1. Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                pipe_cells = [0.0] * NUM_CELLS
                gate_height = 0
                flow_accumulator = 0

    keys = pygame.key.get_pressed()
    
    # 2. Gate Logic
    target_height = PIPE_HEIGHT * 0.9 if keys[pygame.K_SPACE] else 0.0
    
    if gate_height < target_height:
        gate_height += 10
        if gate_height > target_height: gate_height = target_height
    elif gate_height > target_height:
        gate_height -= 10
        if gate_height < target_height: gate_height = target_height

    # 3. Advection (The Pump)
    opening_ratio = gate_height / PIPE_HEIGHT
    flow_accumulator += opening_ratio * MAX_FLOW_SPEED
    
    while flow_accumulator >= 1.0:
        shift_array_right(pipe_cells, gate_height)
        flow_accumulator -= 1.0

    # 4. Diffusion (The Spread)
    pipe_cells = apply_diffusion_optimized(pipe_cells, DIFFUSION_RATE_PER_STEP, DIFFUSION_STEPS_PER_FRAME)

    # 5. Rendering
    screen.fill(COLOR_BG)

    # Pipe Interior
    pipe_rect = pygame.Rect(PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, pipe_rect)

    # Draw Fluid
    points = []
    points.append((PIPE_X, PIPE_Y + PIPE_HEIGHT)) # Bottom Left
    
    # Optimization: With 1500 cells, drawing a polygon is fine, 
    # but we skip cells with 0 height to keep the point list clean.
    for i, height in enumerate(pipe_cells):
        if height < 0.5: continue
        
        x = PIPE_X + (i * CELL_SIZE)
        y = PIPE_Y + (PIPE_HEIGHT - height)
        
        # Since CELL_SIZE is 1, we just plot the top point
        points.append((x, y))
        
    points.append((PIPE_X + PIPE_WIDTH, PIPE_Y + PIPE_HEIGHT)) # Bottom Right
    
    # Only draw if we have fluid
    if len(points) > 2:
        pygame.draw.polygon(screen, COLOR_FLUID, points)

    # Walls
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y), (PIPE_X + PIPE_WIDTH, PIPE_Y), PIPE_THICKNESS)
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y + PIPE_HEIGHT), (PIPE_X + PIPE_WIDTH, PIPE_Y + PIPE_HEIGHT), PIPE_THICKNESS)

    # Gate
    gate_visual_height = gate_height
    gate_rect = pygame.Rect(PIPE_X - 10, PIPE_Y, 10, PIPE_HEIGHT - gate_visual_height)
    pygame.draw.rect(screen, COLOR_GATE, gate_rect)
    
    # UI
    font = pygame.font.SysFont("Arial", 18)
    label = font.render(f"Grid: 1500 Cells (4x Scale). Observe the wave flattening over long distances.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
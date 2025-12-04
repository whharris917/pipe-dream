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
CELL_SIZE = 4            # Width of one grid cell in pixels
NUM_CELLS = int(PIPE_WIDTH / CELL_SIZE) # Fixed grid resolution
MAX_FLOW_SPEED = 2.0     # Advection speed (cells per frame)
                         
# The "Spreading" Settings
DIFFUSION_RATE_PER_STEP = 0.25
DIFFUSION_STEPS_PER_FRAME = 15 

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_WALL = (150, 150, 150)
COLOR_PIPE_INTERIOR = (30, 30, 30)
COLOR_FLUID = (0, 190, 255)
COLOR_GATE = (255, 50, 50) 

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Iteration 6: Fixed Grid & Free Spreading")
clock = pygame.time.Clock()

# --- State Variables ---
# The Pipe is now a FIXED array of size NUM_CELLS.
# Index 0 is the Inlet (Left). Index -1 is the Outlet (Right).
pipe_cells = [0.0] * NUM_CELLS

gate_height = 0.0
flow_accumulator = 0.0 

def apply_diffusion_fixed_grid(cells, rate, iterations):
    """
    Runs diffusion over the entire fixed grid.
    This allows fluid to spread into empty cells (0.0 height).
    """
    # Use a temp buffer to store next state
    # (Using two buffers prevents directional bias)
    current_cells = list(cells)
    
    for _ in range(iterations):
        next_cells = list(current_cells)
        
        # Iterate over the whole pipe, excluding absolute edges
        # We treat index 0 (Inlet) as a "Reflective Wall" so fluid doesn't leak back out the inlet
        # We treat index -1 (Outlet) as an open cliff
        
        for i in range(0, len(current_cells) - 1):
            
            # 1. Define Neighbors
            
            # LEFT NEIGHBOR HANDLING (Inlet Wall)
            if i == 0:
                # Neumann Boundary: Treat left wall as having same height as self 
                # (Fluid presses against wall, doesn't flow out)
                left = current_cells[i] 
            else:
                left = current_cells[i-1]
                
            # RIGHT NEIGHBOR HANDLING
            right = current_cells[i+1]
            
            center = current_cells[i]
            
            # 2. Calculate Laplacian (Flow)
            # If center > right, fluid flows right.
            # If center > left, fluid flows left.
            delta = rate * (left + right - 2 * center)
            
            next_cells[i] += delta
            
        current_cells = next_cells
        
    return current_cells

def shift_array_right(cells, insert_val):
    """
    Advection: Physically shifts the entire array to the right.
    Drops the last value, inserts new value at [0].
    """
    cells.pop() # Remove last
    cells.insert(0, insert_val) # Insert at front
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
        gate_height += 5
        if gate_height > target_height: gate_height = target_height
    elif gate_height > target_height:
        gate_height -= 5
        if gate_height < target_height: gate_height = target_height

    # 3. Advection Logic (The Pump)
    opening_ratio = gate_height / PIPE_HEIGHT
    
    # Only advect (shift right) if there is flow velocity from the pump
    flow_accumulator += opening_ratio * MAX_FLOW_SPEED
    
    while flow_accumulator >= 1.0:
        # Shift everything right 1 cell
        shift_array_right(pipe_cells, gate_height)
        flow_accumulator -= 1.0

    # 4. Diffusion Logic (The Spread)
    # This runs ALWAYS, even if advection is stopped.
    pipe_cells = apply_diffusion_fixed_grid(pipe_cells, DIFFUSION_RATE_PER_STEP, DIFFUSION_STEPS_PER_FRAME)

    # 5. Rendering
    screen.fill(COLOR_BG)

    # Pipe Interior
    pipe_rect = pygame.Rect(PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, pipe_rect)

    # Draw Fluid
    # We construct a polygon from the cell heights
    points = []
    points.append((PIPE_X, PIPE_Y + PIPE_HEIGHT)) # Bottom Left
    
    # Trace top surface
    for i, height in enumerate(pipe_cells):
        if height < 0.5: height = 0 # Visual cleanup for tiny values
        
        x = PIPE_X + (i * CELL_SIZE)
        y = PIPE_Y + (PIPE_HEIGHT - height)
        points.append((x, y))
        points.append((x + CELL_SIZE, y))
        
    points.append((PIPE_X + PIPE_WIDTH, PIPE_Y + PIPE_HEIGHT)) # Bottom Right
    
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
    label = font.render("Tap SPACE. The pulse will stop moving right, but will SPREAD to fill the pipe.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
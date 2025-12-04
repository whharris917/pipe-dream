import pygame

# --- Configuration ---
SCREEN_WIDTH = 1600   # Wider screen
SCREEN_HEIGHT = 400
FPS = 60

# Dimensions
PIPE_X = 50
PIPE_Y = 150
PIPE_WIDTH = 1500     # The pipe now spans almost the whole width
PIPE_HEIGHT = 100
PIPE_THICKNESS = 4

# Fluid Properties
# Reduced speed makes the pipe effectively "longer" in terms of travel time
FLUID_SPEED = 2       
SLICE_WIDTH = FLUID_SPEED 
GATE_SPEED = 2        

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_WALL = (150, 150, 150)
COLOR_PIPE_INTERIOR = (30, 30, 30)
COLOR_FLUID = (0, 190, 255) 
COLOR_GATE = (255, 50, 50) 

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Iteration 2: Long Pipe, Open End")
clock = pygame.time.Clock()

# --- State Variables ---
# List of height values. Index 0 is the furthest right (oldest).
fluid_slices = [] 

gate_height = 0.0

running = True
while running:
    # 1. Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                fluid_slices = []
                gate_height = 0

    keys = pygame.key.get_pressed()
    
    # 2. Logic: The Gate
    target_height = PIPE_HEIGHT if keys[pygame.K_SPACE] else 0.0
    
    if gate_height < target_height:
        gate_height += GATE_SPEED
        if gate_height > target_height: gate_height = target_height
    elif gate_height > target_height:
        gate_height -= GATE_SPEED
        if gate_height < target_height: gate_height = target_height

    # 3. Logic: Fluid Movement (Open End)
    
    # We always append new fluid (even if height is 0, we append 0)
    # This pushes the existing fluid to the right.
    fluid_slices.append(gate_height)
    
    # Check if the "oldest" slice (index 0) has fallen out of the pipe
    # The total length of the fluid stream is len * SLICE_WIDTH
    if len(fluid_slices) * SLICE_WIDTH > PIPE_WIDTH:
        fluid_slices.pop(0) 

    # 4. Rendering
    screen.fill(COLOR_BG)

    # A. Draw Pipe Background
    pipe_rect = pygame.Rect(PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, pipe_rect)

    # B. Draw Fluid
    if len(fluid_slices) > 0:
        points = []
        
        # We need to construct the polygon vertices.
        # The 'head' of the stream is at the right. 
        # The 'tail' is at the inlet (PIPE_X).
        
        # Calculate where the stream ends (visually)
        # If the pipe is full, the stream ends at PIPE_X + PIPE_WIDTH
        # If not full, it ends at PIPE_X + len * width
        
        # 1. Bottom-Right of the fluid stream
        # current_len_px = len(fluid_slices) * SLICE_WIDTH
        # points.append((PIPE_X + current_len_px, PIPE_Y + PIPE_HEIGHT))
        
        # We will iterate backwards from the 'newest' (inlet) to 'oldest' (exit)
        # Newest is at index -1. Location: PIPE_X
        # Oldest is at index 0. Location: PIPE_X + (len-1)*width
        
        # Start at Bottom-Left (Inlet Floor)
        points.append((PIPE_X, PIPE_Y + PIPE_HEIGHT))
        
        # Trace Top Edge from Left (Inlet) to Right (Exit)
        # We iterate through the list in reverse order (newest to oldest)
        # so we draw from left to right
        for i in range(len(fluid_slices)):
            # slice index: len - 1 - i
            # This makes i=0 the newest slice (leftmost)
            slice_index = len(fluid_slices) - 1 - i
            height = fluid_slices[slice_index]
            
            x_pos = PIPE_X + (i * SLICE_WIDTH)
            y_pos = PIPE_Y + (PIPE_HEIGHT - height)
            
            # Top-Left of this slice
            points.append((x_pos, y_pos))
            # Top-Right of this slice
            points.append((x_pos + SLICE_WIDTH, y_pos))
            
        # End at Bottom-Right (Exit Floor)
        points.append((PIPE_X + len(fluid_slices) * SLICE_WIDTH, PIPE_Y + PIPE_HEIGHT))
        
        pygame.draw.polygon(screen, COLOR_FLUID, points)

    # C. Draw Pipe Walls
    # Top and Bottom only (Right side is open)
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y), (PIPE_X + PIPE_WIDTH, PIPE_Y), PIPE_THICKNESS)
    pygame.draw.line(screen, COLOR_PIPE_WALL, (PIPE_X, PIPE_Y + PIPE_HEIGHT), (PIPE_X + PIPE_WIDTH, PIPE_Y + PIPE_HEIGHT), PIPE_THICKNESS)

    # D. Draw The Gate
    gate_visual_height = gate_height
    gate_rect = pygame.Rect(PIPE_X - 10, PIPE_Y, 10, PIPE_HEIGHT - gate_visual_height)
    pygame.draw.rect(screen, COLOR_GATE, gate_rect)
    
    # Text Instructions
    font = pygame.font.SysFont("Arial", 18)
    label = font.render("Hold SPACE to extrude fluid. Release to close gate.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
import pygame

# --- Configuration ---
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 400
FPS = 60

# Dimensions
PIPE_X = 50
PIPE_Y = 150
PIPE_WIDTH = 1500
PIPE_HEIGHT = 150 # Made pipe taller to see the wave clearly
PIPE_THICKNESS = 4

# Physics Properties
FLUID_SPEED = 3          # Advection (Horizontal movement)
SLICE_WIDTH = FLUID_SPEED 
GATE_SPEED = 5
DIFFUSION_RATE = 0.2     # The "Spreading" factor (0.0 to 0.5). Higher = more viscous/faster spread.

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_WALL = (150, 150, 150)
COLOR_PIPE_INTERIOR = (30, 30, 30)
COLOR_FLUID = (0, 190, 255)
COLOR_GATE = (255, 50, 50) 

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Iteration 3: Conserved Area Diffusion")
clock = pygame.time.Clock()

# --- State Variables ---
# fluid_slices[0] is the RIGHT-MOST slice (oldest)
# fluid_slices[-1] is the LEFT-MOST slice (newest, at inlet)
fluid_slices = [] 
gate_height = 0.0

def apply_diffusion(slices, rate):
    """
    Apply a finite-difference diffusion step.
    This effectively solves the Heat Equation: dH/dt = k * d2H/dx2
    It smooths peaks and fills valleys, but strictly maintains the sum (Total Mass).
    """
    if len(slices) < 3:
        return slices

    # We work on a copy to do simultaneous updates (or close to it)
    new_slices = list(slices)
    
    # Iterate through the interior of the stream (skip ends for now)
    for i in range(1, len(slices) - 1):
        left = slices[i-1]
        center = slices[i]
        right = slices[i+1]
        
        # Laplacian: (Left + Right - 2*Center)
        # If center is higher than neighbors, this is negative (height flows out)
        # If center is lower, this is positive (height flows in)
        delta = rate * (left + right - 2 * center)
        
        new_slices[i] += delta

    return new_slices

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
    target_height = PIPE_HEIGHT * 0.8 if keys[pygame.K_SPACE] else 0.0
    
    if gate_height < target_height:
        gate_height += GATE_SPEED
        if gate_height > target_height: gate_height = target_height
    elif gate_height > target_height:
        gate_height -= GATE_SPEED
        if gate_height < target_height: gate_height = target_height

    # 3. Logic: Fluid Advection (Movement)
    fluid_slices.append(gate_height)
    
    # Remove old fluid
    if len(fluid_slices) * SLICE_WIDTH > PIPE_WIDTH:
        fluid_slices.pop(0)

    # 4. Logic: Fluid Diffusion (Spreading)
    # We apply this every frame to the existing buffer.
    # This transforms the "Square" pulses from the gate into "Gaussian" curves.
    fluid_slices = apply_diffusion(fluid_slices, DIFFUSION_RATE)

    # 5. Rendering
    screen.fill(COLOR_BG)

    # Draw Pipe Interior
    pipe_rect = pygame.Rect(PIPE_X, PIPE_Y, PIPE_WIDTH, PIPE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PIPE_INTERIOR, pipe_rect)

    # Draw Fluid
    if len(fluid_slices) > 0:
        points = []
        
        # Bottom-Left (Inlet Floor)
        points.append((PIPE_X, PIPE_Y + PIPE_HEIGHT))
        
        # Trace Top Edge from Left to Right
        for i in range(len(fluid_slices)):
            # slice index: len - 1 - i (Newest to Oldest)
            slice_index = len(fluid_slices) - 1 - i
            height = fluid_slices[slice_index]
            
            # Clamp height to not exceed pipe for visual cleanliness
            draw_height = min(height, PIPE_HEIGHT)
            
            x_pos = PIPE_X + (i * SLICE_WIDTH)
            y_pos = PIPE_Y + (PIPE_HEIGHT - draw_height)
            
            points.append((x_pos, y_pos))
            points.append((x_pos + SLICE_WIDTH, y_pos))
            
        # Bottom-Right (Exit Floor)
        points.append((PIPE_X + len(fluid_slices) * SLICE_WIDTH, PIPE_Y + PIPE_HEIGHT))
        
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
    label = font.render("Tap SPACE. Observe the square wave diffuse into a Gaussian curve.", True, (200, 200, 200))
    screen.blit(label, (PIPE_X, PIPE_Y - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
import numpy as np
import pygame
import random
from numba import njit

# --- Constants & Configuration ---
# Grid Dimensions (Discretized Spatial Domain)
GRID_WIDTH = 200
GRID_HEIGHT = 200
CELL_SIZE = 4       # Visual size of one grid cell in pixels

# Visualization
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
BG_COLOR = (15, 15, 25)
FLUID_COLOR = (50, 150, 255)
FPS_LIMIT = 60

# Simulation Parameters
N_PARTICLES = 10000  # Number of fluid pixels to initialize

# --- Cellular Automata Physics Engine ---

@njit(fastmath=True)
def init_grid(width, height, n_particles):
    """
    Initialize the grid with a block of fluid.
    grid 0 = Empty
    grid 1 = Fluid
    """
    grid = np.zeros((height, width), dtype=np.int8)
    
    # Spawn a random cluster or a block
    # Let's fill the top middle
    count = 0
    center_x = width // 2
    center_y = height // 4
    radius = int(np.sqrt(n_particles)) 
    
    for y in range(height):
        for x in range(width):
            if count >= n_particles:
                return grid
            
            # Simple block spawn
            if (x - center_x)**2 + (y - center_y)**2 < (radius * 0.8)**2:
                 grid[y, x] = 1
                 count += 1
                 
    # If not enough, just fill randomly in top half
    while count < n_particles:
        rx = random.randint(0, width-1)
        ry = random.randint(0, height // 2)
        if grid[ry, rx] == 0:
            grid[ry, rx] = 1
            count += 1
            
    return grid

@njit(fastmath=True)
def update_fluid(grid, width, height):
    """
    Update the grid using Cellular Automata rules for a Liquid.
    Rules are applied essentially simultaneously (using a new buffer or careful iteration).
    For 'Falling Sand' types, iterating Bottom-Up prevents particles from hanging in air
    during a single frame.
    """
    # We copy to a new grid to ensure synchronous-like behavior (optional),
    # but modifying in-place Bottom-Up is standard for this specific algorithm 
    # to allow particles to fall multiple pixels if needed (acceleration approximation),
    # or strictly 1 pixel per frame for stability. 
    # Let's do in-place Bottom-Up for speed and simplicity.
    
    # We iterate from bottom to top so that a particle moving down 
    # doesn't get processed again immediately in the same frame (teleporting).
    
    for y in range(height - 1, -1, -1):
        # Iterate x in random order or alternating order to prevent fluid 
        # from piling up on the left or right side (bias).
        # A simple way is to start from a different side each frame, 
        # or just shuffle a small offset. 
        # For Numba speed, we'll just do a standard loop but check randomized directions.
        
        for x in range(width):
            if grid[y, x] == 1: # Found a particle
                
                # RULE 1: Gravity (Move Down)
                if y + 1 < height:
                    if grid[y + 1, x] == 0:
                        grid[y + 1, x] = 1
                        grid[y, x] = 0
                        continue # Particle moved, done with it
                
                # RULE 2: Flow / Displacement (Move Diagonally Down)
                # This helps piles crumble into pyramids
                moved = False
                if y + 1 < height:
                    # Check left and right diagonals randomly
                    # (Simple pseudo-random using coordinates to decide check order)
                    if (x + y) % 2 == 0:
                        dirs = (-1, 1) # Check Left then Right
                    else:
                        dirs = (1, -1) # Check Right then Left
                        
                    for dx in dirs:
                        nx = x + dx
                        if 0 <= nx < width:
                            if grid[y + 1, nx] == 0:
                                grid[y + 1, nx] = 1
                                grid[y, x] = 0
                                moved = True
                                break
                    if moved: continue

                # RULE 3: Liquid Leveling (Move Sideways)
                # If we can't move down, we try to move sideways to flatten out.
                # This distinguishes "Water" from "Sand".
                # To make it flow fast, we allows moves only if the target is empty.
                
                # Check neighbors
                if (x + y) % 2 == 0:
                    dirs = (-1, 1)
                else:
                    dirs = (1, -1)
                    
                for dx in dirs:
                    nx = x + dx
                    if 0 <= nx < width:
                        if grid[y, nx] == 0:
                            grid[y, nx] = 1
                            grid[y, x] = 0
                            break

@njit(fastmath=True)
def render_grid_to_pixels(grid, pixels, fluid_color, bg_color):
    """
    Fast mapping of grid (int) to pixel array (int/color).
    """
    # Standard packed int color for pygame surfarray (usually ARGB or RGB)
    # R + (G << 8) + (B << 16) usually for little endian
    # Let's assume standard RGB mapping
    
    c_fluid = fluid_color[0] * 65536 + fluid_color[1] * 256 + fluid_color[2]
    c_bg = bg_color[0] * 65536 + bg_color[1] * 256 + bg_color[2]
    
    h, w = grid.shape
    for y in range(h):
        for x in range(w):
            if grid[y, x] == 1:
                pixels[x, y] = c_fluid
            else:
                pixels[x, y] = c_bg

# --- Main Simulation Class ---

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Cellular Automata Fluid: {N_PARTICLES} particles")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("monospace", 16)
        
        # Grid Init
        self.grid = init_grid(GRID_WIDTH, GRID_HEIGHT, N_PARTICLES)
        
        # Rendering Buffer
        self.surface = pygame.Surface((GRID_WIDTH, GRID_HEIGHT))
        self.pixel_array = pygame.surfarray.pixels2d(self.surface)

    def update(self):
        # Physics Update
        update_fluid(self.grid, GRID_WIDTH, GRID_HEIGHT)
        
        # Interaction (Mouse to add fluid)
        m_buttons = pygame.mouse.get_pressed()
        if m_buttons[0]: # Left Click
            mx, my = pygame.mouse.get_pos()
            gx = mx // CELL_SIZE
            gy = my // CELL_SIZE
            
            # Brush size
            r = 2
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        self.grid[ny, nx] = 1

    def draw(self):
        # Fast Render using Numba to map grid->pixels
        # We pass the underlying numpy array of the surface
        # Note: We unlock/lock if needed, but usually surfarray references are safe if not blitting simultaneously
        render_grid_to_pixels(self.grid, self.pixel_array, FLUID_COLOR, BG_COLOR)
        
        # Scale up to window size
        pygame.transform.scale(self.surface, (WINDOW_WIDTH, WINDOW_HEIGHT), self.screen)

        # UI
        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps} | Grid: {GRID_WIDTH}x{GRID_HEIGHT}", True, (200, 200, 200))
        self.screen.blit(fps_text, (10, 10))
        
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_r:
                        self.grid = init_grid(GRID_WIDTH, GRID_HEIGHT, N_PARTICLES)

            self.update()
            self.draw()
            self.clock.tick(FPS_LIMIT)

        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()
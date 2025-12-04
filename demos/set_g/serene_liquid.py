import numpy as np
import pygame
import random
from numba import njit, prange

# --- Constants & Configuration ---

# 1. Grid Dimensions (Discretized Spatial Domain)
GRID_WIDTH = 500
GRID_HEIGHT = 500
CELL_SIZE = 1       # Visual size of one grid cell

# 2. Visualization Colors
BG_COLOR = (15, 15, 25)
FLUID_COLOR = (0, 190, 255)
OBSTACLE_COLOR = (80, 80, 90) # Dark Grey for the bowl

# 3. Window Setup
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS_LIMIT = 0

# 4. Simulation Physics Parameters
N_PARTICLES = 10000  
GRAVITY = 0.25          # Standard gravity
MAX_VEL = 3.0           # Higher velocity cap to allow falling
FRICTION = 0.7          # Air resistance / Drag
OVERLAP_FORCE = 1.0     # Stronger repulsion to prevent collapse
TEMPERATURE = 0.000000000000000001      # High thermal noise to prevent freezing

# 5. Force Kernel Configuration (Lattice Potentials)
KERNEL_RADIUS = 4
FORCE_REPULSION_DIST_SQ = 2
FORCE_REPULSION_STRENGTH = 1.2
FORCE_ATTRACTION_DIST_SQ = 9
FORCE_ATTRACTION_STRENGTH = -0.02

# 6. Obstacle & Wall Interactions
WALL_REPULSION_DIST_SQ = 2
WALL_REPULSION_STRENGTH = 0.5
WALL_BOUNCE_FACTOR = -0.5       # Velocity factor on bounce (negative for reflection + damping)
FLOOR_FRICTION_FACTOR = 0.9     # Tangential friction when sliding on the floor

# 7. Bowl Geometry
BOWL_OFFSET_Y = 10      # Offset from center Y
BOWL_MARGIN = 15        # Margin from edge of screen for radius

# 8. Initialization Parameters
SPAWN_MARGIN_TOP = 5
SPAWN_HEIGHT_DIVISOR = 3
INIT_VEL_X_RANGE = 0.5  # +/- this value
INIT_VEL_Y_MIN = 0.0
INIT_VEL_Y_MAX = 1.0

# 9. Rendering Configuration
# Splatting Weights (5x5 kernel)
SPLAT_CENTER = 10.0
SPLAT_INNER_RING = 6.0
SPLAT_INNER_CORNER = 4.0
SPLAT_OUTER_RING = 2.0
SPLAT_OUTER_CORNER = 1.0

# Smoothing Configuration
# Radius 1 = 3x3 kernel, Radius 2 = 5x5 kernel, Radius 3 = 7x7 kernel, etc.
SMOOTHING_RADIUS = 2    

# Thresholding
THRESHOLD_BASE = 100.0
ROLLING_FRAMES = 5      # No averaging, show raw physics state

# 10. Optimization Constants
NOISE_POOL_SIZE = 16384
NOISE_MASK = NOISE_POOL_SIZE - 1

# --- Discrete Physics Engine ---

@njit(fastmath=True)
def get_force_lookup():
    """
    Pre-calculate a discrete force field kernel.
    """
    dim = 2 * KERNEL_RADIUS + 1
    kernel_x = np.zeros((dim, dim), dtype=np.float32)
    kernel_y = np.zeros((dim, dim), dtype=np.float32)
    
    for dy in range(-KERNEL_RADIUS, KERNEL_RADIUS + 1):
        for dx in range(-KERNEL_RADIUS, KERNEL_RADIUS + 1):
            dist_sq = dx*dx + dy*dy
            if dist_sq == 0: continue
            
            dist = np.sqrt(dist_sq)
            dir_x = dx / dist
            dir_y = dy / dist
            
            force = 0.0
            
            # Heuristic Lattice Potentials
            if dist_sq <= FORCE_REPULSION_DIST_SQ:
                force = FORCE_REPULSION_STRENGTH
            elif dist_sq <= FORCE_ATTRACTION_DIST_SQ:
                force = FORCE_ATTRACTION_STRENGTH
                
            kernel_x[dy + KERNEL_RADIUS, dx + KERNEL_RADIUS] = force * dir_x
            kernel_y[dy + KERNEL_RADIUS, dx + KERNEL_RADIUS] = force * dir_y
            
    return kernel_x, kernel_y

# Pre-compile the kernel once
KERNEL_X, KERNEL_Y = get_force_lookup()

@njit(fastmath=True)
def create_bowl_obstacles(width, height):
    """
    Create a static obstacle map representing a U-shaped bowl.
    """
    obstacles = np.zeros((height, width), dtype=np.int32)
    cx = width // 2
    cy = height // 2 - BOWL_OFFSET_Y
    radius = width // 2 - BOWL_MARGIN  

    for y in range(height):
        for x in range(width):
            if y > cy:
                obstacles[y, x] = 1
            dist_sq = (x - cx)**2 + (y - cy)**2
            if dist_sq < radius**2:
                obstacles[y, x] = 0
                
    return obstacles

@njit(fastmath=True)
def init_system(width, height, n_particles):
    """
    Initialize particle arrays.
    """
    pos_x = np.zeros(n_particles, dtype=np.int32)
    pos_y = np.zeros(n_particles, dtype=np.int32)
    vel_x = np.zeros(n_particles, dtype=np.float32)
    vel_y = np.zeros(n_particles, dtype=np.float32)
    accum_x = np.zeros(n_particles, dtype=np.float32)
    accum_y = np.zeros(n_particles, dtype=np.float32)
    
    spawn_w = width // 2
    spawn_h = height // SPAWN_HEIGHT_DIVISOR
    start_x = (width - spawn_w) // 2
    start_y = SPAWN_MARGIN_TOP 
    
    for i in range(n_particles):
        pos_x[i] = np.random.randint(start_x, start_x + spawn_w)
        pos_y[i] = np.random.randint(start_y, start_y + spawn_h)
        vel_x[i] = np.random.uniform(-INIT_VEL_X_RANGE, INIT_VEL_X_RANGE)
        vel_y[i] = np.random.uniform(INIT_VEL_Y_MIN, INIT_VEL_Y_MAX) 
                
    return pos_x, pos_y, vel_x, vel_y, accum_x, accum_y

@njit(fastmath=True)
def precompute_background(obstacles, bg_color, obs_color):
    """Create a static pixel array for background."""
    h, w = obstacles.shape
    pixels = np.zeros((w, h), dtype=np.int32)
    c_bg = bg_color[0] * 65536 + bg_color[1] * 256 + bg_color[2]
    c_obs = obs_color[0] * 65536 + obs_color[1] * 256 + obs_color[2]
    for y in range(h):
        for x in range(w):
            if obstacles[y, x] == 1:
                pixels[x, y] = c_obs
            else:
                pixels[x, y] = c_bg
    return pixels

@njit(fastmath=True, parallel=True)
def update_physics(pos_x, pos_y, vel_x, vel_y, accum_x, accum_y, head, next_particle, obstacles, width, height, noise_pool, noise_offset_x, noise_offset_y):
    """
    Discrete Particle Dynamics with Noise Pool Optimization.
    """
    n = len(pos_x)
    
    # --- 1. Build Cell Linked List ---
    head.fill(-1)
    next_particle.fill(-1)
    
    for i in range(n):
        cell_idx = pos_y[i] * width + pos_x[i]
        next_particle[i] = head[cell_idx]
        head[cell_idx] = i

    # --- 2. Calculate Forces ---
    # Using parallel loop as in the optimized versions
    for i in prange(n):
        px = pos_x[i]
        py = pos_y[i]
        
        # --- OPTIMIZATION: Static Noise Pool Lookup ---
        idx_x = (i + noise_offset_x) & NOISE_MASK
        vel_x[i] += noise_pool[idx_x]
        
        idx_y = (i + noise_offset_y) & NOISE_MASK
        vel_y[i] += noise_pool[idx_y]

        fx = 0.0
        fy = GRAVITY
        
        # Neighbor scan
        for dy in range(-KERNEL_RADIUS, KERNEL_RADIUS + 1):
            ny = py + dy
            if ny < 0 or ny >= height: continue
            
            for dx in range(-KERNEL_RADIUS, KERNEL_RADIUS + 1):
                nx = px + dx
                if nx < 0 or nx >= width: continue
                
                # Obstacle Repulsion
                if obstacles[ny, nx] == 1:
                    dist_sq = dx*dx + dy*dy
                    if dist_sq <= WALL_REPULSION_DIST_SQ:
                        fx -= dx * WALL_REPULSION_STRENGTH 
                        fy -= dy * WALL_REPULSION_STRENGTH
                
                # Particle Forces
                n_cell_idx = ny * width + nx
                j = head[n_cell_idx]
                while j != -1:
                    if i != j:
                        if dx == 0 and dy == 0:
                            # BASELINE PHYSICS: Random angle kick for exact overlap
                            rand_angle = np.random.uniform(0, 6.28)
                            fx += np.cos(rand_angle) * OVERLAP_FORCE
                            fy += np.sin(rand_angle) * OVERLAP_FORCE
                        else:
                            fx += KERNEL_X[dy + KERNEL_RADIUS, dx + KERNEL_RADIUS]
                            fy += KERNEL_Y[dy + KERNEL_RADIUS, dx + KERNEL_RADIUS]
                    j = next_particle[j]

        # --- 3. Update Velocity ---
        vel_x[i] = (vel_x[i] + fx) * FRICTION
        vel_y[i] = (vel_y[i] + fy) * FRICTION
        
        # Clamp velocity
        if vel_x[i] > MAX_VEL: vel_x[i] = MAX_VEL
        elif vel_x[i] < -MAX_VEL: vel_x[i] = -MAX_VEL
        if vel_y[i] > MAX_VEL: vel_y[i] = MAX_VEL
        elif vel_y[i] < -MAX_VEL: vel_y[i] = -MAX_VEL
        
        # --- 4. Discrete Movement with Accumulators ---
        
        # X Axis
        accum_x[i] += vel_x[i]
        steps_x = int(accum_x[i])
        accum_x[i] -= steps_x 
        
        if steps_x != 0:
            sign = 1 if steps_x > 0 else -1
            count = abs(steps_x)
            for _ in range(count):
                nx = px + sign
                if 0 <= nx < width and obstacles[py, nx] == 0:
                    px = nx
                    pos_x[i] = px
                else:
                    vel_x[i] *= WALL_BOUNCE_FACTOR
                    accum_x[i] = 0 
                    break
        
        # Y Axis
        accum_y[i] += vel_y[i]
        steps_y = int(accum_y[i])
        accum_y[i] -= steps_y 
        
        if steps_y != 0:
            sign = 1 if steps_y > 0 else -1
            count = abs(steps_y)
            for _ in range(count):
                ny = py + sign
                if 0 <= ny < height and obstacles[ny, px] == 0:
                    py = ny
                    pos_y[i] = py
                else:
                    vel_y[i] *= WALL_BOUNCE_FACTOR
                    accum_y[i] = 0 
                    vel_x[i] *= FLOOR_FRICTION_FACTOR 
                    break

@njit(fastmath=True, parallel=True)
def render_fluid_density(pixels, pos_x, pos_y, raw_grid, density_history, frame_idx, static_bg, width, height, fluid_color, bg_color):
    """
    Renders the simulation as a smooth fluid surface by calculating a density field.
    Visual Layer is detached from Physics Layer (particles).
    UPDATED: 
    1. Accumulate raw splats into raw_grid.
    2. Spatially smooth raw_grid (Variable Radius) and store in density_history[frame].
    3. Temporally average density_history across ROLLING_FRAMES.
    4. Threshold.
    """
    # 1. Reset Raw Grid
    raw_grid[:] = 0.0
    
    # 2. Accumulate Density (5x5 Splatting) into Raw Grid
    # Creates broader blobs with weighted centers.
    for i in range(len(pos_x)):
        px = pos_x[i]
        py = pos_y[i]
        
        # Check bounds (padding 2 for 5x5)
        if 2 < px < width-3 and 2 < py < height-3:
            # Core (High weight)
            raw_grid[px, py] += SPLAT_CENTER
            
            # Inner Ring
            raw_grid[px+1, py] += SPLAT_INNER_RING
            raw_grid[px-1, py] += SPLAT_INNER_RING
            raw_grid[px, py+1] += SPLAT_INNER_RING
            raw_grid[px, py-1] += SPLAT_INNER_RING
            
            raw_grid[px+1, py+1] += SPLAT_INNER_CORNER
            raw_grid[px-1, py-1] += SPLAT_INNER_CORNER
            raw_grid[px-1, py+1] += SPLAT_INNER_CORNER
            raw_grid[px+1, py-1] += SPLAT_INNER_CORNER
            
            # Outer Ring
            raw_grid[px+2, py] += SPLAT_OUTER_RING
            raw_grid[px-2, py] += SPLAT_OUTER_RING
            raw_grid[px, py+2] += SPLAT_OUTER_RING
            raw_grid[px, py-2] += SPLAT_OUTER_RING
            
            raw_grid[px+2, py+1] += SPLAT_OUTER_CORNER
            raw_grid[px+2, py-1] += SPLAT_OUTER_CORNER
            raw_grid[px-2, py+1] += SPLAT_OUTER_CORNER
            raw_grid[px-2, py-1] += SPLAT_OUTER_CORNER
            
            raw_grid[px+1, py+2] += SPLAT_OUTER_CORNER
            raw_grid[px-1, py+2] += SPLAT_OUTER_CORNER
            raw_grid[px+1, py-2] += SPLAT_OUTER_CORNER
            raw_grid[px-1, py-2] += SPLAT_OUTER_CORNER

    # Colors
    c_fluid = fluid_color[0] * 65536 + fluid_color[1] * 256 + fluid_color[2]
    c_bg = bg_color[0] * 65536 + bg_color[1] * 256 + bg_color[2]
    
    # Determine which slot to write to in the circular buffer
    current_slot = frame_idx % ROLLING_FRAMES
    
    # Parallel loop for Smoothing, Averaging, and Rendering
    # Using SMOOTHING_RADIUS to determine bounds and loop range
    margin = max(2, SMOOTHING_RADIUS) # Ensure we cover splat (2) and smooth (R) margins
    
    for y in prange(margin, height-margin):
        for x in range(margin, width-margin):
            bg_val = static_bg[x, y]
            
            # If obstacle (not background color), skip fluid density calc
            if bg_val != c_bg:
                pixels[x, y] = bg_val
                continue

            # A. Spatial Smoothing (Variable Area Summation of raw_grid)
            d_smooth = 0.0
            for dy in range(-SMOOTHING_RADIUS, SMOOTHING_RADIUS + 1):
                for dx in range(-SMOOTHING_RADIUS, SMOOTHING_RADIUS + 1):
                    d_smooth += raw_grid[x+dx, y+dy]
            
            # B. Store Smoothed Density in History
            density_history[current_slot, x, y] = d_smooth
            
            # C. Temporal Averaging (Sum across all history frames)
            d_total = 0.0
            for k in range(ROLLING_FRAMES):
                d_total += density_history[k, x, y]
            
            # D. Thresholding
            # Lower threshold allows seeing the fluid even without overlap
            if d_total > THRESHOLD_BASE * ROLLING_FRAMES: 
                pixels[x, y] = c_fluid
            else:
                pixels[x, y] = bg_val

# --- Main Simulation Class ---

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Smooth Fluid: {N_PARTICLES} particles")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("monospace", 16)
        
        # Init Physics
        self.pos_x, self.pos_y, self.vel_x, self.vel_y, self.accum_x, self.accum_y = init_system(GRID_WIDTH, GRID_HEIGHT, N_PARTICLES)
        self.obstacles = create_bowl_obstacles(GRID_WIDTH, GRID_HEIGHT)
        
        # Buffers
        print("Allocating Noise Pool & Buffers...")
        self.noise_pool = np.random.normal(0, TEMPERATURE, NOISE_POOL_SIZE).astype(np.float32)
        
        # Density Grids for Visualization
        # raw_grid: Stores current frame's raw splats
        self.raw_grid = np.zeros((GRID_WIDTH, GRID_HEIGHT), dtype=np.float32)
        # density_history: Circular buffer storing smoothed density for last N frames
        self.density_history = np.zeros((ROLLING_FRAMES, GRID_WIDTH, GRID_HEIGHT), dtype=np.float32)
        
        self.frame_count = 0
        
        # Pre-render Background for speed
        self.static_bg = precompute_background(self.obstacles, BG_COLOR, OBSTACLE_COLOR)
        
        # Spatial Partition
        self.head = np.full(GRID_WIDTH * GRID_HEIGHT, -1, dtype=np.int32)
        self.next_particle = np.full(N_PARTICLES, -1, dtype=np.int32)
        
        # Surface
        self.surface = pygame.Surface((GRID_WIDTH, GRID_HEIGHT))
        self.pixel_array = pygame.surfarray.pixels2d(self.surface)

    def update(self):
        offset_x = np.random.randint(0, NOISE_POOL_SIZE)
        offset_y = np.random.randint(0, NOISE_POOL_SIZE)

        update_physics(self.pos_x, self.pos_y, self.vel_x, self.vel_y, self.accum_x, self.accum_y,
                      self.head, self.next_particle, self.obstacles, GRID_WIDTH, GRID_HEIGHT,
                      self.noise_pool, offset_x, offset_y)
        
        if pygame.mouse.get_pressed()[0]:
            pass 

    def draw(self):
        # Use the new Smooth Density Renderer with Temporal Averaging
        render_fluid_density(self.pixel_array, self.pos_x, self.pos_y, 
                           self.raw_grid, self.density_history, self.frame_count,
                           self.static_bg, GRID_WIDTH, GRID_HEIGHT, FLUID_COLOR, BG_COLOR)
        
        self.frame_count += 1
        
        pygame.transform.scale(self.surface, (WINDOW_WIDTH, WINDOW_HEIGHT), self.screen)

        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps} | Particles: {N_PARTICLES}", True, (200, 200, 200))
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
                         self.pos_x, self.pos_y, self.vel_x, self.vel_y, self.accum_x, self.accum_y = init_system(GRID_WIDTH, GRID_HEIGHT, N_PARTICLES)
                         self.density_history.fill(0) # Reset history on reset

            self.update()
            self.draw()
            self.clock.tick(FPS_LIMIT)

        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()
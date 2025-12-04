import numpy as np
import pygame
import random
from numba import njit, prange

# --- Constants & Configuration ---
# Grid Dimensions (Discretized Spatial Domain) - RESTORED BASELINE
GRID_WIDTH = 500
GRID_HEIGHT = 500
CELL_SIZE = 1       # Visual size of one grid cell

# Visualization
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
BG_COLOR = (15, 15, 25)
FLUID_COLOR = (0, 190, 255)
# Foam color removed for single continuous liquid look
OBSTACLE_COLOR = (80, 80, 90) # Dark Grey for the bowl
FPS_LIMIT = 0

# Simulation Parameters - RESTORED BASELINE
N_PARTICLES = 10000  
GRAVITY = 0.45      
MAX_VEL = 3.0       
FRICTION = 0.999     
OVERLAP_FORCE = 2.0 
TEMPERATURE = 0.001   

# Optimization: Static Noise Pool
NOISE_POOL_SIZE = 16384
NOISE_MASK = NOISE_POOL_SIZE - 1

# --- Discrete Physics Engine ---

@njit(fastmath=True)
def get_force_lookup():
    """
    Pre-calculate a discrete force field kernel.
    RESTORED BASELINE (Radius 4)
    """
    radius = 4
    dim = 2 * radius + 1
    kernel_x = np.zeros((dim, dim), dtype=np.float32)
    kernel_y = np.zeros((dim, dim), dtype=np.float32)
    
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            dist_sq = dx*dx + dy*dy
            if dist_sq == 0: continue
            
            dist = np.sqrt(dist_sq)
            dir_x = dx / dist
            dir_y = dy / dist
            
            force = 0.0
            
            # Heuristic Lattice Potentials
            if dist_sq <= 2:
                force = 0.8 # Repulsion
            elif dist_sq <= 9:
                force = -0.02 # Weak Attraction
                
            kernel_x[dy + radius, dx + radius] = force * dir_x
            kernel_y[dy + radius, dx + radius] = force * dir_y
            
    return kernel_x, kernel_y

# Pre-compile the kernel once
KERNEL_X, KERNEL_Y = get_force_lookup()
KERNEL_RADIUS = 4

@njit(fastmath=True)
def create_bowl_obstacles(width, height):
    """
    Create a static obstacle map representing a U-shaped bowl.
    """
    obstacles = np.zeros((height, width), dtype=np.int32)
    cx = width // 2
    cy = height // 2 - 10
    radius = width // 2 - 15  

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
    spawn_h = height // 3
    start_x = (width - spawn_w) // 2
    start_y = 5 
    
    for i in range(n_particles):
        pos_x[i] = np.random.randint(start_x, start_x + spawn_w)
        pos_y[i] = np.random.randint(start_y, start_y + spawn_h)
        vel_x[i] = np.random.uniform(-0.5, 0.5)
        vel_y[i] = np.random.uniform(0.0, 1.0) 
                
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
    RESTORED BASELINE LOGIC
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
    # Using parallel loop as in the optimized versions, but keeping baseline physics math
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
        
        r = KERNEL_RADIUS
        
        # Neighbor scan
        for dy in range(-r, r + 1):
            ny = py + dy
            if ny < 0 or ny >= height: continue
            
            for dx in range(-r, r + 1):
                nx = px + dx
                if nx < 0 or nx >= width: continue
                
                # Obstacle Repulsion
                if obstacles[ny, nx] == 1:
                    dist_sq = dx*dx + dy*dy
                    if dist_sq <= 2:
                        fx -= dx * 0.5 
                        fy -= dy * 0.5
                
                # Particle Forces
                n_cell_idx = ny * width + nx
                j = head[n_cell_idx]
                while j != -1:
                    if i != j:
                        if dx == 0 and dy == 0:
                            # BASELINE PHYSICS: Random angle kick
                            rand_angle = np.random.uniform(0, 6.28)
                            fx += np.cos(rand_angle) * OVERLAP_FORCE
                            fy += np.sin(rand_angle) * OVERLAP_FORCE
                        else:
                            fx += KERNEL_X[dy + r, dx + r]
                            fy += KERNEL_Y[dy + r, dx + r]
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
                    vel_x[i] *= -0.5
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
                    vel_y[i] *= -0.5
                    accum_y[i] = 0 
                    vel_x[i] *= 0.9 
                    break

@njit(fastmath=True, parallel=True)
def render_fluid_density(pixels, pos_x, pos_y, density_grid, static_bg, width, height, fluid_color, bg_color):
    """
    Renders the simulation as a smooth fluid surface by calculating a density field.
    Visual Layer is detached from Physics Layer (particles).
    UPDATED: 5x5 Splatting + Strong Thresholding to remove small droplets.
    """
    # 1. Reset Density Grid
    density_grid[:] = 0.0
    
    # 2. Accumulate Density (5x5 Splatting)
    # Creates broader blobs with weighted centers.
    for i in range(len(pos_x)):
        px = pos_x[i]
        py = pos_y[i]
        
        # Check bounds (padding 2 for 5x5)
        if 2 < px < width-3 and 2 < py < height-3:
            # Core (High weight)
            density_grid[px, py] += 10.0
            
            # Inner Ring
            density_grid[px+1, py] += 6.0
            density_grid[px-1, py] += 6.0
            density_grid[px, py+1] += 6.0
            density_grid[px, py-1] += 6.0
            
            density_grid[px+1, py+1] += 4.0
            density_grid[px-1, py-1] += 4.0
            density_grid[px-1, py+1] += 4.0
            density_grid[px+1, py-1] += 4.0
            
            # Outer Ring
            density_grid[px+2, py] += 2.0
            density_grid[px-2, py] += 2.0
            density_grid[px, py+2] += 2.0
            density_grid[px, py-2] += 2.0
            
            density_grid[px+2, py+1] += 1.0
            density_grid[px+2, py-1] += 1.0
            density_grid[px-2, py+1] += 1.0
            density_grid[px-2, py-1] += 1.0
            
            density_grid[px+1, py+2] += 1.0
            density_grid[px-1, py+2] += 1.0
            density_grid[px+1, py-2] += 1.0
            density_grid[px-1, py-2] += 1.0

    # 3. Smooth & Threshold
    c_fluid = fluid_color[0] * 65536 + fluid_color[1] * 256 + fluid_color[2]
    c_bg = bg_color[0] * 65536 + bg_color[1] * 256 + bg_color[2]
    
    # Parallel loop for rendering
    for y in prange(2, height-2):
        for x in range(2, width-2):
            bg_val = static_bg[x, y]
            
            # If obstacle (not background color), skip fluid density
            if bg_val != c_bg:
                pixels[x, y] = bg_val
                continue

            # Smooth Density (5x5 Area Summation)
            d = 0.0
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    d += density_grid[x+dx, y+dy]
            
            # Aggressive Thresholding
            # A single particle contributes ~74 mass total.
            # We set threshold > 74 to ensure single particles are invisible.
            # Only overlapping particles will trigger this.
            if d > 150.0: 
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
        
        # Density Grid for Visualization
        self.density_grid = np.zeros((GRID_WIDTH, GRID_HEIGHT), dtype=np.float32)
        
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
        # Use the new Smooth Density Renderer
        render_fluid_density(self.pixel_array, self.pos_x, self.pos_y, self.density_grid, 
                           self.static_bg, GRID_WIDTH, GRID_HEIGHT, FLUID_COLOR, BG_COLOR)
        
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

            self.update()
            self.draw()
            self.clock.tick(FPS_LIMIT)

        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()
import numpy as np
import pygame
import random
from numba import njit, prange

# --- Constants & Configuration ---
# Grid Dimensions (Discretized Spatial Domain)
GRID_WIDTH = 300
GRID_HEIGHT = 300
CELL_SIZE = 1       # Visual size of one grid cell

# Visualization
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
BG_COLOR = (15, 15, 25)
FLUID_COLOR = (0, 190, 255)
FPS_LIMIT = 0

# Simulation Parameters
N_PARTICLES = 5000  
GRAVITY = 0.05
MAX_VEL = 4.0       # Increased to allow rapid separation of overlaps
FRICTION = 0.96     # Slightly more damping to stabilize the higher energy potential
OVERLAP_FORCE = 3.0 # Strong force to push overlapping particles apart

# --- Discrete Physics Engine ---

@njit(fastmath=True)
def get_force_lookup():
    """
    Pre-calculate a discrete force field kernel.
    We scan a small integer radius.
    Range 1 (Neighbors): Repulsion (Pressure)
    Range 2 (Nearby): Attraction (Surface Tension)
    """
    radius = 4
    dim = 2 * radius + 1
    kernel_x = np.zeros((dim, dim), dtype=np.float32)
    kernel_y = np.zeros((dim, dim), dtype=np.float32)
    
    # Lennard-Jones-like discrete profile
    # Center index is [radius, radius]
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            dist_sq = dx*dx + dy*dy
            if dist_sq == 0: continue
            
            # Normalized direction vectors
            dist = np.sqrt(dist_sq)
            dir_x = dx / dist
            dir_y = dy / dist
            
            force = 0.0
            
            # Heuristic Lattice Potentials
            # Very close (1-1.5): Repulse (Positive Force)
            if dist_sq <= 2:
                force = 1.2 # Push away
                
            # Medium (2-3): Attract (Negative Force)
            elif dist_sq <= 9:
                force = -0.3 # Pull in
                
            # Store in kernel (Index offset by radius)
            kernel_x[dy + radius, dx + radius] = force * dir_x
            kernel_y[dy + radius, dx + radius] = force * dir_y
            
    return kernel_x, kernel_y

# Pre-compile the kernel once
KERNEL_X, KERNEL_Y = get_force_lookup()
KERNEL_RADIUS = 4

@njit(fastmath=True)
def init_system(width, height, n_particles):
    """
    Initialize particle arrays.
    pos: Integers (Grid coordinates)
    vel: Floats (Continuous momentum)
    """
    pos_x = np.zeros(n_particles, dtype=np.int32)
    pos_y = np.zeros(n_particles, dtype=np.int32)
    vel_x = np.zeros(n_particles, dtype=np.float32)
    vel_y = np.zeros(n_particles, dtype=np.float32)
    
    # Safe Initialization Logic
    # Calculate how much area we physically need to avoid jamming.
    # We aim for ~50% density in the spawn block.
    needed_area = n_particles * 2
    
    # Determine the height of the spawn block based on grid width
    spawn_height = int(needed_area / width)
    
    # Clamp to be safe (don't spawn outside screen)
    if spawn_height > height - 10:
        spawn_height = height - 10
    if spawn_height < 10: 
        spawn_height = 10
        
    start_y = (height // 2) - (spawn_height // 2)
    
    # Fill the calculated rectangle
    for i in range(n_particles):
        pos_x[i] = np.random.randint(1, width - 1)
        pos_y[i] = np.random.randint(start_y, start_y + spawn_height)
        
        vel_x[i] = np.random.uniform(-0.5, 0.5)
        vel_y[i] = np.random.uniform(-0.5, 0.5)
                
    return pos_x, pos_y, vel_x, vel_y

@njit(fastmath=True)
def update_physics(pos_x, pos_y, vel_x, vel_y, head, next_particle, width, height):
    """
    Discrete Particle Dynamics allowing overlap via Cell Linked List.
    """
    n = len(pos_x)
    total_cells = width * height
    
    # --- 1. Build Cell Linked List ---
    # Reset head array
    head.fill(-1)
    next_particle.fill(-1)
    
    for i in range(n):
        # Flattened index: y * width + x
        cell_idx = pos_y[i] * width + pos_x[i]
        
        # Insert i at the beginning of the list for this cell
        next_particle[i] = head[cell_idx]
        head[cell_idx] = i

    # --- 2. Calculate Forces ---
    # Random update order to prevent bias
    order = np.arange(n)
    np.random.shuffle(order)
    
    for i in order:
        px = pos_x[i]
        py = pos_y[i]
        
        fx = 0.0
        fy = GRAVITY
        
        # Scan neighborhood using kernel
        r = KERNEL_RADIUS
        
        # Check all cells in range, including own cell (0,0) for overlaps
        for dy in range(-r, r + 1):
            ny = py + dy
            if ny < 0 or ny >= height: continue
            
            for dx in range(-r, r + 1):
                nx = px + dx
                if nx < 0 or nx >= width: continue
                
                # Get the cell index
                n_cell_idx = ny * width + nx
                
                # Traverse linked list for this cell
                j = head[n_cell_idx]
                while j != -1:
                    if i != j:
                        # Determine force
                        if dx == 0 and dy == 0:
                            # Exact Overlap!
                            # Apply strong random kick to separate
                            # We use index based noise to be deterministic-ish per step or just random
                            rand_angle = np.random.uniform(0, 6.28)
                            fx += np.cos(rand_angle) * OVERLAP_FORCE
                            fy += np.sin(rand_angle) * OVERLAP_FORCE
                        else:
                            # Use pre-calculated kernel
                            # Kernel indices are shifted by radius
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
        
        # --- 4. Discrete Movement (Allow Overlap) ---
        # Probabilistic movement based on velocity
        
        dx_step = 0
        dy_step = 0
        
        if np.random.random() < abs(vel_x[i]):
            dx_step = 1 if vel_x[i] > 0 else -1
            
        if np.random.random() < abs(vel_y[i]):
            dy_step = 1 if vel_y[i] > 0 else -1
            
        # Move X
        if dx_step != 0:
            nx = px + dx_step
            if 0 <= nx < width:
                pos_x[i] = nx
                px = nx # Update local for Y calculation
            else:
                vel_x[i] *= -0.8 # Wall bounce
                
        # Move Y
        if dy_step != 0:
            ny = py + dy_step
            if 0 <= ny < height:
                pos_y[i] = ny
            else:
                vel_y[i] *= -0.5 # Floor bounce damping
                vel_x[i] *= 0.9  # Floor friction

@njit(fastmath=True)
def render_particles(pixels, pos_x, pos_y, fluid_color, bg_color):
    """
    Render based on particle positions.
    """
    # Clear
    pixels.fill(bg_color[0] * 65536 + bg_color[1] * 256 + bg_color[2])
    
    c_fluid = fluid_color[0] * 65536 + fluid_color[1] * 256 + fluid_color[2]
    
    n = len(pos_x)
    for i in range(n):
        x = pos_x[i]
        y = pos_y[i]
        if 0 <= x < pixels.shape[0] and 0 <= y < pixels.shape[1]:
            pixels[x, y] = c_fluid

# --- Main Simulation Class ---

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Discrete MD: {N_PARTICLES} particles")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("monospace", 16)
        
        # Init System
        self.pos_x, self.pos_y, self.vel_x, self.vel_y = init_system(GRID_WIDTH, GRID_HEIGHT, N_PARTICLES)
        
        # Spatial Partition Memory (Reused every frame)
        self.head = np.full(GRID_WIDTH * GRID_HEIGHT, -1, dtype=np.int32)
        self.next_particle = np.full(N_PARTICLES, -1, dtype=np.int32)
        
        # Rendering Buffer
        self.surface = pygame.Surface((GRID_WIDTH, GRID_HEIGHT))
        self.pixel_array = pygame.surfarray.pixels2d(self.surface)

    def update(self):
        # Physics
        update_physics(self.pos_x, self.pos_y, self.vel_x, self.vel_y, 
                      self.head, self.next_particle, GRID_WIDTH, GRID_HEIGHT)
        
        # Interaction (Mouse adds particles)
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            # Basic logic to just add interaction placeholder
            pass 

    def draw(self):
        render_particles(self.pixel_array, self.pos_x, self.pos_y, FLUID_COLOR, BG_COLOR)
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
                         self.pos_x, self.pos_y, self.vel_x, self.vel_y = init_system(GRID_WIDTH, GRID_HEIGHT, N_PARTICLES)

            self.update()
            self.draw()
            self.clock.tick(FPS_LIMIT)

        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()
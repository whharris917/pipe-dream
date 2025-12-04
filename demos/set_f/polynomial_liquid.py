import numpy as np
import pygame
import time
from numba import njit, prange

# --- Constants & Configuration ---
# Simulation parameters
N_PARTICLES = 10000      # Updated to your count
DENSITY = 0.4
TEMP_INITIAL = 0.5
DT = 0.008
CUTOFF = 1.5            # Updated cutoff
SKIN = 0.3
MASS = 1.0
GRAVITY = 100.5         # High gravity as requested

# Liquid Potential Parameters (Polynomial)
# Optimized Force uses q_squared (r^2/h^2) to avoid Sqrt calls
# Force ~ STIFFNESS * (1-q2)^3 - COHESION * (1-q2)^2
STIFFNESS = 1000.0      
COHESION = 300.0        

# Derived dimensions
BOX_SIZE = np.sqrt(N_PARTICLES / DENSITY)
CELL_SIZE = CUTOFF      # Cells must be at least cutoff size
GRID_DIM = int(np.ceil(BOX_SIZE / CELL_SIZE))

# Visualization
WIDTH, HEIGHT = 800, 800
SCALE = WIDTH / BOX_SIZE
BG_COLOR = (15, 15, 25)
PARTICLE_COLOR = (50, 150, 255) 
FPS_LIMIT = 0

# --- JIT Compiled Physics Engine ---

@njit(fastmath=True)
def init_grid(n, box_size):
    """
    Initialize positions on a square lattice.
    """
    pos = np.zeros((n, 2), dtype=np.float64)
    side = int(np.ceil(np.sqrt(n)))
    spacing = box_size / side
    
    for i in range(n):
        row = i // side
        col = i % side
        pos[i, 0] = (col + 0.5) * spacing
        pos[i, 1] = (row + 0.5) * spacing
    return pos

@njit(fastmath=True)
def init_velocities(n, temp):
    """
    Initialize velocities.
    """
    vel = np.random.normal(0, np.sqrt(temp), (n, 2))
    v_cm = np.sum(vel, axis=0) / n
    vel -= v_cm
    return vel

@njit(fastmath=True)
def apply_thermostat(vel, target_temp):
    """
    Simple thermostat. 
    Optimized: No explicit array creation for sum.
    """
    # Numba handles the reduction of vel**2 efficiently without allocation
    ke = np.sum(vel**2) * 0.5 * MASS
    current_temp = ke / (vel.shape[0]) 
    
    # Drag thermostat: simple multiplication is cheaper than rescaling logic
    if current_temp > target_temp * 2.0:
        vel *= 0.99 # Simple friction

@njit(fastmath=True, parallel=True)
def build_cell_list(pos, head, next_particle, cell_size, grid_dim):
    """
    Builds a linked-list cell structure.
    """
    head[:] = -1
    next_particle[:] = -1
    
    for i in range(pos.shape[0]):
        cx = int(pos[i, 0] / cell_size)
        cy = int(pos[i, 1] / cell_size)
        
        # Periodic X
        cx = cx % grid_dim
        # Clamped Y
        cy = cy % grid_dim 
        
        cell_idx = cy * grid_dim + cx
        next_particle[i] = head[cell_idx]
        head[cell_idx] = i

@njit(fastmath=True, parallel=True)
def compute_forces_liquid(pos, forces, head, next_particle, cell_size, grid_dim, box_size):
    """
    Compute liquid-like forces using a polynomial potential.
    OPTIMIZATION: Uses squared distance (r2) only. 
    Eliminates np.sqrt() and division by dist for normalization.
    """
    forces[:] = 0.0
    cutoff_sq = CUTOFF * CUTOFF
    inv_cutoff_sq = 1.0 / cutoff_sq
    
    # Loop over all particles
    for i in prange(pos.shape[0]):
        # Apply Gravity
        forces[i, 1] += MASS * GRAVITY
        
        px = pos[i, 0]
        py = pos[i, 1]
        
        cx = int(px / cell_size) % grid_dim
        cy = int(py / cell_size) % grid_dim
        
        # Check neighbor cells
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ncx = (cx + dx + grid_dim) % grid_dim
                ncy = (cy + dy + grid_dim) % grid_dim
                n_cell_idx = ncy * grid_dim + ncx
                
                j = head[n_cell_idx]
                while j != -1:
                    if i != j:
                        dx_vec = px - pos[j, 0]
                        dy_vec = py - pos[j, 1]
                        
                        # Periodic X
                        if dx_vec > box_size * 0.5: dx_vec -= box_size
                        elif dx_vec < -box_size * 0.5: dx_vec += box_size
                        
                        r2 = dx_vec*dx_vec + dy_vec*dy_vec
                        
                        # Force Optimization: working directly with r2
                        if r2 < cutoff_sq and r2 > 1e-8:
                            # q2 = (r/h)^2
                            q2 = r2 * inv_cutoff_sq
                            
                            if q2 < 1.0:
                                # Standard SPH-like kernel based on q2
                                # val = (1 - q^2)
                                val = 1.0 - q2
                                
                                # Force Profile:
                                # We multiply by dx_vec (not normalized).
                                # Effectively Force = F_scalar * r.
                                # This naturally handles the r=0 singularity (Force->0).
                                
                                # Use polynomial powers to shape the potential
                                # Stiffness (Repulsion) - Cohesion (Attraction)
                                f_scal = (STIFFNESS * val**3 - COHESION * val**2)
                                
                                # Apply
                                forces[i, 0] += f_scal * dx_vec
                                forces[i, 1] += f_scal * dy_vec
                            
                    j = next_particle[j]

@njit(fastmath=True, parallel=True)
def integrate(pos, vel, forces, dt, box_size):
    """
    Velocity Verlet Integration.
    """
    for i in prange(pos.shape[0]):
        vel[i, 0] += 0.5 * forces[i, 0] * dt
        vel[i, 1] += 0.5 * forces[i, 1] * dt
        
        pos[i, 0] += vel[i, 0] * dt
        pos[i, 1] += vel[i, 1] * dt
        
        # Periodic X
        if pos[i, 0] < 0: pos[i, 0] += box_size
        elif pos[i, 0] >= box_size: pos[i, 0] -= box_size
        
        # Reflective Y with Damping (simulate wall friction)
        if pos[i, 1] >= box_size:
            pos[i, 1] = 2*box_size - pos[i, 1]
            vel[i, 1] *= -0.5 # Lose energy on bounce (inelastic floor)
        elif pos[i, 1] < 0:
            pos[i, 1] = -pos[i, 1]
            vel[i, 1] *= -0.5

@njit(fastmath=True, parallel=True)
def integrate_vel_part2(vel, forces, dt):
    for i in prange(vel.shape[0]):
        vel[i, 0] += 0.5 * forces[i, 0] * dt
        vel[i, 1] += 0.5 * forces[i, 1] * dt

# --- Main Simulation Class ---

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"Liquid Sim: {N_PARTICLES} particles")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("monospace", 16)

        print("Initializing Physics Memory...")
        self.pos = init_grid(N_PARTICLES, BOX_SIZE)
        self.vel = init_velocities(N_PARTICLES, TEMP_INITIAL)
        self.forces = np.zeros_like(self.pos)
        
        self.total_cells = GRID_DIM * GRID_DIM
        self.head = np.full(self.total_cells, -1, dtype=np.int32)
        self.next_particle = np.full(N_PARTICLES, -1, dtype=np.int32)
        
        print(f"System: {N_PARTICLES} particles.")
        print("Compiling JIT functions...")
        start_compile = time.time()
        # Compilation trigger
        build_cell_list(self.pos, self.head, self.next_particle, CELL_SIZE, GRID_DIM)
        compute_forces_liquid(self.pos, self.forces, self.head, self.next_particle, CELL_SIZE, GRID_DIM, BOX_SIZE)
        integrate(self.pos, self.vel, self.forces, DT, BOX_SIZE)
        print(f"Ready. Compile time: {time.time() - start_compile:.2f}s.")

    def update(self):
        build_cell_list(self.pos, self.head, self.next_particle, CELL_SIZE, GRID_DIM)
        integrate(self.pos, self.vel, self.forces, DT, BOX_SIZE)
        compute_forces_liquid(self.pos, self.forces, self.head, self.next_particle, CELL_SIZE, GRID_DIM, BOX_SIZE)
        integrate_vel_part2(self.vel, self.forces, DT)
        apply_thermostat(self.vel, TEMP_INITIAL)

    def draw(self):
        self.screen.fill(BG_COLOR)
        screen_pos = (self.pos * SCALE).astype(np.int32)
        
        # Draw particles
        for x, y in screen_pos:
            # Simple fast circle
            pygame.draw.circle(self.screen, PARTICLE_COLOR, (x, y), 2)

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

            self.update()
            self.draw()
            self.clock.tick(FPS_LIMIT)

        pygame.quit()

if __name__ == "__main__":
    sim = Simulation()
    sim.run()
import numpy as np
import pygame
import time
from numba import njit, prange

# --- Constants & Configuration ---
# Simulation parameters
N_PARTICLES = 10000
DENSITY = 0.7           # LJ density
TEMP_INITIAL = 1.0      # Reduced temperature (kT/epsilon)
DT = 0.005              # Time step
CUTOFF = 2.5            # Force cutoff radius
SKIN = 0.3              # Neighbor list skin (not used in simple cell list, but good practice)
MASS = 1.0

# Lennard-Jones parameters
SIGMA = 1.0
EPSILON = 1.0

# Derived dimensions
# We want a 100x100 lattice. 
# Area needed roughly N / DENSITY. Side length L = sqrt(N/rho).
BOX_SIZE = np.sqrt(N_PARTICLES / DENSITY)
CELL_SIZE = CUTOFF      # Cells must be at least cutoff size
GRID_DIM = int(np.ceil(BOX_SIZE / CELL_SIZE))

# Visualization
WIDTH, HEIGHT = 800, 800
SCALE = WIDTH / BOX_SIZE
BG_COLOR = (10, 10, 30)
PARTICLE_COLOR = (0, 200, 255)
FPS_LIMIT = 0

# --- JIT Compiled Physics Engine ---

@njit(fastmath=True)
def init_grid(n, box_size):
    """
    Initialize positions on a square lattice to prevent overlaps.
    """
    pos = np.zeros((n, 2), dtype=np.float64)
    side = int(np.ceil(np.sqrt(n)))
    spacing = box_size / side
    
    for i in range(n):
        row = i // side
        col = i % side
        # Center the lattice in the box
        pos[i, 0] = (col + 0.5) * spacing
        pos[i, 1] = (row + 0.5) * spacing
    return pos

@njit(fastmath=True)
def init_velocities(n, temp):
    """
    Initialize velocities from a Boltzmann distribution.
    Center of mass momentum is removed to prevent drift.
    """
    vel = np.random.normal(0, np.sqrt(temp), (n, 2))
    
    # Remove center of mass motion
    v_cm = np.sum(vel, axis=0) / n
    vel -= v_cm
    return vel

@njit(fastmath=True, parallel=True)
def build_cell_list(pos, head, next_particle, cell_size, grid_dim):
    """
    Builds a linked-list cell structure for O(N) neighbor lookups.
    """
    # Reset head array
    head[:] = -1
    next_particle[:] = -1
    
    # Iterate over all particles and place them in cells
    # Note: We cannot parallelize this write safely without atomics or sorting.
    # For simplicity in this specific step, we run serial or use a sort-based approach.
    # Serial is plenty fast for 10k particles for just the binning.
    for i in range(pos.shape[0]):
        cx = int(pos[i, 0] / cell_size)
        cy = int(pos[i, 1] / cell_size)
        
        # Periodic boundary wrapping for cell index
        cx = cx % grid_dim
        cy = cy % grid_dim
        
        cell_idx = cy * grid_dim + cx
        
        # Linked list insertion
        next_particle[i] = head[cell_idx]
        head[cell_idx] = i

@njit(fastmath=True, parallel=True)
def compute_forces_lj(pos, forces, head, next_particle, cell_size, grid_dim, box_size):
    """
    Compute Lennard-Jones forces using the Cell List.
    Parallelized over particles.
    """
    forces[:] = 0.0
    cutoff_sq = CUTOFF * CUTOFF
    
    # Pre-calculate LJ constants for efficiency
    # V = 4eps * ((s/r)^12 - (s/r)^6)
    # F = 24eps/r * (2(s/r)^12 - (s/r)^6) * (r_vec / r)
    # F_vec = 24eps * (2(s^12/r^14) - (s^6/r^8)) * r_vec
    c12 = 48.0 * EPSILON * (SIGMA ** 12)
    c6 = 24.0 * EPSILON * (SIGMA ** 6)

    # Loop over all particles
    for i in prange(pos.shape[0]):
        px = pos[i, 0]
        py = pos[i, 1]
        
        # Determine own cell
        cx = int(px / cell_size) % grid_dim
        cy = int(py / cell_size) % grid_dim
        
        # Check neighbor cells (3x3 grid around current cell)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                # Wrap neighbor cell indices (Periodic Boundaries)
                ncx = (cx + dx + grid_dim) % grid_dim
                ncy = (cy + dy + grid_dim) % grid_dim
                n_cell_idx = ncy * grid_dim + ncx
                
                # Traverse linked list of this neighbor cell
                j = head[n_cell_idx]
                while j != -1:
                    if i != j: # Don't interact with self
                        # Calculate distance vector with Minimum Image Convention
                        dx_vec = px - pos[j, 0]
                        dy_vec = py - pos[j, 1]
                        
                        # Periodic BC correction
                        if dx_vec > box_size * 0.5: dx_vec -= box_size
                        elif dx_vec < -box_size * 0.5: dx_vec += box_size
                        if dy_vec > box_size * 0.5: dy_vec -= box_size
                        elif dy_vec < -box_size * 0.5: dy_vec += box_size
                        
                        r2 = dx_vec*dx_vec + dy_vec*dy_vec
                        
                        if r2 < cutoff_sq:
                            r2_inv = 1.0 / r2
                            r6_inv = r2_inv * r2_inv * r2_inv
                            r12_inv = r6_inv * r6_inv
                            
                            # Force magnitude / r
                            f_scal = (c12 * r12_inv - c6 * r6_inv) * r2_inv
                            
                            forces[i, 0] += f_scal * dx_vec
                            forces[i, 1] += f_scal * dy_vec
                            
                    j = next_particle[j]

@njit(fastmath=True, parallel=True)
def integrate(pos, vel, forces, dt, box_size):
    """
    Velocity Verlet Integration.
    """
    # Half-step velocity update was done implicitly or can be split.
    # Standard Velocity Verlet:
    # v(t+0.5) = v(t) + 0.5 * a(t) * dt
    # r(t+1) = r(t) + v(t+0.5) * dt
    # a(t+1) = f(r(t+1))
    # v(t+1) = v(t+0.5) + 0.5 * a(t+1) * dt
    
    # Here we accept forces are calculated for the current position.
    # Update Velocity (Full step for simplicity if coupled, 
    # but for true Verlet we usually split. Using simple Euler-Cromer or similar 
    # for simpler visual code, but let's do real Verlet part 1)
    
    # Assuming forces are from current step:
    for i in prange(pos.shape[0]):
        vel[i, 0] += 0.5 * forces[i, 0] * dt
        vel[i, 1] += 0.5 * forces[i, 1] * dt
        
        pos[i, 0] += vel[i, 0] * dt
        pos[i, 1] += vel[i, 1] * dt
        
        # Periodic Boundary Conditions (Position)
        if pos[i, 0] < 0: pos[i, 0] += box_size
        elif pos[i, 0] >= box_size: pos[i, 0] -= box_size
        
        if pos[i, 1] < 0: pos[i, 1] += box_size
        elif pos[i, 1] >= box_size: pos[i, 1] -= box_size

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
        pygame.display.set_caption(f"Lennard-Jones: {N_PARTICLES} particles")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.SysFont("monospace", 16)

        # Simulation State
        print("Initializing Physics Memory...")
        self.pos = init_grid(N_PARTICLES, BOX_SIZE)
        self.vel = init_velocities(N_PARTICLES, TEMP_INITIAL)
        self.forces = np.zeros_like(self.pos)
        
        # Cell List Arrays
        # head: points to the first particle in a cell (size: total cells)
        # next_particle: points to the next particle in the list (size: N)
        self.total_cells = GRID_DIM * GRID_DIM
        self.head = np.full(self.total_cells, -1, dtype=np.int32)
        self.next_particle = np.full(N_PARTICLES, -1, dtype=np.int32)
        
        print(f"System: {N_PARTICLES} particles in {BOX_SIZE:.1f}x{BOX_SIZE:.1f} box.")
        print(f"Grid: {GRID_DIM}x{GRID_DIM} cells.")
        
        # Warmup JIT (run one step to compile functions)
        print("Compiling JIT functions (this might take a few seconds)...")
        start_compile = time.time()
        build_cell_list(self.pos, self.head, self.next_particle, CELL_SIZE, GRID_DIM)
        compute_forces_lj(self.pos, self.forces, self.head, self.next_particle, CELL_SIZE, GRID_DIM, BOX_SIZE)
        integrate(self.pos, self.vel, self.forces, DT, BOX_SIZE)
        print(f"Compilation finished in {time.time() - start_compile:.2f}s.")

    def update(self):
        # 1. Update Cell Lists (Sorting particles into spatial bins)
        build_cell_list(self.pos, self.head, self.next_particle, CELL_SIZE, GRID_DIM)
        
        # 2. First Half-Kick (Velocity Verlet) & Move
        # We integrate r(t+dt) and v(t+0.5dt)
        integrate(self.pos, self.vel, self.forces, DT, BOX_SIZE)
        
        # 3. Compute Forces at new positions
        compute_forces_lj(self.pos, self.forces, self.head, self.next_particle, CELL_SIZE, GRID_DIM, BOX_SIZE)
        
        # 4. Second Half-Kick
        # v(t+dt) = v(t+0.5dt) + 0.5 * a(t+dt) * dt
        integrate_vel_part2(self.vel, self.forces, DT)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Fast Rendering: Convert physics coordinates to screen coordinates
        # We can map numpy arrays directly to avoid looping in Python
        screen_pos = (self.pos * SCALE).astype(np.int32)
        
        # Direct pixel access or simple circles. 
        # For 10k particles, drawing small circles is optimized in Pygame 2.0+
        # but let's be safe and fast.
        
        # Option A: Draw Circles (Better looking, heavier)
        # for i in range(N_PARTICLES):
        #    pygame.draw.circle(self.screen, PARTICLE_COLOR, screen_pos[i], 2)
             
        # Option B: Pixel Array (Fastest for massive counts, looks like points)
        # Using surfarray can be complex to handle colors.
        
        # Option C: Pygame's efficient C-backend for circles
        # If we loop in Python, 10k iters is ~10ms. Acceptable.
        for x, y in screen_pos:
            pygame.draw.circle(self.screen, PARTICLE_COLOR, (x, y), 2)

        # UI
        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps} | Particles: {N_PARTICLES}", True, (255, 255, 255))
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
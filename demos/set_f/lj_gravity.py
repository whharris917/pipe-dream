import numpy as np
import pygame
import time
from numba import njit, prange

# --- Constants & Configuration ---
# Simulation parameters
N_PARTICLES = 10000
DENSITY = 0.35          # Lower initial density so particles can settle into the bottom half
TEMP_INITIAL = 1.0      # Reduced temperature (kT/epsilon)
DT = 0.005              # Time step
CUTOFF = 2.5            # Force cutoff radius
SKIN = 0.3              # Neighbor list skin
MASS = 1.0
GRAVITY = 0.2           # Gravity force (Downwards in screen coords, i.e., +Y)

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

@njit(fastmath=True)
def apply_thermostat(vel, target_temp):
    """
    Simple velocity rescaling to maintain constant temperature.
    Essential when adding gravity, as PE -> KE conversion causes heating.
    """
    # KE = 0.5 * m * v^2
    # In 2D, Average KE = N * kT
    ke = np.sum(vel**2) * 0.5 * MASS
    current_temp = ke / (vel.shape[0]) # N particles
    
    if current_temp > 1e-9:
        scale = np.sqrt(target_temp / current_temp)
        # Apply a soft scaling (berendsen-like) or hard scaling
        # Hard scaling is more stable for this demo to kill the heat from falling quickly
        vel *= scale

@njit(fastmath=True, parallel=True)
def build_cell_list(pos, head, next_particle, cell_size, grid_dim):
    """
    Builds a linked-list cell structure for O(N) neighbor lookups.
    """
    # Reset head array
    head[:] = -1
    next_particle[:] = -1
    
    # Iterate over all particles and place them in cells
    for i in range(pos.shape[0]):
        cx = int(pos[i, 0] / cell_size)
        cy = int(pos[i, 1] / cell_size)
        
        # Periodic boundary wrapping for cell index (X only)
        # Ideally we clamp Y for cells, but modulo works if we handle boundaries in force calc
        # For simplicity, we keep grid periodic, but particle positions are clamped in integrate
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
    c12 = 48.0 * EPSILON * (SIGMA ** 12)
    c6 = 24.0 * EPSILON * (SIGMA ** 6)
    
    # Gravity Force Vector (0, GRAVITY)
    # Applied to all particles
    # Using a separate loop or broadcasting might be cleaner, but adding here saves memory access
    
    # Loop over all particles
    for i in prange(pos.shape[0]):
        # Apply Gravity (Downwards)
        forces[i, 1] += MASS * GRAVITY
        
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
                        
                        # Periodic BC correction ONLY for X axis
                        if dx_vec > box_size * 0.5: dx_vec -= box_size
                        elif dx_vec < -box_size * 0.5: dx_vec += box_size
                        
                        # For Y axis, we have walls, so no periodic wrapping for distance
                        # However, neighbor search uses periodic grid index. 
                        # We must ensure we don't interact 'through' the floor/ceiling 
                        # if the box is effectively infinite in Y. 
                        # Since we have walls at 0 and BOX_SIZE, and CUTOFF << BOX_SIZE, 
                        # standard distance check handles this implicitly unless wrapping occurs.
                        # The logic below 'unwraps' Y if we treated it as periodic. 
                        # Since we want walls, we simply do NOT wrap dy_vec.
                        
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
    Velocity Verlet Integration with Mixed Boundaries (Periodic X, Reflective Y).
    """
    for i in prange(pos.shape[0]):
        vel[i, 0] += 0.5 * forces[i, 0] * dt
        vel[i, 1] += 0.5 * forces[i, 1] * dt
        
        pos[i, 0] += vel[i, 0] * dt
        pos[i, 1] += vel[i, 1] * dt
        
        # Periodic Boundary Conditions (X - Left/Right)
        if pos[i, 0] < 0: pos[i, 0] += box_size
        elif pos[i, 0] >= box_size: pos[i, 0] -= box_size
        
        # Reflective Boundary Conditions (Y - Top/Bottom)
        # Floor
        if pos[i, 1] >= box_size:
            pos[i, 1] = 2*box_size - pos[i, 1] # Reflect position
            vel[i, 1] *= -1                    # Reflect velocity
        # Ceiling
        elif pos[i, 1] < 0:
            pos[i, 1] = -pos[i, 1]             # Reflect position
            vel[i, 1] *= -1                    # Reflect velocity

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
        
        # 5. Thermostat (Remove heat generated by gravity/falling)
        apply_thermostat(self.vel, TEMP_INITIAL)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Fast Rendering: Convert physics coordinates to screen coordinates
        # We can map numpy arrays directly to avoid looping in Python
        screen_pos = (self.pos * SCALE).astype(np.int32)
        
        # Direct pixel access or simple circles. 
        # For 10k particles, drawing small circles is optimized in Pygame 2.0+
        # but let's be safe and fast.
        
        # Option C: Pygame's efficient C-backend for circles
        for x, y in screen_pos:
            pygame.draw.circle(self.screen, PARTICLE_COLOR, (x, y), 2)

        # UI
        fps = int(self.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps} | Particles: {N_PARTICLES} | g={GRAVITY}", True, (255, 255, 255))
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
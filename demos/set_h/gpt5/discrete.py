import math
import random
import time
import numpy as np
import pygame
from numba import njit, get_num_threads

# ============================================================
# Discrete-lattice “MD” experiment (Metropolis MC on lattice)
# ============================================================
"""
This simulation constrains particles to a 2D periodic square lattice.
On each step, particles attempt discrete moves to neighboring lattice sites.
Moves are accepted via a Metropolis criterion based on an interaction energy
computed from a selected potential model.

Features:
- Lattice positions: integer coordinates (x[i], y[i]) in [0, Lsites-1]
- Periodic boundaries: coordinates wrap modulo Lsites
- Multiplicity: multiple particles per site allowed (optional single-occupancy)
- Interaction models (choose with FORCE_MODEL):
  - "LJ": Lennard-Jones-like energy U(r) = 4ε[(σ/r)^12 − (σ/r)^6], tabulated in r^2
  - "TAB_LJ": Same tabulation; kept for parity with your previous code
  - "QUAD": Piecewise quadratic U(r2) approximation (cheap)
- Neighbor handling: pair list built from cell grid; Verlet-like rebuild using
  a “skin” in lattice steps (r_skin_sites). Rebuild when any particle’s
  displacement since last build exceeds r_skin_sites/2 (Manhattan distance).
- Temperature T controls Metropolis acceptance probability exp(-ΔE/T).
- Pygame visualization with draw-skipping and steps/sec metric.

Controls:
- SPACE: toggle running (pause/resume)
- ESC: quit
- D: toggle draw skipping
- Up/Down: increase/decrease draw_every_M (MC sweeps between draws)
- 1/2/3: select potential model (LJ / TAB_LJ / QUAD)
- T/G: increase/decrease temperature by 10%
- R/F: increase/decrease r_skin_sites by 1 (forces neighbor rebuild)
- V: toggle displacement-based rebuild vs periodic rebuild
- H: toggle extra diagnostics

Notes:
- This is a lattice Monte Carlo experiment, not Newtonian MD.
- Energies are computed via pairwise potential with cutoff r_cut_sites.
- Performance tips: increase draw_every_M for higher steps/sec, keep radius small, and use QUAD potential for speed.
"""

# ============================================================
# Simulation parameters
# ============================================================
N = 1000                 # number of particles
Lsites = 256             # lattice size (Lsites x Lsites)
FORCE_MODEL = "LJ"       # "LJ", "TAB_LJ", "QUAD"
SINGLE_OCCUPANCY = False # if True, moves into occupied sites are rejected
running = True           # SPACE toggles

# Potential parameters (dimensionless lattice units)
epsilon = np.float32(1.0)
sigma = np.float32(1.0)  # in lattice units
r_cut_sites = 8          # cutoff radius in lattice steps
r_cut2 = np.int32(r_cut_sites * r_cut_sites)

# Temperature for Metropolis acceptance
T = np.float32(1.0)

# Verlet-like neighbor rebuild (in lattice steps)
r_skin_sites = 2  # allow modest displacement before rebuild
use_displacement_rebuild = True  # V toggles; if False, periodic rebuild by interval
rebuild_interval = 20

# Move set: von Neumann 4-neighborhood or Moore 8-neighborhood
USE_MOORE = False
if USE_MOORE:
    MOVE_SET = np.array([[-1, -1], [-1, 0], [-1, 1],
                         [ 0, -1],           [ 0, 1],
                         [ 1, -1], [ 1, 0], [ 1, 1]], dtype=np.int32)
else:
    MOVE_SET = np.array([[-1, 0],
                         [ 1, 0],
                         [ 0, -1],
                         [ 0, 1]], dtype=np.int32)

# Visualization
WINDOW_W = 900
WINDOW_H = 900
MARGIN = 40
scale = (WINDOW_W - 2 * MARGIN) / float(Lsites)
particle_draw_radius = 2
background_color = (8, 10, 14)
particle_color = (90, 200, 255)
text_color = (230, 230, 230)
fps_limit = 0  # unlimited

# Draw skipping
draw_skip_enabled = True
draw_every_M = 10
show_extra_diag = True

# Cell grid for neighbor building
cell_size_sites = 8  # cell size in lattice steps
ncell_x = max(1, Lsites // cell_size_sites)
ncell_y = max(1, Lsites // cell_size_sites)

# ============================================================
# Pre-tabulated potentials (as functions of r^2)
# ============================================================
@njit(fastmath=True)
def lj_energy_from_r2(r2, sigma, epsilon):
    # U = 4ε[(σ/r)^12 − (σ/r)^6]
    sigma2 = sigma * sigma
    inv_r2 = np.float32(1.0) / np.float32(r2)
    s2_over_r2 = sigma2 * inv_r2
    inv_r6 = s2_over_r2 * s2_over_r2 * s2_over_r2
    inv_r12 = inv_r6 * inv_r6
    return np.float32(4.0) * epsilon * (inv_r12 - inv_r6)

@njit(fastmath=True)
def quad_energy_from_r2(r2, sigma2, r_a2, r_cut2, a_rep, a_att_mid, a_att_tail):
    # Cheap piecewise quadratic “energy” with LJ-like shape
    if r2 < sigma2:
        return a_rep * (np.float32(1.0) - r2 / sigma2)
    elif r2 < r_a2:
        return -a_att_mid * (r2 - sigma2) / (r_a2 - sigma2)
    elif r2 < r_cut2:
        return -a_att_tail * (np.float32(1.0) - (r2 - r_a2) / (r_cut2 - r_a2))
    else:
        return np.float32(0.0)

def build_energy_table(model_name, r_cut2, sigma, epsilon):
    # Build a small table U_table[r2] for r2 = 0..r_cut2
    U = np.zeros(r_cut2 + 1, dtype=np.float32)
    sigma2 = np.float32(sigma * sigma)
    r_a = np.float32(1.2) * sigma
    r_a2 = np.float32(r_a * r_a)
    a_rep = np.float32(1.5) * epsilon
    a_att_mid = np.float32(0.2) * epsilon
    a_att_tail = np.float32(0.08) * epsilon
    for r2 in range(1, r_cut2 + 1):
        if model_name in ("LJ", "TAB_LJ"):
            U[r2] = lj_energy_from_r2(np.int32(r2), sigma, epsilon)
        else:
            U[r2] = quad_energy_from_r2(np.int32(r2), sigma2, r_a2, np.int32(r_cut2), a_rep, a_att_mid, a_att_tail)
    return U

# Initial energy table
U_table = build_energy_table(FORCE_MODEL, r_cut2, sigma, epsilon)

# ============================================================
# Lattice utilities and neighbor handling
# ============================================================
@njit(fastmath=True)
def wrap_site(v, Lsites):
    # wrap integer site index into [0, Lsites-1]
    if v >= Lsites:
        v = v % Lsites
    elif v < 0:
        v = Lsites - ((-v) % Lsites)
        if v == Lsites:
            v = 0
    return v

@njit(fastmath=True)
def compute_max_manhattan_disp(x, y, last_x, last_y, Lsites):
    max_d = 0
    for i in range(x.shape[0]):
        dx = x[i] - last_x[i]
        dy = y[i] - last_y[i]
        # periodic wrap in manhattan metric
        adx = abs(dx)
        ady = abs(dy)
        if adx > Lsites - adx: adx = Lsites - adx
        if ady > Lsites - ady: ady = Lsites - ady
        d = adx + ady
        if d > max_d:
            max_d = d
    return max_d

@njit(fastmath=True)
def build_cell_heads(x, y, Lsites, cell_size_sites, ncell_x, ncell_y):
    heads = np.full((ncell_x, ncell_y), -1, dtype=np.int32)
    next_idx = np.full(x.shape[0], -1, dtype=np.int32)
    for i in range(x.shape[0]):
        cx = (x[i] // cell_size_sites) % ncell_x
        cy = (y[i] // cell_size_sites) % ncell_y
        next_idx[i] = heads[cx, cy]
        heads[cx, cy] = i
    return heads, next_idx

@njit(fastmath=True)
def build_neighbor_pairs_lattice(x, y, Lsites, r_list2, cell_size_sites, ncell_x, ncell_y, pair_i, pair_j):
    heads, next_idx = build_cell_heads(x, y, Lsites, cell_size_sites, ncell_x, ncell_y)
    halfL = Lsites // 2
    count = 0
    for cx in range(ncell_x):
        for cy in range(ncell_y):
            ii = heads[cx, cy]
            while ii != -1:
                xi = x[ii]
                yi = y[ii]
                for dxcell in (-1, 0, 1):
                    ncx = (cx + dxcell) % ncell_x
                    for dycell in (-1, 0, 1):
                        ncy = (cy + dycell) % ncell_y
                        jj = heads[ncx, ncy]
                        while jj != -1:
                            if jj > ii:
                                dx = xi - x[jj]
                                dy = yi - y[jj]
                                if dx > halfL: dx -= Lsites
                                elif dx < -halfL: dx += Lsites
                                if dy > halfL: dy -= Lsites
                                elif dy < -halfL: dy += Lsites
                                r2 = dx*dx + dy*dy
                                if r2 <= r_list2 and r2 > 0:
                                    pair_i[count] = ii
                                    pair_j[count] = jj
                                    count += 1
                            jj = next_idx[jj]
                ii = next_idx[ii]
    return count

# ============================================================
# Energy and Metropolis step kernels
# ============================================================
@njit(fastmath=True)
def total_energy_pairs(x, y, U_table, r_cut2, pair_i, pair_j, pair_count, Lsites):
    E = np.float32(0.0)
    halfL = Lsites // 2
    for idx in range(pair_count):
        i = pair_i[idx]
        j = pair_j[idx]
        dx = x[i] - x[j]
        dy = y[i] - y[j]
        if dx > halfL: dx -= Lsites
        elif dx < -halfL: dx += Lsites
        if dy > halfL: dy -= Lsites
        elif dy < -halfL: dy += Lsites
        r2 = dx*dx + dy*dy
        if 0 < r2 <= r_cut2:
            E += U_table[r2]
    return E

@njit(fastmath=True)
def propose_move_index(i, x, y, move_set, Lsites):
    # pick a random move from move_set (Numba-compatible)
    m = np.random.randint(0, move_set.shape[0])
    dx = int(move_set[m, 0])
    dy = int(move_set[m, 1])
    newx = x[i] + dx
    newy = y[i] + dy
    if newx >= Lsites: newx -= Lsites
    elif newx < 0: newx += Lsites
    if newy >= Lsites: newy -= Lsites
    elif newy < 0: newy += Lsites
    return newx, newy

@njit(fastmath=True)
def mc_sweep(
    x, y,
    U_table, r_cut2,
    move_set,
    Lsites,
    T,
    single_occupancy,
    occ_grid
):
    accepts = 0
    N = x.shape[0]
    halfL = Lsites // 2
    for _ in range(N):
        i = np.random.randint(0, N)
        oldx = x[i]
        oldy = y[i]
        newx, newy = propose_move_index(i, x, y, move_set, Lsites)
        # occupancy check
        if single_occupancy:
            if occ_grid[newx, newy] > 0 and not (newx == oldx and newy == oldy):
                continue  # reject move into occupied site
        # ΔE: sum against all particles, with cutoff (simple but numba-fast)
        dE = np.float32(0.0)
        for j in range(N):
            if j == i:
                continue
            dx_old = oldx - x[j]
            dy_old = oldy - y[j]
            if dx_old > halfL: dx_old -= Lsites
            elif dx_old < -halfL: dx_old += Lsites
            if dy_old > halfL: dy_old -= Lsites
            elif dy_old < -halfL: dy_old += Lsites
            r2_old = dx_old*dx_old + dy_old*dy_old
            if 0 < r2_old <= r_cut2:
                dE -= U_table[r2_old]
            dx_new = newx - x[j]
            dy_new = newy - y[j]
            if dx_new > halfL: dx_new -= Lsites
            elif dx_new < -halfL: dx_new += Lsites
            if dy_new > halfL: dy_new -= Lsites
            elif dy_new < -halfL: dy_new += Lsites
            r2_new = dx_new*dx_new + dy_new*dy_new
            if 0 < r2_new <= r_cut2:
                dE += U_table[r2_new]
        # Metropolis accept
        if dE <= 0.0 or (np.random.random() < math.exp(-float(dE)/float(T))):
            if single_occupancy:
                occ_grid[oldx, oldy] -= 1
                occ_grid[newx, newy] += 1
            x[i] = newx
            y[i] = newy
            accepts += 1
    return accepts

# ============================================================
# Initialization
# ============================================================
def init_lattice_positions(N, Lsites):
    # Place on a coarse lattice grid uniformly
    x = np.zeros(N, dtype=np.int32)
    y = np.zeros(N, dtype=np.int32)
    i = 0
    step = max(1, Lsites // int(math.sqrt(N)))
    for yy in range(0, Lsites, step):
        for xx in range(0, Lsites, step):
            if i >= N:
                break
            x[i] = xx % Lsites
            y[i] = yy % Lsites
            i += 1
        if i >= N:
            break
    # If not enough, fill randomly (Python side, not jitted)
    rng = np.random.default_rng()
    while i < N:
        xx = int(rng.integers(0, Lsites))
        yy = int(rng.integers(0, Lsites))
        x[i] = xx
        y[i] = yy
        i += 1
    return x, y

x_sites, y_sites = init_lattice_positions(N, Lsites)

# Track last positions for displacement-based rebuild
last_x = x_sites.copy()
last_y = y_sites.copy()

# Optional occupancy grid (only used if SINGLE_OCCUPANCY = True)
occ_grid = np.zeros((Lsites, Lsites), dtype=np.int32)
if SINGLE_OCCUPANCY:
    for i in range(N):
        occ_grid[x_sites[i] % Lsites, y_sites[i] % Lsites] += 1

# ============================================================
# Pygame helpers
# ============================================================
def sim_to_screen(ix, iy):
    sx = MARGIN + float(ix) * scale
    sy = MARGIN + float(iy) * scale
    return int(sx), int(sy)

def draw_particles(screen, x, y):
    for i in range(x.shape[0]):
        sx, sy = sim_to_screen(x[i], y[i])
        pygame.draw.circle(screen, particle_color, (sx, sy), particle_draw_radius)

def draw_box(screen):
    rect = pygame.Rect(MARGIN, MARGIN, int(float(Lsites) * scale), int(float(Lsites) * scale))
    pygame.draw.rect(screen, (80, 80, 90), rect, width=2)

def draw_text(screen, font, text, x, y):
    surf = font.render(text, True, text_color)
    screen.blit(surf, (x, y))

# ============================================================
# Main
# ============================================================
def main():
    global FORCE_MODEL, U_table, running, draw_every_M, draw_skip_enabled, show_extra_diag
    global T, r_skin_sites, use_displacement_rebuild
    global last_x, last_y

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Discrete Lattice Dynamics (Metropolis) - LJ-like potentials (fixed)")
    font = pygame.font.SysFont("consolas", 18)
    clock = pygame.time.Clock()

    # Pair buffers (for neighbor-based energy/diagnostics if needed)
    max_pairs = 40 * N
    pair_i = np.zeros(max_pairs, dtype=np.int32)
    pair_j = np.zeros(max_pairs, dtype=np.int32)
    r_list2 = (r_cut_sites + r_skin_sites) * (r_cut_sites + r_skin_sites)

    # Initial neighbor build (for diagnostics/total energy display)
    pair_count = build_neighbor_pairs_lattice(x_sites, y_sites, Lsites, r_list2, cell_size_sites, ncell_x, ncell_y, pair_i, pair_j)
    last_rebuild_step = 0

    step = 0
    steps_counter = 0
    steps_start_time = time.time()
    steps_per_sec = 0.0

    while True:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    running = not running
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                elif event.key == pygame.K_d:
                    draw_skip_enabled = not draw_skip_enabled
                elif event.key == pygame.K_h:
                    show_extra_diag = not show_extra_diag
                elif event.key == pygame.K_UP:
                    draw_every_M = min(10000, draw_every_M + 1)
                elif event.key == pygame.K_DOWN:
                    draw_every_M = max(1, draw_every_M - 1)
                elif event.key == pygame.K_1:
                    FORCE_MODEL = "LJ"; U_table = build_energy_table(FORCE_MODEL, r_cut2, sigma, epsilon)
                elif event.key == pygame.K_2:
                    FORCE_MODEL = "TAB_LJ"; U_table = build_energy_table(FORCE_MODEL, r_cut2, sigma, epsilon)
                elif event.key == pygame.K_3:
                    FORCE_MODEL = "QUAD"; U_table = build_energy_table(FORCE_MODEL, r_cut2, sigma, epsilon)
                elif event.key == pygame.K_t:
                    T *= np.float32(1.1)
                elif event.key == pygame.K_g:
                    T *= np.float32(0.9)
                elif event.key == pygame.K_r:
                    r_skin_sites = min(32, r_skin_sites + 1)
                    r_list2 = (r_cut_sites + r_skin_sites) * (r_cut_sites + r_skin_sites)
                    pair_count = build_neighbor_pairs_lattice(x_sites, y_sites, Lsites, r_list2, cell_size_sites, ncell_x, ncell_y, pair_i, pair_j)
                    last_rebuild_step = step
                    last_x[:] = x_sites
                    last_y[:] = y_sites
                elif event.key == pygame.K_f:
                    r_skin_sites = max(0, r_skin_sites - 1)
                    r_list2 = (r_cut_sites + r_skin_sites) * (r_cut_sites + r_skin_sites)
                    pair_count = build_neighbor_pairs_lattice(x_sites, y_sites, Lsites, r_list2, cell_size_sites, ncell_x, ncell_y, pair_i, pair_j)
                    last_rebuild_step = step
                    last_x[:] = x_sites
                    last_y[:] = y_sites
                elif event.key == pygame.K_v:
                    use_displacement_rebuild = not use_displacement_rebuild

        # Advance simulation
        nsteps = draw_every_M if draw_skip_enabled else 1
        if running:
            for _ in range(nsteps):
                # Perform one Monte Carlo sweep
                accepts = mc_sweep(
                    x_sites, y_sites,
                    U_table, r_cut2,
                    MOVE_SET,
                    Lsites,
                    T,
                    SINGLE_OCCUPANCY,
                    occ_grid
                )
                step += 1
                steps_counter += 1

                # Neighbor rebuild policy
                if use_displacement_rebuild:
                    max_d = compute_max_manhattan_disp(x_sites, y_sites, last_x, last_y, Lsites)
                    if max_d >= max(1, r_skin_sites // 2):
                        pair_count = build_neighbor_pairs_lattice(x_sites, y_sites, Lsites, r_list2, cell_size_sites, ncell_x, ncell_y, pair_i, pair_j)
                        last_x[:] = x_sites
                        last_y[:] = y_sites
                        last_rebuild_step = step
                else:
                    if (step - last_rebuild_step) >= rebuild_interval:
                        pair_count = build_neighbor_pairs_lattice(x_sites, y_sites, Lsites, r_list2, cell_size_sites, ncell_x, ncell_y, pair_i, pair_j)
                        last_rebuild_step = step
                        last_x[:] = x_sites
                        last_y[:] = y_sites

        # Steps/sec metric
        now = time.time()
        elapsed = now - steps_start_time
        if elapsed >= 0.5:
            steps_per_sec = steps_counter / elapsed
            steps_counter = 0
            steps_start_time = now

        # Draw
        do_draw = True
        if draw_skip_enabled:
            do_draw = True  # draw once per loop after the batch
        if do_draw:
            screen.fill(background_color)
            draw_box(screen)
            draw_particles(screen, x_sites, y_sites)

            ytxt = 20
            draw_text(screen, font, f"Step: {step}", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"Steps/sec: {steps_per_sec:.0f}", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"Running: {'YES' if running else 'NO'} (SPACE)", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"Force model: {FORCE_MODEL} (1=LJ, 2=TAB_LJ, 3=QUAD)", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"T (temperature): {float(T):.3f} (T/G +/-10%)", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"Draw every M: {draw_every_M} (D toggle, Up/Down adjust)", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"r_cut_sites: {r_cut_sites}, r_skin_sites: {r_skin_sites} (R/F +/-1)", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"Pair rebuild: {'displacement' if use_displacement_rebuild else 'periodic'} (V toggle)", 20, ytxt); ytxt += 20
            draw_text(screen, font, f"pair_count (r_list2): {pair_count}", 20, ytxt); ytxt += 20
            if show_extra_diag:
                # Show an estimate of current total energy over current pair list
                E = float(total_energy_pairs(x_sites, y_sites, U_table, r_cut2, pair_i, pair_j, pair_count, Lsites))
                ytxt += 10
                draw_text(screen, font, f"Estimated E (pair-list): {E:.2f}", 20, ytxt); ytxt += 20
                draw_text(screen, font, f"Lattice size: {Lsites} x {Lsites}, N: {N}", 20, ytxt); ytxt += 20
                draw_text(screen, font, f"Move set: {'Moore(8)' if USE_MOORE else 'von Neumann(4)'}", 20, ytxt); ytxt += 20
                draw_text(screen, font, f"Single occupancy: {'ON' if SINGLE_OCCUPANCY else 'OFF'}", 20, ytxt); ytxt += 20
                draw_text(screen, font, f"Threads (Numba): {get_num_threads()}", 20, ytxt); ytxt += 20

            pygame.display.flip()

        clock.tick(fps_limit)

if __name__ == "__main__":
    main()

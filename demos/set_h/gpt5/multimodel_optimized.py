import math
import random
import time

import numpy as np
import pygame
from numba import njit

# ============================================================
# Force model selection
# ============================================================
"""
ForceModel selection:

Set FORCE_MODEL to one of:
- "LJ": Classical truncated Lennard-Jones 12-6 force with cutoff r_cut.
        f_over_r = 24 * epsilon * (2*(sigma/r)^12 - (sigma/r)^6) * (1/r^2)
        Pros: Standard MD reference behavior.
        Cons: More expensive math per pair than simple polynomials.

- "TAB_LJ": Tabulated Lennard-Jones force with linear interpolation in r^2.
            We precompute a table of f_over_r(r^2) over [r_min^2, r_cut^2].
            At runtime we avoid sqrt: compute r2, index into the table, and linearly
            interpolate to get f_over_r, then multiply by (dx, dy).
            Pros: Cheaper than computing powers; no sqrt in the inner loop; smooth.
            Cons: Quality depends on table resolution; still reads the table.

- "QUAD": Piecewise quadratic approximation using r^2 (no sqrt, only multiplies/adds).
          Mimics repulsive core and attractive tail with simple functions of r^2.
          Pros: Very fast; simple; no transcendental functions.
          Cons: Not physically exact; parameters are heuristic.

How to select:
- Set FORCE_MODEL below to "LJ", "TAB_LJ", or "QUAD".
- You can switch at runtime:
    - Press 1 -> LJ
    - Press 2 -> TAB_LJ (r^2 tabulation)
    - Press 3 -> QUAD

Optional Verlet pair-list mode (modification #2):
- Set VERLET_MODE_ENABLED below to True to start with pair-list mode on.
- Toggle at runtime with key V.
- When enabled:
    - Build a flat pair list with list cutoff r_list = r_cut + r_skin
    - Recompute forces by iterating over pairs, faster than cell traversal
    - Rebuild list only when max displacement since last build exceeds r_skin / 2
- When disabled:
    - Use cell-linked list traversal each step (original approach)
"""

FORCE_MODEL = "TAB_LJ"
VERLET_MODE_ENABLED = False  # toggle with V at runtime

# ============================================================
# Simulation parameters (float32-compatible)
# ============================================================
N = 1000
sigma = np.float32(1.0)
epsilon = np.float32(1.0)
mass = np.float32(1.0)
dt = np.float32(0.002)
r_cut = np.float32(2.5) * sigma
r_cut2 = r_cut * r_cut
target_temp = np.float32(1.0)
thermostat = True
thermostat_steps = 2000
damping = np.float32(1.0)
density = np.float32(0.7)
L = np.float32(math.sqrt(N / float(density)))  # computed in float64 then cast

# Visualization parameters
WINDOW_W = 900
WINDOW_H = 900
MARGIN = 50
scale = (WINDOW_W - 2 * MARGIN) / float(L)
particle_draw_radius = 1  # small radius for faster drawing
background_color = (8, 10, 14)
particle_color = (90, 200, 255)
text_color = (230, 230, 230)
fps_limit = 0  # unlimited

# Draw skipping: draw only every Mth step
draw_skip_enabled = True
draw_every_M = 10  # adjustable at runtime

# Neighbor list / cell list parameters
cell_size = np.float32(1.05) * r_cut
ncell_x = max(1, int(float(L) // float(cell_size)))
ncell_y = max(1, int(float(L) // float(cell_size)))
rebuild_interval = 20  # used when not in Verlet mode

# ============================================================
# Tabulation settings (for TAB_LJ; r^2-based)
# ============================================================
# r_min avoids singularity near r=0. Use small fraction of sigma.
tab_r_min = np.float32(0.05) * sigma
tab_r2_min = tab_r_min * tab_r_min
tab_r2_max = r_cut2
tab_size = 2048  # number of samples in r^2 space
tab_dr2 = np.float32((float(tab_r2_max) - float(tab_r2_min)) / (tab_size - 1))
tab_r2 = np.linspace(float(tab_r2_min), float(tab_r2_max), tab_size, dtype=np.float32)
tab_f_over_r = np.zeros(tab_size, dtype=np.float32)

# ============================================================
# Verlet pair-list parameters (modification #2)
# ============================================================
r_skin = np.float32(0.3) * sigma
r_list = r_cut + r_skin
r_list2 = r_list * r_list

# Pair list arrays (allocated later)
# We'll store pairs in two int32 arrays: pair_i, pair_j, length pair_count
# Also track positions at last build and per-particle max displacement
# Rebuild when max_disp > r_skin / 2

# ============================================================
# Numba-jitted helpers (float32 + fastmath)
# ============================================================
@njit(fastmath=True)
def wrap_coord(x, L):
    if x >= L:
        x -= L * math.floor(x / L)
        if x >= L:
            x -= L
    elif x < np.float32(0.0):
        x += L * (1 + math.floor(-x / L))
        if x < np.float32(0.0):
            x += L
    return x

@njit(fastmath=True)
def min_image(dx, L):
    half = np.float32(0.5) * L
    if dx > half:
        dx -= L
    elif dx < -half:
        dx += L
    return dx

@njit(fastmath=True)
def kinetic_energy(vx, vy, mass):
    return np.float32(0.5) * mass * (vx * vx + vy * vy)

@njit(fastmath=True)
def compute_temperature(vels, mass):
    ke = np.float32(0.0)
    Nloc = vels.shape[0]
    for i in range(Nloc):
        ke += kinetic_energy(vels[i, 0], vels[i, 1], mass)
    return ke / np.float32(Nloc)

# -----------------------------
# Initialization (Python)
# -----------------------------
def init_lattice_positions(N, L):
    n_per_side = int(math.ceil(math.sqrt(N)))
    spacing = float(L) / n_per_side
    pos = np.zeros((N, 2), dtype=np.float32)
    count = 0
    for i in range(n_per_side):
        for j in range(n_per_side):
            if count >= N:
                break
            pos[count, 0] = np.float32((i + 0.5) * spacing)
            pos[count, 1] = np.float32((j + 0.5) * spacing)
            count += 1
        if count >= N:
            break
    return pos

def init_random_velocities(N, target_temp, mass):
    vels = np.zeros((N, 2), dtype=np.float32)
    for i in range(N):
        vels[i, 0] = np.float32(random.uniform(-1.0, 1.0))
        vels[i, 1] = np.float32(random.uniform(-1.0, 1.0))
    mean_vx = np.float32(np.mean(vels[:, 0]))
    mean_vy = np.float32(np.mean(vels[:, 1]))
    vels[:, 0] -= mean_vx
    vels[:, 1] -= mean_vy
    current_T = compute_temperature(vels, mass)
    if current_T > 0:
        scale_fac = np.float32(math.sqrt(float(target_temp / current_T)))
        vels *= scale_fac
    return vels

positions = init_lattice_positions(N, L)
velocities = init_random_velocities(N, target_temp, mass)
forces = np.zeros((N, 2), dtype=np.float32)

# ============================================================
# Fill r^2-tabulated LJ table
# ============================================================
@njit(fastmath=True)
def fill_tabulated_lj_r2(table_r2, table_f, sigma, epsilon):
    sigma2 = sigma * sigma
    for i in range(table_r2.shape[0]):
        r2 = table_r2[i]
        # Clamp very small r2 to avoid blow-up; we won't query below tab_r2_min anyway
        if r2 < np.float32(1e-12):
            r2 = np.float32(1e-12)
        inv_r2 = np.float32(1.0) / r2
        inv_r6 = (sigma2 * inv_r2) * (sigma2 * inv_r2) * (sigma2 * inv_r2)  # (sigma^2/r^2)^3
        inv_r12 = inv_r6 * inv_r6
        f_over_r = np.float32(24.0) * epsilon * (np.float32(2.0) * inv_r12 - inv_r6) * inv_r2
        table_f[i] = f_over_r

fill_tabulated_lj_r2(tab_r2, tab_f_over_r, sigma, epsilon)

# ============================================================
# Cell-linked list structures (int32 indices)
# ============================================================
@njit(fastmath=True)
def build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y):
    for cx in range(ncell_x):
        for cy in range(ncell_y):
            cell_heads[cx, cy] = -1
    inv_cell = np.float32(1.0) / cell_size
    Nloc = positions.shape[0]
    for i in range(Nloc):
        x = positions[i, 0]
        y = positions[i, 1]
        cx = int(x * inv_cell) % ncell_x
        cy = int(y * inv_cell) % ncell_y
        next_idx[i] = cell_heads[cx, cy]
        cell_heads[cx, cy] = i

# ============================================================
# Force kernels
# ============================================================
@njit(fastmath=True)
def force_LJ_from_r2(r2, sigma, epsilon):
    if r2 <= np.float32(0.0):
        return np.float32(0.0)
    inv_r2 = np.float32(1.0) / r2
    sigma2 = sigma * sigma
    # (sigma^2/r^2)^3 via multiplies
    s2_over_r2 = sigma2 * inv_r2
    inv_r6 = s2_over_r2 * s2_over_r2 * s2_over_r2
    inv_r12 = inv_r6 * inv_r6
    return np.float32(24.0) * epsilon * (np.float32(2.0) * inv_r12 - inv_r6) * inv_r2

@njit(fastmath=True)
def force_TAB_LJ_r2(f_table, r2, r2_min, r2_max, dr2):
    # Return scalar f_over_r via linear interpolation in r2; zero if r2 >= r2_max
    if r2 >= r2_max:
        return np.float32(0.0)
    if r2 < r2_min:
        r2 = r2_min
    t = (r2 - r2_min) / dr2
    i = int(t)
    if i >= f_table.shape[0] - 1:
        i = f_table.shape[0] - 2
        t = np.float32(i)
    frac = t - np.float32(i)
    return f_table[i] * (np.float32(1.0) - frac) + f_table[i + 1] * frac

@njit(fastmath=True)
def force_QUAD_from_r2(r2, sigma2, r_a2, r_cut2, k_rep, k_mid, k_tail):
    if r2 < sigma2:
        return k_rep * (np.float32(1.0) - r2 / sigma2)
    elif r2 < r_a2:
        return -k_mid * (r2 - sigma2) / (r_a2 - sigma2)
    elif r2 < r_cut2:
        return -k_tail * (np.float32(1.0) - (r2 - r_a2) / (r_cut2 - r_a2))
    else:
        return np.float32(0.0)

# ============================================================
# Force computation: cell traversal
# ============================================================
@njit(fastmath=True)
def compute_forces_cells_model(
    positions, forces, cell_heads, next_idx, L,
    model_id,  # 0=LJ, 1=TAB_LJ(r2), 2=QUAD
    sigma, epsilon, r_cut2,
    # r2-tabulation
    f_table, r2_min, r2_max, dr2,
    # quad params
    sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
    ncell_x, ncell_y
):
    Nloc = positions.shape[0]
    for i in range(Nloc):
        forces[i, 0] = np.float32(0.0)
        forces[i, 1] = np.float32(0.0)

    for cx in range(ncell_x):
        for cy in range(ncell_y):
            ii = cell_heads[cx, cy]
            while ii != -1:
                xi = positions[ii, 0]
                yi = positions[ii, 1]
                for dx_cell in (-1, 0, 1):
                    ncx = (cx + dx_cell) % ncell_x
                    for dy_cell in (-1, 0, 1):
                        ncy = (cy + dy_cell) % ncell_y
                        jj = cell_heads[ncx, ncy]
                        while jj != -1:
                            if jj > ii:
                                xj = positions[jj, 0]
                                yj = positions[jj, 1]
                                dx = xi - xj
                                dy = yi - yj
                                dx = min_image(dx, L)
                                dy = min_image(dy, L)
                                r2 = dx * dx + dy * dy
                                if r2 < r_cut2 and r2 > np.float32(1e-12):
                                    if model_id == 0:
                                        f_over_r = force_LJ_from_r2(r2, sigma, epsilon)
                                    elif model_id == 1:
                                        f_over_r = force_TAB_LJ_r2(f_table, r2, r2_min, r2_max, dr2)
                                    else:
                                        f_over_r = force_QUAD_from_r2(r2, sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail)
                                    fx = f_over_r * dx
                                    fy = f_over_r * dy
                                    forces[ii, 0] += fx
                                    forces[ii, 1] += fy
                                    forces[jj, 0] -= fx
                                    forces[jj, 1] -= fy
                            jj = next_idx[jj]
                ii = next_idx[ii]

# ============================================================
# Verlet pair-list building and force computation
# ============================================================
@njit(fastmath=True)
def compute_max_displacement(positions, last_positions, disp_abs, L):
    Nloc = positions.shape[0]
    max_disp = np.float32(0.0)
    for i in range(Nloc):
        dx = positions[i, 0] - last_positions[i, 0]
        dy = positions[i, 1] - last_positions[i, 1]
        dx = min_image(dx, L)
        dy = min_image(dy, L)
        d2 = dx * dx + dy * dy
        # store absolute displacement magnitude (sqrt avoided; compare squared)
        disp_abs[i] = d2
        if d2 > max_disp:
            max_disp = d2
    return max_disp

@njit(fastmath=True)
def build_verlet_pairs(positions, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j):
    # Build pairs using cell-linked traversal but store flat pair arrays
    # Returns pair_count
    # First, build cell heads for list cutoff r_list (we reuse cell_size and grid)
    cell_heads = np.full((ncell_x, ncell_y), -1, dtype=np.int32)
    next_idx = np.full(positions.shape[0], -1, dtype=np.int32)
    build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)

    count = 0
    for cx in range(ncell_x):
        for cy in range(ncell_y):
            ii = cell_heads[cx, cy]
            while ii != -1:
                xi = positions[ii, 0]
                yi = positions[ii, 1]
                for dx_cell in (-1, 0, 1):
                    ncx = (cx + dx_cell) % ncell_x
                    for dy_cell in (-1, 0, 1):
                        ncy = (cy + dy_cell) % ncell_y
                        jj = cell_heads[ncx, ncy]
                        while jj != -1:
                            if jj > ii:
                                xj = positions[jj, 0]
                                yj = positions[jj, 1]
                                dx = min_image(xi - xj, L)
                                dy = min_image(yi - yj, L)
                                r2 = dx * dx + dy * dy
                                if r2 < r_list2:
                                    pair_i[count] = ii
                                    pair_j[count] = jj
                                    count += 1
                            jj = next_idx[jj]
                ii = next_idx[ii]
    return count

@njit(fastmath=True)
def compute_forces_pairs(
    positions, forces,
    pair_i, pair_j, pair_count, L,
    model_id, sigma, epsilon, r_cut2, r_list2,
    f_table, r2_min, r2_max, dr2,
    sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail
):
    # Zero forces
    Nloc = positions.shape[0]
    for i in range(Nloc):
        forces[i, 0] = np.float32(0.0)
        forces[i, 1] = np.float32(0.0)

    for idx in range(pair_count):
        i = pair_i[idx]
        j = pair_j[idx]
        dx = positions[i, 0] - positions[j, 0]
        dy = positions[i, 1] - positions[j, 1]
        dx = min_image(dx, L)
        dy = min_image(dy, L)
        r2 = dx * dx + dy * dy
        if r2 < r_cut2 and r2 > np.float32(1e-12):
            if model_id == 0:
                f_over_r = force_LJ_from_r2(r2, sigma, epsilon)
            elif model_id == 1:
                f_over_r = force_TAB_LJ_r2(f_table, r2, r2_min, r2_max, dr2)
            else:
                f_over_r = force_QUAD_from_r2(r2, sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail)
            fx = f_over_r * dx
            fy = f_over_r * dy
            forces[i, 0] += fx
            forces[i, 1] += fy
            forces[j, 0] -= fx
            forces[j, 1] -= fy

# ============================================================
# Integration
# ============================================================
@njit(fastmath=True)
def integrate_half(positions, velocities, forces, L, dt, mass):
    half_dt = np.float32(0.5) * dt
    dt2_over2m = np.float32(0.5) * dt * dt / mass
    Nloc = positions.shape[0]
    for i in range(Nloc):
        xi = positions[i, 0]
        yi = positions[i, 1]
        vxi = velocities[i, 0]
        vyi = velocities[i, 1]
        fxi = forces[i, 0]
        fyi = forces[i, 1]

        xi += vxi * dt + fxi * dt2_over2m
        yi += vyi * dt + fyi * dt2_over2m

        xi = wrap_coord(xi, L)
        yi = wrap_coord(yi, L)

        positions[i, 0] = xi
        positions[i, 1] = yi

        vxi += (fxi / mass) * half_dt
        vyi += (fyi / mass) * half_dt
        velocities[i, 0] = vxi
        velocities[i, 1] = vyi

@njit(fastmath=True)
def finish_velocity_update(velocities, forces, dt, mass):
    half_dt = np.float32(0.5) * dt
    Nloc = velocities.shape[0]
    for i in range(Nloc):
        velocities[i, 0] += (forces[i, 0] / mass) * half_dt
        velocities[i, 1] += (forces[i, 1] / mass) * half_dt

@njit(fastmath=True)
def apply_thermostat_numba(velocities, target_temp, mass, mix):
    current_T = compute_temperature(velocities, mass)
    if current_T <= np.float32(0.0):
        return
    scale_fac = np.float32(math.sqrt(float(target_temp / current_T)))
    a = mix
    if a > np.float32(1.0):
        a = np.float32(1.0)
    elif a < np.float32(0.0):
        a = np.float32(0.0)
    Nloc = velocities.shape[0]
    for i in range(Nloc):
        vx = velocities[i, 0]
        vy = velocities[i, 1]
        velocities[i, 0] = vx * (np.float32(1.0) - a) + vx * scale_fac * a
        velocities[i, 1] = vy * (np.float32(1.0) - a) + vy * scale_fac * a

# ============================================================
# Pygame visualization helpers
# ============================================================
def sim_to_screen(x, y):
    sx = MARGIN + float(x) * scale
    sy = MARGIN + float(y) * scale
    return int(sx), int(sy)

def draw_particles(screen, positions):
    for i in range(positions.shape[0]):
        sx, sy = sim_to_screen(positions[i, 0], positions[i, 1])
        pygame.draw.circle(screen, particle_color, (sx, sy), particle_draw_radius)

def draw_box(screen):
    rect = pygame.Rect(MARGIN, MARGIN, int(float(L) * scale), int(float(L) * scale))
    pygame.draw.rect(screen, (80, 80, 90), rect, width=2)

def draw_text(screen, font, text, x, y):
    surf = font.render(text, True, text_color)
    screen.blit(surf, (x, y))

# ============================================================
# Model mapping and QUAD params
# ============================================================
def model_name_to_id(name):
    if name == "LJ":
        return 0
    elif name == "TAB_LJ":
        return 1
    elif name == "QUAD":
        return 2
    else:
        return 0

sigma2_q = sigma * sigma
r_a = np.float32(1.2) * sigma  # anchor near LJ minimum ~1.122 sigma
r_a2 = r_a * r_a
r_cut2_q = r_cut2
k_rep = np.float32(1000.0) * epsilon  # you tuned this high; steep core
k_mid = np.float32(4.0) * epsilon
k_tail = np.float32(1.5) * epsilon

# ============================================================
# Main loop
# ============================================================
def main():
    global draw_every_M, draw_skip_enabled, thermostat, FORCE_MODEL, VERLET_MODE_ENABLED

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("2D MD - Numba float32, selectable force models, r2-tabulated LJ, Verlet pairs")
    font = pygame.font.SysFont("consolas", 18)
    clock = pygame.time.Clock()

    # Preallocate cell-linked list arrays
    cell_heads = np.full((ncell_x, ncell_y), -1, dtype=np.int32)
    next_idx = np.full(N, -1, dtype=np.int32)

    # Pair list buffers: worst-case pairs ~ few neighbors per particle.
    # Conservatively allocate up to 20*N pairs; adjust if needed.
    max_pairs = 20 * N
    pair_i = np.zeros(max_pairs, dtype=np.int32)
    pair_j = np.zeros(max_pairs, dtype=np.int32)
    pair_count = 0

    # Track positions at last list build and displacement
    last_positions = positions.copy()
    disp_abs = np.zeros(N, dtype=np.float32)  # store squared displacement per particle

    # Initial neighbor build and forces
    build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
    model_id = model_name_to_id(FORCE_MODEL)

    # If starting in Verlet mode, build pair list
    if VERLET_MODE_ENABLED:
        pair_count = build_verlet_pairs(positions, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
        last_positions[:] = positions

        compute_forces_pairs(
            positions, forces,
            pair_i, pair_j, pair_count, L,
            model_id, sigma, epsilon, r_cut2, r_list2,
            tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
            sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail
        )
    else:
        compute_forces_cells_model(
            positions, forces, cell_heads, next_idx, L,
            model_id,
            sigma, epsilon, r_cut2,
            tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
            sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
            ncell_x, ncell_y
        )

    step = 0
    last_rebuild = 0  # used for cell traversal mode

    # Steps/sec measurement (independent of drawing)
    steps_counter = 0
    steps_start_time = time.time()
    steps_per_sec = 0.0

    # Warm up JIT to avoid first-step stutter
    integrate_half(positions, velocities, forces, L, dt, mass)
    if VERLET_MODE_ENABLED:
        pair_count = build_verlet_pairs(positions, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
        last_positions[:] = positions
        compute_forces_pairs(
            positions, forces,
            pair_i, pair_j, pair_count, L,
            model_id, sigma, epsilon, r_cut2, r_list2,
            tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
            sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail
        )
    else:
        build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
        compute_forces_cells_model(
            positions, forces, cell_heads, next_idx, L,
            model_id,
            sigma, epsilon, r_cut2,
            tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
            sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
            ncell_x, ncell_y
        )
    finish_velocity_update(velocities, forces, dt, mass)

    while True:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    thermostat = not thermostat
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                elif event.key == pygame.K_d:
                    draw_skip_enabled = not draw_skip_enabled
                elif event.key == pygame.K_UP:
                    draw_every_M = min(1000, draw_every_M + 1)
                elif event.key == pygame.K_DOWN:
                    draw_every_M = max(1, draw_every_M - 1)
                elif event.key == pygame.K_1:
                    FORCE_MODEL = "LJ"
                    model_id = 0
                elif event.key == pygame.K_2:
                    FORCE_MODEL = "TAB_LJ"
                    model_id = 1
                elif event.key == pygame.K_3:
                    FORCE_MODEL = "QUAD"
                    model_id = 2
                elif event.key == pygame.K_v:
                    VERLET_MODE_ENABLED = not VERLET_MODE_ENABLED
                    # Force immediate rebuild of structures to switch modes cleanly
                    last_rebuild = -rebuild_interval
                    last_positions[:] = positions
                    pair_count = 0

        # MD step
        integrate_half(positions, velocities, forces, L, dt, mass)

        if VERLET_MODE_ENABLED:
            # Rebuild if max displacement since last build exceeds (r_skin / 2)^2
            max_disp2 = compute_max_displacement(positions, last_positions, disp_abs, L)
            threshold2 = (np.float32(0.5) * r_skin) * (np.float32(0.5) * r_skin)
            if max_disp2 >= threshold2 or pair_count == 0:
                pair_count = build_verlet_pairs(positions, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
                last_positions[:] = positions

            compute_forces_pairs(
                positions, forces,
                pair_i, pair_j, pair_count, L,
                model_id, sigma, epsilon, r_cut2, r_list2,
                tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
                sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail
            )
        else:
            # Cell traversal mode with periodic rebuild
            if (step - last_rebuild) >= rebuild_interval:
                build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
                last_rebuild = step

            compute_forces_cells_model(
                positions, forces, cell_heads, next_idx, L,
                model_id,
                sigma, epsilon, r_cut2,
                tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
                sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
                ncell_x, ncell_y
            )

        finish_velocity_update(velocities, forces, dt, mass)

        if thermostat and step < thermostat_steps:
            apply_thermostat_numba(velocities, target_temp, mass, mix=damping)

        # Steps/sec measurement
        steps_counter += 1
        now = time.time()
        elapsed = now - steps_start_time
        if elapsed >= 0.5:
            steps_per_sec = steps_counter / elapsed
            steps_counter = 0
            steps_start_time = now

        # Render occasionally
        do_draw = True
        if draw_skip_enabled:
            do_draw = (step % draw_every_M == 0)

        if do_draw:
            screen.fill(background_color)
            draw_box(screen)
            draw_particles(screen, positions)

            T = float(compute_temperature(velocities, mass))
            draw_text(screen, font, f"Step: {step}", 20, 20)
            draw_text(screen, font, f"T: {T:.3f}", 20, 40)
            draw_text(screen, font, f"Steps/sec: {steps_per_sec:.0f}", 20, 60)
            draw_text(screen, font, f"Thermostat: {'ON' if (thermostat and step < thermostat_steps) else 'OFF'} (SPACE)", 20, 80)
            draw_text(screen, font, f"Draw every M: {draw_every_M} (D toggle, Up/Down adjust)", 20, 100)
            draw_text(screen, font, f"Force model: {FORCE_MODEL} (1=LJ, 2=TAB_LJ r2, 3=QUAD)", 20, 120)
            draw_text(screen, font, f"Verlet pairs: {'ON' if VERLET_MODE_ENABLED else 'OFF'} (V toggle)", 20, 140)

            pygame.display.flip()

        clock.tick(fps_limit)  # unlimited
        step += 1

if __name__ == "__main__":
    main()

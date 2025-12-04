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

- "TAB_LJ": Tabulated Lennard-Jones force with linear interpolation in r^2.
            We precompute f_over_r(r^2) over [r_min^2, r_cut^2].
            Runtime uses r2 directly (no sqrt), indexes into the table, and linearly
            interpolates to get f_over_r.

- "QUAD": Piecewise quadratic approximation using r^2 (no sqrt, only multiplies/adds).
          Three regions mimic repulsive core and attractive tail:
            [0, sigma^2), [sigma^2, r_a^2), [r_a^2, r_cut^2)

How to select:
- Set FORCE_MODEL below to "LJ", "TAB_LJ", or "QUAD".
- Switch at runtime:
    - 1 -> LJ
    - 2 -> TAB_LJ (r^2 tabulation)
    - 3 -> QUAD

Verlet pair-list mode:
- VERLET_MODE_ENABLED below chooses whether to start with pair-list mode on.
- Toggle with key V.
- When enabled:
    - Uses a fused Numba kernel that performs multiple MD steps per call in pair-list mode
    - Rebuilds the pair list only when max displacement since last build exceeds r_skin/2
- When disabled:
    - Falls back to cell-linked list traversal each step
"""

FORCE_MODEL = "LJ"
VERLET_MODE_ENABLED = True  # toggle with V at runtime

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
L = np.float32(math.sqrt(N / float(density)))  # compute in float64 then cast

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
draw_every_M = 10  # adjustable at runtime; also used as nsteps per fused kernel call

# Neighbor list / cell list parameters
cell_size = np.float32(1.05) * r_cut
ncell_x = max(1, int(float(L) // float(cell_size)))
ncell_y = max(1, int(float(L) // float(cell_size)))
rebuild_interval = 20  # used when not in Verlet mode

# ============================================================
# Tabulation settings (for TAB_LJ; r^2-based)
# ============================================================
tab_r_min = np.float32(0.05) * sigma
tab_r2_min = tab_r_min * tab_r_min
tab_r2_max = r_cut2
tab_size = 2048
tab_dr2 = np.float32((float(tab_r2_max) - float(tab_r2_min)) / (tab_size - 1))
tab_r2 = np.linspace(float(tab_r2_min), float(tab_r2_max), tab_size, dtype=np.float32)
tab_f_over_r = np.zeros(tab_size, dtype=np.float32)

# ============================================================
# Verlet pair-list parameters
# ============================================================
r_skin = np.float32(0.3) * sigma
r_list = r_cut + r_skin
r_list2 = r_list * r_list

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
def compute_temperature_soa(vel_x, vel_y, mass):
    ke = np.float32(0.0)
    Nloc = vel_x.shape[0]
    for i in range(Nloc):
        ke += np.float32(0.5) * mass * (vel_x[i] * vel_x[i] + vel_y[i] * vel_y[i])
    return ke / np.float32(Nloc)

# -----------------------------
# Initialization (Python)
# -----------------------------
def init_lattice_positions_soa(N, L):
    n_per_side = int(math.ceil(math.sqrt(N)))
    spacing = float(L) / n_per_side
    pos_x = np.zeros(N, dtype=np.float32)
    pos_y = np.zeros(N, dtype=np.float32)
    count = 0
    for i in range(n_per_side):
        for j in range(n_per_side):
            if count >= N:
                break
            pos_x[count] = np.float32((i + 0.5) * spacing)
            pos_y[count] = np.float32((j + 0.5) * spacing)
            count += 1
        if count >= N:
            break
    return pos_x, pos_y

def init_random_velocities_soa(N, target_temp, mass):
    vel_x = np.zeros(N, dtype=np.float32)
    vel_y = np.zeros(N, dtype=np.float32)
    for i in range(N):
        vel_x[i] = np.float32(random.uniform(-1.0, 1.0))
        vel_y[i] = np.float32(random.uniform(-1.0, 1.0))
    mean_vx = np.float32(np.mean(vel_x))
    mean_vy = np.float32(np.mean(vel_y))
    vel_x -= mean_vx
    vel_y -= mean_vy
    # Scale to target temp
    ke = np.float32(0.0)
    for i in range(N):
        ke += np.float32(0.5) * mass * (vel_x[i] * vel_x[i] + vel_y[i] * vel_y[i])
    current_T = ke / np.float32(N)
    if current_T > 0:
        scale_fac = np.float32(math.sqrt(float(target_temp / current_T)))
        vel_x *= scale_fac
        vel_y *= scale_fac
    return vel_x, vel_y

pos_x, pos_y = init_lattice_positions_soa(N, L)
vel_x, vel_y = init_random_velocities_soa(N, target_temp, mass)
force_x = np.zeros(N, dtype=np.float32)
force_y = np.zeros(N, dtype=np.float32)

# ============================================================
# Fill r^2-tabulated LJ table
# ============================================================
@njit(fastmath=True)
def fill_tabulated_lj_r2(table_r2, table_f, sigma, epsilon):
    sigma2 = sigma * sigma
    for i in range(table_r2.shape[0]):
        r2 = table_r2[i]
        if r2 < np.float32(1e-12):
            r2 = np.float32(1e-12)
        inv_r2 = np.float32(1.0) / r2
        s2_over_r2 = sigma2 * inv_r2
        inv_r6 = s2_over_r2 * s2_over_r2 * s2_over_r2
        inv_r12 = inv_r6 * inv_r6
        table_f[i] = np.float32(24.0) * epsilon * (np.float32(2.0) * inv_r12 - inv_r6) * inv_r2

fill_tabulated_lj_r2(tab_r2, tab_f_over_r, sigma, epsilon)

# ============================================================
# Cell-linked list structures (int32 indices)
# ============================================================
@njit(fastmath=True)
def build_cell_linked_list_soa(pos_x, pos_y, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y):
    for cx in range(ncell_x):
        for cy in range(ncell_y):
            cell_heads[cx, cy] = -1
    inv_cell = np.float32(1.0) / cell_size
    Nloc = pos_x.shape[0]
    for i in range(Nloc):
        x = pos_x[i]
        y = pos_y[i]
        cx = int(x * inv_cell) % ncell_x
        cy = int(y * inv_cell) % ncell_y
        next_idx[i] = cell_heads[cx, cy]
        cell_heads[cx, cy] = i

# ============================================================
# Force kernels
# ============================================================
@njit(fastmath=True)
def force_LJ_from_r2(r2, sigma, epsilon):
    inv_r2 = np.float32(1.0) / r2
    sigma2 = sigma * sigma
    s2_over_r2 = sigma2 * inv_r2
    inv_r6 = s2_over_r2 * s2_over_r2 * s2_over_r2
    inv_r12 = inv_r6 * inv_r6
    return np.float32(24.0) * epsilon * (np.float32(2.0) * inv_r12 - inv_r6) * inv_r2

@njit(fastmath=True)
def force_TAB_LJ_r2(f_table, r2, r2_min, r2_max, dr2):
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
# Force computation: cell traversal (SoA)
# ============================================================
@njit(fastmath=True)
def compute_forces_cells_model_soa(
    pos_x, pos_y, force_x, force_y, cell_heads, next_idx, L,
    model_id,  # 0=LJ, 1=TAB_LJ(r2), 2=QUAD
    sigma, epsilon, r_cut2,
    f_table, r2_min, r2_max, dr2,
    sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
    ncell_x, ncell_y
):
    Nloc = pos_x.shape[0]
    for i in range(Nloc):
        force_x[i] = np.float32(0.0)
        force_y[i] = np.float32(0.0)

    for cx in range(ncell_x):
        for cy in range(ncell_y):
            ii = cell_heads[cx, cy]
            while ii != -1:
                xi = pos_x[ii]
                yi = pos_y[ii]
                for dx_cell in (-1, 0, 1):
                    ncx = (cx + dx_cell) % ncell_x
                    for dy_cell in (-1, 0, 1):
                        ncy = (cy + dy_cell) % ncell_y
                        jj = cell_heads[ncx, ncy]
                        while jj != -1:
                            if jj > ii:
                                dx = xi - pos_x[jj]
                                dy = yi - pos_y[jj]
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
                                    force_x[ii] += fx
                                    force_y[ii] += fy
                                    force_x[jj] -= fx
                                    force_y[jj] -= fy
                            jj = next_idx[jj]
                ii = next_idx[ii]

# ============================================================
# Verlet pair-list building and fused multi-step kernel (SoA)
# ============================================================
@njit(fastmath=True)
def compute_max_displacement_soa(pos_x, pos_y, last_x, last_y, disp2, L):
    Nloc = pos_x.shape[0]
    max_disp = np.float32(0.0)
    for i in range(Nloc):
        dx = pos_x[i] - last_x[i]
        dy = pos_y[i] - last_y[i]
        dx = min_image(dx, L)
        dy = min_image(dy, L)
        d2 = dx * dx + dy * dy
        disp2[i] = d2
        if d2 > max_disp:
            max_disp = d2
    return max_disp

@njit(fastmath=True)
def build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j):
    cell_heads = np.full((ncell_x, ncell_y), -1, dtype=np.int32)
    next_idx = np.full(pos_x.shape[0], -1, dtype=np.int32)
    build_cell_linked_list_soa(pos_x, pos_y, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)

    count = 0
    for cx in range(ncell_x):
        for cy in range(ncell_y):
            ii = cell_heads[cx, cy]
            while ii != -1:
                xi = pos_x[ii]
                yi = pos_y[ii]
                for dx_cell in (-1, 0, 1):
                    ncx = (cx + dx_cell) % ncell_x
                    for dy_cell in (-1, 0, 1):
                        ncy = (cy + dy_cell) % ncell_y
                        jj = cell_heads[ncx, ncy]
                        while jj != -1:
                            if jj > ii:
                                dx = xi - pos_x[jj]
                                dy = yi - pos_y[jj]
                                dx = min_image(dx, L)
                                dy = min_image(dy, L)
                                r2 = dx * dx + dy * dy
                                if r2 < r_list2:
                                    pair_i[count] = ii
                                    pair_j[count] = jj
                                    count += 1
                            jj = next_idx[jj]
                ii = next_idx[ii]
    return count

@njit(fastmath=True)
def step_pairs_n(
    nsteps,
    pos_x, pos_y, vel_x, vel_y, force_x, force_y,
    pair_i, pair_j, pair_count,
    L, dt, mass,
    model_id, sigma, epsilon, r_cut2,
    f_table, r2_min, r2_max, dr2,
    sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail
):
    half_dt = np.float32(0.5) * dt
    dt2_over2m = np.float32(0.5) * dt * dt / mass
    Nloc = pos_x.shape[0]
    halfL = np.float32(0.5) * L

    for s in range(nsteps):
        # integrate half step
        for i in range(Nloc):
            xi = pos_x[i] + vel_x[i] * dt + force_x[i] * dt2_over2m
            yi = pos_y[i] + vel_y[i] * dt + force_y[i] * dt2_over2m
            # wrap inline for speed
            if xi >= L:
                xi -= L * math.floor(xi / L)
                if xi >= L:
                    xi -= L
            elif xi < np.float32(0.0):
                xi += L * (1 + math.floor(-xi / L))
                if xi < np.float32(0.0):
                    xi += L
            if yi >= L:
                yi -= L * math.floor(yi / L)
                if yi >= L:
                    yi -= L
            elif yi < np.float32(0.0):
                yi += L * (1 + math.floor(-yi / L))
                if yi < np.float32(0.0):
                    yi += L
            pos_x[i] = xi
            pos_y[i] = yi
            vel_x[i] += (force_x[i] / mass) * half_dt
            vel_y[i] += (force_y[i] / mass) * half_dt

        # zero forces
        for i in range(Nloc):
            force_x[i] = np.float32(0.0)
            force_y[i] = np.float32(0.0)

        # pairs loop
        for idx in range(pair_count):
            i = pair_i[idx]
            j = pair_j[idx]
            dx = pos_x[i] - pos_x[j]
            dy = pos_y[i] - pos_y[j]
            # minimum image inline
            if dx > halfL:
                dx -= L
            elif dx < -halfL:
                dx += L
            if dy > halfL:
                dy -= L
            elif dy < -halfL:
                dy += L
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
                force_x[i] += fx
                force_y[i] += fy
                force_x[j] -= fx
                force_y[j] -= fy

        # finish velocity
        for i in range(Nloc):
            vel_x[i] += (force_x[i] / mass) * half_dt
            vel_y[i] += (force_y[i] / mass) * half_dt

# ============================================================
# Integration (cell mode fallback)
# ============================================================
@njit(fastmath=True)
def integrate_half_soa(pos_x, pos_y, vel_x, vel_y, force_x, force_y, L, dt, mass):
    half_dt = np.float32(0.5) * dt
    dt2_over2m = np.float32(0.5) * dt * dt / mass
    Nloc = pos_x.shape[0]
    for i in range(Nloc):
        xi = pos_x[i] + vel_x[i] * dt + force_x[i] * dt2_over2m
        yi = pos_y[i] + vel_y[i] * dt + force_y[i] * dt2_over2m
        xi = wrap_coord(xi, L)
        yi = wrap_coord(yi, L)
        pos_x[i] = xi
        pos_y[i] = yi
        vel_x[i] += (force_x[i] / mass) * half_dt
        vel_y[i] += (force_y[i] / mass) * half_dt

@njit(fastmath=True)
def finish_velocity_update_soa(vel_x, vel_y, force_x, force_y, dt, mass):
    half_dt = np.float32(0.5) * dt
    Nloc = vel_x.shape[0]
    for i in range(Nloc):
        vel_x[i] += (force_x[i] / mass) * half_dt
        vel_y[i] += (force_y[i] / mass) * half_dt

@njit(fastmath=True)
def apply_thermostat_numba_soa(vel_x, vel_y, target_temp, mass, mix):
    # Compute current T
    ke = np.float32(0.0)
    Nloc = vel_x.shape[0]
    for i in range(Nloc):
        ke += np.float32(0.5) * mass * (vel_x[i] * vel_x[i] + vel_y[i] * vel_y[i])
    current_T = ke / np.float32(Nloc)
    if current_T <= np.float32(0.0):
        return
    scale_fac = np.float32(math.sqrt(float(target_temp / current_T)))
    a = mix
    if a > np.float32(1.0):
        a = np.float32(1.0)
    elif a < np.float32(0.0):
        a = np.float32(0.0)
    for i in range(Nloc):
        vx = vel_x[i]
        vy = vel_y[i]
        vel_x[i] = vx * (np.float32(1.0) - a) + vx * scale_fac * a
        vel_y[i] = vy * (np.float32(1.0) - a) + vy * scale_fac * a

# ============================================================
# Pygame visualization helpers
# ============================================================
def sim_to_screen(x, y):
    sx = MARGIN + float(x) * scale
    sy = MARGIN + float(y) * scale
    return int(sx), int(sy)

def draw_particles(screen, pos_x, pos_y):
    for i in range(pos_x.shape[0]):
        sx, sy = sim_to_screen(pos_x[i], pos_y[i])
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
r_a = np.float32(1.2) * sigma
r_a2 = r_a * r_a
r_cut2_q = r_cut2
k_rep = np.float32(1000.0) * epsilon  # steep repulsion
k_mid = np.float32(4.0) * epsilon
k_tail = np.float32(1.5) * epsilon

# ============================================================
# Main loop
# ============================================================
def main():
    global draw_every_M, draw_skip_enabled, thermostat, FORCE_MODEL, VERLET_MODE_ENABLED

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("2D MD - Numba float32, SoA, fused pair steps, selectable models")
    font = pygame.font.SysFont("consolas", 18)
    clock = pygame.time.Clock()

    # Preallocate cell-linked list arrays (for cell mode)
    cell_heads = np.full((ncell_x, ncell_y), -1, dtype=np.int32)
    next_idx = np.full(N, -1, dtype=np.int32)

    # Pair list buffers (for Verlet mode)
    max_pairs = 40 * N  # generous cap
    pair_i = np.zeros(max_pairs, dtype=np.int32)
    pair_j = np.zeros(max_pairs, dtype=np.int32)
    pair_count = 0

    # Track positions at last pair build and displacement
    last_x = pos_x.copy()
    last_y = pos_y.copy()
    disp2 = np.zeros(N, dtype=np.float32)

    # Initial build
    model_id = model_name_to_id(FORCE_MODEL)

    if VERLET_MODE_ENABLED:
        pair_count = build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
        last_x[:] = pos_x
        last_y[:] = pos_y
        # Warm-up fused kernel with 1 step
        step_pairs_n(
            1,
            pos_x, pos_y, vel_x, vel_y, force_x, force_y,
            pair_i, pair_j, pair_count,
            L, dt, mass,
            model_id, sigma, epsilon, r_cut2,
            tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
            sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail
        )
    else:
        # Cell mode warm-up
        build_cell_linked_list_soa(pos_x, pos_y, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
        integrate_half_soa(pos_x, pos_y, vel_x, vel_y, force_x, force_y, L, dt, mass)
        compute_forces_cells_model_soa(
            pos_x, pos_y, force_x, force_y, cell_heads, next_idx, L,
            model_id, sigma, epsilon, r_cut2,
            tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
            sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
            ncell_x, ncell_y
        )
        finish_velocity_update_soa(vel_x, vel_y, force_x, force_y, dt, mass)

    step = 0
    last_rebuild = 0  # for cell mode

    # Steps/sec measurement (independent of drawing)
    steps_counter = 0
    steps_start_time = time.time()
    steps_per_sec = 0.0

    while True:
        # Event handling (on every loop; for even less overhead you could handle only on draw steps)
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
                    FORCE_MODEL = "LJ"; model_id = 0
                elif event.key == pygame.K_2:
                    FORCE_MODEL = "TAB_LJ"; model_id = 1
                elif event.key == pygame.K_3:
                    FORCE_MODEL = "QUAD"; model_id = 2
                elif event.key == pygame.K_v:
                    VERLET_MODE_ENABLED = not VERLET_MODE_ENABLED
                    # Force rebuild/init for new mode
                    last_rebuild = -rebuild_interval
                    last_x[:] = pos_x
                    last_y[:] = pos_y
                    pair_count = 0

        # Simulation advance
        if VERLET_MODE_ENABLED:
            # Rebuild pair list if needed (displacement threshold)
            max_disp2 = compute_max_displacement_soa(pos_x, pos_y, last_x, last_y, disp2, L)
            threshold2 = (np.float32(0.5) * r_skin) * (np.float32(0.5) * r_skin)
            if max_disp2 >= threshold2 or pair_count == 0:
                pair_count = build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
                last_x[:] = pos_x
                last_y[:] = pos_y
            # Fused kernel: do draw_every_M steps per call to reduce overhead
            nsteps = draw_every_M if draw_skip_enabled else 1
            step_pairs_n(
                nsteps,
                pos_x, pos_y, vel_x, vel_y, force_x, force_y,
                pair_i, pair_j, pair_count,
                L, dt, mass,
                model_id, sigma, epsilon, r_cut2,
                tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
                sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail
            )
            step += nsteps
            steps_counter += nsteps

            # Thermostat during initial steps (apply after fused call)
            if thermostat and step < thermostat_steps:
                apply_thermostat_numba_soa(vel_x, vel_y, target_temp, mass, mix=damping)
        else:
            # Cell traversal mode: one step per loop
            integrate_half_soa(pos_x, pos_y, vel_x, vel_y, force_x, force_y, L, dt, mass)
            if (step - last_rebuild) >= rebuild_interval:
                build_cell_linked_list_soa(pos_x, pos_y, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
                last_rebuild = step
            compute_forces_cells_model_soa(
                pos_x, pos_y, force_x, force_y, cell_heads, next_idx, L,
                model_id, sigma, epsilon, r_cut2,
                tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
                sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
                ncell_x, ncell_y
            )
            finish_velocity_update_soa(vel_x, vel_y, force_x, force_y, dt, mass)
            step += 1
            steps_counter += 1

            if thermostat and step < thermostat_steps:
                apply_thermostat_numba_soa(vel_x, vel_y, target_temp, mass, mix=damping)

        # Steps/sec measurement
        now = time.time()
        elapsed = now - steps_start_time
        if elapsed >= 0.5:
            steps_per_sec = steps_counter / elapsed
            steps_counter = 0
            steps_start_time = now

        # Render occasionally
        do_draw = True
        if draw_skip_enabled:
            do_draw = True  # we advanced by nsteps; draw this loop
        if do_draw:
            screen.fill(background_color)
            draw_box(screen)
            draw_particles(screen, pos_x, pos_y)

            # Stats
            T = float(compute_temperature_soa(vel_x, vel_y, mass))
            draw_text(screen, font, f"Step: {step}", 20, 20)
            draw_text(screen, font, f"T: {T:.3f}", 20, 40)
            draw_text(screen, font, f"Steps/sec: {steps_per_sec:.0f}", 20, 60)
            draw_text(screen, font, f"Thermostat: {'ON' if (thermostat and step < thermostat_steps) else 'OFF'} (SPACE)", 20, 80)
            draw_text(screen, font, f"Draw every M: {draw_every_M} (D toggle, Up/Down adjust)", 20, 100)
            draw_text(screen, font, f"Force model: {FORCE_MODEL} (1=LJ, 2=TAB_LJ r2, 3=QUAD)", 20, 120)
            draw_text(screen, font, f"Verlet pairs: {'ON' if VERLET_MODE_ENABLED else 'OFF'} (V toggle)", 20, 140)

            pygame.display.flip()

        clock.tick(fps_limit)  # unlimited

if __name__ == "__main__":
    main()

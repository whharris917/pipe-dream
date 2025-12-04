import math
import random
import time

import numpy as np
import pygame
from numba import njit

# ============================================================
# Force model selection and mode
# ============================================================
FORCE_MODEL = "LJ"
VERLET_MODE_ENABLED = True
GRAVITY_ENABLED = True

# ============================================================
# Simulation parameters (Gold Standard Tuning)
# ============================================================
N = 300
sigma = np.float32(0.25)
epsilon = np.float32(1.0)
mass = np.float32(1.0)

# Defaults (Stored for Reset)
DEFAULT_DT = np.float32(0.002)
DEFAULT_DENSITY = np.float32(0.7)
DEFAULT_DRAW_M = 10

dt = DEFAULT_DT
density = DEFAULT_DENSITY
r_cut = np.float32(2.5) * sigma
r_cut2 = r_cut * r_cut
target_temp = np.float32(0.5)
thermostat = True
damping = np.float32(0.1)
L = np.float32(math.sqrt(N / float(density)))

# Gravity (downward acceleration)
gravity_accel = np.float32(10.0)

# Wall Damping
WALL_DAMPING = np.float32(0.8)

# Visualization parameters
WINDOW_W = 720
WINDOW_H = 720
MARGIN = 50
particle_draw_radius = 2
background_color = (8, 10, 14)
particle_color = (90, 200, 255)
text_color = (230, 230, 230)
fps_limit = 0

draw_skip_enabled = True
draw_every_M = DEFAULT_DRAW_M
show_extra_diag = True

# Neighbor list / cell list parameters
cell_size = np.float32(1.05) * r_cut
ncell_x = max(1, int(float(L) // float(cell_size)))
ncell_y = max(1, int(float(L) // float(cell_size)))
rebuild_interval = 20

# Spatial sorting interval
sort_interval = 100

# ============================================================
# Tabulation settings
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
# Numba-jitted helpers
# ============================================================
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
            if count >= N: break
            pos_x[count] = np.float32((i + 0.5) * spacing)
            pos_y[count] = np.float32((j + 0.5) * spacing)
            count += 1
        if count >= N: break
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
# Spatial Sorting Helper
# ============================================================
@njit(fastmath=True)
def spatial_sort_soa(pos_x, pos_y, vel_x, vel_y, force_x, force_y, L, cell_size):
    """Sorts particles by cell index to improve CPU cache locality."""
    N = pos_x.shape[0]
    ncell_side = int(L / cell_size)
    if ncell_side < 1: ncell_side = 1
    
    keys = np.zeros(N, dtype=np.int32)
    inv = 1.0 / cell_size
    for i in range(N):
        cx = int(pos_x[i] * inv) % ncell_side
        cy = int(pos_y[i] * inv) % ncell_side
        keys[i] = cy * ncell_side + cx
        
    perm = np.argsort(keys)
    
    pos_x[:] = pos_x[perm]
    pos_y[:] = pos_y[perm]
    vel_x[:] = vel_x[perm]
    vel_y[:] = vel_y[perm]
    force_x[:] = force_x[perm]
    force_y[:] = force_y[perm]

# ============================================================
# Fill r^2-tabulated LJ table
# ============================================================
@njit(fastmath=True)
def fill_tabulated_lj_r2(table_r2, table_f, sigma, epsilon):
    sigma2 = sigma * sigma
    for i in range(table_r2.shape[0]):
        r2 = table_r2[i]
        if r2 < np.float32(1e-12): r2 = np.float32(1e-12)
        inv_r2 = np.float32(1.0) / r2
        s2_over_r2 = sigma2 * inv_r2
        inv_r6 = s2_over_r2 * s2_over_r2 * s2_over_r2
        inv_r12 = inv_r6 * inv_r6
        table_f[i] = np.float32(24.0) * epsilon * (np.float32(2.0) * inv_r12 - inv_r6) * inv_r2

fill_tabulated_lj_r2(tab_r2, tab_f_over_r, sigma, epsilon)

# ============================================================
# Cell-linked list structures
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
        cx = int(x * inv_cell)
        cy = int(y * inv_cell)
        if cx >= ncell_x: cx = ncell_x - 1
        if cy >= ncell_y: cy = ncell_y - 1
        if cx < 0: cx = 0
        if cy < 0: cy = 0
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
    if r2 >= r2_max: return np.float32(0.0)
    if r2 < r2_min: r2 = r2_min
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
def compute_forces_cells_model_soa(
    pos_x, pos_y, force_x, force_y, cell_heads, next_idx, L,
    model_id, sigma, epsilon, r_cut2,
    f_table, r2_min, r2_max, dr2,
    sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
    ncell_x, ncell_y,
    g_val, mass
):
    Nloc = pos_x.shape[0]
    for i in range(Nloc):
        force_x[i] = np.float32(0.0)
        force_y[i] = mass * g_val

    for cx in range(ncell_x):
        for cy in range(ncell_y):
            ii = cell_heads[cx, cy]
            while ii != -1:
                xi = pos_x[ii]
                yi = pos_y[ii]
                for dx_cell in (-1, 0, 1):
                    ncx = cx + dx_cell
                    if ncx < 0 or ncx >= ncell_x: continue
                    for dy_cell in (-1, 0, 1):
                        ncy = cy + dy_cell
                        if ncy < 0 or ncy >= ncell_y: continue
                        jj = cell_heads[ncx, ncy]
                        while jj != -1:
                            if jj > ii:
                                dx = xi - pos_x[jj]
                                dy = yi - pos_y[jj]
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
# Verlet pair-list building
# ============================================================
@njit(fastmath=True)
def compute_max_displacement_soa(pos_x, pos_y, last_x, last_y, disp2, L):
    Nloc = pos_x.shape[0]
    max_disp = np.float32(0.0)
    for i in range(Nloc):
        dx = pos_x[i] - last_x[i]
        dy = pos_y[i] - last_y[i]
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
    max_pairs = pair_i.shape[0]

    for cx in range(ncell_x):
        for cy in range(ncell_y):
            ii = cell_heads[cx, cy]
            while ii != -1:
                xi = pos_x[ii]
                yi = pos_y[ii]
                for dx_cell in (-1, 0, 1):
                    ncx = cx + dx_cell
                    if ncx < 0 or ncx >= ncell_x: continue
                    for dy_cell in (-1, 0, 1):
                        ncy = cy + dy_cell
                        if ncy < 0 or ncy >= ncell_y: continue
                        jj = cell_heads[ncx, ncy]
                        while jj != -1:
                            if jj > ii:
                                dx = xi - pos_x[jj]
                                dy = yi - pos_y[jj]
                                r2 = dx * dx + dy * dy
                                if r2 < r_list2:
                                    if count < max_pairs:
                                        pair_i[count] = ii
                                        pair_j[count] = jj
                                        count += 1
                                    else:
                                        return -1
                            jj = next_idx[jj]
                ii = next_idx[ii]
    return count

# ============================================================
# Check skin breach
# ============================================================
@njit(fastmath=True)
def check_skin_breach(pos_x, pos_y, last_x, last_y, L, limit_sq):
    N = pos_x.shape[0]
    for i in range(N):
        dx = pos_x[i] - last_x[i]
        dy = pos_y[i] - last_y[i]
        d2 = dx*dx + dy*dy
        if d2 > limit_sq:
            return True
    return False

# ============================================================
# Fused Multi-step Kernel
# ============================================================
@njit(fastmath=True)
def step_pairs_n(
    nsteps,
    pos_x, pos_y, vel_x, vel_y, force_x, force_y,
    pair_i, pair_j, pair_count,
    last_x, last_y, r_skin_sq_limit,
    L, dt, mass,
    model_id, sigma, epsilon, r_cut2,
    f_table, r2_min, r2_max, dr2,
    sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
    g_val, wall_damping
):
    half_dt = np.float32(0.5) * dt
    dt2_over2m = np.float32(0.5) * dt * dt / mass
    Nloc = pos_x.shape[0]
    
    steps_done = 0

    for s in range(nsteps):
        if s > 0 and s % 5 == 0:
            if check_skin_breach(pos_x, pos_y, last_x, last_y, L, r_skin_sq_limit):
                return steps_done

        for i in range(Nloc):
            xi = pos_x[i] + vel_x[i] * dt + force_x[i] * dt2_over2m
            yi = pos_y[i] + vel_y[i] * dt + force_y[i] * dt2_over2m
            
            # Wall Reflection X (Damped)
            if xi >= L:
                xi = np.float32(2.0)*L - xi
                vel_x[i] = -vel_x[i] * wall_damping
            elif xi < np.float32(0.0):
                xi = -xi
                vel_x[i] = -vel_x[i] * wall_damping
                
            # Wall Reflection Y (Damped)
            if yi >= L:
                yi = np.float32(2.0)*L - yi
                vel_y[i] = -vel_y[i] * wall_damping
            elif yi < np.float32(0.0):
                yi = -yi
                vel_y[i] = -vel_y[i] * wall_damping

            pos_x[i] = xi
            pos_y[i] = yi
            vel_x[i] += (force_x[i] / mass) * half_dt
            vel_y[i] += (force_y[i] / mass) * half_dt

        # Reset forces (Apply Gravity)
        for i in range(Nloc):
            force_x[i] = np.float32(0.0)
            force_y[i] = mass * g_val

        # pairs loop (No PBC)
        for idx in range(pair_count):
            i = pair_i[idx]
            j = pair_j[idx]
            dx = pos_x[i] - pos_x[j]
            dy = pos_y[i] - pos_y[j]
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

        for i in range(Nloc):
            vel_x[i] += (force_x[i] / mass) * half_dt
            vel_y[i] += (force_y[i] / mass) * half_dt
            
        steps_done += 1
        
    return steps_done

# ============================================================
# Integration (cell mode fallback)
# ============================================================
@njit(fastmath=True)
def integrate_half_soa(pos_x, pos_y, vel_x, vel_y, force_x, force_y, L, dt, mass, wall_damping):
    half_dt = np.float32(0.5) * dt
    dt2_over2m = np.float32(0.5) * dt * dt / mass
    Nloc = pos_x.shape[0]
    for i in range(Nloc):
        xi = pos_x[i] + vel_x[i] * dt + force_x[i] * dt2_over2m
        yi = pos_y[i] + vel_y[i] * dt + force_y[i] * dt2_over2m
        
        # Wall Reflection X (Damped)
        if xi >= L:
            xi = np.float32(2.0)*L - xi
            vel_x[i] = -vel_x[i] * wall_damping
        elif xi < np.float32(0.0):
            xi = -xi
            vel_x[i] = -vel_x[i] * wall_damping
            
        # Wall Reflection Y (Damped)
        if yi >= L:
            yi = np.float32(2.0)*L - yi
            vel_y[i] = -vel_y[i] * wall_damping
        elif yi < np.float32(0.0):
            yi = -yi
            vel_y[i] = -vel_y[i] * wall_damping

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
    ke = np.float32(0.0)
    Nloc = vel_x.shape[0]
    for i in range(Nloc):
        ke += np.float32(0.5) * mass * (vel_x[i] * vel_x[i] + vel_y[i] * vel_y[i])
    current_T = ke / np.float32(Nloc)
    if current_T <= np.float32(0.0): return
    scale_fac = np.float32(math.sqrt(float(target_temp / current_T)))
    a = mix
    if a > np.float32(1.0): a = np.float32(1.0)
    elif a < np.float32(0.0): a = np.float32(0.0)
    for i in range(Nloc):
        vx = vel_x[i]
        vy = vel_y[i]
        vel_x[i] = vx * (np.float32(1.0) - a) + vx * scale_fac * a
        vel_y[i] = vy * (np.float32(1.0) - a) + vy * scale_fac * a

# ============================================================
# Pygame visualization helpers (With Corrected Zoom)
# ============================================================
def sim_to_screen(x, y, zoom, pan_x, pan_y):
    # Base scale fits L into the window with margin
    base_scale = (float(WINDOW_W) - 2.0 * MARGIN) / float(L)
    final_scale = base_scale * zoom
    
    # Center of window
    cx_win = WINDOW_W / 2.0
    cy_win = WINDOW_H / 2.0
    
    # Center of box
    cx_box = float(L) / 2.0
    cy_box = float(L) / 2.0
    
    # Transform: Center box on window center, apply scale, then apply pan
    sx = cx_win + (float(x) - cx_box) * final_scale + pan_x
    sy = cy_win + (float(y) - cy_box) * final_scale + pan_y
    
    return int(sx), int(sy)

def draw_particles(screen, pos_x, pos_y, zoom, pan_x, pan_y):
    for i in range(pos_x.shape[0]):
        sx, sy = sim_to_screen(pos_x[i], pos_y[i], zoom, pan_x, pan_y)
        if -50 <= sx <= WINDOW_W + 50 and -50 <= sy <= WINDOW_H + 50:
             r = max(1, int(particle_draw_radius * zoom))
             pygame.draw.circle(screen, particle_color, (sx, sy), r)

def draw_box(screen, zoom, pan_x, pan_y):
    x1, y1 = sim_to_screen(0, 0, zoom, pan_x, pan_y)
    x2, y2 = sim_to_screen(L, L, zoom, pan_x, pan_y)
    rect = pygame.Rect(x1, y1, x2-x1, y2-y1)
    pygame.draw.rect(screen, (80, 80, 90), rect, width=2)

def draw_text(screen, font, text, x, y):
    surf = font.render(text, True, text_color)
    screen.blit(surf, (x, y))

# ============================================================
# Model mapping
# ============================================================
def model_name_to_id(name):
    if name == "LJ": return 0
    elif name == "TAB_LJ": return 1
    elif name == "QUAD": return 2
    else: return 0

sigma2_q = sigma * sigma
r_a = np.float32(1.2) * sigma
r_a2 = r_a * r_a
r_cut2_q = r_cut2
k_rep = np.float32(1000.0) * epsilon
k_mid = np.float32(4.0) * epsilon
k_tail = np.float32(1.5) * epsilon

# ============================================================
# Main loop
# ============================================================
def main():
    global draw_every_M, draw_skip_enabled, show_extra_diag
    global thermostat, FORCE_MODEL, VERLET_MODE_ENABLED, GRAVITY_ENABLED
    global dt, density, L, scale, r_skin, r_list, r_list2
    global ncell_x, ncell_y, cell_size

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("MD Gold Standard - Complete Reset Logic")
    font = pygame.font.SysFont("consolas", 18)
    clock = pygame.time.Clock()

    cell_heads = np.full((ncell_x, ncell_y), -1, dtype=np.int32)
    next_idx = np.full(N, -1, dtype=np.int32)

    max_pairs = 100 * N 
    pair_i = np.zeros(max_pairs, dtype=np.int32)
    pair_j = np.zeros(max_pairs, dtype=np.int32)
    pair_count = 0

    last_x = pos_x.copy()
    last_y = pos_y.copy()
    disp2 = np.zeros(N, dtype=np.float32)

    model_id = model_name_to_id(FORCE_MODEL)

    # State variables
    zoom = 1.0
    pan_x = 0.0
    pan_y = 0.0
    is_panning = False
    last_mouse_pos = (0, 0)
    step = 0
    total_steps_integrated = 0
    
    def reset_simulation():
        nonlocal zoom, pan_x, pan_y, step, total_steps_integrated, pair_count
        global dt, density, L, scale, draw_every_M, ncell_x, ncell_y
        
        # 1. Reset Constants to Defaults
        dt = DEFAULT_DT
        density = DEFAULT_DENSITY
        draw_every_M = DEFAULT_DRAW_M
        L = np.float32(math.sqrt(N / float(density)))
        scale = (WINDOW_W - 2 * MARGIN) / float(L)
        
        # Recalculate grid based on Default L
        ncell_x = max(1, int(float(L) // float(cell_size)))
        ncell_y = max(1, int(float(L) // float(cell_size)))

        # 2. Reset Physics Arrays
        pos_x[:], pos_y[:] = init_lattice_positions_soa(N, L)
        vel_x[:], vel_y[:] = init_random_velocities_soa(N, target_temp, mass)
        
        # CRITICAL: Zero forces and displacement
        force_x.fill(0.0)
        force_y.fill(0.0)
        disp2.fill(0.0)
        
        # 3. Rebuild neighbors
        pair_count = build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
        last_x[:] = pos_x
        last_y[:] = pos_y
        
        # 4. Reset View
        zoom = 1.0
        pan_x = 0.0
        pan_y = 0.0
        step = 0
        total_steps_integrated = 0
        
        # 5. Warm-up
        skin_sq_limit = (0.5 * r_skin) ** 2
        g_val = gravity_accel if GRAVITY_ENABLED else np.float32(0.0)
        step_pairs_n(1, pos_x, pos_y, vel_x, vel_y, force_x, force_y,
                     pair_i, pair_j, pair_count, last_x, last_y, skin_sq_limit,
                     L, dt, mass, model_id, sigma, epsilon, r_cut2,
                     tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
                     sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
                     g_val, WALL_DAMPING)

    # Initial boot
    reset_simulation()
    
    steps_counter = 0
    steps_start_time = time.time()
    steps_per_sec = 0.0
    last_rebuild = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            elif event.type == pygame.MOUSEWHEEL:
                factor = 1.1 if event.y > 0 else (1.0 / 1.1)
                new_zoom = zoom * factor
                if 0.1 <= new_zoom <= 50.0:
                    zoom = new_zoom
                    pan_x *= factor
                    pan_y *= factor
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    is_panning = True
                    last_mouse_pos = event.pos
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_panning = False
                    
            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]
                    pan_x += dx
                    pan_y += dy
                    last_mouse_pos = event.pos

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: thermostat = not thermostat
                elif event.key == pygame.K_ESCAPE: pygame.quit(); return
                elif event.key == pygame.K_g: GRAVITY_ENABLED = not GRAVITY_ENABLED
                elif event.key == pygame.K_d: draw_skip_enabled = not draw_skip_enabled
                elif event.key == pygame.K_h: show_extra_diag = not show_extra_diag
                elif event.key == pygame.K_UP: draw_every_M = min(5000, draw_every_M + 10)
                elif event.key == pygame.K_DOWN: draw_every_M = max(1, draw_every_M - 10)
                elif event.key == pygame.K_1: FORCE_MODEL = "LJ"; model_id = 0
                elif event.key == pygame.K_2: FORCE_MODEL = "TAB_LJ"; model_id = 1
                elif event.key == pygame.K_3: FORCE_MODEL = "QUAD"; model_id = 2
                elif event.key == pygame.K_v:
                    VERLET_MODE_ENABLED = not VERLET_MODE_ENABLED
                    last_rebuild = -rebuild_interval
                    last_x[:] = pos_x; last_y[:] = pos_y; pair_count = 0
                elif event.key == pygame.K_r: 
                    reset_simulation()
                elif event.key == pygame.K_t: dt = dt * np.float32(1.1)
                elif event.key == pygame.K_y: dt = dt * np.float32(0.9)
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    density = density * np.float32(1.05)
                    L = np.float32(math.sqrt(N / float(density)))
                    ncell_x = max(1, int(float(L) // float(cell_size)))
                    ncell_y = max(1, int(float(L) // float(cell_size)))
                    for i in range(N):
                        if pos_x[i] >= L: pos_x[i] = L - 0.01
                        if pos_y[i] >= L: pos_y[i] = L - 0.01
                    pair_count = build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
                    last_x[:] = pos_x; last_y[:] = pos_y
                elif event.key == pygame.K_MINUS:
                    density = density * np.float32(0.95)
                    L = np.float32(math.sqrt(N / float(density)))
                    ncell_x = max(1, int(float(L) // float(cell_size)))
                    ncell_y = max(1, int(float(L) // float(cell_size)))
                    pair_count = build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
                    last_x[:] = pos_x; last_y[:] = pos_y

        g_val = gravity_accel if GRAVITY_ENABLED else np.float32(0.0)

        if VERLET_MODE_ENABLED:
            if total_steps_integrated % sort_interval == 0:
                spatial_sort_soa(pos_x, pos_y, vel_x, vel_y, force_x, force_y, L, cell_size)
                pair_count = 0 
            
            max_disp2 = compute_max_displacement_soa(pos_x, pos_y, last_x, last_y, disp2, L)
            threshold2 = (np.float32(0.5) * r_skin) ** 2
            
            if max_disp2 >= threshold2 or pair_count == 0:
                pc = build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
                if pc == -1:
                    print(f"Warning: Pair list overflow (size {max_pairs}). Resizing...")
                    max_pairs *= 2
                    pair_i = np.zeros(max_pairs, dtype=np.int32)
                    pair_j = np.zeros(max_pairs, dtype=np.int32)
                    pc = build_verlet_pairs_soa(pos_x, pos_y, L, r_list2, cell_size, ncell_x, ncell_y, pair_i, pair_j)
                pair_count = pc
                last_x[:] = pos_x
                last_y[:] = pos_y

            nsteps = draw_every_M if draw_skip_enabled else 1
            
            done = step_pairs_n(
                nsteps,
                pos_x, pos_y, vel_x, vel_y, force_x, force_y,
                pair_i, pair_j, pair_count,
                last_x, last_y, threshold2,
                L, dt, mass,
                model_id, sigma, epsilon, r_cut2,
                tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
                sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
                g_val, WALL_DAMPING
            )
            
            step += done
            total_steps_integrated += done
            steps_counter += done

            if thermostat:
                apply_thermostat_numba_soa(vel_x, vel_y, target_temp, mass, mix=damping)
        else:
            integrate_half_soa(pos_x, pos_y, vel_x, vel_y, force_x, force_y, L, dt, mass, WALL_DAMPING)
            if (step - last_rebuild) >= rebuild_interval:
                build_cell_linked_list_soa(pos_x, pos_y, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
                last_rebuild = step
            compute_forces_cells_model_soa(
                pos_x, pos_y, force_x, force_y, cell_heads, next_idx, L,
                model_id, sigma, epsilon, r_cut2,
                tab_f_over_r, tab_r2_min, tab_r2_max, tab_dr2,
                sigma2_q, r_a2, r_cut2_q, k_rep, k_mid, k_tail,
                ncell_x, ncell_y,
                g_val, mass
            )
            finish_velocity_update_soa(vel_x, vel_y, force_x, force_y, dt, mass)
            step += 1
            total_steps_integrated += 1
            steps_counter += 1

            if thermostat:
                apply_thermostat_numba_soa(vel_x, vel_y, target_temp, mass, mix=damping)

        now = time.time()
        elapsed = now - steps_start_time
        if elapsed >= 0.5:
            steps_per_sec = steps_counter / elapsed
            steps_counter = 0
            steps_start_time = now

        if draw_skip_enabled or not VERLET_MODE_ENABLED:
            screen.fill(background_color)
            draw_box(screen, zoom, pan_x, pan_y)
            draw_particles(screen, pos_x, pos_y, zoom, pan_x, pan_y)

            T = float(compute_temperature_soa(vel_x, vel_y, mass))
            y = 20
            draw_text(screen, font, f"Step: {step}", 20, y); y += 20
            draw_text(screen, font, f"T: {T:.3f}", 20, y); y += 20
            draw_text(screen, font, f"Steps/sec: {steps_per_sec:.0f}", 20, y); y += 20
            draw_text(screen, font, f"Zoom: {zoom:.2f} (Mouse Wheel)", 20, y); y += 20
            
            energy_loss = (1.0 - float(WALL_DAMPING)**2) * 100.0
            draw_text(screen, font, f"Wall Damping: {float(WALL_DAMPING):.2f} (~{energy_loss:.1f}% E loss)", 20, y); y += 20
            
            if VERLET_MODE_ENABLED:
                draw_text(screen, font, f"pair_count: {pair_count}", 20, y); y += 20
            draw_text(screen, font, f"Draw every M: {draw_every_M} (D toggle, Up/Down adjust)", 20, y); y += 20
            draw_text(screen, font, f"Thermostat: {'ON' if thermostat else 'OFF'} (SPACE)", 20, y); y += 20

            if show_extra_diag:
                y += 10
                draw_text(screen, font, f"dt: {float(dt):.5f} (T/Y)", 20, y); y += 20
                draw_text(screen, font, f"Box L: {float(L):.3f}", 20, y); y += 20
                draw_text(screen, font, f"Pan: {int(pan_x)}, {int(pan_y)} (Drag Left Click)", 20, y); y += 20

            pygame.display.flip()

        clock.tick(fps_limit)

if __name__ == "__main__":
    main()
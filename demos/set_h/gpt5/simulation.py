import math
import random
import time

import numpy as np
import pygame
from numba import njit

# -----------------------------
# Simulation parameters (float32-compatible)
# -----------------------------
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
scale = (WINDOW_W - 2 * MARGIN) / float(L)  # keep screen math in Python float
particle_draw_radius = max(1, int(0.25 * scale))
background_color = (8, 10, 14)
particle_color = (90, 200, 255)
text_color = (230, 230, 230)
fps_limit = 0  # unlimited

# Draw skipping: draw only every Mth frame
draw_skip_enabled = True
draw_every_M = 10  # adjustable at runtime

# Neighbor list / cell list parameters
cell_size = np.float32(1.05) * r_cut
ncell_x = max(1, int(float(L) // float(cell_size)))
ncell_y = max(1, int(float(L) // float(cell_size)))
rebuild_interval = 20

# -----------------------------
# Numba-jitted helpers (float32 + fastmath)
# -----------------------------
@njit(fastmath=True)
def wrap_coord(x, L):
    # Wrap coordinate to [0, L)
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
    # Remove net momentum
    mean_vx = np.float32(np.mean(vels[:, 0]))
    mean_vy = np.float32(np.mean(vels[:, 1]))
    vels[:, 0] -= mean_vx
    vels[:, 1] -= mean_vy
    # Scale to target temperature
    current_T = compute_temperature(vels, mass)
    if current_T > 0:
        scale_fac = np.float32(math.sqrt(float(target_temp / current_T)))
        vels *= scale_fac
    return vels

positions = init_lattice_positions(N, L)
velocities = init_random_velocities(N, target_temp, mass)
forces = np.zeros((N, 2), dtype=np.float32)

# -----------------------------
# Cell-linked list structures (int32 indices)
# -----------------------------
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

@njit(fastmath=True)
def compute_forces_cells(positions, forces, cell_heads, next_idx, L, sigma, epsilon, r_cut2, ncell_x, ncell_y):
    Nloc = positions.shape[0]
    for i in range(Nloc):
        forces[i, 0] = np.float32(0.0)
        forces[i, 1] = np.float32(0.0)

    sigma2 = sigma * sigma

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
                                    inv_r2 = np.float32(1.0) / r2
                                    inv_r6 = (sigma2 * inv_r2) ** np.float32(3.0)
                                    inv_r12 = inv_r6 * inv_r6
                                    f_over_r = np.float32(24.0) * epsilon * (np.float32(2.0) * inv_r12 - inv_r6) * inv_r2
                                    fx = f_over_r * dx
                                    fy = f_over_r * dy
                                    forces[ii, 0] += fx
                                    forces[ii, 1] += fy
                                    forces[jj, 0] -= fx
                                    forces[jj, 1] -= fy
                            jj = next_idx[jj]
                ii = next_idx[ii]

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

# -----------------------------
# Pygame visualization helpers
# -----------------------------
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

# -----------------------------
# Main loop
# -----------------------------
def main():
    global draw_every_M, draw_skip_enabled, thermostat

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("2D Lennard-Jones MD (N=1000) - Numba float32, skip-draw")
    font = pygame.font.SysFont("consolas", 18)
    clock = pygame.time.Clock()

    # Preallocate cell-linked list arrays
    cell_heads = np.full((ncell_x, ncell_y), -1, dtype=np.int32)
    next_idx = np.full(N, -1, dtype=np.int32)

    # Initial neighbor build and forces
    build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
    compute_forces_cells(positions, forces, cell_heads, next_idx, L, sigma, epsilon, r_cut2, ncell_x, ncell_y)

    step = 0
    last_rebuild = 0
    last_time = time.time()
    frames = 0
    avg_fps = 0.0
    running = True

    # Warm up JIT to avoid first-frame stutter
    integrate_half(positions, velocities, forces, L, dt, mass)
    build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
    compute_forces_cells(positions, forces, cell_heads, next_idx, L, sigma, epsilon, r_cut2, ncell_x, ncell_y)
    finish_velocity_update(velocities, forces, dt, mass)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    thermostat = not thermostat
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_d:
                    draw_skip_enabled = not draw_skip_enabled
                elif event.key == pygame.K_UP:
                    draw_every_M = min(1000, draw_every_M + 1)
                elif event.key == pygame.K_DOWN:
                    draw_every_M = max(1, draw_every_M - 1)

        # MD step
        integrate_half(positions, velocities, forces, L, dt, mass)

        if (step - last_rebuild) >= rebuild_interval:
            build_cell_linked_list(positions, cell_heads, next_idx, L, cell_size, ncell_x, ncell_y)
            last_rebuild = step

        compute_forces_cells(positions, forces, cell_heads, next_idx, L, sigma, epsilon, r_cut2, ncell_x, ncell_y)
        finish_velocity_update(velocities, forces, dt, mass)

        # Optional thermostat
        if thermostat and step < thermostat_steps:
            apply_thermostat_numba(velocities, target_temp, mass, mix=damping)

        # Render: draw only every Mth frame if skipping is enabled
        do_draw = True
        if draw_skip_enabled:
            do_draw = (step % draw_every_M == 0)

        if do_draw:
            screen.fill(background_color)
            draw_box(screen)
            draw_particles(screen, positions)

            # Stats
            T = float(compute_temperature(velocities, mass))
            draw_text(screen, font, f"Step: {step}", 20, 20)
            draw_text(screen, font, f"T: {T:.3f}", 20, 40)
            draw_text(screen, font, f"FPS: {avg_fps:.1f}", 20, 60)
            draw_text(screen, font, f"Thermostat: {'ON' if (thermostat and step < thermostat_steps) else 'OFF'} (SPACE)", 20, 80)
            draw_text(screen, font, f"Draw every M: {draw_every_M} (D toggle, Up/Down adjust)", 20, 100)

            pygame.display.flip()

            frames += 1
            now = time.time()
            if now - last_time >= 0.5:
                avg_fps = frames / (now - last_time)
                frames = 0
                last_time = now

        # No frame cap: fps_limit = 0 means no delay
        clock.tick(fps_limit)

        step += 1

    pygame.quit()

if __name__ == "__main__":
    main()

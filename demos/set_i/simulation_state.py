import numpy as np
import random
import math
import time
import config
from physics_core import integrate_n_steps, build_neighbor_list, check_displacement, apply_thermostat, spatial_sort

class Simulation:
    def __init__(self):
        self.capacity = 5000
        self.count = 0
        
        # Physics State Arrays
        self.pos_x = np.zeros(self.capacity, dtype=np.float32)
        self.pos_y = np.zeros(self.capacity, dtype=np.float32)
        self.vel_x = np.zeros(self.capacity, dtype=np.float32)
        self.vel_y = np.zeros(self.capacity, dtype=np.float32)
        self.force_x = np.zeros(self.capacity, dtype=np.float32)
        self.force_y = np.zeros(self.capacity, dtype=np.float32)
        self.is_static = np.zeros(self.capacity, dtype=np.int32)
        
        self.walls = []
        
        # Neighbors
        self.max_pairs = self.capacity * 100
        self.pair_i = np.zeros(self.max_pairs, dtype=np.int32)
        self.pair_j = np.zeros(self.max_pairs, dtype=np.int32)
        self.pair_count = 0
        self.last_x = np.zeros(self.capacity, dtype=np.float32)
        self.last_y = np.zeros(self.capacity, dtype=np.float32)
        
        # Settings
        self.paused = True
        self.dt = config.DEFAULT_DT
        self.gravity = config.DEFAULT_GRAVITY
        self.target_temp = 0.5
        self.use_thermostat = False
        
        # NOTE: Damping removed to match improved_ui.py performance
        
        self.r_skin = 0.3
        self.r_cut_base = 2.5
        self.r_list = self.r_cut_base + self.r_skin
        self.r_list2 = self.r_list**2
        self.r_skin_sq_limit = (0.5 * self.r_skin)**2
        self.cell_size = self.r_list
        
        self.total_steps = 0
        
        # Performance Metrics (SPS)
        self.sps = 0.0
        self.steps_accumulator = 0
        self.last_sps_update = time.time()

    def add_particles_brush(self, x, y, radius, density=0.5):
        if self.count >= self.capacity - 100:
            self._resize_arrays()
            
        n_to_add = 1 if radius < 1.0 else int(density * radius**2)
        if n_to_add < 1: n_to_add = 1
        
        for _ in range(n_to_add):
            angle = random.random() * 6.28
            r = math.sqrt(random.random()) * radius
            px = x + math.cos(angle) * r
            py = y + math.sin(angle) * r
            
            if 0 < px < config.WORLD_SIZE and 0 < py < config.WORLD_SIZE:
                idx = self.count
                self.pos_x[idx] = px
                self.pos_y[idx] = py
                self.vel_x[idx] = 0.0
                self.vel_y[idx] = 0.0
                self.is_static[idx] = 0 
                self.count += 1
                
        self.pair_count = 0

    def delete_particles_brush(self, x, y, radius):
        r2 = radius**2
        
        wall_hit = -1
        for idx, wall in enumerate(self.walls):
            for pt in [wall['start'], wall['end']]:
                dx = pt[0] - x
                dy = pt[1] - y
                if dx*dx + dy*dy < r2:
                    wall_hit = idx
                    break
            if wall_hit != -1: break
            
        if wall_hit != -1:
            self.walls.pop(wall_hit)
            self.rebuild_static_atoms()
            return

        keep_indices = []
        for i in range(self.count):
            if self.is_static[i] == 1:
                keep_indices.append(i)
                continue
            dx = self.pos_x[i] - x
            dy = self.pos_y[i] - y
            if dx*dx + dy*dy > r2:
                keep_indices.append(i)
                
        if len(keep_indices) < self.count:
            self._compact_arrays(keep_indices)
            self.pair_count = 0

    def add_wall(self, start_pos, end_pos):
        self.walls.append({'start': start_pos, 'end': end_pos})
        self.rebuild_static_atoms()

    def update_wall(self, index, start_pos, end_pos):
        if 0 <= index < len(self.walls):
            self.walls[index]['start'] = start_pos
            self.walls[index]['end'] = end_pos
            self.rebuild_static_atoms()

    def rebuild_static_atoms(self):
        is_dynamic = self.is_static[:self.count] == 0
        dyn_indices = np.where(is_dynamic)[0]
        self._compact_arrays(dyn_indices)
        
        for wall in self.walls:
            p1 = np.array(wall['start'])
            p2 = np.array(wall['end'])
            spacing = config.ATOM_SIGMA * 0.7
            vec = p2 - p1
            length = np.linalg.norm(vec)
            if length < 1e-4: continue 
            
            num_atoms = max(1, int(length / spacing) + 1)
            for k in range(num_atoms):
                if self.count >= self.capacity: self._resize_arrays()
                t = k / max(1, num_atoms - 1) if num_atoms > 1 else 0.5
                pos = p1 + vec * t
                self.pos_x[self.count] = pos[0]
                self.pos_y[self.count] = pos[1]
                self.vel_x[self.count] = 0.0
                self.vel_y[self.count] = 0.0
                self.is_static[self.count] = 1
                self.count += 1
        self.pair_count = 0 

    def _compact_arrays(self, keep_indices):
        indices = np.array(keep_indices, dtype=np.int32)
        new_count = len(indices)
        self.pos_x[:new_count] = self.pos_x[indices]
        self.pos_y[:new_count] = self.pos_y[indices]
        self.vel_x[:new_count] = self.vel_x[indices]
        self.vel_y[:new_count] = self.vel_y[indices]
        self.is_static[:new_count] = self.is_static[indices]
        self.count = new_count

    def step(self, steps_to_run):
        if self.paused: return

        if self.total_steps % 100 == 0 and self.count > 0:
            spatial_sort(
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.vel_x[:self.count], self.vel_y[:self.count],
                self.force_x[:self.count], self.force_y[:self.count],
                self.is_static[:self.count],
                config.WORLD_SIZE, self.cell_size
            )
            self.pair_count = 0 

        rebuild = False
        if self.pair_count == 0:
            rebuild = True
        elif self.count > 0:
            rebuild = check_displacement(
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.last_x[:self.count], self.last_y[:self.count],
                self.r_skin_sq_limit
            )
            
        if rebuild and self.count > 0:
            self.pair_count = build_neighbor_list(
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.r_list2, self.cell_size, config.WORLD_SIZE,
                self.pair_i, self.pair_j
            )
            self.last_x[:self.count] = self.pos_x[:self.count]
            self.last_y[:self.count] = self.pos_y[:self.count]

        if self.count > 0:
            # CRITICAL OPTIMIZATION: Cast all scalars to float32
            # This ensures Numba generates a pure float32 kernel (AVX friendly)
            # instead of promoting everything to float64 (slow).
            f32_sigma = np.float32(config.ATOM_SIGMA)
            f32_epsilon = np.float32(config.ATOM_EPSILON)
            f32_mass = np.float32(config.ATOM_MASS)
            f32_dt = np.float32(self.dt)
            f32_gravity = np.float32(self.gravity)
            f32_rcut2 = np.float32(self.r_cut_base**2)
            f32_skin_sq = np.float32(self.r_skin_sq_limit)
            
            steps_done = integrate_n_steps(
                steps_to_run,
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.vel_x[:self.count], self.vel_y[:self.count],
                self.force_x[:self.count], self.force_y[:self.count],
                self.last_x[:self.count], self.last_y[:self.count],
                self.is_static[:self.count],
                f32_sigma, f32_epsilon, f32_mass,
                self.pair_i, self.pair_j, self.pair_count,
                f32_dt, f32_gravity, f32_rcut2,
                f32_skin_sq
            )
            
            self.total_steps += steps_done
            
            # --- SPS Calculation ---
            self.steps_accumulator += steps_done
            now = time.time()
            elapsed = now - self.last_sps_update
            if elapsed >= 0.5: # Update metric every 0.5s
                self.sps = self.steps_accumulator / elapsed
                self.steps_accumulator = 0
                self.last_sps_update = now
            
            if steps_done < steps_to_run:
                self.pair_count = 0

            if self.use_thermostat:
                # Same rigorous casting for thermostat
                apply_thermostat(
                    self.vel_x[:self.count], self.vel_y[:self.count],
                    np.float32(config.ATOM_MASS), 
                    self.is_static[:self.count],
                    np.float32(self.target_temp), 
                    np.float32(0.1)
                )
            
            # Boundary Check
            active_x = self.pos_x[:self.count]
            active_y = self.pos_y[:self.count]
            w = config.WORLD_SIZE
            is_inside = (active_x >= 0) & (active_x <= w) & \
                        (active_y >= 0) & (active_y <= w)
            
            if not np.all(is_inside):
                keep_indices = np.where(is_inside)[0]
                self._compact_arrays(keep_indices)
                self.pair_count = 0

    def _resize_arrays(self):
        self.capacity *= 2
        print(f"Resizing simulation capacity to {self.capacity}")
        self.pos_x = np.resize(self.pos_x, self.capacity)
        self.pos_y = np.resize(self.pos_y, self.capacity)
        self.vel_x = np.resize(self.vel_x, self.capacity)
        self.vel_y = np.resize(self.vel_y, self.capacity)
        self.force_x = np.resize(self.force_x, self.capacity)
        self.force_y = np.resize(self.force_y, self.capacity)
        self.is_static = np.resize(self.is_static, self.capacity)
        self.last_x = np.resize(self.last_x, self.capacity)
        self.last_y = np.resize(self.last_y, self.capacity)
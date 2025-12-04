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
        
        # State
        self.world_size = config.DEFAULT_WORLD_SIZE
        self.use_boundaries = False
        
        # Physics Parameters (Mutable)
        self.sigma = config.ATOM_SIGMA
        self.epsilon = config.ATOM_EPSILON
        
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
        
        # Control flags
        self.rebuild_next = False
        
        # Settings
        self.paused = True
        self.dt = config.DEFAULT_DT
        self.gravity = config.DEFAULT_GRAVITY
        self.target_temp = 0.5
        self.use_thermostat = False
        self.damping = config.DEFAULT_DAMPING
        
        self.r_skin = 0.3
        self.r_cut_base = 2.5
        self.r_list = self.r_cut_base + self.r_skin
        self.r_list2 = self.r_list**2
        self.r_skin_sq_limit = (0.5 * self.r_skin)**2
        self.cell_size = self.r_list
        
        self.total_steps = 0
        
        # Performance Metrics
        self.sps = 0.0
        self.steps_accumulator = 0
        self.last_sps_update = time.time()
        
        # Trigger JIT compilation immediately
        self._warmup_compiler()

    def _warmup_compiler(self):
        """
        Runs a dummy step with 2 particles to force Numba to compile
        all JIT functions immediately on startup.
        """
        print("Warming up Numba compiler...")
        
        self.pos_x[0] = 10.0; self.pos_y[0] = 10.0
        self.pos_x[1] = 12.0; self.pos_y[1] = 10.0
        self.count = 2
        
        self.pair_count = build_neighbor_list(
            self.pos_x[:2], self.pos_y[:2],
            self.r_list2, self.cell_size, self.world_size,
            self.pair_i, self.pair_j
        )
        
        # Use current sigma/epsilon for warmup
        f32_sigma = np.float32(self.sigma)
        f32_epsilon = np.float32(self.epsilon)
        f32_mass = np.float32(config.ATOM_MASS)
        f32_dt = np.float32(self.dt)
        f32_gravity = np.float32(self.gravity)
        f32_rcut2 = np.float32(self.r_cut_base**2)
        f32_skin_sq = np.float32(self.r_skin_sq_limit)
        f32_world = np.float32(self.world_size)
        f32_damping = np.float32(self.damping)
        
        integrate_n_steps(
            1,
            self.pos_x[:2], self.pos_y[:2],
            self.vel_x[:2], self.vel_y[:2],
            self.force_x[:2], self.force_y[:2],
            self.last_x[:2], self.last_y[:2],
            self.is_static[:2],
            f32_sigma, f32_epsilon, f32_mass,
            self.pair_i, self.pair_j, self.pair_count,
            f32_dt, f32_gravity, f32_rcut2,
            f32_skin_sq,
            f32_world,
            self.use_boundaries,
            f32_damping
        )
        
        check_displacement(
            self.pos_x[:2], self.pos_y[:2],
            self.last_x[:2], self.last_y[:2],
            self.r_skin_sq_limit
        )
        
        spatial_sort(
            self.pos_x[:2], self.pos_y[:2],
            self.vel_x[:2], self.vel_y[:2],
            self.force_x[:2], self.force_y[:2],
            self.is_static[:2],
            self.world_size, self.cell_size
        )
        
        apply_thermostat(
            self.vel_x[:2], self.vel_y[:2],
            f32_mass, self.is_static[:2],
            np.float32(0.5), np.float32(0.1)
        )
        
        self.clear_particles()
        print("Warmup complete.")

    def resize_world(self, new_size):
        if new_size < 100.0: new_size = 100.0
        self.world_size = new_size
        self.clear_particles()
        print(f"World resized to {self.world_size}")

    def clear_particles(self):
        self.count = 0
        self.pair_count = 0
        self.walls = []
        self.pos_x.fill(0)
        self.pos_y.fill(0)
        self.vel_x.fill(0)
        self.vel_y.fill(0)
        self.is_static.fill(0)
        self.rebuild_next = True

    def reset_simulation(self):
        self.world_size = config.DEFAULT_WORLD_SIZE
        self.dt = config.DEFAULT_DT
        self.gravity = config.DEFAULT_GRAVITY
        self.target_temp = 0.5
        self.damping = config.DEFAULT_DAMPING
        self.use_boundaries = False
        # Reset physics parameters
        self.sigma = config.ATOM_SIGMA
        self.epsilon = config.ATOM_EPSILON
        self.clear_particles()

    def add_particles_brush(self, x, y, radius):
        # Use dynamic sigma
        sigma = self.sigma
        spacing = 1.12246 * sigma  
        row_height = spacing * 0.866025 
        r_sq = radius * radius
        n_rows = int(radius / row_height) + 1
        n_cols = int(radius / spacing) + 1
        
        estimated_add = int(3.14159 * radius * radius / (spacing * row_height)) + 10
        if self.count + estimated_add >= self.capacity:
            self._resize_arrays()

        for row in range(-n_rows, n_rows + 1):
            offset_x = 0.5 * spacing if (row % 2 != 0) else 0.0
            y_curr = y + row * row_height
            for col in range(-n_cols, n_cols + 1):
                x_curr = x + col * spacing + offset_x
                dx = x_curr - x
                dy = y_curr - y
                if dx*dx + dy*dy <= r_sq:
                    if 0 < x_curr < self.world_size and 0 < y_curr < self.world_size:
                        if not self._check_overlap(x_curr, y_curr, 0.8 * sigma):
                            if self.count >= self.capacity: self._resize_arrays()
                            idx = self.count
                            self.pos_x[idx] = x_curr
                            self.pos_y[idx] = y_curr
                            self.vel_x[idx] = 0.0
                            self.vel_y[idx] = 0.0
                            self.is_static[idx] = 0 
                            self.count += 1
        self.rebuild_next = True

    def _check_overlap(self, x, y, threshold):
        if self.count == 0: return False
        threshold_sq = threshold * threshold
        dx = self.pos_x[:self.count] - x
        dy = self.pos_y[:self.count] - y
        dist_sq = dx*dx + dy*dy
        if np.any(dist_sq < threshold_sq):
            return True
        return False

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
            self.rebuild_next = True

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
            # Use dynamic sigma
            spacing = self.sigma * 0.7
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
        self.rebuild_next = True

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
                self.world_size, self.cell_size
            )
            self.rebuild_next = True

        should_rebuild = False
        if self.pair_count == 0 or self.rebuild_next:
            should_rebuild = True
        elif self.count > 0:
            should_rebuild = check_displacement(
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.last_x[:self.count], self.last_y[:self.count],
                self.r_skin_sq_limit
            )

        if should_rebuild and self.count > 0:
            while True:
                count = build_neighbor_list(
                    self.pos_x[:self.count], self.pos_y[:self.count],
                    self.r_list2, self.cell_size, self.world_size,
                    self.pair_i, self.pair_j
                )
                
                if count >= self.max_pairs:
                    print(f"Pair list overflow ({count} >= {self.max_pairs}). Resizing...")
                    self.max_pairs *= 2
                    self.pair_i = np.zeros(self.max_pairs, dtype=np.int32)
                    self.pair_j = np.zeros(self.max_pairs, dtype=np.int32)
                    continue 
                
                self.pair_count = count
                break 
            
            self.last_x[:self.count] = self.pos_x[:self.count]
            self.last_y[:self.count] = self.pos_y[:self.count]
            self.rebuild_next = False

        if self.count > 0:
            # Pass dynamic sigma/epsilon
            f32_sigma = np.float32(self.sigma)
            f32_epsilon = np.float32(self.epsilon)
            f32_mass = np.float32(config.ATOM_MASS)
            f32_dt = np.float32(self.dt)
            f32_gravity = np.float32(self.gravity)
            f32_rcut2 = np.float32(self.r_cut_base**2)
            f32_skin_sq = np.float32(self.r_skin_sq_limit)
            f32_world = np.float32(self.world_size)
            f32_damping = np.float32(self.damping)
            
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
                f32_skin_sq,
                f32_world,
                self.use_boundaries,
                f32_damping
            )
            
            self.total_steps += steps_done
            self.steps_accumulator += steps_done
            now = time.time()
            elapsed = now - self.last_sps_update
            if elapsed >= 0.5:
                self.sps = self.steps_accumulator / elapsed
                self.steps_accumulator = 0
                self.last_sps_update = now
            
            if steps_done < steps_to_run:
                self.rebuild_next = True

            if self.use_thermostat:
                apply_thermostat(
                    self.vel_x[:self.count], self.vel_y[:self.count],
                    np.float32(config.ATOM_MASS), 
                    self.is_static[:self.count],
                    np.float32(self.target_temp), 
                    np.float32(0.1)
                )
            
            active_x = self.pos_x[:self.count]
            active_y = self.pos_y[:self.count]
            w = self.world_size
            is_inside = (active_x >= 0) & (active_x <= w) & \
                        (active_y >= 0) & (active_y <= w)
            
            if not np.all(is_inside):
                keep_indices = np.where(is_inside)[0]
                self._compact_arrays(keep_indices)
                self.rebuild_next = True

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
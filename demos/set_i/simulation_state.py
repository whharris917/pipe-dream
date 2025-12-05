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
        
        # Global Physics Parameters (for Gas)
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
        
        # New: Per-Particle Properties
        self.atom_sigma = np.zeros(self.capacity, dtype=np.float32)
        self.atom_eps_sqrt = np.zeros(self.capacity, dtype=np.float32)
        
        self.walls = [] # List of dicts
        
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
        
        self.sps = 0.0
        self.steps_accumulator = 0
        self.last_sps_update = time.time()
        
        self._warmup_compiler()

    def _warmup_compiler(self):
        print("Warming up Numba compiler...")
        self.pos_x[0] = 10.0; self.pos_y[0] = 10.0
        self.pos_x[1] = 12.0; self.pos_y[1] = 10.0
        self.count = 2
        # Fill props for warmup
        self.atom_sigma[:2] = 1.0
        self.atom_eps_sqrt[:2] = 1.0
        
        build_neighbor_list(self.pos_x[:2], self.pos_y[:2], self.r_list2, self.cell_size, self.world_size, self.pair_i, self.pair_j)
        
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
            self.atom_sigma[:2], self.atom_eps_sqrt[:2], f32_mass,
            self.pair_i, self.pair_j, self.pair_count,
            f32_dt, f32_gravity, f32_rcut2, f32_skin_sq, f32_world, self.use_boundaries, f32_damping
        )
        
        spatial_sort(
            self.pos_x[:2], self.pos_y[:2],
            self.vel_x[:2], self.vel_y[:2],
            self.force_x[:2], self.force_y[:2],
            self.is_static[:2],
            self.atom_sigma[:2], self.atom_eps_sqrt[:2],
            self.world_size, self.cell_size
        )
        self.clear_particles()
        print("Warmup complete.")

    def resize_world(self, new_size):
        if new_size < 100.0: new_size = 100.0
        self.world_size = new_size
        self.clear_particles()

    def clear_particles(self):
        self.count = 0
        self.pair_count = 0
        self.walls = []
        self.pos_x.fill(0); self.pos_y.fill(0)
        self.vel_x.fill(0); self.vel_y.fill(0)
        self.is_static.fill(0)
        self.rebuild_next = True

    def reset_simulation(self):
        self.world_size = config.DEFAULT_WORLD_SIZE
        self.dt = config.DEFAULT_DT
        self.gravity = config.DEFAULT_GRAVITY
        self.target_temp = 0.5
        self.damping = config.DEFAULT_DAMPING
        self.use_boundaries = False
        self.sigma = config.ATOM_SIGMA
        self.epsilon = config.ATOM_EPSILON
        self.clear_particles()

    def add_particles_brush(self, x, y, radius):
        sigma = self.sigma
        spacing = 1.12246 * sigma  
        row_height = spacing * 0.866025 
        r_sq = radius * radius
        n_rows = int(radius / row_height) + 1
        n_cols = int(radius / spacing) + 1
        
        estimated_add = int(3.14159 * radius * radius / (spacing * row_height)) + 10
        if self.count + estimated_add >= self.capacity: self._resize_arrays()

        for row in range(-n_rows, n_rows + 1):
            offset_x = 0.5 * spacing if (row % 2 != 0) else 0.0
            y_curr = y + row * row_height
            for col in range(-n_cols, n_cols + 1):
                x_curr = x + col * spacing + offset_x
                dx = x_curr - x; dy = y_curr - y
                if dx*dx + dy*dy <= r_sq:
                    if 0 < x_curr < self.world_size and 0 < y_curr < self.world_size:
                        if not self._check_overlap(x_curr, y_curr, 0.8 * sigma):
                            if self.count >= self.capacity: self._resize_arrays()
                            idx = self.count
                            self.pos_x[idx] = x_curr
                            self.pos_y[idx] = y_curr
                            self.vel_x[idx] = 0.0; self.vel_y[idx] = 0.0
                            self.is_static[idx] = 0 
                            # Initialize props
                            self.atom_sigma[idx] = self.sigma
                            self.atom_eps_sqrt[idx] = math.sqrt(self.epsilon)
                            self.count += 1
        self.rebuild_next = True

    def _check_overlap(self, x, y, threshold):
        if self.count == 0: return False
        threshold_sq = threshold * threshold
        dx = self.pos_x[:self.count] - x
        dy = self.pos_y[:self.count] - y
        dist_sq = dx*dx + dy*dy
        if np.any(dist_sq < threshold_sq): return True
        return False

    def delete_particles_brush(self, x, y, radius):
        r2 = radius**2
        
        # Don't delete wall handles via brush anymore, use context menu
        # Just delete dynamic particles
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
        # Default props
        self.walls.append({
            'start': start_pos, 
            'end': end_pos,
            'sigma': config.ATOM_SIGMA,
            'epsilon': config.ATOM_EPSILON,
            'spacing': 0.7 * config.ATOM_SIGMA
        })
        self.rebuild_static_atoms()

    def update_wall(self, index, start_pos, end_pos):
        if 0 <= index < len(self.walls):
            self.walls[index]['start'] = start_pos
            self.walls[index]['end'] = end_pos
            self.rebuild_static_atoms()

    def remove_wall(self, index):
        if 0 <= index < len(self.walls):
            self.walls.pop(index)
            self.rebuild_static_atoms()

    def update_wall_props(self, index, props):
        if 0 <= index < len(self.walls):
            w = self.walls[index]
            w['sigma'] = props['sigma']
            w['epsilon'] = props['epsilon']
            w['spacing'] = props['spacing']
            self.rebuild_static_atoms()

    def rebuild_static_atoms(self):
        # Keep dynamic atoms
        is_dynamic = self.is_static[:self.count] == 0
        dyn_indices = np.where(is_dynamic)[0]
        self._compact_arrays(dyn_indices)
        
        for wall in self.walls:
            p1 = np.array(wall['start'])
            p2 = np.array(wall['end'])
            # Use wall-specific spacing
            spacing = wall.get('spacing', 0.7)
            
            vec = p2 - p1
            length = np.linalg.norm(vec)
            if length < 1e-4: continue 
            
            num_atoms = max(1, int(length / spacing) + 1)
            
            w_sigma = wall.get('sigma', 1.0)
            w_eps_sqrt = math.sqrt(wall.get('epsilon', 1.0))
            
            for k in range(num_atoms):
                if self.count >= self.capacity: self._resize_arrays()
                t = k / max(1, num_atoms - 1) if num_atoms > 1 else 0.5
                pos = p1 + vec * t
                self.pos_x[self.count] = pos[0]
                self.pos_y[self.count] = pos[1]
                self.vel_x[self.count] = 0.0
                self.vel_y[self.count] = 0.0
                self.is_static[self.count] = 1
                
                # Apply wall props
                self.atom_sigma[self.count] = w_sigma
                self.atom_eps_sqrt[self.count] = w_eps_sqrt
                
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
        self.atom_sigma[:new_count] = self.atom_sigma[indices]
        self.atom_eps_sqrt[:new_count] = self.atom_eps_sqrt[indices]
        self.count = new_count

    def step(self, steps_to_run):
        if self.paused: return

        # 1. SYNC DYNAMIC PARTICLES WITH GLOBAL SLIDERS
        # This allows real-time tuning of gas properties
        is_dyn = self.is_static[:self.count] == 0
        if np.any(is_dyn):
            # Fill dynamic atoms with current global sigma/epsilon
            self.atom_sigma[:self.count][is_dyn] = self.sigma
            self.atom_eps_sqrt[:self.count][is_dyn] = math.sqrt(self.epsilon)

        if self.total_steps % 100 == 0 and self.count > 0:
            spatial_sort(
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.vel_x[:self.count], self.vel_y[:self.count],
                self.force_x[:self.count], self.force_y[:self.count],
                self.is_static[:self.count],
                self.atom_sigma[:self.count], self.atom_eps_sqrt[:self.count],
                self.world_size, self.cell_size
            )
            self.rebuild_next = True

        should_rebuild = False
        if self.pair_count == 0 or self.rebuild_next: should_rebuild = True
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
            steps_done = integrate_n_steps(
                steps_to_run,
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.vel_x[:self.count], self.vel_y[:self.count],
                self.force_x[:self.count], self.force_y[:self.count],
                self.last_x[:self.count], self.last_y[:self.count],
                self.is_static[:self.count],
                self.atom_sigma[:self.count], self.atom_eps_sqrt[:self.count], 
                np.float32(config.ATOM_MASS),
                self.pair_i, self.pair_j, self.pair_count,
                np.float32(self.dt), np.float32(self.gravity), np.float32(self.r_cut_base**2),
                np.float32(self.r_skin_sq_limit), np.float32(self.world_size), 
                self.use_boundaries, np.float32(self.damping)
            )
            
            self.total_steps += steps_done
            self.steps_accumulator += steps_done
            now = time.time()
            elapsed = now - self.last_sps_update
            if elapsed >= 0.5:
                self.sps = self.steps_accumulator / elapsed
                self.steps_accumulator = 0
                self.last_sps_update = now
            
            if steps_done < steps_to_run: self.rebuild_next = True

            if self.use_thermostat:
                apply_thermostat(
                    self.vel_x[:self.count], self.vel_y[:self.count],
                    np.float32(config.ATOM_MASS), self.is_static[:self.count],
                    np.float32(self.target_temp), np.float32(0.1)
                )
            
            active_x = self.pos_x[:self.count]
            active_y = self.pos_y[:self.count]
            w = self.world_size
            is_inside = (active_x >= 0) & (active_x <= w) & (active_y >= 0) & (active_y <= w)
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
        self.atom_sigma = np.resize(self.atom_sigma, self.capacity)
        self.atom_eps_sqrt = np.resize(self.atom_eps_sqrt, self.capacity)
        self.last_x = np.resize(self.last_x, self.capacity)
        self.last_y = np.resize(self.last_y, self.capacity)
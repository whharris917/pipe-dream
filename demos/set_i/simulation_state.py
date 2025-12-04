import numpy as np
import random
import math
import config
from physics_core import integrate_n_steps, build_neighbor_list, check_displacement, apply_thermostat, spatial_sort

class Simulation:
    def __init__(self):
        # Capacity
        self.capacity = 5000
        self.count = 0
        
        # Physics State Arrays
        self.pos_x = np.zeros(self.capacity, dtype=np.float32)
        self.pos_y = np.zeros(self.capacity, dtype=np.float32)
        self.vel_x = np.zeros(self.capacity, dtype=np.float32)
        self.vel_y = np.zeros(self.capacity, dtype=np.float32)
        self.force_x = np.zeros(self.capacity, dtype=np.float32)
        self.force_y = np.zeros(self.capacity, dtype=np.float32)
        self.atom_types = np.zeros(self.capacity, dtype=np.int32)
        self.is_static = np.zeros(self.capacity, dtype=np.int32)
        
        # Wall Definitions (Lines)
        # List of dicts: {'start': (x,y), 'end': (x,y), 'type': int}
        self.walls = []
        
        # Neighbor List
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
        self.damping = config.DEFAULT_DAMPING
        
        self.r_skin = 0.3
        self.r_cut_base = 2.5
        self.r_list = self.r_cut_base + self.r_skin
        self.r_list2 = self.r_list**2
        self.r_skin_sq_limit = (0.5 * self.r_skin)**2
        self.cell_size = self.r_list
        
        self.total_steps = 0
        
        # Optimization: Pre-calculate Mixing Matrices
        self.matrix_sigma2 = np.zeros((config.MAX_TYPES, config.MAX_TYPES), dtype=np.float32)
        self.matrix_epsilon24 = np.zeros((config.MAX_TYPES, config.MAX_TYPES), dtype=np.float32)
        
        for i in range(config.MAX_TYPES):
            for j in range(config.MAX_TYPES):
                s_i = config.TYPE_SIGMA[i]
                s_j = config.TYPE_SIGMA[j]
                e_i = config.TYPE_EPSILON[i]
                e_j = config.TYPE_EPSILON[j]
                
                s_ij = (s_i + s_j) * 0.5
                e_ij = math.sqrt(e_i * e_j)
                
                self.matrix_sigma2[i, j] = s_ij * s_ij
                self.matrix_epsilon24[i, j] = 24.0 * e_ij

    def add_particles_brush(self, x, y, type_id, radius, density=0.5):
        """Paint particles into the world at x,y with specific type"""
        if config.ATOM_TYPES[type_id]["static"] == 1:
            # Static atoms are now handled by add_wall, not the brush
            return

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
                self.atom_types[idx] = type_id
                self.is_static[idx] = 0 # Brush only paints dynamic now
                self.count += 1
                
        self.pair_count = 0

    def delete_particles_brush(self, x, y, radius):
        """Remove particles within radius of x,y"""
        r2 = radius**2
        
        # 1. Detect if we are deleting a wall endpoint
        # If so, remove the wall entirely
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

        # 2. Delete Free Particles
        # Filter logic to keep particles NOT in radius
        # Only check dynamic particles to avoid breaking walls partially
        keep_indices = []
        for i in range(self.count):
            if self.is_static[i] == 1:
                keep_indices.append(i) # Keep walls, they are deleted by endpoint only
                continue
                
            dx = self.pos_x[i] - x
            dy = self.pos_y[i] - y
            if dx*dx + dy*dy > r2:
                keep_indices.append(i)
                
        if len(keep_indices) < self.count:
            self._compact_arrays(keep_indices)
            self.pair_count = 0

    # --- Wall Management ---
    def add_wall(self, start_pos, end_pos, type_id):
        self.walls.append({
            'start': start_pos,
            'end': end_pos,
            'type': type_id
        })
        self.rebuild_static_atoms()

    def update_wall(self, index, start_pos, end_pos):
        if 0 <= index < len(self.walls):
            self.walls[index]['start'] = start_pos
            self.walls[index]['end'] = end_pos
            self.rebuild_static_atoms()

    def rebuild_static_atoms(self):
        """Regenerates all static atoms based on current wall definitions."""
        # 1. Identify dynamic atoms
        is_dynamic = self.is_static[:self.count] == 0
        dyn_indices = np.where(is_dynamic)[0]
        
        # 2. Compact arrays to remove old static atoms
        self._compact_arrays(dyn_indices)
        
        # 3. Generate new static atoms from walls
        for wall in self.walls:
            p1 = np.array(wall['start'])
            p2 = np.array(wall['end'])
            tid = wall['type']
            
            # Determine spacing
            sigma = config.ATOM_TYPES[tid]['sigma']
            spacing = sigma * 0.7 # Tight packing
            
            vec = p2 - p1
            length = np.linalg.norm(vec)
            
            if length < 1e-4: continue # Too short
            
            num_atoms = max(1, int(length / spacing) + 1)
            
            for k in range(num_atoms):
                if self.count >= self.capacity: self._resize_arrays()
                
                t = k / max(1, num_atoms - 1) if num_atoms > 1 else 0.5
                pos = p1 + vec * t
                
                self.pos_x[self.count] = pos[0]
                self.pos_y[self.count] = pos[1]
                self.vel_x[self.count] = 0.0
                self.vel_y[self.count] = 0.0
                self.atom_types[self.count] = tid
                self.is_static[self.count] = 1
                self.count += 1
        
        self.pair_count = 0 # Force physics rebuild

    def _compact_arrays(self, keep_indices):
        indices = np.array(keep_indices, dtype=np.int32)
        new_count = len(indices)
        
        self.pos_x[:new_count] = self.pos_x[indices]
        self.pos_y[:new_count] = self.pos_y[indices]
        self.vel_x[:new_count] = self.vel_x[indices]
        self.vel_y[:new_count] = self.vel_y[indices]
        self.atom_types[:new_count] = self.atom_types[indices]
        self.is_static[:new_count] = self.is_static[indices]
        
        self.count = new_count

    def step(self, steps_to_run):
        if self.paused: return # Allow 0 count for editing

        if self.total_steps % 100 == 0 and self.count > 0:
            spatial_sort(
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.vel_x[:self.count], self.vel_y[:self.count],
                self.force_x[:self.count], self.force_y[:self.count],
                self.atom_types[:self.count], self.is_static[:self.count],
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
            steps_done = integrate_n_steps(
                steps_to_run,
                self.pos_x[:self.count], self.pos_y[:self.count],
                self.vel_x[:self.count], self.vel_y[:self.count],
                self.force_x[:self.count], self.force_y[:self.count],
                self.last_x[:self.count], self.last_y[:self.count],
                self.atom_types[:self.count], self.is_static[:self.count],
                self.matrix_sigma2, self.matrix_epsilon24, config.TYPE_MASS,
                self.pair_i, self.pair_j, self.pair_count,
                self.dt, self.gravity, self.damping, self.r_cut_base**2,
                self.r_skin_sq_limit
            )
            
            self.total_steps += steps_done
            if steps_done < steps_to_run:
                self.pair_count = 0

            if self.use_thermostat:
                apply_thermostat(
                    self.vel_x[:self.count], self.vel_y[:self.count],
                    self.atom_types[:self.count], config.TYPE_MASS, 
                    self.is_static[:self.count],
                    self.target_temp, 0.1
                )

    def _resize_arrays(self):
        self.capacity *= 2
        print(f"Resizing simulation capacity to {self.capacity}")
        self.pos_x = np.resize(self.pos_x, self.capacity)
        self.pos_y = np.resize(self.pos_y, self.capacity)
        self.vel_x = np.resize(self.vel_x, self.capacity)
        self.vel_y = np.resize(self.vel_y, self.capacity)
        self.force_x = np.resize(self.force_x, self.capacity)
        self.force_y = np.resize(self.force_y, self.capacity)
        self.atom_types = np.resize(self.atom_types, self.capacity)
        self.is_static = np.resize(self.is_static, self.capacity)
        self.last_x = np.resize(self.last_x, self.capacity)
        self.last_y = np.resize(self.last_y, self.capacity)
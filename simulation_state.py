import numpy as np
import random
import math
import time
import copy
import config
from physics_core import integrate_n_steps, build_neighbor_list, check_displacement, apply_thermostat, spatial_sort
from constraint_solver import solve_constraints

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
        
        # New: Mutable Skin Distance
        self.skin_distance = config.DEFAULT_SKIN_DISTANCE
        
        # Physics State Arrays
        self.pos_x = np.zeros(self.capacity, dtype=np.float32)
        self.pos_y = np.zeros(self.capacity, dtype=np.float32)
        self.vel_x = np.zeros(self.capacity, dtype=np.float32)
        self.vel_y = np.zeros(self.capacity, dtype=np.float32)
        self.force_x = np.zeros(self.capacity, dtype=np.float32)
        self.force_y = np.zeros(self.capacity, dtype=np.float32)
        
        # 0=Dynamic, 1=Static, 2=Kinematic
        self.is_static = np.zeros(self.capacity, dtype=np.int32)
        
        # Kinematic Props: [pivot_x, pivot_y, omega]
        self.kinematic_props = np.zeros((self.capacity, 3), dtype=np.float32)
        
        # Per-Particle Properties
        self.atom_sigma = np.zeros(self.capacity, dtype=np.float32)
        self.atom_eps_sqrt = np.zeros(self.capacity, dtype=np.float32)
        
        self.walls = [] # List of dicts
        self.constraints = [] # List of constraint dicts
        
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
        
        self.r_cut_base = 2.5
        self._update_derived_params()
        
        self.total_steps = 0
        self.sps = 0.0
        self.steps_accumulator = 0
        self.last_sps_update = time.time()
        
        self.undo_stack = []
        self.redo_stack = []
        
        self._warmup_compiler()

    def _update_derived_params(self):
        self.r_list = self.r_cut_base + self.skin_distance
        self.r_list2 = self.r_list**2
        self.r_skin_sq_limit = (0.5 * self.skin_distance)**2
        self.cell_size = self.r_list

    def _warmup_compiler(self):
        print("Warming up Numba compiler...")
        self.pos_x[0] = 10.0; self.pos_y[0] = 10.0
        self.pos_x[1] = 12.0; self.pos_y[1] = 10.0
        self.count = 2
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
        integrate_n_steps(1, self.pos_x[:2], self.pos_y[:2], self.vel_x[:2], self.vel_y[:2], self.force_x[:2], self.force_y[:2], self.last_x[:2], self.last_y[:2], self.is_static[:2], self.kinematic_props[:2], self.atom_sigma[:2], self.atom_eps_sqrt[:2], f32_mass, self.pair_i, self.pair_j, self.pair_count, f32_dt, f32_gravity, f32_rcut2, f32_skin_sq, f32_world, self.use_boundaries, f32_damping)
        spatial_sort(self.pos_x[:2], self.pos_y[:2], self.vel_x[:2], self.vel_y[:2], self.force_x[:2], self.force_y[:2], self.is_static[:2], self.kinematic_props[:2], self.atom_sigma[:2], self.atom_eps_sqrt[:2], self.world_size, self.cell_size)
        self.clear_particles()
        print("Warmup complete.")

    def snapshot(self):
        state = {
            'count': self.count,
            'pos_x': np.copy(self.pos_x[:self.count]),
            'pos_y': np.copy(self.pos_y[:self.count]),
            'vel_x': np.copy(self.vel_x[:self.count]),
            'vel_y': np.copy(self.vel_y[:self.count]),
            'is_static': np.copy(self.is_static[:self.count]),
            'kinematic_props': np.copy(self.kinematic_props[:self.count]),
            'atom_sigma': np.copy(self.atom_sigma[:self.count]),
            'atom_eps_sqrt': np.copy(self.atom_eps_sqrt[:self.count]),
            'walls': copy.deepcopy(self.walls),
            'constraints': copy.deepcopy(self.constraints),
            'world_size': self.world_size
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > 50: self.undo_stack.pop(0)
        self.redo_stack.clear()

    def restore_state(self, state):
        self.count = state['count']
        if self.count > self.capacity:
            while self.capacity < self.count: self.capacity *= 2
            self._resize_arrays()
        self.pos_x[:self.count] = state['pos_x']
        self.pos_y[:self.count] = state['pos_y']
        self.vel_x[:self.count] = state['vel_x']
        self.vel_y[:self.count] = state['vel_y']
        self.is_static[:self.count] = state['is_static']
        if 'kinematic_props' in state: self.kinematic_props[:self.count] = state['kinematic_props']
        else: self.kinematic_props[:self.count] = 0.0
        self.atom_sigma[:self.count] = state['atom_sigma']
        self.atom_eps_sqrt[:self.count] = state['atom_eps_sqrt']
        self.walls = copy.deepcopy(state['walls'])
        self.constraints = copy.deepcopy(state.get('constraints', []))
        self.world_size = state['world_size']
        self.rebuild_next = True
        self.pair_count = 0 

    def undo(self):
        if not self.undo_stack: return
        current_state = {
            'count': self.count, 'pos_x': np.copy(self.pos_x[:self.count]), 'pos_y': np.copy(self.pos_y[:self.count]), 'vel_x': np.copy(self.vel_x[:self.count]), 'vel_y': np.copy(self.vel_y[:self.count]),
            'is_static': np.copy(self.is_static[:self.count]), 'kinematic_props': np.copy(self.kinematic_props[:self.count]), 'atom_sigma': np.copy(self.atom_sigma[:self.count]), 'atom_eps_sqrt': np.copy(self.atom_eps_sqrt[:self.count]),
            'walls': copy.deepcopy(self.walls), 'constraints': copy.deepcopy(self.constraints), 'world_size': self.world_size
        }
        self.redo_stack.append(current_state)
        prev_state = self.undo_stack.pop()
        self.restore_state(prev_state)

    def redo(self):
        if not self.redo_stack: return
        current_state = {
            'count': self.count, 'pos_x': np.copy(self.pos_x[:self.count]), 'pos_y': np.copy(self.pos_y[:self.count]), 'vel_x': np.copy(self.vel_x[:self.count]), 'vel_y': np.copy(self.vel_y[:self.count]),
            'is_static': np.copy(self.is_static[:self.count]), 'kinematic_props': np.copy(self.kinematic_props[:self.count]), 'atom_sigma': np.copy(self.atom_sigma[:self.count]), 'atom_eps_sqrt': np.copy(self.atom_eps_sqrt[:self.count]),
            'walls': copy.deepcopy(self.walls), 'constraints': copy.deepcopy(self.constraints), 'world_size': self.world_size
        }
        self.undo_stack.append(current_state)
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)

    def resize_world(self, new_size):
        self.snapshot()
        if new_size < 100.0: new_size = 100.0
        self.world_size = new_size
        self.clear_particles(snapshot=False)

    def clear_particles(self, snapshot=True):
        if snapshot: self.snapshot()
        self.count = 0
        self.pair_count = 0
        self.walls = []
        self.constraints = []
        self.pos_x.fill(0); self.pos_y.fill(0)
        self.vel_x.fill(0); self.vel_y.fill(0)
        self.is_static.fill(0)
        self.kinematic_props.fill(0)
        self.rebuild_next = True

    def reset_simulation(self):
        self.snapshot()
        self.world_size = config.DEFAULT_WORLD_SIZE
        self.dt = config.DEFAULT_DT
        self.gravity = config.DEFAULT_GRAVITY
        self.target_temp = 0.5
        self.damping = config.DEFAULT_DAMPING
        self.use_boundaries = False
        self.sigma = config.ATOM_SIGMA
        self.epsilon = config.ATOM_EPSILON
        self.skin_distance = config.DEFAULT_SKIN_DISTANCE
        self._update_derived_params()
        self.clear_particles(snapshot=False)

    def export_asset_data(self):
        if not self.walls: return None
        min_x = float('inf'); max_x = float('-inf'); min_y = float('inf'); max_y = float('-inf')
        for w in self.walls:
            for p in [w['start'], w['end']]:
                min_x = min(min_x, p[0]); max_x = max(max_x, p[0]); min_y = min(min_y, p[1]); max_y = max(max_y, p[1])
        center_x = (min_x + max_x) / 2.0; center_y = (min_y + max_y) / 2.0
        normalized_walls = []
        for w in self.walls:
            nw = copy.deepcopy(w)
            nw['start'] = (w['start'][0] - center_x, w['start'][1] - center_y)
            nw['end'] = (w['end'][0] - center_x, w['end'][1] - center_y)
            if 'anim' in nw and nw['anim']:
                anim = nw['anim']
                rs = anim['ref_start']; re = anim['ref_end']
                anim['ref_start'] = (rs[0] - center_x, rs[1] - center_y); anim['ref_end'] = (re[0] - center_x, re[1] - center_y)
            normalized_walls.append(nw)
        return {'walls': normalized_walls, 'constraints': self.constraints}

    def place_asset(self, asset_data, x, y):
        self.snapshot()
        walls_to_add = asset_data.get('walls', [])
        constraints_to_add = asset_data.get('constraints', [])
        base_index = len(self.walls)
        for w in walls_to_add:
            new_w = copy.deepcopy(w)
            new_w['start'] = (w['start'][0] + x, w['start'][1] + y)
            new_w['end'] = (w['end'][0] + x, w['end'][1] + y)
            if 'anim' in new_w and new_w['anim']:
                anim = new_w['anim']
                rs = anim['ref_start']; re = anim['ref_end']
                anim['ref_start'] = (rs[0] + x, rs[1] + y); anim['ref_end'] = (re[0] + x, re[1] + y)
            self.walls.append(new_w)
        for c in constraints_to_add:
            new_c = copy.deepcopy(c)
            new_indices = []
            for idx in new_c['indices']:
                if isinstance(idx, (list, tuple)): new_indices.append((idx[0] + base_index, idx[1]))
                else: new_indices.append(idx + base_index)
            new_c['indices'] = new_indices
            self.constraints.append(new_c)
        self.rebuild_static_atoms()

    def set_wall_rotation(self, index, params):
        if 0 <= index < len(self.walls):
            w = self.walls[index]
            speed = params['speed']; pivot = params['pivot']
            if abs(speed) < 1e-5: w['anim'] = None; return
            w['anim'] = {'type': 'rotate', 'speed': speed, 'pivot': pivot, 'angle': 0.0, 'ref_start': w['start'], 'ref_end': w['end']}
            self.rebuild_static_atoms()

    def update_animations(self, dt):
        for w in self.walls:
            anim = w.get('anim')
            if anim and anim['type'] == 'rotate':
                anim['angle'] += anim['speed'] * dt
                rad = math.radians(anim['angle']); c = math.cos(rad); s = math.sin(rad)
                rs = np.array(anim['ref_start']); re = np.array(anim['ref_end'])
                if anim['pivot'] == 'start': pivot = rs
                elif anim['pivot'] == 'end': pivot = re
                else: pivot = (rs + re) * 0.5
                v_s = rs - pivot; v_e = re - pivot
                w['start'] = tuple(np.array([v_s[0]*c - v_s[1]*s, v_s[0]*s + v_s[1]*c]) + pivot)
                w['end'] = tuple(np.array([v_e[0]*c - v_e[1]*s, v_e[0]*s + v_e[1]*c]) + pivot)

    def apply_constraints(self):
        if self.constraints:
            solve_constraints(self.walls, self.constraints, iterations=20)
            self.rebuild_static_atoms()

    def add_constraint(self, c_type, indices, value=None):
        self.snapshot()
        c = {'type': c_type, 'indices': indices}
        if value is not None: c['value'] = value
        self.constraints.append(c)
        self.apply_constraints()

    def remove_wall(self, index):
        self.snapshot()
        if 0 <= index < len(self.walls):
            # 1. Remove constraints involving this wall
            self.constraints = [c for c in self.constraints if not self._constraint_involves(c, index)]
            
            # 2. Shift indices for remaining constraints
            for c in self.constraints:
                new_indices = []
                for idx in c['indices']:
                    if isinstance(idx, (list, tuple)):
                        w_idx, pt_idx = idx
                        if w_idx > index: w_idx -= 1
                        new_indices.append((w_idx, pt_idx))
                    else:
                        if idx > index: idx -= 1
                        new_indices.append(idx)
                c['indices'] = new_indices

            self.walls.pop(index)
            self.rebuild_static_atoms()

    def _constraint_involves(self, c, wall_idx):
        for idx in c['indices']:
            if isinstance(idx, (list, tuple)):
                if idx[0] == wall_idx: return True
            else:
                if idx == wall_idx: return True
        return False

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
        keep_indices = []
        for i in range(self.count):
            if self.is_static[i] == 1 or self.is_static[i] == 2:
                keep_indices.append(i)
                continue
            dx = self.pos_x[i] - x
            dy = self.pos_y[i] - y
            if dx*dx + dy*dy > r2:
                keep_indices.append(i)
        if len(keep_indices) < self.count:
            self._compact_arrays(keep_indices)
            self.rebuild_next = True

    def add_wall(self, start_pos, end_pos, is_ref=False):
        self.walls.append({
            'start': start_pos, 'end': end_pos, 
            'sigma': config.ATOM_SIGMA, 'epsilon': config.ATOM_EPSILON, 'spacing': 0.7 * config.ATOM_SIGMA, 
            'anim': None, 'anchored': [False, False],
            'ref': is_ref
        })
        self.rebuild_static_atoms()

    def toggle_anchor(self, wall_idx, pt_idx):
        if 0 <= wall_idx < len(self.walls):
            w = self.walls[wall_idx]
            if 'anchored' not in w: w['anchored'] = [False, False]
            w['anchored'][pt_idx] = not w['anchored'][pt_idx]
            self.snapshot()
            self.rebuild_static_atoms()

    def update_wall(self, index, start_pos, end_pos):
        if 0 <= index < len(self.walls):
            self.walls[index]['start'] = start_pos
            self.walls[index]['end'] = end_pos
            self.rebuild_static_atoms()

    def update_wall_props(self, index, props):
        self.snapshot()
        if 0 <= index < len(self.walls):
            w = self.walls[index]
            w['sigma'] = props['sigma']; w['epsilon'] = props['epsilon']; w['spacing'] = props['spacing']
            self.rebuild_static_atoms()

    def rebuild_static_atoms(self):
        is_dynamic = self.is_static[:self.count] == 0
        dyn_indices = np.where(is_dynamic)[0]
        self._compact_arrays(dyn_indices)
        for wall in self.walls:
            # Check for Reference Line - do not generate atoms
            if wall.get('ref'): continue

            p1 = np.array(wall['start']); p2 = np.array(wall['end'])
            spacing = wall.get('spacing', 0.7)
            vec = p2 - p1; length = np.linalg.norm(vec)
            if length < 1e-4: continue 
            num_atoms = max(1, int(length / spacing) + 1)
            w_sigma = wall.get('sigma', 1.0); w_eps_sqrt = math.sqrt(wall.get('epsilon', 1.0))
            anim = wall.get('anim'); is_rotating = False; pivot = np.zeros(2); omega = 0.0
            if anim and anim['type'] == 'rotate':
                is_rotating = True; omega = math.radians(anim['speed'])
                w_s = np.array(wall['start']); w_e = np.array(wall['end'])
                if anim['pivot'] == 'start': pivot = w_s
                elif anim['pivot'] == 'end': pivot = w_e
                else: pivot = (w_s + w_e) * 0.5
            for k in range(num_atoms):
                if self.count >= self.capacity: self._resize_arrays()
                t = k / max(1, num_atoms - 1) if num_atoms > 1 else 0.5
                pos = p1 + vec * t
                self.pos_x[self.count] = pos[0]; self.pos_y[self.count] = pos[1]
                self.vel_x[self.count] = 0.0; self.vel_y[self.count] = 0.0
                if is_rotating:
                    self.is_static[self.count] = 2
                    self.kinematic_props[self.count, 0] = pivot[0]
                    self.kinematic_props[self.count, 1] = pivot[1]
                    self.kinematic_props[self.count, 2] = omega
                else:
                    self.is_static[self.count] = 1
                    self.kinematic_props[self.count, :] = 0.0
                self.atom_sigma[self.count] = w_sigma; self.atom_eps_sqrt[self.count] = w_eps_sqrt
                self.count += 1
        self.rebuild_next = True

    def _compact_arrays(self, keep_indices):
        indices = np.array(keep_indices, dtype=np.int32)
        new_count = len(indices)
        self.pos_x[:new_count] = self.pos_x[indices]; self.pos_y[:new_count] = self.pos_y[indices]
        self.vel_x[:new_count] = self.vel_x[indices]; self.vel_y[:new_count] = self.vel_y[indices]
        self.is_static[:new_count] = self.is_static[indices]
        self.kinematic_props[:new_count] = self.kinematic_props[indices]
        self.atom_sigma[:new_count] = self.atom_sigma[indices]
        self.atom_eps_sqrt[:new_count] = self.atom_eps_sqrt[indices]
        self.count = new_count

    def step(self, steps_to_run):
        if self.paused: return
        is_dyn = self.is_static[:self.count] == 0
        if np.any(is_dyn):
            self.atom_sigma[:self.count][is_dyn] = self.sigma
            self.atom_eps_sqrt[:self.count][is_dyn] = math.sqrt(self.epsilon)
        self._update_derived_params()
        total_dt = self.dt * steps_to_run
        self.update_animations(total_dt)
        if self.total_steps % 100 == 0 and self.count > 0:
            spatial_sort(self.pos_x[:self.count], self.pos_y[:self.count], self.vel_x[:self.count], self.vel_y[:self.count], self.force_x[:self.count], self.force_y[:self.count], self.is_static[:self.count], self.kinematic_props[:self.count], self.atom_sigma[:self.count], self.atom_eps_sqrt[:self.count], self.world_size, self.cell_size)
            self.rebuild_next = True
        should_rebuild = False
        if self.pair_count == 0 or self.rebuild_next: should_rebuild = True
        elif self.count > 0: should_rebuild = check_displacement(self.pos_x[:self.count], self.pos_y[:self.count], self.last_x[:self.count], self.last_y[:self.count], self.r_skin_sq_limit)
        if should_rebuild and self.count > 0:
            while True:
                count = build_neighbor_list(self.pos_x[:self.count], self.pos_y[:self.count], self.r_list2, self.cell_size, self.world_size, self.pair_i, self.pair_j)
                if count >= self.max_pairs: self.max_pairs *= 2; self.pair_i = np.zeros(self.max_pairs, dtype=np.int32); self.pair_j = np.zeros(self.max_pairs, dtype=np.int32); continue 
                self.pair_count = count; break 
            self.last_x[:self.count] = self.pos_x[:self.count]; self.last_y[:self.count] = self.pos_y[:self.count]; self.rebuild_next = False
        if self.count > 0:
            steps_done = integrate_n_steps(steps_to_run, self.pos_x[:self.count], self.pos_y[:self.count], self.vel_x[:self.count], self.vel_y[:self.count], self.force_x[:self.count], self.force_y[:self.count], self.last_x[:self.count], self.last_y[:self.count], self.is_static[:self.count], self.kinematic_props[:self.count], self.atom_sigma[:self.count], self.atom_eps_sqrt[:self.count], np.float32(config.ATOM_MASS), self.pair_i, self.pair_j, self.pair_count, np.float32(self.dt), np.float32(self.gravity), np.float32(self.r_cut_base**2), np.float32(self.r_skin_sq_limit), np.float32(self.world_size), self.use_boundaries, np.float32(self.damping))
            self.total_steps += steps_done
            self.steps_accumulator += steps_done
            total_dt = self.dt * steps_done
            self.update_animations(total_dt)
            now = time.time(); elapsed = now - self.last_sps_update
            if elapsed >= 0.5: self.sps = self.steps_accumulator / elapsed; self.steps_accumulator = 0; self.last_sps_update = now
            if steps_done < steps_to_run: self.rebuild_next = True
            if self.use_thermostat: apply_thermostat(self.vel_x[:self.count], self.vel_y[:self.count], np.float32(config.ATOM_MASS), self.is_static[:self.count], np.float32(self.target_temp), np.float32(0.1))
            active_x = self.pos_x[:self.count]; active_y = self.pos_y[:self.count]; w = self.world_size
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
        self.kinematic_props = np.resize(self.kinematic_props, (self.capacity, 3))
        self.atom_sigma = np.resize(self.atom_sigma, self.capacity)
        self.atom_eps_sqrt = np.resize(self.atom_eps_sqrt, self.capacity)
        self.last_x = np.resize(self.last_x, self.capacity)
        self.last_y = np.resize(self.last_y, self.capacity)
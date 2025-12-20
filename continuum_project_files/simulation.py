import math
import copy
import config
from fluid import FluidBatch

class Node:
    def __init__(self, x, y, kind='pipe', fixed_pressure=None, is_primary=True, material_type='Water'):
        self.x = x
        self.y = y
        self.kind = kind 
        self.setting = 1.0 
        self.material_type = material_type 
        
        # 'pressure' is used to visualize crowding (0-100%+)
        self.pressure = 0.0 
        self.fluid = FluidBatch() 
        
        self.volume_capacity = config.PIPE_AREA_M2 * config.SEGMENT_LENGTH_M
        self.current_volume = 0.0 
        
        self.fixed_pressure = fixed_pressure 
        self.connections = [] 
        self.is_primary = is_primary
        
        self.last_velocity = 0.0

class Simulation:
    def __init__(self):
        self.nodes = []
        self.history = [] 
        
        self.source_node = Node(0, 0, kind='source', fixed_pressure=config.DEFAULT_SOURCE_PRESSURE, is_primary=True, material_type='Red')
        self.source_node.current_volume = self.source_node.volume_capacity
        self.source_node.fluid.mass = 1000.0 
        self.source_node.fluid.composition = {'Red': 1.0}
        self.nodes.append(self.source_node)

    def save_state(self):
        if len(self.history) > 50: self.history.pop(0)
        self.history.append(copy.deepcopy(self.nodes))

    def undo(self):
        if not self.history: return
        self.nodes = self.history.pop()
        if self.nodes: 
            sources = [n for n in self.nodes if n.kind == 'source']
            self.source_node = sources[0] if sources else self.nodes[0]

    def create_node(self, x, y, kind='pipe', material_type='Water'):
        fp = None
        if kind == 'source': fp = config.DEFAULT_SOURCE_PRESSURE
        if kind == 'sink': fp = 0.0 
        new_node = Node(x, y, kind=kind, fixed_pressure=fp, is_primary=True, material_type=material_type)
        self.nodes.append(new_node)
        return new_node

    def convert_node(self, node, kind, material_type='Water'):
        node.kind = kind
        node.material_type = material_type
        node.is_primary = True 
        
        if kind == 'source':
            node.fixed_pressure = config.DEFAULT_SOURCE_PRESSURE
            node.current_volume = node.volume_capacity
            node.fluid.composition = {material_type: 1.0}
        elif kind == 'sink':
            node.fixed_pressure = 0.0
            node.current_volume = 0.0
            node.fluid.composition = {}
        else:
            node.fixed_pressure = None

    def cycle_source_material(self, node):
        if node.kind != 'source': return
        modes = ['Red', 'Green', 'Blue', 'Water']
        try:
            current_idx = modes.index(node.material_type)
            next_idx = (current_idx + 1) % len(modes)
            node.material_type = modes[next_idx]
            node.fluid.composition = {node.material_type: 1.0}
        except ValueError:
            node.material_type = 'Red'

    def adjust_source_rate(self, node, delta):
        if node.fixed_pressure is not None:
            node.fixed_pressure += delta
            if node.fixed_pressure < 0: node.fixed_pressure = 0

    def add_pipe(self, start_node, end_x, end_y, connect_to_end_node=None):
        if not start_node.is_primary: start_node.is_primary = True
        dx = end_x - start_node.x
        dy = end_y - start_node.y
        dist = math.hypot(dx, dy)
        if dist < 0.1: return start_node
        num_segments = max(1, int(dist / config.SEGMENT_LENGTH_PX))
        prev_node = start_node
        for i in range(1, num_segments + 1):
            t = i / num_segments
            nx = start_node.x + dx * t
            ny = start_node.y + dy * t
            if i == num_segments and connect_to_end_node:
                new_node = connect_to_end_node
                if not new_node.is_primary: new_node.is_primary = True
            else:
                new_node = Node(nx, ny, kind='pipe', is_primary=(i==num_segments))
                self.nodes.append(new_node)
            if new_node not in prev_node.connections: prev_node.connections.append(new_node)
            if prev_node not in new_node.connections: new_node.connections.append(prev_node)
            prev_node = new_node
        return prev_node

    def _cleanup_chain(self, start_node):
        if start_node.is_primary: return
        if start_node not in self.nodes: return
        neighbors = list(start_node.connections)
        self.nodes.remove(start_node)
        for neighbor in neighbors:
            if start_node in neighbor.connections: neighbor.connections.remove(start_node)
            self._cleanup_chain(neighbor)

    def _gc_node(self, node):
        if node.kind in ['source', 'sink']: return
        if not node.connections:
            if node in self.nodes: self.nodes.remove(node)

    def delete_entity(self, target, target_type):
        if target_type == 'node':
            node_to_delete = target
            if node_to_delete.kind in ['source', 'sink', 'valve'] and node_to_delete.connections:
                node_to_delete.kind = 'pipe'
                node_to_delete.fixed_pressure = None
                node_to_delete.setting = 1.0 
                return
            neighbors_to_check = list(node_to_delete.connections)
            for neighbor in node_to_delete.connections:
                if node_to_delete in neighbor.connections: neighbor.connections.remove(node_to_delete)
                self._cleanup_chain(neighbor)
            if node_to_delete in self.nodes: self.nodes.remove(node_to_delete)
            for n in neighbors_to_check:
                if n in self.nodes: self._gc_node(n)
        elif target_type == 'segment':
            _, _, node_a, node_b = target
            if node_b in node_a.connections: node_a.connections.remove(node_b)
            if node_a in node_b.connections: node_b.connections.remove(node_a)
            self._cleanup_chain(node_a)
            self._cleanup_chain(node_b)
            if node_a in self.nodes: self._gc_node(node_a)
            if node_b in self.nodes: self._gc_node(node_b)

    def get_snap_target(self, x, y, threshold, nodes_only=False):
        closest_node = None
        min_node_dist = float('inf')
        for node in self.nodes:
            if nodes_only and not node.is_primary: continue
            dist = math.hypot(node.x - x, node.y - y)
            if dist < min_node_dist:
                min_node_dist = dist
                closest_node = node
        if min_node_dist > threshold: closest_node = None
        if nodes_only: return (closest_node, 'node') if closest_node else (None, None)
        
        seen_edges = set()
        best_segment = None 
        min_seg_dist = float('inf')
        for node_a in self.nodes:
            for node_b in node_a.connections:
                edge_id = frozenset([node_a, node_b])
                if edge_id in seen_edges: continue
                seen_edges.add(edge_id)
                dx = node_b.x - node_a.x
                dy = node_b.y - node_a.y
                if dx == 0 and dy == 0: continue
                t = max(0, min(1, ((x - node_a.x)*dx + (y - node_a.y)*dy) / (dx*dx+dy*dy)))
                cp_x, cp_y = node_a.x + t * dx, node_a.y + t * dy
                dist = math.hypot(x - cp_x, y - cp_y)
                if dist < min_seg_dist:
                    min_seg_dist = dist
                    best_segment = (cp_x, cp_y, node_a, node_b)
        if min_seg_dist > threshold: best_segment = None
        
        if best_segment:
            cp_x, cp_y, s_node_a, s_node_b = best_segment
            dist_to_a = math.hypot(cp_x - s_node_a.x, cp_y - s_node_a.y)
            dist_to_b = math.hypot(cp_x - s_node_b.x, cp_y - s_node_b.y)
            if dist_to_a < config.MIN_PIPE_LENGTH and s_node_a.is_primary:
                dist_a_cursor = math.hypot(s_node_a.x - x, s_node_a.y - y)
                if dist_a_cursor < min_node_dist: closest_node = s_node_a; min_node_dist = dist_a_cursor
                best_segment = None
            elif dist_to_b < config.MIN_PIPE_LENGTH and s_node_b.is_primary:
                dist_b_cursor = math.hypot(s_node_b.x - x, s_node_b.y - y)
                if dist_b_cursor < min_node_dist: closest_node = s_node_b; min_node_dist = dist_b_cursor
                best_segment = None
        
        if closest_node and best_segment: return (closest_node, 'node') if min_node_dist <= min_seg_dist else (best_segment, 'segment')
        elif closest_node: return closest_node, 'node'
        elif best_segment: return best_segment, 'segment'
        return None, None

    def split_pipe(self, node_a, node_b, split_x, split_y, kind='pipe', material_type='Water'):
        if node_b in node_a.connections: node_a.connections.remove(node_b)
        if node_a in node_b.connections: node_b.connections.remove(node_a)
        fp = None
        if kind == 'sink': fp = 0.0
        new_node = Node(split_x, split_y, kind=kind, fixed_pressure=fp, is_primary=True, material_type=material_type)
        self.nodes.append(new_node)
        node_a.connections.append(new_node)
        new_node.connections.append(node_a)
        new_node.connections.append(node_b)
        node_b.connections.append(new_node)
        return new_node

    def toggle_valve(self, node):
        if node.kind == 'valve':
            node.setting = 0.0 if node.setting > 0.5 else 1.0

    def update(self, dt):
        dt = min(dt, 0.1)
        sub_dt = dt / config.PHYSICS_SUBSTEPS
        
        velocity_sums = {n: 0.0 for n in self.nodes}

        for _ in range(config.PHYSICS_SUBSTEPS):
            self._step_physics(sub_dt)
            for n in self.nodes:
                velocity_sums[n] += n.last_velocity

        for n in self.nodes:
            if config.PHYSICS_SUBSTEPS > 0:
                n.last_velocity = velocity_sums[n] / config.PHYSICS_SUBSTEPS
            
            # Update visual pressure (100% = Capacity)
            # We can now go over 100%, indicating pressure
            n.pressure = (n.current_volume / n.volume_capacity) * 100.0

    def _step_physics(self, dt):
        # 1. EMISSION & SINKS
        for node in self.nodes:
            if node.kind == 'source':
                # Sources act as infinite reservoirs at 100% capacity
                if node.current_volume < node.volume_capacity:
                    node.current_volume = node.volume_capacity
                    node.fluid.composition = {node.material_type: 1.0}
            elif node.kind == 'sink':
                node.current_volume = 0.0
                node.pressure = 0.0

        # 2. CALCULATE POTENTIAL ENERGY & TRANSFERS
        transfers = []
        step_velocities = dict.fromkeys(self.nodes, 0.0)

        # Pre-calculate Energy States using Compressible Model
        node_energies = {}
        for node in self.nodes:
            fill = node.current_volume / node.volume_capacity
            
            # PRESSURE COMPONENT
            if fill <= 1.0:
                # Gentle slope for normal filling/spreading
                p_energy = fill * config.PRESSURE_SENSITIVITY
            else:
                # Steep slope for compression (Weight Support)
                p_energy = config.PRESSURE_SENSITIVITY + (fill - 1.0) * config.COMPRESSION_PENALTY
            
            # GRAVITY COMPONENT (Higher y = Lower Energy)
            g_energy = -node.y * config.GRAVITY_SENSITIVITY
            
            node_energies[node] = p_energy + g_energy

        for node_a in self.nodes:
            if node_a.current_volume <= 0.0001: continue
            
            valid_neighbors = []
            for neighbor in node_a.connections:
                if node_a.kind == 'valve' and node_a.setting < 0.01: continue
                if neighbor.kind == 'valve' and neighbor.setting < 0.01: continue
                valid_neighbors.append(neighbor)

            if not valid_neighbors: continue

            scores = {}
            total_score = 0.0
            energy_a = node_energies[node_a]
            
            for nb in valid_neighbors:
                energy_b = node_energies[nb]
                
                # Flow is driven by Energy Delta
                delta_energy = energy_a - energy_b
                
                # ATOMIC COHESION (Surface Tension)
                # If target is virtually empty (breaking the surface), it costs extra energy.
                if nb.current_volume < 0.05 * nb.volume_capacity:
                    delta_energy -= config.SURFACE_TENSION

                # FRICTION CHECK
                if delta_energy < config.FLOW_FRICTION:
                    score = 0.0
                else:
                    # Exclusion Rule:
                    fill_b = nb.current_volume / nb.volume_capacity
                    
                    if fill_b >= config.MAX_COMPRESSION:
                        score = 0.0
                    else:
                        score = delta_energy

                if score > 0:
                    scores[nb] = score
                    total_score += score

            # --- DISTRIBUTE FLUID ---
            if total_score <= 0.001: continue

            mobility = min(1.0, total_score * dt * config.MAX_FLOW_SPEED / 100.0)
            amount_to_move = node_a.current_volume * mobility

            for nb, score in scores.items():
                if score <= 0: continue
                
                share = amount_to_move * (score / total_score)
                
                # We allow compressing the neighbor up to MAX_COMPRESSION
                space_in_nb = (nb.volume_capacity * config.MAX_COMPRESSION) - nb.current_volume
                actual_flow = min(share, space_in_nb)
                
                if actual_flow > 0:
                    transfers.append((node_a, nb, actual_flow))

        # 3. APPLY TRANSFERS
        for source, dest, amount in transfers:
            # Safety checks
            real_amount = min(amount, source.current_volume)
            space_dest = (dest.volume_capacity * config.MAX_COMPRESSION) - dest.current_volume
            real_amount = min(real_amount, space_dest)

            if real_amount <= 1e-9: continue

            source.current_volume -= real_amount
            dest.current_volume += real_amount
            
            # Mixing Logic
            vol_existing = dest.current_volume - real_amount
            vol_incoming = real_amount
            vol_total = dest.current_volume
            
            if vol_total > 1e-9:
                new_comp = {}
                all_chems = set(dest.fluid.composition.keys()) | set(source.fluid.composition.keys())
                for chem in all_chems:
                    qty_existing = vol_existing * dest.fluid.composition.get(chem, 0.0)
                    qty_incoming = vol_incoming * source.fluid.composition.get(chem, 0.0)
                    new_frac = (qty_existing + qty_incoming) / vol_total
                    if new_frac > 0.001:
                        new_comp[chem] = new_frac
                dest.fluid.composition = new_comp

            v = real_amount / config.PIPE_AREA_M2
            if v > step_velocities[source]: step_velocities[source] = v
            if v > step_velocities[dest]: step_velocities[dest] = v

        for node in self.nodes:
            node.last_velocity = step_velocities[node]
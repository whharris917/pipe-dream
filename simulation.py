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
        
        # PHYSICAL STATE
        self.pressure = 0.0 # Calculated by Solver
        self.fluid = FluidBatch() # Holds Mass and Composition
        
        # Capacity (m^3)
        self.volume_capacity = config.PIPE_AREA_M2 * config.SEGMENT_LENGTH_M
        self.current_volume = 0.0 
        
        # Boundary Conditions
        self.fixed_pressure = fixed_pressure 
        
        self.connections = [] 
        self.is_primary = is_primary
        
        self.last_velocity = 0.0

class Simulation:
    def __init__(self):
        self.nodes = []
        self.history = [] 
        
        # Initial Source
        self.source_node = Node(0, 0, kind='source', fixed_pressure=config.DEFAULT_SOURCE_PRESSURE, is_primary=True, material_type='Red')
        # Prime it so it has mass to give
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
        # Adjust Pressure
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

    def _solve_pressure_network(self):
        """
        Iterative solver to find steady-state pressures based on connectivity.
        P_node = Average(P_neighbors_weighted_by_conductance)
        """
        # 1. Initialize Unknown Pressures
        # If a node is fixed (Source/Sink), it anchors the field.
        # If not, we let it float.
        
        for _ in range(config.PRESSURE_ITERATIONS):
            max_change = 0.0
            
            for node in self.nodes:
                if node.fixed_pressure is not None: continue
                
                # Calculate target pressure based on neighbors
                total_p_conductance = 0.0
                total_conductance = 0.0
                
                for neighbor in node.connections:
                    # Determine Conductance (1/Resistance)
                    # Basic pipe = 1/PIPE_RESISTANCE
                    # Valve = Setting/VALVE_RESISTANCE
                    
                    c = 1.0 / config.PIPE_RESISTANCE
                    
                    # Valve check logic
                    if node.kind == 'valve':
                        c = node.setting / config.VALVE_RESISTANCE
                    elif neighbor.kind == 'valve':
                        c = neighbor.setting / config.VALVE_RESISTANCE
                        
                    if c > 0.0001:
                        total_p_conductance += neighbor.pressure * c
                        total_conductance += c
                
                if total_conductance > 0:
                    new_p = total_p_conductance / total_conductance
                    diff = abs(new_p - node.pressure)
                    if diff > max_change: max_change = diff
                    node.pressure = new_p
                else:
                    # Trapped node, decays to 0 or stays static
                    # Realistically it stays static, but let's bleed it for stability
                    node.pressure *= 0.98 
            
            if max_change < 0.1: break # Converged

    def update(self, dt):
        # Clamp DT to prevent explosion if frame rate drops
        dt = min(dt, 0.1)
        
        sub_dt = dt / config.PHYSICS_SUBSTEPS
        for _ in range(config.PHYSICS_SUBSTEPS):
            self._step_physics(sub_dt)

    def _step_physics(self, dt):
        # 1. Refill Sources / Empty Sinks
        for node in self.nodes:
            if node.kind == 'source':
                node.current_volume = node.volume_capacity
                node.pressure = node.fixed_pressure # Reset anchor
                node.fluid.composition = {node.material_type: 1.0}
            elif node.kind == 'sink':
                node.current_volume = 0.0
                node.pressure = 0.0
                node.fluid.composition = {}

        # 2. Solve Pressure Field (Steady State)
        self._solve_pressure_network()

        # 3. Transport (Mixing)
        flows = [] # (source, dest, volume_m3)
        seen_edges = set()
        
        for node_a in self.nodes:
            for node_b in node_a.connections:
                edge_id = frozenset([node_a, node_b])
                if edge_id in seen_edges: continue
                seen_edges.add(edge_id)
                
                delta_p = node_a.pressure - node_b.pressure
                
                # Resistance
                r = config.PIPE_RESISTANCE
                if node_a.kind == 'valve':
                    # Avoid divide by zero, treat 0.0 as infinite resistance
                    if node_a.setting < 0.01: r = 1e9
                    else: r = config.VALVE_RESISTANCE / node_a.setting
                elif node_b.kind == 'valve':
                    if node_b.setting < 0.01: r = 1e9
                    else: r = config.VALVE_RESISTANCE / node_b.setting
                
                # Flow Rate Q (m^3/s) = DeltaP / R
                q = delta_p / r
                
                # Store velocity for visuals
                v = q / config.PIPE_AREA_M2
                node_a.last_velocity = v
                node_b.last_velocity = v
                
                vol_to_move = abs(q) * dt
                
                if q > 0:
                    # A -> B
                    # Only flow if A has liquid to give
                    # Infinite sources are always full
                    if node_a.current_volume > 0:
                        flows.append((node_a, node_b, vol_to_move))
                elif q < 0:
                    # B -> A
                    if node_b.current_volume > 0:
                        flows.append((node_b, node_a, vol_to_move))

        # 4. Apply Mixing (CSTR)
        for source, dest, vol in flows:
            # Clamp to available volume (cannot give what you don't have)
            real_vol = min(vol, source.current_volume)
            
            if real_vol > 0:
                # Calculate Mass to move based on source density
                # (Simplified: assume density is property of fluid inside)
                # Ideally density depends on composition. 
                # Let's just move "FluidBatch" proportional to volume.
                
                # Fraction of source being moved
                frac = real_vol / max(source.current_volume, 0.00001)
                frac = min(frac, 1.0)
                
                mass_moved = source.fluid.mass * frac
                
                # Extract
                packet = source.fluid.extract(mass_moved)
                source.current_volume -= real_vol
                
                # Add to Dest (Mixes)
                dest.fluid.add(packet.mass, packet.composition)
                dest.current_volume += real_vol
                
                # Sink Logic: If dest is sink, it vanishes instantly (handled in step 1 next frame)
                # Source Logic: If source is source, it regenerates instantly (handled in step 1 next frame)
                
                # Overflow Logic?
                # In CSTR, usually volume is constant and overflow happens. 
                # Here, we allow "filling up". 
                # If dest overfills, pressure solver handles it next frame (P rises, pushing fluid out).
                # But for mass conservation, we clamp volume to capacity visually?
                if dest.current_volume > dest.volume_capacity:
                    dest.current_volume = dest.volume_capacity
                    # Note: We just deleted mass here (Spillover). 
                    # In a closed loop, pressure would rise until flow stops.
                    # In our "open" logic, this acts like a relief valve.
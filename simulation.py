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
        
        self.fluid = FluidBatch()
        self.volume_capacity = 0.2 
        self.fixed_pressure = fixed_pressure 
        self.connections = [] 
        self.is_primary = is_primary

    @property
    def pressure(self):
        if self.fixed_pressure is not None:
            return self.fixed_pressure
        
        fill_ratio = self.fluid.mass / (self.volume_capacity * 1000.0)
        return fill_ratio * 100.0 * 5.0

class Simulation:
    def __init__(self):
        self.nodes = []
        self.history = [] 
        # Initial default source
        self.source_node = Node(0, 0, kind='source', fixed_pressure=config.SOURCE_PRESSURE, is_primary=True, material_type='Red')
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
        if kind == 'source': fp = config.SOURCE_PRESSURE
        if kind == 'sink': fp = 0.0 
        
        new_node = Node(x, y, kind=kind, fixed_pressure=fp, is_primary=True, material_type=material_type)
        self.nodes.append(new_node)
        return new_node

    def convert_node(self, node, kind, material_type='Water'):
        node.kind = kind
        node.material_type = material_type
        node.is_primary = True 
        
        if kind == 'source':
            node.fixed_pressure = config.SOURCE_PRESSURE
        elif kind == 'sink':
            node.fixed_pressure = 0.0
            node.fluid.mass = 0.0
            node.fluid.composition = {}
        else:
            node.fixed_pressure = None

    def add_pipe(self, start_node, end_x, end_y, connect_to_end_node=None):
        if not start_node.is_primary: start_node.is_primary = True
        dx = end_x - start_node.x
        dy = end_y - start_node.y
        dist = math.hypot(dx, dy)
        if dist < 0.1: return start_node
        num_segments = max(1, int(dist / config.SEGMENT_LENGTH))
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
            
            # DEMOTION LOGIC: If deleting a component, revert to pipe
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
        if kind == 'source': fp = config.SOURCE_PRESSURE
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
        # 1. Sources & Sinks Logic
        for node in self.nodes:
            if node.kind == 'source':
                target_mass = (config.SOURCE_PRESSURE / 5.0 / 100.0) * (node.volume_capacity * 1000.0)
                if node.fluid.mass < target_mass:
                    node.fluid.mass = target_mass
                    node.fluid.composition = {node.material_type: 1.0}
            elif node.kind == 'sink':
                node.fluid.mass = 0.0
                node.fluid.composition = {}

        # 2. Flow Calculation
        flows = [] 
        seen_edges = set()
        
        for node_a in self.nodes:
            p_a = node_a.pressure
            for node_b in node_a.connections:
                edge_id = frozenset([node_a, node_b])
                if edge_id in seen_edges: continue
                seen_edges.add(edge_id)
                p_b = node_b.pressure
                delta_p = p_a - p_b
                if abs(delta_p) < 0.01: continue
                valve_factor = 1.0
                if node_a.kind == 'valve': valve_factor *= node_a.setting
                if node_b.kind == 'valve': valve_factor *= node_b.setting
                flow_rate = delta_p * config.FLOW_SPEED * valve_factor * 0.5 
                amount_to_move = flow_rate * dt
                if amount_to_move > 0: flows.append((node_a, node_b, amount_to_move))
                else: flows.append((node_b, node_a, -amount_to_move))

        # 3. Mass Transfer
        for source, dest, amount in flows:
            real_amount = min(amount, source.fluid.mass)
            packet = source.fluid.extract(real_amount)
            dest.fluid.add(packet.mass, packet.composition)
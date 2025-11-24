import math
import copy
import config
from fluid import FluidBatch

class Junction:
    def __init__(self, x, y, kind='pipe', fixed_pressure=None, material_type='Water'):
        self.x = x
        self.y = y
        self.kind = kind 
        self.fixed_pressure = fixed_pressure
        self.material_type = material_type
        
        self.pressure = 0.0
        self.fluid = FluidBatch()
        self.volume_capacity = 0.1 
        self.current_volume = 0.0
        
        self.setting = 1.0 
        
        self.pipes = []

class Pipe:
    def __init__(self, start_node, end_node):
        self.start_node = start_node
        self.end_node = end_node
        
        dx = end_node.x - start_node.x
        dy = end_node.y - start_node.y
        self.length_px = math.hypot(dx, dy)
        
        self.num_cells = max(1, int(self.length_px / config.SEGMENT_LENGTH_PX))
        self.cell_volume = config.PIPE_AREA_M2 * config.SEGMENT_LENGTH_M
        
        self.cells = [FluidBatch() for _ in range(self.num_cells)]
        
        self.flow_rate = 0.0 
        self.flow_accumulator = 0.0 

class Simulation:
    def __init__(self):
        self.junctions = []
        self.pipes = []
        self.history = []
        
        self.source_node = self.create_node(100, 360, kind='source', material_type='Red')
        self.source_node.current_volume = self.source_node.volume_capacity
        self.source_node.fluid.mass = 1000.0
        self.source_node.fluid.composition = {'Red': 1.0}

    def save_state(self):
        if len(self.history) > 50: self.history.pop(0)
        self.history.append((copy.deepcopy(self.junctions), copy.deepcopy(self.pipes)))

    def undo(self):
        if not self.history: return
        j_snap, p_snap = self.history.pop()
        self.junctions = j_snap
        self.pipes = p_snap
        for j in self.junctions:
            if j.kind == 'source':
                self.source_node = j
                break

    def create_node(self, x, y, kind='pipe', material_type='Water'):
        fp = None
        if kind == 'source': fp = config.DEFAULT_SOURCE_PRESSURE
        if kind == 'sink': fp = 0.0
        
        node = Junction(x, y, kind, fp, material_type)
        self.junctions.append(node)
        return node

    def create_pipe(self, node_a, node_b):
        for p in self.pipes:
            if (p.start_node == node_a and p.end_node == node_b) or \
               (p.start_node == node_b and p.end_node == node_a):
                return p
        
        pipe = Pipe(node_a, node_b)
        self.pipes.append(pipe)
        node_a.pipes.append(pipe)
        node_b.pipes.append(pipe)
        return pipe

    def split_pipe(self, pipe, split_point_x, split_point_y, kind='pipe'):
        node_a = pipe.start_node
        node_b = pipe.end_node
        
        self.pipes.remove(pipe)
        if pipe in node_a.pipes: node_a.pipes.remove(pipe)
        if pipe in node_b.pipes: node_b.pipes.remove(pipe)
        
        new_node = self.create_node(split_point_x, split_point_y, kind)
        
        self.create_pipe(node_a, new_node)
        self.create_pipe(new_node, node_b)
        
        return new_node

    def delete_entity(self, target, target_type):
        if target_type == 'node':
            if target.kind in ['source', 'sink', 'valve'] and target.pipes:
                target.kind = 'pipe'
                target.fixed_pressure = None
                target.setting = 1.0
                return
                
            if target == self.source_node: return 
            
            for p in list(target.pipes):
                self.pipes.remove(p)
                other = p.end_node if p.start_node == target else p.start_node
                if p in other.pipes: other.pipes.remove(p)
            
            self.junctions.remove(target)

        elif target_type == 'segment':
            pipe = target
            self.pipes.remove(pipe)
            if pipe in pipe.start_node.pipes: pipe.start_node.pipes.remove(pipe)
            if pipe in pipe.end_node.pipes: pipe.end_node.pipes.remove(pipe)
            
            for n in [pipe.start_node, pipe.end_node]:
                if not n.pipes and n != self.source_node:
                    self.junctions.remove(n)

    def get_snap_target(self, x, y, threshold, nodes_only=False):
        closest_node = None
        min_dist = float('inf')
        for node in self.junctions:
            d = math.hypot(node.x - x, node.y - y)
            if d < min_dist:
                min_dist = d
                closest_node = node
        
        if min_dist < threshold:
            return closest_node, 'node'
        
        if nodes_only: return None, None

        best_pipe = None
        min_pipe_dist = float('inf')
        best_point = (0,0)

        for pipe in self.pipes:
            x1, y1 = pipe.start_node.x, pipe.start_node.y
            x2, y2 = pipe.end_node.x, pipe.end_node.y
            
            dx, dy = x2-x1, y2-y1
            if dx == 0 and dy == 0: continue
            
            t = ((x-x1)*dx + (y-y1)*dy) / (dx*dx + dy*dy)
            t = max(0, min(1, t))
            
            px = x1 + t*dx
            py = y1 + t*dy
            
            d = math.hypot(x-px, y-py)
            if d < min_pipe_dist:
                min_pipe_dist = d
                best_pipe = pipe
                best_point = (px, py)

        if min_pipe_dist < threshold:
            d1 = math.hypot(best_point[0] - best_pipe.start_node.x, best_point[1] - best_pipe.start_node.y)
            d2 = math.hypot(best_point[0] - best_pipe.end_node.x, best_point[1] - best_pipe.end_node.y)
            
            if d1 < config.MIN_PIPE_LENGTH: return best_pipe.start_node, 'node'
            if d2 < config.MIN_PIPE_LENGTH: return best_pipe.end_node, 'node'
            
            return (best_point[0], best_point[1], best_pipe), 'segment'

        return None, None

    def toggle_valve(self, node):
        if node.kind == 'valve':
            node.setting = 0.0 if node.setting > 0.5 else 1.0

    def update(self, dt):
        for j in self.junctions:
            if j.kind == 'source':
                j.pressure = j.fixed_pressure
                j.current_volume = j.volume_capacity
                j.fluid.composition = {j.material_type: 1.0}
                j.fluid.mass = 1000.0 
            elif j.kind == 'sink':
                j.pressure = 0.0
                j.current_volume = 0.0
                j.fluid.mass = 0.0
                j.fluid.composition = {}

        for _ in range(config.PRESSURE_ITERATIONS):
            max_diff = 0.0
            for j in self.junctions:
                if j.fixed_pressure is not None: continue
                
                # Partial Fill Logic
                # If not full, pressure is dominated by hydrostatic head (low)
                if j.current_volume < j.volume_capacity * 0.99:
                    fill_ratio = j.current_volume / j.volume_capacity
                    # Matched 5.0 constant to DEFAULT_SOURCE_PRESSURE
                    j.pressure = fill_ratio * 5.0 
                    continue 
                
                total_p_cond = 0.0
                total_cond = 0.0
                
                for pipe in j.pipes:
                    other = pipe.end_node if pipe.start_node == j else pipe.start_node
                    
                    r = config.PIPE_RESISTANCE
                    if j.kind == 'valve':
                         if j.setting < 0.01: r = float('inf')
                         else: r += config.VALVE_RESISTANCE / j.setting
                    if other.kind == 'valve':
                         if other.setting < 0.01: r = float('inf')
                         else: r += config.VALVE_RESISTANCE / other.setting

                    if r == float('inf'): cond = 0.0
                    else: cond = 1.0 / r
                        
                    total_p_cond += other.pressure * cond
                    total_cond += cond
                
                if total_cond > 0:
                    target = total_p_cond / total_cond
                    diff = abs(target - j.pressure)
                    if diff > max_diff: max_diff = diff
                    j.pressure = target
            
            if max_diff < 0.1: break

        for pipe in self.pipes:
            p_start = pipe.start_node.pressure
            p_end = pipe.end_node.pressure
            
            delta_p = p_start - p_end
            
            r_start = 0.0
            if pipe.start_node.kind == 'valve':
                if pipe.start_node.setting < 0.01: r_start = float('inf')
                else: r_start = config.VALVE_RESISTANCE / pipe.start_node.setting
                
            r_end = 0.0
            if pipe.end_node.kind == 'valve':
                if pipe.end_node.setting < 0.01: r_end = float('inf')
                else: r_end = config.VALVE_RESISTANCE / pipe.end_node.setting
            
            is_flow_forward = (delta_p > 0)
            
            exit_full = False
            if is_flow_forward:
                if pipe.cells[-1].mass > 0.001: exit_full = True
            else:
                if pipe.cells[0].mass > 0.001: exit_full = True
            
            total_r = config.PIPE_RESISTANCE
            
            if is_flow_forward:
                total_r += r_start 
                if exit_full: total_r += r_end 
            else:
                total_r += r_end 
                if exit_full: total_r += r_start 
            
            if total_r == float('inf'):
                pipe.flow_rate = 0.0
            else:
                pipe.flow_rate = delta_p / total_r
            
            pipe.flow_accumulator += pipe.flow_rate * dt

        for pipe in self.pipes:
            cell_vol_m3 = pipe.cell_volume
            shifts = int(pipe.flow_accumulator / cell_vol_m3)
            
            if shifts != 0:
                pipe.flow_accumulator -= shifts * cell_vol_m3
                
                if shifts > 0:
                    for _ in range(min(shifts, pipe.num_cells)):
                        in_packet = FluidBatch()
                        if pipe.start_node.current_volume > 0:
                            mass_needed = cell_vol_m3 * config.DENSITIES['Water'] 
                            extracted = pipe.start_node.fluid.extract(mass_needed)
                            in_packet = extracted
                            pipe.start_node.current_volume -= cell_vol_m3
                        
                        pipe.cells.insert(0, in_packet)
                        out_packet = pipe.cells.pop()
                        
                        pipe.end_node.fluid.add(out_packet.mass, out_packet.composition)
                        pipe.end_node.current_volume += cell_vol_m3
                        
                else:
                    for _ in range(min(abs(shifts), pipe.num_cells)):
                        in_packet = FluidBatch()
                        if pipe.end_node.current_volume > 0:
                            mass_needed = cell_vol_m3 * config.DENSITIES['Water']
                            extracted = pipe.end_node.fluid.extract(mass_needed)
                            in_packet = extracted
                            pipe.end_node.current_volume -= cell_vol_m3
                            
                        pipe.cells.append(in_packet)
                        out_packet = pipe.cells.pop(0)
                        
                        pipe.start_node.fluid.add(out_packet.mass, out_packet.composition)
                        pipe.start_node.current_volume += cell_vol_m3

            if config.DIFFUSION_FACTOR > 0:
                for i in range(1, len(pipe.cells) - 1):
                    c1 = pipe.cells[i]
                    c2 = pipe.cells[i+1]
                    if c1.mass > 0 or c2.mass > 0:
                        pass
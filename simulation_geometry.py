import math
import pygame
import utils
import numpy as np
import copy
from geometry import Line, Circle
from constraints import create_constraint

class GeometryManager:
    """
    Handles geometric operations, spatial queries, and serialization.
    Works with both Simulation and ModelBuilder contexts.
    """
    def __init__(self, context):
        self.context = context # Renamed from self.sim

    def find_wall_at(self, x, y, radius):
        """Returns the index of a wall or circle intersecting the given point (x,y) with radius."""
        hit_wall = -1
        p3 = np.array([x, y])
        
        # Access walls via context property (works for Sim and Builder)
        for i, w in enumerate(self.context.walls):
            if isinstance(w, Line):
                p1 = w.start; p2 = w.end
                d_vec = p2 - p1
                len_sq = np.dot(d_vec, d_vec)
                
                if len_sq == 0:
                    dist = np.linalg.norm(p3 - p1)
                else:
                    t = max(0, min(1, np.dot(p3 - p1, d_vec) / len_sq))
                    closest = p1 + t * d_vec
                    dist = np.linalg.norm(p3 - closest)
                
                if dist < radius:
                    hit_wall = i
                    break
                    
            elif isinstance(w, Circle):
                dist = math.hypot(x - w.center[0], y - w.center[1])
                if abs(dist - w.radius) < radius:
                    hit_wall = i
                    break
        
        return hit_wall

    def get_context_options(self, target_type, index, pt_index=-1):
        opts = []
        if target_type == 'constraint':
            if 0 <= index < len(self.context.constraints):
                c = self.context.constraints[index]
                opts.append("Delete Constraint")
                if getattr(c, 'type', '') == 'ANGLE':
                    opts.insert(0, "Set Angle...")
                    opts.insert(1, "Animate...")
        elif target_type == 'wall':
            if 0 <= index < len(self.context.walls):
                w = self.context.walls[index]
                opts = ["Properties", "Delete"]
                if isinstance(w, Line):
                    opts.extend(["Set Length...", "Set Rotation..."])
        elif target_type == 'point':
            is_anchored = False
            if 0 <= index < len(self.context.walls):
                w = self.context.walls[index]
                if isinstance(w, Line):
                    if 0 <= pt_index < 2:
                        is_anchored = w.anchored[pt_index]
                elif isinstance(w, Circle):
                    is_anchored = w.anchored[0]
            
            if is_anchored: opts = ["Un-Anchor"]
            else: opts = ["Anchor"]
            
        return opts

    def export_geometry_data(self):
        if not self.context.walls: return None
        
        min_x = float('inf'); max_x = float('-inf'); min_y = float('inf'); max_y = float('-inf')
        for w in self.context.walls:
            if isinstance(w, Line):
                p1, p2 = w.start, w.end
                min_x = min(min_x, p1[0], p2[0]); max_x = max(max_x, p1[0], p2[0])
                min_y = min(min_y, p1[1], p2[1]); max_y = max(max_y, p1[1], p2[1])
            elif isinstance(w, Circle):
                min_x = min(min_x, w.center[0] - w.radius); max_x = max(max_x, w.center[0] + w.radius)
                min_y = min(min_y, w.center[1] - w.radius); max_y = max(max_y, w.center[1] + w.radius)
        
        if min_x == float('inf'): return None # Empty world

        center_x = (min_x + max_x) / 2.0; center_y = (min_y + max_y) / 2.0
        
        normalized_walls = []
        for w in self.context.walls:
            d = w.to_dict()
            if d['type'] == 'line':
                d = copy.deepcopy(d)
                d['start'][0] -= center_x; d['start'][1] -= center_y
                d['end'][0] -= center_x; d['end'][1] -= center_y
            elif d['type'] == 'circle':
                d = copy.deepcopy(d)
                d['center'][0] -= center_x; d['center'][1] -= center_y
            
            if d.get('anim') and d['anim']['type'] == 'rotate':
                d['anim']['ref_start'][0] -= center_x; d['anim']['ref_start'][1] -= center_y
                d['anim']['ref_end'][0] -= center_x; d['anim']['ref_end'][1] -= center_y
                
            normalized_walls.append(d)
            
        serialized_constraints = [c.to_dict() for c in self.context.constraints]
        
        return {
            'walls': normalized_walls, 
            'constraints': serialized_constraints,
            'origin_offset': [center_x, center_y]
        }

    def place_geometry(self, geometry_data, x, y, use_original_coordinates=False, current_time=0.0):
        # We need to snapshot via the context because Sim and Builder handle history differently
        if hasattr(self.context, 'snapshot'):
            self.context.snapshot()

        walls_data = geometry_data.get('walls', [])
        constraints_data = geometry_data.get('constraints', [])
        
        offset_x, offset_y = x, y
        if use_original_coordinates:
            orig_offset = geometry_data.get('origin_offset', [0, 0])
            offset_x, offset_y = orig_offset[0], orig_offset[1]
        
        base_index = len(self.context.walls)
        
        for wd in walls_data:
            if wd['type'] == 'line':
                start = np.array(wd['start']) + np.array([offset_x, offset_y])
                end = np.array(wd['end']) + np.array([offset_x, offset_y])
                # Access sketch directly to add entities
                w_idx = self.context.sketch.add_line(start, end, wd.get('ref', False))
                w = self.context.sketch.entities[w_idx]
                
                w.anchored = wd.get('anchored', [False, False])
                w.material_id = wd.get('material_id', "Default")
                
                if wd.get('anim'):
                    anim = copy.deepcopy(wd['anim'])
                    if anim['type'] == 'rotate':
                        anim['ref_start'][0] += offset_x; anim['ref_start'][1] += offset_y
                        anim['ref_end'][0] += offset_x; anim['ref_end'][1] += offset_y
                    w.anim = anim
                    
            elif wd['type'] == 'circle':
                center = np.array(wd['center']) + np.array([offset_x, offset_y])
                w_idx = self.context.sketch.add_circle(center, wd['radius'])
                w = self.context.sketch.entities[w_idx]
                w.anchored = wd.get('anchored', [False])
                w.material_id = wd.get('material_id', "Default")
            
        for cd in constraints_data:
            new_indices = []
            for idx in cd['indices']:
                if isinstance(idx, (list, tuple)): new_indices.append((idx[0] + base_index, idx[1]))
                else: new_indices.append(idx + base_index)
            
            temp_data = cd.copy(); temp_data['indices'] = new_indices
            if 'driver' in temp_data and temp_data['driver']:
                temp_data['driver'] = copy.deepcopy(temp_data['driver'])
            
            # Use Sketch API to add constraint
            c_obj = create_constraint(temp_data)
            if c_obj:
                if hasattr(c_obj, 'driver') and c_obj.driver:
                     if not hasattr(c_obj, 'base_time') or c_obj.base_time is None:
                        c_obj.base_time = current_time
                self.context.sketch.constraints.append(c_obj)

        self.context.sketch.solve(iterations=500)
        
        # If the context is a Simulation, we need to rebuild atoms
        if hasattr(self.context, 'rebuild_static_atoms'):
            self.context.rebuild_static_atoms()

# --- View Layout Logic (Moved from utils.py) ---

def _get_entity_center_screen(entity_idx, entities, transform):
    if entity_idx < 0 or entity_idx >= len(entities): return (0,0)
    e = entities[entity_idx]
    if hasattr(e, 'start'): # Line
        p1 = transform(e.start[0], e.start[1])
        p2 = transform(e.end[0], e.end[1])
        return ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
    elif hasattr(e, 'center'): # Circle
        return transform(e.center[0], e.center[1])
    elif hasattr(e, 'pos'): # Point
            return transform(e.pos[0], e.pos[1])
    return (0,0)

def _get_point_screen(ent_idx, pt_idx, entities, transform):
    if ent_idx < 0 or ent_idx >= len(entities): return (0,0)
    e = entities[ent_idx]
    pt = e.get_point(pt_idx)
    return transform(pt[0], pt[1])

def get_constraint_symbol(c):
    if c.type == 'COINCIDENT': return "C"
    elif c.type == 'COLLINEAR': return "CL"
    elif c.type == 'MIDPOINT': return "M"
    elif c.type == 'LENGTH': return f"{c.value:.1f}"
    elif c.type == 'EQUAL': return "="
    elif c.type == 'ANGLE':
        if hasattr(c, 'value'): return f"{c.value:.0f}°"
        return "//" if c.type == 'PARALLEL' else "T"
    elif c.type == 'PARALLEL': return "//"
    elif c.type == 'PERPENDICULAR': return "T"
    elif c.type == 'HORIZONTAL': return "H"
    elif c.type == 'VERTICAL': return "V"
    return "?"

def get_constraint_raw_pos(c, entities, transform):
    """Calculates the ideal center position for a constraint icon before grouping."""
    ctype = c.type
    indices = c.indices
    
    if ctype == 'COINCIDENT':
        idx1, idx2 = indices[0][1], indices[1][1]
        if idx1 == -1 or idx2 == -1: # Pt-Entity
            ent_idx = indices[0][0] if idx1 == -1 else indices[1][0]
            pt_ref = indices[1] if idx1 == -1 else indices[0]
            c_pos = _get_entity_center_screen(ent_idx, entities, transform)
            p_pos = _get_point_screen(pt_ref[0], pt_ref[1], entities, transform)
            return ((c_pos[0] + p_pos[0]) // 2, (c_pos[1] + p_pos[1]) // 2)
        else:
            p_pos = _get_point_screen(indices[0][0], idx1, entities, transform)
            return (p_pos[0] + 15, p_pos[1] - 15)
            
    elif ctype in ['COLLINEAR', 'MIDPOINT']:
        pt_ref = indices[0]
        line_idx = indices[1]
        p_pos = _get_point_screen(pt_ref[0], pt_ref[1], entities, transform)
        l_pos = _get_entity_center_screen(line_idx, entities, transform)
        return ((p_pos[0] + l_pos[0]) // 2, (p_pos[1] + l_pos[1]) // 2)
        
    elif ctype in ['LENGTH', 'HORIZONTAL', 'VERTICAL']:
        c_pos = _get_entity_center_screen(indices[0], entities, transform)
        if ctype == 'LENGTH': return (c_pos[0], c_pos[1] + 15)
        return (c_pos[0], c_pos[1] - 15)
        
    elif ctype in ['EQUAL', 'ANGLE', 'PARALLEL', 'PERPENDICULAR']:
            c1 = _get_entity_center_screen(indices[0], entities, transform)
            c2 = _get_entity_center_screen(indices[1], entities, transform)
            return ((c1[0]+c2[0])//2, (c1[1]+c2[1])//2)
            
    return (0,0)

def get_constraint_layout(constraints, entities, zoom, pan_x, pan_y, world_size, layout):
    """
    Calculates the screen positions and bounding boxes for all constraints.
    Returns a list of dicts: {'index', 'constraint', 'center', 'rect', 'symbol', 'bg_color'}
    """
    transform = lambda x, y: utils.sim_to_screen(x, y, zoom, pan_x, pan_y, world_size, layout)
    
    # 1. Group by Proximity
    grouped = {}
    threshold = 20
    layout_data = [] # (index, constraint, group_key)
    
    for i, c in enumerate(constraints):
        cx, cy = get_constraint_raw_pos(c, entities, transform)
        found_group = None
        for key in grouped:
            if math.hypot(key[0]-cx, key[1]-cy) < threshold:
                found_group = key; break
        if found_group:
            grouped[found_group].append((i, c)); layout_data.append((i, c, found_group))
        else:
            grouped[(cx, cy)] = [(i, c)]; layout_data.append((i, c, (cx, cy)))

    # 2. Calculate Final Positions & Rects
    results = []
    group_counts = {k: 0 for k in grouped}
    
    for i, c, key in layout_data:
        idx = group_counts[key]; group_counts[key] += 1
        total_in_group = len(grouped[key]); spacing = 30
        
        start_x = -((total_in_group - 1) * spacing) / 2.0
        final_offset_x = start_x + idx * spacing
        
        cx, cy = get_constraint_raw_pos(c, entities, transform)
        final_x, final_y = cx + final_offset_x, cy
        
        symbol = get_constraint_symbol(c)
        
        # Hitbox calculation (Approximate but consistent)
        w = len(symbol) * 9 + 12 
        h = 20
        rect = pygame.Rect(final_x - w//2, final_y - h//2, w, h)
        
        # Colors
        bg_color = (50, 50, 50)
        text_color = (255, 255, 255)
        if c.type == 'COINCIDENT': text_color = (100, 255, 255)
        elif c.type == 'COLLINEAR': text_color = (150, 255, 150)
        elif c.type == 'MIDPOINT': text_color = (150, 150, 255)
        elif c.type == 'LENGTH': text_color = (255, 200, 100)
        elif c.type == 'ANGLE' and hasattr(c, 'value'): text_color = (255, 200, 200)

        results.append({
            'index': i,
            'constraint': c,
            'center': (final_x, final_y),
            'rect': rect,
            'symbol': symbol,
            'text_color': text_color,
            'bg_color': bg_color
        })
        
    return results
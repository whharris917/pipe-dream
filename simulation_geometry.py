import math
import numpy as np
import pygame
import utils
from geometry import Line, Circle, Point

class GeometryManager:
    """
    Handles purely geometric and spatial queries for the simulation.
    REMOVED: Context Menu logic (Controller) and Export logic (Persistence).
    """
    def __init__(self, sketch_or_sim):
        # Robust initialization: Handle receiving Simulation OR Sketch
        if hasattr(sketch_or_sim, 'sketch'):
            self.sketch = sketch_or_sim.sketch
        else:
            self.sketch = sketch_or_sim

    def find_wall_at(self, x, y, radius):
        """Finds the index of a wall intersecting the circle (x, y, radius)."""
        best_dist = float('inf')
        best_idx = -1
        
        for i, w in enumerate(self.sketch.entities):
            dist = float('inf')
            
            if isinstance(w, Line):
                if np.array_equal(w.start, w.end): continue
                p1 = w.start
                p2 = w.end
                p3 = np.array([x, y])
                
                # Point-Line Segment Distance
                d_vec = p2 - p1
                len_sq = np.dot(d_vec, d_vec)
                if len_sq == 0:
                    dist = np.linalg.norm(p3 - p1)
                else:
                    t = max(0, min(1, np.dot(p3 - p1, d_vec) / len_sq))
                    proj = p1 + t * d_vec
                    dist = np.linalg.norm(p3 - proj)
                    
            elif isinstance(w, Circle):
                center_dist = math.hypot(x - w.center[0], y - w.center[1])
                dist = abs(center_dist - w.radius)
                
            elif isinstance(w, Point):
                 dist = math.hypot(x - w.pos[0], y - w.pos[1])

            if dist < radius and dist < best_dist:
                best_dist = dist
                best_idx = i
                
        return best_idx

    def place_geometry(self, data, offset_x, offset_y, current_time=0.0):
        """Instantiates geometry data at a specific location."""
        # Calculate centroid of imported data to center it at cursor
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        
        if not data.get('walls'): return
        
        for w in data['walls']:
            if w['type'] == 'line':
                min_x = min(min_x, w['start'][0], w['end'][0])
                max_x = max(max_x, w['start'][0], w['end'][0])
                min_y = min(min_y, w['start'][1], w['end'][1])
                max_y = max(max_y, w['start'][1], w['end'][1])
            elif w['type'] == 'circle':
                 min_x = min(min_x, w['center'][0] - w['radius'])
                 max_x = max(max_x, w['center'][0] + w['radius'])
                 min_y = min(min_y, w['center'][1] - w['radius'])
                 max_y = max(max_y, w['center'][1] + w['radius'])

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        dx = offset_x - center_x
        dy = offset_y - center_y
        
        base_idx = len(self.sketch.entities)
        
        # 1. Create Entities
        for w in data['walls']:
            if w['type'] == 'line':
                s = (w['start'][0] + dx, w['start'][1] + dy)
                e = (w['end'][0] + dx, w['end'][1] + dy)
                l = Line(s, e, w.get('ref', False), w.get('material_id', "Default"))
                l.anchored = w.get('anchored', [False, False])
                if 'anim' in w: l.anim = w['anim']
                self.sketch.entities.append(l)
            elif w['type'] == 'circle':
                c = (w['center'][0] + dx, w['center'][1] + dy)
                circ = Circle(c, w['radius'], w.get('material_id', "Default"))
                circ.anchored = w.get('anchored', [False])
                if 'anim' in w: circ.anim = w['anim']
                self.sketch.entities.append(circ)

        # 2. Import Constraints (Offset indices)
        from constraints import create_constraint
        for c_data in data.get('constraints', []):
            # Remap indices
            new_indices = []
            if isinstance(c_data['indices'], list):
                if isinstance(c_data['indices'][0], list): # Nested (Entity, Pt)
                    for item in c_data['indices']:
                        if isinstance(item, list):
                            new_indices.append([item[0] + base_idx, item[1]])
                        else:
                            new_indices.append(item + base_idx)
                else: # Simple List
                     for item in c_data['indices']:
                         new_indices.append(item + base_idx)
            
            c_data_copy = c_data.copy()
            c_data_copy['indices'] = new_indices
            
            c = create_constraint(c_data_copy)
            if c:
                if c.base_time is not None: c.base_time = current_time
                self.sketch.constraints.append(c)

# --- View Layout Logic (Shared) ---

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
    transform = lambda x, y: utils.sim_to_screen(x, y, zoom, pan_x, pan_y, world_size, layout)
    
    grouped = {}
    threshold = 20
    layout_data = [] 
    
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
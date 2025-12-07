import json
import os
import numpy as np
from geometry import Line, Circle
from constraints import create_constraint

def save_file(sim, filename, settings=None):
    if not filename: return "Cancelled"
    walls_dicts = [w.to_dict() for w in sim.walls]
    constraints_dicts = [c.to_dict() for c in sim.constraints]
    state = {
        'count': sim.count,
        'pos_x': sim.pos_x[:sim.count].tolist(), 
        'pos_y': sim.pos_y[:sim.count].tolist(),
        'vel_x': sim.vel_x[:sim.count].tolist(), 
        'vel_y': sim.vel_y[:sim.count].tolist(),
        'is_static': sim.is_static[:sim.count].tolist(),
        'atom_sigma': sim.atom_sigma[:sim.count].tolist(), 
        'atom_eps_sqrt': sim.atom_eps_sqrt[:sim.count].tolist(),
        'walls': walls_dicts, 
        'constraints': constraints_dicts,
        'world_size': sim.world_size, 
        'settings': settings if settings else {}
    }
    try:
        with open(filename, 'w') as f: json.dump(state, f)
        return f"Saved to {os.path.basename(filename)}"
    except Exception as e: return f"Error: {e}"

def load_file(sim, filename):
    if not filename: return False, "Cancelled", {}
    try:
        with open(filename, 'r') as f: data = json.load(f)
        
        walls = []
        for w_data in data['walls']:
            if w_data['type'] == 'line': walls.append(Line.from_dict(w_data))
            elif w_data['type'] == 'circle': walls.append(Circle.from_dict(w_data))
            
        constraints = []
        for c_data in data.get('constraints', []):
            c = create_constraint(c_data)
            if c: constraints.append(c)
            
        restored_state = {}
        for k, v in data.items():
            if k in ['walls', 'constraints']: continue 
            if k in ['pos_x', 'pos_y', 'vel_x', 'vel_y', 'is_static', 'atom_sigma', 'atom_eps_sqrt']:
                dtype = np.float32
                if k == 'is_static': dtype = np.int32
                restored_state[k] = np.array(v, dtype=dtype)
            else: restored_state[k] = v
            
        restored_state['walls'] = walls
        restored_state['constraints'] = constraints
        sim.restore_state(restored_state)
        
        return True, f"Loaded {os.path.basename(filename)}", data.get('settings', {})
    except Exception as e: return False, f"Error: {e}", {}

def save_geometry_file(sim, filename):
    if not filename: return "Cancelled"
    geo_data = sim.export_geometry_data() 
    if not geo_data: return "Empty Geometry"
    wrapper = {'type': 'GEOMETRY', 'data': geo_data}
    try:
        with open(filename, 'w') as f: json.dump(wrapper, f)
        return f"Geometry Saved: {os.path.basename(filename)}"
    except Exception as e: return f"Error: {e}"

def load_geometry_file(filename):
    if not filename: return None
    try:
        with open(filename, 'r') as f: data = json.load(f)
        if data.get('type') != 'GEOMETRY': return None
        return data.get('data', {}) 
    except Exception as e: return None
import pickle
import numpy as np
# UPDATED: Import new module names
from simulation import Simulation
from session import Session
import config
import json

# UPDATED: Argument name app_state -> session
def save_file(sim, session, filepath):
    try:
        data = {
            'sim_data': {
                'count': sim.count,
                'pos_x': sim.pos_x[:sim.count],
                'pos_y': sim.pos_y[:sim.count],
                'vel_x': sim.vel_x[:sim.count],
                'vel_y': sim.vel_y[:sim.count],
                'is_static': sim.is_static[:sim.count],
                'kinematic_props': sim.kinematic_props[:sim.count],
                'atom_sigma': sim.atom_sigma[:sim.count],
                'atom_eps_sqrt': sim.atom_eps_sqrt[:sim.count],
                'world_size': sim.world_size
            },
            'sketch_data': sim.sketch.to_dict(),
            # UPDATED: Access session object
            'view_state': {
                'zoom': session.zoom,
                'pan_x': session.pan_x,
                'pan_y': session.pan_y
            }
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        return f"Saved to {filepath}"
    except Exception as e:
        return f"Error saving: {e}"

def load_file(sim, filepath):
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            
        sim.snapshot()
        
        s_data = data['sim_data']
        sim.world_size = s_data['world_size']
        sim.count = s_data['count']
        
        if sim.count > sim.capacity:
            sim.capacity = sim.count * 2
            sim._resize_arrays()
            
        sim.pos_x[:sim.count] = s_data['pos_x']
        sim.pos_y[:sim.count] = s_data['pos_y']
        sim.vel_x[:sim.count] = s_data['vel_x']
        sim.vel_y[:sim.count] = s_data['vel_y']
        sim.is_static[:sim.count] = s_data['is_static']
        
        if 'kinematic_props' in s_data: sim.kinematic_props[:sim.count] = s_data['kinematic_props']
        else: sim.kinematic_props[:sim.count] = 0.0
            
        sim.atom_sigma[:sim.count] = s_data['atom_sigma']
        sim.atom_eps_sqrt[:sim.count] = s_data['atom_eps_sqrt']
        
        if 'sketch_data' in data:
            sim.sketch.restore(data['sketch_data'])
        else:
            import copy
            sim.sketch.entities = copy.deepcopy(data.get('walls', []))
            sim.sketch.constraints = copy.deepcopy(data.get('constraints', []))
            
        sim.rebuild_static_atoms()
        
        return True, f"Loaded {filepath}", data.get('view_state')
    except Exception as e:
        return False, f"Error loading: {e}", None

def save_geometry_file(sim, session, filepath):
    try:
        data = {
            'walls': [w.to_dict() for w in sim.walls if hasattr(w, 'to_dict')],
            'world_size': sim.world_size
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return f"Geometry saved to {filepath}"
    except Exception as e:
        return f"Error saving geo: {e}"

def load_geometry_file(filepath):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data, "Geometry Loaded"
    except Exception as e:
        return None, f"Error: {e}"
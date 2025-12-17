import copy
import config
from sketch import Sketch
from simulation_geometry import GeometryManager
from definitions import CONSTRAINT_DEFS  # Import definitions to look up rules

class ModelBuilder:
    """
    The 'pure CAD' context. 
    It manages the Sketch and Undo/Redo history, but has no physics engine.
    """
    def __init__(self):
        self.sketch = Sketch()
        self.geo = GeometryManager(self)
        self.world_size = config.DEFAULT_WORLD_SIZE
        
        # Undo/Redo Stacks
        self.undo_stack = []
        self.redo_stack = []
        
        # View State (Saved per snapshot)
        self.view_params = {'zoom': 1.0, 'pan_x': 0.0, 'pan_y': 0.0}

    # --- Properties for GeometryManager compatibility ---
    @property
    def walls(self):
        return self.sketch.entities
    
    @property
    def constraints(self):
        return self.sketch.constraints
    
    @constraints.setter
    def constraints(self, value):
        self.sketch.constraints = value

    # --- State Management ---
    
    def snapshot(self):
        state = {
            'sketch_data': self.sketch.to_dict(),
            'world_size': self.world_size
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > 50: self.undo_stack.pop(0)
        self.redo_stack.clear()

    def restore_state(self, state):
        if 'sketch_data' in state:
            self.sketch.restore(state['sketch_data'])
        self.world_size = state.get('world_size', config.DEFAULT_WORLD_SIZE)

    def undo(self):
        if not self.undo_stack: return
        self._push_redo()
        prev_state = self.undo_stack.pop()
        self.restore_state(prev_state)

    def redo(self):
        if not self.redo_stack: return
        self._push_undo_internal()
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)

    def _push_redo(self):
        self._save_current_to_stack(self.redo_stack)

    def _push_undo_internal(self):
        self._save_current_to_stack(self.undo_stack)
        
    def _save_current_to_stack(self, stack):
        stack.append({
            'sketch_data': self.sketch.to_dict(),
            'world_size': self.world_size
        })

    def reset_simulation(self):
        # "Reset" in Model Builder just clears the sketch
        self.snapshot()
        self.sketch.clear()
        self.world_size = config.DEFAULT_WORLD_SIZE

    def resize_world(self, new_size):
        self.snapshot()
        self.world_size = new_size

    # --- Dummy Methods for Physics Compatibility ---

    def clear_particles(self, snapshot=True):
        pass # No particles to clear

    def update_constraint_drivers(self, time):
        # We visualize drivers in CAD mode by updating the sketch state
        self.sketch.update_drivers(time)

    def apply_constraints(self):
        self.sketch.solve()

    # --- Constraint Application Logic (RESTORED) ---

    def attempt_apply_constraint(self, ctype, wall_idxs, pt_idxs):
        """
        Tries to match the selected geometry (walls/points) to a constraint rule.
        If valid, creates and applies the constraint.
        """
        rules = CONSTRAINT_DEFS.get(ctype, [])
        for r in rules:
            # Check strict count match
            if len(wall_idxs) == r['w'] and len(pt_idxs) == r['p']:
                valid = True
                
                # Check type match (e.g., verify selected items are Lines, not Circles)
                if r.get('t'):
                    for w_idx in wall_idxs:
                        # self.walls works here because it maps to sketch.entities
                        if not isinstance(self.walls[w_idx], r['t']): 
                            valid = False
                            break
                
                if valid:
                    # Execute the lambda from definitions.py to create the constraint
                    # Pass 'self' as the context 's' so get_angle can access self.walls
                    c_obj = r['f'](self, wall_idxs, pt_idxs)
                    self.add_constraint_object(c_obj)
                    return True
        return False

    def add_constraint_object(self, c_obj):
        self.snapshot()
        
        # Conflict resolution: remove existing angle/parallel constraints on same lines
        angle_types = ['PARALLEL', 'PERPENDICULAR', 'HORIZONTAL', 'VERTICAL']
        if hasattr(c_obj, 'type') and c_obj.type in angle_types:
            new_indices = set(c_obj.indices) if isinstance(c_obj.indices, (list, tuple)) else {c_obj.indices}
            keep = []
            for c in self.constraints:
                is_angle = getattr(c, 'type', '') in angle_types
                if is_angle:
                    old_indices = set(c.indices) if isinstance(c.indices, (list, tuple)) else {c.indices}
                    if old_indices == new_indices: continue 
                keep.append(c)
            self.constraints = keep # Use setter
            
        self.sketch.constraints.append(c_obj)
        self.sketch.solve(iterations=500)

    # --- Geometry API Wrappers ---

    def remove_wall(self, index):
        self.snapshot()
        self.sketch.remove_entity(index)

    def toggle_anchor(self, wall_idx, pt_idx):
        if 0 <= wall_idx < len(self.walls):
            self.snapshot()
            w = self.walls[wall_idx]
            w.anchored[pt_idx] = not w.anchored[pt_idx]
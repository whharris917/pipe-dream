import copy
import numpy as np
from geometry import Line, Circle
from constraints import create_constraint
from solver import Solver

class Sketch:
    """
    The Sketch is the 'Model' or 'Blueprint'.
    It holds Geometries, Constraints, and Drivers.
    It isolates the Physics Engine from the Design Tools.
    """
    def __init__(self):
        self.entities = []      # Lines, Circles, Points
        self.constraints = []   # Constraint Data Objects
        self.drivers = []       # (Future: Explicit Driver objects if we separate them from constraints)
        
        # History for Undo/Redo (Managed by the App, but Sketch provides the state)
        # We can implement specific sketch-level undo here if desired later.

    # --- Geometry API ---

    def add_line(self, start, end, is_ref=False, anchored=None):
        if anchored is None:
            anchored = [False, False]
        l = Line(start, end, is_ref)
        l.anchored = anchored
        self.entities.append(l)
        return len(self.entities) - 1

    def add_circle(self, center, radius, anchored=None):
        if anchored is None:
            anchored = [False]
        c = Circle(center, radius)
        c.anchored = anchored
        self.entities.append(c)
        return len(self.entities) - 1

    def update_entity(self, index, **kwargs):
        """
        Generic update for entity properties (pos, radius, physics flags).
        """
        if 0 <= index < len(self.entities):
            e = self.entities[index]
            
            # Position updates
            if 'start' in kwargs and hasattr(e, 'start'): e.start[:] = kwargs['start']
            if 'end' in kwargs and hasattr(e, 'end'): e.end[:] = kwargs['end']
            if 'center' in kwargs and hasattr(e, 'center'): e.center[:] = kwargs['center']
            if 'radius' in kwargs and hasattr(e, 'radius'): e.radius = kwargs['radius']
            
            # Property updates
            if 'physical' in kwargs: e.physical = kwargs['physical']
            if 'anchored' in kwargs: e.anchored = kwargs['anchored']
            
            # Trigger Solve
            self.solve()

    def remove_entity(self, index):
        """
        Removes an entity and any dependent constraints.
        """
        if 0 <= index < len(self.entities):
            # 1. Clean up dependent constraints
            self.constraints = [c for c in self.constraints if not self._constraint_involves(c, index)]
            
            # 2. Shift indices in remaining constraints
            for c in self.constraints:
                self._shift_constraint_indices(c, index)

            # 3. Remove entity
            self.entities.pop(index)
            self.solve()

    def get_entity(self, index):
        if 0 <= index < len(self.entities):
            return self.entities[index]
        return None

    # --- Constraint API ---

    def add_constraint(self, type_name, indices, value=None):
        """
        Creates and adds a constraint via the Factory in constraints.py (or locally).
        """
        # Prepare data dict for the factory
        data = {'type': type_name, 'indices': indices}
        if value is not None: data['value'] = value
        
        c = create_constraint(data)
        if c:
            self._handle_constraint_conflicts(c)
            self.constraints.append(c)
            self.solve(iterations=500) # Strong solve on add
            return c
        return None

    def remove_constraint(self, index):
        if 0 <= index < len(self.constraints):
            self.constraints.pop(index)
            self.solve()

    def clear(self):
        self.entities = []
        self.constraints = []

    # --- Driver API ---

    def set_driver(self, constraint_index, driver_data):
        """
        Attaches a motor/driver to a constraint.
        """
        if 0 <= constraint_index < len(self.constraints):
            c = self.constraints[constraint_index]
            c.driver = driver_data
            # Set base values for relative driving
            if getattr(c, 'value', None) is not None:
                c.base_value = c.value

    def update_drivers(self, time):
        """
        Called by the App/Simulation loop to animate the Sketch.
        """
        import math
        for c in self.constraints:
            if hasattr(c, 'driver') and c.driver:
                d = c.driver
                if c.base_value is None: c.base_value = c.value
                
                base = c.base_value
                
                # Check for None explicitly because getattr returns None if the attr exists but is None
                t0 = getattr(c, 'base_time', 0.0)
                if t0 is None: t0 = 0.0
                
                dt_drive = time - t0
                
                if d['type'] == 'sin':
                    offset = d['amp'] * math.sin(2 * math.pi * d['freq'] * dt_drive + math.radians(d['phase']))
                    c.value = base + offset
                elif d['type'] == 'lin':
                    c.value = base + d['rate'] * dt_drive

    # --- Solver Integration ---

    def solve(self, iterations=20):
        """
        The Bridge to the Solver.
        """
        Solver.solve(self.constraints, self.entities, iterations)

    # --- Private Helpers ---

    def _constraint_involves(self, c, entity_idx):
        for idx in c.indices:
            if isinstance(idx, (list, tuple)):
                if idx[0] == entity_idx: return True
            else:
                if idx == entity_idx: return True
        return False

    def _shift_constraint_indices(self, c, removed_idx):
        new_indices = []
        for idx in c.indices:
            if isinstance(idx, (list, tuple)):
                w_idx, pt_idx = idx
                if w_idx > removed_idx: w_idx -= 1
                new_indices.append((w_idx, pt_idx))
            else:
                val = idx
                if val > removed_idx: val -= 1
                new_indices.append(val)
        c.indices = new_indices

    def _handle_constraint_conflicts(self, new_c):
        # Remove conflicting constraints (e.g. setting an Angle twice)
        angle_types = ['PARALLEL', 'PERPENDICULAR', 'HORIZONTAL', 'VERTICAL']
        if new_c.type in angle_types:
            new_indices = set(new_c.indices) if isinstance(new_c.indices, (list, tuple)) else {new_c.indices}
            keep = []
            for c in self.constraints:
                if c.type in angle_types:
                    old_indices = set(c.indices) if isinstance(c.indices, (list, tuple)) else {c.indices}
                    if old_indices == new_indices:
                        continue 
                keep.append(c)
            self.constraints = keep

    # --- Serialization ---

    def to_dict(self):
        return {
            'entities': [e.to_dict() for e in self.entities],
            'constraints': [c.to_dict() for c in self.constraints]
        }

    def restore(self, data):
        # We need to import Line/Circle factories here to avoid top-level circular imports if they use Sketch
        from geometry import Line, Circle, Point
        
        self.entities = []
        for e_data in data.get('entities', []):
            if e_data['type'] == 'line': self.entities.append(Line.from_dict(e_data))
            elif e_data['type'] == 'circle': self.entities.append(Circle.from_dict(e_data))
            elif e_data['type'] == 'point': self.entities.append(Point.from_dict(e_data))
            
        self.constraints = []
        for c_data in data.get('constraints', []):
            c = create_constraint(c_data)
            if c: self.constraints.append(c)
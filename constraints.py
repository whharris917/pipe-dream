import math
import numpy as np
from geometry import Line, Circle

class Constraint:
    def __init__(self, type_name):
        self.type = type_name
        self.temp = False # For temporary drag constraints

    def solve(self, entities):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError

class Coincident(Constraint):
    def __init__(self, entity_idx1, pt_idx1, entity_idx2, pt_idx2):
        super().__init__('COINCIDENT')
        # indices are [(entity_idx, point_idx), (entity_idx, point_idx)]
        # If point_idx is -1, it indicates the constraint applies to the whole entity (e.g. the line itself)
        self.indices = [(entity_idx1, pt_idx1), (entity_idx2, pt_idx2)]

    def solve(self, entities):
        try:
            e1 = entities[self.indices[0][0]]
            e2 = entities[self.indices[1][0]]
        except IndexError: return # Entity deleted

        idx1, idx2 = self.indices[0][1], self.indices[1][1]

        # --- Case 1: Point-Point Coincidence ---
        if idx1 != -1 and idx2 != -1:
            p1 = e1.get_point(idx1)
            p2 = e2.get_point(idx2)
            
            w1 = e1.get_inv_mass(idx1)
            w2 = e2.get_inv_mass(idx2)
            w_sum = w1 + w2
            
            if w_sum == 0: return

            # Weighted Average
            avg_x = (p1[0]*w1 + p2[0]*w2) / w_sum
            avg_y = (p1[1]*w1 + p2[1]*w2) / w_sum
            target = np.array([avg_x, avg_y])
            
            # Snap strictly if one is anchored to avoid drift
            if w1 == 0: target = p1
            elif w2 == 0: target = p2

            if w1 > 0: e1.set_point(idx1, target)
            if w2 > 0: e2.set_point(idx2, target)

        # --- Case 2: Point-Entity Coincidence ---
        else:
            if idx1 == -1:
                target_ent, pt_ent = e1, e2
                pt_idx_local = idx2
            else:
                target_ent, pt_ent = e2, e1
                pt_idx_local = idx1

            # --- Subcase 2A: Point on Circle Perimeter ---
            if isinstance(target_ent, Circle):
                P = pt_ent.get_point(pt_idx_local)
                C = target_ent.center
                R = target_ent.radius
                
                # Vector from Center to Point
                diff = P - C
                dist = np.linalg.norm(diff)
                
                # Handle center overlap (singularity)
                if dist < 1e-6:
                    diff = np.array([1.0, 0.0])
                    dist = 1.0
                
                # We want dist to be R. Error = current - target
                error = dist - R
                dir_vec = diff / dist
                
                w_p = pt_ent.get_inv_mass(pt_idx_local)
                w_c = target_ent.get_inv_mass(0) # Circle center mass
                w_sum = w_p + w_c
                
                if w_sum == 0: return
                
                correction = dir_vec * error
                
                # Move Point P towards circle surface (opposite to error direction relative to P)
                if w_p > 0:
                    pt_ent.set_point(pt_idx_local, P - correction * (w_p / w_sum))
                
                # Move Circle Center C towards P to satisfy radius (same direction as error vector)
                if w_c > 0:
                    target_ent.set_point(0, C + correction * (w_c / w_sum))

            # --- Subcase 2B: Point on Line Segment ---
            elif isinstance(target_ent, Line):
                P = pt_ent.get_point(pt_idx_local)
                A = target_ent.get_point(0)
                B = target_ent.get_point(1)
                
                u = B - A
                len_sq = np.dot(u, u)
                
                if len_sq < 1e-8: return 

                v = P - A
                t = np.dot(v, u) / len_sq
                
                # CLAMP t to [0, 1] for strict coincidence on segment
                t_clamped = max(0.0, min(1.0, t))
                
                S = A + t_clamped * u
                err = S - P
                
                w_p = pt_ent.get_inv_mass(pt_idx_local)
                w_a = target_ent.get_inv_mass(0)
                w_b = target_ent.get_inv_mass(1)
                
                W = w_p + w_a * (1.0 - t_clamped)**2 + w_b * t_clamped**2
                
                if W == 0: return
                lambda_val = 1.0 / W
                
                if w_p > 0:
                    pt_ent.set_point(pt_idx_local, P + w_p * lambda_val * err)
                if w_a > 0:
                    target_ent.set_point(0, A - w_a * (1.0 - t_clamped) * lambda_val * err)
                if w_b > 0:
                    target_ent.set_point(1, B - w_b * t_clamped * lambda_val * err)

    def to_dict(self):
        return {'type': 'COINCIDENT', 'indices': self.indices}

class Collinear(Constraint):
    def __init__(self, pt_wall_idx, pt_idx, line_wall_idx):
        super().__init__('COLLINEAR')
        self.indices = [(pt_wall_idx, pt_idx), line_wall_idx]

    def solve(self, entities):
        try:
            pt_ent = entities[self.indices[0][0]]
            line_ent = entities[self.indices[1]]
        except IndexError: return

        pt_idx = self.indices[0][1]
        
        P = pt_ent.get_point(pt_idx)
        A = line_ent.get_point(0)
        B = line_ent.get_point(1)
        
        u = B - A
        len_sq = np.dot(u, u)
        
        if len_sq < 1e-8: return

        v = P - A
        t = np.dot(v, u) / len_sq
        
        # UNCLAMPED t for infinite line
        S = A + t * u
        err = S - P
        
        w_p = pt_ent.get_inv_mass(pt_idx)
        w_a = line_ent.get_inv_mass(0)
        w_b = line_ent.get_inv_mass(1)
        
        W = w_p + w_a * (1.0 - t)**2 + w_b * t**2
        
        if W == 0: return
        lambda_val = 1.0 / W
        
        if w_p > 0:
            pt_ent.set_point(pt_idx, P + w_p * lambda_val * err)
        
        if w_a > 0:
            line_ent.set_point(0, A - w_a * (1.0 - t) * lambda_val * err)
        
        if w_b > 0:
            line_ent.set_point(1, B - w_b * t * lambda_val * err)

    def to_dict(self):
        return {'type': 'COLLINEAR', 'indices': self.indices}

class Midpoint(Constraint):
    def __init__(self, pt_wall_idx, pt_idx, line_wall_idx):
        super().__init__('MIDPOINT')
        self.indices = [(pt_wall_idx, pt_idx), line_wall_idx]

    def solve(self, entities):
        try:
            pt_ent = entities[self.indices[0][0]]
            line_ent = entities[self.indices[1]]
        except IndexError: return

        pt_idx = self.indices[0][1]
        
        P = pt_ent.get_point(pt_idx)
        A = line_ent.get_point(0)
        B = line_ent.get_point(1)
        
        w_p = pt_ent.get_inv_mass(pt_idx)
        w_a = line_ent.get_inv_mass(0)
        w_b = line_ent.get_inv_mass(1)
        
        denom = w_p + 0.25 * (w_a + w_b)
        if denom == 0: return
        
        M = (A + B) * 0.5
        diff = M - P
        lambda_val = diff / denom
        
        if w_p > 0:
            pt_ent.set_point(pt_idx, P + w_p * lambda_val)
        
        if w_a > 0:
            line_ent.set_point(0, A - 0.5 * w_a * lambda_val)
        if w_b > 0:
            line_ent.set_point(1, B - 0.5 * w_b * lambda_val)

    def to_dict(self):
        return {'type': 'MIDPOINT', 'indices': self.indices}

class Length(Constraint):
    def __init__(self, entity_idx, target_length):
        super().__init__('LENGTH')
        self.indices = [entity_idx]
        self.value = target_length

    def solve(self, entities):
        try: e = entities[self.indices[0]]
        except IndexError: return

        p1 = e.get_point(0)
        p2 = e.get_point(1)
        w1 = e.get_inv_mass(0)
        w2 = e.get_inv_mass(1)
        
        if w1 + w2 == 0: return
        
        curr_vec = p2 - p1
        curr_len = np.linalg.norm(curr_vec)
        if curr_len < 1e-6: return
        
        diff = curr_len - self.value
        correction = (curr_vec / curr_len) * diff
        
        if w1 > 0: e.set_point(0, p1 + correction * (w1 / (w1+w2)))
        if w2 > 0: e.set_point(1, p2 - correction * (w2 / (w1+w2)))

    def to_dict(self):
        return {'type': 'LENGTH', 'indices': self.indices, 'value': self.value}

class EqualLength(Constraint):
    def __init__(self, entity_idx1, entity_idx2):
        super().__init__('EQUAL')
        self.indices = [entity_idx1, entity_idx2]

    def solve(self, entities):
        try:
            e1 = entities[self.indices[0]]
            e2 = entities[self.indices[1]]
        except IndexError: return

        l1 = e1.length()
        l2 = e2.length()
        
        im1 = e1.get_inv_mass(0) + e1.get_inv_mass(1)
        im2 = e2.get_inv_mass(0) + e2.get_inv_mass(1)
        
        if im1 + im2 == 0: return
        
        target = (l1 * im2 + l2 * im1) / (im1 + im2)
        
        self._apply_len(e1, target)
        self._apply_len(e2, target)

    def _apply_len(self, e, target):
        p1 = e.get_point(0); p2 = e.get_point(1)
        w1 = e.get_inv_mass(0); w2 = e.get_inv_mass(1)
        if w1 + w2 == 0: return
        
        vec = p2 - p1
        cur = np.linalg.norm(vec)
        if cur < 1e-6: return
        diff = cur - target
        corr = (vec / cur) * diff
        
        if w1 > 0: e.set_point(0, p1 + corr * (w1 / (w1+w2)))
        if w2 > 0: e.set_point(1, p2 - corr * (w2 / (w1+w2)))

    def to_dict(self):
        return {'type': 'EQUAL', 'indices': self.indices}

class Angle(Constraint):
    def __init__(self, type_name, entity_idx1, entity_idx2=None):
        super().__init__(type_name) # PARALLEL, PERPENDICULAR, HORIZONTAL, VERTICAL
        if entity_idx2 is not None:
            self.indices = [entity_idx1, entity_idx2]
        else:
            self.indices = [entity_idx1]

    def solve(self, entities):
        if self.type in ['HORIZONTAL', 'VERTICAL']:
            try: e = entities[self.indices[0]]
            except IndexError: return
            
            p1 = e.get_point(0); p2 = e.get_point(1)
            w1 = e.get_inv_mass(0); w2 = e.get_inv_mass(1)
            if w1 + w2 == 0: return
            
            if self.type == 'HORIZONTAL':
                avg_y = (p1[1] + p2[1]) / 2.0
                if w1 == 0: avg_y = p1[1]
                elif w2 == 0: avg_y = p2[1]
                
                if w1 > 0: e.set_point(0, [p1[0], avg_y])
                if w2 > 0: e.set_point(1, [p2[0], avg_y])
            else:
                avg_x = (p1[0] + p2[0]) / 2.0
                if w1 == 0: avg_x = p1[0]
                elif w2 == 0: avg_x = p2[0]
                
                if w1 > 0: e.set_point(0, [avg_x, p1[1]])
                if w2 > 0: e.set_point(1, [avg_x, p2[1]])
                
        elif self.type in ['PARALLEL', 'PERPENDICULAR']:
            try:
                e1 = entities[self.indices[0]]
                e2 = entities[self.indices[1]]
            except IndexError: return
            
            self._solve_dual_angle(e1, e2)

    def _solve_dual_angle(self, e1, e2):
        v1 = e1.end - e1.start; v2 = e2.end - e2.start
        if np.linalg.norm(v1) < 1e-6 or np.linalg.norm(v2) < 1e-6: return

        a1 = math.atan2(v1[1], v1[0])
        a2 = math.atan2(v2[1], v2[0])
        
        target_a1, target_a2 = a1, a2
        
        if self.type == 'PARALLEL':
            if abs(a1 - a2) > math.pi/2:
                if a2 < a1: a2 += math.pi 
                else: a2 -= math.pi
            avg = (a1 + a2) / 2.0
            target_a1, target_a2 = avg, avg
        elif self.type == 'PERPENDICULAR':
            diff = a2 - a1
            while diff > math.pi: diff -= 2*math.pi
            while diff < -math.pi: diff += 2*math.pi
            goal = math.pi/2 if diff > 0 else -math.pi/2
            corr = (goal - diff) / 2.0
            target_a1 = a1 - corr
            target_a2 = a2 + corr

        fixed1 = (e1.get_inv_mass(0) == 0 and e1.get_inv_mass(1) == 0)
        fixed2 = (e2.get_inv_mass(0) == 0 and e2.get_inv_mass(1) == 0)
        
        if fixed1 and fixed2: return
        if fixed1: 
            target_a1 = a1
            target_a2 = a1 if self.type == 'PARALLEL' else a1 + (math.pi/2 if a2>a1 else -math.pi/2)
        elif fixed2:
            target_a2 = a2
            target_a1 = a2 if self.type == 'PARALLEL' else a2 - (math.pi/2 if a2>a1 else -math.pi/2)

        stiffness = 0.5
        if not fixed1: self._rotate_entity(e1, target_a1, stiffness)
        if not fixed2: self._rotate_entity(e2, target_a2, stiffness)

    def _rotate_entity(self, e, target, stiffness):
        v = e.end - e.start
        length = np.linalg.norm(v)
        if length < 1e-6: return

        curr_ang = math.atan2(v[1], v[0])
        diff = target - curr_ang
        while diff > math.pi: diff -= 2*math.pi
        while diff < -math.pi: diff += 2*math.pi
        
        final = curr_ang + diff * stiffness
        
        if e.get_inv_mass(0) == 0: pivot = e.start
        elif e.get_inv_mass(1) == 0: pivot = e.end
        else: pivot = (e.start + e.end) * 0.5
        
        c = math.cos(final); s = math.sin(final)
        
        if np.array_equal(pivot, e.start):
            e.set_point(1, e.start + np.array([c*length, s*length]))
        elif np.array_equal(pivot, e.end):
            e.set_point(0, e.end - np.array([c*length, s*length]))
        else:
            half = length / 2.0
            e.set_point(0, pivot - np.array([c*half, s*half]))
            e.set_point(1, pivot + np.array([c*half, s*half]))

    def to_dict(self):
        return {'type': self.type, 'indices': self.indices}

def create_constraint(data):
    t = data['type']
    idx = data['indices']
    if t == 'COINCIDENT':
        return Coincident(idx[0][0], idx[0][1], idx[1][0], idx[1][1])
    elif t == 'COLLINEAR':
        return Collinear(idx[0][0], idx[0][1], idx[1])
    elif t == 'MIDPOINT':
        return Midpoint(idx[0][0], idx[0][1], idx[1])
    elif t == 'LENGTH':
        return Length(idx[0], data['value'])
    elif t == 'EQUAL':
        return EqualLength(idx[0], idx[1])
    elif t in ['HORIZONTAL', 'VERTICAL', 'PARALLEL', 'PERPENDICULAR']:
        if len(idx) == 2: return Angle(t, idx[0], idx[1])
        else: return Angle(t, idx[0])
    return None
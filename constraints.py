import math
import numpy as np
import pygame
from geometry import Line, Circle

class Constraint:
    def __init__(self, type_name):
        self.type = type_name
        self.temp = False # For temporary drag constraints
        self.icon_rect = None # For hit testing
        self.driver = None # For animation/forcing
        self.base_value = None # Original value before driving
        # base_time is dynamic, added when a driver is attached/started

    def solve(self, entities):
        raise NotImplementedError

    def to_dict(self):
        d = {'type': self.type, 'indices': self.indices}
        if hasattr(self, 'value'): d['value'] = self.value
        if self.driver: d['driver'] = self.driver
        if self.base_value is not None: d['base_value'] = self.base_value
        
        # --- UPDATE: Persist base_time ---
        if hasattr(self, 'base_time'): d['base_time'] = self.base_time
        
        return d

    def get_visual_center(self, transform_func, entities):
        """Returns the preferred (x, y) screen coordinates for the icon."""
        return (0, 0)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        """Draws the constraint. Offset is applied to the icon position for stacking."""
        pass

    def hit_test(self, mx, my):
        if self.icon_rect:
            return self.icon_rect.collidepoint(mx, my)
        return False

    def _draw_icon(self, screen, cx, cy, symbol, font, color=(255, 255, 255), bg_color=(50, 50, 50)):
        # Draw a small box with a symbol
        text = font.render(symbol, True, color)
        w, h = text.get_width() + 8, text.get_height() + 4
        self.icon_rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
        
        # Shadow
        s_rect = self.icon_rect.copy()
        s_rect.x += 2; s_rect.y += 2
        pygame.draw.rect(screen, (0,0,0), s_rect, border_radius=4)
        
        # Main Box
        pygame.draw.rect(screen, bg_color, self.icon_rect, border_radius=4)
        pygame.draw.rect(screen, (100, 100, 100), self.icon_rect, 1, border_radius=4)
        
        # Text
        screen.blit(text, (self.icon_rect.x + 4, self.icon_rect.y + 2))

    def _draw_connector(self, screen, p1, p2, color=(100, 100, 100)):
        pygame.draw.line(screen, color, p1, p2, 1)

    def _get_entity_center_screen(self, entity_idx, entities, transform_func):
        if entity_idx < 0 or entity_idx >= len(entities): return (0,0)
        e = entities[entity_idx]
        if isinstance(e, Line):
            p1 = transform_func(e.start[0], e.start[1])
            p2 = transform_func(e.end[0], e.end[1])
            return ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
        elif isinstance(e, Circle):
            return transform_func(e.center[0], e.center[1])
        return (0,0)

    def _get_point_screen(self, ent_idx, pt_idx, entities, transform_func):
        if ent_idx < 0 or ent_idx >= len(entities): return (0,0)
        e = entities[ent_idx]
        pt = e.get_point(pt_idx)
        return transform_func(pt[0], pt[1])

# --- Helper for Rotation ---
def rotate_entity_by_angle(e, angle_delta, stiffness=0.5):
    """Rotates entity e by angle_delta radians. Checks anchors to pick pivot."""
    v = e.end - e.start; length = np.linalg.norm(v)
    if length < 1e-6: return
    
    current_ang = math.atan2(v[1], v[0])
    target = current_ang + angle_delta * stiffness
    
    # Determine Pivot
    if e.get_inv_mass(0) == 0: pivot = e.start
    elif e.get_inv_mass(1) == 0: pivot = e.end
    else: pivot = (e.start + e.end) * 0.5
    
    c = math.cos(target); s = math.sin(target)
    
    if np.array_equal(pivot, e.start):
        e.set_point(1, e.start + np.array([c*length, s*length]))
    elif np.array_equal(pivot, e.end):
        e.set_point(0, e.end - np.array([c*length, s*length]))
    else:
        half = length / 2.0
        e.set_point(0, pivot - np.array([c*half, s*half]))
        e.set_point(1, pivot + np.array([c*half, s*half]))

class Coincident(Constraint):
    def __init__(self, entity_idx1, pt_idx1, entity_idx2, pt_idx2):
        super().__init__('COINCIDENT')
        self.indices = [(entity_idx1, pt_idx1), (entity_idx2, pt_idx2)]

    def solve(self, entities):
        try:
            e1 = entities[self.indices[0][0]]
            e2 = entities[self.indices[1][0]]
        except IndexError: return

        idx1, idx2 = self.indices[0][1], self.indices[1][1]

        # Case 1: Point-Point
        if idx1 != -1 and idx2 != -1:
            p1 = e1.get_point(idx1); p2 = e2.get_point(idx2)
            w1 = e1.get_inv_mass(idx1); w2 = e2.get_inv_mass(idx2)
            w_sum = w1 + w2
            if w_sum == 0: return
            avg_x = (p1[0]*w1 + p2[0]*w2) / w_sum
            avg_y = (p1[1]*w1 + p2[1]*w2) / w_sum
            target = np.array([avg_x, avg_y])
            if w1 == 0: target = p1
            elif w2 == 0: target = p2
            if w1 > 0: e1.set_point(idx1, target)
            if w2 > 0: e2.set_point(idx2, target)

        # Case 2: Point-Entity
        else:
            if idx1 == -1: target_ent, pt_ent = e1, e2; pt_idx_local = idx2
            else: target_ent, pt_ent = e2, e1; pt_idx_local = idx1

            if isinstance(target_ent, Circle):
                P = pt_ent.get_point(pt_idx_local); C = target_ent.center; R = target_ent.radius
                diff = P - C; dist = np.linalg.norm(diff)
                if dist < 1e-6: diff = np.array([1.0, 0.0]); dist = 1.0
                error = dist - R; dir_vec = diff / dist
                w_p = pt_ent.get_inv_mass(pt_idx_local); w_c = target_ent.get_inv_mass(0); w_r = 1.0
                w_sum = w_p + w_c + w_r
                if w_sum == 0: return
                lambda_val = error / w_sum
                if w_p > 0: pt_ent.set_point(pt_idx_local, P - dir_vec * (w_p * lambda_val))
                if w_c > 0: target_ent.set_point(0, C + dir_vec * (w_c * lambda_val))
                if w_r > 0: target_ent.radius += w_r * lambda_val

            elif isinstance(target_ent, Line):
                P = pt_ent.get_point(pt_idx_local); A = target_ent.get_point(0); B = target_ent.get_point(1)
                u = B - A; len_sq = np.dot(u, u)
                if len_sq < 1e-8: return 
                v = P - A; t = np.dot(v, u) / len_sq
                t_clamped = max(0.0, min(1.0, t))
                S = A + t_clamped * u; err = S - P
                w_p = pt_ent.get_inv_mass(pt_idx_local); w_a = target_ent.get_inv_mass(0); w_b = target_ent.get_inv_mass(1)
                W = w_p + w_a * (1.0 - t_clamped)**2 + w_b * t_clamped**2
                if W == 0: return
                lambda_val = 1.0 / W
                if w_p > 0: pt_ent.set_point(pt_idx_local, P + w_p * lambda_val * err)
                if w_a > 0: target_ent.set_point(0, A - w_a * (1.0 - t_clamped) * lambda_val * err)
                if w_b > 0: target_ent.set_point(1, B - w_b * t_clamped * lambda_val * err)

    def get_visual_center(self, transform_func, entities):
        idx1, idx2 = self.indices[0][1], self.indices[1][1]
        if idx1 == -1 or idx2 == -1:
            ent_idx = self.indices[0][0] if idx1 == -1 else self.indices[1][0]
            pt_ref = self.indices[1] if idx1 == -1 else self.indices[0]
            c_pos = self._get_entity_center_screen(ent_idx, entities, transform_func)
            p_pos = self._get_point_screen(pt_ref[0], pt_ref[1], entities, transform_func)
            return ((c_pos[0] + p_pos[0]) // 2, (c_pos[1] + p_pos[1]) // 2)
        else:
            p_pos = self._get_point_screen(self.indices[0][0], idx1, entities, transform_func)
            return (p_pos[0] + 15, p_pos[1] - 15)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        cx, cy = self.get_visual_center(transform_func, entities)
        idx1, idx2 = self.indices[0][1], self.indices[1][1]
        
        if idx1 == -1 or idx2 == -1:
            # Draw connector for Pt-Entity
            ent_idx = self.indices[0][0] if idx1 == -1 else self.indices[1][0]
            pt_ref = self.indices[1] if idx1 == -1 else self.indices[0]
            c_pos = self._get_entity_center_screen(ent_idx, entities, transform_func)
            p_pos = self._get_point_screen(pt_ref[0], pt_ref[1], entities, transform_func)
            self._draw_connector(screen, c_pos, p_pos)
            
        self._draw_icon(screen, cx + offset[0], cy + offset[1], "C", font, color=(100, 255, 255))

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
        A = line_ent.get_point(0); B = line_ent.get_point(1)
        u = B - A; len_sq = np.dot(u, u)
        if len_sq < 1e-8: return
        v = P - A; t = np.dot(v, u) / len_sq
        S = A + t * u; err = S - P
        w_p = pt_ent.get_inv_mass(pt_idx)
        w_a = line_ent.get_inv_mass(0); w_b = line_ent.get_inv_mass(1)
        W = w_p + w_a * (1.0 - t)**2 + w_b * t**2
        if W == 0: return
        lambda_val = 1.0 / W
        if w_p > 0: pt_ent.set_point(pt_idx, P + w_p * lambda_val * err)
        if w_a > 0: line_ent.set_point(0, A - w_a * (1.0 - t) * lambda_val * err)
        if w_b > 0: line_ent.set_point(1, B - w_b * t * lambda_val * err)

    def get_visual_center(self, transform_func, entities):
        pt_ref = self.indices[0]
        line_idx = self.indices[1]
        p_pos = self._get_point_screen(pt_ref[0], pt_ref[1], entities, transform_func)
        l_pos = self._get_entity_center_screen(line_idx, entities, transform_func)
        return ((p_pos[0] + l_pos[0]) // 2, (p_pos[1] + l_pos[1]) // 2)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        cx, cy = self.get_visual_center(transform_func, entities)
        
        # Re-get positions for connector (not affected by offset)
        pt_ref = self.indices[0]
        line_idx = self.indices[1]
        p_pos = self._get_point_screen(pt_ref[0], pt_ref[1], entities, transform_func)
        l_pos = self._get_entity_center_screen(line_idx, entities, transform_func)
        
        self._draw_connector(screen, p_pos, l_pos, (100, 150, 100))
        self._draw_icon(screen, cx + offset[0], cy + offset[1], "CL", font, color=(150, 255, 150))

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
        A = line_ent.get_point(0); B = line_ent.get_point(1)
        w_p = pt_ent.get_inv_mass(pt_idx)
        w_a = line_ent.get_inv_mass(0); w_b = line_ent.get_inv_mass(1)
        denom = w_p + 0.25 * (w_a + w_b)
        if denom == 0: return
        M = (A + B) * 0.5; diff = M - P; lambda_val = diff / denom
        if w_p > 0: pt_ent.set_point(pt_idx, P + w_p * lambda_val)
        if w_a > 0: line_ent.set_point(0, A - 0.5 * w_a * lambda_val)
        if w_b > 0: line_ent.set_point(1, B - 0.5 * w_b * lambda_val)

    def get_visual_center(self, transform_func, entities):
        pt_ref = self.indices[0]
        line_idx = self.indices[1]
        p_pos = self._get_point_screen(pt_ref[0], pt_ref[1], entities, transform_func)
        l_pos = self._get_entity_center_screen(line_idx, entities, transform_func)
        return ((p_pos[0] + l_pos[0]) // 2, (p_pos[1] + l_pos[1]) // 2)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        cx, cy = self.get_visual_center(transform_func, entities)
        
        pt_ref = self.indices[0]
        line_idx = self.indices[1]
        p_pos = self._get_point_screen(pt_ref[0], pt_ref[1], entities, transform_func)
        l_pos = self._get_entity_center_screen(line_idx, entities, transform_func)
        
        self._draw_connector(screen, p_pos, l_pos, (100, 100, 150))
        self._draw_icon(screen, cx + offset[0], cy + offset[1], "M", font, color=(150, 150, 255))

class Length(Constraint):
    def __init__(self, entity_idx, target_length):
        super().__init__('LENGTH')
        self.indices = [entity_idx]
        self.value = target_length

    def solve(self, entities):
        try: e = entities[self.indices[0]]
        except IndexError: return
        p1 = e.get_point(0); p2 = e.get_point(1)
        w1 = e.get_inv_mass(0); w2 = e.get_inv_mass(1)
        if w1 + w2 == 0: return
        curr_vec = p2 - p1; curr_len = np.linalg.norm(curr_vec)
        if curr_len < 1e-6: return
        diff = curr_len - self.value; correction = (curr_vec / curr_len) * diff
        if w1 > 0: e.set_point(0, p1 + correction * (w1 / (w1+w2)))
        if w2 > 0: e.set_point(1, p2 - correction * (w2 / (w1+w2)))

    def get_visual_center(self, transform_func, entities):
        c_pos = self._get_entity_center_screen(self.indices[0], entities, transform_func)
        return (c_pos[0], c_pos[1] + 15)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        cx, cy = self.get_visual_center(transform_func, entities)
        self._draw_icon(screen, cx + offset[0], cy + offset[1], f"{self.value:.1f}", font, color=(255, 200, 100))

class EqualLength(Constraint):
    def __init__(self, entity_idx1, entity_idx2):
        super().__init__('EQUAL')
        self.indices = [entity_idx1, entity_idx2]

    def solve(self, entities):
        try: e1 = entities[self.indices[0]]; e2 = entities[self.indices[1]]
        except IndexError: return
        l1 = e1.length(); l2 = e2.length()
        im1 = e1.get_inv_mass(0) + e1.get_inv_mass(1); im2 = e2.get_inv_mass(0) + e2.get_inv_mass(1)
        if im1 + im2 == 0: return
        target = (l1 * im2 + l2 * im1) / (im1 + im2)
        self._apply_len(e1, target); self._apply_len(e2, target)

    def _apply_len(self, e, target):
        p1 = e.get_point(0); p2 = e.get_point(1)
        w1 = e.get_inv_mass(0); w2 = e.get_inv_mass(1)
        if w1 + w2 == 0: return
        vec = p2 - p1; cur = np.linalg.norm(vec)
        if cur < 1e-6: return
        diff = cur - target; corr = (vec / cur) * diff
        if w1 > 0: e.set_point(0, p1 + corr * (w1 / (w1+w2)))
        if w2 > 0: e.set_point(1, p2 - corr * (w2 / (w1+w2)))

    def get_visual_center(self, transform_func, entities):
        c1 = self._get_entity_center_screen(self.indices[0], entities, transform_func)
        c2 = self._get_entity_center_screen(self.indices[1], entities, transform_func)
        return ((c1[0]+c2[0])//2, (c1[1]+c2[1])//2)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        cx, cy = self.get_visual_center(transform_func, entities)
        
        c1 = self._get_entity_center_screen(self.indices[0], entities, transform_func)
        c2 = self._get_entity_center_screen(self.indices[1], entities, transform_func)
        
        self._draw_connector(screen, c1, c2)
        self._draw_icon(screen, cx + offset[0], cy + offset[1], "=", font)

class Angle(Constraint):
    def __init__(self, type_name, entity_idx1, entity_idx2=None):
        super().__init__(type_name) 
        if entity_idx2 is not None: self.indices = [entity_idx1, entity_idx2]
        else: self.indices = [entity_idx1]

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
            try: e1 = entities[self.indices[0]]; e2 = entities[self.indices[1]]
            except IndexError: return
            self._solve_dual_angle(e1, e2)

    def _solve_dual_angle(self, e1, e2):
        v1 = e1.end - e1.start; v2 = e2.end - e2.start
        if np.linalg.norm(v1) < 1e-6 or np.linalg.norm(v2) < 1e-6: return
        a1 = math.atan2(v1[1], v1[0]); a2 = math.atan2(v2[1], v2[0])
        target_a1, target_a2 = a1, a2
        
        if self.type == 'PARALLEL':
            if abs(a1 - a2) > math.pi/2:
                if a2 < a1: a2 += math.pi 
                else: a2 -= math.pi
            avg = (a1 + a2) / 2.0; target_a1, target_a2 = avg, avg
        elif self.type == 'PERPENDICULAR':
            diff = a2 - a1
            while diff > math.pi: diff -= 2*math.pi
            while diff < -math.pi: diff += 2*math.pi
            goal = math.pi/2 if diff > 0 else -math.pi/2
            corr = (goal - diff) / 2.0; target_a1 = a1 - corr; target_a2 = a2 + corr

        fixed1 = (e1.get_inv_mass(0) == 0 and e1.get_inv_mass(1) == 0)
        fixed2 = (e2.get_inv_mass(0) == 0 and e2.get_inv_mass(1) == 0)
        
        if fixed1 and fixed2: return
        if fixed1: target_a1 = a1; target_a2 = a1 if self.type == 'PARALLEL' else a1 + (math.pi/2 if a2>a1 else -math.pi/2)
        elif fixed2: target_a2 = a2; target_a1 = a2 if self.type == 'PARALLEL' else a2 - (math.pi/2 if a2>a1 else -math.pi/2)

        stiffness = 0.5
        if not fixed1: rotate_entity_by_angle(e1, target_a1 - a1, stiffness)
        if not fixed2: rotate_entity_by_angle(e2, target_a2 - a2, stiffness)

    def get_visual_center(self, transform_func, entities):
        if self.type in ['HORIZONTAL', 'VERTICAL']:
            c_pos = self._get_entity_center_screen(self.indices[0], entities, transform_func)
            return (c_pos[0], c_pos[1] - 15)
        else:
            c1 = self._get_entity_center_screen(self.indices[0], entities, transform_func)
            c2 = self._get_entity_center_screen(self.indices[1], entities, transform_func)
            return ((c1[0]+c2[0])//2, (c1[1]+c2[1])//2)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        cx, cy = self.get_visual_center(transform_func, entities)
        
        if self.type in ['HORIZONTAL', 'VERTICAL']:
            sym = "H" if self.type == 'HORIZONTAL' else "V"
            self._draw_icon(screen, cx + offset[0], cy + offset[1], sym, font)
        else:
            c1 = self._get_entity_center_screen(self.indices[0], entities, transform_func)
            c2 = self._get_entity_center_screen(self.indices[1], entities, transform_func)
            
            self._draw_connector(screen, c1, c2)
            
            sym = "//" if self.type == 'PARALLEL' else "T"
            self._draw_icon(screen, cx + offset[0], cy + offset[1], sym, font)

class FixedAngle(Constraint):
    def __init__(self, w1_idx, w2_idx, angle_deg):
        super().__init__('ANGLE')
        self.indices = [w1_idx, w2_idx]
        self.value = angle_deg

    def solve(self, entities):
        try: 
            e1 = entities[self.indices[0]]
            e2 = entities[self.indices[1]]
        except IndexError: return
        
        if not isinstance(e1, Line) or not isinstance(e2, Line): return

        v1 = e1.end - e1.start
        v2 = e2.end - e2.start
        if np.linalg.norm(v1) < 1e-6 or np.linalg.norm(v2) < 1e-6: return

        # Current signed angle from v1 to v2
        cross = v1[0]*v2[1] - v1[1]*v2[0]
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        curr_rad = math.atan2(cross, dot)
        
        target_rad = math.radians(self.value)
        diff = curr_rad - target_rad
        # Normalize diff to [-pi, pi]
        while diff > math.pi: diff -= 2*math.pi
        while diff < -math.pi: diff += 2*math.pi
        
        fixed1 = (e1.get_inv_mass(0) == 0 and e1.get_inv_mass(1) == 0)
        fixed2 = (e2.get_inv_mass(0) == 0 and e2.get_inv_mass(1) == 0)
        
        if fixed1 and fixed2: return
        
        stiffness = 0.5
        if fixed1:
            rotate_entity_by_angle(e2, -diff, stiffness)
        elif fixed2:
            rotate_entity_by_angle(e1, diff, stiffness)
        else:
            rotate_entity_by_angle(e1, diff * 0.5, stiffness)
            rotate_entity_by_angle(e2, -diff * 0.5, stiffness)

    def get_visual_center(self, transform_func, entities):
        c1 = self._get_entity_center_screen(self.indices[0], entities, transform_func)
        c2 = self._get_entity_center_screen(self.indices[1], entities, transform_func)
        return ((c1[0]+c2[0])//2, (c1[1]+c2[1])//2)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        cx, cy = self.get_visual_center(transform_func, entities)
        c1 = self._get_entity_center_screen(self.indices[0], entities, transform_func)
        c2 = self._get_entity_center_screen(self.indices[1], entities, transform_func)
        self._draw_connector(screen, c1, c2)
        self._draw_icon(screen, cx + offset[0], cy + offset[1], f"{self.value:.0f}°", font, color=(255, 200, 200))

def create_constraint(data):
    t = data['type']
    idx = data['indices']
    
    c = None
    if t == 'COINCIDENT': c = Coincident(idx[0][0], idx[0][1], idx[1][0], idx[1][1])
    elif t == 'COLLINEAR': c = Collinear(idx[0][0], idx[0][1], idx[1])
    elif t == 'MIDPOINT': c = Midpoint(idx[0][0], idx[0][1], idx[1])
    elif t == 'LENGTH': c = Length(idx[0], data['value'])
    elif t == 'EQUAL': c = EqualLength(idx[0], idx[1])
    elif t == 'ANGLE': c = FixedAngle(idx[0], idx[1], data['value'])
    elif t in ['HORIZONTAL', 'VERTICAL', 'PARALLEL', 'PERPENDICULAR']:
        if len(idx) == 2: c = Angle(t, idx[0], idx[1])
        else: c = Angle(t, idx[0])
        
    if c:
        if 'driver' in data: c.driver = data['driver']
        if 'base_value' in data: c.base_value = data['base_value']
        # --- UPDATE: Restore base_time if present ---
        if 'base_time' in data: c.base_time = data['base_time']
    
    return c
import pygame
import numpy as np

# Note: Solve logic has moved to solver.py
# These classes are now primarily Data Containers + Visualization helpers

class Constraint:
    def __init__(self, type_name):
        self.type = type_name
        self.temp = False 
        self.icon_rect = None 
        self.driver = None 
        self.base_value = None 
        self.base_time = None

    def to_dict(self):
        d = {'type': self.type, 'indices': self.indices}
        if hasattr(self, 'value'): d['value'] = self.value
        if self.driver: d['driver'] = self.driver
        if self.base_value is not None: d['base_value'] = self.base_value
        if self.base_time is not None: d['base_time'] = self.base_time
        return d

    # --- Visualization (View) Logic ---
    # Kept here temporarily to avoid breaking renderer.py
    
    def get_visual_center(self, transform_func, entities):
        return (0, 0)

    def render(self, screen, transform_func, entities, font, offset=(0,0)):
        pass

    def hit_test(self, mx, my):
        if self.icon_rect:
            return self.icon_rect.collidepoint(mx, my)
        return False

    def _draw_icon(self, screen, cx, cy, symbol, font, color=(255, 255, 255), bg_color=(50, 50, 50)):
        text = font.render(symbol, True, color)
        w, h = text.get_width() + 8, text.get_height() + 4
        self.icon_rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
        
        s_rect = self.icon_rect.copy(); s_rect.x += 2; s_rect.y += 2
        pygame.draw.rect(screen, (0,0,0), s_rect, border_radius=4)
        pygame.draw.rect(screen, bg_color, self.icon_rect, border_radius=4)
        pygame.draw.rect(screen, (100, 100, 100), self.icon_rect, 1, border_radius=4)
        screen.blit(text, (self.icon_rect.x + 4, self.icon_rect.y + 2))

    def _draw_connector(self, screen, p1, p2, color=(100, 100, 100)):
        pygame.draw.line(screen, color, p1, p2, 1)

    def _get_entity_center_screen(self, entity_idx, entities, transform_func):
        if entity_idx < 0 or entity_idx >= len(entities): return (0,0)
        e = entities[entity_idx]
        # Duck typing check for Line vs Circle since we can't easily import them here without circular deps
        if hasattr(e, 'start') and hasattr(e, 'end'): # Line
            p1 = transform_func(e.start[0], e.start[1])
            p2 = transform_func(e.end[0], e.end[1])
            return ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
        elif hasattr(e, 'center'): # Circle
            return transform_func(e.center[0], e.center[1])
        return (0,0)

    def _get_point_screen(self, ent_idx, pt_idx, entities, transform_func):
        if ent_idx < 0 or ent_idx >= len(entities): return (0,0)
        e = entities[ent_idx]
        pt = e.get_point(pt_idx)
        return transform_func(pt[0], pt[1])

class Coincident(Constraint):
    def __init__(self, entity_idx1, pt_idx1, entity_idx2, pt_idx2):
        super().__init__('COINCIDENT')
        self.indices = [(entity_idx1, pt_idx1), (entity_idx2, pt_idx2)]

    def get_visual_center(self, transform_func, entities):
        idx1, idx2 = self.indices[0][1], self.indices[1][1]
        if idx1 == -1 or idx2 == -1: # Pt-Entity
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
        self._draw_connector(screen, p_pos, l_pos, (100, 150, 100))
        self._draw_icon(screen, cx + offset[0], cy + offset[1], "CL", font, color=(150, 255, 150))

class Midpoint(Constraint):
    def __init__(self, pt_wall_idx, pt_idx, line_wall_idx):
        super().__init__('MIDPOINT')
        self.indices = [(pt_wall_idx, pt_idx), line_wall_idx]

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
        if 'base_time' in data: c.base_time = data['base_time']
    
    return c
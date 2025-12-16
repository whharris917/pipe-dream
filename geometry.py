import numpy as np
import math
import pygame

class Entity:
    def __init__(self):
        self.sigma = 1.0
        self.epsilon = 1.0
        self.spacing = 0.7
        self.anim = None 
        # NEW: Physical flag for Atomizer
        self.physical = False

    def render(self, screen, transform_func, is_selected=False, is_pending=False):
        raise NotImplementedError

    def get_point(self, index):
        raise NotImplementedError

    def set_point(self, index, pos):
        raise NotImplementedError

    def get_inv_mass(self, index):
        raise NotImplementedError
        
    def move(self, dx, dy, indices=None):
        raise NotImplementedError
    
    def to_dict(self):
        raise NotImplementedError

class Point(Entity):
    def __init__(self, x, y, anchored=False):
        super().__init__()
        self.pos = np.array([x, y], dtype=np.float64)
        self.anchored = anchored

    def render(self, screen, transform_func, is_selected=False, is_pending=False):
        sx, sy = transform_func(self.pos[0], self.pos[1])
        color = (255, 255, 255)
        if is_selected: color = (0, 255, 255)
        elif is_pending: color = (100, 255, 100)
        
        if self.anchored:
            pygame.draw.circle(screen, (255, 50, 50), (int(sx), int(sy)), 6)
        
        pygame.draw.circle(screen, color, (int(sx), int(sy)), 4)

    def get_point(self, index):
        return self.pos

    def set_point(self, index, pos):
        self.pos[0] = pos[0]; self.pos[1] = pos[1]

    def get_inv_mass(self, index):
        return 0.0 if self.anchored else 1.0

    def move(self, dx, dy, indices=None):
        if not self.anchored:
            self.pos[0] += dx; self.pos[1] += dy

    def to_dict(self):
        return {'type': 'point', 'x': float(self.pos[0]), 'y': float(self.pos[1]), 'anchored': self.anchored, 'physical': self.physical}

    @staticmethod
    def from_dict(data):
        p = Point(data['x'], data['y'], data.get('anchored', False))
        p.physical = data.get('physical', False)
        return p

class Line(Entity):
    def __init__(self, start, end, is_ref=False):
        super().__init__()
        self.start = np.array(start, dtype=np.float64)
        self.end = np.array(end, dtype=np.float64)
        self.ref = is_ref
        self.anchored = [False, False]

    def length(self):
        return np.linalg.norm(self.end - self.start)

    def get_point(self, index):
        return self.start if index == 0 else self.end

    def set_point(self, index, pos):
        if index == 0: self.start[:] = pos
        else: self.end[:] = pos

    def get_inv_mass(self, index):
        return 0.0 if self.anchored[index] else 1.0

    def move(self, dx, dy, indices=None):
        if indices is None: indices = [0, 1]
        if 0 in indices and not self.anchored[0]:
            self.start[0] += dx; self.start[1] += dy
        if 1 in indices and not self.anchored[1]:
            self.end[0] += dx; self.end[1] += dy

    def render(self, screen, transform_func, is_selected=False, is_pending=False):
        s1 = transform_func(self.start[0], self.start[1])
        s2 = transform_func(self.end[0], self.end[1])
        
        color = (255, 255, 255)
        if is_selected: color = (255, 200, 50)
        elif is_pending: color = (100, 255, 100)
        
        # Ghost visual (Dotted/Alpha) if not physical? 
        # For now, keep visual simple to avoid renderer breaks.
        if not self.physical: 
            # Could dim the color slightly to indicate "Ghost"
            if not is_selected and not is_pending:
                color = (180, 180, 180)
        
        width = 3 if (is_selected or is_pending) else 1
        
        if self.ref: 
            self._draw_dashed(screen, color, s1, s2, width)
        else: 
            pygame.draw.line(screen, color, s1, s2, width)

        if self.anchored[0]: pygame.draw.circle(screen, (255, 50, 50), s1, 3)
        if self.anchored[1]: pygame.draw.circle(screen, (255, 50, 50), s2, 3)

    def _draw_dashed(self, surf, color, start_pos, end_pos, width=1, dash_length=10):
        x1, y1 = start_pos; x2, y2 = end_pos
        length = math.hypot(x2 - x1, y2 - y1)
        if length == 0: return
        dash_amount = int(length / dash_length)
        if dash_amount == 0: return
        dx = (x2 - x1) / length; dy = (y2 - y1) / length
        for i in range(0, dash_amount, 2):
            s = (x1 + dx * i * dash_length, y1 + dy * i * dash_length)
            e = (x1 + dx * (i + 1) * dash_length, y1 + dy * (i + 1) * dash_length)
            pygame.draw.line(surf, color, s, e, width)

    def to_dict(self):
        return {
            'type': 'line', 'start': self.start.tolist(), 'end': self.end.tolist(),
            'ref': self.ref, 'anchored': self.anchored,
            'sigma': self.sigma, 'epsilon': self.epsilon, 'spacing': self.spacing, 'anim': self.anim,
            'physical': self.physical
        }

    @staticmethod
    def from_dict(data):
        l = Line(data['start'], data['end'], data.get('ref', False))
        l.anchored = data.get('anchored', [False, False])
        l.sigma = data.get('sigma', 1.0); l.epsilon = data.get('epsilon', 1.0)
        l.spacing = data.get('spacing', 0.7); l.anim = data.get('anim', None)
        l.physical = data.get('physical', False)
        return l

class Circle(Entity):
    def __init__(self, center, radius):
        super().__init__()
        self.center = np.array(center, dtype=np.float64)
        self.radius = float(radius)
        self.anchored = [False] 

    def get_point(self, index):
        return self.center

    def set_point(self, index, pos):
        if index == 0: self.center[:] = pos

    def get_inv_mass(self, index):
        return 0.0 if self.anchored[0] else 1.0

    def move(self, dx, dy, indices=None):
        if not self.anchored[0]:
            self.center[0] += dx; self.center[1] += dy

    def render(self, screen, transform_func, is_selected=False, is_pending=False):
        sx, sy = transform_func(self.center[0], self.center[1])
        p0 = transform_func(0, 0)
        pr = transform_func(self.radius, 0)
        s_radius = abs(pr[0] - p0[0])
        
        color = (255, 255, 255)
        if is_selected: color = (255, 200, 50)
        elif is_pending: color = (100, 255, 100)
        
        if not self.physical:
            if not is_selected and not is_pending:
                color = (180, 180, 180)
                
        width = 3 if (is_selected or is_pending) else 1
        
        if self.anchored[0]: pygame.draw.circle(screen, (255, 50, 50), (int(sx), int(sy)), 4)
        pygame.draw.circle(screen, color, (int(sx), int(sy)), int(s_radius), width)

    def to_dict(self):
        return {
            'type': 'circle', 'center': self.center.tolist(), 'radius': self.radius,
            'anchored': self.anchored,
            'sigma': self.sigma, 'epsilon': self.epsilon, 'spacing': self.spacing, 'anim': self.anim,
            'physical': self.physical
        }

    @staticmethod
    def from_dict(data):
        c = Circle(data['center'], data['radius'])
        c.anchored = data.get('anchored', [False])
        c.sigma = data.get('sigma', 1.0); c.epsilon = data.get('epsilon', 1.0)
        c.spacing = data.get('spacing', 0.7); c.anim = data.get('anim', None)
        c.physical = data.get('physical', False)
        return c
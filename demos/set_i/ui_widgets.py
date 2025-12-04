import pygame

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False
        self.handle_w = 12
        self.cached_surf = None
        self.last_drawn_val = None
        
    def handle_event(self, event):
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val(event.pos[0])
                changed = True
        return changed
                
    def update_val(self, mouse_x):
        rel_x = mouse_x - self.rect.x
        rel_x = max(0, min(rel_x, self.rect.width))
        pct = rel_x / self.rect.width
        self.val = self.min_val + pct * (self.max_val - self.min_val)
        
    def draw(self, screen, font):
        pygame.draw.rect(screen, (60, 60, 70), self.rect, border_radius=4)
        if self.max_val == self.min_val: pct = 0.0
        else: pct = (float(self.val) - float(self.min_val)) / (float(self.max_val) - float(self.min_val))
        
        handle_x = self.rect.x + pct * self.rect.width - self.handle_w / 2
        handle_rect = pygame.Rect(int(handle_x), int(self.rect.y - 4), int(self.handle_w), int(self.rect.height + 8))
        pygame.draw.rect(screen, (180, 180, 200), handle_rect, border_radius=2)
        
        if self.label == "Steps/Frame (M)": val_str = f"{int(self.val)}"
        else: val_str = f"{self.val:.2f}"
            
        if self.cached_surf is None or val_str != self.last_drawn_val:
            self.last_drawn_val = val_str
            self.cached_surf = font.render(f"{self.label}: {val_str}", True, (200, 200, 200))
            
        screen.blit(self.cached_surf, (self.rect.x, self.rect.y - 20))

class Button:
    def __init__(self, x, y, w, h, text, active=False, toggle=True, color_active=(90, 200, 90), color_inactive=(80, 80, 80)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = active
        self.toggle = toggle
        self.clicked = False
        self.c_active = color_active
        self.c_inactive = color_inactive
        self.cached_surf = None
        
    def handle_event(self, event):
        action = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.clicked and self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.active = not self.active
                action = True
            self.clicked = False
        return action

    def draw(self, screen, font):
        color = self.c_active if self.active else self.c_inactive
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1, border_radius=5)
        
        if self.cached_surf is None:
            self.cached_surf = font.render(self.text, True, (255, 255, 255))
            
        txt_rect = self.cached_surf.get_rect(center=self.rect.center)
        screen.blit(self.cached_surf, txt_rect)
import pygame

class InputField:
    def __init__(self, x, y, w, h, initial_text="", text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = str(initial_text)
        self.active = False
        self.color_active = (50, 50, 70)
        self.color_inactive = (30, 30, 35)
        self.text_color = text_color
        self.cached_surf = None
        self.last_text = None
        
    def handle_event(self, event):
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                changed = True
            else:
                if self.active:
                    self.active = False
                    changed = True
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Allow numbers, point, and minus
                if event.unicode.isdigit() or event.unicode in ('.', '-'):
                    self.text += event.unicode
            changed = True
            
        return changed

    def get_value(self, default=0.0):
        try:
            return float(self.text)
        except ValueError:
            return default

    def set_value(self, val):
        # Only update text if not currently being edited to prevent fighting
        if not self.active:
            # Format nicely: remove trailing zeros if int
            val = float(val)
            if val.is_integer():
                self.text = str(int(val))
            else:
                self.text = f"{val:.2f}"

    def draw(self, screen, font):
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (100, 100, 120), self.rect, 1)
        
        if self.cached_surf is None or self.text != self.last_text:
            self.last_text = self.text
            self.cached_surf = font.render(self.text, True, self.text_color)
            
        # Center vertically
        text_y = self.rect.y + (self.rect.height - self.cached_surf.get_height()) // 2
        screen.blit(self.cached_surf, (self.rect.x + 5, text_y))

class SmartSlider:
    def __init__(self, x, y, w, min_val, max_val, initial_val, label, hard_min=None, hard_max=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = 50 # Height of the entire widget block
        
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.hard_min = hard_min
        self.hard_max = hard_max
        self.label = label
        
        # Layout:
        # Line 1: Label ........ ValueInput
        # Line 2: MinInput --[Slider]-- MaxInput
        
        self.input_w = 50
        self.input_h = 20
        
        # Inputs
        self.input_val = InputField(x + w - self.input_w, y, self.input_w, self.input_h, str(initial_val))
        self.input_min = InputField(x, y + 25, self.input_w, self.input_h, str(min_val), text_color=(150, 150, 150))
        self.input_max = InputField(x + w - self.input_w, y + 25, self.input_w, self.input_h, str(max_val), text_color=(150, 150, 150))
        
        # Slider Bar Rect
        slider_start_x = x + self.input_w + 5
        slider_width = w - (2 * self.input_w) - 10
        self.slider_rect = pygame.Rect(slider_start_x, y + 25, slider_width, self.input_h)
        self.dragging = False
        self.handle_w = 10

    def handle_event(self, event):
        changed = False
        
        # 1. Handle Inputs
        if self.input_val.handle_event(event):
            new_val = self.input_val.get_value(self.val)
            self.val = self.clamp(new_val, self.min_val, self.max_val)
            changed = True
            
        if self.input_min.handle_event(event):
            new_min = self.input_min.get_value(self.min_val)
            if self.hard_min is not None: new_min = max(new_min, self.hard_min)
            if new_min < self.max_val:
                self.min_val = new_min
                self.val = max(self.val, self.min_val) # Clamp val to new bounds
            changed = True
            
        if self.input_max.handle_event(event):
            new_max = self.input_max.get_value(self.max_val)
            if self.hard_max is not None: new_max = min(new_max, self.hard_max)
            if new_max > self.min_val:
                self.max_val = new_max
                self.val = min(self.val, self.max_val) # Clamp val to new bounds
            changed = True

        # 2. Handle Slider Drag
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.slider_rect.collidepoint(event.pos):
                self.dragging = True
                self.update_from_mouse(event.pos[0])
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_from_mouse(event.pos[0])
                changed = True
        
        # Sync inputs if slider moved
        if changed and not self.input_val.active:
            self.input_val.set_value(self.val)
            
        return changed

    def update_from_mouse(self, mx):
        rel_x = mx - self.slider_rect.x
        rel_x = max(0, min(rel_x, self.slider_rect.width))
        pct = rel_x / self.slider_rect.width
        self.val = self.min_val + pct * (self.max_val - self.min_val)

    def clamp(self, val, min_v, max_v):
        return max(min_v, min(val, max_v))

    def reset(self, val, min_v, max_v):
        self.val = val
        self.min_val = min_v
        self.max_val = max_v
        self.input_val.set_value(val)
        self.input_min.set_value(min_v)
        self.input_max.set_value(max_v)

    def draw(self, screen, font):
        # Draw Label
        lbl = font.render(self.label, True, (200, 200, 200))
        screen.blit(lbl, (self.x, self.y + 2))
        
        # Draw Inputs
        self.input_val.draw(screen, font)
        self.input_min.draw(screen, font)
        self.input_max.draw(screen, font)
        
        # Draw Track
        pygame.draw.rect(screen, (60, 60, 70), self.slider_rect, border_radius=4)
        
        # Draw Handle
        if self.max_val == self.min_val: pct = 0.0
        else: pct = (self.val - self.min_val) / (self.max_val - self.min_val)
        pct = max(0.0, min(1.0, pct))
        
        handle_x = self.slider_rect.x + pct * self.slider_rect.width - self.handle_w / 2
        handle_rect = pygame.Rect(int(handle_x), self.slider_rect.y - 2, self.handle_w, self.slider_rect.height + 4)
        pygame.draw.rect(screen, (150, 180, 220), handle_rect, border_radius=2)

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
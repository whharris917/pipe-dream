import pygame

# Modern Theme Colors (Internal to widgets for self-containment)
THEME_BG = (37, 37, 38)
THEME_INPUT_BG = (60, 60, 60)
THEME_INPUT_ACTIVE = (70, 70, 70)
THEME_ACCENT = (0, 122, 204) # VS Blue
THEME_TEXT = (220, 220, 220)
THEME_TEXT_DIM = (150, 150, 150)
THEME_BORDER = (80, 80, 80)
THEME_HOVER = (60, 60, 65) # Lighter gray for hover

class InputField:
    def __init__(self, x, y, w, h, initial_text="", text_color=THEME_TEXT):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = str(initial_text)
        self.active = False
        self.text_color = text_color
        self.cached_surf = None
        self.last_text = None
        
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

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
        if not self.active:
            val = float(val)
            if val.is_integer(): self.text = str(int(val))
            else: self.text = f"{val:.2f}"

    def draw(self, screen, font):
        # Flat modern look
        bg = THEME_INPUT_ACTIVE if self.active else THEME_INPUT_BG
        border = THEME_ACCENT if self.active else THEME_BORDER
        
        pygame.draw.rect(screen, bg, self.rect, border_radius=3)
        pygame.draw.rect(screen, border, self.rect, 1, border_radius=3)
        
        if self.cached_surf is None or self.text != self.last_text:
            self.last_text = self.text
            # Anti-aliasing = True
            self.cached_surf = font.render(self.text, True, self.text_color)
            
        text_y = self.rect.y + (self.rect.height - self.cached_surf.get_height()) // 2
        # Clip text if too long
        screen.set_clip(self.rect)
        screen.blit(self.cached_surf, (self.rect.x + 5, text_y))
        screen.set_clip(None)

class SmartSlider:
    def __init__(self, x, y, w, min_val, max_val, initial_val, label, hard_min=None, hard_max=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = 50
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.hard_min = hard_min
        self.hard_max = hard_max
        self.label = label
        
        self.input_w = 50
        self.input_h = 24 # Slightly taller inputs
        
        self.input_val = InputField(x + w - self.input_w, y, self.input_w, self.input_h, str(initial_val))
        self.input_min = InputField(x, y + 25, self.input_w, self.input_h, str(min_val), text_color=THEME_TEXT_DIM)
        self.input_max = InputField(x + w - self.input_w, y + 25, self.input_w, self.input_h, str(max_val), text_color=THEME_TEXT_DIM)
        
        slider_start_x = x + self.input_w + 10
        slider_width = w - (2 * self.input_w) - 20
        self.slider_rect = pygame.Rect(slider_start_x, y + 25, slider_width, self.input_h)
        self.dragging = False
        self.handle_radius = 6

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.input_val.move(dx, dy)
        self.input_min.move(dx, dy)
        self.input_max.move(dx, dy)
        self.slider_rect.x += dx
        self.slider_rect.y += dy

    def handle_event(self, event):
        changed = False
        if self.input_val.handle_event(event):
            new_val = self.input_val.get_value(self.val)
            self.val = self.clamp(new_val, self.min_val, self.max_val)
            changed = True
        if self.input_min.handle_event(event):
            new_min = self.input_min.get_value(self.min_val)
            if self.hard_min is not None: new_min = max(new_min, self.hard_min)
            if new_min < self.max_val:
                self.min_val = new_min
                self.val = max(self.val, self.min_val)
            changed = True
        if self.input_max.handle_event(event):
            new_max = self.input_max.get_value(self.max_val)
            if self.hard_max is not None: new_max = min(new_max, self.hard_max)
            if new_max > self.min_val:
                self.max_val = new_max
                self.val = min(self.val, self.max_val)
            changed = True

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check collision with a relaxed hitbox around the slider track
            hitbox = self.slider_rect.inflate(0, 10)
            if hitbox.collidepoint(event.pos):
                self.dragging = True
                self.update_from_mouse(event.pos[0])
                changed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_from_mouse(event.pos[0])
                changed = True
        
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
        # Label
        lbl = font.render(self.label, True, THEME_TEXT) # True = antialias
        screen.blit(lbl, (self.x, self.y + 2))
        
        # Inputs
        self.input_val.draw(screen, font)
        self.input_min.draw(screen, font)
        self.input_max.draw(screen, font)
        
        # Slider Track
        track_y = self.slider_rect.centery
        pygame.draw.line(screen, (80, 80, 80), (self.slider_rect.left, track_y), (self.slider_rect.right, track_y), 2)
        
        # Calculate Handle
        if self.max_val == self.min_val: pct = 0.0
        else: pct = (self.val - self.min_val) / (self.max_val - self.min_val)
        pct = max(0.0, min(1.0, pct))
        
        handle_x = self.slider_rect.x + pct * self.slider_rect.width
        
        # Filled Track (Accent)
        pygame.draw.line(screen, THEME_ACCENT, (self.slider_rect.left, track_y), (handle_x, track_y), 2)
        
        # Handle (Circle)
        pygame.draw.circle(screen, (200, 200, 200), (int(handle_x), int(track_y)), self.handle_radius)
        pygame.draw.circle(screen, THEME_ACCENT, (int(handle_x), int(track_y)), self.handle_radius-2)

class Button:
    def __init__(self, x, y, w, h, text, active=False, toggle=True, color_active=THEME_ACCENT, color_inactive=(60, 60, 60)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = active
        self.toggle = toggle
        self.clicked = False
        self.c_active = color_active
        self.c_inactive = color_inactive
        self.cached_surf = None
    
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

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
        # Modern Flat Button
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        
        # Optional: Subtle border if inactive to distinguish from BG
        if not self.active:
            pygame.draw.rect(screen, (80, 80, 80), self.rect, 1, border_radius=4)
            
        if self.cached_surf is None:
            # Antialias = True
            self.cached_surf = font.render(self.text, True, (255, 255, 255))
        txt_rect = self.cached_surf.get_rect(center=self.rect.center)
        screen.blit(self.cached_surf, txt_rect)

class ContextMenu:
    def __init__(self, x, y, options):
        self.x = x
        self.y = y
        self.options = options
        self.width = 140
        self.height = len(options) * 30 + 10
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.selected_idx = -1
        self.action = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                rel_y = event.pos[1] - (self.y + 5)
                if rel_y >= 0:
                    self.selected_idx = rel_y // 30
                else:
                    self.selected_idx = -1
            else:
                self.selected_idx = -1
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                rel_y = event.pos[1] - (self.y + 5)
                idx = rel_y // 30
                if 0 <= idx < len(self.options):
                    self.action = self.options[idx]
                    return True
            else:
                self.action = "CLOSE"
                return True
        return False

    def draw(self, screen, font):
        # Drop Shadow
        shadow = self.rect.copy()
        shadow.x += 4; shadow.y += 4
        s_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=4)
        screen.blit(s_surf, shadow)
        
        # Main Body
        pygame.draw.rect(screen, (45, 45, 48), self.rect, border_radius=4)
        pygame.draw.rect(screen, (80, 80, 80), self.rect, 1, border_radius=4)
        
        for i, opt in enumerate(self.options):
            bg_col = (0, 122, 204) if i == self.selected_idx else (45, 45, 48)
            item_rect = pygame.Rect(self.x + 2, self.y + 5 + i*30, self.width - 4, 28)
            
            if i == self.selected_idx:
                pygame.draw.rect(screen, bg_col, item_rect, border_radius=3)
            
            # Antialias = True
            txt = font.render(opt, True, (255, 255, 255))
            screen.blit(txt, (self.x + 10, self.y + 5 + i*30 + 5))

class PropertiesDialog:
    def __init__(self, x, y, wall_data):
        self.rect = pygame.Rect(x, y, 250, 210)
        self.wall_data = wall_data
        self.done = False
        self.apply = False
        self.in_sigma = InputField(x + 100, y + 40, 100, 25, str(wall_data.get('sigma', 1.0)))
        self.in_epsilon = InputField(x + 100, y + 75, 100, 25, str(wall_data.get('epsilon', 1.0)))
        self.in_spacing = InputField(x + 100, y + 110, 100, 25, str(wall_data.get('spacing', 0.7)))
        self.btn_apply = Button(x + 20, y + 160, 80, 30, "Apply", toggle=False)
        self.btn_ok = Button(x + 150, y + 160, 80, 30, "OK", toggle=False)

    def handle_event(self, event):
        if self.in_sigma.handle_event(event): return True
        if self.in_epsilon.handle_event(event): return True
        if self.in_spacing.handle_event(event): return True
        if self.btn_apply.handle_event(event):
            self.apply = True; return True
        if self.btn_ok.handle_event(event):
            self.apply = True; self.done = True; return True
        return False

    def get_values(self):
        return {
            'sigma': self.in_sigma.get_value(1.0),
            'epsilon': self.in_epsilon.get_value(1.0),
            'spacing': self.in_spacing.get_value(0.7)
        }

    def draw(self, screen, font):
        # Shadow
        shadow = self.rect.copy(); shadow.x += 5; shadow.y += 5
        s_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=6)
        screen.blit(s_surf, shadow)
        
        # BG
        pygame.draw.rect(screen, (45, 45, 48), self.rect, border_radius=6)
        pygame.draw.rect(screen, THEME_ACCENT, self.rect, 1, border_radius=6)
        
        # Antialias = True for all font renders
        title = font.render("Wall Properties", True, (255, 255, 255))
        screen.blit(title, (self.rect.x + 15, self.rect.y + 10))
        
        screen.blit(font.render("Sigma:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 45))
        screen.blit(font.render("Epsilon:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 80))
        screen.blit(font.render("Spacing:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 115))
        
        self.in_sigma.draw(screen, font)
        self.in_epsilon.draw(screen, font)
        self.in_spacing.draw(screen, font)
        self.btn_apply.draw(screen, font)
        self.btn_ok.draw(screen, font)

class RotationDialog:
    def __init__(self, x, y, anim_data):
        self.rect = pygame.Rect(x, y, 250, 210)
        self.done = False
        self.apply = False
        
        speed = 0.0
        pivot = "center"
        if anim_data:
            speed = anim_data.get('speed', 0.0)
            pivot = anim_data.get('pivot', 'center')

        self.in_speed = InputField(x + 100, y + 60, 100, 25, str(speed))
        
        self.pivots = ["center", "start", "end"]
        try:
            self.pivot_idx = self.pivots.index(pivot)
        except:
            self.pivot_idx = 0
            
        self.btn_pivot = Button(x + 100, y + 100, 100, 25, f"{self.pivots[self.pivot_idx].title()}", toggle=False, color_inactive=(60, 60, 70))
        
        self.btn_apply = Button(x + 20, y + 160, 80, 30, "Apply", toggle=False)
        self.btn_ok = Button(x + 150, y + 160, 80, 30, "OK", toggle=False)

    def handle_event(self, event):
        if self.in_speed.handle_event(event): return True
        
        if self.btn_pivot.handle_event(event):
            self.pivot_idx = (self.pivot_idx + 1) % len(self.pivots)
            self.btn_pivot.text = f"{self.pivots[self.pivot_idx].title()}"
            self.btn_pivot.cached_surf = None
            return True
            
        if self.btn_apply.handle_event(event):
            self.apply = True; return True
        if self.btn_ok.handle_event(event):
            self.apply = True; self.done = True; return True
        return False

    def get_values(self):
        return {
            'speed': self.in_speed.get_value(0.0),
            'pivot': self.pivots[self.pivot_idx]
        }

    def draw(self, screen, font):
        # Shadow
        shadow = self.rect.copy(); shadow.x += 5; shadow.y += 5
        s_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=6)
        screen.blit(s_surf, shadow)
        
        # BG
        pygame.draw.rect(screen, (45, 45, 48), self.rect, border_radius=6)
        pygame.draw.rect(screen, THEME_ACCENT, self.rect, 1, border_radius=6)
        
        # Antialias = True for all font renders
        title = font.render("Rotation Animation", True, (255, 255, 255))
        screen.blit(title, (self.rect.x + 15, self.rect.y + 10))
        
        screen.blit(font.render("Speed:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 65))
        self.in_speed.draw(screen, font)
        
        screen.blit(font.render("Axis:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 105))
        self.btn_pivot.draw(screen, font)
        
        self.btn_apply.draw(screen, font)
        self.btn_ok.draw(screen, font)

class MenuBar:
    def __init__(self, w, h=30):
        self.rect = pygame.Rect(0, 0, w, h)
        self.items = {"File": ["(empty)"], "Tools": ["(empty)"], "Help": ["(empty)"]}
        self.active_menu = None 
        self.dropdown_rect = None
        self.hover_item_idx = -1 # Track hovered dropdown item index
        
        self.item_rects = {}
        curr_x = 10
        for key in self.items:
            r = pygame.Rect(curr_x, 0, 60, h)
            self.item_rects[key] = r
            curr_x += 60

    def resize(self, w):
        self.rect.width = w

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            # Check if mouse is over dropdown
            if self.active_menu and self.dropdown_rect:
                if self.dropdown_rect.collidepoint(event.pos):
                    # Calculate index
                    rel_y = event.pos[1] - self.dropdown_rect.y - 5
                    if rel_y >= 0:
                        idx = rel_y // 30
                        # Check bounds
                        if 0 <= idx < len(self.items[self.active_menu]):
                            # Don't hover separators
                            if self.items[self.active_menu][idx] != "---":
                                self.hover_item_idx = idx
                            else:
                                self.hover_item_idx = -1
                        else:
                            self.hover_item_idx = -1
                    else:
                        self.hover_item_idx = -1
                else:
                    self.hover_item_idx = -1
            else:
                self.hover_item_idx = -1
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for key, r in self.item_rects.items():
                if r.collidepoint(event.pos):
                    if self.active_menu == key:
                        self.active_menu = None
                        self.hover_item_idx = -1
                    else:
                        self.active_menu = key
                        self.hover_item_idx = -1
                    return True
        return False

    def draw(self, screen, font):
        pygame.draw.rect(screen, (30, 30, 30), self.rect) # Darker BG
        # No bottom line, cleaner
        
        for key, r in self.item_rects.items():
            if self.active_menu == key:
                pygame.draw.rect(screen, (50, 50, 50), r)
            
            # Antialias = True
            txt = font.render(key, True, (200, 200, 200))
            screen.blit(txt, (r.x + 10, r.y + 8))
            
        if self.active_menu:
            opts = self.items[self.active_menu]
            r = self.item_rects[self.active_menu]
            
            dd_w = 160
            dd_h = len(opts) * 30 + 10
            self.dropdown_rect = pygame.Rect(r.x, r.height, dd_w, dd_h)
            
            # Shadow
            s = self.dropdown_rect.copy(); s.x+=4; s.y+=4
            s_surf = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
            pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=4)
            screen.blit(s_surf, s)
            
            pygame.draw.rect(screen, (37, 37, 38), self.dropdown_rect, border_radius=4)
            pygame.draw.rect(screen, (60, 60, 60), self.dropdown_rect, 1, border_radius=4)
            
            for i, opt in enumerate(opts):
                # Hover Highlight
                if i == self.hover_item_idx and opt != "---":
                    h_rect = pygame.Rect(self.dropdown_rect.x + 2, self.dropdown_rect.y + 5 + i*30, self.dropdown_rect.width - 4, 30)
                    pygame.draw.rect(screen, THEME_HOVER, h_rect, border_radius=2)

                if opt == "---":
                    y = self.dropdown_rect.y + 5 + i*30 + 15
                    pygame.draw.line(screen, (60, 60, 60), (self.dropdown_rect.x + 10, y), (self.dropdown_rect.right - 10, y))
                else:
                    # Antialias = True
                    otxt = font.render(opt, True, (220, 220, 220))
                    screen.blit(otxt, (self.dropdown_rect.x + 15, self.dropdown_rect.y + 5 + i*30 + 5))
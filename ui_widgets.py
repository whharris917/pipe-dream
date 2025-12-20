import pygame
from properties import Material

# Modern Theme Colors
THEME_BG = (37, 37, 38)
THEME_INPUT_BG = (60, 60, 60)
THEME_INPUT_ACTIVE = (70, 70, 70)
THEME_ACCENT = (0, 122, 204) # VS Blue
THEME_TEXT = (220, 220, 220)
THEME_TEXT_DIM = (150, 150, 150)
THEME_BORDER = (80, 80, 80)
THEME_HOVER = (60, 60, 65) 

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
                if event.unicode.isdigit() or event.unicode in ('.', '-', ' ') or event.unicode.isalnum():
                    self.text += event.unicode
            changed = True
        return changed

    def get_value(self, default=0.0):
        try:
            return float(self.text)
        except ValueError:
            return default
            
    def get_text(self):
        return self.text

    def set_value(self, val):
        if not self.active:
            if isinstance(val, float):
                if val.is_integer(): self.text = str(int(val))
                else: self.text = f"{val:.2f}"
            else:
                self.text = str(val)

    def draw(self, screen, font):
        bg = THEME_INPUT_ACTIVE if self.active else THEME_INPUT_BG
        border = THEME_ACCENT if self.active else THEME_BORDER
        
        pygame.draw.rect(screen, bg, self.rect, border_radius=3)
        pygame.draw.rect(screen, border, self.rect, 1, border_radius=3)
        
        if self.cached_surf is None or self.text != self.last_text:
            self.last_text = self.text
            self.cached_surf = font.render(self.text, True, self.text_color)
            
        text_y = self.rect.y + (self.rect.height - self.cached_surf.get_height()) // 2
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
        self.input_h = 24 
        
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
        lbl = font.render(self.label, True, THEME_TEXT)
        screen.blit(lbl, (self.x, self.y + 2))
        
        self.input_val.draw(screen, font)
        self.input_min.draw(screen, font)
        self.input_max.draw(screen, font)
        
        track_y = self.slider_rect.centery
        pygame.draw.line(screen, (80, 80, 80), (self.slider_rect.left, track_y), (self.slider_rect.right, track_y), 2)
        
        if self.max_val == self.min_val: pct = 0.0
        else: pct = (self.val - self.min_val) / (self.max_val - self.min_val)
        pct = max(0.0, min(1.0, pct))
        
        handle_x = self.slider_rect.x + pct * self.slider_rect.width
        pygame.draw.line(screen, THEME_ACCENT, (self.slider_rect.left, track_y), (handle_x, track_y), 2)
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
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        if not self.active:
            pygame.draw.rect(screen, (80, 80, 80), self.rect, 1, border_radius=4)
            
        if self.cached_surf is None:
            self.cached_surf = font.render(self.text, True, (255, 255, 255))
        txt_rect = self.cached_surf.get_rect(center=self.rect.center)
        screen.blit(self.cached_surf, txt_rect)

class ContextMenu:
    def __init__(self, x, y, options):
        self.x = x
        self.y = y
        self.options = options
        self.width = 160
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
        shadow = self.rect.copy()
        shadow.x += 4; shadow.y += 4
        s_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=4)
        screen.blit(s_surf, shadow)
        
        pygame.draw.rect(screen, (45, 45, 48), self.rect, border_radius=4)
        pygame.draw.rect(screen, (80, 80, 80), self.rect, 1, border_radius=4)
        
        for i, opt in enumerate(self.options):
            bg_col = (0, 122, 204) if i == self.selected_idx else (45, 45, 48)
            item_rect = pygame.Rect(self.x + 2, self.y + 5 + i*30, self.width - 4, 28)
            
            if i == self.selected_idx:
                pygame.draw.rect(screen, bg_col, item_rect, border_radius=3)
            
            txt = font.render(opt, True, (255, 255, 255))
            screen.blit(txt, (self.x + 10, self.y + 5 + i*30 + 5))

class MaterialDialog:
    """
    Dialog to select, create, or edit materials.
    Replaces the old PropertiesDialog.
    """
    def __init__(self, x, y, sketch, current_material_id):
        self.rect = pygame.Rect(x, y, 300, 280)
        self.sketch = sketch
        self.done = False
        self.apply = False
        
        # Load current or default
        mat = sketch.get_material(current_material_id)
        
        self.in_id = InputField(x + 120, y + 45, 150, 25, mat.name)
        self.in_sigma = InputField(x + 120, y + 80, 150, 25, str(mat.sigma))
        self.in_epsilon = InputField(x + 120, y + 115, 150, 25, str(mat.epsilon))
        self.in_spacing = InputField(x + 120, y + 150, 150, 25, str(mat.spacing))
        
        self.btn_phys = Button(x + 120, y + 185, 80, 25, "Solid" if mat.physical else "Ghost", 
                               active=mat.physical, toggle=True, color_active=(60, 160, 60))

        self.btn_apply = Button(x + 20, y + 230, 80, 30, "Apply", toggle=False)
        self.btn_ok = Button(x + 180, y + 230, 80, 30, "OK", toggle=False)

    def handle_event(self, event):
        if self.in_id.handle_event(event):
            # Try to load existing if user types a known name
            name = self.in_id.get_text()
            if name in self.sketch.materials:
                m = self.sketch.materials[name]
                self.in_sigma.set_value(m.sigma)
                self.in_epsilon.set_value(m.epsilon)
                self.in_spacing.set_value(m.spacing)
                self.btn_phys.active = m.physical
                self.btn_phys.text = "Solid" if m.physical else "Ghost"
                self.btn_phys.cached_surf = None
            return True
            
        if self.in_sigma.handle_event(event): return True
        if self.in_epsilon.handle_event(event): return True
        if self.in_spacing.handle_event(event): return True
        
        if self.btn_phys.handle_event(event):
            self.btn_phys.text = "Solid" if self.btn_phys.active else "Ghost"
            self.btn_phys.cached_surf = None
            return True

        if self.btn_apply.handle_event(event):
            self.apply = True; return True
        if self.btn_ok.handle_event(event):
            self.apply = True; self.done = True; return True
        return False

    def get_result(self):
        name = self.in_id.get_text()
        if not name: name = "Default"
        
        # Create new Material object
        m = Material(
            name,
            sigma=self.in_sigma.get_value(1.0),
            epsilon=self.in_epsilon.get_value(1.0),
            spacing=self.in_spacing.get_value(0.7),
            physical=self.btn_phys.active
        )
        return m

    def draw(self, screen, font):
        shadow = self.rect.copy(); shadow.x += 5; shadow.y += 5
        s_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=6)
        screen.blit(s_surf, shadow)
        
        pygame.draw.rect(screen, (45, 45, 48), self.rect, border_radius=6)
        pygame.draw.rect(screen, THEME_ACCENT, self.rect, 1, border_radius=6)
        
        title = font.render("Material Editor", True, (255, 255, 255))
        screen.blit(title, (self.rect.x + 15, self.rect.y + 10))
        
        screen.blit(font.render("Material ID:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 50))
        screen.blit(font.render("Sigma:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 85))
        screen.blit(font.render("Epsilon:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 120))
        screen.blit(font.render("Spacing:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 155))
        screen.blit(font.render("Physics:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 190))
        
        self.in_id.draw(screen, font)
        self.in_sigma.draw(screen, font)
        self.in_epsilon.draw(screen, font)
        self.in_spacing.draw(screen, font)
        self.btn_phys.draw(screen, font)
        
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
        shadow = self.rect.copy(); shadow.x += 5; shadow.y += 5
        s_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=6)
        screen.blit(s_surf, shadow)
        
        pygame.draw.rect(screen, (45, 45, 48), self.rect, border_radius=6)
        pygame.draw.rect(screen, THEME_ACCENT, self.rect, 1, border_radius=6)
        
        title = font.render("Rotation Animation", True, (255, 255, 255))
        screen.blit(title, (self.rect.x + 15, self.rect.y + 10))
        
        screen.blit(font.render("Speed:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 65))
        self.in_speed.draw(screen, font)
        
        screen.blit(font.render("Axis:", True, THEME_TEXT), (self.rect.x + 20, self.rect.y + 105))
        self.btn_pivot.draw(screen, font)
        
        self.btn_apply.draw(screen, font)
        self.btn_ok.draw(screen, font)

class AnimationDialog:
    def __init__(self, x, y, driver_data):
        self.rect = pygame.Rect(x, y, 300, 280)
        self.driver = driver_data if driver_data else {'type': 'sin', 'amp': 15.0, 'freq': 0.5, 'phase': 0.0, 'rate': 10.0}
        self.done = False
        self.apply = False
        self.current_tab = self.driver.get('type', 'sin')
        
        self.btn_stop = Button(x + 20, y + 230, 100, 30, "Remove/Stop", toggle=False, color_inactive=(160, 60, 60))
        self.btn_ok = Button(x + 180, y + 230, 100, 30, "Start/Update", toggle=False, color_inactive=(60, 160, 60))
        
        self.btn_tab_sin = Button(x + 20, y + 50, 120, 25, "Sinusoidal", toggle=False, active=(self.current_tab == 'sin'))
        self.btn_tab_lin = Button(x + 160, y + 50, 120, 25, "Linear", toggle=False, active=(self.current_tab == 'lin'))

        self.in_amp = InputField(x + 150, y + 90, 100, 25, str(self.driver.get('amp', 15.0)))
        self.in_freq = InputField(x + 150, y + 130, 100, 25, str(self.driver.get('freq', 0.5)))
        self.in_phase = InputField(x + 150, y + 170, 100, 25, str(self.driver.get('phase', 0.0)))
        
        self.in_rate = InputField(x + 150, y + 90, 100, 25, str(self.driver.get('rate', 10.0)))

    def handle_event(self, event):
        if self.btn_tab_sin.handle_event(event):
            self.current_tab = 'sin'
            self.btn_tab_sin.active = True; self.btn_tab_lin.active = False
            return True
        if self.btn_tab_lin.handle_event(event):
            self.current_tab = 'lin'
            self.btn_tab_sin.active = False; self.btn_tab_lin.active = True
            return True

        if self.current_tab == 'sin':
            if self.in_amp.handle_event(event): return True
            if self.in_freq.handle_event(event): return True
            if self.in_phase.handle_event(event): return True
        else:
            if self.in_rate.handle_event(event): return True
        
        if self.btn_stop.handle_event(event):
            self.driver = None 
            self.apply = True; self.done = True
            return True
            
        if self.btn_ok.handle_event(event):
            if self.current_tab == 'sin':
                self.driver = {
                    'type': 'sin',
                    'amp': self.in_amp.get_value(0.0),
                    'freq': self.in_freq.get_value(0.0),
                    'phase': self.in_phase.get_value(0.0)
                }
            else:
                self.driver = {
                    'type': 'lin',
                    'rate': self.in_rate.get_value(0.0)
                }
            self.apply = True; self.done = True
            return True
        return False

    def get_values(self):
        return self.driver

    def draw(self, screen, font):
        shadow = self.rect.copy(); shadow.x += 5; shadow.y += 5
        s_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=6)
        screen.blit(s_surf, shadow)
        
        pygame.draw.rect(screen, (45, 45, 48), self.rect, border_radius=6)
        pygame.draw.rect(screen, (0, 122, 204), self.rect, 1, border_radius=6)
        
        title = font.render("Drive Constraint", True, (255, 255, 255))
        screen.blit(title, (self.rect.x + 15, self.rect.y + 10))
        
        self.btn_tab_sin.draw(screen, font)
        self.btn_tab_lin.draw(screen, font)
        
        if self.current_tab == 'sin':
            screen.blit(font.render("Amplitude:", True, (220, 220, 220)), (self.rect.x + 20, self.rect.y + 95))
            screen.blit(font.render("Freq (Hz):", True, (220, 220, 220)), (self.rect.x + 20, self.rect.y + 135))
            screen.blit(font.render("Phase (deg):", True, (220, 220, 220)), (self.rect.x + 20, self.rect.y + 175))
            self.in_amp.draw(screen, font)
            self.in_freq.draw(screen, font)
            self.in_phase.draw(screen, font)
        else:
            screen.blit(font.render("Rate (deg/s):", True, (220, 220, 220)), (self.rect.x + 20, self.rect.y + 95))
            self.in_rate.draw(screen, font)
            
        self.btn_stop.draw(screen, font)
        self.btn_ok.draw(screen, font)

class MenuBar:
    def __init__(self, w, h=30):
        self.rect = pygame.Rect(0, 0, w, h)
        self.items = {"File": ["(empty)"], "Tools": ["(empty)"], "Help": ["(empty)"]}
        self.active_menu = None 
        self.dropdown_rect = None
        self.hover_item_idx = -1 
        
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
            if self.active_menu and self.dropdown_rect:
                if self.dropdown_rect.collidepoint(event.pos):
                    rel_y = event.pos[1] - self.dropdown_rect.y - 5
                    if rel_y >= 0:
                        idx = rel_y // 30
                        if 0 <= idx < len(self.items[self.active_menu]):
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
        pygame.draw.rect(screen, (30, 30, 30), self.rect) 
        
        for key, r in self.item_rects.items():
            if self.active_menu == key:
                pygame.draw.rect(screen, (50, 50, 50), r)
            txt = font.render(key, True, (200, 200, 200))
            screen.blit(txt, (r.x + 10, r.y + 8))
            
        if self.active_menu:
            opts = self.items[self.active_menu]
            r = self.item_rects[self.active_menu]
            
            dd_w = 160
            dd_h = len(opts) * 30 + 10
            self.dropdown_rect = pygame.Rect(r.x, r.height, dd_w, dd_h)
            
            s = self.dropdown_rect.copy(); s.x+=4; s.y+=4
            s_surf = pygame.Surface((s.width, s.height), pygame.SRCALPHA)
            pygame.draw.rect(s_surf, (0, 0, 0, 100), s_surf.get_rect(), border_radius=4)
            screen.blit(s_surf, s)
            
            pygame.draw.rect(screen, (37, 37, 38), self.dropdown_rect, border_radius=4)
            pygame.draw.rect(screen, (60, 60, 60), self.dropdown_rect, 1, border_radius=4)
            
            for i, opt in enumerate(opts):
                if i == self.hover_item_idx and opt != "---":
                    h_rect = pygame.Rect(self.dropdown_rect.x + 2, self.dropdown_rect.y + 5 + i*30, self.dropdown_rect.width - 4, 30)
                    pygame.draw.rect(screen, THEME_HOVER, h_rect, border_radius=2)

                if opt == "---":
                    y = self.dropdown_rect.y + 5 + i*30 + 15
                    pygame.draw.line(screen, (60, 60, 60), (self.dropdown_rect.x + 10, y), (self.dropdown_rect.right - 10, y))
                else:
                    otxt = font.render(opt, True, (220, 220, 220))
                    screen.blit(otxt, (self.dropdown_rect.x + 15, self.dropdown_rect.y + 5 + i*30 + 5))
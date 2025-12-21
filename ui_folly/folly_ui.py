import pygame
import math

# --- THEME SETTINGS ---
C_BG = (18, 18, 20)
C_PANEL = (30, 30, 33)
C_BORDER = (55, 55, 60)

# --- COLOR UPDATES: MAXIMUM BRIGHTNESS ---
C_TEXT = (255, 255, 255)       # Pure White (Active/Hover)
C_TEXT_IDLE = (255, 255, 255)  # Pure White (Normal State) - No longer gray
C_TEXT_DIM = (220, 220, 220)   # Very Light Gray (Disabled/Headers) - Readable & Bright
C_SHADOW = (0, 0, 0, 80)       

# Styles
C_ACCENT = (0, 122, 204)       
C_DANGER = (204, 50, 50)       
C_SUCCESS = (60, 160, 60)      
C_WARNING = (220, 160, 40)     

# --- MATH HELPER ---
def lerp(start, end, t):
    return start + (end - start) * t

class AnimVar:
    def __init__(self, value, speed=10.0):
        self.value = value
        self.target = value
        self.speed = speed

    def update(self, dt):
        self.value += (self.target - self.value) * min(self.speed * dt, 1.0)
        
    def set(self, target):
        self.target = target

# --- WIDGETS ---

class JuicyButton:
    def __init__(self, x, y, w, h, text="", icon_name=None, sound_name=None, style="normal", tooltip=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.icon_name = icon_name
        self.sound_name = sound_name
        self.style = style 
        self.active = False 
        self.hovered = False
        self.clicked = False
        self.disabled = False
        # Hooks
        self.track_to_play = None
        self.is_stop_btn = False
        self.is_external_track = None
        # Anim
        self.anim_hover = AnimVar(0.0, speed=15.0)
        self.anim_scale = AnimVar(1.0, speed=20.0)
        self.anim_click = AnimVar(0.0, speed=10.0)
        self.ripples = []

    def handle_event(self, event, assets):
        if self.disabled: return
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.hovered
            self.hovered = self.rect.collidepoint(event.pos)
            if self.hovered:
                self.anim_hover.set(1.0)
                self.anim_scale.set(1.02)
                if not was_hovered and assets: assets.play_sound('hover')
            else:
                self.anim_hover.set(0.0)
                self.anim_scale.set(1.0)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.clicked = True
                self.anim_scale.value = 0.95
                self.anim_click.value = 1.0
                self.ripples.append({'x': event.pos[0]-self.rect.x, 'y': event.pos[1]-self.rect.y, 'r': 5, 'a': 1.0})
                if assets: assets.play_sound('click')
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.clicked:
                if self.hovered and event.button == 1:
                    if self.style == "toggle": self.active = not self.active
                self.clicked = False

    def update(self, dt):
        self.anim_hover.update(dt)
        self.anim_scale.update(dt)
        self.anim_click.update(dt)
        for r in self.ripples[:]:
            r['r'] += 200 * dt
            r['a'] -= 2.0 * dt
            if r['a'] <= 0: self.ripples.remove(r)

    def draw(self, screen, font, assets=None):
        scale = self.anim_scale.value
        w, h = self.rect.width * scale, self.rect.height * scale
        draw_rect = pygame.Rect(0, 0, w, h)
        draw_rect.center = self.rect.center
        
        # Colors
        base_col = list(C_PANEL)
        target_col = list(C_PANEL)
        border_target = C_BORDER
        
        if self.style == "primary": base_col, target_col, border_target = list(C_ACCENT), [min(c+30,255) for c in C_ACCENT], C_ACCENT
        elif self.style == "danger": base_col, target_col, border_target = list(C_DANGER), [min(c+30,255) for c in C_DANGER], C_DANGER
        elif self.style == "success": base_col, target_col, border_target = list(C_SUCCESS), [min(c+30,255) for c in C_SUCCESS], C_SUCCESS
        elif (self.style == "toggle" or self.style == "normal") and self.active: target_col, border_target = list(C_ACCENT), C_ACCENT

        h_val = self.anim_hover.value
        r = lerp(base_col[0], target_col[0], h_val)
        g = lerp(base_col[1], target_col[1], h_val)
        b = lerp(base_col[2], target_col[2], h_val)
        
        # Click flash
        c_val = self.anim_click.value
        r, g, b = min(255, r+100*c_val), min(255, g+100*c_val), min(255, b+100*c_val)
        final_col = (int(r), int(g), int(b))
        
        # Draw Shadow
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, C_SHADOW, (0,0,w,h), border_radius=8) 
        screen.blit(s, (draw_rect.x, draw_rect.y+4))
        
        # Draw Body
        pygame.draw.rect(screen, final_col, draw_rect, border_radius=8)
        
        # Draw Border
        br, bg, bb = lerp(C_BORDER[0], border_target[0], h_val), lerp(C_BORDER[1], border_target[1], h_val), lerp(C_BORDER[2], border_target[2], h_val)
        pygame.draw.rect(screen, (br, bg, bb), draw_rect, 1, border_radius=8)
        
        # Draw Ripple
        if self.ripples:
            clip = pygame.Surface((w, h), pygame.SRCALPHA)
            for rip in self.ripples:
                pygame.draw.circle(clip, (255, 255, 255, int(rip['a']*50)), (int(rip['x']), int(rip['y'])), int(rip['r']))
            screen.blit(clip, draw_rect.topleft)

        # Draw Content
        if self.icon_name and assets:
            icon = assets.get_icon(self.icon_name)
            if icon: screen.blit(icon, (draw_rect.centerx - icon.get_width()//2, draw_rect.centery - icon.get_height()//2))
        elif self.text:
            col = C_TEXT_IDLE
            if self.hovered or self.active or self.style != "normal":
                col = C_TEXT
            if self.disabled: 
                col = C_TEXT_DIM
            
            # Simple Drop Shadow on Text for readability against bright colors
            if self.style != "normal" or self.active:
                ts_shadow = font.render(self.text, True, (0,0,0))
                screen.blit(ts_shadow, (draw_rect.centerx - ts_shadow.get_width()//2 + 1, draw_rect.centery - ts_shadow.get_height()//2 + 1))

            ts = font.render(self.text, True, col)
            screen.blit(ts, (draw_rect.centerx - ts.get_width()//2, draw_rect.centery - ts.get_height()//2))

class Checkbox:
    def __init__(self, x, y, size, label="", checked=False):
        self.rect = pygame.Rect(x, y, size, size)
        self.label = label
        self.checked = checked
        self.hovered = False
        self.anim_fill = AnimVar(1.0 if checked else 0.0)

    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.checked = not self.checked
                if assets: assets.play_sound('click')

    def update(self, dt):
        self.anim_fill.set(1.0 if self.checked else 0.0)
        self.anim_fill.update(dt)

    def draw(self, screen, font):
        border_col = C_ACCENT if (self.hovered or self.checked) else C_BORDER
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=4)
        pygame.draw.rect(screen, border_col, self.rect, 1, border_radius=4)
        
        sz = self.anim_fill.value * (self.rect.width - 6)
        if sz > 1:
            check_rect = pygame.Rect(0, 0, sz, sz)
            check_rect.center = self.rect.center
            pygame.draw.rect(screen, C_ACCENT, check_rect, border_radius=2)
            
        if self.label:
            ts = font.render(self.label, True, C_TEXT) # Always bright
            screen.blit(ts, (self.rect.right + 10, self.rect.centery - ts.get_height()//2))

class Slider:
    def __init__(self, x, y, w, val=0.5):
        self.rect = pygame.Rect(x, y, w, 20)
        self.val = val
        self.dragging = False
        self.hovered = False
        
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            if self.dragging:
                rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.width))
                self.val = rel_x / self.rect.width
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.dragging = True
                rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.width))
                self.val = rel_x / self.rect.width
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
    def update(self, dt): pass
    
    def draw(self, screen, font):
        pygame.draw.rect(screen, C_PANEL, (self.rect.x, self.rect.centery-3, self.rect.width, 6), border_radius=3)
        fill_w = self.rect.width * self.val
        pygame.draw.rect(screen, C_ACCENT, (self.rect.x, self.rect.centery-3, fill_w, 6), border_radius=3)
        hx = self.rect.x + fill_w
        # Handle Color
        col = C_TEXT
        pygame.draw.circle(screen, col, (int(hx), self.rect.centery), 8)

class Knob:
    def __init__(self, x, y, r, val=0.0):
        self.rect = pygame.Rect(x-r, y-r, r*2, r*2)
        self.r = r
        self.val = val
        self.dragging = False
        self.start_y = 0
        self.start_val = 0
        
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.start_y = event.pos[1]
                self.start_val = self.val
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                dy = self.start_y - event.pos[1]
                self.val = max(0.0, min(1.0, self.start_val + dy * 0.01))
                
    def update(self, dt): pass
    
    def draw(self, screen, font):
        cx, cy = self.rect.center
        pygame.draw.circle(screen, C_PANEL, (cx, cy), self.r)
        pygame.draw.circle(screen, C_BORDER, (cx, cy), self.r, 2)
        start_angle = math.radians(225)
        end_angle = math.radians(225 - (270 * self.val))
        dot_x = cx + math.cos(end_angle) * (self.r * 0.7)
        dot_y = cy - math.sin(end_angle) * (self.r * 0.7)
        col = C_ACCENT if self.dragging else C_TEXT
        pygame.draw.line(screen, col, (cx, cy), (dot_x, dot_y), 3)
        pygame.draw.circle(screen, C_TEXT, (int(dot_x), int(dot_y)), 4)

class TextInput:
    def __init__(self, x, y, w, h, placeholder="Type here..."):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.focused = False
        self.cursor_timer = 0.0
        
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.focused = False
            else:
                if len(self.text) < 30:
                    self.text += event.unicode
                    
    def update(self, dt):
        self.cursor_timer += dt
        
    def draw(self, screen, font):
        col = C_PANEL
        border = C_ACCENT if self.focused else C_BORDER
        pygame.draw.rect(screen, col, self.rect, border_radius=4)
        pygame.draw.rect(screen, border, self.rect, 1, border_radius=4)
        
        # Text Logic
        txt_col = C_TEXT if self.text else C_TEXT_DIM
        display_txt = self.text if self.text else self.placeholder
        
        ts = font.render(display_txt, True, txt_col)
        screen.blit(ts, (self.rect.x + 8, self.rect.centery - ts.get_height()//2))
        
        if self.focused and (int(self.cursor_timer * 2) % 2 == 0):
            cx = self.rect.x + 8 + font.size(self.text)[0]
            pygame.draw.line(screen, C_ACCENT, (cx, self.rect.y+8), (cx, self.rect.bottom-8), 2)

class ProgressBar:
    def __init__(self, x, y, w, h, val=0.0):
        self.rect = pygame.Rect(x, y, w, h)
        self.val = val
        
    def update(self, dt):
        self.val += dt * 0.2
        if self.val > 1.0: self.val = 0.0
        
    def draw(self, screen, font):
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=4)
        fill_w = int(self.rect.width * self.val)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(screen, C_ACCENT, fill_rect, border_radius=4)
            for i in range(0, fill_w, 10):
                pygame.draw.line(screen, (255,255,255,50), (self.rect.x+i, self.rect.y), (self.rect.x+i-5, self.rect.bottom), 2)

class Dropdown:
    def __init__(self, x, y, w, h, options, default_index=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.selected_index = default_index
        self.is_open = False
        self.hovered = False
        self.hover_index = -1
        self.anim_open = AnimVar(0.0, speed=15.0)

    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            self.hover_index = -1
            if self.is_open:
                total_h = len(self.options) * 30
                menu_rect = pygame.Rect(self.rect.x, self.rect.bottom + 5, self.rect.width, total_h)
                if menu_rect.collidepoint(event.pos):
                    rel_y = event.pos[1] - menu_rect.y
                    self.hover_index = int(rel_y // 30)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
                    if assets: assets.play_sound('click')
                    return True
                elif self.is_open and self.hover_index != -1:
                    self.selected_index = self.hover_index
                    self.is_open = False
                    if assets: assets.play_sound('snap')
                    return True
                elif self.is_open:
                    self.is_open = False
                    return True
        return False

    def update(self, dt):
        self.anim_open.set(1.0 if self.is_open else 0.0)
        self.anim_open.update(dt)

    def draw(self, screen, font):
        border = C_ACCENT if (self.is_open or self.hovered) else C_BORDER
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=6)
        pygame.draw.rect(screen, border, self.rect, 1, border_radius=6)
        txt = self.options[self.selected_index] if self.options else ""
        t_surf = font.render(txt, True, C_TEXT) # Always bright
        screen.blit(t_surf, (self.rect.x + 10, self.rect.centery - t_surf.get_height()//2))
        ax, ay = self.rect.right - 15, self.rect.centery
        pygame.draw.polygon(screen, C_TEXT, [(ax-5, ay-3), (ax+5, ay-3), (ax, ay+3)] if not self.is_open else [(ax-5, ay+3), (ax+5, ay+3), (ax, ay-3)])

    def draw_overlay(self, screen, font):
        if self.anim_open.value < 0.01: return
        h_per_item = 30
        total_h = len(self.options) * h_per_item
        current_h = total_h * self.anim_open.value
        full_surf = pygame.Surface((self.rect.width, total_h), pygame.SRCALPHA)
        full_surf.fill((*C_BG, 255))
        pygame.draw.rect(full_surf, (40, 40, 45), (0, 0, self.rect.width, total_h))
        pygame.draw.rect(full_surf, C_BORDER, (0, 0, self.rect.width, total_h), 1)
        for i, opt in enumerate(self.options):
            iy = i * h_per_item
            if i == self.hover_index: pygame.draw.rect(full_surf, (60, 60, 65), (0, iy, self.rect.width, h_per_item))
            if i == self.selected_index: pygame.draw.rect(full_surf, C_ACCENT, (0, iy, 4, h_per_item))
            col = C_TEXT # All list items bright
            t_surf = font.render(opt, True, col)
            full_surf.blit(t_surf, (15, iy + 8))
        screen.blit(full_surf, (self.rect.x, self.rect.bottom + 5), area=(0, 0, self.rect.width, int(current_h)))

class Panel:
    def __init__(self, x, y, w, h, title=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
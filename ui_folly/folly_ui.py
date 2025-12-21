import pygame
import math
import random

# --- PROFESSIONAL THEME ---
C_BG = (18, 20, 24)           # Deep charcoal blue
C_PANEL = (30, 34, 40)        # Soft Slate
C_BORDER = (50, 55, 65)       # Low contrast border
C_TEXT = (255, 255, 255)      # Pure White core (Active)
C_TEXT_IDLE = (235, 235, 240) # Soft paper white (Normal)
C_TEXT_DIM = (160, 165, 175)  # Muted slate (Disabled/Header)
C_SHADOW = (0, 0, 0, 120)     

# Muted Accent Colors
C_ACCENT = (70, 160, 220)     # Industrial Blue
C_SUCCESS = (110, 190, 130)   # Sage Green
C_DANGER = (210, 100, 100)    # Soft Red
C_WARNING = (230, 180, 80)    # Amber

# --- HELPERS ---
def lerp(start, end, t): return start + (end - start) * t

def draw_soft_circle(surf, color, center, radius):
    """Draws a circle with volumetric highlights."""
    pygame.draw.circle(surf, color, center, radius)
    # Highlight (Top-Left)
    high_col = [min(c + 45, 255) for c in color]
    off_r = int(radius * 0.6)
    off_x = center[0] - int(radius * 0.3)
    off_y = center[1] - int(radius * 0.3)
    if off_r > 0:
        pygame.draw.circle(surf, high_col, (off_x, off_y), off_r)
    # Rim Light
    pygame.draw.circle(surf, (0, 0, 0, 60), center, radius, 1) 
    pygame.draw.arc(surf, (255, 255, 255, 80), 
                    (center[0]-radius+1, center[1]-radius+1, radius*2-2, radius*2-2), 
                    math.radians(45), math.radians(180), 1)

def draw_glass_body(surf, rect, color, level=0.0):
    """Draws a glass container with liquid inside."""
    pygame.draw.rect(surf, (25, 30, 35), rect, border_radius=4)
    if level > 0:
        fill_h = int(rect.height * level)
        if fill_h > 0:
            fill_rect = pygame.Rect(rect.x, rect.bottom - fill_h, rect.width, fill_h)
            liq_s = pygame.Surface((rect.width, fill_h), pygame.SRCALPHA)
            liq_s.fill((*color, 180)) 
            surf.blit(liq_s, fill_rect.topleft)
            pygame.draw.line(surf, (255,255,255,150), fill_rect.topleft, fill_rect.topright, 1)
    
    # Glint
    glint_s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.line(glint_s, (255,255,255,30), (0, rect.height), (rect.width, 0), 10)
    surf.blit(glint_s, rect.topleft)
    pygame.draw.rect(surf, (60, 65, 75), rect, 2, border_radius=4)

class AnimVar:
    def __init__(self, value, speed=10.0): self.value = value; self.target = value; self.speed = speed
    def update(self, dt): self.value += (self.target - self.value) * min(self.speed * dt, 1.0)
    def set(self, target): self.target = target

# --- BASE WIDGET ---
class JuicyButton:
    def __init__(self, x, y, w, h, text="", icon_name=None, sound_name=None, style="normal", tooltip=""):
        self.rect = pygame.Rect(x, y, w, h); self.text = text; self.icon_name = icon_name; self.sound_name = sound_name; self.style = style 
        self.active = False; self.hovered = False; self.clicked = False; self.disabled = False
        self.track_to_play = None; self.is_stop_btn = False; self.is_external_track = None
        self.anim_hover = AnimVar(0.0, speed=15.0); self.anim_scale = AnimVar(1.0, speed=20.0); self.anim_click = AnimVar(0.0, speed=10.0); self.ripples = []
    
    def handle_event(self, event, assets):
        if self.disabled: return
        if event.type == pygame.MOUSEMOTION:
            was = self.hovered; self.hovered = self.rect.collidepoint(event.pos)
            if self.hovered: 
                self.anim_hover.set(1.0); self.anim_scale.set(1.02); 
            else: 
                self.anim_hover.set(0.0); self.anim_scale.set(1.0)
            
            # --- FIX: Play the assigned sound on hover (Preview Mode) ---
            if self.hovered and not was and assets:
                preview = self.sound_name if self.sound_name else 'hover'
                assets.play_sound(preview)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.clicked = True; self.anim_scale.value = 0.95; self.anim_click.value = 1.0
                self.ripples.append({'x': event.pos[0]-self.rect.x, 'y': event.pos[1]-self.rect.y, 'r': 5, 'a': 1.0})
                
                # We still play on click for rhythmic tapping
                if assets: 
                    snd = self.sound_name if self.sound_name else 'click'
                    assets.play_sound(snd)
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.clicked:
                if self.hovered and event.button == 1 and self.style == "toggle": self.active = not self.active
                self.clicked = False

    def update(self, dt):
        self.anim_hover.update(dt); self.anim_scale.update(dt); self.anim_click.update(dt)
        for r in self.ripples[:]: r['r']+=200*dt; r['a']-=2.0*dt; 
        if self.ripples and self.ripples[0]['a']<=0: self.ripples.pop(0)

    def draw(self, screen, font, assets=None):
        scale = self.anim_scale.value; w, h = self.rect.width * scale, self.rect.height * scale
        draw_rect = pygame.Rect(0, 0, w, h); draw_rect.center = self.rect.center
        
        base, target, border = list(C_PANEL), list(C_PANEL), list(C_BORDER)
        if self.style == "primary": base, target, border = list(C_ACCENT), [min(c+30,255) for c in C_ACCENT], list(C_ACCENT)
        elif self.style == "danger": base, target, border = list(C_DANGER), [min(c+30,255) for c in C_DANGER], list(C_DANGER)
        elif self.style == "success": base, target, border = list(C_SUCCESS), [min(c+30,255) for c in C_SUCCESS], list(C_SUCCESS)
        elif (self.style=="toggle" or self.style=="normal") and self.active: target, border = list(C_ACCENT), list(C_ACCENT)
        
        h_val = self.anim_hover.value
        col = [int(lerp(base[i], target[i], h_val)) for i in range(3)]
        c_val = self.anim_click.value
        col = [min(255, c + int(100*c_val)) for c in col]
        
        s = pygame.Surface((w, h), pygame.SRCALPHA); pygame.draw.rect(s, C_SHADOW, (0,0,w,h), border_radius=8) 
        screen.blit(s, (draw_rect.x, draw_rect.y+4))
        pygame.draw.rect(screen, col, draw_rect, border_radius=8)
        
        b_col = [int(lerp(C_BORDER[i], border[i], h_val)) for i in range(3)]
        pygame.draw.rect(screen, b_col, draw_rect, 1, border_radius=8)
        
        if self.ripples:
            clip = pygame.Surface((w, h), pygame.SRCALPHA)
            for rip in self.ripples: pygame.draw.circle(clip, (255, 255, 255, int(rip['a']*50)), (int(rip['x']), int(rip['y'])), int(rip['r']))
            screen.blit(clip, draw_rect.topleft)

        if self.icon_name and assets:
            icon = assets.get_icon(self.icon_name)
            if icon: screen.blit(icon, (draw_rect.centerx - icon.get_width()//2, draw_rect.centery - icon.get_height()//2))
        elif self.text:
            t_col = C_TEXT if (self.hovered or self.active or self.style != "normal") else C_TEXT_IDLE
            if self.disabled: t_col = C_TEXT_DIM
            ts = font.render(self.text, True, t_col)
            screen.blit(ts, (draw_rect.centerx-ts.get_width()//2, draw_rect.centery-ts.get_height()//2))

# --- STANDARD WIDGETS ---
class Checkbox:
    def __init__(self, x, y, size, label="", checked=False):
        self.rect = pygame.Rect(x, y, size, size); self.label = label; self.checked = checked; self.hovered = False; self.anim_fill = AnimVar(1.0 if checked else 0.0)
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEMOTION: self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hovered: self.checked = not self.checked; assets and assets.play_sound('click')
    def update(self, dt): self.anim_fill.set(1.0 if self.checked else 0.0); self.anim_fill.update(dt)
    def draw(self, s, f):
        border = C_ACCENT if (self.hovered or self.checked) else C_BORDER
        pygame.draw.rect(s, C_PANEL, self.rect, border_radius=4); pygame.draw.rect(s, border, self.rect, 1, border_radius=4)
        sz = self.anim_fill.value * (self.rect.width - 6)
        if sz > 1:
            cr = pygame.Rect(0,0,sz,sz); cr.center = self.rect.center; pygame.draw.rect(s, C_ACCENT, cr, border_radius=2)
        if self.label: s.blit(f.render(self.label, True, C_TEXT_IDLE), (self.rect.right+10, self.rect.centery-8))

class Slider:
    def __init__(self, x, y, w, val=0.5): self.rect = pygame.Rect(x, y, w, 20); self.val = val; self.dragging = False; self.hovered = False
    def handle_event(self, e, a):
        if e.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(e.pos)
            if self.dragging: self.val = max(0, min((e.pos[0]-self.rect.x)/self.rect.w, 1.0))
        elif e.type == pygame.MOUSEBUTTONDOWN and self.hovered: self.dragging = True; self.val = max(0, min((e.pos[0]-self.rect.x)/self.rect.w, 1.0))
        elif e.type == pygame.MOUSEBUTTONUP: self.dragging = False
    def update(self, dt): pass
    def draw(self, s, f):
        pygame.draw.rect(s, C_PANEL, (self.rect.x, self.rect.centery-3, self.rect.w, 6), border_radius=3)
        pygame.draw.rect(s, C_ACCENT, (self.rect.x, self.rect.centery-2, self.rect.w*self.val, 4), border_radius=2)
        draw_soft_circle(s, (200,200,200), (int(self.rect.x+self.rect.width*self.val), self.rect.centery), 7)

class Knob:
    def __init__(self, x, y, r, val=0.0):
        self.rect = pygame.Rect(x-r, y-r, r*2, r*2); self.r = r; self.val = val; self.dragging = False; self.sy=0; self.sv=0
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos): self.dragging = True; self.sy = event.pos[1]; self.sv = self.val
        elif event.type == pygame.MOUSEBUTTONUP: self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging: self.val = max(0.0, min(1.0, self.sv + (self.sy - event.pos[1]) * 0.01))
    def update(self, dt): pass
    def draw(self, s, f):
        cx, cy = self.rect.center
        draw_soft_circle(s, C_PANEL, (cx, cy), self.r)
        pygame.draw.circle(s, C_BORDER, (cx, cy), self.r, 2)
        end = math.radians(225 - (270 * self.val))
        dx, dy = cx + math.cos(end)*(self.r*0.7), cy - math.sin(end)*(self.r*0.7)
        col = C_ACCENT if self.dragging else C_TEXT_DIM
        pygame.draw.line(s, col, (cx, cy), (dx, dy), 3); pygame.draw.circle(s, C_TEXT, (int(dx), int(dy)), 3)

class ProgressBar:
    def __init__(self, x, y, w, h, val=0.0): self.rect = pygame.Rect(x, y, w, h); self.val = val
    def update(self, dt): self.val = (self.val + dt * 0.2) % 1.0
    def draw(self, screen, font):
        pygame.draw.rect(screen, (20,22,26), self.rect, border_radius=4)
        pygame.draw.rect(screen, C_ACCENT, (self.rect.x, self.rect.y, self.rect.w*self.val, self.rect.h), border_radius=4)

class TextInput:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h); self.text = ""; self.placeholder = placeholder; self.focused = False; self.t = 0.0
    def handle_event(self, e, a):
        if e.type == pygame.MOUSEBUTTONDOWN: self.focused = self.rect.collidepoint(e.pos)
        elif e.type == pygame.KEYDOWN and self.focused:
            if e.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif e.key == pygame.K_RETURN: self.focused = False
            else: self.text += e.unicode
    def update(self, dt): self.t += dt
    def draw(self, s, f):
        border = C_ACCENT if self.focused else C_BORDER
        pygame.draw.rect(s, C_PANEL, self.rect, border_radius=4); pygame.draw.rect(s, border, self.rect, 1, border_radius=4)
        ts = f.render(self.text if self.text else self.placeholder, True, C_TEXT if self.text else C_TEXT_DIM)
        s.blit(ts, (self.rect.x+8, self.rect.centery-ts.get_height()//2))
        if self.focused and (int(self.t*2)%2==0):
            cx = self.rect.x + 8 + f.size(self.text)[0]
            pygame.draw.line(s, C_ACCENT, (cx, self.rect.y+8), (cx, self.rect.bottom-8), 2)

class Dropdown:
    def __init__(self, x, y, w, h, options, default_index=0):
        self.rect = pygame.Rect(x, y, w, h); self.options = options; self.selected_index = default_index
        self.is_open = False; self.hovered = False; self.hover_index = -1; self.anim_open = AnimVar(0.0)
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos); self.hover_index = -1
            if self.is_open:
                mr = pygame.Rect(self.rect.x, self.rect.bottom+5, self.rect.width, len(self.options)*30)
                if mr.collidepoint(event.pos): self.hover_index = int((event.pos[1]-mr.y)//30)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos): self.is_open = not self.is_open; assets and assets.play_sound('click'); return True
                elif self.is_open and self.hover_index != -1: self.selected_index = self.hover_index; self.is_open = False; assets and assets.play_sound('snap'); return True
                elif self.is_open: self.is_open = False; return True
        return False
    def update(self, dt): self.anim_open.set(1.0 if self.is_open else 0.0); self.anim_open.update(dt)
    def draw(self, screen, font):
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=6); pygame.draw.rect(screen, C_BORDER, self.rect, 1, border_radius=6)
        ts = font.render(self.options[self.selected_index] if self.options else "", True, C_TEXT_IDLE)
        screen.blit(ts, (self.rect.x+10, self.rect.centery-ts.get_height()//2))
    def draw_overlay(self, screen, font):
        if self.anim_open.value < 0.01: return
        th = len(self.options)*30; ch = th * self.anim_open.value
        fs = pygame.Surface((self.rect.width, th), pygame.SRCALPHA); fs.fill((*C_BG, 255)); pygame.draw.rect(fs, (40,40,45), (0,0,self.rect.width,th)); pygame.draw.rect(fs, C_BORDER, (0,0,self.rect.width,th), 1)
        for i, opt in enumerate(self.options):
            iy = i * 30
            if i == self.hover_index: pygame.draw.rect(fs, (60,60,65), (0,iy,self.rect.width,30))
            fs.blit(font.render(opt, True, C_TEXT if i==self.selected_index else C_TEXT_IDLE), (15, iy+8))
        screen.blit(fs, (self.rect.x, self.rect.bottom+5), area=(0,0,self.rect.width, int(ch)))

class Panel:
    def __init__(self, x, y, w, h, title=""): self.rect = pygame.Rect(x, y, w, h); self.title = title

# --- PROFESSIONAL FACTORY WIDGETS ---

class FactoryGear(JuicyButton):
    def __init__(self, x, y, size, speed=30): super().__init__(x, y, size, size); self.a=0; self.base=speed
    def update(self, dt): super().update(dt); self.a += (self.base*5 if self.hovered else self.base)*dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.35
        for i in range(8):
            rad = math.radians(self.a + i*45)
            draw_soft_circle(s, (100, 110, 120), (cx+math.cos(rad)*(r+3), cy+math.sin(rad)*(r+3)), 3)
        draw_soft_circle(s, (80, 85, 95), (cx, cy), int(r))
        pygame.draw.circle(s, (40, 45, 50), (cx, cy), int(r/2.5))

class FactoryTank(JuicyButton):
    def __init__(self, x, y, size, fluid_col=C_ACCENT): super().__init__(x, y, size, size); self.lvl=0; self.fill=True; self.col=fluid_col
    def update(self, dt): 
        super().update(dt); self.lvl += (dt*0.4 if self.fill else -dt*0.4)
        if self.lvl>=1 or self.lvl<=0: self.fill = not self.fill
    def draw(self, s, f, a=None):
        super().draw(s, f, a)
        inner_rect = self.rect.inflate(-10, -10)
        draw_glass_body(s, inner_rect, self.col, self.lvl)

class FactoryFan(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.a = 0
    def update(self, dt): super().update(dt); self.a += (1000 if self.hovered else 200)*dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.35
        draw_soft_circle(s, (40, 40, 45), (cx, cy), int(r))
        for i in range(3):
            rad = math.radians(self.a + i*120)
            ex, ey = cx+math.cos(rad)*r, cy+math.sin(rad)*r
            pygame.draw.line(s, (180, 190, 200), (cx, cy), (ex, ey), 3)
        pygame.draw.circle(s, (100, 100, 110), (cx, cy), 4)

class FactoryPower(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t = random.uniform(0, 10)
    def update(self, dt): super().update(dt); self.t += dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.32
        p = (math.sin(self.t*4)+1)*0.5; col = [int(lerp(60, C_ACCENT[i], p)) for i in range(3)]
        pygame.draw.arc(s, col, (cx-r, cy-r, r*2, r*2), 2.1, 0.9, 3)
        pygame.draw.line(s, col, (cx, cy-r), (cx, cy), 3)
        if p > 0.4:
            bs = int(r*1.5); bloom = pygame.Surface((bs*2, bs*2), pygame.SRCALPHA)
            pygame.draw.circle(bloom, (*C_ACCENT, int(40*p)), (bs, bs), bs)
            s.blit(bloom, (cx-bs, cy-bs), special_flags=pygame.BLEND_RGBA_ADD)

class FactoryGauge(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.v=0.5; self.nt=random.uniform(0,100)
    def update(self, dt): super().update(dt); self.nt+=dt; self.v=0.5+math.sin(self.nt)*0.4
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.35
        draw_soft_circle(s, (30, 30, 35), (cx, cy), int(r))
        rect=(cx-r, cy-r, r*2, r*2)
        pygame.draw.arc(s, C_SUCCESS, rect, 3.14, 5.0, 2)
        pygame.draw.arc(s, C_DANGER, rect, 5.0, 6.28, 2)
        rad = math.radians(180 + self.v*180); pygame.draw.line(s, (230, 80, 80), (cx, cy), (cx+math.cos(rad)*r, cy-math.sin(rad)*r), 2)

class FactoryLight(JuicyButton):
    def __init__(self, x, y, size, color=C_SUCCESS): super().__init__(x, y, size, size); self.col=color; self.t=0
    def update(self, dt): super().update(dt); self.t += dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.3
        p = (math.sin(self.t*6)+1)*0.5
        draw_soft_circle(s, [int(lerp(40, self.col[i], p)) for i in range(3)], (cx, cy), int(r))
        if p > 0.2:
            bs = int(r*2.0); bloom = pygame.Surface((bs*2, bs*2), pygame.SRCALPHA)
            pygame.draw.circle(bloom, (*self.col, int(60*p)), (bs, bs), bs)
            s.blit(bloom, (cx-bs, cy-bs), special_flags=pygame.BLEND_RGBA_ADD)

class FactoryChip(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size)
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-12, -12)
        pygame.draw.rect(s, (35, 38, 45), r, border_radius=2)
        for i in range(4): 
            y_pos = r.y + (i+1)*(r.h/5)
            pygame.draw.line(s, (180, 160, 50), (r.x-2, y_pos), (r.x+2, y_pos), 1)
            pygame.draw.line(s, (180, 160, 50), (r.right-2, y_pos), (r.right+2, y_pos), 1)
        pygame.draw.rect(s, (255,255,255,20), r, 1, border_radius=2)

class FactoryPiston(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.ph = random.uniform(0, 10)
    def update(self, dt): super().update(dt); self.ph += dt*5
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; ho = math.sin(self.ph)*5
        pygame.draw.rect(s, (80, 80, 85), (cx-3, cy-8, 6, 16))
        pygame.draw.rect(s, (180, 185, 190), (cx-6, cy+ho-3, 12, 6))

class FactoryGraph(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.d = [0.5]*5; self.t = 0
    def update(self, dt): 
        super().update(dt); self.t += dt
        if self.t > 0.1: self.t=0; self.d.pop(0); self.d.append(max(0.1, min(0.9, self.d[-1]+random.uniform(-0.3, 0.3))))
    def draw(self, s, f, a=None):
        super().draw(s, f, a); rect = self.rect.inflate(-10, -10); pts = []
        for i, v in enumerate(self.d): pts.append((rect.x + (i/4)*rect.w, rect.bottom - v*rect.h))
        pygame.draw.lines(s, C_SUCCESS, False, pts, 2)

class FactoryConveyor(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.off=0
    def update(self, dt): super().update(dt); self.off = (self.off + dt*20) % 10
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-10, -20)
        pygame.draw.rect(s, (30,30,35), r); pygame.draw.rect(s, (80,85,90), r, 1)
        for i in range(int(self.off)-10, int(r.w), 10):
            if i >= 0 and i < r.w: pygame.draw.line(s, (100,105,110), (r.x+i, r.y), (r.x+i, r.bottom), 1)

class FactoryValve(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.ang=0
    def update(self, dt): 
        super().update(dt)
        if self.hovered: self.ang += dt*5
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.35
        draw_soft_circle(s, (120, 50, 50), (cx, cy), int(r)) # Red handle
        rad = math.radians(self.ang*50)
        ex, ey = cx+math.cos(rad)*r, cy+math.sin(rad)*r
        pygame.draw.line(s, (200, 100, 100), (cx, cy), (ex, ey), 2)

class FactoryBurner(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t=0
    def update(self, dt): super().update(dt); self.t += dt*20
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.3
        cols = [(200, 50, 50), (220, 100, 50), (255, 200, 50)]
        for i in range(3):
            sz = (math.sin(self.t + i) + 2) * (r/3)
            # Additive fire
            bs = int(sz*2); flame = pygame.Surface((bs*2, bs*2), pygame.SRCALPHA)
            pygame.draw.circle(flame, (*cols[i], 100), (bs, bs), int(sz))
            s.blit(flame, (cx-bs, int(cy+r-sz)-bs), special_flags=pygame.BLEND_RGBA_ADD)

class FactoryRadar(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.ang=0
    def update(self, dt): super().update(dt); self.ang += dt*180
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.35
        pygame.draw.circle(s, (20, 40, 20), (cx, cy), int(r))
        pygame.draw.circle(s, (50, 100, 50), (cx, cy), int(r), 1)
        rad = math.radians(self.ang)
        pygame.draw.line(s, (100, 255, 100), (cx, cy), (cx+math.cos(rad)*r, cy+math.sin(rad)*r), 1)

class FactoryBattery(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.chg=0
    def update(self, dt): super().update(dt); self.chg = (self.chg + dt*0.5) % 1.0
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-20, -10)
        pygame.draw.rect(s, (50, 55, 60), r, 1)
        h = int(r.h * self.chg)
        pygame.draw.rect(s, C_SUCCESS, (r.x+2, r.bottom-h, r.w-4, h))

class FactoryServer(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t=0
    def update(self, dt): super().update(dt); self.t += dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-16, -10)
        pygame.draw.rect(s, (25, 25, 30), r)
        for i in range(3):
            col = C_SUCCESS if math.sin(self.t*5 + i*2) > 0 else (40, 40, 40)
            pygame.draw.circle(s, col, (r.right-6, r.y + 6 + i*6), 2)

class FactorySolar(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size)
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-10, -10)
        pygame.draw.rect(s, (20, 20, 60), r)
        pygame.draw.line(s, (100, 100, 150), r.topleft, r.bottomright, 1)
        pygame.draw.rect(s, (100, 100, 150), r, 1)

class FactoryTurbine(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.a=0
    def update(self, dt): super().update(dt); self.a += dt*500
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.35
        for i in range(6):
            rad = math.radians(self.a + i*60)
            pygame.draw.line(s, (180, 200, 220), (cx, cy), (cx+math.cos(rad)*r, cy+math.sin(rad)*r), 2)

class FactorySiren(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t=0
    def update(self, dt): super().update(dt); self.t += dt*10
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.3
        p = (math.sin(self.t)+1)*0.5
        col = (int(lerp(60, 200, p)), 20, 20)
        draw_soft_circle(s, col, (cx, cy), int(r))

class FactoryCrate(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size)
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-18, -18)
        pygame.draw.rect(s, (110, 85, 60), r, border_radius=1)
        pygame.draw.rect(s, (140, 110, 80), r, 2, border_radius=1)
        pygame.draw.line(s, (80, 60, 40), r.topleft, r.bottomright, 2)

class FactoryRobotArm(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.a=0
    def update(self, dt): super().update(dt); self.a += dt*2
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = self.rect.w*0.35
        elb_x = cx + math.cos(self.a)*8; elb_y = cy + math.sin(self.a)*8
        end_x = elb_x + math.cos(self.a*2.5)*8; end_y = elb_y + math.sin(self.a*2.5)*8
        pygame.draw.line(s, (120, 125, 135), (cx, cy+8), (elb_x, elb_y), 3)
        pygame.draw.line(s, C_ACCENT, (elb_x, elb_y), (end_x, end_y), 2)
        pygame.draw.circle(s, (80, 85, 90), (cx, cy+8), 3)

class FactoryHazard(JuicyButton):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h); self.scroll = 0.0
    def update(self, dt): super().update(dt); self.scroll += dt * 30
    def draw(self, s, f, a=None):
        shad = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shad, C_SHADOW, (0,0,self.rect.w,self.rect.h), border_radius=8)
        s.blit(shad, (self.rect.x, self.rect.y+4))
        surf = pygame.Surface((self.rect.w, self.rect.h))
        surf.fill(C_WARNING)
        offset = int(self.scroll) % 40
        for i in range(-50, self.rect.w + 50, 20):
            pts = [(i+offset, 0), (i+offset+10, 0), (i+offset-10, self.rect.h), (i+offset-20, self.rect.h)]
            pygame.draw.polygon(surf, (20, 20, 20), pts)
        pygame.draw.rect(surf, (255,255,255,40), (0,0,self.rect.w,self.rect.h//2))
        s.blit(surf, self.rect.topleft)
        pygame.draw.rect(s, (20,20,20), self.rect, 2)
        ts = f.render("CAUTION", True, (20,20,20))
        pill = ts.get_rect(center=self.rect.center).inflate(16, 4)
        pygame.draw.rect(s, (240,240,240), pill, border_radius=4)
        s.blit(ts, (self.rect.centerx - ts.get_width()//2, self.rect.centery - ts.get_height()//2))
import pygame
import math
import random

# --- THEME SETTINGS ---
C_BG = (18, 18, 20)
C_PANEL = (30, 30, 33)
C_BORDER = (55, 55, 60)
C_TEXT = (255, 255, 255)       
C_TEXT_IDLE = (255, 255, 255)  
C_TEXT_DIM = (220, 220, 220)   
C_SHADOW = (0, 0, 0, 80)       
C_ACCENT = (0, 122, 204)       
C_DANGER = (204, 50, 50)       
C_SUCCESS = (60, 160, 60)      
C_WARNING = (220, 160, 40)     

def lerp(start, end, t): return start + (end - start) * t

class AnimVar:
    def __init__(self, value, speed=10.0): self.value = value; self.target = value; self.speed = speed
    def update(self, dt): self.value += (self.target - self.value) * min(self.speed * dt, 1.0)
    def set(self, target): self.target = target

# --- BASE WIDGETS ---
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
            if self.hovered: self.anim_hover.set(1.0); self.anim_scale.set(1.02); 
            else: self.anim_hover.set(0.0); self.anim_scale.set(1.0)
            if self.hovered and not was and assets: assets.play_sound('hover')
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.clicked = True; self.anim_scale.value = 0.95; self.anim_click.value = 1.0
                self.ripples.append({'x': event.pos[0]-self.rect.x, 'y': event.pos[1]-self.rect.y, 'r': 5, 'a': 1.0})
                if assets: assets.play_sound('click')
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
        base, target, border = list(C_PANEL), list(C_PANEL), C_BORDER
        if self.style == "primary": base, target, border = list(C_ACCENT), [min(c+30,255) for c in C_ACCENT], C_ACCENT
        elif self.style == "danger": base, target, border = list(C_DANGER), [min(c+30,255) for c in C_DANGER], C_DANGER
        elif self.style == "success": base, target, border = list(C_SUCCESS), [min(c+30,255) for c in C_SUCCESS], C_SUCCESS
        elif (self.style=="toggle" or self.style=="normal") and self.active: target, border = list(C_ACCENT), C_ACCENT
        h_val = self.anim_hover.value
        r,g,b = lerp(base[0],target[0],h_val), lerp(base[1],target[1],h_val), lerp(base[2],target[2],h_val)
        c_val = self.anim_click.value; r,g,b = min(255,r+100*c_val), min(255,g+100*c_val), min(255,b+100*c_val)
        final_col = (int(r), int(g), int(b))
        
        s = pygame.Surface((w, h), pygame.SRCALPHA); pygame.draw.rect(s, C_SHADOW, (0,0,w,h), border_radius=8) 
        screen.blit(s, (draw_rect.x, draw_rect.y+4))
        pygame.draw.rect(screen, final_col, draw_rect, border_radius=8)
        br,bg,bb = lerp(C_BORDER[0],border[0],h_val), lerp(C_BORDER[1],border[1],h_val), lerp(C_BORDER[2],border[2],h_val)
        pygame.draw.rect(screen, (br,bg,bb), draw_rect, 1, border_radius=8)
        
        if self.icon_name and assets:
            icon = assets.get_icon(self.icon_name)
            if icon: screen.blit(icon, (draw_rect.centerx - icon.get_width()//2, draw_rect.centery - icon.get_height()//2))
        elif self.text:
            col = C_TEXT if (self.hovered or self.active or self.style != "normal") else C_TEXT_IDLE
            if self.disabled: col = C_TEXT_DIM
            if self.style!="normal" or self.active:
                ts_shadow = font.render(self.text, True, (0,0,0))
                screen.blit(ts_shadow, (draw_rect.centerx-ts_shadow.get_width()//2+1, draw_rect.centery-ts_shadow.get_height()//2+1))
            ts = font.render(self.text, True, col)
            screen.blit(ts, (draw_rect.centerx-ts.get_width()//2, draw_rect.centery-ts.get_height()//2))

class Checkbox:
    def __init__(self, x, y, size, label="", checked=False):
        self.rect = pygame.Rect(x, y, size, size); self.label = label; self.checked = checked; self.hovered = False; self.anim_fill = AnimVar(1.0 if checked else 0.0)
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEMOTION: self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1: self.checked = not self.checked; assets and assets.play_sound('click')
    def update(self, dt): self.anim_fill.set(1.0 if self.checked else 0.0); self.anim_fill.update(dt)
    def draw(self, screen, font):
        border = C_ACCENT if (self.hovered or self.checked) else C_BORDER
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=4); pygame.draw.rect(screen, border, self.rect, 1, border_radius=4)
        sz = self.anim_fill.value * (self.rect.width - 6)
        if sz > 1:
            cr = pygame.Rect(0,0,sz,sz); cr.center = self.rect.center; pygame.draw.rect(screen, C_ACCENT, cr, border_radius=2)
        if self.label: ts = font.render(self.label, True, C_TEXT_IDLE); screen.blit(ts, (self.rect.right+10, self.rect.centery-ts.get_height()//2))

class Slider:
    def __init__(self, x, y, w, val=0.5): self.rect = pygame.Rect(x, y, w, 20); self.val = val; self.dragging = False; self.hovered = False
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos); 
            if self.dragging: self.val = max(0, min((event.pos[0]-self.rect.x)/self.rect.width, 1.0))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered: self.dragging = True; self.val = max(0, min((event.pos[0]-self.rect.x)/self.rect.width, 1.0))
        elif event.type == pygame.MOUSEBUTTONUP: self.dragging = False
    def update(self, dt): pass
    def draw(self, screen, font):
        pygame.draw.rect(screen, C_PANEL, (self.rect.x, self.rect.centery-3, self.rect.width, 6), border_radius=3)
        pygame.draw.rect(screen, C_ACCENT, (self.rect.x, self.rect.centery-3, self.rect.width*self.val, 6), border_radius=3)
        col = C_TEXT if (self.dragging or self.hovered) else C_TEXT_IDLE
        pygame.draw.circle(screen, col, (int(self.rect.x+self.rect.width*self.val), self.rect.centery), 8)

class Knob:
    def __init__(self, x, y, r, val=0.0):
        self.rect = pygame.Rect(x-r, y-r, r*2, r*2); self.r = r; self.val = val; self.dragging = False; self.sy=0; self.sv=0
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos): self.dragging = True; self.sy = event.pos[1]; self.sv = self.val
        elif event.type == pygame.MOUSEBUTTONUP: self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging: self.val = max(0.0, min(1.0, self.sv + (self.sy - event.pos[1]) * 0.01))
    def update(self, dt): pass
    def draw(self, screen, font):
        cx, cy = self.rect.center
        pygame.draw.circle(screen, C_PANEL, (cx, cy), self.r); pygame.draw.circle(screen, C_BORDER, (cx, cy), self.r, 2)
        end = math.radians(225 - (270 * self.val))
        dx, dy = cx + math.cos(end)*(self.r*0.7), cy - math.sin(end)*(self.r*0.7)
        pygame.draw.line(screen, C_ACCENT if self.dragging else C_TEXT_IDLE, (cx, cy), (dx, dy), 3); pygame.draw.circle(screen, C_TEXT, (int(dx), int(dy)), 4)

class TextInput:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h); self.text = ""; self.placeholder = placeholder; self.focused = False; self.t = 0.0
    def handle_event(self, event, assets):
        if event.type == pygame.MOUSEBUTTONDOWN: self.focused = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN: self.focused = False
            else: self.text += event.unicode
    def update(self, dt): self.t += dt
    def draw(self, screen, font):
        border = C_ACCENT if self.focused else C_BORDER
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=4); pygame.draw.rect(screen, border, self.rect, 1, border_radius=4)
        txt_col = C_TEXT if self.text else C_TEXT_DIM
        ts = font.render(self.text if self.text else self.placeholder, True, txt_col)
        screen.blit(ts, (self.rect.x+8, self.rect.centery-ts.get_height()//2))
        if self.focused and (int(self.t*2)%2==0):
            cx = self.rect.x + 8 + font.size(self.text)[0]
            pygame.draw.line(screen, C_ACCENT, (cx, self.rect.y+8), (cx, self.rect.bottom-8), 2)

class ProgressBar:
    def __init__(self, x, y, w, h, val=0.0): self.rect = pygame.Rect(x, y, w, h); self.val = val
    def update(self, dt): self.val = (self.val + dt * 0.2) % 1.0
    def draw(self, screen, font):
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=4)
        fw = int(self.rect.width * self.val)
        if fw > 0:
            pygame.draw.rect(screen, C_ACCENT, (self.rect.x, self.rect.y, fw, self.rect.height), border_radius=4)
            for i in range(0, fw, 10): pygame.draw.line(screen, (255,255,255,50), (self.rect.x+i, self.rect.y), (self.rect.x+i-5, self.rect.bottom), 2)

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
        border = C_ACCENT if (self.is_open or self.hovered) else C_BORDER
        pygame.draw.rect(screen, C_PANEL, self.rect, border_radius=6); pygame.draw.rect(screen, border, self.rect, 1, border_radius=6)
        ts = font.render(self.options[self.selected_index] if self.options else "", True, C_TEXT_IDLE)
        screen.blit(ts, (self.rect.x+10, self.rect.centery-ts.get_height()//2))
    def draw_overlay(self, screen, font):
        if self.anim_open.value < 0.01: return
        th = len(self.options)*30; ch = th * self.anim_open.value
        fs = pygame.Surface((self.rect.width, th), pygame.SRCALPHA)
        fs.fill((*C_BG, 255)); pygame.draw.rect(fs, (40,40,45), (0,0,self.rect.width,th)); pygame.draw.rect(fs, C_BORDER, (0,0,self.rect.width,th), 1)
        for i, opt in enumerate(self.options):
            iy = i * 30
            if i == self.hover_index: pygame.draw.rect(fs, (60,60,65), (0,iy,self.rect.width,30))
            if i == self.selected_index: pygame.draw.rect(fs, C_ACCENT, (0,iy,4,30))
            col = C_TEXT if i == self.selected_index else C_TEXT_IDLE
            t_surf = font.render(opt, True, col)
            full_surf.blit(t_surf, (15, iy + 8))
        screen.blit(fs, (self.rect.x, self.rect.bottom+5), area=(0,0,self.rect.width, int(ch)))

class Panel:
    def __init__(self, x, y, w, h, title=""): self.rect = pygame.Rect(x, y, w, h); self.title = title

class FactoryHazard(JuicyButton):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h); self.scroll = 0.0
    def update(self, dt): super().update(dt); self.scroll += dt * 30
    def draw(self, screen, font, assets=None):
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, C_SHADOW, (0,0,self.rect.width,self.rect.height), border_radius=8) 
        screen.blit(s, (self.rect.x, self.rect.y+4))
        surf = pygame.Surface((self.rect.width, self.rect.height))
        surf.fill((255, 200, 0)) 
        offset = int(self.scroll) % 40
        for i in range(-50, self.rect.width + 50, 20):
            pts = [(i+offset, 0), (i+offset+10, 0), (i+offset-10, self.rect.height), (i+offset-20, self.rect.height)]
            pygame.draw.polygon(surf, (20, 20, 20), pts)
        if self.hovered:
            s_high = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s_high, (255, 255, 255, 50), (0,0,self.rect.width,self.rect.height))
            surf.blit(s_high, (0,0))
        screen.blit(surf, self.rect.topleft)
        pygame.draw.rect(screen, (0,0,0), self.rect, 2)
        ts = font.render("CAUTION", True, (0,0,0))
        pill = ts.get_rect(center=self.rect.center).inflate(10, 4)
        pygame.draw.rect(screen, (255,255,255), pill, border_radius=4)
        screen.blit(ts, (self.rect.centerx - ts.get_width()//2, self.rect.centery - ts.get_height()//2))

# --- NEW FACTORY WIDGETS ---

class FactoryGear(JuicyButton):
    def __init__(self, x, y, size, speed=30): super().__init__(x, y, size, size); self.angle=0; self.base=speed
    def update(self, dt): super().update(dt); self.angle += (self.base*10 if self.hovered else self.base)*dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        for i in range(8):
            rad = math.radians(self.angle + i*45)
            pygame.draw.circle(s, (200,200,210), (cx+math.cos(rad)*(r+4), cy+math.sin(rad)*(r+4)), 3)
        pygame.draw.circle(s, (150,150,160), (cx, cy), int(r)); pygame.draw.circle(s, C_PANEL, (cx, cy), int(r/2))

class FactoryTank(JuicyButton):
    def __init__(self, x, y, size, fluid_col=C_ACCENT): super().__init__(x, y, size, size); self.lvl=0; self.fill=True; self.col=fluid_col
    def update(self, dt): 
        super().update(dt); self.lvl += (dt*0.5 if self.fill else -dt*0.5)
        if self.lvl>=1 or self.lvl<=0: self.fill = not self.fill
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        pygame.draw.circle(s, (40,40,45), (cx, cy), int(r))
        lh = int(r*2*self.lvl)
        if lh > 0:
            ls = pygame.Surface((int(r*2), int(r*2)), pygame.SRCALPHA); pygame.draw.circle(ls, (255,255,255), (int(r),int(r)), int(r))
            pygame.draw.rect(ls, self.col, (0, int(r*2)-lh, int(r*2), lh))
            s.blit(ls, (cx-r, cy-r), special_flags=pygame.BLEND_RGBA_MIN)
        pygame.draw.circle(s, (200,200,200), (cx, cy), int(r), 1)

class FactoryFan(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.a = 0
    def update(self, dt): super().update(dt); self.a += (800 if self.hovered else 200)*dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        pygame.draw.circle(s, (30,30,30), (cx, cy), int(r)); pygame.draw.circle(s, C_BORDER, (cx, cy), int(r), 1)
        for i in range(3):
            rad = math.radians(self.a + i*120)
            pygame.draw.line(s, C_TEXT, (cx, cy), (cx+math.cos(rad)*r, cy+math.sin(rad)*r), 3)

class FactoryPower(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t = random.uniform(0, 10)
    def update(self, dt): super().update(dt); self.t += dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.3
        p = (math.sin(self.t*4)+1)*0.5; col = (int(lerp(80,0,p)), int(lerp(80,255,p)), int(lerp(80,255,p)))
        pygame.draw.arc(s, col, (cx-r, cy-r, r*2, r*2), math.radians(120), math.radians(60), 2)
        pygame.draw.line(s, col, (cx, cy-r), (cx, cy), 2)

class FactoryGauge(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.v=0.5; self.nt=random.uniform(0,100)
    def update(self, dt): super().update(dt); self.nt+=dt; self.v=0.5+math.sin(self.nt)*0.4
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        pygame.draw.circle(s, (20,20,20), (cx, cy), int(r)); rect=(cx-r, cy-r, r*2, r*2)
        pygame.draw.arc(s, C_SUCCESS, rect, math.radians(180), math.radians(300), 2)
        pygame.draw.arc(s, C_DANGER, rect, math.radians(300), math.radians(360), 2)
        rad = math.radians(180 + self.v*180); pygame.draw.line(s, (255,50,50), (cx, cy), (cx+math.cos(rad)*r, cy-math.sin(rad)*r), 2)

class FactoryLight(JuicyButton):
    def __init__(self, x, y, size, color=C_SUCCESS): super().__init__(x, y, size, size); self.col=color; self.t=0
    def update(self, dt): super().update(dt); self.t += dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.3
        on = math.sin(self.t*4) > 0; col = self.col if on else (50,50,50)
        pygame.draw.circle(s, col, (cx, cy), int(r))

class FactoryPiston(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.ph = random.uniform(0, 10)
    def update(self, dt): super().update(dt); self.ph += dt*5
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; ho = math.sin(self.ph)*5
        pygame.draw.rect(s, (100,100,100), (cx-3, cy-8, 6, 16)); pygame.draw.rect(s, (200,200,200), (cx-6, cy+ho-3, 12, 6))

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
        pygame.draw.rect(s, (30,30,30), r); pygame.draw.rect(s, (80,80,80), r, 1)
        for i in range(int(self.off)-10, int(r.w), 10):
            if i >= 0 and i < r.w: pygame.draw.line(s, (100,100,100), (r.x+i, r.y), (r.x+i, r.bottom), 2)

class FactoryValve(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.ang=0
    def update(self, dt): 
        super().update(dt)
        if self.hovered: self.ang += dt*5
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        pygame.draw.circle(s, (100,100,100), (cx, cy), int(r), 2); pygame.draw.line(s, (100,100,100), (cx-r, cy), (cx+r, cy), 2)
        pygame.draw.line(s, (100,100,100), (cx, cy-r), (cx, cy+r), 2); rad = math.radians(self.ang*50)
        pygame.draw.line(s, C_DANGER, (cx, cy), (cx+math.cos(rad)*r, cy+math.sin(rad)*r), 3)

class FactoryBurner(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t=0
    def update(self, dt): super().update(dt); self.t += dt*20
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.3
        cols = [(255, 0, 0), (255, 100, 0), (255, 200, 0)]
        for i in range(3):
            sz = (math.sin(self.t + i) + 2) * (r/3)
            pygame.draw.circle(s, cols[i], (cx, int(cy+r-sz)), int(sz))

class FactoryRadar(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.ang=0
    def update(self, dt): super().update(dt); self.ang += dt*200
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        pygame.draw.circle(s, (0, 50, 0), (cx, cy), int(r)); pygame.draw.circle(s, (0, 150, 0), (cx, cy), int(r), 1)
        rad = math.radians(self.ang); ex, ey = cx+math.cos(rad)*r, cy+math.sin(rad)*r
        pygame.draw.line(s, (0, 255, 0), (cx, cy), (ex, ey), 1)

class FactoryChip(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size)
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-16, -16)
        pygame.draw.rect(s, (20, 20, 20), r); pygame.draw.rect(s, (150, 150, 0), r, 1)
        for i in range(4): pygame.draw.line(s, (100, 100, 0), (r.x, r.y+i*4+4), (r.right, r.y+i*4+4), 1)

class FactoryBattery(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.chg=0
    def update(self, dt): super().update(dt); self.chg = (self.chg + dt*0.5) % 1.0
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-20, -10)
        pygame.draw.rect(s, (50, 50, 50), r, 1)
        h = int(r.h * self.chg)
        pygame.draw.rect(s, C_SUCCESS, (r.x+2, r.bottom-h, r.w-4, h))

class FactoryServer(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t=0
    def update(self, dt): super().update(dt); self.t += dt
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-16, -10)
        pygame.draw.rect(s, (20, 20, 25), r)
        for i in range(3):
            col = C_SUCCESS if math.sin(self.t*5 + i*2) > 0 else (50, 50, 50)
            pygame.draw.circle(s, col, (r.right-6, r.y + 6 + i*6), 2)

class FactorySolar(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size)
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-10, -10)
        pygame.draw.rect(s, (20, 20, 80), r)
        pygame.draw.line(s, (100, 100, 150), r.topleft, r.bottomright, 1)
        pygame.draw.rect(s, (100, 100, 150), r, 1)

class FactoryTurbine(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.a=0
    def update(self, dt): super().update(dt); self.a += dt*500
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        for i in range(6):
            rad = math.radians(self.a + i*60)
            pygame.draw.line(s, (200, 200, 255), (cx, cy), (cx+math.cos(rad)*r, cy+math.sin(rad)*r), 2)

class FactorySiren(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.t=0
    def update(self, dt): super().update(dt); self.t += dt*10
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.3
        col = (255, 0, 0) if math.sin(self.t)>0 else (50, 0, 0)
        pygame.draw.circle(s, col, (cx, cy), int(r))

class FactoryCrate(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size)
    def draw(self, s, f, a=None):
        super().draw(s, f, a); r = self.rect.inflate(-16, -16)
        pygame.draw.rect(s, (100, 70, 20), r); pygame.draw.rect(s, (150, 100, 30), r, 1)
        pygame.draw.line(s, (80, 50, 10), r.topleft, r.bottomright, 2)
        pygame.draw.line(s, (80, 50, 10), r.topright, r.bottomleft, 2)

class FactoryRobotArm(JuicyButton):
    def __init__(self, x, y, size): super().__init__(x, y, size, size); self.a=0
    def update(self, dt): super().update(dt); self.a += dt*2
    def draw(self, s, f, a=None):
        super().draw(s, f, a); cx, cy = self.rect.center; r = min(self.rect.w, self.rect.h)*0.35
        elb_x = cx + math.cos(self.a)*10; elb_y = cy + math.sin(self.a)*10
        end_x = elb_x + math.cos(self.a*2)*10; end_y = elb_y + math.sin(self.a*2)*10
        pygame.draw.line(s, (200, 200, 200), (cx, cy+10), (elb_x, elb_y), 3)
        pygame.draw.line(s, C_ACCENT, (elb_x, elb_y), (end_x, end_y), 2)
        pygame.draw.circle(s, (150, 150, 150), (cx, cy+10), 3)
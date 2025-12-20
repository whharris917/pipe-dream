import pygame
from folly_assets import AssetManager

# Colors
C_BG = (30, 30, 30)
C_PANEL = (45, 45, 48)
C_ACCENT = (0, 122, 204)
C_HOVER = (60, 60, 65)
C_BORDER = (80, 80, 80)
C_TEXT = (220, 220, 220)

class JuicyButton:
    def __init__(self, x, y, w, h, text="", icon_name=None, sound_name=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.icon_name = icon_name
        self.sound_name = sound_name # <--- NEW: Custom sound override
        
        self.active = False
        self.hovered = False
        self.clicked = False
        
        # Animation State
        self.current_color = list(C_PANEL)
        self.target_color = C_PANEL
        self.cached_surf = None
    
    def update(self):
        speed = 0.2
        for i in range(3):
            self.current_color[i] += (self.target_color[i] - self.current_color[i]) * speed

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.hovered
            self.hovered = self.rect.collidepoint(event.pos)
            
            if self.hovered and not was_hovered:
                # Use custom sound if provided, otherwise default 'hover'
                snd = self.sound_name if self.sound_name else 'hover'
                AssetManager.get().play_sound(snd)
            
            if self.active: self.target_color = C_ACCENT
            elif self.hovered: self.target_color = C_HOVER
            else: self.target_color = C_PANEL
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                AssetManager.get().play_sound('click')
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.clicked and self.rect.collidepoint(event.pos):
                self.active = not self.active 
                if self.active: self.target_color = C_ACCENT
                elif self.hovered: self.target_color = C_HOVER
                else: self.target_color = C_PANEL
            self.clicked = False

    def draw(self, screen, font=None):
        # Draw Body
        col = (int(self.current_color[0]), int(self.current_color[1]), int(self.current_color[2]))
        pygame.draw.rect(screen, col, self.rect, border_radius=6)
        
        border_col = (200, 200, 200) if self.active else C_BORDER
        pygame.draw.rect(screen, border_col, self.rect, 1, border_radius=6)
        
        # Draw Icon
        if self.icon_name:
            icon = AssetManager.get().get_icon(self.icon_name)
            if icon:
                ix = self.rect.centerx - icon.get_width() // 2
                iy = self.rect.centery - icon.get_height() // 2
                screen.blit(icon, (ix, iy))
        # Draw Text
        elif self.text and font:
            if self.cached_surf is None:
                self.cached_surf = font.render(self.text, True, C_TEXT)
            
            # Center text
            tx = self.rect.centerx - self.cached_surf.get_width() // 2
            ty = self.rect.centery - self.cached_surf.get_height() // 2
            screen.blit(self.cached_surf, (tx, ty))
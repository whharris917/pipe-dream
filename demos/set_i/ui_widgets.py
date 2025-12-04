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
        
        # Caching text to speed up rendering
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
        # Draw Track
        pygame.draw.rect(screen, (60, 60, 70), self.rect, border_radius=4)
        
        # Draw Handle
        if self.max_val == self.min_val: 
            pct = 0.0
        else: 
            pct = (float(self.val) - float(self.min_val)) / (float(self.max_val) - float(self.min_val))
        
        handle_x = self.rect.x + pct * self.rect.width - self.handle_w / 2
        handle_rect = pygame.Rect(int(handle_x), int(self.rect.y - 4), int(self.handle_w), int(self.rect.height + 8))
        pygame.draw.rect(screen, (180, 180, 200), handle_rect, border_radius=2)
        
        # Optimization: Only render text if value changed significantly or not cached
        # For floats, we check if the string representation changes
        if self.label == "Steps/Frame (M)":
            val_str = f"{int(self.val)}"
        else:
            val_str = f"{self.val:.2f}"
            
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
        
        # Cache text
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
        # Border
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1, border_radius=5)
        
        if self.cached_surf is None:
            self.cached_surf = font.render(self.text, True, (255, 255, 255))
            
        txt_rect = self.cached_surf.get_rect(center=self.rect.center)
        screen.blit(self.cached_surf, txt_rect)

class AtomPalette:
    def __init__(self, x, y, w, atom_types):
        self.x = x
        self.y = y
        self.w = w
        self.atom_types = atom_types
        self.selected_type = 0
        self.buttons = []
        self.title_surf = None
        
        # Create a button for each type
        btn_h = 30
        gap = 5
        cur_y = y + 25 # Space for title
        
        for tid, props in atom_types.items():
            # Use specific colors for palette buttons
            c_rgb = props["color"]
            # Dim version for inactive
            c_dim = (max(20, c_rgb[0]//3), max(20, c_rgb[1]//3), max(20, c_rgb[2]//3))
            
            btn = Button(x, cur_y, w, btn_h, props["name"], active=(tid==0), toggle=False, 
                         color_active=c_rgb, color_inactive=c_dim)
            self.buttons.append((tid, btn))
            cur_y += btn_h + gap
            
    def handle_event(self, event):
        for tid, btn in self.buttons:
            if btn.handle_event(event):
                self.selected_type = tid
                # Reset others
                for oid, obtn in self.buttons:
                    obtn.active = (oid == tid)
                    
    def draw(self, screen, font):
        if self.title_surf is None:
            self.title_surf = font.render("Atom Brush", True, (220, 220, 220))
        screen.blit(self.title_surf, (self.x, self.y))
        
        for _, btn in self.buttons:
            btn.draw(screen, font)
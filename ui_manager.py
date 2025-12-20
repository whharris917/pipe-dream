import pygame
import config
from session import InteractionState
from ui_widgets import Button, SmartSlider, InputField

class UIManager:
    def __init__(self, layout, input_world, mode=config.MODE_SIM):
        self.buttons = {}
        self.sliders = {}
        self.inputs = []
        self.layout = layout
        self.menu = TopMenu(layout['W'])
        self.mode = mode
        
        self._init_ui(input_world)

    def _init_ui(self, input_world):
        self.inputs.append(input_world)
        
        y_off = config.TOP_MENU_H + 20
        lx = self.layout['LEFT_X'] + 10
        rx = self.layout['RIGHT_X'] + 10
        
        # Left Panel (Tools)
        self.buttons['select'] = Button(lx, y_off, 120, 30, "Select (S)", toggle=True, group='tools')
        y_off += 40
        self.buttons['brush'] = Button(lx, y_off, 120, 30, "Brush (B)", toggle=True, group='tools')
        y_off += 40
        
        # FIXED: SmartSlider does not take a height argument (removed '20')
        self.sliders['brush_size'] = SmartSlider(lx, y_off, 120, 0.5, 5.0, 2.0, "Size")
        y_off += 40
        
        self.buttons['line'] = Button(lx, y_off, 55, 30, "Line", toggle=True, group='tools')
        self.buttons['rect'] = Button(lx + 65, y_off, 55, 30, "Rect", toggle=True, group='tools')
        y_off += 35
        self.buttons['circ'] = Button(lx, y_off, 55, 30, "Circ", toggle=True, group='tools')
        self.buttons['point'] = Button(lx + 65, y_off, 55, 30, "Point", toggle=True, group='tools')
        y_off += 35
        self.buttons['ref'] = Button(lx, y_off, 120, 30, "Ref Line", toggle=True, group='tools')
        y_off += 40
        
        # Constraints
        self.buttons['c_coincident'] = Button(lx, y_off, 35, 30, "Coin", toggle=True, group='const')
        self.buttons['c_parallel'] = Button(lx+40, y_off, 35, 30, "Para", toggle=True, group='const')
        self.buttons['c_perp'] = Button(lx+80, y_off, 35, 30, "Perp", toggle=True, group='const')
        y_off += 35
        self.buttons['c_horiz'] = Button(lx, y_off, 35, 30, "Horz", toggle=True, group='const')
        self.buttons['c_vert'] = Button(lx+40, y_off, 35, 30, "Vert", toggle=True, group='const')
        self.buttons['c_fix'] = Button(lx+80, y_off, 35, 30, "Fix", toggle=True, group='const')
        y_off += 35
        self.buttons['c_dist'] = Button(lx, y_off, 55, 30, "Dist", toggle=True, group='const')
        self.buttons['c_equal'] = Button(lx+65, y_off, 55, 30, "Equal", toggle=True, group='const')

        # Right Panel (Sim Controls)
        y_r = config.TOP_MENU_H + 20
        self.buttons['play'] = Button(rx, y_r, 120, 30, "Play/Pause", toggle=True)
        y_r += 40
        # FIXED: Removed height argument '20' from all SmartSliders
        self.sliders['speed'] = SmartSlider(rx, y_r, 120, 1, 20, 5, "Speed")
        y_r += 40
        self.sliders['gravity'] = SmartSlider(rx, y_r, 120, 0, 200, 98, "Gravity")
        y_r += 40
        self.sliders['temp'] = SmartSlider(rx, y_r, 120, 0.1, 5.0, 0.5, "Temp")
        y_r += 30
        self.buttons['thermostat'] = Button(rx, y_r, 120, 25, "Thermostat", toggle=True)
        y_r += 40
        self.sliders['damping'] = SmartSlider(rx, y_r, 120, 0.90, 1.0, 0.99, "Damping")
        y_r += 40
        self.sliders['dt'] = SmartSlider(rx, y_r, 120, 0.001, 0.01, 0.005, "dt")
        y_r += 40
        self.sliders['sigma'] = SmartSlider(rx, y_r, 120, 0.5, 2.0, 1.0, "Sigma")
        y_r += 40
        self.sliders['epsilon'] = SmartSlider(rx, y_r, 120, 0.1, 5.0, 1.0, "Epsilon")
        y_r += 40
        self.sliders['skin'] = SmartSlider(rx, y_r, 120, 0.1, 1.0, 0.3, "Skin")
        y_r += 40
        self.buttons['boundaries'] = Button(rx, y_r, 120, 25, "Boundaries", toggle=True)
        y_r += 40
        
        # Editor specific
        self.buttons['mode_ghost'] = Button(rx, y_r, 120, 25, "Ghost Mode", toggle=True)
        y_r += 30
        self.buttons['editor_play'] = Button(rx, y_r, 120, 25, "Simulate")
        y_r += 30
        self.buttons['show_const'] = Button(rx, y_r, 120, 25, "Hide Cnstr")

    def handle_event(self, event, app):
        res = self.menu.handle_event(event)
        if res: app._execute_menu(res); return True
        
        mx, my = pygame.mouse.get_pos()
        
        # Check against SESSION state
        if app.session.state == InteractionState.PAINTING: return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Check Buttons
                for name, btn in self.buttons.items():
                    if btn.is_hovered(mx, my):
                        if name == 'play':
                            btn.active = not btn.active
                            app.sim.paused = not btn.active
                        elif name == 'boundaries':
                            btn.active = not btn.active
                        elif name == 'thermostat':
                            btn.active = not btn.active
                        elif name == 'mode_ghost':
                            btn.active = not btn.active
                        elif name == 'editor_play':
                            app.toggle_editor_play()
                        elif name == 'show_const':
                            app.toggle_show_constraints()
                        elif btn.group == 'tools':
                            app.change_tool(app.input_handler.tool_btn_map[btn])
                        elif btn.group == 'const':
                             ctype = app.input_handler.constraint_btn_map[btn]
                             app.trigger_constraint(ctype)
                        return True
                
                # Check Sliders
                for s in self.sliders.values():
                    if s.handle_event(event): return True
                    
                # Check Inputs
                for inp in self.inputs:
                    if inp.handle_event(event):
                         if inp == app.session.input_world:
                             try:
                                 val = float(inp.text)
                                 app.sim.resize_world(val)
                             except: pass
                         return True
                         
        elif event.type == pygame.MOUSEBUTTONUP:
            for s in self.sliders.values(): s.handle_event(event)

        elif event.type == pygame.MOUSEMOTION:
            for s in self.sliders.values(): 
                if s.handle_event(event): return True
        
        return False

    def draw(self, screen, font, mode):
        self.menu.draw(screen, font)
        
        for name, btn in self.buttons.items():
            if mode == config.MODE_SIM:
                if name in ['mode_ghost', 'editor_play', 'show_const']: continue
            else:
                if name in ['play', 'thermostat']: continue
                
            btn.draw(screen, font)
            
        for name, s in self.sliders.items():
            s.draw(screen, font)
            
        for inp in self.inputs:
            inp.draw(screen, font)

class TopMenu:
    def __init__(self, w):
        self.rect = pygame.Rect(0, 0, w, config.TOP_MENU_H)
        self.items = ["New", "New Simulation", "New Model", "Save", "Save As...", "Open...", "Import Geometry"]
        self.item_rects = []
        x = 10
        for item in self.items:
            w = len(item) * 8 + 10
            self.item_rects.append((item, pygame.Rect(x, 2, w, 26)))
            x += w + 5
            
    def resize(self, w):
        self.rect.width = w

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                for item, r in self.item_rects:
                    if r.collidepoint(mx, my): return item
        return None

    def draw(self, screen, font):
        pygame.draw.rect(screen, (40, 40, 40), self.rect)
        pygame.draw.line(screen, (60, 60, 60), (0, 30), (self.rect.width, 30))
        
        mx, my = pygame.mouse.get_pos()
        for item, r in self.item_rects:
            col = (200, 200, 200)
            if r.collidepoint(mx, my):
                pygame.draw.rect(screen, (60, 60, 80), r, border_radius=4)
                col = (255, 255, 255)
            screen.blit(font.render(item, True, col), (r.x + 5, r.y + 4))
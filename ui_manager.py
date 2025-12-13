import config
from ui_widgets import SmartSlider, Button, InputField, MenuBar
from tools import SelectTool, BrushTool, LineTool, RectTool, CircleTool, PointTool

class UIManager:
    """Helper to organize UI elements"""
    def __init__(self, layout, app_input_world=None):
        self.sliders = {}
        self.buttons = {}
        self.tools = {}
        self.inputs = {}
        self.menu = MenuBar(layout['W'], config.TOP_MENU_H)
        self.menu.items["File"] = ["New", "Open...", "Save", "Save As...", "---", "Import Geometry"] 
        
        self._init_elements(layout)
        # Store or create the input field if not provided (legacy support)
        if app_input_world:
            self.inputs['world'] = app_input_world
        else:
            rp_x = layout['RIGHT_X'] + 15
            rp_y_for_input = config.TOP_MENU_H + 120 + 480 + 160 + 60
            self.inputs['world'] = InputField(rp_x + 80, rp_y_for_input, 60, 25, str(config.DEFAULT_WORLD_SIZE))

    def _init_elements(self, layout):
        # --- Mode Tabs (Top Center) ---
        tab_w = 200 # Made wider for tab feel
        tab_h = 28  # Slightly taller
        tab_y = 1   # Almost flush with top
        center_x = layout['W'] // 2
        tab_inactive_col = (45, 45, 48)
        
        self.buttons['tab_sim'] = Button(center_x - tab_w, tab_y, tab_w, tab_h, "Simulation", toggle=False, active=True, color_inactive=tab_inactive_col)
        self.buttons['tab_edit'] = Button(center_x, tab_y, tab_w, tab_h, "Geometry Editor", toggle=False, active=False, color_inactive=tab_inactive_col)

        # Left Panel Buttons
        lp_y = config.TOP_MENU_H + 20; lp_m = 10
        self.buttons['play'] = Button(layout['LEFT_X'] + lp_m, lp_y, layout['LEFT_W']-20, 35, "Play/Pause", active=False, color_active=(60, 120, 60), color_inactive=(180, 60, 60)); lp_y += 50
        self.buttons['clear'] = Button(layout['LEFT_X'] + lp_m, lp_y, layout['LEFT_W']-20, 35, "Clear", active=False, toggle=False, color_inactive=(80, 80, 80)); lp_y += 50
        self.buttons['reset'] = Button(layout['LEFT_X'] + lp_m, lp_y, layout['LEFT_W']-20, 35, "Reset", active=False, toggle=False, color_inactive=(80, 80, 80)); lp_y += 50
        self.buttons['undo'] = Button(layout['LEFT_X'] + lp_m, lp_y, layout['LEFT_W']-20, 35, "Undo", active=False, toggle=False); lp_y += 45
        self.buttons['redo'] = Button(layout['LEFT_X'] + lp_m, lp_y, layout['LEFT_W']-20, 35, "Redo", active=False, toggle=False)

        # Right Panel Sliders
        rp_x = layout['RIGHT_X'] + 15; rp_w = layout['RIGHT_W'] - 30; rp_y = config.TOP_MENU_H + 120
        self.sliders['gravity'] = SmartSlider(rp_x, rp_y, rp_w, 0.0, 50.0, config.DEFAULT_GRAVITY, "Gravity", hard_min=0.0)
        self.sliders['temp'] = SmartSlider(rp_x, rp_y+60, rp_w, 0.0, 5.0, 0.5, "Temperature", hard_min=0.0)
        self.sliders['damping'] = SmartSlider(rp_x, rp_y+120, rp_w, 0.90, 1.0, config.DEFAULT_DAMPING, "Damping", hard_min=0.0, hard_max=1.0)
        self.sliders['dt'] = SmartSlider(rp_x, rp_y+180, rp_w, 0.0001, 0.01, config.DEFAULT_DT, "Time Step (dt)", hard_min=0.00001)
        self.sliders['sigma'] = SmartSlider(rp_x, rp_y+240, rp_w, 0.5, 2.0, config.ATOM_SIGMA, "Sigma (Size)", hard_min=0.1)
        self.sliders['epsilon'] = SmartSlider(rp_x, rp_y+300, rp_w, 0.1, 5.0, config.ATOM_EPSILON, "Epsilon (Strength)", hard_min=0.0)
        self.sliders['speed'] = SmartSlider(rp_x, rp_y+360, rp_w, 1.0, 100.0, float(config.DEFAULT_DRAW_M), "Speed (Steps/Frame)", hard_min=1.0)
        self.sliders['skin'] = SmartSlider(rp_x, rp_y+420, rp_w, 0.1, 2.0, config.DEFAULT_SKIN_DISTANCE, "Skin Distance", hard_min=0.05)
        rp_y += 480
        
        btn_half = (rp_w - 10) // 2
        self.buttons['thermostat'] = Button(rp_x, rp_y, btn_half, 30, "Thermostat", active=False)
        self.buttons['boundaries'] = Button(rp_x + btn_half + 10, rp_y, btn_half, 30, "Bounds", active=False); rp_y += 40
        
        # Tools
        self.tools['brush'] = Button(rp_x, rp_y, btn_half, 30, "Brush", active=True, toggle=False)
        self.tools['select'] = Button(rp_x + btn_half + 10, rp_y, btn_half, 30, "Select", active=False, toggle=False)
        self.tools['line'] = Button(rp_x, rp_y+40, btn_half, 30, "Line", active=False, toggle=False)
        self.tools['rect'] = Button(rp_x + btn_half + 10, rp_y+40, btn_half, 30, "Rectangle", active=False, toggle=False)
        self.tools['circle'] = Button(rp_x, rp_y+80, btn_half, 30, "Circle", active=False, toggle=False)
        self.tools['point'] = Button(rp_x + btn_half + 10, rp_y+80, btn_half, 30, "Point", active=False, toggle=False)
        self.tools['ref'] = Button(rp_x, rp_y+120, btn_half, 30, "Ref Line", active=False, toggle=False)
        rp_y += 160
        
        self.sliders['brush_size'] = SmartSlider(rp_x, rp_y, rp_w, 1.0, 10.0, 2.0, "Brush Radius", hard_min=0.5); rp_y+=60
        # self.inputs['world'] created in __init__ or passed in
        self.buttons['resize'] = Button(rp_x + 150, rp_y, rp_w - 150, 25, "Resize & Restart", active=False, toggle=False)

        # Editor Buttons
        ae_y = config.TOP_MENU_H + 40
        self.buttons['save_geo'] = Button(rp_x, ae_y, rp_w, 40, "Save Geometry", active=False, toggle=False, color_inactive=(50, 120, 50)); ae_y+=50
        self.buttons['discard_geo'] = Button(rp_x, ae_y, rp_w, 40, "Discard & Exit", active=False, toggle=False, color_inactive=(150, 50, 50)); ae_y+=50
        
        self.buttons['editor_play'] = Button(rp_x, ae_y, btn_half, 35, "Pause", active=False, toggle=False); 
        self.buttons['show_const'] = Button(rp_x + btn_half + 10, ae_y, btn_half, 35, "Hide Cnstr", active=False, toggle=False); ae_y+=45

        # Constraints
        self.buttons['const_coincident'] = Button(rp_x, ae_y, rp_w, 30, "Coincident (Pt-Pt/Ln/Circ)", toggle=False)
        self.buttons['const_collinear'] = Button(rp_x, ae_y+35, rp_w, 30, "Collinear (Pt-Ln)", toggle=False)
        self.buttons['const_midpoint'] = Button(rp_x, ae_y+70, rp_w, 30, "Midpoint (Pt-Ln)", toggle=False)
        self.buttons['const_length'] = Button(rp_x, ae_y+105, btn_half, 30, "Fix Length", toggle=False)
        self.buttons['const_equal'] = Button(rp_x + btn_half + 10, ae_y+105, btn_half, 30, "Equal Len", toggle=False)
        self.buttons['const_parallel'] = Button(rp_x, ae_y+140, btn_half, 30, "Parallel", toggle=False)
        self.buttons['const_perp'] = Button(rp_x + btn_half + 10, ae_y+140, btn_half, 30, "Perpendic", toggle=False)
        self.buttons['const_horiz'] = Button(rp_x, ae_y+175, btn_half, 30, "Horizontal", toggle=False)
        self.buttons['const_vert'] = Button(rp_x + btn_half + 10, ae_y+175, btn_half, 30, "Vertical", toggle=False)
        self.buttons['const_angle'] = Button(rp_x, ae_y+210, btn_half, 30, "Angle", toggle=False)
        
        ae_y += 210
        self.buttons['extend'] = Button(rp_x + btn_half + 10, ae_y, btn_half, 30, "Extend Infinite", toggle=False)

    def draw(self, screen, font, mode):
        # Determine active lists
        sim_elements = [
            self.buttons['play'], self.buttons['clear'], self.buttons['reset'], 
            self.buttons['undo'], self.buttons['redo'],
            *self.sliders.values(), self.buttons['thermostat'], self.buttons['boundaries'],
            self.tools['brush'], self.tools['line'], self.buttons['resize'],
            self.inputs['world']
        ]
        
        editor_elements = [
            self.buttons['save_geo'], self.buttons['discard_geo'], 
            self.buttons['undo'], self.buttons['redo'], self.buttons['clear'],
            self.buttons['editor_play'], self.buttons['show_const'],
            *self.tools.values(), 
            self.buttons['const_coincident'], self.buttons['const_collinear'], self.buttons['const_midpoint'],
            self.buttons['const_length'], self.buttons['const_equal'], self.buttons['const_parallel'],
            self.buttons['const_perp'], self.buttons['const_horiz'], self.buttons['const_vert'],
            self.buttons['const_angle'], self.buttons['extend']
        ]
        
        active_list = sim_elements if mode == config.MODE_SIM else editor_elements
        
        for el in active_list:
            if el == self.inputs['world'] and mode == config.MODE_SIM:
                screen.blit(font.render("World Size:", True, (200, 200, 200)), 
                             (el.rect.x - 70, el.rect.y + 4))
            el.draw(screen, font)

        # Draw Menu LAST to ensure dropdowns are on top
        self.menu.draw(screen, font)

        # Draw Tabs LAST so they appear on top of the Menu Background
        self.buttons['tab_sim'].active = (mode == config.MODE_SIM)
        self.buttons['tab_edit'].active = (mode == config.MODE_EDITOR)
        self.buttons['tab_sim'].draw(screen, font)
        self.buttons['tab_edit'].draw(screen, font)
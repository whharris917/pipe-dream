import pygame
import config
import utils
import file_io
import time
import math
import numpy as np
from tkinter import filedialog, Tk, simpledialog

# Modules
from simulation_state import Simulation
from ui_widgets import InputField, ContextMenu, PropertiesDialog, RotationDialog, AnimationDialog
from geometry import Line, Circle
from constraints import Length
from renderer import Renderer
from app_state import AppState, InteractionState
from tools import SelectTool, BrushTool, LineTool, RectTool, CircleTool, PointTool
from definitions import CONSTRAINT_DEFS
from ui_manager import UIManager
from input_handler import InputHandler

class FlowStateApp:
    def __init__(self):
        # 1. System Setup
        try: self.root_tk = Tk(); self.root_tk.withdraw()
        except: self.root_tk = None

        pygame.init()
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Flow State - Chemical Engineering Simulation")
        
        self.font = pygame.font.SysFont("segoeui", 15)
        self.big_font = pygame.font.SysFont("segoeui", 22)
        self.renderer = Renderer(self.screen, self.font, self.big_font)
        self.clock = pygame.time.Clock()
        self.running = True

        # 2. App Logic
        self.sim = Simulation()
        self.app = AppState()
        self.app.input_world = InputField(0, 0, 0, 0) # Placeholder
        
        # Default View Settings
        self.app.zoom = 0.9
        self.app.sim_view['zoom'] = 0.9
        self.app.editor_view['zoom'] = 0.9
        
        # State
        self.app.editor_paused = False # UI Pause state
        self.app.show_constraints = True
        self.app.geo_time = 0.0
        self.last_time = time.time()

        # 3. UI State
        self.context_menu = None
        self.prop_dialog = None
        self.rot_dialog = None
        self.anim_dialog = None
        self.ctx_vars = {'wall': -1, 'pt': None, 'const': -1}

        # 4. Initialization
        w, h = self.screen.get_size()
        self.init_layout(w, h)
        
        self.ui = UIManager(self.layout, self.app.input_world)
        self.input_handler = InputHandler(self) # Pass self as 'editor'
        
        self.init_tools()    

    def init_layout(self, w, h):
        self.layout = {
            'W': w, 'H': h,
            'LEFT_X': 0, 'LEFT_W': config.PANEL_LEFT_WIDTH,
            'RIGHT_W': config.PANEL_RIGHT_WIDTH, 'RIGHT_X': w - config.PANEL_RIGHT_WIDTH,
            'MID_X': config.PANEL_LEFT_WIDTH, 'MID_W': w - config.PANEL_LEFT_WIDTH - config.PANEL_RIGHT_WIDTH,
            'MID_H': h - config.TOP_MENU_H
        }

    def init_tools(self):
        tool_registry = [
            (config.TOOL_SELECT, SelectTool, None), (config.TOOL_BRUSH, BrushTool, None),
            (config.TOOL_LINE, LineTool, None), (config.TOOL_RECT, RectTool, None),
            (config.TOOL_CIRCLE, CircleTool, None), (config.TOOL_POINT, PointTool, None),
            (config.TOOL_REF, LineTool, "Ref Line"), 
        ]
        for tid, cls, name in tool_registry:
            self.app.tools[tid] = cls(self.app, self.sim)
            if name: self.app.tools[tid].name = name
        self.change_tool(config.TOOL_BRUSH)

    def handle_resize(self, w, h):
        old_mid_w = self.layout['MID_W']
        old_mid_h = self.layout['MID_H']
        self.init_layout(w, h)
        
        if old_mid_w > 0 and old_mid_h > 0:
            new_mid_w = self.layout['MID_W']
            new_mid_h = self.layout['MID_H']
            old_ar = old_mid_w / old_mid_h
            new_ar = new_mid_w / new_mid_h
            if abs(new_ar - old_ar) > 0.001:
                correction = old_ar / new_ar
                self.app.zoom *= correction
                self.app.sim_view['zoom'] *= correction
                self.app.editor_view['zoom'] *= correction

        self.ui = UIManager(self.layout, self.app.input_world)
        self.input_handler = InputHandler(self)
        self.ui.menu.resize(w)

    def run(self):
        while self.running:
            self.input_handler.handle_input()
            self.update_physics()
            self.render()
            self.clock.tick()
        if self.root_tk: self.root_tk.destroy()
        pygame.quit()

    def _spawn_context_menu(self, pos):
        mx, my = pos
        sim_x, sim_y = utils.screen_to_sim(mx, my, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, self.layout)
        
        # 1. Constraints
        if self.app.show_constraints:
            for i, c in enumerate(self.sim.constraints):
                if c.hit_test(mx, my): 
                    self.ctx_vars['const'] = i
                    opts = self.sim.geo.get_context_options('constraint', i)
                    self.context_menu = ContextMenu(mx, my, opts)
                    return

        # 2. Points
        point_map = utils.get_grouped_points(self.sim, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, self.layout)
        hit_pt = None; base_r, step_r = 5, 4
        for center_pos, items in point_map.items():
            if math.hypot(mx - center_pos[0], my - center_pos[1]) <= base_r + (len(items) - 1) * step_r: hit_pt = items[0]; break

        if hit_pt:
            self.ctx_vars['wall'] = hit_pt[0]; self.ctx_vars['pt'] = hit_pt[1]
            # Updated to pass point index for Anchor/Un-Anchor context
            opts = self.sim.geo.get_context_options('point', hit_pt[0], hit_pt[1])
            self.context_menu = ContextMenu(mx, my, opts)
            if self.app.pending_constraint: self.handle_pending_constraint_click(pt_idx=hit_pt)
            return

        # 3. Walls
        rad_sim = 5.0 / (((self.layout['MID_W'] - 50) / self.sim.world_size) * self.app.zoom)
        hit_wall = self.sim.geo.find_wall_at(sim_x, sim_y, rad_sim)
        
        if hit_wall != -1:
            if self.app.pending_constraint: self.handle_pending_constraint_click(wall_idx=hit_wall)
            else:
                self.ctx_vars['wall'] = hit_wall
                opts = self.sim.geo.get_context_options('wall', hit_wall)
                self.context_menu = ContextMenu(mx, my, opts)
        else:
            if self.app.mode == config.MODE_EDITOR: 
                self.change_tool(config.TOOL_SELECT)
                self.app.set_status("Switched to Select Tool")

    def update_physics(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        
        # Update Editor/Geometry Time
        if not self.app.editor_paused:
            self.app.geo_time += dt

        # Update Drivers (Motors)
        self.sim.update_constraint_drivers(self.app.geo_time)
        
        # Solve Constraints (The 'Blueprint' layer)
        # We solve constraints in both modes now, ensuring "Live" feel
        self.sim.apply_constraints()

        # Update Physics (The 'Fluid' layer)
        if self.app.mode == config.MODE_SIM:
            # Sync Controls
            self.sim.paused = not self.ui.buttons['play'].active
            self.sim.gravity = self.ui.sliders['gravity'].val
            self.sim.target_temp = self.ui.sliders['temp'].val
            self.sim.damping = self.ui.sliders['damping'].val
            self.sim.dt = self.ui.sliders['dt'].val
            self.sim.sigma = self.ui.sliders['sigma'].val
            self.sim.epsilon = self.ui.sliders['epsilon'].val
            self.sim.skin_distance = self.ui.sliders['skin'].val
            self.sim.use_thermostat = self.ui.buttons['thermostat'].active
            self.sim.use_boundaries = self.ui.buttons['boundaries'].active
            
            if not self.sim.paused:
                self.sim.step(int(self.ui.sliders['speed'].val))
            
            # Tool Updates
            if self.app.current_tool:
                self.app.current_tool.update(dt, self.layout, self.ui)

    def render(self):
        ui_list = [] 
        
        # Temp hide constraints if disabled in UI
        held_constraints = self.sim.constraints
        if not self.app.show_constraints:
            # We temporarily mask constraints for the renderer
            self.sim.constraints = []
            
        self.renderer.draw_app(self.app, self.sim, self.layout, [])
        
        if not self.app.show_constraints:
            self.sim.constraints = held_constraints

        # Draw UI
        self.ui.draw(self.screen, self.font, self.app.mode)

        if self.context_menu: self.context_menu.draw(self.screen, self.font)
        if self.prop_dialog: self.prop_dialog.draw(self.screen, self.font)
        if self.rot_dialog: self.rot_dialog.draw(self.screen, self.font)
        if self.anim_dialog: self.anim_dialog.draw(self.screen, self.font)
        pygame.display.flip()

    def change_tool(self, tool_id):
        self.app.change_tool(tool_id) 
        if hasattr(self, 'input_handler'):
            for btn, tid in self.input_handler.tool_btn_map.items(): 
                btn.active = (tid == tool_id)

    def _update_window_title(self):
        title = "Flow State - Chemical Engineering Simulation"
        if self.app.current_sim_filepath:
            name = self.app.current_sim_filepath.replace("\\", "/").split("/")[-1]
            title += f" - {name}"
        elif self.app.current_geom_filepath:
            name = self.app.current_geom_filepath.replace("\\", "/").split("/")[-1]
            title += f" - {name}"
        pygame.display.set_caption(title)

    def _execute_menu(self, selection):
        # Unified Menu Logic
        if selection == "New": 
            # Clears EVERYTHING (Geometry + Physics)
            self.sim.reset_simulation()
            self.sim.sketch.clear() # Clear Sketch too
            self.app.input_world.set_value(config.DEFAULT_WORLD_SIZE)
            self.app.current_sim_filepath = None
            self.app.current_geom_filepath = None
            self.app.set_status("New Project Created")
            self._update_window_title()
            
        elif selection == "Import Geometry":
            if self.root_tk:
                f = filedialog.askopenfilename(filetypes=[("Geometry Files", "*.geom"), ("All Files", "*.*")])
                if f:
                    data, _ = file_io.load_geometry_file(f)
                    if data: 
                        self.app.placing_geo_data = data
                        self.app.set_status("Place Model")
                        
        elif self.root_tk:
            if selection == "Save As..." or (selection == "Save"):
                # Unified Save: We just save the "Simulation" which now includes the Sketch
                is_save_as = (selection == "Save As...")
                if is_save_as or not self.app.current_sim_filepath:
                    f = filedialog.asksaveasfilename(defaultextension=".sim", filetypes=[("Simulation Files", "*.sim")])
                    if f: self.app.current_sim_filepath = f
                
                if self.app.current_sim_filepath:
                    self.app.set_status(file_io.save_file(self.sim, self.app, self.app.current_sim_filepath))
                    self._update_window_title()
                    
            elif selection == "Open...":
                f = filedialog.askopenfilename(filetypes=[("Simulation Files", "*.sim")])
                if f:
                    self.app.current_sim_filepath = f
                    success, msg, view_state = file_io.load_file(self.sim, f)
                    self.app.set_status(msg)
                    if success: 
                        self.app.input_world.set_value(self.sim.world_size)
                        if view_state:
                            self.app.zoom = view_state['zoom']
                            self.app.pan_x = view_state['pan_x']
                            self.app.pan_y = view_state['pan_y']
                    self._update_window_title()
        pygame.event.pump()

    def switch_mode(self, mode):
        if mode == self.app.mode: return

        # Store previous view
        if self.app.mode == config.MODE_SIM:
            self.app.sim_view['zoom'] = self.app.zoom
            self.app.sim_view['pan_x'] = self.app.pan_x
            self.app.sim_view['pan_y'] = self.app.pan_y
        else:
            self.app.editor_view['zoom'] = self.app.zoom
            self.app.editor_view['pan_x'] = self.app.pan_x
            self.app.editor_view['pan_y'] = self.app.pan_y

        self.app.mode = mode

        # Restore view & Configure UI
        if mode == config.MODE_SIM:
            self.app.zoom = self.app.sim_view['zoom']
            self.app.pan_x = self.app.sim_view['pan_x']
            self.app.pan_y = self.app.sim_view['pan_y']
            
            # Entering Sim Mode: Enable Physics UI, maybe unpause?
            self.ui.buttons['play'].active = False
            self.sim.paused = True
            self.change_tool(self.app.sim_tool)
            
        else:
            self.app.zoom = self.app.editor_view['zoom']
            self.app.pan_x = self.app.editor_view['pan_x']
            self.app.pan_y = self.app.editor_view['pan_y']
            
            # Entering Editor Mode: Force Pause Physics
            self.ui.buttons['play'].active = False
            self.sim.paused = True
            self.change_tool(self.app.editor_tool)
            
        self._update_window_title()

    # --- Wrapper methods to satisfy InputHandler calls ---
    
    def toggle_extend(self):
        if self.app.selected_walls:
            for idx in self.app.selected_walls:
                if idx < len(self.sim.walls) and isinstance(self.sim.walls[idx], Line): 
                    # Need to check if 'infinite' attr exists on Line, if not add it
                    if not hasattr(self.sim.walls[idx], 'infinite'): self.sim.walls[idx].infinite = False
                    self.sim.walls[idx].infinite = not self.sim.walls[idx].infinite
            self.sim.rebuild_static_atoms(); self.app.set_status("Toggled Extend")
            
    def toggle_editor_play(self):
        self.app.editor_paused = not self.app.editor_paused
        self.ui.buttons['editor_play'].text = "Play" if self.app.editor_paused else "Pause"
        self.ui.buttons['editor_play'].cached_surf = None
        
    def toggle_show_constraints(self):
        self.app.show_constraints = not self.app.show_constraints
        self.ui.buttons['show_const'].text = "Show Cnstr" if not self.app.show_constraints else "Hide Cnstr"
        self.ui.buttons['show_const'].cached_surf = None

    def save_geo_dialog(self):
        if self.root_tk:
            f = filedialog.asksaveasfilename(defaultextension=".geom", filetypes=[("Geometry Files", "*.geom")])
            if f: 
                self.app.current_geom_filepath = f
                self.app.set_status(file_io.save_geometry_file(self.sim, self.app, f))
                self._update_window_title()

    def trigger_constraint(self, ctype):
        for btn, c_val in self.input_handler.constraint_btn_map.items(): btn.active = (c_val == ctype)
        
        # Check for multi-select rules (Horizontal/Vertical on multiple lines)
        is_multi = False
        if ctype in CONSTRAINT_DEFS and CONSTRAINT_DEFS[ctype][0].get('multi'):
            walls = list(self.app.selected_walls)
            if walls:
                count = 0
                for w_idx in walls:
                    if self.sim.attempt_apply_constraint(ctype, [w_idx], []): count += 1
                if count > 0:
                    self.app.set_status(f"Applied {ctype} to {count} items")
                    self.app.selected_walls.clear(); self.app.selected_points.clear()
                    self.sim.apply_constraints(); is_multi = True
        
        if is_multi: return
        
        # Standard constraint application
        walls = list(self.app.selected_walls); pts = list(self.app.selected_points)
        if self.sim.attempt_apply_constraint(ctype, walls, pts):
            self.app.set_status(f"Applied {ctype}")
            self.app.selected_walls.clear(); self.app.selected_points.clear()
            self.app.pending_constraint = None
            for btn in self.input_handler.constraint_btn_map.keys(): btn.active = False
            self.sim.apply_constraints()
        else:
            self.app.pending_constraint = ctype
            self.app.pending_targets_walls = list(self.app.selected_walls)
            self.app.pending_targets_points = list(self.app.selected_points)
            self.app.selected_walls.clear(); self.app.selected_points.clear()
            msg = CONSTRAINT_DEFS[ctype][0]['msg'] if ctype in CONSTRAINT_DEFS else "Select targets..."
            self.app.set_status(f"{ctype}: {msg}")

    def handle_pending_constraint_click(self, wall_idx=None, pt_idx=None):
        if not self.app.pending_constraint: return
        if wall_idx is not None and wall_idx not in self.app.pending_targets_walls: self.app.pending_targets_walls.append(wall_idx)
        if pt_idx is not None and pt_idx not in self.app.pending_targets_points: self.app.pending_targets_points.append(pt_idx)
        
        if self.sim.attempt_apply_constraint(self.app.pending_constraint, self.app.pending_targets_walls, self.app.pending_targets_points):
            self.app.set_status(f"Applied {self.app.pending_constraint}")
            self.app.pending_constraint = None
            for btn in self.input_handler.constraint_btn_map.keys(): btn.active = False
            self.sim.apply_constraints()
        else:
            ctype = self.app.pending_constraint; msg = CONSTRAINT_DEFS[ctype][0]['msg']
            self.app.set_status(f"{ctype} ({len(self.app.pending_targets_walls)}W, {len(self.app.pending_targets_points)}P): {msg}")
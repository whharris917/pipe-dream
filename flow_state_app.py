import pygame
import config
import utils
import file_io
import time
import math
import sys
import subprocess
import numpy as np
from tkinter import filedialog, Tk, simpledialog

# Contexts
from simulation_state import Simulation
from model_builder import ModelBuilder 

from ui_widgets import InputField, ContextMenu, MaterialDialog, RotationDialog, AnimationDialog
from geometry import Line, Circle
from constraints import Length
from renderer import Renderer
from app_state import AppState, InteractionState
from tools import SelectTool, BrushTool, LineTool, RectTool, CircleTool, PointTool
from definitions import CONSTRAINT_DEFS
from ui_manager import UIManager
from input_handler import InputHandler

class FlowStateApp:
    def __init__(self, start_mode=config.MODE_SIM):
        # 1. System Setup
        try: self.root_tk = Tk(); self.root_tk.withdraw()
        except: self.root_tk = None

        pygame.init()
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.RESIZABLE)
        
        title_suffix = "Simulation" if start_mode == config.MODE_SIM else "Model Builder"
        pygame.display.set_caption(f"Flow State - {title_suffix}")
        
        self.font = pygame.font.SysFont("segoeui", 15)
        self.big_font = pygame.font.SysFont("segoeui", 22)
        self.renderer = Renderer(self.screen, self.font, self.big_font)
        self.clock = pygame.time.Clock()
        self.running = True

        # 2. App Logic
        self.app = AppState()
        self.app.mode = start_mode 
        
        # --- CONTEXT SWITCHING ---
        if self.app.mode == config.MODE_EDITOR:
            self.active_context = ModelBuilder()
            self.sim = None # Explicitly None to prevent accidental usage
        else:
            self.active_context = Simulation()
            self.sim = self.active_context # Alias for backward compat if needed temporarily
            
        self.app.input_world = InputField(0, 0, 0, 0)
        
        # Default View Settings
        self.app.zoom = 0.9
        
        # State
        self.app.editor_paused = False 
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
        self.input_handler = InputHandler(self) 
        
        self.init_tools() 
        
        if self.app.mode == config.MODE_EDITOR:
            self.change_tool(config.TOOL_SELECT) 
        else:
            self.change_tool(config.TOOL_BRUSH) 

    # --- Properties to expose active context ---
    @property
    def walls(self): return self.active_context.walls
    
    @property
    def constraints(self): return self.active_context.constraints
    
    @constraints.setter
    def constraints(self, value):
        # REQUIRED: This setter allows tools.py to modify the list (e.g. cleaning temp constraints)
        self.active_context.constraints = value

    @property
    def geo(self): return self.active_context.geo
    @property
    def world_size(self): return self.active_context.world_size

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
            self.app.tools[tid] = cls(self.app, self) 
            if name: self.app.tools[tid].name = name

    def handle_resize(self, w, h):
        old_mid_w = self.layout['MID_W']
        old_mid_h = self.layout['MID_H']
        self.init_layout(w, h)
        if old_mid_w > 0 and old_mid_h > 0:
            new_mid_w = self.layout['MID_W']
            new_mid_h = self.layout['MID_H']
            correction = (old_mid_w / old_mid_h) / (new_mid_w / new_mid_h)
            if abs(correction - 1.0) > 0.001:
                self.app.zoom *= correction
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
        sim_x, sim_y = utils.screen_to_sim(mx, my, self.app.zoom, self.app.pan_x, self.app.pan_y, self.active_context.world_size, self.layout)
        
        if self.app.show_constraints:
            for i, c in enumerate(self.active_context.constraints):
                if c.hit_test(mx, my): 
                    self.ctx_vars['const'] = i
                    opts = self.active_context.geo.get_context_options('constraint', i)
                    self.context_menu = ContextMenu(mx, my, opts)
                    return

        point_map = utils.get_grouped_points(self.active_context, self.app.zoom, self.app.pan_x, self.app.pan_y, self.active_context.world_size, self.layout)
        hit_pt = None; base_r, step_r = 5, 4
        for center_pos, items in point_map.items():
            if math.hypot(mx - center_pos[0], my - center_pos[1]) <= base_r + (len(items) - 1) * step_r: hit_pt = items[0]; break

        if hit_pt:
            self.ctx_vars['wall'] = hit_pt[0]; self.ctx_vars['pt'] = hit_pt[1]
            opts = self.active_context.geo.get_context_options('point', hit_pt[0], hit_pt[1])
            self.context_menu = ContextMenu(mx, my, opts)
            if self.app.pending_constraint: self.handle_pending_constraint_click(pt_idx=hit_pt)
            return

        rad_sim = 5.0 / (((self.layout['MID_W'] - 50) / self.active_context.world_size) * self.app.zoom)
        hit_wall = self.active_context.geo.find_wall_at(sim_x, sim_y, rad_sim)
        
        if hit_wall != -1:
            if self.app.pending_constraint: self.handle_pending_constraint_click(wall_idx=hit_wall)
            else:
                self.ctx_vars['wall'] = hit_wall
                opts = self.active_context.geo.get_context_options('wall', hit_wall)
                self.context_menu = ContextMenu(mx, my, opts)
        else:
            if self.app.mode == config.MODE_EDITOR: 
                self.change_tool(config.TOOL_SELECT)
                self.app.set_status("Switched to Select Tool")

    def update_physics(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        
        if not self.app.editor_paused:
            self.app.geo_time += dt
        
        if isinstance(self.active_context, Simulation):
            self.active_context.update_constraint_drivers(self.app.geo_time)
            self.active_context.apply_constraints()
            
            self.active_context.paused = not self.ui.buttons['play'].active
            self.active_context.gravity = self.ui.sliders['gravity'].val
            self.active_context.target_temp = self.ui.sliders['temp'].val
            self.active_context.damping = self.ui.sliders['damping'].val
            self.active_context.dt = self.ui.sliders['dt'].val
            self.active_context.sigma = self.ui.sliders['sigma'].val
            self.active_context.epsilon = self.ui.sliders['epsilon'].val
            self.active_context.skin_distance = self.ui.sliders['skin'].val
            self.active_context.use_thermostat = self.ui.buttons['thermostat'].active
            self.active_context.use_boundaries = self.ui.buttons['boundaries'].active
            
            if not self.active_context.paused:
                self.active_context.step(int(self.ui.sliders['speed'].val))
        
        else:
            # ModelBuilder Logic
            self.active_context.update_constraint_drivers(self.app.geo_time)
            self.active_context.apply_constraints()

        if self.app.current_tool:
            self.app.current_tool.update(dt, self.layout, self.ui)

    def render(self):
        # Pass active_context to renderer
        self.renderer.draw_app(self.app, self.active_context, self.layout, [])

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
        base = "Simulation" if self.app.mode == config.MODE_SIM else "Model Builder"
        title = f"Flow State - {base}"
        if self.app.current_sim_filepath:
            name = self.app.current_sim_filepath.replace("\\", "/").split("/")[-1]
            title += f" - {name}"
        pygame.display.set_caption(title)

    def _execute_menu(self, selection):
        if selection == "New Simulation":
            subprocess.Popen([sys.executable, "run_instance.py", "sim"])
        elif selection == "New Model":
            subprocess.Popen([sys.executable, "run_instance.py", "editor"])
        elif selection == "New": 
            self.active_context.reset_simulation()
            self.app.input_world.set_value(config.DEFAULT_WORLD_SIZE)
            self.app.current_sim_filepath = None
            self.app.set_status("New Project Created")
            self._update_window_title()
        elif selection == "Import Geometry":
            if self.root_tk:
                f = filedialog.askopenfilename(filetypes=[("Geometry Files", "*.geom"), ("All Files", "*.*")])
                if f:
                    data, _ = file_io.load_geometry_file(f)
                    if data: 
                        if hasattr(self.active_context.geo, 'place_geometry'):
                            self.app.placing_geo_data = data
                            self.app.set_status("Place Model")
        elif self.root_tk:
            if selection == "Save As..." or (selection == "Save"):
                is_save_as = (selection == "Save As...")
                if is_save_as or not self.app.current_sim_filepath:
                    ext = ".sim" if isinstance(self.active_context, Simulation) else ".mdl"
                    ft = [("Simulation Files", "*.sim")] if ext == ".sim" else [("Model Files", "*.mdl")]
                    f = filedialog.asksaveasfilename(defaultextension=ext, filetypes=ft)
                    if f: self.app.current_sim_filepath = f
                if self.app.current_sim_filepath:
                    self.app.set_status(file_io.save_file(self.active_context, self.app, self.app.current_sim_filepath))
                    self._update_window_title()
            elif selection == "Open...":
                ext = "*.sim" if isinstance(self.active_context, Simulation) else "*.mdl"
                f = filedialog.askopenfilename(filetypes=[("Project Files", ext)])
                if f:
                    self.app.current_sim_filepath = f
                    success, msg, view_state = file_io.load_file(self.active_context, f)
                    self.app.set_status(msg)
                    if success: 
                        self.app.input_world.set_value(self.active_context.world_size)
                        if view_state:
                            self.app.zoom = view_state['zoom']
                            self.app.pan_x = view_state['pan_x']
                            self.app.pan_y = view_state['pan_y']
                    self._update_window_title()
        pygame.event.pump()

    # --- Wrapper methods (Controller Layer) ---
    
    def exit_editor_mode(self, backup_state=None):
        self.active_context.reset_simulation()
        self.app.set_status("Reset/Discarded")

    def toggle_extend(self):
        if self.app.selected_walls:
            for idx in self.app.selected_walls:
                if idx < len(self.active_context.walls) and isinstance(self.active_context.walls[idx], Line): 
                    if not hasattr(self.active_context.walls[idx], 'infinite'): self.active_context.walls[idx].infinite = False
                    self.active_context.walls[idx].infinite = not self.active_context.walls[idx].infinite
            
            if hasattr(self.active_context, 'rebuild_static_atoms'):
                self.active_context.rebuild_static_atoms()
            self.app.set_status("Toggled Extend")
            
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
                self.app.set_status(file_io.save_geometry_file(self.active_context, self.app, f))
                self._update_window_title()

    # --- SMART CONSTRAINT TRIGGER (FIXED) ---
    
    def _try_apply_constraint_smart(self, ctype, walls, pts):
        # 1. Try Strict Match
        if self.active_context.attempt_apply_constraint(ctype, walls, pts):
            self.app.set_status(f"Applied {ctype}")
            self.app.selected_walls.clear(); self.app.selected_points.clear()
            self.app.pending_constraint = None
            for btn in self.input_handler.constraint_btn_map.keys(): btn.active = False
            self.active_context.apply_constraints()
            return True
            
        # 2. Try Fuzzy Match (Auto-Trim)
        # If we have *more* than required, trim to fit the first rule found.
        if ctype in CONSTRAINT_DEFS:
            rules = CONSTRAINT_DEFS[ctype]
            for r in rules:
                if len(walls) >= r['w'] and len(pts) >= r['p']:
                    sub_w = walls[:r['w']]
                    sub_p = pts[:r['p']]
                    if self.active_context.attempt_apply_constraint(ctype, sub_w, sub_p):
                         self.app.set_status(f"Applied {ctype} (Auto-Trimmed)")
                         self.app.selected_walls.clear(); self.app.selected_points.clear()
                         self.app.pending_constraint = None
                         for btn in self.input_handler.constraint_btn_map.keys(): btn.active = False
                         self.active_context.apply_constraints()
                         return True
        return False

    def trigger_constraint(self, ctype):
        for btn, c_val in self.input_handler.constraint_btn_map.items(): btn.active = (c_val == ctype)
        is_multi = False
        if ctype in CONSTRAINT_DEFS and CONSTRAINT_DEFS[ctype][0].get('multi'):
            walls = list(self.app.selected_walls)
            if walls:
                count = 0
                for w_idx in walls:
                    if self.active_context.attempt_apply_constraint(ctype, [w_idx], []): count += 1
                if count > 0:
                    self.app.set_status(f"Applied {ctype} to {count} items")
                    self.app.selected_walls.clear(); self.app.selected_points.clear()
                    self.active_context.apply_constraints(); is_multi = True
        if is_multi: return
        
        walls = list(self.app.selected_walls); pts = list(self.app.selected_points)
        
        if self._try_apply_constraint_smart(ctype, walls, pts):
            return

        # 3. Fallback to Pending
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
        
        if self._try_apply_constraint_smart(self.app.pending_constraint, self.app.pending_targets_walls, self.app.pending_targets_points):
            return
            
        ctype = self.app.pending_constraint; msg = CONSTRAINT_DEFS[ctype][0]['msg']
        self.app.set_status(f"{ctype} ({len(self.app.pending_targets_walls)}W, {len(self.app.pending_targets_points)}P): {msg}")

    # --- Geometry Creation Interceptors ---
    
    def add_wall(self, start_pos, end_pos, is_ref=False):
        is_ghost = self.ui.buttons['mode_ghost'].active
        mat_id = "Ghost" if is_ref or is_ghost else "Default"
        self.active_context.snapshot()
        self.active_context.sketch.add_line(start_pos, end_pos, is_ref, material_id=mat_id)
        if hasattr(self.active_context, 'rebuild_static_atoms'):
            self.active_context.rebuild_static_atoms()
        
    def add_circle(self, center, radius):
        is_ghost = self.ui.buttons['mode_ghost'].active
        mat_id = "Ghost" if is_ghost else "Default"
        self.active_context.snapshot()
        self.active_context.sketch.add_circle(center, radius, material_id=mat_id)
        if hasattr(self.active_context, 'rebuild_static_atoms'):
            self.active_context.rebuild_static_atoms()

    # --- Pass-throughs ---
    def remove_wall(self, index): self.active_context.remove_wall(index)
    def toggle_anchor(self, wall_idx, pt_idx): self.active_context.toggle_anchor(wall_idx, pt_idx)
    def update_wall(self, index, s, e): 
        self.active_context.sketch.update_entity(index, start=s, end=e, center=s)
        if hasattr(self.active_context, 'rebuild_static_atoms'): self.active_context.rebuild_static_atoms()
        
    def update_wall_props(self, idx, props): 
        self.active_context.snapshot()
        self.active_context.sketch.update_entity(idx, **props)
        if hasattr(self.active_context, 'rebuild_static_atoms'): self.active_context.rebuild_static_atoms()

    def set_wall_rotation(self, idx, params): 
        w = self.active_context.walls[idx]
        if isinstance(w, Circle): return
        speed = params['speed']; pivot = params['pivot']
        anim = None
        if abs(speed) > 1e-5:
             anim = {'type': 'rotate', 'speed': speed, 'pivot': pivot, 'angle': 0.0, 'ref_start': w.start.copy(), 'ref_end': w.end.copy()}
        w.anim = anim
        if hasattr(self.active_context, 'rebuild_static_atoms'): self.active_context.rebuild_static_atoms()

    def update_constraint_drivers(self, t): self.active_context.update_constraint_drivers(t)
    def attempt_apply_constraint(self, t, w, p): return self.active_context.attempt_apply_constraint(t, w, p)
    def apply_constraints(self): self.active_context.apply_constraints()
    def add_constraint_object(self, c): self.active_context.add_constraint_object(c)
    
    def add_particles_brush(self, x, y, r): 
        if hasattr(self.active_context, 'add_particles_brush'): self.active_context.add_particles_brush(x, y, r)
    def delete_particles_brush(self, x, y, r): 
        if hasattr(self.active_context, 'delete_particles_brush'): self.active_context.delete_particles_brush(x, y, r)
    
    def snapshot(self): self.active_context.snapshot()
    def undo(self): self.active_context.undo()
    def redo(self): self.active_context.redo()
    def resize_world(self, s): self.active_context.resize_world(s)
    def reset_simulation(self): self.active_context.reset_simulation()
    def clear_particles(self): self.active_context.clear_particles()
    def rebuild_static_atoms(self): 
        if hasattr(self.active_context, 'rebuild_static_atoms'): self.active_context.rebuild_static_atoms()
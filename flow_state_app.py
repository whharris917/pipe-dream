import pygame
# CRITICAL: Initialize mixer before pygame.init for high-quality procedural audio
pygame.mixer.pre_init(44100, -16, 1, 1024)
pygame.init()

import config
import utils
import file_io
import time
import math
import sys
import subprocess
import numpy as np
from tkinter import filedialog, Tk, simpledialog

# Modules
from simulation import Simulation
from session import Session
from ui_widgets import InputField, ContextMenu, MaterialDialog, RotationDialog, AnimationDialog
from geometry import Line, Circle
from constraints import Length
from renderer import Renderer
from session import InteractionState
from tools import SelectTool, BrushTool, LineTool, RectTool, CircleTool, PointTool
from definitions import CONSTRAINT_DEFS
from ui_manager import UIManager
from input_handler import InputHandler
import simulation_geometry
from sound_manager import SoundManager

class FlowStateApp:
    def __init__(self, start_mode=config.MODE_SIM):
        # 1. System Setup
        try: self.root_tk = Tk(); self.root_tk.withdraw()
        except: self.root_tk = None

        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.RESIZABLE)
        
        title_suffix = "Simulation" if start_mode == config.MODE_SIM else "Model Builder"
        pygame.display.set_caption(f"Flow State - {title_suffix}")
        
        # Load Fonts
        self.font = pygame.font.SysFont("segoeui", 15)
        self.big_font = pygame.font.SysFont("segoeui", 22)
        
        self.renderer = Renderer(self.screen, self.font, self.big_font)
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize Audio
        self.sound_manager = SoundManager.get()
        if start_mode == config.MODE_SIM:
            self.sound_manager.play_music('Whimsical')
        else:
            self.sound_manager.play_music('Jungle')

        # 2. App Logic (Session)
        self.session = Session()
        self.session.mode = start_mode 
        
        # Initialize Simulation
        is_editor = (start_mode == config.MODE_EDITOR)
        self.sim = Simulation(skip_warmup=is_editor)
        
        # Expose Sketch Explicitly
        self.sketch = self.sim.sketch
        
        self.session.input_world = InputField(0, 0, 0, 0)
        
        # Default View Settings
        self.session.zoom = 0.9
        
        # State
        self.session.editor_paused = False 
        self.session.show_constraints = True
        self.session.geo_time = 0.0
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
        
        self.ui = UIManager(self.layout, self.session.input_world, mode=self.session.mode)
        self.input_handler = InputHandler(self) 
        
        self.init_tools() 
        
        if self.session.mode == config.MODE_EDITOR:
            self.change_tool(config.TOOL_SELECT) 
        else:
            self.change_tool(config.TOOL_BRUSH) 

    # --- Properties ---
    @property
    def walls(self): return self.sim.walls
    
    @property
    def constraints(self): return self.sim.constraints
    
    @constraints.setter
    def constraints(self, value):
        self.sim.constraints = value

    @property
    def geo(self): return self.sim.geo
    @property
    def world_size(self): return self.sim.world_size

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
            self.session.tools[tid] = cls(self) 
            if name: self.session.tools[tid].name = name

    def handle_resize(self, w, h):
        old_mid_w = self.layout['MID_W']
        old_mid_h = self.layout['MID_H']
        self.init_layout(w, h)
        if old_mid_w > 0 and old_mid_h > 0:
            new_mid_w = self.layout['MID_W']
            new_mid_h = self.layout['MID_H']
            correction = (old_mid_w / old_mid_h) / (new_mid_w / new_mid_h)
            if abs(correction - 1.0) > 0.001:
                self.session.zoom *= correction
        self.ui = UIManager(self.layout, self.session.input_world)
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

    # --- BUSINESS LOGIC ACTIONS ---

    def toggle_ghost_mode(self):
        self.session.show_wall_atoms = not getattr(self.session, 'show_wall_atoms', True)
        if 'mode_ghost' in self.ui.buttons:
            self.ui.buttons['mode_ghost'].active = not self.session.show_wall_atoms 
        state = "Hidden" if not self.session.show_wall_atoms else "Visible"
        self.session.set_status(f"Wall Atoms: {state}")

    def atomize_selected(self):
        if self.session.selected_walls:
            count = 0
            for idx in self.session.selected_walls:
                if idx < len(self.sim.walls):
                    self.sim.update_wall_props(idx, {'physical': True})
                    count += 1
            self.sim.rebuild_static_atoms()
            self.session.set_status(f"Atomized {count} entities")
        else:
            self.sim.rebuild_static_atoms()
            self.session.set_status("Atomized All Geometry")

    def open_material_dialog(self):
        if not self.session.selected_walls: 
            self.session.set_status("Select a wall first")
            return
            
        mx, my = pygame.mouse.get_pos()
        
        def on_apply(mat_id, color):
            # Update material library if needed
            if mat_id not in self.sketch.materials:
                 self.sketch.materials[mat_id] = type('Material', (), {'color': color}) # Dummy prop
            
            for idx in self.session.selected_walls:
                if idx < len(self.sim.walls):
                    self.sim.walls[idx].material_id = mat_id
            self.session.set_status(f"Assigned Material: {mat_id}")
            self.prop_dialog = None

        first_idx = list(self.session.selected_walls)[0]
        current_mat = self.sim.walls[first_idx].material_id
        
        self.prop_dialog = MaterialDialog(mx, my, self.sketch, current_mat) # Fixed args

    def open_rotation_dialog(self):
        if not self.session.selected_walls:
            self.session.set_status("Select walls to rotate")
            return

        mx, my = pygame.mouse.get_pos()
        first_idx = list(self.session.selected_walls)[0]
        anim = getattr(self.sim.walls[first_idx], 'anim', None)
        self.rot_dialog = RotationDialog(mx, my, anim) # Fixed args to pass existing anim

    def get_context_options(self, target_type, idx1, idx2=None):
        """Moved from SimulationGeometry. Determines valid actions for right-click context."""
        options = []
        if target_type == 'wall':
            options = ["Properties", "Rotate", "Animate", "Atomize", "Delete"]
        elif target_type == 'point':
            w_idx, pt_idx = idx1, idx2
            walls = self.sim.walls
            if w_idx < len(walls):
                w = walls[w_idx]
                is_anchored = False
                if isinstance(w, Line): is_anchored = w.anchored[pt_idx]
                elif isinstance(w, Circle): is_anchored = w.anchored[0]
                elif isinstance(w, PointTool): is_anchored = w.anchored # Should be Point entity
                
                options.append("Un-Anchor" if is_anchored else "Anchor")
                options.append("Set Length...") # Contextual
        elif target_type == 'constraint':
            options = ["Delete Constraint", "Animate...", "Set Angle..."]
            
        return options

    def handle_context_menu_action(self, action):
        """Routes context menu selections to appropriate logic."""
        if action == "Properties":
            self.open_material_dialog()
        elif action == "Rotate":
            self.open_rotation_dialog()
        # "Animate" usually opens AnimationDialog for a wall or constraint
        elif action == "Animate":
             # This is tricky because Animate for Walls vs Constraints differs.
             # Implementation deferred or handled by InputHandler directly calling Dialog.
             pass 
        elif action == "Delete":
            if self.ctx_vars['wall'] != -1:
                self.sim.remove_wall(self.ctx_vars['wall'])
                self.session.set_status("Deleted Wall")
        elif action == "Delete Constraint":
            if self.ctx_vars['const'] != -1:
                if self.ctx_vars['const'] < len(self.sim.constraints):
                    self.sim.constraints.pop(self.ctx_vars['const'])
                    self.session.set_status("Deleted Constraint")
        elif action == "Anchor" or action == "Un-Anchor":
            if self.ctx_vars['wall'] != -1 and self.ctx_vars['pt'] is not None:
                self.sim.toggle_anchor(self.ctx_vars['wall'], self.ctx_vars['pt'])
        elif action == "Atomize":
            if self.ctx_vars['wall'] != -1:
                self.session.selected_walls.add(self.ctx_vars['wall'])
                self.atomize_selected()
                self.session.selected_walls.clear()
        
        self.context_menu = None # Close menu

    # --- End Business Logic ---

    def _spawn_context_menu(self, pos):
        mx, my = pos
        sim_x, sim_y = utils.screen_to_sim(mx, my, self.session.zoom, self.session.pan_x, self.session.pan_y, self.sim.world_size, self.layout)
        
        # Check for constraints using SIMULATION GEOMETRY LAYOUT
        if self.session.show_constraints:
            # Re-calculate layout for hit testing
            layout_data = simulation_geometry.get_constraint_layout(
                self.sim.constraints, self.sim.walls, 
                self.session.zoom, self.session.pan_x, self.session.pan_y, 
                self.sim.world_size, self.layout
            )
            
            for item in layout_data:
                if item['rect'].collidepoint(mx, my):
                    const_idx = item['index']
                    self.ctx_vars['const'] = const_idx
                    opts = self.get_context_options('constraint', const_idx) # Use local method
                    self.context_menu = ContextMenu(mx, my, opts)
                    return

        point_map = utils.get_grouped_points(self.sim.walls, self.session.zoom, self.session.pan_x, self.session.pan_y, self.sim.world_size, self.layout)
        hit_pt = None; base_r, step_r = 5, 4
        for center_pos, items in point_map.items():
            if math.hypot(mx - center_pos[0], my - center_pos[1]) <= base_r + (len(items) - 1) * step_r: hit_pt = items[0]; break

        if hit_pt:
            self.ctx_vars['wall'] = hit_pt[0]; self.ctx_vars['pt'] = hit_pt[1]
            opts = self.get_context_options('point', hit_pt[0], hit_pt[1]) # Use local method
            self.context_menu = ContextMenu(mx, my, opts)
            if self.session.pending_constraint: self.handle_pending_constraint_click(pt_idx=hit_pt)
            return

        rad_sim = 5.0 / (((self.layout['MID_W'] - 50) / self.sim.world_size) * self.session.zoom)
        hit_wall = self.sim.geo.find_wall_at(sim_x, sim_y, rad_sim)
        
        if hit_wall != -1:
            if self.session.pending_constraint: self.handle_pending_constraint_click(wall_idx=hit_wall)
            else:
                self.ctx_vars['wall'] = hit_wall
                opts = self.get_context_options('wall', hit_wall) # Use local method
                self.context_menu = ContextMenu(mx, my, opts)
        else:
            if self.session.mode == config.MODE_EDITOR: 
                self.change_tool(config.TOOL_SELECT)
                self.session.set_status("Switched to Select Tool")

    def update_physics(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        
        # ANIMATE UI
        self.ui.update(dt)
        if self.prop_dialog: self.prop_dialog.update(dt)
        if self.rot_dialog: self.rot_dialog.update(dt)
        if self.anim_dialog: self.anim_dialog.update(dt)
        
        if not self.session.editor_paused:
            self.session.geo_time += dt

        self.sim.update_constraint_drivers(self.session.geo_time)
        self.sim.apply_constraints()

        if self.session.mode == config.MODE_SIM:
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
        
        if self.session.current_tool:
            # Sync Tool Properties from UI (Controller Logic)
            if self.session.current_tool.name == "Brush":
                if 'brush_size' in self.ui.sliders:
                    self.session.current_tool.brush_radius = self.ui.sliders['brush_size'].val
            
            self.session.current_tool.update(dt, self.layout)

    def render(self):
        self.renderer.draw_app(self, self.layout, [])

        self.ui.draw(self.screen, self.font, self.session.mode)

        if self.context_menu: self.context_menu.draw(self.screen, self.font)
        if self.prop_dialog: self.prop_dialog.draw(self.screen, self.font)
        if self.rot_dialog: self.rot_dialog.draw(self.screen, self.font)
        if self.anim_dialog: self.anim_dialog.draw(self.screen, self.font)
        pygame.display.flip()

    def change_tool(self, tool_id):
        self.session.change_tool(tool_id) 
        if hasattr(self, 'input_handler'):
            for btn, tid in self.input_handler.tool_btn_map.items(): 
                btn.active = (tid == tool_id)
            self.sound_manager.play_sound('tool_select')

    def _update_window_title(self):
        base = "Simulation" if self.session.mode == config.MODE_SIM else "Model Builder"
        title = f"Flow State - {base}"
        if self.session.current_sim_filepath:
            name = self.session.current_sim_filepath.replace("\\", "/").split("/")[-1]
            title += f" - {name}"
        pygame.display.set_caption(title)

    def _execute_menu(self, selection):
        self.sound_manager.play_sound('click')
        if selection == "New Simulation":
            subprocess.Popen([sys.executable, "run_instance.py", "sim"])
        elif selection == "New Model":
            subprocess.Popen([sys.executable, "run_instance.py", "editor"])
        elif selection == "New": 
            self.sim.reset_simulation()
            self.sim.sketch.clear()
            self.session.input_world.set_value(config.DEFAULT_WORLD_SIZE)
            self.session.current_sim_filepath = None
            self.session.set_status("New Project Created")
            self._update_window_title()
        elif selection == "Import Geometry":
            if self.root_tk:
                f = filedialog.askopenfilename(filetypes=[("Geometry Files", "*.geom"), ("All Files", "*.*")])
                if f:
                    data, _ = file_io.load_geometry_file(f)
                    if data: 
                        if hasattr(self.sim.geo, 'place_geometry'):
                            self.session.placing_geo_data = data
                            self.session.set_status("Place Model")
        elif self.root_tk:
            if selection == "Save As..." or (selection == "Save"):
                is_save_as = (selection == "Save As...")
                if is_save_as or not self.session.current_sim_filepath:
                    ext = ".sim" if self.session.mode == config.MODE_SIM else ".mdl"
                    ft = [("Simulation Files", "*.sim")] if ext == ".sim" else [("Model Files", "*.mdl")]
                    f = filedialog.asksaveasfilename(defaultextension=ext, filetypes=ft)
                    if f: self.session.current_sim_filepath = f
                if self.session.current_sim_filepath:
                    self.session.set_status(file_io.save_file(self.sim, self.session, self.session.current_sim_filepath))
                    self._update_window_title()
            elif selection == "Open...":
                ext = "*.sim" if self.session.mode == config.MODE_SIM else "*.mdl"
                f = filedialog.askopenfilename(filetypes=[("Project Files", ext)])
                if f:
                    self.session.current_sim_filepath = f
                    success, msg, view_state = file_io.load_file(self.sim, f)
                    self.session.set_status(msg)
                    if success: 
                        self.session.input_world.set_value(self.sim.world_size)
                        if view_state:
                            self.session.zoom = view_state['zoom']
                            self.session.pan_x = view_state['pan_x']
                            self.session.pan_y = view_state['pan_y']
                    self._update_window_title()
        pygame.event.pump()

    def exit_editor_mode(self, backup_state=None):
        self.sim.reset_simulation()
        self.sim.sketch.clear()
        self.session.set_status("Reset/Discarded")

    def toggle_extend(self):
        if self.session.selected_walls:
            for idx in self.session.selected_walls:
                if idx < len(self.sim.walls) and isinstance(self.sim.walls[idx], Line): 
                    if not hasattr(self.sim.walls[idx], 'infinite'): self.sim.walls[idx].infinite = False
                    self.sim.walls[idx].infinite = not self.sim.walls[idx].infinite
            self.sim.rebuild_static_atoms(); self.session.set_status("Toggled Extend")
            
    def toggle_editor_play(self):
        self.session.editor_paused = not self.session.editor_paused
        self.ui.buttons['editor_play'].text = "Play" if self.session.editor_paused else "Pause"
        self.ui.buttons['editor_play'].cached_surf = None
        
    def toggle_show_constraints(self):
        self.session.show_constraints = not self.session.show_constraints
        self.ui.buttons['show_const'].text = "Show Cnstr" if not self.session.show_constraints else "Hide Cnstr"
        self.ui.buttons['show_const'].cached_surf = None

    def save_geo_dialog(self):
        if self.root_tk:
            f = filedialog.asksaveasfilename(defaultextension=".geom", filetypes=[("Geometry Files", "*.geom")])
            if f: 
                self.session.current_geom_filepath = f
                self.session.set_status(file_io.save_geometry_file(self.sim, self.session, f))
                self._update_window_title()

    def _try_apply_constraint_smart(self, ctype, walls, pts):
        if self.sim.attempt_apply_constraint(ctype, walls, pts):
            self.session.set_status(f"Applied {ctype}")
            self.session.selected_walls.clear(); self.session.selected_points.clear()
            self.session.pending_constraint = None
            for btn in self.input_handler.constraint_btn_map.keys(): btn.active = False
            self.sim.apply_constraints()
            return True
            
        if ctype in CONSTRAINT_DEFS:
            rules = CONSTRAINT_DEFS[ctype]
            for r in rules:
                if len(walls) >= r['w'] and len(pts) >= r['p']:
                    sub_w = walls[:r['w']]
                    sub_p = pts[:r['p']]
                    if self.sim.attempt_apply_constraint(ctype, sub_w, sub_p):
                         self.session.set_status(f"Applied {ctype} (Auto-Trimmed)")
                         self.session.selected_walls.clear(); self.session.selected_points.clear()
                         self.session.pending_constraint = None
                         for btn in self.input_handler.constraint_btn_map.keys(): btn.active = False
                         self.sim.apply_constraints()
                         return True
        return False

    def trigger_constraint(self, ctype):
        for btn, c_val in self.input_handler.constraint_btn_map.items(): btn.active = (c_val == ctype)
        is_multi = False
        if ctype in CONSTRAINT_DEFS and CONSTRAINT_DEFS[ctype][0].get('multi'):
            walls = list(self.session.selected_walls)
            if walls:
                count = 0
                for w_idx in walls:
                    if self.sim.attempt_apply_constraint(ctype, [w_idx], []): count += 1
                if count > 0:
                    self.session.set_status(f"Applied {ctype} to {count} items")
                    self.session.selected_walls.clear(); self.session.selected_points.clear()
                    self.sim.apply_constraints(); is_multi = True
        if is_multi: return
        
        walls = list(self.session.selected_walls); pts = list(self.session.selected_points)
        
        if self._try_apply_constraint_smart(ctype, walls, pts):
            return

        self.session.pending_constraint = ctype
        self.session.pending_targets_walls = list(self.session.selected_walls)
        self.session.pending_targets_points = list(self.session.selected_points)
        self.session.selected_walls.clear(); self.session.selected_points.clear()
        msg = CONSTRAINT_DEFS[ctype][0]['msg'] if ctype in CONSTRAINT_DEFS else "Select targets..."
        self.session.set_status(f"{ctype}: {msg}")

    def handle_pending_constraint_click(self, wall_idx=None, pt_idx=None):
        if not self.session.pending_constraint: return
        if wall_idx is not None and wall_idx not in self.session.pending_targets_walls: self.session.pending_targets_walls.append(wall_idx)
        if pt_idx is not None and pt_idx not in self.session.pending_targets_points: self.session.pending_targets_points.append(pt_idx)
        
        if self._try_apply_constraint_smart(self.session.pending_constraint, self.session.pending_targets_walls, self.session.pending_targets_points):
            return
            
        ctype = self.session.pending_constraint; msg = CONSTRAINT_DEFS[ctype][0]['msg']
        self.session.set_status(f"{ctype} ({len(self.session.pending_targets_walls)}W, {len(self.session.pending_targets_points)}P): {msg}")
    
    def add_wall(self, start_pos, end_pos, is_ref=False):
        is_ghost = self.ui.buttons['mode_ghost'].active
        mat_id = "Ghost" if is_ref or is_ghost else "Default"
        self.sim.add_wall(start_pos, end_pos, is_ref, material_id=mat_id)
        
    def add_circle(self, center, radius):
        is_ghost = self.ui.buttons['mode_ghost'].active
        mat_id = "Ghost" if is_ghost else "Default"
        self.sim.add_circle(center, radius, material_id=mat_id)

    def remove_wall(self, index): self.sim.remove_wall(index)
    def toggle_anchor(self, wall_idx, pt_idx): self.sim.toggle_anchor(wall_idx, pt_idx)
    def update_wall(self, index, s, e): self.sim.update_wall(index, s, e)
    def update_wall_props(self, idx, props): self.sim.update_wall_props(idx, props)
    def set_wall_rotation(self, idx, params): self.sim.set_wall_rotation(idx, params)
    def update_constraint_drivers(self, t): self.sim.update_constraint_drivers(t)
    def attempt_apply_constraint(self, t, w, p): return self.sim.attempt_apply_constraint(t, w, p)
    def apply_constraints(self): self.sim.apply_constraints()
    def add_constraint_object(self, c): self.sim.add_constraint_object(c)
    def add_particles_brush(self, x, y, r): self.sim.add_particles_brush(x, y, r)
    def delete_particles_brush(self, x, y, r): self.sim.delete_particles_brush(x, y, r)
    def snapshot(self): self.sim.snapshot()
    def undo(self): self.sim.undo()
    def redo(self): self.sim.redo()
    def resize_world(self, s): self.sim.resize_world(s)
    def reset_simulation(self): self.sim.reset_simulation()
    def clear_particles(self): self.sim.clear_particles()
    def rebuild_static_atoms(self): self.sim.rebuild_static_atoms()
import pygame
import config
import utils
import sys
from ui_widgets import MaterialDialog, RotationDialog, AnimationDialog, ContextMenu
from constraints import Length
from session import InteractionState
from tkinter import simpledialog

class InputHandler:
    def __init__(self, controller):
        # The 'controller' is the FlowStateApp instance
        self.controller = controller
        
        # Direct references to Model (Sim) and View State (Session)
        self.session = controller.session
        self.sim = controller.sim
        self.ui = controller.ui
        self.layout = controller.layout
        
        # Mappings - Using safe initialization
        self.tool_btn_map = {}
        tool_defs = {
            'brush': config.TOOL_BRUSH, 'select': config.TOOL_SELECT,
            'line': config.TOOL_LINE, 'rect': config.TOOL_RECT,
            'circle': config.TOOL_CIRCLE, 'point': config.TOOL_POINT,
            'ref': config.TOOL_REF
        }
        for key, val in tool_defs.items():
            if key in self.ui.tools:
                self.tool_btn_map[self.ui.tools[key]] = val
        
        self.constraint_btn_map = {}
        constraint_defs = {
            'const_length': 'LENGTH', 'const_equal': 'EQUAL',
            'const_parallel': 'PARALLEL', 'const_perp': 'PERPENDICULAR',
            'const_coincident': 'COINCIDENT', 'const_collinear': 'COLLINEAR',
            'const_midpoint': 'MIDPOINT', 'const_angle': 'ANGLE',
            'const_horiz': 'HORIZONTAL', 'const_vert': 'VERTICAL'
        }
        for key, val in constraint_defs.items():
            if key in self.ui.buttons:
                self.constraint_btn_map[self.ui.buttons[key]] = val

        # Action Map - Now mostly delegates to Controller
        self.ui_action_map = {}
        
        # Helper to safely map buttons if they exist
        def bind_action(btn_key, action):
            if btn_key in self.ui.buttons:
                self.ui_action_map[self.ui.buttons[btn_key]] = action

        bind_action('reset', lambda: self.sim.reset_simulation())
        bind_action('clear', lambda: self.sim.clear_particles())
        bind_action('undo', lambda: (self.sim.undo(), self.session.set_status("Undo")))
        bind_action('redo', lambda: (self.sim.redo(), self.session.set_status("Redo")))
        
        # Delegated to Controller
        bind_action('atomize', self.controller.atomize_selected)
        bind_action('mode_ghost', self.controller.toggle_ghost_mode)
        bind_action('discard_geo', lambda: self.controller.exit_editor_mode(None))
        bind_action('save_geo', self.controller.save_geo_dialog)
        bind_action('extend', self.controller.toggle_extend)
        bind_action('editor_play', self.controller.toggle_editor_play)
        bind_action('show_const', self.controller.toggle_show_constraints)
        
        if 'resize' in self.ui.buttons and 'world' in self.ui.inputs:
             self.ui_action_map[self.ui.buttons['resize']] = lambda: self.sim.resize_world(self.ui.inputs['world'].get_value(50.0))

    def handle_input(self):
        self.layout = self.controller.layout
        
        # Build UI list based on what is actually initialized in the UI Manager
        physics_elements = [
            self.ui.buttons.get('play'), self.ui.buttons.get('clear'), self.ui.buttons.get('reset'), 
            self.ui.buttons.get('undo'), self.ui.buttons.get('redo'),
            self.ui.buttons.get('thermostat'), self.ui.buttons.get('boundaries'),
            *self.ui.sliders.values()
        ]
        
        editor_elements = [
            self.ui.buttons.get('mode_ghost'), self.ui.buttons.get('atomize'), 
            self.ui.buttons.get('save_geo'), self.ui.buttons.get('discard_geo'), 
            self.ui.buttons.get('editor_play'), self.ui.buttons.get('show_const'),
            self.ui.buttons.get('resize'), self.ui.inputs.get('world'),
            self.ui.buttons.get('extend'),
            *self.ui.tools.values(), 
            *self.constraint_btn_map.keys()
        ]
        
        # Filter out None values (buttons that don't exist in this mode)
        ui_list = [el for el in physics_elements + editor_elements if el is not None]

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.controller.running = False
            elif event.type == pygame.VIDEORESIZE: self.controller.handle_resize(event.w, event.h)
            
            if self._handle_keys(event): continue
            
            tool_switched = False
            for btn, tid in self.tool_btn_map.items():
                if btn.handle_event(event): 
                    # Delegate tool change to controller to ensure consistent state update
                    self.controller.change_tool(tid)
                    tool_switched = True
            if tool_switched: continue

            if self._handle_menus(event): continue
            if self._handle_dialogs(event): continue

            ui_interacted = False
            for el in ui_list:
                if el.handle_event(event):
                    ui_interacted = True
                    if el in self.constraint_btn_map:
                        self.controller.trigger_constraint(self.constraint_btn_map[el])
                    elif el in self.ui_action_map:
                        self.ui_action_map[el]()
            
            mouse_on_ui = (event.type == pygame.MOUSEBUTTONDOWN and 
                          (event.pos[0] > self.layout['RIGHT_X'] or event.pos[0] < self.layout['LEFT_W'] or event.pos[1] < config.TOP_MENU_H))
            
            if not mouse_on_ui and not ui_interacted:
                self._handle_scene_mouse(event)

    def _handle_keys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.session.placing_geo_data:
                    self.session.placing_geo_data = None
                    self.session.set_status("Placement Cancelled")
                    return True
                if self.session.current_tool: self.session.current_tool.cancel()
                self.session.pending_constraint = None
                self.session.selected_walls.clear(); self.session.selected_points.clear()
                for btn in self.constraint_btn_map.keys(): btn.active = False
                self.session.set_status("Cancelled")
                return True
            if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if self.session.current_tool: self.session.current_tool.cancel()
                self.sim.undo(); self.session.set_status("Undo"); return True
            if event.key == pygame.K_y and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if self.session.current_tool: self.session.current_tool.cancel()
                self.sim.redo(); self.session.set_status("Redo"); return True
            if event.key == pygame.K_DELETE:
                if self.session.selected_walls:
                    for idx in sorted(list(self.session.selected_walls), reverse=True):
                        self.sim.remove_wall(idx)
                    self.session.selected_walls.clear()
                    self.sim.rebuild_static_atoms() 
        return False

    def _handle_menus(self, event):
        if self.ui.menu.handle_event(event): return True
        if event.type == pygame.MOUSEBUTTONDOWN and self.ui.menu.active_menu:
            if self.ui.menu.dropdown_rect and self.ui.menu.dropdown_rect.collidepoint(event.pos):
                rel_y = event.pos[1] - self.ui.menu.dropdown_rect.y - 5; idx = rel_y // 30
                opts = self.ui.menu.items[self.ui.menu.active_menu]
                if 0 <= idx < len(opts): self.controller._execute_menu(opts[idx])
            self.ui.menu.active_menu = None
            return True
        return False

    def _handle_dialogs(self, event):
        captured = False
        if self.controller.context_menu and self.controller.context_menu.handle_event(event):
            action = self.controller.context_menu.action
            ctx_vars = self.controller.ctx_vars
            
            if action == "Delete Constraint":
                if 0 <= ctx_vars['const'] < len(self.sim.constraints):
                    self.sim.snapshot(); self.sim.constraints.pop(ctx_vars['const']); self.sim.apply_constraints()
            elif action == "Set Angle...":
                val = simpledialog.askfloat("Set Angle", "Enter target angle (degrees):")
                if val is not None:
                    if 0 <= ctx_vars['const'] < len(self.sim.constraints):
                        self.sim.constraints[ctx_vars['const']].value = val
                        self.sim.apply_constraints()
            elif action == "Animate...":
                c = self.sim.constraints[ctx_vars['const']]
                driver = getattr(c, 'driver', None)
                self.controller.anim_dialog = AnimationDialog(self.layout['W']//2, self.layout['H']//2, driver)
            elif action == "Delete": 
                self.sim.remove_wall(ctx_vars['wall'])
                self.session.selected_walls.clear(); self.session.selected_points.clear()
            elif action == "Properties" or action == "Edit Material":
                idx = ctx_vars['wall']
                mat_id = getattr(self.sim.walls[idx], 'material_id', "Default")
                self.controller.prop_dialog = MaterialDialog(self.layout['W']//2, self.layout['H']//2, self.sim.sketch, mat_id)
            elif action == "Set Rotation...":
                anim = getattr(self.sim.walls[ctx_vars['wall']], 'anim', None)
                self.controller.rot_dialog = RotationDialog(self.layout['W']//2, self.layout['H']//2, anim)
            elif action == "Anchor": 
                self.sim.toggle_anchor(ctx_vars['wall'], ctx_vars['pt'])
            elif action == "Un-Anchor":
                self.sim.toggle_anchor(ctx_vars['wall'], ctx_vars['pt'])
            elif action == "Set Length...":
                val = simpledialog.askfloat("Set Length", "Enter target length:")
                if val: self.sim.add_constraint_object(Length(ctx_vars['wall'], val))
            self.controller.context_menu = None; captured = True

        if self.controller.prop_dialog and self.controller.prop_dialog.handle_event(event):
            if self.controller.prop_dialog.apply: 
                mat = self.controller.prop_dialog.get_result()
                self.sim.sketch.add_material(mat)
                self.sim.update_wall_props(self.controller.ctx_vars['wall'], {'material_id': mat.name})
                self.controller.prop_dialog.apply = False
            if self.controller.prop_dialog.done: self.controller.prop_dialog = None
            captured = True
            
        if self.controller.rot_dialog and self.controller.rot_dialog.handle_event(event):
            if self.controller.rot_dialog.apply: self.sim.set_wall_rotation(self.controller.ctx_vars['wall'], self.controller.rot_dialog.get_values()); self.controller.rot_dialog.apply = False
            if self.controller.rot_dialog.done: self.controller.rot_dialog = None
            captured = True
        if self.controller.anim_dialog and self.controller.anim_dialog.handle_event(event):
            if self.controller.anim_dialog.apply:
                self.sim.sketch.set_driver(self.controller.ctx_vars['const'], self.controller.anim_dialog.get_values())
                self.controller.anim_dialog.apply = False
            if self.controller.anim_dialog.done: self.controller.anim_dialog = None
            captured = True
        return captured

    def _handle_scene_mouse(self, event):
        if self.session.placing_geo_data:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    sx, sy = utils.screen_to_sim(mx, my, self.session.zoom, self.session.pan_x, self.session.pan_y, self.sim.world_size, self.layout)
                    if hasattr(self.sim.geo, 'place_geometry'):
                        self.sim.geo.place_geometry(self.session.placing_geo_data, sx, sy, current_time=self.session.geo_time)
                    self.session.placing_geo_data = None
                    self.session.set_status("Geometry Placed")
                elif event.button == 3:
                    self.session.placing_geo_data = None
                    self.session.set_status("Placement Cancelled")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            self.session.state = InteractionState.PANNING; self.session.last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            self.session.state = InteractionState.IDLE
        elif event.type == pygame.MOUSEMOTION and self.session.state == InteractionState.PANNING:
            self.session.pan_x += event.pos[0] - self.session.last_mouse_pos[0]; self.session.pan_y += event.pos[1] - self.session.last_mouse_pos[1]; self.session.last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            self.session.zoom = max(0.1, min(self.session.zoom * (1.1 if event.y > 0 else 0.9), 50.0))
        
        if self.session.current_tool:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.session.state == InteractionState.DRAGGING_GEOMETRY: self.session.current_tool.cancel()
                else: 
                    self.controller._spawn_context_menu(event.pos)
            else:
                self.session.current_tool.handle_event(event, self.layout)
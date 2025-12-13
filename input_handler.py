import pygame
import config
import utils
from ui_widgets import PropertiesDialog, RotationDialog, AnimationDialog, ContextMenu
from constraints import Length
from app_state import InteractionState
from tkinter import simpledialog

class InputHandler:
    def __init__(self, editor):
        self.editor = editor
        self.app = editor.app
        self.sim = editor.sim
        self.ui = editor.ui
        self.layout = editor.layout
        
        # Mappings
        self.tool_btn_map = {
            self.ui.tools['brush']: config.TOOL_BRUSH, self.ui.tools['select']: config.TOOL_SELECT,
            self.ui.tools['line']: config.TOOL_LINE, self.ui.tools['rect']: config.TOOL_RECT,
            self.ui.tools['circle']: config.TOOL_CIRCLE, self.ui.tools['point']: config.TOOL_POINT,
            self.ui.tools['ref']: config.TOOL_REF
        }
        
        self.constraint_btn_map = {
            self.ui.buttons['const_length']: 'LENGTH', self.ui.buttons['const_equal']: 'EQUAL',
            self.ui.buttons['const_parallel']: 'PARALLEL', self.ui.buttons['const_perp']: 'PERPENDICULAR',
            self.ui.buttons['const_coincident']: 'COINCIDENT', self.ui.buttons['const_collinear']: 'COLLINEAR',
            self.ui.buttons['const_midpoint']: 'MIDPOINT', self.ui.buttons['const_horiz']: 'HORIZONTAL',
            self.ui.buttons['const_vert']: 'VERTICAL', self.ui.buttons['const_angle']: 'ANGLE'
        }
        
        # Action Map
        self.ui_action_map = {
            self.ui.buttons['reset']: lambda: self.sim.reset_simulation(),
            self.ui.buttons['clear']: lambda: self.sim.clear_particles(),
            self.ui.buttons['undo']: lambda: (self.sim.undo(), self.app.set_status("Undo")),
            self.ui.buttons['redo']: lambda: (self.sim.redo(), self.app.set_status("Redo")),
            self.ui.buttons['resize']: lambda: self.sim.resize_world(self.ui.inputs['world'].get_value(50.0)),
            self.ui.buttons['discard_geo']: lambda: self.editor.exit_editor_mode(self.app.sim_backup_state),
            self.ui.buttons['save_geo']: self.editor.save_geo_dialog,
            self.ui.buttons['extend']: self.editor.toggle_extend,
            self.ui.buttons['editor_play']: self.editor.toggle_editor_play,
            self.ui.buttons['show_const']: self.editor.toggle_show_constraints,
            self.ui.buttons['tab_sim']: lambda: self.editor.switch_mode(config.MODE_SIM),
            self.ui.buttons['tab_edit']: lambda: self.editor.switch_mode(config.MODE_EDITOR)
        }

    def handle_input(self):
        # Refresh layout ref in case of resize
        self.layout = self.editor.layout
        
        # Build active UI list for hit testing
        sim_elements = [
            self.ui.buttons['play'], self.ui.buttons['clear'], self.ui.buttons['reset'], 
            self.ui.buttons['undo'], self.ui.buttons['redo'],
            self.ui.buttons['tab_sim'], self.ui.buttons['tab_edit'],
            *self.ui.sliders.values(), self.ui.buttons['thermostat'], self.ui.buttons['boundaries'],
            self.ui.tools['brush'], self.ui.tools['line'], self.ui.buttons['resize'],
            self.ui.inputs['world']
        ]
        editor_elements = [
            self.ui.buttons['save_geo'], self.ui.buttons['discard_geo'], 
            self.ui.buttons['undo'], self.ui.buttons['redo'], self.ui.buttons['clear'],
            self.ui.buttons['editor_play'], self.ui.buttons['show_const'],
            self.ui.buttons['tab_sim'], self.ui.buttons['tab_edit'],
            *self.ui.tools.values(), *self.constraint_btn_map.keys(), self.ui.buttons['extend']
        ]
        ui_list = sim_elements if self.app.mode == config.MODE_SIM else editor_elements

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.editor.running = False
            elif event.type == pygame.VIDEORESIZE: self.editor.handle_resize(event.w, event.h)
            
            if self._handle_keys(event): continue
            
            # Tool Switching
            tool_switched = False
            for btn, tid in self.tool_btn_map.items():
                if btn.handle_event(event): 
                    self.editor.change_tool(tid); tool_switched = True
            if tool_switched: continue

            if self._handle_menus(event): continue
            if self._handle_dialogs(event): continue

            # General UI
            ui_interacted = False
            for el in ui_list:
                if el.handle_event(event):
                    ui_interacted = True
                    if self.app.mode == config.MODE_EDITOR and el in self.constraint_btn_map:
                        self.editor.trigger_constraint(self.constraint_btn_map[el])
                    elif el in self.ui_action_map:
                        self.ui_action_map[el]()
            
            # Scene Interaction
            mouse_on_ui = (event.type == pygame.MOUSEBUTTONDOWN and 
                          (event.pos[0] > self.layout['RIGHT_X'] or event.pos[0] < self.layout['LEFT_W'] or event.pos[1] < config.TOP_MENU_H))
            
            if not mouse_on_ui and not ui_interacted:
                self._handle_scene_mouse(event)

    def _handle_keys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.app.placing_geo_data:
                    self.app.placing_geo_data = None
                    self.app.set_status("Placement Cancelled")
                    return True
                if self.app.current_tool: self.app.current_tool.cancel()
                self.app.pending_constraint = None
                self.app.selected_walls.clear(); self.app.selected_points.clear()
                for btn in self.constraint_btn_map.keys(): btn.active = False
                self.app.set_status("Cancelled")
                return True
            if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if self.app.current_tool: self.app.current_tool.cancel()
                self.sim.undo(); self.app.set_status("Undo"); return True
            if event.key == pygame.K_y and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                if self.app.current_tool: self.app.current_tool.cancel()
                self.sim.redo(); self.app.set_status("Redo"); return True
        return False

    def _handle_menus(self, event):
        if self.ui.menu.handle_event(event): return True
        if event.type == pygame.MOUSEBUTTONDOWN and self.ui.menu.active_menu:
            if self.ui.menu.dropdown_rect and self.ui.menu.dropdown_rect.collidepoint(event.pos):
                rel_y = event.pos[1] - self.ui.menu.dropdown_rect.y - 5; idx = rel_y // 30
                opts = self.ui.menu.items[self.ui.menu.active_menu]
                if 0 <= idx < len(opts): self.editor._execute_menu(opts[idx])
            self.ui.menu.active_menu = None
            return True
        return False

    def _handle_dialogs(self, event):
        captured = False
        if self.editor.context_menu and self.editor.context_menu.handle_event(event):
            action = self.editor.context_menu.action
            if action == "Delete Constraint":
                if 0 <= self.editor.ctx_vars['const'] < len(self.sim.constraints):
                    self.sim.snapshot(); self.sim.constraints.pop(self.editor.ctx_vars['const']); self.sim.apply_constraints()
            elif action == "Set Angle...":
                val = simpledialog.askfloat("Set Angle", "Enter target angle (degrees):")
                if val is not None:
                    if 0 <= self.editor.ctx_vars['const'] < len(self.sim.constraints):
                        self.sim.constraints[self.editor.ctx_vars['const']].value = val
                        self.sim.apply_constraints()
            elif action == "Animate...":
                c = self.sim.constraints[self.editor.ctx_vars['const']]
                driver = getattr(c, 'driver', None)
                self.editor.anim_dialog = AnimationDialog(self.layout['W']//2, self.layout['H']//2, driver)
            elif action == "Delete": 
                self.sim.remove_wall(self.editor.ctx_vars['wall']); self.app.selected_walls.clear(); self.app.selected_points.clear()
            elif action == "Properties":
                w_props = self.sim.walls[self.editor.ctx_vars['wall']].to_dict()
                self.editor.prop_dialog = PropertiesDialog(self.layout['W']//2, self.layout['H']//2, w_props)
            elif action == "Set Rotation...":
                self.editor.rot_dialog = RotationDialog(self.layout['W']//2, self.layout['H']//2, self.sim.walls[self.editor.ctx_vars['wall']].anim)
            elif action == "Anchor": self.sim.toggle_anchor(self.editor.ctx_vars['wall'], self.editor.ctx_vars['pt'])
            elif action == "Set Length...":
                val = simpledialog.askfloat("Set Length", "Enter target length:")
                if val: self.sim.add_constraint_object(Length(self.editor.ctx_vars['wall'], val))
            self.editor.context_menu = None; captured = True

        if self.editor.prop_dialog and self.editor.prop_dialog.handle_event(event):
            if self.editor.prop_dialog.apply: self.sim.update_wall_props(self.editor.ctx_vars['wall'], self.editor.prop_dialog.get_values()); self.editor.prop_dialog.apply = False
            if self.editor.prop_dialog.done: self.editor.prop_dialog = None
            captured = True
        if self.editor.rot_dialog and self.editor.rot_dialog.handle_event(event):
            if self.editor.rot_dialog.apply: self.sim.set_wall_rotation(self.editor.ctx_vars['wall'], self.editor.rot_dialog.get_values()); self.editor.rot_dialog.apply = False
            if self.editor.rot_dialog.done: self.editor.rot_dialog = None
            captured = True
        if self.editor.anim_dialog and self.editor.anim_dialog.handle_event(event):
            if self.editor.anim_dialog.apply:
                c = self.sim.constraints[self.editor.ctx_vars['const']]
                if self.editor.anim_dialog.get_values() is None:
                    if hasattr(c, 'driver'): del c.driver
                    c.base_value = None
                else:
                    c.driver = self.editor.anim_dialog.get_values()
                    if c.base_value is None: c.base_value = c.value 
                    if c.driver['type'] == 'lin': c.base_time = self.app.geo_time 
                self.editor.anim_dialog.apply = False
            if self.editor.anim_dialog.done: self.editor.anim_dialog = None
            captured = True
        return captured

    def _handle_scene_mouse(self, event):
        if self.app.placing_geo_data:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    sx, sy = utils.screen_to_sim(mx, my, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, self.layout)
                    self.sim.place_geometry(self.app.placing_geo_data, sx, sy, current_time=self.app.geo_time)
                    self.app.placing_geo_data = None
                    self.app.set_status("Geometry Placed")
                elif event.button == 3:
                    self.app.placing_geo_data = None
                    self.app.set_status("Placement Cancelled")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            self.app.state = InteractionState.PANNING; self.app.last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            self.app.state = InteractionState.IDLE
        elif event.type == pygame.MOUSEMOTION and self.app.state == InteractionState.PANNING:
            self.app.pan_x += event.pos[0] - self.app.last_mouse_pos[0]; self.app.pan_y += event.pos[1] - self.app.last_mouse_pos[1]; self.app.last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEWHEEL:
            self.app.zoom = max(0.1, min(self.app.zoom * (1.1 if event.y > 0 else 0.9), 50.0))
        
        if self.app.current_tool:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.app.state == InteractionState.DRAGGING_GEOMETRY: self.app.current_tool.cancel()
                else: self.editor._spawn_context_menu(event.pos)
            else:
                self.app.current_tool.handle_event(event, self.layout)
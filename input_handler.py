import pygame
import config
from session import InteractionState
from ui_widgets import MaterialDialog, RotationDialog, AnimationDialog
from constraints import Length, Angle, Coincident, Perpendicular, Parallel

class InputHandler:
    def __init__(self, app):
        self.app = app
        self.tool_btn_map = {
            app.ui.buttons['select']: config.TOOL_SELECT,
            app.ui.buttons['brush']: config.TOOL_BRUSH,
            app.ui.buttons['line']: config.TOOL_LINE,
            app.ui.buttons['rect']: config.TOOL_RECT,
            app.ui.buttons['circ']: config.TOOL_CIRCLE,
            app.ui.buttons['point']: config.TOOL_POINT,
            app.ui.buttons['ref']: config.TOOL_REF,
        }
        self.constraint_btn_map = {
            app.ui.buttons['c_coincident']: 'COINCIDENT',
            app.ui.buttons['c_parallel']: 'PARALLEL',
            app.ui.buttons['c_perp']: 'PERPENDICULAR',
            app.ui.buttons['c_horiz']: 'HORIZONTAL',
            app.ui.buttons['c_vert']: 'VERTICAL',
            app.ui.buttons['c_dist']: 'DISTANCE',
            app.ui.buttons['c_equal']: 'EQUAL_LENGTH',
            app.ui.buttons['c_fix']: 'FIXED',
        }

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.app.running = False
            
            # --- Global Hotkeys ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    if (pygame.key.get_mods() & pygame.KMOD_SHIFT): self.app.redo()
                    else: self.app.undo()
                elif event.key == pygame.K_DELETE:
                    # UPDATED: self.app.session
                    if self.app.session.selected_walls:
                        to_remove = sorted(list(self.app.session.selected_walls), reverse=True)
                        for idx in to_remove: self.app.remove_wall(idx)
                        self.app.session.selected_walls.clear()
                        self.app.session.set_status("Deleted Selection")
                elif event.key == pygame.K_ESCAPE:
                    if self.app.session.pending_constraint:
                        self.app.session.pending_constraint = None
                        self.app.session.pending_targets_walls.clear()
                        self.app.session.pending_targets_points.clear()
                        for btn in self.constraint_btn_map.keys(): btn.active = False
                        self.app.session.set_status("Constraint Cancelled")
                    elif self.app.session.current_tool:
                        self.app.session.current_tool.cancel()

            # --- Dialogs ---
            if self.app.prop_dialog:
                self.app.prop_dialog.handle_event(event)
                if not self.app.prop_dialog.active: self.app.prop_dialog = None
                continue
            if self.app.rot_dialog:
                self.app.rot_dialog.handle_event(event)
                if not self.app.rot_dialog.active: self.app.rot_dialog = None
                continue
            if self.app.anim_dialog:
                self.app.anim_dialog.handle_event(event)
                if not self.app.anim_dialog.active: self.app.anim_dialog = None
                continue

            # --- Context Menu ---
            if self.app.context_menu:
                res = self.app.context_menu.handle_event(event)
                if res is not None:
                    if res != -1: self._handle_context_action(res)
                    self.app.context_menu = None
                continue

            # --- UI Events ---
            if self.app.ui.handle_event(event, self.app):
                continue
                
            # --- Tool Events ---
            if self.app.session.current_tool:
                if self.app.session.current_tool.handle_event(event, self.app.layout):
                    continue

            # --- View Navigation (Pan/Zoom) ---
            self._handle_navigation(event)

            # --- Right Click (Context Menu) ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if self.app.session.state == InteractionState.IDLE:
                    self.app._spawn_context_menu(event.pos)

    def _handle_navigation(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2: # Middle Click
                self.app.session.state = InteractionState.PANNING
                self.app.session.last_mouse_pos = event.pos
            elif event.button == 4: # Wheel Up
                self._zoom(1.1, event.pos)
            elif event.button == 5: # Wheel Down
                self._zoom(1/1.1, event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.app.session.state = InteractionState.IDLE
        
        elif event.type == pygame.MOUSEMOTION:
            if self.app.session.state == InteractionState.PANNING:
                dx = event.pos[0] - self.app.session.last_mouse_pos[0]
                dy = event.pos[1] - self.app.session.last_mouse_pos[1]
                self.app.session.pan_x += dx
                self.app.session.pan_y += dy
                self.app.session.last_mouse_pos = event.pos

    def _zoom(self, factor, center):
        self.app.session.zoom *= factor
        self.app.session.pan_x = center[0] + (self.app.session.pan_x - center[0]) * factor
        self.app.session.pan_y = center[1] + (self.app.session.pan_y - center[1]) * factor

    def _handle_context_action(self, action):
        if action == "Properties":
            w_idx = self.app.ctx_vars['wall']
            if w_idx != -1:
                 w = self.app.sim.walls[w_idx]
                 current_mat = w.material_id
                 self.app.prop_dialog = MaterialDialog(self.app.layout['MID_X'] + 50, config.TOP_MENU_H + 50, 
                                                    callback=lambda vals: self.app.update_wall_props(w_idx, vals),
                                                    initial_mat=current_mat, 
                                                    initial_color=w.color)
        
        elif action == "Anchor":
             self.app.toggle_anchor(self.app.ctx_vars['wall'], self.app.ctx_vars['pt'])
        
        elif action == "Delete":
            if self.app.ctx_vars['const'] != -1:
                self.app.sim.snapshot()
                self.app.sim.constraints.pop(self.app.ctx_vars['const'])
                self.app.sim.rebuild_static_atoms()
            elif self.app.ctx_vars['wall'] != -1:
                self.app.remove_wall(self.app.ctx_vars['wall'])

        elif action == "Rotate...":
             self.app.rot_dialog = RotationDialog(self.app.layout['MID_X'] + 50, config.TOP_MENU_H + 50,
                                                  lambda vals: self.app.set_wall_rotation(self.app.ctx_vars['wall'], vals))

        elif action == "Animate...":
             pass
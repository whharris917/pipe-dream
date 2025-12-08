import pygame
import numpy as np
import math
import config
import utils
import time
from geometry import Line, Circle
from constraints import Coincident, Length
from app_state import InteractionState

class Tool:
    def __init__(self, app, sim, name="Tool"):
        self.app = app
        self.sim = sim
        self.name = name

    def activate(self):
        pass

    def deactivate(self):
        # Ensure we clear snap target when switching tools
        self.app.current_snap_target = None

    def handle_event(self, event, layout):
        """Returns True if the event was consumed by the tool."""
        return False

    def update(self):
        pass

    def draw_overlay(self, screen, renderer):
        pass
    
    def cancel(self):
        pass

class BrushTool(Tool):
    def __init__(self, app, sim):
        super().__init__(app, sim, "Brush")
        self.brush_radius = 2.0 

    def handle_event(self, event, layout):
        if self.app.mode != config.MODE_SIM: return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.app.state = InteractionState.PAINTING
                self.sim.snapshot()
                return True
            elif event.button == 3:
                self.app.state = InteractionState.PAINTING
                self.sim.snapshot()
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.app.state == InteractionState.PAINTING:
                self.app.state = InteractionState.IDLE
                return True
        
        return False

class GeometryTool(Tool):
    """Base class for tools that create geometry (Line, Rect, etc.)"""
    def __init__(self, app, sim, name):
        super().__init__(app, sim, name)
        self.dragging = False
        self.start_pos = None
        self.created_indices = [] 

    def get_world_pos(self, mx, my, layout):
        return utils.screen_to_sim(mx, my, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout)

    def get_snapped(self, mx, my, layout, anchor=None, exclude_idx=-1):
        return utils.get_snapped_pos(mx, my, self.sim, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout, anchor, exclude_idx)

    def cancel(self):
        if self.dragging:
            # Remove walls created during this drag in reverse order
            for _ in self.created_indices:
                if self.sim.walls:
                    self.sim.walls.pop()
            self.dragging = False
            self.created_indices = []
            self.sim.rebuild_static_atoms()
            self.app.set_status("Cancelled")
        self.app.current_snap_target = None # Clear visual feedback

    def _update_hover_snap(self, mx, my, layout):
        """Updates the snap target for visual feedback even when not dragging."""
        if not self.dragging:
            # Check for snap at current mouse position
            # We pass None as anchor since we aren't constraining to a start point yet
            _, _, snap = self.get_snapped(mx, my, layout, anchor=None)
            self.app.current_snap_target = snap

class LineTool(GeometryTool):
    def __init__(self, app, sim):
        super().__init__(app, sim, "Line")
        self.current_wall_idx = -1

    def handle_event(self, event, layout):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if layout['LEFT_X'] < mx < layout['RIGHT_X']:
                self.sim.snapshot()
                sx, sy, snap = self.get_snapped(mx, my, layout)
                
                is_ref = (self.name == "Ref Line") 
                
                self.sim.add_wall((sx, sy), (sx, sy), is_ref=is_ref)
                self.current_wall_idx = len(self.sim.walls) - 1
                self.created_indices = [self.current_wall_idx]
                self.dragging = True
                self.app.state = InteractionState.DRAGGING_GEOMETRY
                
                # Auto-Coincident start
                if snap and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.sim.add_constraint_object(Coincident(self.current_wall_idx, 0, snap[0], snap[1]))
                return True

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.dragging:
                if self.current_wall_idx < len(self.sim.walls):
                    w = self.sim.walls[self.current_wall_idx]
                    # Snap end point
                    sx, sy, snap = self.get_snapped(mx, my, layout, w.start, self.current_wall_idx)
                    
                    self.sim.update_wall(self.current_wall_idx, w.start, (sx, sy))
                    self.app.current_snap_target = snap 
                    
                    if self.app.mode == config.MODE_EDITOR:
                        self.sim.apply_constraints()
                return True
            else:
                # Hover logic: update snap indicator
                self._update_hover_snap(mx, my, layout)
                return False # Allow other hover effects (like cursor changes)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            # Finalize
            mx, my = event.pos
            if self.current_wall_idx < len(self.sim.walls):
                w = self.sim.walls[self.current_wall_idx]
                sx, sy, snap = self.get_snapped(mx, my, layout, w.start, self.current_wall_idx)
                
                # Auto-Coincident end
                if snap and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.sim.add_constraint_object(Coincident(self.current_wall_idx, 1, snap[0], snap[1]))
                
                # Auto-Axis Align (Shift)
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                     dx = abs(w.start[0] - w.end[0])
                     dy = abs(w.start[1] - w.end[1])
                     from constraints import Angle
                     if dy < 0.001: self.sim.add_constraint_object(Angle('HORIZONTAL', self.current_wall_idx))
                     elif dx < 0.001: self.sim.add_constraint_object(Angle('VERTICAL', self.current_wall_idx))

            self.dragging = False
            self.created_indices = []
            self.app.current_snap_target = None # Clear snap on finish
            self.app.state = InteractionState.IDLE
            self.sim.apply_constraints() # Ensure constraints are applied final time
            return True
            
        return False

class RectTool(GeometryTool):
    def __init__(self, app, sim):
        super().__init__(app, sim, "Rectangle")
        self.base_idx = -1
        self.rect_start_pos = None

    def handle_event(self, event, layout):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if layout['LEFT_X'] < mx < layout['RIGHT_X']:
                self.sim.snapshot()
                sx, sy, _ = self.get_snapped(mx, my, layout)
                self.rect_start_pos = (sx, sy)
                
                self.base_idx = len(self.sim.walls)
                # Create 4 lines
                for _ in range(4): self.sim.add_wall((sx, sy), (sx, sy))
                self.created_indices = [self.base_idx + i for i in range(4)]
                self.dragging = True
                self.app.state = InteractionState.DRAGGING_GEOMETRY
                return True

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.dragging:
                cur_x, cur_y = self.get_world_pos(mx, my, layout)
                sx, sy = self.rect_start_pos
                
                # Top
                self.sim.update_wall(self.base_idx, (sx, sy), (cur_x, sy))
                # Right
                self.sim.update_wall(self.base_idx+1, (cur_x, sy), (cur_x, cur_y))
                # Bottom
                self.sim.update_wall(self.base_idx+2, (cur_x, cur_y), (sx, cur_y))
                # Left
                self.sim.update_wall(self.base_idx+3, (sx, cur_y), (sx, sy))
                return True
            else:
                self._update_hover_snap(mx, my, layout)
                return False

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            # Apply constraints
            base = self.base_idx
            from constraints import Angle, Coincident
            self.sim.add_constraint_object(Coincident(base, 1, base+1, 0))
            self.sim.add_constraint_object(Coincident(base+1, 1, base+2, 0))
            self.sim.add_constraint_object(Coincident(base+2, 1, base+3, 0))
            self.sim.add_constraint_object(Coincident(base+3, 1, base, 0))
            self.sim.add_constraint_object(Angle('HORIZONTAL', base))
            self.sim.add_constraint_object(Angle('VERTICAL', base+1))
            self.sim.add_constraint_object(Angle('HORIZONTAL', base+2))
            self.sim.add_constraint_object(Angle('VERTICAL', base+3))
            
            self.sim.apply_constraints()
            self.dragging = False
            self.created_indices = []
            self.app.state = InteractionState.IDLE
            return True
        return False

class CircleTool(GeometryTool):
    def __init__(self, app, sim):
        super().__init__(app, sim, "Circle")
        self.circle_idx = -1

    def handle_event(self, event, layout):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if layout['LEFT_X'] < mx < layout['RIGHT_X']:
                self.sim.snapshot()
                sx, sy, snap = self.get_snapped(mx, my, layout) # Fix: Capture snap
                
                self.sim.add_circle((sx, sy), 0.1)
                self.circle_idx = len(self.sim.walls) - 1
                self.created_indices = [self.circle_idx]
                self.dragging = True
                self.app.state = InteractionState.DRAGGING_GEOMETRY
                
                # Auto-Coincident start
                if snap and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.sim.add_constraint_object(Coincident(self.circle_idx, 0, snap[0], snap[1]))
                return True

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.dragging:
                cur_x, cur_y = self.get_world_pos(mx, my, layout)
                if self.circle_idx < len(self.sim.walls):
                    c = self.sim.walls[self.circle_idx]
                    c.radius = max(0.1, math.hypot(cur_x - c.center[0], cur_y - c.center[1]))
                    self.sim.rebuild_static_atoms() 
                return True
            else:
                self._update_hover_snap(mx, my, layout)
                return False

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            self.created_indices = []
            self.app.state = InteractionState.IDLE
            self.app.current_snap_target = None
            return True
        return False

class PointTool(GeometryTool):
    def __init__(self, app, sim):
        super().__init__(app, sim, "Point")

    def handle_event(self, event, layout):
        if event.type == pygame.MOUSEMOTION:
            # Just update visual snap feedback
            mx, my = event.pos
            self._update_hover_snap(mx, my, layout)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if layout['LEFT_X'] < mx < layout['RIGHT_X']:
                self.sim.snapshot()
                sx, sy, snap = self.get_snapped(mx, my, layout)
                self.sim.add_wall((sx, sy), (sx, sy), is_ref=False)
                wall_idx = len(self.sim.walls)-1
                if snap and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.sim.add_constraint_object(Coincident(wall_idx, 0, snap[0], snap[1]))
                return True
        return False

class SelectTool(Tool):
    def __init__(self, app, sim):
        super().__init__(app, sim, "Select")
        self.mode = None 
        self.target_idx = -1
        self.target_pt = -1
        self.group_indices = []
        self.drag_start_mouse = (0, 0)
        
        # Double Click Handling
        self.last_click_time = 0.0
        self.last_click_pos = (0, 0)
        self.DOUBLE_CLICK_TIME = 0.3
        self.DOUBLE_CLICK_DIST = 5

    def handle_event(self, event, layout):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if layout['LEFT_X'] < mx < layout['RIGHT_X']:
                if event.button == 1: 
                    return self._handle_left_click(mx, my, layout)
        
        elif event.type == pygame.MOUSEMOTION:
            if self.mode:
                return self._handle_drag(event.pos, layout)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.mode:
                # Apply constraint if snapped during EDIT move
                if self.mode == 'EDIT' and self.app.current_snap_target:
                    # Prevent self-snap
                    if not (self.target_idx == self.app.current_snap_target[0] and self.target_pt == self.app.current_snap_target[1]):
                        c = Coincident(
                            self.target_idx, self.target_pt,
                            self.app.current_snap_target[0], self.app.current_snap_target[1]
                        )
                        self.sim.add_constraint_object(c)
                        self.app.set_status("Snapped & Connected")

                self.mode = None
                self.app.current_snap_target = None
                self.app.state = InteractionState.IDLE
                self.sim.apply_constraints()
                
                if self.app.temp_constraint_active:
                    self.sim.constraints = [c for c in self.sim.constraints if not c.temp]
                    self.app.temp_constraint_active = False
                return True
                
        return False

    def cancel(self):
        self.mode = None
        self.group_indices = []
        self.app.state = InteractionState.IDLE
        self.app.set_status("Move Cancelled")

    def _handle_left_click(self, mx, my, layout):
        now = time.time()
        is_double = False
        dist = math.hypot(mx - self.last_click_pos[0], my - self.last_click_pos[1])
        if (now - self.last_click_time < self.DOUBLE_CLICK_TIME) and (dist < self.DOUBLE_CLICK_DIST):
            is_double = True
        
        self.last_click_time = now
        self.last_click_pos = (mx, my)

        # 1. Check Points
        point_map = utils.get_grouped_points(self.sim, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout)
        hit_pt = self._hit_test_points(mx, my, point_map)
        
        if hit_pt:
            if hit_pt in self.app.selected_points:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self._select_point(hit_pt) # Toggle off
            else:
                self._select_point(hit_pt)

            self.mode = 'EDIT'
            self.target_idx = hit_pt[0]
            self.target_pt = hit_pt[1]
            self.sim.snapshot()
            self.app.state = InteractionState.DRAGGING_GEOMETRY
            return True
            
        # 2. Check Walls
        hit_wall = self._hit_test_walls(mx, my, layout)
        if hit_wall != -1:
            w = self.sim.walls[hit_wall]
            
            # --- Double Click Logic: Select Connected Group ---
            if is_double:
                group = utils.get_connected_group(self.sim, hit_wall)
                self.app.selected_walls.update(group)
                self.app.set_status("Group Selected")
                return True

            # --- Single Click Logic ---
            if hit_wall in self.app.selected_walls:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self._select_wall(hit_wall) # Toggle off
            else:
                self._select_wall(hit_wall)
            
            if isinstance(w, Circle):
                # Clicking circle perimeter -> RESIZE
                self.mode = 'RESIZE_CIRCLE'
                self.target_idx = hit_wall
                self.sim.snapshot()
                self.drag_start_mouse = (mx, my)
                self.app.state = InteractionState.DRAGGING_GEOMETRY
                return True
            
            # Line / Move Logic
            # Only MOVE_GROUP if fully selected
            target_group = utils.get_connected_group(self.sim, hit_wall)
            group_set = set(target_group)
            
            is_fully_selected = group_set.issubset(self.app.selected_walls)
            
            if is_fully_selected and not utils.is_group_anchored(self.sim, target_group):
                self.mode = 'MOVE_GROUP'
                self.group_indices = target_group
            else:
                self.mode = 'MOVE_WALL'
                self.target_idx = hit_wall
                if isinstance(w, Line) and self.app.mode == config.MODE_EDITOR:
                    l = np.linalg.norm(w.end - w.start)
                    c = Length(hit_wall, l); c.temp = True
                    self.sim.constraints.append(c)
                    self.app.temp_constraint_active = True
            
            self.sim.snapshot()
            self.drag_start_mouse = (mx, my)
            self.app.state = InteractionState.DRAGGING_GEOMETRY
            return True
            
        # 3. Clicked Empty -> Deselect
        if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
            self.app.selected_walls.clear()
            self.app.selected_points.clear()
        return True

    def _handle_drag(self, mouse_pos, layout):
        mx, my = mouse_pos
        curr_sim = utils.screen_to_sim(mx, my, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout)
        
        if self.mode == 'EDIT':
            if self.target_idx >= len(self.sim.walls): return False
            w = self.sim.walls[self.target_idx]
            if isinstance(w, Line):
                anchor = w.end if self.target_pt == 0 else w.start
                dest_x, dest_y, snap = utils.get_snapped_pos(mx, my, self.sim, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout, anchor, self.target_idx)
                
                self.app.current_snap_target = snap 
                if self.target_pt == 0: self.sim.update_wall(self.target_idx, (dest_x, dest_y), w.end)
                else: self.sim.update_wall(self.target_idx, w.start, (dest_x, dest_y))
            
            elif isinstance(w, Circle):
                dest_x, dest_y, snap = utils.get_snapped_pos(mx, my, self.sim, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout, None, self.target_idx)
                self.app.current_snap_target = snap
                self.sim.update_wall(self.target_idx, (dest_x, dest_y), None)
            
            if self.app.mode == config.MODE_EDITOR: self.sim.apply_constraints()
            return True

        elif self.mode == 'RESIZE_CIRCLE':
            w = self.sim.walls[self.target_idx]
            if isinstance(w, Circle):
                new_r = math.hypot(curr_sim[0] - w.center[0], curr_sim[1] - w.center[1])
                w.radius = max(0.1, new_r)
                self.sim.rebuild_static_atoms()
            return True

        elif self.mode in ['MOVE_WALL', 'MOVE_GROUP']:
            prev_sim = utils.screen_to_sim(self.drag_start_mouse[0], self.drag_start_mouse[1], self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout)
            dx = curr_sim[0] - prev_sim[0]
            dy = curr_sim[1] - prev_sim[1]
            self.drag_start_mouse = (mx, my)
            
            targets = self.group_indices if self.mode == 'MOVE_GROUP' else [self.target_idx]
            
            for idx in targets:
                if idx < len(self.sim.walls):
                    w = self.sim.walls[idx]
                    w.move(dx, dy) 
                    self.sim.rebuild_static_atoms()
            
            if self.app.mode == config.MODE_EDITOR:
                self.sim.apply_constraints()
            return True
            
        return False

    def _hit_test_points(self, mx, my, point_map):
        base_r, step_r = 5, 4
        for center_pos, items in point_map.items():
            dist = math.hypot(mx - center_pos[0], my - center_pos[1])
            max_r = base_r + (len(items) - 1) * step_r
            if dist <= max_r:
                if dist < base_r: return items[0]
                k = int((dist - base_r) / step_r) + 1
                if k < len(items): return items[k]
                return items[-1]
        return None

    def _hit_test_walls(self, mx, my, layout):
        sim_x, sim_y = utils.screen_to_sim(mx, my, self.app.zoom, self.app.pan_x, self.app.pan_y, self.sim.world_size, layout)
        rad_sim = 5.0 / (((layout['MID_W'] - 50) / self.sim.world_size) * self.app.zoom)
        
        for i, w in enumerate(self.sim.walls):
            if isinstance(w, Line):
                if np.array_equal(w.start, w.end): continue
                p1, p2 = w.start, w.end
                p3 = np.array([sim_x, sim_y])
                d_vec = p2-p1
                len_sq = np.dot(d_vec, d_vec)
                if len_sq == 0: dist = np.linalg.norm(p3-p1)
                else:
                    t = max(0, min(1, np.dot(p3-p1, d_vec)/len_sq))
                    proj = p1 + t*d_vec
                    dist = np.linalg.norm(p3-proj)
                if dist < rad_sim: return i
            elif isinstance(w, Circle):
                d = math.hypot(sim_x - w.center[0], sim_y - w.center[1])
                if abs(d - w.radius) < rad_sim: return i
        return -1

    def _select_point(self, pt_tuple):
        if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
            if pt_tuple not in self.app.selected_points:
                self.app.selected_walls.clear(); self.app.selected_points.clear()
        
        if pt_tuple in self.app.selected_points: self.app.selected_points.remove(pt_tuple)
        else: self.app.selected_points.add(pt_tuple)

    def _select_wall(self, wall_idx):
        if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
            if wall_idx not in self.app.selected_walls:
                self.app.selected_walls.clear(); self.app.selected_points.clear()
        
        if wall_idx in self.app.selected_walls: self.app.selected_walls.remove(wall_idx)
        else: self.app.selected_walls.add(wall_idx)
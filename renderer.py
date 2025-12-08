import pygame
import config
from utils import sim_to_screen, screen_to_sim, get_grouped_points, calculate_current_temp
from geometry import Line, Circle

class Renderer:
    def __init__(self, screen, font, big_font):
        self.screen = screen
        self.font = font
        self.big_font = big_font

    def draw_app(self, app, sim, layout, ui_list):
        self.screen.fill(config.BACKGROUND_COLOR)
        
        # 1. Draw Viewport & Grid
        self._draw_viewport(app, sim, layout)
        
        # 2. Draw Simulation Content
        if app.mode == config.MODE_SIM:
            self._draw_particles(app, sim, layout)
        else:
            self._draw_editor_guides(app, sim, layout)
            
        # 3. Draw Geometry (Walls/Shapes)
        self._draw_geometry(app, sim, layout)
        
        # 4. Draw Tool Overlays (Ghost shapes, etc)
        if app.current_tool:
            app.current_tool.draw_overlay(self.screen, self)
        
        # 5. Draw Editor Specifics (Points, Selection Highlights)
        if app.mode == config.MODE_EDITOR:
            self._draw_editor_overlays(app, sim, layout)
            
        # 6. Draw Placement Preview (if importing geometry)
        if app.placing_geo_data:
            self._draw_placement_preview(app, sim, layout)

        # 7. Draw Snapping Feedback (Green Dot) - NEW
        self._draw_snap_indicator(app, sim, layout)

        # 8. Draw UI Panels & Widgets
        self.screen.set_clip(None) # Reset clip to draw UI over everything
        self._draw_panels(layout)
        self._draw_stats(app, sim, layout)
        
        for el in ui_list:
            el.draw(self.screen, self.font)
            
        # 9. Draw Tool Specific UI
        if app.mode == config.MODE_SIM:
            self.screen.blit(self.font.render("World Size:", True, (200, 200, 200)), 
                             (layout['RIGHT_X'] + 15, app.input_world.rect.y + 4))
            app.input_world.draw(self.screen, self.font)

        # 10. Status Message
        self._draw_status(app, layout)

    def _draw_snap_indicator(self, app, sim, layout):
        if app.current_snap_target:
            # snap_target is (wall_idx, pt_idx)
            # Or creating new wall snap, stored as coordinate tuple sometimes?
            # utils.get_snapped_pos returns (x, y, snap_target_tuple)
            # The tool stores `app.current_snap_target` as the tuple (idx, pt)
            
            w_idx, pt_idx = app.current_snap_target
            if w_idx < len(sim.walls):
                ent = sim.walls[w_idx]
                pt_pos = ent.get_point(pt_idx)
                sx, sy = sim_to_screen(pt_pos[0], pt_pos[1], app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
                
                # Draw green indicator
                pygame.draw.circle(self.screen, (0, 255, 0), (sx, sy), 6)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), 8, 1)

    def _draw_viewport(self, app, sim, layout):
        sim_rect = pygame.Rect(layout['MID_X'], config.TOP_MENU_H, layout['MID_W'], layout['MID_H'])
        self.screen.set_clip(sim_rect)
        
        tl = sim_to_screen(0, 0, app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
        br = sim_to_screen(sim.world_size, sim.world_size, app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
        
        g_col = config.GRID_COLOR if app.mode == config.MODE_SIM else (50, 60, 50)
        pygame.draw.rect(self.screen, g_col, (tl[0], tl[1], br[0]-tl[0], br[1]-tl[1]), 2)

    def _draw_particles(self, app, sim, layout):
        for i in range(sim.count):
            sx, sy = sim_to_screen(sim.pos_x[i], sim.pos_y[i], app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
            # Simple cull check
            if layout['MID_X'] < sx < layout['RIGHT_X'] and config.TOP_MENU_H < sy < config.WINDOW_HEIGHT:
                is_stat = sim.is_static[i]
                col = config.COLOR_STATIC if is_stat else config.COLOR_DYNAMIC
                atom_sig = sim.atom_sigma[i]
                # Scale radius by zoom
                rad = max(2, int(atom_sig * config.PARTICLE_RADIUS_SCALE * ((layout['MID_W']-50)/sim.world_size) * app.zoom))
                pygame.draw.circle(self.screen, col, (sx, sy), rad)

    def _draw_editor_guides(self, app, sim, layout):
        # Draw Center Crosshair
        cx, cy = sim_to_screen(sim.world_size/2, sim.world_size/2, app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
        pygame.draw.line(self.screen, (50, 50, 50), (cx-10, cy), (cx+10, cy))
        pygame.draw.line(self.screen, (50, 50, 50), (cx, cy-10), (cx, cy+10))

    def _draw_geometry(self, app, sim, layout):
        transform = lambda x, y: sim_to_screen(x, y, app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
        for i, w in enumerate(sim.walls):
            if isinstance(w, Line) and w.start is not None and w.end is not None:
                # Avoid drawing zero length lines if they glitch
                pass 
            
            is_sel = (i in app.selected_walls)
            is_pend = (app.pending_constraint and i in app.pending_targets_walls)
            w.render(self.screen, transform, is_sel, is_pend)

    def _draw_editor_overlays(self, app, sim, layout):
        point_map = get_grouped_points(sim, app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
        anchored_points_draw_list = []
        base_r, step_r = 5, 4
        
        for center_pos, items in point_map.items():
            cx, cy = center_pos
            count = len(items)
            for k in range(count - 1, -1, -1):
                w_idx, pt_idx = items[k]
                radius = base_r + (k * step_r)
                
                color = (200, 200, 200) 
                if (w_idx, pt_idx) in app.selected_points: color = (0, 255, 255)
                elif app.pending_constraint and (w_idx, pt_idx) in app.pending_targets_points: color = (100, 255, 100)
                
                pygame.draw.circle(self.screen, (30,30,30), (cx, cy), radius)
                pygame.draw.circle(self.screen, color, (cx, cy), radius, 2)
                
                # Track anchors to draw red dot on top
                w = sim.walls[w_idx]
                if w.anchored[pt_idx]: anchored_points_draw_list.append((cx, cy))
        
        for pt in anchored_points_draw_list: 
            pygame.draw.circle(self.screen, (255, 50, 50), pt, 3)

    def _draw_placement_preview(self, app, sim, layout):
        mx, my = pygame.mouse.get_pos()
        if layout['LEFT_X'] < mx < layout['RIGHT_X']:
            sim_mx, sim_my = screen_to_sim(mx, my, app.zoom, app.pan_x, app.pan_y, sim.world_size, layout)
            zoom = app.zoom
            pan_x, pan_y = app.pan_x, app.pan_y
            
            for wd in app.placing_geo_data.get('walls', []):
                if wd['type'] == 'line':
                    ws = wd['start']; we = wd['end']
                    s1 = sim_to_screen(sim_mx + ws[0], sim_my + ws[1], zoom, pan_x, pan_y, sim.world_size, layout)
                    s2 = sim_to_screen(sim_mx + we[0], sim_my + we[1], zoom, pan_x, pan_y, sim.world_size, layout)
                    pygame.draw.line(self.screen, (100, 255, 100), s1, s2, 2)
                elif wd['type'] == 'circle':
                        wc = wd['center']; wr = wd['radius']
                        sc = sim_to_screen(sim_mx + wc[0], sim_my + wc[1], zoom, pan_x, pan_y, sim.world_size, layout)
                        pr = sim_to_screen(sim_mx + wc[0] + wr, sim_my + wc[1], zoom, pan_x, pan_y, sim.world_size, layout)
                        sr = abs(pr[0] - sc[0])
                        pygame.draw.circle(self.screen, (100, 255, 100), sc, int(sr), 2)

    def _draw_panels(self, layout):
        # Left Panel
        pygame.draw.rect(self.screen, config.PANEL_BG_COLOR, (0, config.TOP_MENU_H, layout['LEFT_W'], layout['H']))
        pygame.draw.line(self.screen, config.PANEL_BORDER_COLOR, (layout['LEFT_W'], config.TOP_MENU_H), (layout['LEFT_W'], layout['H']))
        
        # Right Panel
        pygame.draw.rect(self.screen, config.PANEL_BG_COLOR, (layout['RIGHT_X'], config.TOP_MENU_H, layout['RIGHT_W'], layout['H']))
        pygame.draw.line(self.screen, config.PANEL_BORDER_COLOR, (layout['RIGHT_X'], config.TOP_MENU_H), (layout['RIGHT_X'], layout['H']))
        
        # Right Header (Stats Area)
        pygame.draw.rect(self.screen, (40, 40, 45), (layout['RIGHT_X'], config.TOP_MENU_H, layout['RIGHT_W'], 90))
        pygame.draw.line(self.screen, config.PANEL_BORDER_COLOR, (layout['RIGHT_X'], config.TOP_MENU_H + 90), (layout['W'], config.TOP_MENU_H + 90))

    def _draw_stats(self, app, sim, layout):
        metric_x = layout['RIGHT_X'] + 15
        if app.mode == config.MODE_SIM:
            curr_t = calculate_current_temp(sim.vel_x, sim.vel_y, sim.count, config.ATOM_MASS)
            self.screen.blit(self.big_font.render(f"Particles: {sim.count}", True, (255, 255, 255)), (metric_x, config.TOP_MENU_H + 10))
            self.screen.blit(self.font.render(f"Pairs: {sim.pair_count} | T: {curr_t:.3f}", True, (180, 180, 180)), (metric_x, config.TOP_MENU_H + 40))
            fps = 0.0 # Placeholder or pass clock
            self.screen.blit(self.font.render(f"SPS: {int(sim.sps)}", True, (100, 255, 100)), (metric_x, config.TOP_MENU_H + 60))
        else:
            self.screen.blit(self.big_font.render("GEOMETRY EDITOR", True, (255, 200, 100)), (metric_x, config.TOP_MENU_H + 10))
            self.screen.blit(self.font.render(f"Entities: {len(sim.walls)}", True, (200, 200, 200)), (metric_x, config.TOP_MENU_H + 40))
            self.screen.blit(self.font.render(f"Constrs: {len(sim.constraints)}", True, (150, 150, 150)), (metric_x, config.TOP_MENU_H + 60))

    def _draw_status(self, app, layout):
        import time
        if time.time() - app.status_time < 3.0:
            status_surf = self.font.render(app.status_msg, True, (100, 255, 100))
            pygame.draw.rect(self.screen, (30,30,30), (layout['MID_X'] + 15, config.TOP_MENU_H + 10, status_surf.get_width()+10, 25), border_radius=5)
            self.screen.blit(status_surf, (layout['MID_X'] + 20, config.TOP_MENU_H + 15))
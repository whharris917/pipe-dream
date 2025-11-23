import pygame
import math
import config

class Renderer:
    def __init__(self, surface, cam):
        self.surface = surface
        self.cam = cam
        self.font = pygame.font.SysFont("Consolas", 14)
        self.ui_font = pygame.font.SysFont("Consolas", 16, bold=True)

    def _get_fluid_color(self, node):
        total_frac = sum(node.fluid.composition.values())
        if total_frac <= 0.001:
            base_rgb = config.C_FLUID 
        else:
            r, g, b = 0, 0, 0
            for chem, frac in node.fluid.composition.items():
                chem_color = config.FLUID_COLORS.get(chem, config.C_FLUID)
                r += chem_color[0] * frac; g += chem_color[1] * frac; b += chem_color[2] * frac
            r /= total_frac; g /= total_frac; b /= total_frac
            base_rgb = (int(r), int(g), int(b))

        pressure = node.pressure
        t = min(max(pressure / 100.0, 0.0), 1.0)
        start_c = config.C_PIPE_EMPTY
        end_c = base_rgb
        fin_r = int(start_c[0] + (end_c[0] - start_c[0]) * t)
        fin_g = int(start_c[1] + (end_c[1] - start_c[1]) * t)
        fin_b = int(start_c[2] + (end_c[2] - start_c[2]) * t)
        return (fin_r, fin_g, fin_b)

    def draw_grid(self):
        scaled_size = 40 * self.cam.zoom 
        start_x = (self.cam.offset_x % scaled_size) - scaled_size
        start_y = (self.cam.offset_y % scaled_size) - scaled_size
        for x in range(int(config.SCREEN_WIDTH / scaled_size) + 2):
            px = start_x + (x * scaled_size)
            pygame.draw.line(self.surface, config.C_GRID, (px, 0), (px, config.SCREEN_HEIGHT))
        for y in range(int(config.SCREEN_HEIGHT / scaled_size) + 2):
            py = start_y + (y * scaled_size)
            pygame.draw.line(self.surface, config.C_GRID, (0, py), (config.SCREEN_WIDTH, py))

    def draw_valve(self, node, x, y, size, angle=0, color=None):
        if color is None:
            if node: color = config.C_VALVE_OPEN if node.setting > 0.5 else config.C_VALVE_CLOSED
            else: color = config.C_VALVE_CLOSED
        pts = [(-size, -size/2), (-size, size/2), (size, -size/2), (size, size/2)]
        rot_pts = []
        cos_a = math.cos(angle); sin_a = math.sin(angle)
        for px, py in pts:
            rx = px * cos_a - py * sin_a; ry = px * sin_a + py * cos_a
            rot_pts.append((x + rx, y + ry))
        p_tl, p_bl, p_tr, p_br = rot_pts
        center = (x, y)
        pygame.draw.polygon(self.surface, color, [p_tl, p_bl, center])
        pygame.draw.polygon(self.surface, color, [p_tr, p_br, center])
        pygame.draw.polygon(self.surface, (255,255,255), [p_tl, p_bl, center], 1)
        pygame.draw.polygon(self.surface, (255,255,255), [p_tr, p_br, center], 1)

    def draw_valve_preview(self, world_pos, angle=0):
        sx, sy = self.cam.world_to_screen(world_pos[0], world_pos[1])
        size = 14 * self.cam.zoom
        self.draw_valve(None, sx, sy, size, angle, color=config.C_VALVE_HOVER)

    def draw_source(self, node, x, y, radius):
        mat_color = config.FLUID_COLORS.get(node.material_type, config.C_HIGHLIGHT)
        pygame.draw.circle(self.surface, mat_color, (x, y), radius)
        pygame.draw.circle(self.surface, (255,255,255), (x, y), radius * 0.3) 
        pygame.draw.circle(self.surface, (255,255,255), (x, y), radius, 2)    

    def draw_sink(self, node, x, y, size):
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (x, y)
        pygame.draw.rect(self.surface, config.C_SINK, rect)
        pygame.draw.rect(self.surface, (255,255,255), rect, 2)
        pygame.draw.line(self.surface, (255,255,255), rect.topleft, rect.bottomright, 2)
        pygame.draw.line(self.surface, (255,255,255), rect.topright, rect.bottomleft, 2)

    def draw_simulation(self, sim):
        line_width = max(2, int(4 * self.cam.zoom))
        for node in sim.nodes:
            sx, sy = self.cam.world_to_screen(node.x, node.y)
            for neighbor in node.connections:
                nsx, nsy = self.cam.world_to_screen(neighbor.x, neighbor.y)
                color = self._get_fluid_color(node) 
                pygame.draw.line(self.surface, color, (sx, sy), (nsx, nsy), line_width)

        for node in sim.nodes:
            sx, sy = self.cam.world_to_screen(node.x, node.y)
            if node.kind == 'source':
                self.draw_source(node, sx, sy, 15 * self.cam.zoom)
            elif node.kind == 'sink':
                self.draw_sink(node, sx, sy, 24 * self.cam.zoom)
            elif node.kind == 'valve':
                angle = 0
                if len(node.connections) >= 1:
                    n1 = node.connections[0]
                    dx = n1.x - node.x; dy = n1.y - node.y
                    angle = math.atan2(dy, dx)
                self.draw_valve(node, sx, sy, 14 * self.cam.zoom, angle)

    def draw_preview_line(self, start_node, end_screen_pos):
        sx, sy = self.cam.world_to_screen(start_node.x, start_node.y)
        pygame.draw.line(self.surface, config.C_PREVIEW, (sx, sy), end_screen_pos, 2)
    
    def draw_snap_indicator(self, world_pos):
        sx, sy = self.cam.world_to_screen(world_pos[0], world_pos[1])
        pygame.draw.circle(self.surface, config.C_PREVIEW, (sx, sy), 8, 2)
        pygame.draw.circle(self.surface, config.C_HIGHLIGHT, (sx, sy), 3)
        
    def draw_ui(self, mouse_world_pos):
        txt = self.font.render(f"POS: {int(mouse_world_pos[0])}, {int(mouse_world_pos[1])}", True, config.C_HIGHLIGHT)
        self.surface.blit(txt, (10, 10))

    def draw_telemetry(self, node, mouse_screen_pos):
        if not node: return
        box_w, box_h = 180, 110
        x, y = mouse_screen_pos[0] + 15, mouse_screen_pos[1] + 15
        if x + box_w > config.SCREEN_WIDTH: x -= box_w + 30
        if y + box_h > config.SCREEN_HEIGHT: y -= box_h + 30
        
        rect = (x, y, box_w, box_h)
        pygame.draw.rect(self.surface, (20, 20, 25), rect)
        pygame.draw.rect(self.surface, config.C_HIGHLIGHT, rect, 1)
        
        comp_str = ""
        if node.fluid.composition:
            sorted_comp = sorted(node.fluid.composition.items(), key=lambda item: item[1], reverse=True)
            top_chem, top_frac = sorted_comp[0]
            comp_str = f"{top_chem} {int(top_frac*100)}%"
            if len(sorted_comp) > 1: comp_str += "..."

        lines = [
            f"TYPE: {node.kind.upper()}",
            f"MAT:  {node.material_type}" if node.kind == 'source' else "",
            f"PRESS: {node.pressure:.1f} kPa",
            f"MASS:  {node.fluid.mass:.2f} kg",
            f"COMP:  {comp_str}"
        ]
        
        curr_y = y + 10
        for line in lines:
            if not line: continue
            txt = self.font.render(line, True, config.C_TEXT)
            self.surface.blit(txt, (x + 10, curr_y))
            curr_y += 20

    def draw_toolbar(self, buttons, current_mode, mouse_pos, active_material):
        rect = (0, config.SCREEN_HEIGHT - config.TOOLBAR_HEIGHT, config.SCREEN_WIDTH, config.TOOLBAR_HEIGHT)
        pygame.draw.rect(self.surface, config.C_UI_BG, rect)
        pygame.draw.line(self.surface, config.C_HIGHLIGHT, (0, rect[1]), (config.SCREEN_WIDTH, rect[1]), 2)

        for btn in buttons:
            color = config.C_BUTTON_IDLE
            if btn['mode'] == current_mode:
                color = config.C_BUTTON_ACTIVE
            elif btn['rect'].collidepoint(mouse_pos):
                color = config.C_BUTTON_HOVER
            
            pygame.draw.rect(self.surface, color, btn['rect'], border_radius=4)
            pygame.draw.rect(self.surface, (0,0,0), btn['rect'], 1, border_radius=4)
            
            label = btn['label']
            if btn['mode'] == 'source' and current_mode == 'source':
                label = f"SOURCE ({active_material[0]})" 

            text_color = (0,0,0) if btn['mode'] == current_mode else config.C_BUTTON_TEXT
            txt = self.ui_font.render(label, True, text_color)
            text_rect = txt.get_rect(center=btn['rect'].center)
            self.surface.blit(txt, text_rect)
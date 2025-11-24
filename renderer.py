import pygame
import math
import config

class Renderer:
    def __init__(self, surface, cam):
        self.surface = surface
        self.cam = cam
        self.font = pygame.font.SysFont("Consolas", 14)
        self.ui_font = pygame.font.SysFont("Consolas", 16, bold=True)

    def _get_color_from_comp(self, fluid):
        total_frac = sum(fluid.composition.values())
        if total_frac <= 0.001 or fluid.mass <= 0.001:
            return config.C_PIPE_EMPTY
        
        r, g, b = 0, 0, 0
        for chem, frac in fluid.composition.items():
            chem_color = config.FLUID_COLORS.get(chem, config.C_FLUID)
            r += chem_color[0] * frac
            g += chem_color[1] * frac
            b += chem_color[2] * frac
        
        r /= total_frac
        g /= total_frac
        b /= total_frac
        
        return (int(r), int(g), int(b))

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

    def draw_valve(self, node, x, y, size, angle=0):
        color = config.C_VALVE_OPEN if node.setting > 0.5 else config.C_VALVE_CLOSED
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

    def draw_simulation(self, sim):
        line_width = max(2, int(6 * self.cam.zoom))
        
        # 1. Draw Pipes
        for pipe in sim.pipes:
            start_pos = (pipe.start_node.x, pipe.start_node.y)
            end_pos = (pipe.end_node.x, pipe.end_node.y)
            
            sx, sy = self.cam.world_to_screen(*start_pos)
            ex, ey = self.cam.world_to_screen(*end_pos)
            
            # Draw Background Pipe
            pygame.draw.line(self.surface, config.C_PIPE_EMPTY, (sx, sy), (ex, ey), line_width)
            
            # Draw Fluid Segments (The FIFO Array)
            num_cells = len(pipe.cells)
            dx = (ex - sx) / num_cells
            dy = (ey - sy) / num_cells
            
            for i, cell in enumerate(pipe.cells):
                color = self._get_color_from_comp(cell)
                if color != config.C_PIPE_EMPTY:
                    # Calculate segment points
                    p1x = sx + dx * i
                    p1y = sy + dy * i
                    p2x = sx + dx * (i+1)
                    p2y = sy + dy * (i+1)
                    # Overlap slightly to prevent cracks
                    pygame.draw.line(self.surface, color, (p1x, p1y), (p2x, p2y), line_width)

        # 2. Draw Junctions/Nodes
        for node in sim.junctions:
            sx, sy = self.cam.world_to_screen(node.x, node.y)
            
            if node.kind == 'source':
                self.draw_source(node, sx, sy, 15 * self.cam.zoom)
            elif node.kind == 'sink':
                self.draw_sink(node, sx, sy, 24 * self.cam.zoom)
            elif node.kind == 'valve':
                # Determine Angle
                angle = 0
                if node.pipes:
                    p = node.pipes[0]
                    other = p.end_node if p.start_node == node else p.start_node
                    dx = other.x - node.x
                    dy = other.y - node.y
                    angle = math.atan2(dy, dx)
                self.draw_valve(node, sx, sy, 14 * self.cam.zoom, angle)

    def draw_preview_line(self, start_node, end_screen_pos):
        sx, sy = self.cam.world_to_screen(start_node.x, start_node.y)
        pygame.draw.line(self.surface, config.C_PREVIEW, (sx, sy), end_screen_pos, 2)
    
    def draw_snap_indicator(self, world_pos):
        sx, sy = self.cam.world_to_screen(world_pos[0], world_pos[1])
        pygame.draw.circle(self.surface, config.C_PREVIEW, (sx, sy), 8, 2)
        
    def draw_ui(self, mouse_world_pos):
        txt = self.font.render(f"POS: {int(mouse_world_pos[0])}, {int(mouse_world_pos[1])}", True, config.C_HIGHLIGHT)
        self.surface.blit(txt, (10, 10))

    def draw_inspector_tooltip(self, target, mouse_screen_pos):
        # Handle both Node and Pipe inspection
        lines = []
        
        # Check if it's a Node or a Pipe object
        if hasattr(target, 'pressure'): # It's a Node/Junction
            lines.append(f"TYPE: {target.kind.upper()}")
            lines.append(f"PRESS: {target.pressure:.1f} kPa")
            if target.kind == 'source':
                lines.append(f"MAT: {target.material_type}")
        elif hasattr(target, 'flow_rate'): # It's a Pipe
            lines.append("TYPE: PIPE")
            # Unit Conversion: m^3/s -> L/s
            flow_lps = target.flow_rate * 1000.0
            lines.append(f"FLOW: {flow_lps:.2f} L/s")
            full_cells = sum(1 for c in target.cells if c.mass > 0.001)
            lines.append(f"FILL: {int(full_cells/len(target.cells)*100)}%")

        # Draw Box
        box_w, box_h = 200, 20 + len(lines)*20
        x, y = mouse_screen_pos[0] + 20, mouse_screen_pos[1] + 20
        
        pygame.draw.rect(self.surface, (20, 20, 30), (x, y, box_w, box_h))
        pygame.draw.rect(self.surface, config.C_HIGHLIGHT, (x, y, box_w, box_h), 2)
        
        curr_y = y + 10
        for line in lines:
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
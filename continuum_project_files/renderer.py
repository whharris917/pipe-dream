import pygame
import math
import config
import random

class Renderer:
    def __init__(self, surface, cam):
        self.surface = surface
        self.cam = cam
        self.font = pygame.font.SysFont("Consolas", 14)
        self.ui_font = pygame.font.SysFont("Consolas", 16, bold=True)

    def _get_fluid_color(self, node):
        # 1. Get Base Color from Composition
        total_frac = sum(node.fluid.composition.values())
        
        if total_frac <= 0.001:
            return config.C_PIPE_EMPTY
        
        r, g, b = 0, 0, 0
        for chem, frac in node.fluid.composition.items():
            chem_color = config.FLUID_COLORS.get(chem, config.C_FLUID)
            r += chem_color[0] * frac; g += chem_color[1] * frac; b += chem_color[2] * frac
        r /= total_frac; g /= total_frac; b /= total_frac
        base_rgb = (int(r), int(g), int(b))

        # 2. Return base RGB (Intensity is now handled by dot density)
        return base_rgb

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
        particle_radius = max(1, int(1.5 * self.cam.zoom))
        
        # VISUAL CONFIGURATION
        # How many dots represent a "full" pipe segment?
        # Adjust this to make the swarm look denser or sparser.
        DOTS_PER_FULL_SEGMENT = 25 
        
        # PASS 1: Draw Pipe Skeleton (Empty Gray Lines)
        for node in sim.nodes:
            sx, sy = self.cam.world_to_screen(node.x, node.y)
            for neighbor in node.connections:
                nsx, nsy = self.cam.world_to_screen(neighbor.x, neighbor.y)
                pygame.draw.line(self.surface, config.C_PIPE_EMPTY, (sx, sy), (nsx, nsy), line_width)

        # PASS 2: Draw Fluid as "Random Walker" Dots
        for node in sim.nodes:
            # Skip empty nodes
            if node.current_volume <= 0.0001: continue
            
            sx, sy = self.cam.world_to_screen(node.x, node.y)
            color = self._get_fluid_color(node)
            
            # Calculate number of particles based on volume/capacity ratio
            # Over-pressurized nodes (volume > capacity) will get extra dots
            fill_ratio = node.current_volume / node.volume_capacity
            num_dots = int(fill_ratio * DOTS_PER_FULL_SEGMENT)
            
            if num_dots < 1 and node.current_volume > 0: num_dots = 1
            
            connections = node.connections
            
            # If solitary node (no connections), draw at center
            if not connections:
                pygame.draw.circle(self.surface, color, (int(sx), int(sy)), particle_radius)
                continue
                
            # Distribute dots among the connections
            # We draw dots on the "half-pipe" belonging to this node
            dots_per_conn = num_dots // len(connections)
            remainder = num_dots % len(connections)
            
            for i, neighbor in enumerate(connections):
                count = dots_per_conn + (1 if i < remainder else 0)
                if count <= 0: continue
                
                nsx, nsy = self.cam.world_to_screen(neighbor.x, neighbor.y)
                
                # Vector to Midpoint
                mx = (sx + nsx) / 2
                my = (sy + nsy) / 2
                vx = mx - sx
                vy = my - sy
                
                # Perpendicular Vector for width jitter
                length = math.hypot(vx, vy)
                if length < 0.1: px, py = 0, 0
                else: px, py = -vy/length, vx/length
                
                # Scatter dots
                for _ in range(count):
                    # Random position along the length (0.0 to 1.0)
                    t = random.random()
                    
                    # Random jitter across the width (-0.5 to 0.5)
                    # We keep it slightly inside the pipe walls (0.8 factor)
                    jitter = (random.random() - 0.5) * line_width * 0.8
                    
                    dot_x = sx + vx * t + px * jitter
                    dot_y = sy + vy * t + py * jitter
                    
                    pygame.draw.circle(self.surface, color, (int(dot_x), int(dot_y)), particle_radius)

        # PASS 3: Draw Components
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

    def draw_inspector_tooltip(self, node, mouse_screen_pos, world_pos=None):
        """
        Draws the detailed engineering inspector.
        Highlights the specific segment being inspected.
        """
        if not node: return
        
        # --- HIGHLIGHT THE SEGMENT ---
        line_width = max(4, int(6 * self.cam.zoom)) 
        sx, sy = self.cam.world_to_screen(node.x, node.y)
        
        for neighbor in node.connections:
            nsx, nsy = self.cam.world_to_screen(neighbor.x, neighbor.y)
            pygame.draw.line(self.surface, config.C_HIGHLIGHT, (sx, sy), (nsx, nsy), line_width)

        # --- TOOLTIP BOX ---
        box_w, box_h = 240, 140 
        x, y = mouse_screen_pos[0] + 20, mouse_screen_pos[1] + 20
        if x + box_w > config.SCREEN_WIDTH: x -= box_w + 40
        if y + box_h > config.SCREEN_HEIGHT: y -= box_h + 40
        
        rect = (x, y, box_w, box_h)
        pygame.draw.rect(self.surface, (10, 15, 20), rect)
        pygame.draw.rect(self.surface, config.C_HIGHLIGHT, rect, 2)
        
        flow_rate_lps = abs(node.last_velocity) * config.PIPE_AREA_M2 * 1000.0
        
        # In the new model, Pressure = Crowding %
        display_pressure = node.pressure 
        pressure_label = f"CROWDING: {int(display_pressure)}%"

        comp_lines = []
        if node.fluid.composition:
            sorted_comp = sorted(node.fluid.composition.items(), key=lambda item: item[1], reverse=True)
            for chem, frac in sorted_comp:
                if frac > 0.01: 
                    comp_lines.append(f"  {chem}: {int(frac*100)}%")
        else:
            comp_lines.append("  Empty")

        lines = [
            f"NODE: {node.kind.upper()}",
            f"FLOW: {flow_rate_lps:,.1f} L/s",
            pressure_label,
            "COMPOSITION:"
        ] + comp_lines
        
        curr_y = y + 12
        for i, line in enumerate(lines):
            color = config.C_TEXT
            if i == 0: color = config.C_HIGHLIGHT
            txt = self.font.render(line, True, color)
            self.surface.blit(txt, (x + 12, curr_y))
            curr_y += 20
            
        # --- DRAW POINTER TRIANGLE ---
        if world_pos:
            wsx, wsy = self.cam.world_to_screen(world_pos[0], world_pos[1])
            box_cx = x + box_w / 2
            box_cy = y + box_h / 2
            dx = wsx - box_cx
            dy = wsy - box_cy
            angle = math.atan2(dy, dx)
            
            tip = (wsx, wsy)
            size = 12
            base_x = math.cos(angle) * size
            base_y = math.sin(angle) * size
            perp_x = -base_y * 0.5
            perp_y = base_x * 0.5
            back_x = wsx - base_x
            back_y = wsy - base_y
            
            p1 = (back_x + perp_x, back_y + perp_y)
            p2 = (back_x - perp_x, back_y - perp_y)
            
            pygame.draw.polygon(self.surface, config.C_HIGHLIGHT, [tip, p1, p2])

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
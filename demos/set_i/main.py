import pygame
import numpy as np
import config
import math
from simulation_state import Simulation
from ui_widgets import SmartSlider, Button, InputField

# --- Layout Constants ---
LEFT_X = 0
LEFT_W = config.PANEL_LEFT_WIDTH

RIGHT_W = config.PANEL_RIGHT_WIDTH
RIGHT_X = config.WINDOW_WIDTH - RIGHT_W

MID_X = LEFT_W
MID_W = config.WINDOW_WIDTH - LEFT_W - RIGHT_W
MID_H = config.WINDOW_HEIGHT

# Coordinate transforms now relative to the Middle Panel
def sim_to_screen(x, y, zoom, pan_x, pan_y, world_size):
    # Center relative to World
    cx_world = world_size / 2.0
    cy_world = world_size / 2.0
    
    # Center relative to Middle Panel Screen Area
    cx_screen = MID_X + (MID_W / 2.0)
    cy_screen = MID_H / 2.0
    
    # Base scale fits world into the middle panel (with padding)
    base_scale = (MID_W - 50) / world_size
    final_scale = base_scale * zoom
    
    sx = cx_screen + (x - cx_world) * final_scale + pan_x
    sy = cy_screen + (y - cy_world) * final_scale + pan_y
    return int(sx), int(sy)

def screen_to_sim(sx, sy, zoom, pan_x, pan_y, world_size):
    cx_world = world_size / 2.0
    cy_world = world_size / 2.0
    
    cx_screen = MID_X + (MID_W / 2.0)
    cy_screen = MID_H / 2.0
    
    base_scale = (MID_W - 50) / world_size
    final_scale = base_scale * zoom
    
    x = (sx - pan_x - cx_screen) / final_scale + cx_world
    y = (sy - pan_y - cy_screen) / final_scale + cy_world
    return x, y

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    pygame.display.set_caption("Fast MD - Panel Layout")
    font = pygame.font.SysFont("consolas", 14)
    big_font = pygame.font.SysFont("consolas", 20)
    clock = pygame.time.Clock()
    
    sim = Simulation()
    
    # --- UI INITIALIZATION ---
    ui_elements = []
    
    # Right Panel Layout Helper
    rp_margin = 15
    rp_curr_y = 20
    rp_width = RIGHT_W - 2 * rp_margin
    rp_start_x = RIGHT_X + rp_margin
    
    # 1. Metrics Section (Placeholder for text)
    rp_curr_y += 100 # Leave space for the text metrics
    
    # 2. Controls Section
    btn_play = Button(rp_start_x, rp_curr_y, rp_width, 40, "PLAY / PAUSE", active=False, color_active=(50, 200, 50), color_inactive=(200, 50, 50))
    ui_elements.append(btn_play)
    rp_curr_y += 55
    
    # Sliders
    # Params: x, y, w, min, max, init, label, hard_min, hard_max
    slider_gravity = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.0, 50.0, config.DEFAULT_GRAVITY, "Gravity", hard_min=0.0)
    rp_curr_y += 60
    slider_temp = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.0, 5.0, 0.5, "Temperature", hard_min=0.0)
    rp_curr_y += 60
    slider_damping = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.90, 1.0, config.DEFAULT_DAMPING, "Damping", hard_min=0.0, hard_max=1.0)
    rp_curr_y += 60
    slider_sigma = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.5, 2.0, config.ATOM_SIGMA, "Sigma (Size)", hard_min=0.1)
    rp_curr_y += 60
    slider_epsilon = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.1, 5.0, config.ATOM_EPSILON, "Epsilon (Strength)", hard_min=0.0)
    rp_curr_y += 60
    slider_M = SmartSlider(rp_start_x, rp_curr_y, rp_width, 1.0, 100.0, float(config.DEFAULT_DRAW_M), "Speed (Steps/Frame)", hard_min=1.0)
    rp_curr_y += 60
    
    ui_elements.extend([slider_gravity, slider_temp, slider_damping, slider_sigma, slider_epsilon, slider_M])
    
    # Toggles Row
    btn_w = (rp_width - 10) // 2
    btn_thermostat = Button(rp_start_x, rp_curr_y, btn_w, 30, "Thermostat", active=False)
    btn_boundaries = Button(rp_start_x + btn_w + 10, rp_curr_y, btn_w, 30, "Bounds", active=False)
    ui_elements.extend([btn_thermostat, btn_boundaries])
    rp_curr_y += 40
    
    # Tools Row
    btn_tool_brush = Button(rp_start_x, rp_curr_y, btn_w, 30, "Brush", active=True, toggle=False)
    btn_tool_wall = Button(rp_start_x + btn_w + 10, rp_curr_y, btn_w, 30, "Wall", active=False, toggle=False)
    ui_elements.extend([btn_tool_brush, btn_tool_wall])
    rp_curr_y += 40
    
    slider_brush_size = SmartSlider(rp_start_x, rp_curr_y, rp_width, 1.0, 10.0, 2.0, "Brush Radius", hard_min=0.5)
    ui_elements.append(slider_brush_size)
    rp_curr_y += 60
    
    # World Control
    lbl_resize = font.render("World Size:", True, (200, 200, 200))
    input_world = InputField(rp_start_x + 80, rp_curr_y, 60, 25, str(config.DEFAULT_WORLD_SIZE))
    btn_resize = Button(rp_start_x + 150, rp_curr_y, rp_width - 150, 25, "Resize & Restart", active=False, toggle=False)
    ui_elements.append(btn_resize) # Input handled separately
    rp_curr_y += 40
    
    # Reset Row
    btn_clear = Button(rp_start_x, rp_curr_y, btn_w, 30, "Clear", active=False, toggle=False, color_inactive=(120, 60, 60))
    btn_reset = Button(rp_start_x + btn_w + 10, rp_curr_y, btn_w, 30, "Reset All", active=False, toggle=False, color_inactive=(150, 50, 50))
    ui_elements.extend([btn_clear, btn_reset])
    
    # --- STATE ---
    current_tool = 0 # 0=Brush, 1=Wall
    zoom = 1.0
    pan_x = 0.0
    pan_y = 0.0
    is_panning = False
    last_mouse_pos = (0, 0)
    
    is_painting = False
    is_erasing = False
    
    wall_mode = None
    wall_idx = -1
    wall_pt = -1
    
    running = True
    while running:
        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            # 1. UI Interaction
            # Check if mouse is in Right Panel
            mouse_in_ui = (event.type == pygame.MOUSEBUTTONDOWN and event.pos[0] > RIGHT_X)
            
            ui_captured = False
            for el in ui_elements:
                if el.handle_event(event): ui_captured = True
            if input_world.handle_event(event): ui_captured = True
            
            if mouse_in_ui or ui_captured:
                # Logic Hooks
                if btn_reset.clicked:
                    sim.reset_simulation()
                    input_world.set_value(config.DEFAULT_WORLD_SIZE)
                    # Reset sliders visual state
                    slider_gravity.reset(config.DEFAULT_GRAVITY, 0.0, 50.0)
                    slider_temp.reset(0.5, 0.0, 5.0)
                    slider_damping.reset(config.DEFAULT_DAMPING, 0.9, 1.0)
                    slider_sigma.reset(config.ATOM_SIGMA, 0.5, 2.0)
                    slider_epsilon.reset(config.ATOM_EPSILON, 0.1, 5.0)
                    btn_thermostat.active = False
                    btn_boundaries.active = False
                    zoom = 1.0; pan_x = 0; pan_y = 0
                    
                if btn_clear.clicked: sim.clear_particles()
                
                if btn_resize.clicked:
                    sim.resize_world(input_world.get_value(50.0))
                    zoom = 1.0; pan_x = 0; pan_y = 0
                
                # Tool Logic
                if btn_tool_brush.active and current_tool != 0:
                    current_tool = 0; btn_tool_wall.active = False
                elif btn_tool_wall.active and current_tool != 1:
                    current_tool = 1; btn_tool_brush.active = False
                if not btn_tool_brush.active and not btn_tool_wall.active:
                    if current_tool == 0: btn_tool_brush.active = True
                    else: btn_tool_wall.active = True
                
                continue # Skip world interaction if UI hit

            # 2. World Interaction (Middle Panel)
            # Only process if mouse x < RIGHT_X
            if event.type == pygame.MOUSEWHEEL:
                factor = 1.1 if event.y > 0 else 0.9
                zoom = max(0.1, min(zoom * factor, 50.0))
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2: # Pan
                    is_panning = True
                    last_mouse_pos = event.pos
                elif event.button == 3: # Erase
                    is_erasing = True
                elif event.button == 1: # Action
                    mx, my = event.pos
                    # Only act if in middle panel
                    if LEFT_X < mx < RIGHT_X:
                        sim_x, sim_y = screen_to_sim(mx, my, zoom, pan_x, pan_y, sim.world_size)
                        
                        if current_tool == 0: # Brush
                            is_painting = True
                        elif current_tool == 1: # Wall
                            # Check existing
                            hit = -1; endp = -1
                            rad = 5.0 / zoom
                            for i, w in enumerate(sim.walls):
                                if math.hypot(w['start'][0]-sim_x, w['start'][1]-sim_y) < rad:
                                    hit=i; endp=0; break
                                if math.hypot(w['end'][0]-sim_x, w['end'][1]-sim_y) < rad:
                                    hit=i; endp=1; break
                            
                            if hit != -1:
                                wall_mode = 'EDIT'; wall_idx = hit; wall_pt = endp
                            else:
                                wall_mode = 'NEW'
                                sim.add_wall((sim_x, sim_y), (sim_x, sim_y))
                                wall_idx = len(sim.walls)-1; wall_pt = 1
            
            elif event.type == pygame.MOUSEBUTTONUP:
                is_panning = False
                is_painting = False
                is_erasing = False
                wall_mode = None; wall_idx = -1

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if is_panning:
                    pan_x += mx - last_mouse_pos[0]
                    pan_y += my - last_mouse_pos[1]
                    last_mouse_pos = (mx, my)
                
                # Logic updates for dragging walls
                if wall_mode is not None and wall_idx < len(sim.walls):
                    sim_x, sim_y = screen_to_sim(mx, my, zoom, pan_x, pan_y, sim.world_size)
                    w = sim.walls[wall_idx]
                    if wall_pt == 0: sim.update_wall(wall_idx, (sim_x, sim_y), w['end'])
                    else: sim.update_wall(wall_idx, w['start'], (sim_x, sim_y))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: btn_play.active = not btn_play.active

        # --- PHYSICS UPDATE ---
        sim.paused = not btn_play.active
        sim.gravity = slider_gravity.val
        sim.target_temp = slider_temp.val
        sim.damping = slider_damping.val
        sim.sigma = slider_sigma.val
        sim.epsilon = slider_epsilon.val
        sim.use_thermostat = btn_thermostat.active
        sim.use_boundaries = btn_boundaries.active
        
        steps = int(slider_M.val)
        
        # Brush Logic
        mx, my = pygame.mouse.get_pos()
        if is_painting or is_erasing:
             if LEFT_X < mx < RIGHT_X:
                sim_x, sim_y = screen_to_sim(mx, my, zoom, pan_x, pan_y, sim.world_size)
                if is_painting: sim.add_particles_brush(sim_x, sim_y, slider_brush_size.val)
                elif is_erasing: sim.delete_particles_brush(sim_x, sim_y, slider_brush_size.val)

        if not sim.paused:
            sim.step(steps)
            
        # --- RENDER ---
        screen.fill(config.BACKGROUND_COLOR)
        
        # 1. Middle Panel (Sim)
        # Clip drawing to middle panel
        sim_rect = pygame.Rect(MID_X, 0, MID_W, MID_H)
        screen.set_clip(sim_rect)
        
        # Draw Bounds
        tl = sim_to_screen(0, 0, zoom, pan_x, pan_y, sim.world_size)
        br = sim_to_screen(sim.world_size, sim.world_size, zoom, pan_x, pan_y, sim.world_size)
        pygame.draw.rect(screen, config.GRID_COLOR, (tl[0], tl[1], br[0]-tl[0], br[1]-tl[1]), 2)
        
        # Draw Particles
        for i in range(sim.count):
            sx, sy = sim_to_screen(sim.pos_x[i], sim.pos_y[i], zoom, pan_x, pan_y, sim.world_size)
            # Optimization: simple bounds check before draw
            if 0 < sx < config.WINDOW_WIDTH and 0 < sy < config.WINDOW_HEIGHT:
                is_stat = sim.is_static[i]
                col = config.COLOR_STATIC if is_stat else config.COLOR_DYNAMIC
                
                # Rad calc
                rad = max(2, int(sim.sigma * config.PARTICLE_RADIUS_SCALE * ((MID_W-50)/sim.world_size) * zoom))
                pygame.draw.circle(screen, col, (sx, sy), rad)
        
        # Draw Walls
        for w in sim.walls:
            s1 = sim_to_screen(w['start'][0], w['start'][1], zoom, pan_x, pan_y, sim.world_size)
            s2 = sim_to_screen(w['end'][0], w['end'][1], zoom, pan_x, pan_y, sim.world_size)
            pygame.draw.rect(screen, (255, 255, 255), (s1[0]-3, s1[1]-3, 6, 6))
            pygame.draw.rect(screen, (255, 255, 255), (s2[0]-3, s2[1]-3, 6, 6))
            
        screen.set_clip(None) # Reset clip
        
        # 2. Left Panel
        pygame.draw.rect(screen, config.PANEL_BG_COLOR, (0, 0, LEFT_W, config.WINDOW_HEIGHT))
        pygame.draw.line(screen, config.PANEL_BORDER_COLOR, (LEFT_W, 0), (LEFT_W, config.WINDOW_HEIGHT))
        
        # 3. Right Panel
        pygame.draw.rect(screen, config.PANEL_BG_COLOR, (RIGHT_X, 0, RIGHT_W, config.WINDOW_HEIGHT))
        pygame.draw.line(screen, config.PANEL_BORDER_COLOR, (RIGHT_X, 0), (RIGHT_X, config.WINDOW_HEIGHT))
        
        # Draw Right Panel Content
        # Metrics Header
        pygame.draw.rect(screen, (40, 40, 45), (RIGHT_X, 0, RIGHT_W, 90))
        pygame.draw.line(screen, config.PANEL_BORDER_COLOR, (RIGHT_X, 90), (config.WINDOW_WIDTH, 90))
        
        metric_x = RIGHT_X + 15
        screen.blit(big_font.render(f"Particles: {sim.count}", True, (255, 255, 255)), (metric_x, 10))
        screen.blit(font.render(f"Pairs: {sim.pair_count}", True, (180, 180, 180)), (metric_x, 40))
        screen.blit(font.render(f"SPS: {int(sim.sps)}  FPS: {clock.get_fps():.1f}", True, (100, 255, 100)), (metric_x, 60))
        
        # Widgets
        for el in ui_elements: el.draw(screen, font)
        
        # World Size Widget
        screen.blit(lbl_resize, (RIGHT_X + 15, input_world.rect.y + 4))
        input_world.draw(screen, font)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
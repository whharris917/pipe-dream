import pygame
import numpy as np
import config
import math
from simulation_state import Simulation
from ui_widgets import Slider, Button, AtomPalette

def sim_to_screen(x, y, zoom, pan_x, pan_y, view_w, view_h):
    cx_world = config.WORLD_SIZE / 2.0
    cy_world = config.WORLD_SIZE / 2.0
    cx_screen = view_w / 2.0
    cy_screen = view_h / 2.0
    base_scale = (view_w - 100) / config.WORLD_SIZE
    final_scale = base_scale * zoom
    sx = cx_screen + (x - cx_world) * final_scale + pan_x
    sy = cy_screen + (y - cy_world) * final_scale + pan_y
    return int(sx), int(sy)

def screen_to_sim(sx, sy, zoom, pan_x, pan_y, view_w, view_h):
    cx_world = config.WORLD_SIZE / 2.0
    cy_world = config.WORLD_SIZE / 2.0
    cx_screen = view_w / 2.0
    cy_screen = view_h / 2.0
    base_scale = (view_w - 100) / config.WORLD_SIZE
    final_scale = base_scale * zoom
    x = (sx - pan_x - cx_screen) / final_scale + cx_world
    y = (sy - pan_y - cy_screen) / final_scale + cy_world
    return x, y

def main():
    pygame.init()
    total_h = config.WINDOW_HEIGHT + config.UI_HEIGHT
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, total_h))
    pygame.display.set_caption("MD Sandbox - Wall Builder Mode")
    font = pygame.font.SysFont("consolas", 14)
    clock = pygame.time.Clock()
    
    sim = Simulation()
    ui_y = config.WINDOW_HEIGHT + 40 
    
    btn_play = Button(20, ui_y, 80, 40, "PLAY", active=False, color_active=(50, 200, 50), color_inactive=(200, 50, 50))
    slider_gravity = Slider(120, ui_y, 150, 10, 0.0, 50.0, 0.0, "Gravity")
    slider_temp = Slider(120, ui_y + 40, 150, 10, 0.0, 5.0, 0.5, "Temperature")
    slider_damping = Slider(120, ui_y + 80, 150, 10, 0.90, 1.0, 1.0, "Damping (1=None)")
    slider_M = Slider(120, ui_y + 120, 150, 10, 1.0, 50.0, float(config.DEFAULT_DRAW_M), "Speed (Steps/Frame)")
    btn_thermostat = Button(300, ui_y, 100, 25, "Thermostat", active=False)
    
    palette = AtomPalette(config.WINDOW_WIDTH - 150, ui_y, 130, config.ATOM_TYPES)
    slider_brush_size = Slider(config.WINDOW_WIDTH - 320, ui_y, 150, 10, 1.0, 10.0, 2.0, "Brush Size")
    
    ui_elements = [btn_play, slider_gravity, slider_temp, slider_damping, slider_M, btn_thermostat, slider_brush_size]
    
    zoom = 1.0
    pan_x = 0.0
    pan_y = 0.0
    is_panning = False
    last_mouse_pos = (0, 0)
    
    # Interaction State
    is_painting_free = False
    is_erasing = False
    
    # Wall Building State
    wall_drag_mode = None # 'NEW' or 'EDIT'
    wall_start_pos = (0, 0)
    wall_end_pos = (0, 0)
    active_wall_idx = -1
    active_wall_endpoint = -1 # 0 or 1
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            captured = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.pos[1] > config.WINDOW_HEIGHT:
                captured = True
            for el in ui_elements: el.handle_event(event)
            palette.handle_event(event)
            if captured: continue
            
            # --- MOUSE LOGIC ---
            if event.type == pygame.MOUSEWHEEL:
                factor = 1.1 if event.y > 0 else 0.9
                zoom = max(0.1, min(zoom * factor, 50.0))
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2: # Middle Pan
                    is_panning = True
                    last_mouse_pos = event.pos
                elif event.button == 3: # Right Erase
                    is_erasing = True
                elif event.button == 1: # Left Click
                    # Determine Tool: Free Brush vs Wall Line
                    sel_type = palette.selected_type
                    is_static_type = (config.ATOM_TYPES[sel_type]['static'] == 1)
                    
                    sim_x, sim_y = screen_to_sim(event.pos[0], event.pos[1], zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
                    
                    if not is_static_type:
                        # Free Atom Brush
                        is_painting_free = True
                    else:
                        # Wall Tool - Check for existing handles first
                        hit_idx = -1
                        hit_endpoint = -1
                        search_rad = 3.0 / zoom # Scale hit area with zoom
                        
                        for idx, wall in enumerate(sim.walls):
                            # Check Start
                            if math.hypot(wall['start'][0]-sim_x, wall['start'][1]-sim_y) < search_rad:
                                hit_idx = idx; hit_endpoint = 0; break
                            # Check End
                            if math.hypot(wall['end'][0]-sim_x, wall['end'][1]-sim_y) < search_rad:
                                hit_idx = idx; hit_endpoint = 1; break
                        
                        if hit_idx != -1:
                            # Grab existing wall
                            wall_drag_mode = 'EDIT'
                            active_wall_idx = hit_idx
                            active_wall_endpoint = hit_endpoint
                        else:
                            # Start new wall
                            wall_drag_mode = 'NEW'
                            wall_start_pos = (sim_x, sim_y)
                            wall_end_pos = (sim_x, sim_y)
                            # Create placeholder
                            sim.add_wall(wall_start_pos, wall_end_pos, sel_type)
                            active_wall_idx = len(sim.walls) - 1
                            active_wall_endpoint = 1 # Dragging the end

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2: is_panning = False
                elif event.button == 3: is_erasing = False
                elif event.button == 1:
                    is_painting_free = False
                    wall_drag_mode = None
                    active_wall_idx = -1

            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                if is_panning:
                    dx = mouse_x - last_mouse_pos[0]
                    dy = mouse_y - last_mouse_pos[1]
                    pan_x += dx
                    pan_y += dy
                    last_mouse_pos = (mouse_x, mouse_y)
                
                # Update Tools
                sim_x, sim_y = screen_to_sim(mouse_x, mouse_y, zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
                
                if wall_drag_mode is not None and active_wall_idx < len(sim.walls):
                    wall = sim.walls[active_wall_idx]
                    p_start = wall['start']
                    p_end = wall['end']
                    
                    if active_wall_endpoint == 0:
                        sim.update_wall(active_wall_idx, (sim_x, sim_y), p_end)
                    else:
                        sim.update_wall(active_wall_idx, p_start, (sim_x, sim_y))

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: btn_play.active = not btn_play.active

        # --- UPDATE SIMULATION ---
        sim.paused = not btn_play.active
        sim.gravity = slider_gravity.val
        sim.target_temp = slider_temp.val
        sim.damping = slider_damping.val
        sim.use_thermostat = btn_thermostat.active
        steps_per_frame = int(slider_M.val)
        
        # Continuous Brushing / Erasing
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_y < config.WINDOW_HEIGHT:
            sim_x, sim_y = screen_to_sim(mouse_x, mouse_y, zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            if is_painting_free:
                sim.add_particles_brush(sim_x, sim_y, palette.selected_type, slider_brush_size.val)
            elif is_erasing:
                sim.delete_particles_brush(sim_x, sim_y, slider_brush_size.val)

        if not sim.paused:
            sim.step(steps_per_frame)
        
        # --- RENDERING ---
        screen.fill(config.BACKGROUND_COLOR)
        
        # Grid
        tl = sim_to_screen(0, 0, zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        br = sim_to_screen(config.WORLD_SIZE, config.WORLD_SIZE, zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        pygame.draw.rect(screen, config.GRID_COLOR, (tl[0], tl[1], br[0]-tl[0], br[1]-tl[1]), 2)
        
        # Particles
        for i in range(sim.count):
            tid = sim.atom_types[i]
            color = config.ATOM_TYPES[tid]["color"]
            sx, sy = sim_to_screen(sim.pos_x[i], sim.pos_y[i], zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            
            if -10 < sx < config.WINDOW_WIDTH + 10 and -10 < sy < config.WINDOW_HEIGHT + 10:
                radius_sim = config.ATOM_TYPES[tid]["sigma"] * config.PARTICLE_RADIUS_SCALE
                base_scale = (config.WINDOW_WIDTH - 100) / config.WORLD_SIZE
                radius_screen = max(2, int(radius_sim * base_scale * zoom))
                pygame.draw.circle(screen, color, (sx, sy), radius_screen)
        
        # Wall Handles (Draw over particles)
        for wall in sim.walls:
            s_start = sim_to_screen(wall['start'][0], wall['start'][1], zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            s_end = sim_to_screen(wall['end'][0], wall['end'][1], zoom, pan_x, pan_y, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            # Draw line visual aid? Optional, since atoms show the line
            # Draw Handles
            handle_sz = 6
            pygame.draw.rect(screen, (255, 255, 255), (s_start[0]-handle_sz//2, s_start[1]-handle_sz//2, handle_sz, handle_sz))
            pygame.draw.rect(screen, (255, 255, 255), (s_end[0]-handle_sz//2, s_end[1]-handle_sz//2, handle_sz, handle_sz))

        # UI
        pygame.draw.rect(screen, (20, 20, 25), (0, config.WINDOW_HEIGHT, config.WINDOW_WIDTH, config.UI_HEIGHT))
        pygame.draw.line(screen, (100, 100, 100), (0, config.WINDOW_HEIGHT), (config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        for el in ui_elements: el.draw(screen, font)
        palette.draw(screen, font)
        
        status = f"Particles: {sim.count} | Pairs: {sim.pair_count} | FPS: {clock.get_fps():.1f}"
        txt = font.render(status, True, (150, 150, 150))
        screen.blit(txt, (10, 10))
        
        pygame.display.flip()
        clock.tick(0)

    pygame.quit()

if __name__ == "__main__":
    main()
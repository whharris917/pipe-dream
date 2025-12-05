import pygame
import numpy as np
import config
import math
import json
import os
import time # Added for status message timing
from tkinter import filedialog, Tk
from simulation_state import Simulation
from ui_widgets import SmartSlider, Button, InputField, ContextMenu, PropertiesDialog, MenuBar

# --- Layout Constants ---
TOP_MENU_H = 30
LEFT_X = 0
LEFT_W = config.PANEL_LEFT_WIDTH

RIGHT_W = config.PANEL_RIGHT_WIDTH
RIGHT_X = config.WINDOW_WIDTH - RIGHT_W

MID_X = LEFT_W
MID_W = config.WINDOW_WIDTH - LEFT_W - RIGHT_W
MID_H = config.WINDOW_HEIGHT - TOP_MENU_H # Reduce height for top bar

def sim_to_screen(x, y, zoom, pan_x, pan_y, world_size):
    cx_world = world_size / 2.0
    cy_world = world_size / 2.0
    cx_screen = MID_X + (MID_W / 2.0)
    cy_screen = TOP_MENU_H + (MID_H / 2.0) # Offset by Menu Height
    base_scale = (MID_W - 50) / world_size
    final_scale = base_scale * zoom
    sx = cx_screen + (x - cx_world) * final_scale + pan_x
    sy = cy_screen + (y - cy_world) * final_scale + pan_y
    return int(sx), int(sy)

def screen_to_sim(sx, sy, zoom, pan_x, pan_y, world_size):
    cx_world = world_size / 2.0
    cy_world = world_size / 2.0
    cx_screen = MID_X + (MID_W / 2.0)
    cy_screen = TOP_MENU_H + (MID_H / 2.0)
    base_scale = (MID_W - 50) / world_size
    final_scale = base_scale * zoom
    x = (sx - pan_x - cx_screen) / final_scale + cx_world
    y = (sy - pan_y - cy_screen) / final_scale + cy_world
    return x, y

# --- File I/O Helpers ---
def convert_state_to_serializable(state):
    """Converts numpy arrays in state dict to lists for JSON serialization."""
    serializable_state = {}
    for k, v in state.items():
        if isinstance(v, np.ndarray):
            serializable_state[k] = v.tolist()
        else:
            serializable_state[k] = v
    return serializable_state

def convert_state_from_serializable(state):
    """Converts lists back to numpy arrays for the simulation."""
    restored_state = {}
    for k, v in state.items():
        if k in ['pos_x', 'pos_y', 'vel_x', 'vel_y', 'is_static', 'atom_sigma', 'atom_eps_sqrt']:
            # Restore to specific types based on known keys
            dtype = np.float32
            if k == 'is_static': dtype = np.int32
            restored_state[k] = np.array(v, dtype=dtype)
        else:
            restored_state[k] = v
    return restored_state

def save_file(sim, filename, settings=None):
    if not filename: return "Cancelled"
    # Create a snapshot-like dict manually to ensure we get current state
    state = {
        'count': sim.count,
        'pos_x': sim.pos_x[:sim.count],
        'pos_y': sim.pos_y[:sim.count],
        'vel_x': sim.vel_x[:sim.count],
        'vel_y': sim.vel_y[:sim.count],
        'is_static': sim.is_static[:sim.count],
        'atom_sigma': sim.atom_sigma[:sim.count],
        'atom_eps_sqrt': sim.atom_eps_sqrt[:sim.count],
        'walls': sim.walls,
        'world_size': sim.world_size,
        'settings': settings if settings else {}
    }
    
    data = convert_state_to_serializable(state)
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
        return f"Saved to {os.path.basename(filename)}"
    except Exception as e:
        return f"Error: {e}"

def load_file(sim, filename):
    if not filename: return False, "Cancelled", {}
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        state = convert_state_from_serializable(data)
        sim.restore_state(state)
        # Return the settings dict so the UI can update
        return True, f"Loaded {os.path.basename(filename)}", data.get('settings', {})
    except Exception as e:
        return False, f"Error: {e}", {}

def main():
    # Initialize Tkinter root once and keep it hidden
    # This prevents creating/destroying root repeatedly which can fail silently
    try:
        root_tk = Tk()
        root_tk.withdraw()
    except:
        print("Warning: Tkinter initialization failed. File dialogs may not work.")
        root_tk = None

    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    pygame.display.set_caption("Fast MD - Panel Layout")
    font = pygame.font.SysFont("consolas", 14)
    big_font = pygame.font.SysFont("consolas", 20)
    clock = pygame.time.Clock()
    
    sim = Simulation()
    
    # --- UI SETUP ---
    ui_elements = []
    
    # Top Menu
    menu_bar = MenuBar(config.WINDOW_WIDTH, TOP_MENU_H)
    menu_bar.items["File"] = ["Open", "Save", "Save As"] 
    
    current_filepath = None
    
    # Status Message State
    status_msg = ""
    status_time = 0
    
    # -- Left Panel --
    lp_margin = 10
    lp_w = LEFT_W - 2 * lp_margin
    lp_h = 40 
    lp_curr_y = TOP_MENU_H + 20
    
    btn_play = Button(LEFT_X + lp_margin, lp_curr_y, lp_w, lp_h, "Play/Pause", active=False, color_active=(50, 200, 50), color_inactive=(200, 50, 50))
    lp_curr_y += lp_h + 20
    
    btn_clear = Button(LEFT_X + lp_margin, lp_curr_y, lp_w, lp_h, "Clear", active=False, toggle=False, color_inactive=(150, 80, 80))
    lp_curr_y += lp_h + 20
    
    btn_reset = Button(LEFT_X + lp_margin, lp_curr_y, lp_w, lp_h, "Reset", active=False, toggle=False, color_inactive=(150, 50, 50))
    lp_curr_y += lp_h + 20
    
    btn_undo = Button(LEFT_X + lp_margin, lp_curr_y, lp_w, lp_h, "Undo", active=False, toggle=False)
    lp_curr_y += lp_h + 10
    btn_redo = Button(LEFT_X + lp_margin, lp_curr_y, lp_w, lp_h, "Redo", active=False, toggle=False)
    
    ui_elements.extend([btn_play, btn_clear, btn_reset, btn_undo, btn_redo])

    # -- Right Panel --
    rp_margin = 15
    rp_curr_y = TOP_MENU_H + 20
    rp_width = RIGHT_W - 2 * rp_margin
    rp_start_x = RIGHT_X + rp_margin
    
    # Metrics
    rp_curr_y += 100 
    
    # Sliders
    slider_gravity = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.0, 50.0, config.DEFAULT_GRAVITY, "Gravity", hard_min=0.0)
    rp_curr_y += 60
    slider_temp = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.0, 5.0, 0.5, "Temperature", hard_min=0.0)
    rp_curr_y += 60
    slider_damping = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.90, 1.0, config.DEFAULT_DAMPING, "Damping", hard_min=0.0, hard_max=1.0)
    rp_curr_y += 60
    slider_dt = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.0001, 0.01, config.DEFAULT_DT, "Time Step (dt)", hard_min=0.00001)
    rp_curr_y += 60
    slider_sigma = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.5, 2.0, config.ATOM_SIGMA, "Sigma (Size)", hard_min=0.1)
    rp_curr_y += 60
    slider_epsilon = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.1, 5.0, config.ATOM_EPSILON, "Epsilon (Strength)", hard_min=0.0)
    rp_curr_y += 60
    slider_M = SmartSlider(rp_start_x, rp_curr_y, rp_width, 1.0, 100.0, float(config.DEFAULT_DRAW_M), "Speed (Steps/Frame)", hard_min=1.0)
    rp_curr_y += 60
    slider_skin = SmartSlider(rp_start_x, rp_curr_y, rp_width, 0.1, 2.0, config.DEFAULT_SKIN_DISTANCE, "Skin Distance", hard_min=0.05)
    rp_curr_y += 60
    
    ui_elements.extend([slider_gravity, slider_temp, slider_damping, slider_dt, slider_sigma, slider_epsilon, slider_M, slider_skin])
    
    btn_w = (rp_width - 10) // 2
    btn_thermostat = Button(rp_start_x, rp_curr_y, btn_w, 30, "Thermostat", active=False)
    btn_boundaries = Button(rp_start_x + btn_w + 10, rp_curr_y, btn_w, 30, "Bounds", active=False)
    ui_elements.extend([btn_thermostat, btn_boundaries])
    rp_curr_y += 40
    
    btn_tool_brush = Button(rp_start_x, rp_curr_y, btn_w, 30, "Brush", active=True, toggle=False)
    btn_tool_wall = Button(rp_start_x + btn_w + 10, rp_curr_y, btn_w, 30, "Wall", active=False, toggle=False)
    rp_curr_y += 40
    
    slider_brush_size = SmartSlider(rp_start_x, rp_curr_y, rp_width, 1.0, 10.0, 2.0, "Brush Radius", hard_min=0.5)
    ui_elements.append(slider_brush_size)
    rp_curr_y += 60
    
    lbl_resize = font.render("World Size:", True, (200, 200, 200))
    input_world = InputField(rp_start_x + 80, rp_curr_y, 60, 25, str(config.DEFAULT_WORLD_SIZE))
    btn_resize = Button(rp_start_x + 150, rp_curr_y, rp_width - 150, 25, "Resize & Restart", active=False, toggle=False)
    ui_elements.append(btn_resize)
    rp_curr_y += 40
    
    # --- APP STATE ---
    current_tool = 0 
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
    
    context_menu = None
    prop_dialog = None
    context_wall_idx = -1
    
    def calculate_current_temp(vel_x, vel_y, count, mass):
        if count == 0: return 0.0
        vx = vel_x[:count]
        vy = vel_y[:count]
        ke_total = 0.5 * mass * np.sum(vx**2 + vy**2)
        return ke_total / count

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                
                # Global Shortcuts
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        sim.undo()
                        status_msg = "Undo"; status_time = time.time()
                    elif event.key == pygame.K_y and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        sim.redo()
                        status_msg = "Redo"; status_time = time.time()
                
                # --- PRIORITY 1: Menu Bar and Dropdowns ---
                # CRITICAL FIX: Don't consume event if it just toggled menu open
                menu_clicked = menu_bar.handle_event(event)
                
                # Manual Menu Action Handling
                if event.type == pygame.MOUSEBUTTONDOWN and menu_bar.active_menu:
                    # If menu was JUST clicked, menu_clicked is True.
                    # We only process dropdown clicks if we didn't just open the menu header.
                    if menu_bar.dropdown_rect and menu_bar.dropdown_rect.collidepoint(event.pos):
                        # Clicked inside dropdown
                        rel_y = event.pos[1] - menu_bar.dropdown_rect.y
                        idx = rel_y // 30
                        opts = menu_bar.items[menu_bar.active_menu]
                        if 0 <= idx < len(opts):
                            selection = opts[idx]
                            menu_bar.active_menu = None # Close menu
                            
                            # EXECUTE FILE ACTIONS
                            if root_tk:
                                if selection == "Save As" or (selection == "Save" and not current_filepath):
                                    f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
                                    if f:
                                        current_filepath = f
                                        # Gather current settings to save
                                        current_settings = {
                                            'gravity': slider_gravity.val,
                                            'temperature': slider_temp.val,
                                            'damping': slider_damping.val,
                                            'dt': slider_dt.val,
                                            'sigma': slider_sigma.val,
                                            'epsilon': slider_epsilon.val,
                                            'speed': slider_M.val,
                                            'skin': slider_skin.val,
                                            'thermostat': btn_thermostat.active,
                                            'bounds': btn_boundaries.active
                                        }
                                        msg = save_file(sim, f, current_settings)
                                        status_msg = msg; status_time = time.time()
                                elif selection == "Save" and current_filepath:
                                    current_settings = {
                                        'gravity': slider_gravity.val,
                                        'temperature': slider_temp.val,
                                        'damping': slider_damping.val,
                                        'dt': slider_dt.val,
                                        'sigma': slider_sigma.val,
                                        'epsilon': slider_epsilon.val,
                                        'speed': slider_M.val,
                                        'skin': slider_skin.val,
                                        'thermostat': btn_thermostat.active,
                                        'bounds': btn_boundaries.active
                                    }
                                    msg = save_file(sim, current_filepath, current_settings)
                                    status_msg = msg; status_time = time.time()
                                elif selection == "Open":
                                    f = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
                                    if f:
                                        current_filepath = f
                                        success, msg, loaded_settings = load_file(sim, f)
                                        status_msg = msg; status_time = time.time()
                                        if success:
                                            input_world.set_value(sim.world_size)
                                            zoom=1.0; pan_x=0; pan_y=0
                                            
                                            # Update UI elements to match loaded settings
                                            if 'gravity' in loaded_settings: slider_gravity.reset(loaded_settings['gravity'], 0.0, 50.0)
                                            if 'temperature' in loaded_settings: slider_temp.reset(loaded_settings['temperature'], 0.0, 5.0)
                                            if 'damping' in loaded_settings: slider_damping.reset(loaded_settings['damping'], 0.9, 1.0)
                                            if 'dt' in loaded_settings: slider_dt.reset(loaded_settings['dt'], 0.0001, 0.01)
                                            if 'sigma' in loaded_settings: slider_sigma.reset(loaded_settings['sigma'], 0.5, 2.0)
                                            if 'epsilon' in loaded_settings: slider_epsilon.reset(loaded_settings['epsilon'], 0.1, 5.0)
                                            if 'speed' in loaded_settings: slider_M.reset(loaded_settings['speed'], 1.0, 100.0)
                                            if 'skin' in loaded_settings: slider_skin.reset(loaded_settings['skin'], 0.1, 2.0)
                                            
                                            if 'thermostat' in loaded_settings: btn_thermostat.active = loaded_settings['thermostat']
                                            if 'bounds' in loaded_settings: btn_boundaries.active = loaded_settings['bounds']

                        continue # Consume dropdown click
                    elif not menu_clicked:
                        # Clicked outside AND didn't just click header -> Close menu
                        menu_bar.active_menu = None
                        # Don't consume, allow click to pass to world
                
                # If we just clicked the menu header, stop here
                if menu_clicked:
                    continue

                # --- PRIORITY 2: Modals ---
                if context_menu:
                    if context_menu.handle_event(event):
                        action = context_menu.action
                        if action == "Delete":
                            sim.remove_wall(context_wall_idx)
                            context_menu = None
                        elif action == "Properties":
                            wall_data = sim.walls[context_wall_idx]
                            prop_dialog = PropertiesDialog(config.WINDOW_WIDTH//2 - 125, config.WINDOW_HEIGHT//2 - 100, wall_data)
                            context_menu = None
                        elif action == "CLOSE":
                            context_menu = None
                    continue 
                    
                if prop_dialog:
                    if prop_dialog.handle_event(event):
                        if prop_dialog.apply:
                            new_props = prop_dialog.get_values()
                            sim.update_wall_props(context_wall_idx, new_props)
                            prop_dialog.apply = False
                        if prop_dialog.done:
                            prop_dialog = None
                    continue

                # --- PRIORITY 3: Standard UI ---
                mouse_in_ui = (event.type == pygame.MOUSEBUTTONDOWN and (event.pos[0] > RIGHT_X or event.pos[0] < LEFT_W or event.pos[1] < TOP_MENU_H))
                ui_captured = False
                
                for el in ui_elements:
                    if el.handle_event(event): ui_captured = True
                if input_world.handle_event(event): ui_captured = True
                
                if btn_tool_brush.handle_event(event):
                    current_tool = 0
                    btn_tool_brush.active = True
                    btn_tool_wall.active = False
                    ui_captured = True
                
                if btn_tool_wall.handle_event(event):
                    current_tool = 1
                    btn_tool_wall.active = True
                    btn_tool_brush.active = False
                    ui_captured = True
                
                if mouse_in_ui or ui_captured:
                    if btn_reset.clicked:
                        sim.reset_simulation()
                        input_world.set_value(config.DEFAULT_WORLD_SIZE)
                        slider_gravity.reset(config.DEFAULT_GRAVITY, 0.0, 50.0)
                        slider_temp.reset(0.5, 0.0, 5.0)
                        slider_damping.reset(config.DEFAULT_DAMPING, 0.9, 1.0)
                        slider_sigma.reset(config.ATOM_SIGMA, 0.5, 2.0)
                        slider_epsilon.reset(config.ATOM_EPSILON, 0.1, 5.0)
                        slider_dt.reset(config.DEFAULT_DT, 0.0001, 0.01)
                        slider_skin.reset(config.DEFAULT_SKIN_DISTANCE, 0.1, 2.0)
                        btn_thermostat.active = False
                        btn_boundaries.active = False
                        zoom = 1.0; pan_x = 0; pan_y = 0
                        status_msg = "Reset Simulation"; status_time = time.time()
                    if btn_clear.clicked: 
                        sim.clear_particles()
                        status_msg = "Cleared Particles"; status_time = time.time()
                    if btn_resize.clicked:
                        sim.resize_world(input_world.get_value(50.0))
                        zoom = 1.0; pan_x = 0; pan_y = 0
                        status_msg = f"Resized to {sim.world_size}"; status_time = time.time()
                    
                    if btn_undo.clicked: 
                        sim.undo()
                        status_msg = "Undo"; status_time = time.time()
                    if btn_redo.clicked: 
                        sim.redo()
                        status_msg = "Redo"; status_time = time.time()
                    continue 

                # --- PRIORITY 4: World Interaction ---
                if event.type == pygame.MOUSEWHEEL:
                    factor = 1.1 if event.y > 0 else 0.9
                    zoom = max(0.1, min(zoom * factor, 50.0))
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 2:
                        is_panning = True
                        last_mouse_pos = event.pos
                    
                    elif event.button == 3:
                        mx, my = event.pos
                        if LEFT_X < mx < RIGHT_X:
                            sim_x, sim_y = screen_to_sim(mx, my, zoom, pan_x, pan_y, sim.world_size)
                            rad_sim = 5.0 / ( ((MID_W - 50) / sim.world_size) * zoom )
                            hit_wall = -1
                            for i, w in enumerate(sim.walls):
                                if math.hypot(w['start'][0]-sim_x, w['start'][1]-sim_y) < rad_sim or \
                                   math.hypot(w['end'][0]-sim_x, w['end'][1]-sim_y) < rad_sim:
                                    hit_wall = i
                                    break
                            
                            if hit_wall != -1:
                                context_menu = ContextMenu(mx, my, ["Properties", "Delete"])
                                context_wall_idx = hit_wall
                            else:
                                is_erasing = True
                                sim.snapshot()

                    elif event.button == 1:
                        mx, my = event.pos
                        if LEFT_X < mx < RIGHT_X:
                            sim_x, sim_y = screen_to_sim(mx, my, zoom, pan_x, pan_y, sim.world_size)
                            
                            if current_tool == 0:
                                is_painting = True
                                sim.snapshot()
                            elif current_tool == 1:
                                hit = -1; endp = -1
                                rad_sim = 5.0 / ( ((MID_W - 50) / sim.world_size) * zoom )
                                for i, w in enumerate(sim.walls):
                                    if math.hypot(w['start'][0]-sim_x, w['start'][1]-sim_y) < rad_sim:
                                        hit=i; endp=0; break
                                    if math.hypot(w['end'][0]-sim_x, w['end'][1]-sim_y) < rad_sim:
                                        hit=i; endp=1; break
                                
                                if hit != -1:
                                    wall_mode = 'EDIT'; wall_idx = hit; wall_pt = endp
                                    sim.snapshot()
                                else:
                                    wall_mode = 'NEW'
                                    sim.snapshot()
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
                    
                    if wall_mode is not None and wall_idx < len(sim.walls):
                        sim_x, sim_y = screen_to_sim(mx, my, zoom, pan_x, pan_y, sim.world_size)
                        w = sim.walls[wall_idx]
                        if wall_pt == 0: sim.update_wall(wall_idx, (sim_x, sim_y), w['end'])
                        else: sim.update_wall(wall_idx, w['start'], (sim_x, sim_y))

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: btn_play.active = not btn_play.active

            # --- UPDATE ---
            if not prop_dialog:
                sim.paused = not btn_play.active
                sim.gravity = slider_gravity.val
                sim.target_temp = slider_temp.val
                sim.damping = slider_damping.val
                sim.dt = slider_dt.val
                sim.sigma = slider_sigma.val
                sim.epsilon = slider_epsilon.val
                sim.skin_distance = slider_skin.val
                sim.use_thermostat = btn_thermostat.active
                sim.use_boundaries = btn_boundaries.active
                
                steps = int(slider_M.val)
                
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
            
            sim_rect = pygame.Rect(MID_X, TOP_MENU_H, MID_W, MID_H)
            screen.set_clip(sim_rect)
            
            tl = sim_to_screen(0, 0, zoom, pan_x, pan_y, sim.world_size)
            br = sim_to_screen(sim.world_size, sim.world_size, zoom, pan_x, pan_y, sim.world_size)
            pygame.draw.rect(screen, config.GRID_COLOR, (tl[0], tl[1], br[0]-tl[0], br[1]-tl[1]), 2)
            
            for i in range(sim.count):
                sx, sy = sim_to_screen(sim.pos_x[i], sim.pos_y[i], zoom, pan_x, pan_y, sim.world_size)
                if 0 < sx < config.WINDOW_WIDTH and 0 < sy < config.WINDOW_HEIGHT:
                    is_stat = sim.is_static[i]
                    col = config.COLOR_STATIC if is_stat else config.COLOR_DYNAMIC
                    atom_sig = sim.atom_sigma[i]
                    rad = max(2, int(atom_sig * config.PARTICLE_RADIUS_SCALE * ((MID_W-50)/sim.world_size) * zoom))
                    pygame.draw.circle(screen, col, (sx, sy), rad)
            
            for w in sim.walls:
                s1 = sim_to_screen(w['start'][0], w['start'][1], zoom, pan_x, pan_y, sim.world_size)
                s2 = sim_to_screen(w['end'][0], w['end'][1], zoom, pan_x, pan_y, sim.world_size)
                pygame.draw.rect(screen, (255, 255, 255), (s1[0]-3, s1[1]-3, 6, 6))
                pygame.draw.rect(screen, (255, 255, 255), (s2[0]-3, s2[1]-3, 6, 6))
                
            screen.set_clip(None)
            
            # Panels
            pygame.draw.rect(screen, config.PANEL_BG_COLOR, (0, TOP_MENU_H, LEFT_W, config.WINDOW_HEIGHT))
            pygame.draw.line(screen, config.PANEL_BORDER_COLOR, (LEFT_W, TOP_MENU_H), (LEFT_W, config.WINDOW_HEIGHT))
            
            pygame.draw.rect(screen, config.PANEL_BG_COLOR, (RIGHT_X, TOP_MENU_H, RIGHT_W, config.WINDOW_HEIGHT))
            pygame.draw.line(screen, config.PANEL_BORDER_COLOR, (RIGHT_X, TOP_MENU_H), (RIGHT_X, config.WINDOW_HEIGHT))
            
            # Metrics
            pygame.draw.rect(screen, (40, 40, 45), (RIGHT_X, TOP_MENU_H, RIGHT_W, 90))
            pygame.draw.line(screen, config.PANEL_BORDER_COLOR, (RIGHT_X, TOP_MENU_H + 90), (config.WINDOW_WIDTH, TOP_MENU_H + 90))
            
            curr_t = calculate_current_temp(sim.vel_x, sim.vel_y, sim.count, config.ATOM_MASS)
            
            metric_x = RIGHT_X + 15
            screen.blit(big_font.render(f"Particles: {sim.count}", True, (255, 255, 255)), (metric_x, TOP_MENU_H + 10))
            screen.blit(font.render(f"Pairs: {sim.pair_count} | T: {curr_t:.3f}", True, (180, 180, 180)), (metric_x, TOP_MENU_H + 40))
            screen.blit(font.render(f"SPS: {int(sim.sps)}  FPS: {clock.get_fps():.1f}", True, (100, 255, 100)), (metric_x, TOP_MENU_H + 60))
            
            for el in ui_elements: el.draw(screen, font)
            
            btn_tool_brush.draw(screen, font)
            btn_tool_wall.draw(screen, font)
            
            screen.blit(lbl_resize, (RIGHT_X + 15, input_world.rect.y + 4))
            input_world.draw(screen, font)
            
            # Status Bar Overlay (if active)
            if time.time() - status_time < 3.0: # Show for 3 seconds
                status_surf = font.render(status_msg, True, (100, 255, 100))
                # Draw top left over game view
                pygame.draw.rect(screen, (30,30,30), (MID_X + 10, TOP_MENU_H + 10, status_surf.get_width()+10, 25), border_radius=5)
                screen.blit(status_surf, (MID_X + 15, TOP_MENU_H + 15))

            # Draw Menu Bar and Overlays LAST to cover everything
            menu_bar.draw(screen, font)
            
            if context_menu: context_menu.draw(screen, font)
            if prop_dialog: prop_dialog.draw(screen, font)
            
            pygame.display.flip()
            clock.tick(60)
            
    finally:
        if root_tk:
            root_tk.destroy() # Ensure Tkinter cleans up
    
    pygame.quit()

if __name__ == "__main__":
    main()
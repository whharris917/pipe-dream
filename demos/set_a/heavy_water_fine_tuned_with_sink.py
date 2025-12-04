import pygame
import random
import sys
import math
import time

# --- CONFIGURATION ---
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800
PHYSICS_STEPS_PER_FRAME = 60 

# Geometry
MAIN_PIPE_LENGTH = 200    
BRANCH_PIPE_LENGTH = 120 
BOTTOM_PIPE_LENGTH = 150  
NUM_LANES = 16            
CELL_SIZE = 5             

# Topology
VALVE_POS = MAIN_PIPE_LENGTH // 2
JUNCTION_POS = (MAIN_PIPE_LENGTH * 3) // 4 

# --- USER TUNED PARAMETERS ---
# "Heavy Water" Configuration
KT = 0.2                # Low Temp: Reduces gas-like mist/boiling
GRAVITY_POTENTIAL = 0.9 # High Gravity: Aggressively seeks lowest point
INTERACTION_J = 0.01    # Near-Zero Repulsion: Minimizes "puffiness/expansion"
MU_SOURCE = 5.0         # High Pressure: Ensures inlet stays full

# Stochastic Cap (Breaks Crystal Lattice)
MAX_MOVE_PROB = 0.5     

# Colors
COLOR_BG = (15, 15, 20)
COLOR_GRID = (30, 30, 35)
COLOR_PIPE_BG = (35, 35, 35)
COLOR_FLUID_TOP = (0, 191, 255)    
COLOR_FLUID_BOT = (0, 50, 120)     
COLOR_SOURCE = (0, 255, 0)
COLOR_SINK = (255, 0, 255)
COLOR_WALL = (255, 50, 50)
COLOR_VALVE_OPEN = (0, 255, 0)
COLOR_VALVE_CLOSED = (255, 0, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_UI_BG = (0, 0, 0, 180)

class Camera:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.is_panning = False
        self.last_mouse_pos = (0, 0)

    def world_to_screen(self, wx, wy):
        sx = (wx * self.zoom) + self.offset_x
        sy = (wy * self.zoom) + self.offset_y
        return sx, sy

    def screen_to_world(self, sx, sy):
        wx = (sx - self.offset_x) / self.zoom
        wy = (sy - self.offset_y) / self.zoom
        return wx, wy

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3: 
                self.is_panning = True
                self.last_mouse_pos = event.pos
            elif event.button == 4: 
                self.apply_zoom(1.1, event.pos)
            elif event.button == 5: 
                self.apply_zoom(0.9, event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.is_panning = False
        elif event.type == pygame.MOUSEMOTION:
            if self.is_panning:
                mx, my = event.pos
                dx = mx - self.last_mouse_pos[0]
                dy = my - self.last_mouse_pos[1]
                self.offset_x += dx
                self.offset_y += dy
                self.last_mouse_pos = (mx, my)

    def apply_zoom(self, scale_factor, mouse_pos):
        old_zoom = self.zoom
        new_zoom = self.zoom * scale_factor
        if new_zoom < self.min_zoom: new_zoom = self.min_zoom
        if new_zoom > self.max_zoom: new_zoom = self.max_zoom
        wx, wy = self.screen_to_world(*mouse_pos)
        self.zoom = new_zoom
        new_sx, new_sy = self.world_to_screen(wx, wy)
        self.offset_x += (mouse_pos[0] - new_sx)
        self.offset_y += (mouse_pos[1] - new_sy)

class BitwisePipe:
    def __init__(self, length, lanes, angle_deg=0):
        self.length = length
        self.lanes = lanes
        self.states = [0] * lanes 
        self.mask = (1 << length) - 1 
        self.valve_active = False 
        self.valve_open = True
        
        rad = math.radians(angle_deg)
        self.dE_long_plus  = -math.sin(rad) * GRAVITY_POTENTIAL
        self.dE_long_minus =  math.sin(rad) * GRAVITY_POTENTIAL
        self.dE_trans_plus  = -math.cos(rad) * GRAVITY_POTENTIAL
        self.dE_trans_minus =  math.cos(rad) * GRAVITY_POTENTIAL
        
        self.angle = angle_deg

    def reset(self):
        self.states = [0] * self.lanes

    def get_boltzmann_mask(self, dE_tensor, length):
        if dE_tensor <= 0:
            base_p = MAX_MOVE_PROB
        else:
            base_p = math.exp(-dE_tensor / KT) * MAX_MOVE_PROB
            
        if base_p <= 0.01: return 0
        if base_p >= 0.99: return (1 << length) - 1
        
        r1 = random.getrandbits(length)
        if base_p > 0.5:
            r2 = random.getrandbits(length)
            return r1 | r2 if base_p > 0.75 else r1
        else:
            r2 = random.getrandbits(length)
            return r1 & r2 if base_p < 0.25 else r1

    def step_monte_carlo(self, chemical_potential_on):
        directions = [0, 1, 2, 3]
        random.shuffle(directions)
        
        valve_blocker = self.mask
        if self.valve_active and not self.valve_open:
            valve_bit_index = self.length - 1 - VALVE_POS
            valve_blocker = ~(1 << valve_bit_index) & self.mask

        for d in directions:
            if d == 0: # Right
                dE_base = self.dE_long_plus
                phantom_bit = (1 << (self.length - 1)) if chemical_potential_on else 0
                
                for i in range(self.lanes):
                    state = self.states[i]
                    candidates = (state >> 1) & (~state)
                    
                    neighbors = (state >> 1) | phantom_bit
                    has_neighbor_behind = neighbors & state
                    
                    # With J=0.01, mask_pushed and mask_lonely are nearly identical.
                    # This means Flow is driven purely by dE_base (Gravity) 
                    # and Diffusion (Random Walk), not pressure.
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor_behind & mask_pushed) | \
                                 (~has_neighbor_behind & mask_lonely)
                    
                    valid = candidates & acceptance & valve_blocker & self.mask
                    state = state ^ valid ^ (valid << 1)
                    self.states[i] = state

            elif d == 1: # Left
                dE_base = self.dE_long_minus
                for i in range(self.lanes):
                    state = self.states[i]
                    candidates = (state << 1) & (~state)
                    
                    neighbors = (state << 1) 
                    has_neighbor_behind = neighbors & state
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor_behind & mask_pushed) | \
                                 (~has_neighbor_behind & mask_lonely)
                    
                    valid = candidates & acceptance & valve_blocker & self.mask
                    state = state ^ valid ^ (valid >> 1)
                    self.states[i] = state

            elif d == 2: # Down
                dE_base = self.dE_trans_plus
                for i in range(self.lanes - 2, -1, -1):
                    src = self.states[i]
                    tgt = self.states[i+1]
                    candidates = src & (~tgt)
                    
                    has_neighbor = (self.states[i-1] & src) if i > 0 else 0
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor & mask_pushed) | (~has_neighbor & mask_lonely)
                    moves = candidates & acceptance
                    self.states[i] ^= moves
                    self.states[i+1] |= moves

            elif d == 3: # Up
                dE_base = self.dE_trans_minus
                for i in range(self.lanes - 1):
                    src = self.states[i+1]
                    tgt = self.states[i]
                    candidates = src & (~tgt)
                    
                    has_neighbor = (self.states[i+2] & src) if i < self.lanes - 2 else 0
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor & mask_pushed) | (~has_neighbor & mask_lonely)
                    moves = candidates & acceptance
                    self.states[i+1] ^= moves
                    self.states[i] |= moves

        # --- INJECTION ---
        if chemical_potential_on:
            entry_bit = 1 << (self.length - 1)
            dE_insert = -MU_SOURCE
            prob = (1.0 if dE_insert < 0 else math.exp(-dE_insert/KT)) * MAX_MOVE_PROB
            
            for i in range(self.lanes):
                if not (self.states[i] & entry_bit):
                    if random.random() < prob:
                        self.states[i] |= entry_bit


def handle_junction(source, dest):
    source_exit_idx = 0 
    dest_entry_idx = dest.length - 1
    empty_dest_lanes = []
    for i in range(NUM_LANES):
        if not ((dest.states[i] >> dest_entry_idx) & 1):
            empty_dest_lanes.append(i)
    random.shuffle(empty_dest_lanes)
    for i in range(NUM_LANES):
        if (source.states[i] >> source_exit_idx) & 1:
            if random.random() > 0.95: continue
            if not empty_dest_lanes: break 
            target_lane = empty_dest_lanes.pop()
            source.states[i] &= ~(1 << source_exit_idx)
            dest.states[target_lane] |= (1 << dest_entry_idx)

def handle_mid_junction(main, branch, junction_pos):
    junction_bit_idx = main.length - 1 - junction_pos
    branch_inlet_idx = branch.length - 1
    falling_count = 0
    for i in range(NUM_LANES):
        if (main.states[i] >> junction_bit_idx) & 1:
            if random.random() < 0.90:
                main.states[i] &= ~(1 << junction_bit_idx)
                falling_count += 1
    if falling_count > 0:
        available_lanes = list(range(NUM_LANES))
        random.shuffle(available_lanes)
        for _ in range(falling_count):
            if not available_lanes: break
            target_lane = available_lanes.pop()
            if not ((branch.states[target_lane] >> branch_inlet_idx) & 1):
                branch.states[target_lane] |= (1 << branch_inlet_idx)

def handle_sink(pipe, active=True):
    """Removes particles from the end of the pipe (Right side)"""
    if not active: return
    exit_bit = 1 # Bit 0
    for i in range(pipe.lanes):
        if pipe.states[i] & exit_bit:
            # Simple removal (Infinite Sink)
            pipe.states[i] &= ~exit_bit

def draw_pipe(screen, pipe, world_x, world_y, camera):
    rad = math.radians(pipe.angle)
    s_cell = CELL_SIZE * camera.zoom
    if s_cell < 0.5: return 
    u_len_x = math.cos(rad) * s_cell
    u_len_y = math.sin(rad) * s_cell
    u_wid_x = -math.sin(rad) * s_cell
    u_wid_y = math.cos(rad) * s_cell
    start_sx, start_sy = camera.world_to_screen(world_x, world_y)
    len_px = pipe.length * s_cell
    p1 = (start_sx, start_sy)
    p2 = (start_sx + (math.cos(rad) * len_px), start_sy + (math.sin(rad) * len_px))
    p3 = (p2[0] + (u_wid_x * pipe.lanes), p2[1] + (u_wid_y * pipe.lanes))
    p4 = (start_sx + (u_wid_x * pipe.lanes), start_sy + (u_wid_y * pipe.lanes))
    pygame.draw.polygon(screen, COLOR_PIPE_BG, [p1, p2, p3, p4])
    for lane_idx in range(pipe.lanes):
        state = pipe.states[lane_idx]
        if state == 0: continue
        t = lane_idx / (pipe.lanes - 1)
        color = (
            int(COLOR_FLUID_TOP[0] * (1-t) + COLOR_FLUID_BOT[0] * t),
            int(COLOR_FLUID_TOP[1] * (1-t) + COLOR_FLUID_BOT[1] * t),
            int(COLOR_FLUID_TOP[2] * (1-t) + COLOR_FLUID_BOT[2] * t),
        )
        for bit_idx in range(pipe.length):
            if (state >> bit_idx) & 1:
                dist_long = pipe.length - 1 - bit_idx
                dist_trans = lane_idx
                draw_x = start_sx + (dist_long * u_len_x) + (dist_trans * u_wid_x)
                draw_y = start_sy + (dist_long * u_len_y) + (dist_trans * u_wid_y)
                draw_size = math.ceil(s_cell)
                pygame.draw.rect(screen, color, (int(draw_x), int(draw_y), draw_size, draw_size))

def draw_grid(screen, camera):
    grid_spacing = 100 * camera.zoom
    if grid_spacing < 10: return
    offset_x = camera.offset_x % grid_spacing
    offset_y = camera.offset_y % grid_spacing
    cols = int(DEFAULT_WIDTH / grid_spacing) + 2
    rows = int(DEFAULT_HEIGHT / grid_spacing) + 2
    for c in range(cols):
        x = offset_x + (c * grid_spacing) - grid_spacing
        pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, DEFAULT_HEIGHT))
    for r in range(rows):
        y = offset_y + (r * grid_spacing) - grid_spacing
        pygame.draw.line(screen, COLOR_GRID, (0, y), (DEFAULT_WIDTH, y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Final Tuned Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    bold_font = pygame.font.SysFont("monospace", 24, bold=True)

    camera = Camera()
    main_pipe = BitwisePipe(MAIN_PIPE_LENGTH, NUM_LANES, angle_deg=0)
    main_pipe.valve_active = True
    branch_pipe = BitwisePipe(BRANCH_PIPE_LENGTH, NUM_LANES, angle_deg=45)
    bottom_pipe = BitwisePipe(BOTTOM_PIPE_LENGTH, NUM_LANES, angle_deg=0)

    pumping = True
    draining = True # Sink active by default
    
    w_main_x = 100
    w_main_y = 300
    w_junc_x = w_main_x + (JUNCTION_POS * CELL_SIZE)
    w_junc_y = w_main_y + (NUM_LANES * CELL_SIZE)
    rad_45 = math.radians(45)
    diag_len_px = BRANCH_PIPE_LENGTH * CELL_SIZE
    w_bottom_x = w_junc_x + (math.cos(rad_45) * diag_len_px)
    w_bottom_y = w_junc_y + (math.sin(rad_45) * diag_len_px)

    running = True
    frame_count = 0
    start_time = time.time()
    physics_ticks = 0
    fps_display = 0
    tps_display = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE: pass 
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pumping = not pumping
                elif event.key == pygame.K_d:
                    draining = not draining
                elif event.key == pygame.K_r:
                    main_pipe.reset()
                    branch_pipe.reset()
                    bottom_pipe.reset()
                    camera.offset_x, camera.offset_y, camera.zoom = 0, 0, 1.0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    w_valve_x = w_main_x + (VALVE_POS * CELL_SIZE)
                    sx, sy = camera.world_to_screen(w_valve_x, w_main_y)
                    sw, sh = CELL_SIZE * 3 * camera.zoom, CELL_SIZE * NUM_LANES * camera.zoom
                    valve_rect = pygame.Rect(sx - 10, sy - 20, sw + 20, sh + 40)
                    if valve_rect.collidepoint(event.pos):
                        main_pipe.valve_open = not main_pipe.valve_open
            camera.handle_event(event)

        for _ in range(PHYSICS_STEPS_PER_FRAME):
            main_pipe.step_monte_carlo(chemical_potential_on=pumping)
            branch_pipe.step_monte_carlo(chemical_potential_on=False)
            bottom_pipe.step_monte_carlo(chemical_potential_on=False)
            
            handle_mid_junction(main_pipe, branch_pipe, JUNCTION_POS)
            handle_junction(branch_pipe, bottom_pipe) 
            handle_sink(bottom_pipe, active=draining)
            
            physics_ticks += 1

        screen.fill(COLOR_BG)
        draw_grid(screen, camera)
        
        draw_pipe(screen, bottom_pipe, w_bottom_x, w_bottom_y, camera)
        draw_pipe(screen, branch_pipe, w_junc_x, w_junc_y, camera)
        draw_pipe(screen, main_pipe, w_main_x, w_main_y, camera)

        w_valve_x = w_main_x + (VALVE_POS * CELL_SIZE)
        s_valve_x, s_valve_y = camera.world_to_screen(w_valve_x, w_main_y)
        s_valve_h = (NUM_LANES * CELL_SIZE) * camera.zoom
        v_col = COLOR_VALVE_OPEN if main_pipe.valve_open else COLOR_VALVE_CLOSED
        pygame.draw.rect(screen, v_col, (s_valve_x - 5, s_valve_y - 20, 10, s_valve_h + 40), 2)
        if not main_pipe.valve_open:
            pygame.draw.line(screen, v_col, (s_valve_x, s_valve_y), (s_valve_x, s_valve_y + s_valve_h), 4)

        # Draw Sink Indicator
        if draining:
            s_sink_x, s_sink_y = camera.world_to_screen(w_bottom_x + BOTTOM_PIPE_LENGTH*CELL_SIZE, w_bottom_y)
            pygame.draw.circle(screen, COLOR_SINK, (int(s_sink_x), int(s_sink_y + (NUM_LANES*CELL_SIZE*camera.zoom)/2)), int(10*camera.zoom))

        if frame_count % 30 == 0:
            dt = time.time() - start_time
            if dt > 0: fps_display, tps_display = frame_count / dt, physics_ticks / dt 

        stats_surf = pygame.Surface((400, 160), pygame.SRCALPHA)
        stats_surf.fill(COLOR_UI_BG)
        screen.blit(stats_surf, (10, 10))
        screen.blit(bold_font.render(f"FPS: {fps_display:.0f} | TPS: {tps_display:.0f}", True, COLOR_SOURCE), (20, 20))
        screen.blit(font.render("Parameter Set: 'Heavy Water'", True, COLOR_TEXT), (20, 50))
        screen.blit(font.render(f"J={INTERACTION_J}, G={GRAVITY_POTENTIAL}, kT={KT}", True, (200, 200, 200)), (20, 80))
        screen.blit(font.render("SPACE: Pump | D: Drain | CLICK: Valve", True, (200, 200, 200)), (20, 110))

        pygame.display.flip()
        frame_count += 1

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
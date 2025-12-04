import pygame
import random
import sys
import math
import time

# --- CONFIGURATION ---
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800
PHYSICS_STEPS_PER_FRAME = 50 

# Geometry
MAIN_PIPE_LENGTH = 200    
BRANCH_PIPE_LENGTH = 120  
NUM_LANES = 16            
CELL_SIZE = 5             # World Unit size (Base size before zoom)

# Topology
VALVE_POS = MAIN_PIPE_LENGTH // 2
JUNCTION_POS = (MAIN_PIPE_LENGTH * 3) // 4 

# Physics Knobs
GLOBAL_PRESSURE = 0.90     
GLOBAL_GRAVITY = 0.50      
BASE_DIFFUSION = 0.60      

# Colors
COLOR_BG = (15, 15, 20)          # Slightly blue-ish dark bg
COLOR_GRID = (30, 30, 35)        # Grid lines
COLOR_PIPE_BG = (35, 35, 35)
COLOR_FLUID_TOP = (0, 191, 255)    
COLOR_FLUID_BOT = (0, 50, 120)     
COLOR_SOURCE = (0, 255, 0)
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
            if event.button == 3: # Right Click
                self.is_panning = True
                self.last_mouse_pos = event.pos
            elif event.button == 4: # Scroll Up
                self.apply_zoom(1.1, event.pos)
            elif event.button == 5: # Scroll Down
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
        
        # Clamp zoom
        if new_zoom < self.min_zoom: new_zoom = self.min_zoom
        if new_zoom > self.max_zoom: new_zoom = self.max_zoom
        
        # Zoom towards mouse cursor:
        # 1. Convert mouse to world space
        wx, wy = self.screen_to_world(*mouse_pos)
        
        # 2. Apply new zoom
        self.zoom = new_zoom
        
        # 3. Calculate new screen pos of that world point
        new_sx, new_sy = self.world_to_screen(wx, wy)
        
        # 4. Adjust offset to pull that point back under the mouse
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
        self.g_long = math.sin(rad) 
        self.g_trans = math.cos(rad)
        self.angle = angle_deg

    def reset(self):
        self.states = [0] * self.lanes

    def inject(self, pump_rate=1.0):
        entry_bit = 1 << (self.length - 1)
        for i in range(self.lanes):
            if random.random() < pump_rate:
                self.states[i] |= entry_bit

    def get_stochastic_mask(self, probability):
        if probability <= 0: return 0
        if probability >= 1: return self.mask
        r1 = random.getrandbits(self.length)
        if probability > 0.5:
            r2 = random.getrandbits(self.length)
            return r1 | r2 if probability > 0.75 else r1
        else:
            r2 = random.getrandbits(self.length)
            return r1 & r2 if probability < 0.25 else r1

    def update(self):
        force_trans_down = abs(self.g_trans * GLOBAL_GRAVITY)
        force_trans_up = BASE_DIFFUSION 
        force_long_right = GLOBAL_PRESSURE + (self.g_long * GLOBAL_GRAVITY)
        force_long_left = BASE_DIFFUSION

        valve_blocker = self.mask
        if self.valve_active and not self.valve_open:
            valve_bit_index = self.length - 1 - VALVE_POS
            valve_blocker = ~(1 << valve_bit_index) & self.mask

        passes = 3 if force_trans_down > 0.1 else 1
        for _ in range(passes):
            for i in range(self.lanes - 2, -1, -1):
                upper = self.states[i]
                lower = self.states[i+1]
                candidates = upper & (~lower)
                move_mask = self.get_stochastic_mask(force_trans_down + 0.2)
                falling = candidates & move_mask
                self.states[i] ^= falling
                self.states[i+1] |= falling

        if force_trans_up > 0:
            for i in range(self.lanes - 1):
                upper = self.states[i]
                lower = self.states[i+1]
                candidates = lower & (~upper)
                move_mask = self.get_stochastic_mask(force_trans_up * 0.5) 
                rising = candidates & move_mask
                self.states[i+1] ^= rising
                self.states[i] |= rising

        for i in range(self.lanes):
            state = self.states[i]
            mask_right = self.get_stochastic_mask(force_long_right)
            candidates = (state >> 1) & (~state) & self.mask
            valid_moves = candidates & mask_right & valve_blocker
            state = state ^ valid_moves ^ (valid_moves << 1)

            mask_left = self.get_stochastic_mask(force_long_left)
            candidates = (state << 1) & (~state) & self.mask
            valid_moves = candidates & mask_left & valve_blocker
            state = state ^ valid_moves ^ (valid_moves >> 1)
            
            self.states[i] = state
        for i in range(self.lanes):
            self.states[i] &= self.mask


def handle_junction(main, branch):
    junction_bit_idx = main.length - 1 - JUNCTION_POS
    branch_inlet_idx = branch.length - 1
    falling_count = 0
    for i in range(NUM_LANES):
        if (main.states[i] >> junction_bit_idx) & 1:
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

def draw_pipe(screen, pipe, world_x, world_y, camera):
    rad = math.radians(pipe.angle)
    # Calculate screen cell size
    s_cell = CELL_SIZE * camera.zoom
    
    # Early culling check (optional but good for performance)
    # If the pipe is way off screen, don't iterate bits.
    # (Skipping implementation for brevity, but this is where it would go)

    # Unit Vectors in Screen Space
    # How many pixels to move on screen for 1 unit of World Length
    u_len_x = math.cos(rad) * s_cell
    u_len_y = math.sin(rad) * s_cell
    u_wid_x = -math.sin(rad) * s_cell
    u_wid_y = math.cos(rad) * s_cell

    # Pipe Start Point in Screen Space
    start_sx, start_sy = camera.world_to_screen(world_x, world_y)

    # 1. Background Polygon
    len_px = pipe.length * s_cell
    wid_px = pipe.lanes * s_cell
    
    # We construct corners based on unit vectors
    p1 = (start_sx, start_sy)
    p2 = (start_sx + (math.cos(rad) * len_px), start_sy + (math.sin(rad) * len_px))
    p3 = (p2[0] + (u_wid_x * pipe.lanes), p2[1] + (u_wid_y * pipe.lanes))
    p4 = (start_sx + (u_wid_x * pipe.lanes), start_sy + (u_wid_y * pipe.lanes))
    
    pygame.draw.polygon(screen, COLOR_PIPE_BG, [p1, p2, p3, p4])

    # 2. Fluid Atoms
    # Only draw if cells are large enough to be visible
    if s_cell < 1.0: return

    for lane_idx in range(pipe.lanes):
        state = pipe.states[lane_idx]
        if state == 0: continue # Optimization: Skip empty lanes

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
                
                # Position calculation in Screen Space
                draw_x = start_sx + (dist_long * u_len_x) + (dist_trans * u_wid_x)
                draw_y = start_sy + (dist_long * u_len_y) + (dist_trans * u_wid_y)
                
                # Draw square (using +1 to avoid sub-pixel gaps at low zoom)
                draw_size = math.ceil(s_cell) 
                pygame.draw.rect(screen, color, (int(draw_x), int(draw_y), draw_size, draw_size))

def draw_grid(screen, camera):
    """Draws a background grid to visualize pan/zoom"""
    grid_spacing = 100 * camera.zoom
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
    pygame.display.set_caption("Infinite Canvas Fluid Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    bold_font = pygame.font.SysFont("monospace", 24, bold=True)

    # Initialize Camera
    camera = Camera()
    
    # Initialize Physics World
    main_pipe = BitwisePipe(MAIN_PIPE_LENGTH, NUM_LANES, angle_deg=0)
    main_pipe.valve_active = True
    branch_pipe = BitwisePipe(BRANCH_PIPE_LENGTH, NUM_LANES, angle_deg=45)

    pumping = True
    
    # World Coordinates for Pipes (Not screen coords!)
    world_main_x = 100
    world_main_y = 300
    world_junc_x = world_main_x + (JUNCTION_POS * CELL_SIZE)
    world_junc_y = world_main_y + (NUM_LANES * CELL_SIZE)

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
            elif event.type == pygame.VIDEORESIZE:
                pass 
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pumping = not pumping
                elif event.key == pygame.K_r:
                    main_pipe.reset()
                    branch_pipe.reset()
                    camera.offset_x = 0 # Reset camera too
                    camera.offset_y = 0
                    camera.zoom = 1.0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click for Logic (Valve)
                    # We need to calculate where the valve is in SCREEN SPACE
                    # based on the current camera
                    
                    # 1. Calc World Pos of Valve
                    w_valve_x = world_main_x + (VALVE_POS * CELL_SIZE)
                    w_valve_y = world_main_y
                    w_valve_w = CELL_SIZE * 3 # rough hit box
                    w_valve_h = CELL_SIZE * NUM_LANES
                    
                    # 2. Convert to Screen Rect
                    sx, sy = camera.world_to_screen(w_valve_x, w_valve_y)
                    sw = w_valve_w * camera.zoom
                    sh = w_valve_h * camera.zoom
                    
                    # 3. Create Rect and Check
                    # Expand hit area slightly for ease of use
                    valve_rect = pygame.Rect(sx - 10, sy - 20, sw + 20, sh + 40)
                    
                    if valve_rect.collidepoint(event.pos):
                        main_pipe.valve_open = not main_pipe.valve_open

            # Pass event to camera
            camera.handle_event(event)

        # --- PHYSICS LOOP ---
        for _ in range(PHYSICS_STEPS_PER_FRAME):
            if pumping:
                main_pipe.inject()
            main_pipe.update()
            branch_pipe.update()
            handle_junction(main_pipe, branch_pipe)
            physics_ticks += 1

        # --- RENDER LOOP ---
        screen.fill(COLOR_BG)
        draw_grid(screen, camera) # Helper grid

        # Draw Pipes
        draw_pipe(screen, branch_pipe, world_junc_x, world_junc_y, camera)
        draw_pipe(screen, main_pipe, world_main_x, world_main_y, camera)

        # Draw Valve (Overlay)
        # Recalculate screen position for drawing
        w_valve_x = world_main_x + (VALVE_POS * CELL_SIZE)
        s_valve_x, s_valve_y = camera.world_to_screen(w_valve_x, world_main_y)
        s_valve_h = (NUM_LANES * CELL_SIZE) * camera.zoom
        
        v_col = COLOR_VALVE_OPEN if main_pipe.valve_open else COLOR_VALVE_CLOSED
        
        # Draw Valve Body
        pygame.draw.rect(screen, v_col, (s_valve_x - 5, s_valve_y - 20, 10, s_valve_h + 40), 2)
        
        # Draw Valve Gate (Line inside)
        if not main_pipe.valve_open:
            pygame.draw.line(screen, v_col, 
                             (s_valve_x, s_valve_y), 
                             (s_valve_x, s_valve_y + s_valve_h), 4)


        # --- UI OVERLAY (Static, ignores camera) ---
        if frame_count % 30 == 0:
            current_time = time.time()
            dt = current_time - start_time
            if dt > 0:
                fps_display = frame_count / dt
                tps_display = physics_ticks / dt 

        stats_surf = pygame.Surface((350, 120), pygame.SRCALPHA)
        stats_surf.fill(COLOR_UI_BG)
        screen.blit(stats_surf, (10, 10))
        
        screen.blit(bold_font.render(f"FPS: {fps_display:.0f} | TPS: {tps_display:.0f}", True, COLOR_SOURCE), (20, 20))
        screen.blit(font.render(f"Zoom: {camera.zoom:.2f}x", True, COLOR_TEXT), (20, 50))
        screen.blit(font.render(f"Right-Drag: PAN | Wheel: ZOOM", True, (200, 200, 200)), (20, 80))

        pygame.display.flip()
        frame_count += 1

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
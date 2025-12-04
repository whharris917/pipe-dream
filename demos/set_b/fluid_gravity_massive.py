import pygame
import random
import sys
import math
import time

# --- CONFIGURATION ---
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800
PHYSICS_STEPS_PER_FRAME = 60 

# Geometry (3x Larger)
PIPE_LENGTH = 600    
NUM_LANES = 48            
CELL_SIZE = 5             

# --- THERMODYNAMICS ---
KT = 0.5                
GRAVITY_POTENTIAL = 0.4 # Gravity is ON. Fluid settles to the bottom.
INTERACTION_J = 3.0     
MAX_MOVE_PROB = 0.5

# Colors
COLOR_BG = (15, 15, 20)
COLOR_GRID = (30, 30, 35)
COLOR_PIPE_BG = (35, 35, 35)
COLOR_SOURCE_A = (0, 255, 0)   # Green (Left)
COLOR_SOURCE_B = (255, 0, 0)   # Red (Right)
COLOR_TEXT = (255, 255, 255)
COLOR_UI_BG = (0, 0, 0, 180)

class Camera:
    def __init__(self):
        self.offset_x = 50
        self.offset_y = 200
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
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
    def __init__(self, length, lanes):
        self.length = length
        self.lanes = lanes
        self.states_a = [0] * lanes 
        self.states_b = [0] * lanes 
        self.mask = (1 << length) - 1 
        
        self.mu_left = 4.0
        self.mu_right = 2.0 # Lower right pressure so we see flow

        # Horizontal Pipe Vectors with Gravity
        # Longitudinal: No gravity bias (Level pipe)
        self.dE_long = 0.0 
        
        # Transverse: Gravity pulls Down (+Energy if moving up)
        self.dE_trans_down = -GRAVITY_POTENTIAL # Favorable
        self.dE_trans_up   = GRAVITY_POTENTIAL  # Unfavorable

    def reset(self):
        self.states_a = [0] * self.lanes
        self.states_b = [0] * self.lanes

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

    def generate_boundary_mask(self, mu, length):
        if mu <= 0: prob = 0.0
        else: prob = 1.0 - math.exp(-mu * 0.3)
        
        if prob <= 0.01: return 0
        if prob >= 0.99: return (1 << length) - 1
        
        r1 = random.getrandbits(length)
        if prob > 0.5:
            r2 = random.getrandbits(length)
            return r1 | r2 if prob > 0.75 else r1
        else:
            r2 = random.getrandbits(length)
            return r1 & r2 if prob < 0.25 else r1

    def step_monte_carlo(self):
        directions = [0, 1, 2, 3]
        random.shuffle(directions)
        
        res_mask_left = self.generate_boundary_mask(self.mu_left, self.lanes)
        res_mask_right = self.generate_boundary_mask(self.mu_right, self.lanes)

        for d in directions:
            # --- SETUP ---
            if d == 0: # Right
                shift_op = lambda s: (s << 1)
                rev_op   = lambda s: (s >> 1)
                dE_base = self.dE_long
                is_long = True
            elif d == 1: # Left
                shift_op = lambda s: (s >> 1)
                rev_op   = lambda s: (s << 1)
                dE_base = self.dE_long
                is_long = True
            elif d == 2: # Down
                dE_base = self.dE_trans_down
                is_long = False
                src_off, tgt_off = 0, 1
                rng = range(self.lanes - 2, -1, -1)
            elif d == 3: # Up
                dE_base = self.dE_trans_up
                is_long = False
                src_off, tgt_off = 1, 0
                rng = range(0, self.lanes - 1, 1)

            # --- LONGITUDINAL ---
            if is_long:
                phantom_left = (1 << (self.length - 1)) if self.mu_left > 0 else 0
                phantom_right = 1 if self.mu_right > 0 else 0

                for i in range(self.lanes):
                    state_a = self.states_a[i]
                    state_b = self.states_b[i]
                    total = state_a | state_b
                    
                    if d == 0: # Right
                        candidates = (total << 1) & (~total)
                        neighbors = (total >> 1) # Internal neighbor left
                        
                        # Boundary Injection Left
                        res_has_particle = (res_mask_left >> i) & 1
                        pipe_empty_at_0 = not (total & 1)
                        if res_has_particle:
                            neighbors |= 1 
                            if pipe_empty_at_0:
                                # We handle injection via probability logic below, 
                                # or assume "Push" creates space. 
                                pass

                    else: # Left
                        candidates = (total >> 1) & (~total)
                        neighbors = (total << 1)
                        
                        # Boundary Injection Right
                        res_has_particle = (res_mask_right >> i) & 1
                        if res_has_particle:
                            neighbors |= (1 << (self.length - 1))

                    # Energy
                    has_neighbor_behind = neighbors & total
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor_behind & mask_pushed) | \
                                 (~has_neighbor_behind & mask_lonely)
                    
                    valid_moves = candidates & acceptance & self.mask
                    
                    # Apply A
                    sources_a = state_a & rev_op(valid_moves)
                    dests_a   = shift_op(sources_a)
                    self.states_a[i] = (state_a ^ sources_a) | dests_a
                    
                    # Apply B
                    sources_b = state_b & rev_op(valid_moves)
                    dests_b   = shift_op(sources_b)
                    self.states_b[i] = (state_b ^ sources_b) | dests_b
                    
                    # --- BOUNDARY EXCHANGE ---
                    # 1. Exit (Sink)
                    if d == 0: # Exit Right
                        res_space = not ((res_mask_right >> i) & 1)
                        if res_space:
                            at_end = (1 << (self.length - 1))
                            if total & at_end:
                                # Neighbor at L-2?
                                has_neigh = (total & (at_end >> 1))
                                mask = mask_pushed if has_neigh else mask_lonely
                                if mask & at_end:
                                    self.states_a[i] &= ~at_end
                                    self.states_b[i] &= ~at_end
                    elif d == 1: # Exit Left
                        res_space = not ((res_mask_left >> i) & 1)
                        if res_space:
                            at_start = 1
                            if total & at_start:
                                has_neigh = (total & 2)
                                mask = mask_pushed if has_neigh else mask_lonely
                                if mask & at_start:
                                    self.states_a[i] &= ~at_start
                                    self.states_b[i] &= ~at_start
                                    
                    # 2. Enter (Source)
                    if d == 0: # Enter Left
                        res_part = (res_mask_left >> i) & 1
                        if res_part:
                            if not (total & 1):
                                if mask_pushed & 1:
                                    self.states_a[i] |= 1
                    elif d == 1: # Enter Right
                        res_part = (res_mask_right >> i) & 1
                        if res_part:
                            bit_L = (1 << (self.length - 1))
                            if not (total & bit_L):
                                if mask_pushed & bit_L:
                                    self.states_b[i] |= bit_L

            # --- TRANSVERSE ---
            else:
                for i in rng:
                    src_idx = i + src_off
                    tgt_idx = i + tgt_off
                    
                    src_tot = self.states_a[src_idx] | self.states_b[src_idx]
                    tgt_tot = self.states_a[tgt_idx] | self.states_b[tgt_idx]
                    
                    candidates = src_tot & (~tgt_tot)
                    
                    if d == 2: # Down
                        has_neighbor = (self.states_a[i-1]|self.states_b[i-1]) & src_tot if i>0 else 0
                    else: # Up
                        has_neighbor = (self.states_a[i+2]|self.states_b[i+2]) & src_tot if i<self.lanes-2 else 0
                        
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    acceptance = (has_neighbor & mask_pushed) | (~has_neighbor & mask_lonely)
                    
                    valid = candidates & acceptance
                    
                    move_a = valid & self.states_a[src_idx]
                    self.states_a[src_idx] ^= move_a
                    self.states_a[tgt_idx] |= move_a
                    
                    move_b = valid & self.states_b[src_idx]
                    self.states_b[src_idx] ^= move_b
                    self.states_b[tgt_idx] |= move_b

def draw_pipe(screen, pipe, start_x, start_y, cell_size, camera):
    # Only draw what is on screen
    # Simple check: calculate bounds
    
    # Just draw full pipe relative to camera
    len_px = pipe.length * cell_size
    wid_px = pipe.lanes * cell_size
    
    # Screen Coords for top left
    sx, sy = camera.world_to_screen(start_x, start_y)
    
    # Scale dimensions
    sw = len_px * camera.zoom
    sh = wid_px * camera.zoom
    
    # Cull
    if sx + sw < 0 or sx > DEFAULT_WIDTH or sy + sh < 0 or sy > DEFAULT_HEIGHT:
        return # Off screen

    # Draw BG
    pygame.draw.rect(screen, COLOR_PIPE_BG, (sx, sy, sw, sh))

    # Draw Particles
    # If zoom is very low, drawing individual pixels is expensive and invisible.
    # Level of Detail optimization:
    if camera.zoom < 0.2:
        return # Skip particles if too small

    scaled_cell = cell_size * camera.zoom
    # Render loop
    for lane_idx in range(pipe.lanes):
        row_a = pipe.states_a[lane_idx]
        row_b = pipe.states_b[lane_idx]
        if (row_a | row_b) == 0: continue

        for bit_idx in range(pipe.length):
            mask = 1 << bit_idx
            is_a = row_a & mask
            is_b = row_b & mask
            
            if is_a or is_b:
                draw_x = sx + (bit_idx * scaled_cell)
                draw_y = sy + (lane_idx * scaled_cell)
                
                # Simple culling per pixel
                if draw_x < -scaled_cell or draw_x > DEFAULT_WIDTH: continue
                
                color = COLOR_SOURCE_A if is_a else COLOR_SOURCE_B
                # Draw slightly larger to avoid gaps
                pygame.draw.rect(screen, color, (draw_x, draw_y, math.ceil(scaled_cell), math.ceil(scaled_cell)))

def draw_grid(screen, camera):
    grid_spacing = 100 * camera.zoom
    if grid_spacing < 20: return
    
    start_x = (camera.offset_x % grid_spacing) - grid_spacing
    start_y = (camera.offset_y % grid_spacing) - grid_spacing
    
    cols = int(DEFAULT_WIDTH / grid_spacing) + 2
    rows = int(DEFAULT_HEIGHT / grid_spacing) + 2
    
    for c in range(cols):
        x = start_x + (c * grid_spacing)
        pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, DEFAULT_HEIGHT))
    for r in range(rows):
        y = start_y + (r * grid_spacing)
        pygame.draw.line(screen, COLOR_GRID, (0, y), (DEFAULT_WIDTH, y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Massive Pipe Gravity Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    bold_font = pygame.font.SysFont("monospace", 24, bold=True)

    camera = Camera()
    
    pipe = BitwisePipe(PIPE_LENGTH, NUM_LANES)
    
    running = True
    paused = False
    
    pipe_world_x = 100
    pipe_world_y = 300

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE: pass 
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click logic
                    pass
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    pipe.reset()
                elif event.key == pygame.K_q:
                    pipe.mu_left += 1.0
                elif event.key == pygame.K_a:
                    pipe.mu_left -= 1.0
                elif event.key == pygame.K_w:
                    pipe.mu_right += 1.0
                elif event.key == pygame.K_s:
                    pipe.mu_right -= 1.0
            
            camera.handle_event(event)

        if not paused:
            for _ in range(PHYSICS_STEPS_PER_FRAME):
                pipe.step_monte_carlo()

        screen.fill(COLOR_BG)
        draw_grid(screen, camera)
        
        draw_pipe(screen, pipe, pipe_world_x, pipe_world_y, CELL_SIZE, camera)

        # UI Overlay (Fixed position)
        stats_surf = pygame.Surface((400, 180), pygame.SRCALPHA)
        stats_surf.fill(COLOR_UI_BG)
        screen.blit(stats_surf, (10, 10))
        
        screen.blit(bold_font.render("MASSIVE PIPE DEMO", True, COLOR_TEXT), (20, 20))
        screen.blit(font.render(f"Size: {PIPE_LENGTH} x {NUM_LANES}", True, (200, 200, 200)), (20, 50))
        
        screen.blit(font.render(f"Left Mu (Green): {pipe.mu_left:.1f} [Q/A]", True, COLOR_SOURCE_A), (20, 80))
        screen.blit(font.render(f"Right Mu (Red):  {pipe.mu_right:.1f} [W/S]", True, COLOR_SOURCE_B), (20, 100))
        
        screen.blit(font.render("Use Scroll Wheel to Zoom.", True, (150, 150, 150)), (20, 130))
        screen.blit(font.render("Right Click + Drag to Pan.", True, (150, 150, 150)), (20, 150))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
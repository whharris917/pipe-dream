import pygame
import random
import sys

# --- CONFIGURATION ---
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# Geometry
MAIN_PIPE_LENGTH = 200    
BRANCH_PIPE_LENGTH = 100  
NUM_LANES = 16            
CELL_SIZE = 4             # Smaller cells to make the diagonal look smoother

# Topology
VALVE_POS = MAIN_PIPE_LENGTH // 2
JUNCTION_POS = (MAIN_PIPE_LENGTH * 3) // 4  # 75% down the pipe

# Physics Knobs
PROB_FLOW_MAIN = 0.90     
PROB_FLOW_BRANCH = 1.0    # Gravity accelerates flow in diagonal/vertical
GRAVITY_PASSES = 4        

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_BG = (30, 30, 30)
COLOR_FLUID_TOP = (0, 191, 255)    
COLOR_FLUID_BOT = (0, 50, 120)     
COLOR_SOURCE = (0, 255, 0)
COLOR_WALL = (255, 50, 50)
COLOR_VALVE_OPEN = (0, 255, 0)
COLOR_VALVE_CLOSED = (255, 0, 0)
COLOR_TEXT = (255, 255, 255)

class BitwisePipe:
    def __init__(self, length, lanes, orientation='horizontal'):
        self.length = length
        self.lanes = lanes
        self.states = [0] * lanes 
        self.mask = (1 << length) - 1 
        self.orientation = orientation
        self.valve_active = False 
        self.valve_open = True

    def reset(self):
        self.states = [0] * self.lanes

    def inject(self, pump_rate=1.0):
        entry_bit = 1 << (self.length - 1)
        for i in range(self.lanes):
            if random.random() < pump_rate:
                self.states[i] |= entry_bit

    def update(self, flow_prob):
        
        # --- 1. TRANSVERSE PHYSICS (Gravity/Settling) ---
        
        # HORIZONTAL: Gravity pulls Top Lanes -> Bottom Lanes
        # DIAGONAL: Gravity pulls Top-Left Lanes -> Bottom-Right Lanes (Same logic)
        # VERTICAL: Gravity has no transverse component (Mixing only)
        
        if self.orientation in ['horizontal', 'diagonal']:
            # Apply strong transverse gravity
            for _ in range(GRAVITY_PASSES):
                for i in range(self.lanes - 2, -1, -1):
                    upper = self.states[i]
                    lower = self.states[i+1]
                    falling = upper & (~lower)
                    self.states[i] ^= falling
                    self.states[i+1] |= falling
        
        elif self.orientation == 'vertical':
            # Horizontal mixing for vertical pipes
            for i in range(self.lanes - 1):
                left = self.states[i]
                right = self.states[i+1]
                
                # Right -> Left
                move_left = right & (~left) & random.getrandbits(self.length)
                self.states[i+1] ^= move_left
                self.states[i] |= move_left
                
                # Left -> Right
                move_right = left & (~right) & random.getrandbits(self.length)
                self.states[i] ^= move_right
                self.states[i+1] |= move_right

        # --- 2. LONGITUDINAL FLOW ---
        
        valve_blocker = self.mask
        if self.valve_active and not self.valve_open:
            valve_bit_index = self.length - 1 - VALVE_POS
            valve_blocker = ~(1 << valve_bit_index) & self.mask

        for i in range(self.lanes):
            state = self.states[i]
            candidates = (state >> 1) & (~state) & self.mask
            
            r1 = random.getrandbits(self.length)
            r2 = random.getrandbits(self.length)
            flow_mask = r1 | r2 
            
            valid_moves = candidates & flow_mask & valve_blocker
            self.states[i] = state ^ valid_moves ^ (valid_moves << 1)

        # --- 3. BACKWARDS DIFFUSION ---
        # Low in diagonal/vertical (Gravity fights it)
        diff_chance = 0.1 if self.orientation == 'horizontal' else 0.005
        
        for i in range(self.lanes):
            state = self.states[i]
            candidates = (state << 1) & (~state) & self.mask
            
            r1 = random.getrandbits(self.length)
            r2 = random.getrandbits(self.length)
            diff_mask = r1 & r2
            
            if random.random() > diff_chance: 
                diff_mask = 0

            valid_moves = candidates & diff_mask & valve_blocker
            self.states[i] = state ^ valid_moves ^ (valid_moves >> 1)

        # Cleanup
        for i in range(self.lanes):
            self.states[i] &= self.mask


def handle_junction(main, branch):
    """
    Moves particles from Main Pipe to Branch Pipe.
    """
    junction_bit_idx = main.length - 1 - JUNCTION_POS
    branch_inlet_idx = branch.length - 1
    
    falling_particles_count = 0
    
    for i in range(NUM_LANES):
        if (main.states[i] >> junction_bit_idx) & 1:
            main.states[i] &= ~(1 << junction_bit_idx)
            falling_particles_count += 1
    
    # Splash logic
    if falling_particles_count > 0:
        available_lanes = list(range(NUM_LANES))
        random.shuffle(available_lanes)
        
        for _ in range(falling_particles_count):
            if not available_lanes: break
            target_lane = available_lanes.pop()
            if not ((branch.states[target_lane] >> branch_inlet_idx) & 1):
                branch.states[target_lane] |= (1 << branch_inlet_idx)

def draw_pipe(screen, pipe, start_x, start_y, cell_size):
    # BACKGROUND DRAWING
    if pipe.orientation == 'horizontal':
        # Simple Rect
        w = pipe.length * cell_size
        h = pipe.lanes * cell_size
        pygame.draw.rect(screen, COLOR_PIPE_BG, (start_x, start_y, w, h))
    elif pipe.orientation == 'diagonal':
        # Polygon for diagonal pipe
        # We calculate the 4 corners of the pipe grid
        
        # Vector along pipe (Length)
        dx_len = (pipe.length * cell_size)
        dy_len = (pipe.length * cell_size)
        
        # Vector across pipe (Lanes) - Perpendicular (-1, 1)
        dx_width = -(pipe.lanes * cell_size)
        dy_width = (pipe.lanes * cell_size)
        
        p1 = (start_x, start_y)
        p2 = (start_x + dx_len, start_y + dy_len)
        p3 = (start_x + dx_len + dx_width, start_y + dy_len + dy_width)
        p4 = (start_x + dx_width, start_y + dy_width)
        
        pygame.draw.polygon(screen, COLOR_PIPE_BG, [p1, p2, p3, p4])

    # FLUID DRAWING
    for lane_idx in range(pipe.lanes):
        state = pipe.states[lane_idx]
        
        t = lane_idx / (pipe.lanes - 1)
        color = (
            int(COLOR_FLUID_TOP[0] * (1-t) + COLOR_FLUID_BOT[0] * t),
            int(COLOR_FLUID_TOP[1] * (1-t) + COLOR_FLUID_BOT[1] * t),
            int(COLOR_FLUID_TOP[2] * (1-t) + COLOR_FLUID_BOT[2] * t),
        )

        for bit_idx in range(pipe.length):
            if (state >> bit_idx) & 1:
                dist = pipe.length - 1 - bit_idx
                
                if pipe.orientation == 'horizontal':
                    draw_x = start_x + (dist * cell_size)
                    draw_y = start_y + (lane_idx * cell_size)
                
                elif pipe.orientation == 'diagonal':
                    # Coordinate Transform:
                    # Flow moves (1, 1)
                    # Lanes move (-1, 1)
                    
                    # Center the flow on the start point roughly
                    flow_offset_x = dist * cell_size
                    flow_offset_y = dist * cell_size
                    
                    lane_offset_x = -(lane_idx * cell_size)
                    lane_offset_y = (lane_idx * cell_size)
                    
                    draw_x = start_x + flow_offset_x + lane_offset_x
                    draw_y = start_y + flow_offset_y + lane_offset_y
                
                pygame.draw.rect(screen, color, (draw_x, draw_y, cell_size, cell_size))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("45-Degree Pipe Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    bold_font = pygame.font.SysFont("monospace", 16, bold=True)

    main_pipe = BitwisePipe(MAIN_PIPE_LENGTH, NUM_LANES, 'horizontal')
    main_pipe.valve_active = True
    
    # 45-Degree Branch
    branch_pipe = BitwisePipe(BRANCH_PIPE_LENGTH, NUM_LANES, 'diagonal')

    pumping = True

    # Geometry Setup
    main_x = (SCREEN_WIDTH - (MAIN_PIPE_LENGTH * CELL_SIZE)) // 2 + 100
    main_y = 200 
    
    # Junction is at main_x + offset
    junction_pixel_x = main_x + (JUNCTION_POS * CELL_SIZE)
    junction_pixel_y = main_y + (NUM_LANES * CELL_SIZE) # Bottom of main pipe
    
    # Branch starts exactly where the junction is.
    # Note: In our diagonal draw logic, (StartX, StartY) is the top-left corner of the Inlet (Lane 0).
    # Since Main Pipe drops from bottom (Lane 15), we need to adjust start position
    # so the branch "Inlet" aligns with the Main Pipe "Outlet" zone.
    # Actually, simpler: Start branch at Junction X, Main Y + Height.
    branch_x = junction_pixel_x 
    branch_y = junction_pixel_y 

    valve_x_pixel = main_x + (VALVE_POS * CELL_SIZE)
    valve_rect = pygame.Rect(valve_x_pixel - 5, main_y - 20, 
                             CELL_SIZE + 10, (NUM_LANES * CELL_SIZE) + 40)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and valve_rect.collidepoint(pygame.mouse.get_pos()):
                    main_pipe.valve_open = not main_pipe.valve_open
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pumping = not pumping
                elif event.key == pygame.K_r:
                    main_pipe.reset()
                    branch_pipe.reset()

        # --- PHYSICS ---
        if pumping:
            main_pipe.inject()
        
        main_pipe.update(PROB_FLOW_MAIN)
        branch_pipe.update(PROB_FLOW_BRANCH)
        
        handle_junction(main_pipe, branch_pipe)

        # --- DRAWING ---
        screen.fill(COLOR_BG)
        
        draw_pipe(screen, branch_pipe, branch_x, branch_y, CELL_SIZE)
        draw_pipe(screen, main_pipe, main_x, main_y, CELL_SIZE) # Draw main on top to cover seams

        h_height = NUM_LANES * CELL_SIZE
        pygame.draw.rect(screen, COLOR_SOURCE, (main_x - 10, main_y, 10, h_height)) 
        pygame.draw.rect(screen, COLOR_WALL, (main_x + (MAIN_PIPE_LENGTH * CELL_SIZE), main_y, 10, h_height))
        
        # Valve
        v_col = COLOR_VALVE_OPEN if main_pipe.valve_open else COLOR_VALVE_CLOSED
        pygame.draw.rect(screen, v_col, valve_rect, width=2, border_radius=3)
        if not main_pipe.valve_open:
            pygame.draw.line(screen, v_col, (valve_x_pixel + CELL_SIZE//2, main_y), 
                             (valve_x_pixel + CELL_SIZE//2, main_y + h_height), 4)

        # UI
        ui_x, ui_y = 20, 20
        screen.blit(bold_font.render("45-DEGREE GRAVITY DEMO", True, COLOR_TEXT), (ui_x, ui_y))
        ui_y += 30
        screen.blit(font.render("Horizontal Pipe: Transverse Gravity (Top->Bot)", True, (150,150,150)), (ui_x, ui_y))
        ui_y += 20
        screen.blit(font.render("Diagonal Pipe: Combined Gravity (Flows Fast + Hugs Bottom Wall)", True, (150,150,150)), (ui_x, ui_y))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
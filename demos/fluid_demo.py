import pygame
import random
import sys

# --- CONFIGURATION ---
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
FPS = 60

# Geometry
MAIN_PIPE_LENGTH = 240    
BRANCH_PIPE_LENGTH = 100 
NUM_LANES = 16            
CELL_SIZE = 5             

# Topology
VALVE_POS = MAIN_PIPE_LENGTH // 2
JUNCTION_POS = (MAIN_PIPE_LENGTH * 3) // 4  # 75% down the pipe

# Physics Knobs
PROB_FLOW_MAIN = 0.90     
PROB_FLOW_BRANCH = 1.0    # Vertical pipe falls at max speed
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
        
        # --- 1. TRANSVERSE PHYSICS (Lane-to-Lane interactions) ---
        
        if self.orientation == 'horizontal':
            # STANDARD GRAVITY: Fluid falls from Top Lanes to Bottom Lanes
            for _ in range(GRAVITY_PASSES):
                for i in range(self.lanes - 2, -1, -1):
                    upper = self.states[i]
                    lower = self.states[i+1]
                    falling = upper & (~lower)
                    self.states[i] ^= falling
                    self.states[i+1] |= falling
        
        else: # Vertical Pipe
            # HORIZONTAL MIXING: Fluid spreads out to fill the width of the pipe
            # It doesn't fall "down" lanes, it diffuses across them.
            for i in range(self.lanes - 1):
                left = self.states[i]
                right = self.states[i+1]
                
                # Randomly swap particles between lanes to simulate turbulence/filling
                # We want particles to move into empty spots sideways
                
                # Move Right -> Left
                move_left = right & (~left)
                # Random mask for mixing speed
                r1 = random.getrandbits(self.length)
                move_left &= r1 
                
                self.states[i+1] ^= move_left
                self.states[i] |= move_left
                
                # Move Left -> Right
                move_right = left & (~right)
                r2 = random.getrandbits(self.length)
                move_right &= r2
                
                self.states[i] ^= move_right
                self.states[i+1] |= move_right


        # --- 2. LONGITUDINAL FLOW (Along the length) ---
        
        valve_blocker = self.mask
        if self.valve_active and not self.valve_open:
            valve_bit_index = self.length - 1 - VALVE_POS
            valve_blocker = ~(1 << valve_bit_index) & self.mask

        for i in range(self.lanes):
            state = self.states[i]
            candidates = (state >> 1) & (~state) & self.mask
            
            # Stochastic Flow Mask
            r1 = random.getrandbits(self.length)
            r2 = random.getrandbits(self.length)
            flow_mask = r1 | r2 
            
            valid_moves = candidates & flow_mask & valve_blocker
            self.states[i] = state ^ valid_moves ^ (valid_moves << 1)

        # --- 3. BACKWARDS DIFFUSION ---
        # Very low in vertical pipes (gravity prevents floating up)
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
    Moves particles from Main Pipe (at JUNCTION_POS) 
    to Branch Pipe (at Inlet).
    """
    junction_bit_idx = main.length - 1 - JUNCTION_POS
    branch_inlet_idx = branch.length - 1
    
    # We create a list of particles falling out of the main pipe
    falling_particles_count = 0
    
    for i in range(NUM_LANES):
        # Remove particle from main pipe
        if (main.states[i] >> junction_bit_idx) & 1:
            main.states[i] &= ~(1 << junction_bit_idx)
            falling_particles_count += 1
    
    # "Splash" logic:
    # If particles fell, inject them into RANDOM lanes in the branch pipe.
    # This prevents the "single lane stream" artifact.
    if falling_particles_count > 0:
        available_lanes = list(range(NUM_LANES))
        random.shuffle(available_lanes)
        
        for _ in range(falling_particles_count):
            if not available_lanes: break # Branch inlet is 100% full
            
            target_lane = available_lanes.pop()
            # Only inject if spot is empty
            if not ((branch.states[target_lane] >> branch_inlet_idx) & 1):
                branch.states[target_lane] |= (1 << branch_inlet_idx)

def draw_pipe(screen, pipe, start_x, start_y, cell_size):
    if pipe.orientation == 'horizontal':
        w = pipe.length * cell_size
        h = pipe.lanes * cell_size
    else:
        w = pipe.lanes * cell_size
        h = pipe.length * cell_size
        
    pygame.draw.rect(screen, COLOR_PIPE_BG, (start_x, start_y, w, h))
    
    for lane_idx in range(pipe.lanes):
        state = pipe.states[lane_idx]
        
        # Color Logic
        t = lane_idx / (pipe.lanes - 1)
        color = (
            int(COLOR_FLUID_TOP[0] * (1-t) + COLOR_FLUID_BOT[0] * t),
            int(COLOR_FLUID_TOP[1] * (1-t) + COLOR_FLUID_BOT[1] * t),
            int(COLOR_FLUID_TOP[2] * (1-t) + COLOR_FLUID_BOT[2] * t),
        )

        for bit_idx in range(pipe.length):
            if (state >> bit_idx) & 1:
                if pipe.orientation == 'horizontal':
                    draw_x = start_x + ((pipe.length - 1 - bit_idx) * cell_size)
                    draw_y = start_y + (lane_idx * cell_size)
                else:
                    # Vertical drawing
                    draw_y = start_y + ((pipe.length - 1 - bit_idx) * cell_size)
                    draw_x = start_x + (lane_idx * cell_size)
                
                pygame.draw.rect(screen, color, (draw_x, draw_y, cell_size, cell_size))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Network Demo: Chaotic Branching")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    bold_font = pygame.font.SysFont("monospace", 16, bold=True)

    main_pipe = BitwisePipe(MAIN_PIPE_LENGTH, NUM_LANES, 'horizontal')
    main_pipe.valve_active = True
    
    branch_pipe = BitwisePipe(BRANCH_PIPE_LENGTH, NUM_LANES, 'vertical')

    pumping = True

    # Geometry Setup
    main_x = (SCREEN_WIDTH - (MAIN_PIPE_LENGTH * CELL_SIZE)) // 2
    main_y = 200 
    
    branch_x = main_x + (JUNCTION_POS * CELL_SIZE)
    branch_y = main_y + (NUM_LANES * CELL_SIZE) 

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
        draw_pipe(screen, main_pipe, main_x, main_y, CELL_SIZE)
        draw_pipe(screen, branch_pipe, branch_x, branch_y, CELL_SIZE)

        h_height = NUM_LANES * CELL_SIZE
        pygame.draw.rect(screen, COLOR_SOURCE, (main_x - 10, main_y, 10, h_height)) 
        pygame.draw.rect(screen, COLOR_WALL, (main_x + (MAIN_PIPE_LENGTH * CELL_SIZE), main_y, 10, h_height))
        v_width = NUM_LANES * CELL_SIZE
        pygame.draw.rect(screen, COLOR_WALL, (branch_x, branch_y + (BRANCH_PIPE_LENGTH * CELL_SIZE), v_width, 10))

        v_col = COLOR_VALVE_OPEN if main_pipe.valve_open else COLOR_VALVE_CLOSED
        pygame.draw.rect(screen, v_col, valve_rect, width=2, border_radius=3)
        if not main_pipe.valve_open:
            pygame.draw.line(screen, v_col, (valve_x_pixel + CELL_SIZE//2, main_y), 
                             (valve_x_pixel + CELL_SIZE//2, main_y + h_height), 4)

        ui_x, ui_y = 20, 20
        screen.blit(bold_font.render("CHAOTIC BRANCHING DEMO", True, COLOR_TEXT), (ui_x, ui_y))
        ui_y += 30
        screen.blit(font.render("Horizontal Pipe: Gravity pulls to bottom (Transverse).", True, (150,150,150)), (ui_x, ui_y))
        ui_y += 20
        screen.blit(font.render("Vertical Pipe: Turbulence mixes fluid across width.", True, (150,150,150)), (ui_x, ui_y))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
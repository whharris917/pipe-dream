import pygame
import random
import sys
import math

# --- CONFIGURATION ---
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# Geometry
MAIN_PIPE_LENGTH = 200    
BRANCH_PIPE_LENGTH = 120  
NUM_LANES = 16            
CELL_SIZE = 5             

# Topology
VALVE_POS = MAIN_PIPE_LENGTH // 2
JUNCTION_POS = (MAIN_PIPE_LENGTH * 3) // 4 

# Physics Knobs (TUNED FOR LEVELING)
GLOBAL_PRESSURE = 0.90     # Strong pump
GLOBAL_GRAVITY = 0.50      # Reduced slightly to prevent "concrete stacking"
BASE_DIFFUSION = 0.60      # High diffusion allows the pile to collapse (level out)

# Colors
COLOR_BG = (20, 20, 20)
COLOR_PIPE_BG = (35, 35, 35)
COLOR_FLUID_TOP = (0, 191, 255)    
COLOR_FLUID_BOT = (0, 50, 120)     
COLOR_SOURCE = (0, 255, 0)
COLOR_WALL = (255, 50, 50)
COLOR_VALVE_OPEN = (0, 255, 0)
COLOR_VALVE_CLOSED = (255, 0, 0)
COLOR_TEXT = (255, 255, 255)

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
        # --- CALCULATE FORCES ---
        
        # 1. Transverse (Across Lanes)
        force_trans_down = abs(self.g_trans * GLOBAL_GRAVITY)
        
        # FIX: Diffusion is now a constant base energy. 
        # We don't subtract gravity here. We let the stochastic nature fight it out.
        # This allows particles to "boil" out of the bottom lane.
        force_trans_up = BASE_DIFFUSION 

        # 2. Longitudinal (Along Pipe)
        force_long_right = GLOBAL_PRESSURE + (self.g_long * GLOBAL_GRAVITY)
        
        # FIX: We do NOT subtract gravity from diffusion here.
        # Back-diffusion must be active to allow the pile to "slump" backwards.
        force_long_left = BASE_DIFFUSION

        valve_blocker = self.mask
        if self.valve_active and not self.valve_open:
            valve_bit_index = self.length - 1 - VALVE_POS
            valve_blocker = ~(1 << valve_bit_index) & self.mask

        # --- PHYSICS STEP ---

        # A. TRANSVERSE DOWN (Gravity)
        # Multiple passes to ensure weight is felt
        passes = 3 if force_trans_down > 0.1 else 1
        for _ in range(passes):
            for i in range(self.lanes - 2, -1, -1):
                upper = self.states[i]
                lower = self.states[i+1]
                candidates = upper & (~lower)
                
                # Gravity pushes down
                move_mask = self.get_stochastic_mask(force_trans_down + 0.2)
                falling = candidates & move_mask
                self.states[i] ^= falling
                self.states[i+1] |= falling

        # B. TRANSVERSE UP (High Mixing)
        # This is critical for leveling. It allows particles to climb 
        # so they can slide back upstream.
        if force_trans_up > 0:
            for i in range(self.lanes - 1):
                upper = self.states[i]
                lower = self.states[i+1]
                candidates = lower & (~upper)
                
                # Diffusion pushes up (randomly)
                move_mask = self.get_stochastic_mask(force_trans_up * 0.5) # Scaled down slightly
                rising = candidates & move_mask
                
                self.states[i+1] ^= rising
                self.states[i] |= rising

        # C. LONGITUDINAL MOVEMENT
        for i in range(self.lanes):
            state = self.states[i]
            
            # Flow Right (Pressure + Gravity)
            mask_right = self.get_stochastic_mask(force_long_right)
            candidates = (state >> 1) & (~state) & self.mask
            valid_moves = candidates & mask_right & valve_blocker
            state = state ^ valid_moves ^ (valid_moves << 1)

            # Flow Left (Back Diffusion)
            # This pushes the "top of the pile" back upstream
            mask_left = self.get_stochastic_mask(force_long_left)
            candidates = (state << 1) & (~state) & self.mask
            valid_moves = candidates & mask_left & valve_blocker
            state = state ^ valid_moves ^ (valid_moves >> 1)
            
            self.states[i] = state

        # Cleanup
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

def draw_pipe(screen, pipe, start_x, start_y, cell_size):
    rad = math.radians(pipe.angle)
    v_len_x = math.cos(rad) * (pipe.length * cell_size)
    v_len_y = math.sin(rad) * (pipe.length * cell_size)
    v_wid_x = -math.sin(rad) * (pipe.lanes * cell_size)
    v_wid_y = math.cos(rad) * (pipe.lanes * cell_size)
    
    p1 = (start_x, start_y)
    p2 = (start_x + v_len_x, start_y + v_len_y)
    p3 = (start_x + v_len_x + v_wid_x, start_y + v_len_y + v_wid_y)
    p4 = (start_x + v_wid_x, start_y + v_wid_y)
    pygame.draw.polygon(screen, COLOR_PIPE_BG, [p1, p2, p3, p4])

    u_len_x = math.cos(rad) * cell_size
    u_len_y = math.sin(rad) * cell_size
    u_wid_x = -math.sin(rad) * cell_size
    u_wid_y = math.cos(rad) * cell_size

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
                dist_long = pipe.length - 1 - bit_idx
                dist_trans = lane_idx
                
                draw_x = start_x + (dist_long * u_len_x) + (dist_trans * u_wid_x)
                draw_y = start_y + (dist_long * u_len_y) + (dist_trans * u_wid_y)
                
                pygame.draw.rect(screen, color, (int(draw_x), int(draw_y), cell_size, cell_size))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("True Leveling Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)

    main_pipe = BitwisePipe(MAIN_PIPE_LENGTH, NUM_LANES, angle_deg=0)
    main_pipe.valve_active = True
    
    branch_pipe = BitwisePipe(BRANCH_PIPE_LENGTH, NUM_LANES, angle_deg=45)

    pumping = True

    main_x = (SCREEN_WIDTH - (MAIN_PIPE_LENGTH * CELL_SIZE)) // 2 
    main_y = 300
    
    junction_x = main_x + (JUNCTION_POS * CELL_SIZE)
    junction_y = main_y + (NUM_LANES * CELL_SIZE)
    
    valve_x = main_x + (VALVE_POS * CELL_SIZE)
    valve_rect = pygame.Rect(valve_x - 5, main_y - 20, 15, 100)

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

        if pumping:
            main_pipe.inject()
        
        main_pipe.update()
        branch_pipe.update()
        
        handle_junction(main_pipe, branch_pipe)

        screen.fill(COLOR_BG)
        
        draw_pipe(screen, branch_pipe, junction_x, junction_y, CELL_SIZE)
        draw_pipe(screen, main_pipe, main_x, main_y, CELL_SIZE)

        v_col = COLOR_VALVE_OPEN if main_pipe.valve_open else COLOR_VALVE_CLOSED
        pygame.draw.rect(screen, v_col, valve_rect, 2)
        if not main_pipe.valve_open:
            pygame.draw.line(screen, v_col, (valve_x + 2, main_y), (valve_x + 2, main_y + NUM_LANES*CELL_SIZE), 3)

        lines = [
            "HYDROSTATIC EQUILIBRIUM",
            "---------------------",
            "Gravity = 0.5, Diffusion = 0.6",
            "Gravity pushes down-stream.",
            "Diffusion pushes up-stream (and up-lane).",
            "The balance creates a natural slope ~0 degrees world space.",
            "Watch the diagonal pipe fill: it should seek a horizontal level."
        ]
        
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, COLOR_TEXT), (20, 20 + i*20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
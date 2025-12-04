import pygame
import random
import sys
import math
import time

# --- CONFIGURATION ---
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 600
PHYSICS_STEPS_PER_FRAME = 60 

# Geometry
PIPE_LENGTH = 200    
NUM_LANES = 16            
CELL_SIZE = 5             

# --- THERMODYNAMICS ---
KT = 0.5                
INTERACTION_J = 3.0     
MAX_MOVE_PROB = 0.5

# Colors
COLOR_BG = (15, 15, 20)
COLOR_PIPE_BG = (35, 35, 35)
COLOR_SOURCE_A = (0, 255, 0)   # Green
COLOR_SOURCE_B = (255, 0, 0)   # Red
COLOR_TEXT = (255, 255, 255)
COLOR_UI_BG = (0, 0, 0, 180)

class BitwisePipe:
    def __init__(self, length, lanes):
        self.length = length
        self.lanes = lanes
        self.states_a = [0] * lanes 
        self.states_b = [0] * lanes 
        self.mask = (1 << length) - 1 
        
        self.mu_left = 4.0
        self.mu_right = 6.0

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
        """
        Generates a bitmask representing the state of the Reservoir.
        High Mu = High Density (Mostly 1s).
        Low Mu = Low Density (Mostly 0s).
        """
        # Fermi-Dirac-like probability for occupancy based on potential
        # We shift Mu so that reasonable values (0-10) give good range
        # Let's say Mu=5 is 50%, Mu=10 is 99%
        # P = 1 / (1 + exp(-(mu - center)))? 
        # Simpler: P = 1 - exp(-mu). If Mu=0, P=0. If Mu=high, P=1.
        
        if mu <= 0: prob = 0.0
        else: prob = 1.0 - math.exp(-mu * 0.5) # Tuning factor 0.5
        
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
        
        # 1. GENERATE RESERVOIR STATES (The "Stochastic Phantom")
        # Instead of a single bit, we generate a whole lane's worth of boundary conditions
        # This determines if the "Next spot outside the pipe" is full or empty.
        
        # Left Reservoir (Source A)
        res_mask_left = self.generate_boundary_mask(self.mu_left, self.lanes)
        
        # Right Reservoir (Source B)
        res_mask_right = self.generate_boundary_mask(self.mu_right, self.lanes)

        for d in directions:
            # --- SETUP ---
            if d == 0: # Right (0 -> 1)
                shift_op = lambda s: (s << 1)
                rev_op   = lambda s: (s >> 1)
                dE_base = 0.0
                is_long = True
                
                # PHANTOM NEIGHBOR LOGIC (Check Left)
                # To check if lane `i` has a neighbor to its left (at -1):
                # We check the `res_mask_left` bit `i`.
                # We construct a mask `has_phantom` where bit `0` is set if res_mask has bit `i` set.
                # Actually, we can just process all lanes in a loop, getting the i-th bit of the res_mask.
                
            elif d == 1: # Left (1 -> 0)
                shift_op = lambda s: (s >> 1)
                rev_op   = lambda s: (s << 1)
                dE_base = 0.0
                is_long = True
                
            elif d == 2: # Down
                dE_base = 0.0
                is_long = False
                src_off, tgt_off = 0, 1
                rng = range(self.lanes - 2, -1, -1)
            elif d == 3: # Up
                dE_base = 0.0
                is_long = False
                src_off, tgt_off = 1, 0
                rng = range(0, self.lanes - 1, 1)

            # --- PROCESS ---
            
            if is_long:
                for i in range(self.lanes):
                    state_a = self.states_a[i]
                    state_b = self.states_b[i]
                    total = state_a | state_b
                    
                    # 1. SETUP NEIGHBORS & CANDIDATES
                    if d == 0: # Moving Right
                        # Candidate: Particle at x, Hole at x+1
                        # Base internal candidates
                        candidates = (total << 1) & (~total)
                        
                        # Neighbor Check (Left)
                        # Internal neighbors: (total >> 1)
                        neighbors = (total >> 1)
                        
                        # BOUNDARY: INJECTION (Left Edge)
                        # Can we inject from -1 to 0?
                        # If Reservoir (-1) has particle AND Pipe (0) is empty.
                        res_has_particle = (res_mask_left >> i) & 1
                        pipe_empty_at_0  = not (total & 1)
                        
                        if res_has_particle and pipe_empty_at_0:
                            # We mark bit 0 as a candidate for "Injection Move"
                            # This isn't a shift, it's a creation. We handle it in "Apply".
                            # But wait, we can handle it as a flow if we treat phantom as part of shift.
                            pass # Handled in separate Injection phase to keep logic clean?
                            # No, let's do "Push" logic here.
                            
                        # BOUNDARY: PRESSURE (Left Edge)
                        # If I am at 0, do I have a neighbor at -1?
                        if res_has_particle:
                            # The bit at 0 effectively has a neighbor at -1
                            # We add the phantom neighbor bit to the neighbors mask at bit 0.
                            neighbors |= 1 
                            
                        # BOUNDARY: EXIT (Right Edge)
                        # Can particle at L-1 move to L (Reservoir)?
                        # Only if Reservoir (L) is empty!
                        res_has_space = not ((res_mask_right >> i) & 1)
                        
                        # If res_has_space, we allow the bit at L-1 to "move right" into oblivion.
                        # We simulate this by clearing the "wall" at the end.
                        # Normal mask `self.mask` blocks exit.
                        # If space exists, we technically extend the mask for the check?
                        # Easier: Handle exit explicitly.
                        
                    else: # Moving Left
                        candidates = (total >> 1) & (~total)
                        neighbors = (total << 1)
                        
                        # Right Reservoir (Source B)
                        res_has_particle = (res_mask_right >> i) & 1
                        if res_has_particle:
                            neighbors |= (1 << (self.length - 1))
                            
                        # Exit Logic Left: Check if res_mask_left has space
                        res_has_space_left = not ((res_mask_left >> i) & 1)

                    # 2. ENERGY & ACCEPTANCE
                    has_neighbor_behind = neighbors & total
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor_behind & mask_pushed) | \
                                 (~has_neighbor_behind & mask_lonely)
                    
                    valid_moves = candidates & acceptance & self.mask
                    
                    # 3. APPLY INTERNAL MOVES
                    # A
                    src_a = state_a & rev_op(valid_moves)
                    dst_a = shift_op(src_a)
                    self.states_a[i] = (state_a ^ src_a) | dst_a
                    
                    # B
                    src_b = state_b & rev_op(valid_moves)
                    dst_b = shift_op(src_b)
                    self.states_b[i] = (state_b ^ src_b) | dst_b
                    
                    # 4. BOUNDARY: EXIT (SINKING)
                    # If pressure at boundary is low (res has space), particles fall out.
                    if d == 0: # Right Edge Exit
                        res_space_right = not ((res_mask_right >> i) & 1)
                        if res_space_right:
                            # Particle at L-1 wants to move Right.
                            # Is it pushed? (Neighbor at L-2)
                            at_end = (1 << (self.length - 1))
                            if total & at_end:
                                has_neigh = (total & (at_end >> 1))
                                # Probability to exit
                                mask = mask_pushed if has_neigh else mask_lonely
                                if mask & at_end:
                                    # Exit accepted
                                    self.states_a[i] &= ~at_end
                                    self.states_b[i] &= ~at_end
                                    
                    elif d == 1: # Left Edge Exit
                        res_space_left = not ((res_mask_left >> i) & 1)
                        if res_space_left:
                            # Particle at 0 wants to move Left
                            at_start = 1
                            if total & at_start:
                                has_neigh = (total & 2) # Bit 1
                                mask = mask_pushed if has_neigh else mask_lonely
                                if mask & at_start:
                                    self.states_a[i] &= ~at_start
                                    self.states_b[i] &= ~at_start

                    # 5. BOUNDARY: INJECTION (SOURCING)
                    # If pressure at boundary is high (res has particle), it enters.
                    if d == 0: # Left Injecting Right (Green/A)
                        res_part_left = (res_mask_left >> i) & 1
                        if res_part_left:
                            # Try inject at 0
                            if not (total & 1):
                                # It enters if pushed (phantom neighbor at -1 is the reservoir itself)
                                # Always pushed if res has particle.
                                if mask_pushed & 1:
                                    self.states_a[i] |= 1
                                    
                    elif d == 1: # Right Injecting Left (Red/B)
                        res_part_right = (res_mask_right >> i) & 1
                        if res_part_right:
                            # Try inject at L-1
                            bit_L = (1 << (self.length - 1))
                            if not (total & bit_L):
                                if mask_pushed & bit_L:
                                    self.states_b[i] |= bit_L

            else:
                # Transverse (Simplified mixing)
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
                    
                    # Move A
                    move_a = valid & self.states_a[src_idx]
                    self.states_a[src_idx] ^= move_a
                    self.states_a[tgt_idx] |= move_a
                    
                    # Move B
                    move_b = valid & self.states_b[src_idx]
                    self.states_b[src_idx] ^= move_b
                    self.states_b[tgt_idx] |= move_b

def draw_pipe(screen, pipe, start_x, start_y, cell_size):
    len_px = pipe.length * cell_size
    wid_px = pipe.lanes * cell_size
    pygame.draw.rect(screen, COLOR_PIPE_BG, (start_x, start_y, len_px, wid_px))

    for lane_idx in range(pipe.lanes):
        row_a = pipe.states_a[lane_idx]
        row_b = pipe.states_b[lane_idx]
        if (row_a | row_b) == 0: continue

        for bit_idx in range(pipe.length):
            mask = 1 << bit_idx
            is_a = row_a & mask
            is_b = row_b & mask
            
            if is_a or is_b:
                draw_x = start_x + (bit_idx * cell_size)
                draw_y = start_y + (lane_idx * cell_size)
                color = COLOR_SOURCE_A if is_a else COLOR_SOURCE_B
                pygame.draw.rect(screen, color, (draw_x, draw_y, cell_size, cell_size))

def main():
    pygame.init()
    screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Pressure Reservoir War")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)
    bold_font = pygame.font.SysFont("monospace", 24, bold=True)

    pipe = BitwisePipe(PIPE_LENGTH, NUM_LANES)
    
    running = True
    paused = False
    
    pipe_x = (DEFAULT_WIDTH - (PIPE_LENGTH * CELL_SIZE)) // 2
    pipe_y = (DEFAULT_HEIGHT - (NUM_LANES * CELL_SIZE)) // 2

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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

        if not paused:
            for _ in range(PHYSICS_STEPS_PER_FRAME):
                pipe.step_monte_carlo()

        screen.fill(COLOR_BG)
        
        pygame.draw.rect(screen, COLOR_SOURCE_A, (pipe_x - 20, pipe_y, 15, NUM_LANES*CELL_SIZE))
        pygame.draw.rect(screen, COLOR_SOURCE_B, (pipe_x + PIPE_LENGTH*CELL_SIZE + 5, pipe_y, 15, NUM_LANES*CELL_SIZE))
        
        draw_pipe(screen, pipe, pipe_x, pipe_y, CELL_SIZE)

        screen.blit(bold_font.render("RESERVOIR EQUILIBRIUM", True, COLOR_TEXT), (20, 20))
        
        l_text = f"LEFT RESERVOIR (Green)\nPotential: {pipe.mu_left:.1f}\n[Q] / [A]"
        y = 80
        for line in l_text.split('\n'):
            screen.blit(font.render(line, True, COLOR_SOURCE_A), (20, y))
            y += 20
            
        r_text = f"RIGHT RESERVOIR (Red)\nPotential: {pipe.mu_right:.1f}\n[W] / [S]"
        y = 80
        for line in r_text.split('\n'):
            screen.blit(font.render(line, True, COLOR_SOURCE_B), (DEFAULT_WIDTH - 250, y))
            y += 20

        screen.blit(font.render("High Potential = Injecting more + Absorbing less.", True, (150, 150, 150)), (DEFAULT_WIDTH//2 - 250, 500))
        screen.blit(font.render("Low Potential = Injecting less + Absorbing more.", True, (150, 150, 150)), (DEFAULT_WIDTH//2 - 250, 520))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
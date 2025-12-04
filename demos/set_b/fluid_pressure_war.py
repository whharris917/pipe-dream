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
GRAVITY_POTENTIAL = 0.0 # Horizontal pipe for this demo
INTERACTION_J = 3.0     # Strong repulsion to visualize pressure fronts
MAX_MOVE_PROB = 0.5

# Colors
COLOR_BG = (15, 15, 20)
COLOR_GRID = (30, 30, 35)
COLOR_PIPE_BG = (35, 35, 35)
COLOR_FLUID = (0, 191, 255)    
COLOR_SOURCE_A = (0, 255, 0)   # Green (Left)
COLOR_SOURCE_B = (255, 0, 0)   # Red (Right)
COLOR_TEXT = (255, 255, 255)
COLOR_UI_BG = (0, 0, 0, 180)

class BitwisePipe:
    def __init__(self, length, lanes):
        self.length = length
        self.lanes = lanes
        self.states = [0] * lanes 
        self.mask = (1 << length) - 1 
        
        # Thermodynamics
        self.mu_left = 2.0
        self.mu_right = 8.0
        
        # Energy Vectors (Horizontal)
        # We add a tiny bias to simulate "Net Flow" if potential is equal? 
        # No, let it be purely pressure driven.
        self.dE_long = 0.0 
        self.dE_trans_plus = -GRAVITY_POTENTIAL # If we had gravity
        self.dE_trans_minus = GRAVITY_POTENTIAL

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

    def step_monte_carlo(self):
        directions = [0, 1, 2, 3]
        random.shuffle(directions)
        
        for d in directions:
            if d == 0: # --- MOVE RIGHT (Left pushes Right) ---
                dE_base = 0.0
                
                # Phantom Neighbor at Left (Bit L)
                # Exists if Mu_Left is high enough to inject
                phantom_left = (1 << (self.length - 1)) if self.mu_left > 0 else 0
                
                for i in range(self.lanes):
                    state = self.states[i]
                    candidates = (state >> 1) & (~state)
                    
                    # Neighbor Check (Upstream/Left)
                    # Shift >> 1 brings Left neighbor to current pos
                    neighbors = (state >> 1) | phantom_left
                    has_neighbor_behind = neighbors & state
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor_behind & mask_pushed) | \
                                 (~has_neighbor_behind & mask_lonely)
                    
                    valid = candidates & acceptance & self.mask
                    state = state ^ valid ^ (valid << 1)
                    self.states[i] = state

            elif d == 1: # --- MOVE LEFT (Right pushes Left) ---
                dE_base = 0.0
                
                # Phantom Neighbor at Right (Bit -1)
                # Exists if Mu_Right is high
                # We align it to Bit 0.
                phantom_right = 1 if self.mu_right > 0 else 0
                
                for i in range(self.lanes):
                    state = self.states[i]
                    candidates = (state << 1) & (~state)
                    
                    # Neighbor Check (Upstream/Right)
                    # Shift << 1 brings Right neighbor (i-1) to current pos (i)
                    neighbors = (state << 1) | phantom_right
                    has_neighbor_behind = neighbors & state
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    
                    acceptance = (has_neighbor_behind & mask_pushed) | \
                                 (~has_neighbor_behind & mask_lonely)
                    
                    valid = candidates & acceptance & self.mask
                    state = state ^ valid ^ (valid >> 1)
                    self.states[i] = state

            elif d == 2: # Down (Transverse Mixing)
                # Just for mixing, no gravity
                dE_base = 0.0
                for i in range(self.lanes - 2, -1, -1):
                    src = self.states[i]
                    tgt = self.states[i+1]
                    # Simple repulsion
                    has_neighbor = (self.states[i-1] & src) if i > 0 else 0
                    
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    acceptance = (has_neighbor & mask_pushed) | (~has_neighbor & mask_lonely)
                    
                    moves = src & (~tgt) & acceptance
                    self.states[i] ^= moves
                    self.states[i+1] |= moves

            elif d == 3: # Up (Transverse Mixing)
                dE_base = 0.0
                for i in range(self.lanes - 1):
                    src = self.states[i+1]
                    tgt = self.states[i]
                    
                    has_neighbor = (self.states[i+2] & src) if i < self.lanes - 2 else 0
                    mask_pushed = self.get_boltzmann_mask(dE_base - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_base, self.length)
                    acceptance = (has_neighbor & mask_pushed) | (~has_neighbor & mask_lonely)
                    
                    moves = src & (~tgt) & acceptance
                    self.states[i+1] ^= moves
                    self.states[i] |= moves

        # --- DUAL INJECTION ---
        # Left Source (at Length-1)
        if self.mu_left > 0:
            entry_bit = 1 << (self.length - 1)
            prob = (1.0 if self.mu_left > 10 else math.exp(self.mu_left/KT)) * MAX_MOVE_PROB
            # Wait, Mu is potential. dE = -Mu. 
            # P = exp(-(-Mu)/kT) = exp(Mu/kT). If Mu is positive, P > 1. Cap at 1.
            # My previous code used dE logic.
            # Let's standardize: dE_insert = -Mu.
            dE = -self.mu_left
            prob = 1.0 if dE < 0 else math.exp(-dE/KT)
            prob *= MAX_MOVE_PROB
            
            for i in range(self.lanes):
                if not (self.states[i] & entry_bit):
                    if random.random() < prob:
                        self.states[i] |= entry_bit

        # Right Source (at 0)
        if self.mu_right > 0:
            entry_bit = 1
            dE = -self.mu_right
            prob = 1.0 if dE < 0 else math.exp(-dE/KT)
            prob *= MAX_MOVE_PROB
            
            for i in range(self.lanes):
                if not (self.states[i] & entry_bit):
                    if random.random() < prob:
                        self.states[i] |= entry_bit

def draw_pipe(screen, pipe, start_x, start_y, cell_size):
    len_px = pipe.length * cell_size
    wid_px = pipe.lanes * cell_size
    
    pygame.draw.rect(screen, COLOR_PIPE_BG, (start_x, start_y, len_px, wid_px))

    for lane_idx in range(pipe.lanes):
        state = pipe.states[lane_idx]
        if state == 0: continue
        
        # Color gradient doesn't really matter here as it's mixed fluid
        color = COLOR_FLUID

        for bit_idx in range(pipe.length):
            if (state >> bit_idx) & 1:
                # Bit 0 is Right. Bit Length-1 is Left.
                # x = 0 is Left on screen.
                # So dist from left = Length - 1 - bit_idx
                dist = pipe.length - 1 - bit_idx
                
                draw_x = start_x + (dist * cell_size)
                draw_y = start_y + (lane_idx * cell_size)
                
                pygame.draw.rect(screen, color, (draw_x, draw_y, cell_size, cell_size))

def main():
    pygame.init()
    screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Pressure Tug-of-War")
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
        
        # Draw Source Indicators
        pygame.draw.rect(screen, COLOR_SOURCE_A, (pipe_x - 20, pipe_y, 15, NUM_LANES*CELL_SIZE))
        pygame.draw.rect(screen, COLOR_SOURCE_B, (pipe_x + PIPE_LENGTH*CELL_SIZE + 5, pipe_y, 15, NUM_LANES*CELL_SIZE))
        
        draw_pipe(screen, pipe, pipe_x, pipe_y, CELL_SIZE)

        # UI
        screen.blit(bold_font.render("PRESSURE TUG-OF-WAR", True, COLOR_TEXT), (20, 20))
        
        # Left Stats
        l_text = f"LEFT SOURCE (A)\nPotential: {pipe.mu_left:.1f}\n[Q] Increase\n[A] Decrease"
        y = 80
        for line in l_text.split('\n'):
            screen.blit(font.render(line, True, COLOR_SOURCE_A), (20, y))
            y += 20
            
        # Right Stats
        r_text = f"RIGHT SOURCE (B)\nPotential: {pipe.mu_right:.1f}\n[W] Increase\n[S] Decrease"
        y = 80
        for line in r_text.split('\n'):
            screen.blit(font.render(line, True, COLOR_SOURCE_B), (DEFAULT_WIDTH - 200, y))
            y += 20

        # Info
        screen.blit(font.render("Fluid moves from High Potential to Low.", True, (150, 150, 150)), (DEFAULT_WIDTH//2 - 150, 500))
        screen.blit(font.render("High Potential = High Density = High Repulsion.", True, (150, 150, 150)), (DEFAULT_WIDTH//2 - 180, 520))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
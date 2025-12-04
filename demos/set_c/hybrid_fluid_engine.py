import pygame
import random
import sys
import math
import time

# --- CONFIGURATION ---
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800
PHYSICS_STEPS_PER_FRAME = 60 

# Simulation Constants
PIPE_LENGTH = 200    
NUM_LANES = 16            
CELL_SIZE = 5             

# --- SOLVER CONFIGURATION (LAYER 1) ---
SOURCE_PRESSURE = 100.0  # P_in
SINK_PRESSURE = 0.0      # P_out
RESISTANCE_BASE = 1.0    # Resistance of an open pipe
RESISTANCE_VALVE = 1000000.0 # Resistance of a closed valve

# --- MC CONFIGURATION (LAYER 2) ---
KT = 0.3                 # Low Temp = Stable "Liquid"
INTERACTION_J = 0.1      # Low Repulsion = Incompressible-ish packing
MAX_MOVE_PROB = 0.5      # Symmetry breaking
COUPLING_STRENGTH = 0.2  # How strongly the Solver forces the MC particles (Gain)

# Colors
COLOR_BG = (20, 20, 25)
COLOR_PIPE_BG = (40, 40, 45)
COLOR_FLUID = (0, 191, 255)    
COLOR_SOURCE = (0, 255, 0)
COLOR_WALL = (255, 50, 50)
COLOR_TEXT = (255, 255, 255)
COLOR_UI_BG = (0, 0, 0, 200)

# ==========================================
# LAYER 1: THE ANALYTIC SOLVER
# ==========================================
class ResistorNode:
    def __init__(self, name, fixed_pressure=None):
        self.name = name
        self.pressure = fixed_pressure if fixed_pressure is not None else 0.0
        self.fixed = (fixed_pressure is not None)
        self.edges_in = []
        self.edges_out = []

class ResistorEdge:
    def __init__(self, name, node_from, node_to, resistance=1.0):
        self.name = name
        self.node_from = node_from
        self.node_to = node_to
        self.base_resistance = resistance
        self.current_resistance = resistance
        self.flow = 0.0 # Calculated Flow
        
        # Link graph
        node_from.edges_out.append(self)
        node_to.edges_in.append(self)

class CircuitSolver:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, name, pressure=None):
        n = ResistorNode(name, pressure)
        self.nodes.append(n)
        return n

    def add_edge(self, name, n1, n2):
        e = ResistorEdge(name, n1, n2)
        self.edges.append(e)
        return e

    def solve(self):
        """
        Iterative Relaxation (Gauss-Seidel style) to solve for Pressures.
        Kirchhoff's Current Law: Sum(Flow_In) = Sum(Flow_Out)
        (P_neighbor - P_node) / R = Flow
        """
        # 1. Update Resistances (Handle Valves)
        # (Done externally before call)

        # 2. Iterate Pressures
        iterations = 50 
        for _ in range(iterations):
            max_delta = 0
            for node in self.nodes:
                if node.fixed: continue
                
                # Calculate ideal pressure based on neighbors
                # P_node = Sum(P_neigh / R) / Sum(1/R)
                numerator = 0.0
                denominator = 0.0
                
                # Inputs
                for e in node.edges_in:
                    cond = 1.0 / max(1e-9, e.current_resistance)
                    numerator += e.node_from.pressure * cond
                    denominator += cond
                
                # Outputs (Treating downstream as neighbor)
                for e in node.edges_out:
                    cond = 1.0 / max(1e-9, e.current_resistance)
                    numerator += e.node_to.pressure * cond
                    denominator += cond
                
                if denominator > 0:
                    new_p = numerator / denominator
                    diff = abs(new_p - node.pressure)
                    if diff > max_delta: max_delta = diff
                    node.pressure = new_p
            
            if max_delta < 0.001: break

        # 3. Calculate Flows
        for e in self.edges:
            delta_P = e.node_from.pressure - e.node_to.pressure
            e.flow = delta_P / max(1e-9, e.current_resistance)

# ==========================================
# LAYER 2: THE BITWISE MONTE CARLO
# ==========================================
class BitwisePipe:
    def __init__(self, length, lanes, angle_deg=0):
        self.length = length
        self.lanes = lanes
        self.states = [0] * lanes 
        self.mask = (1 << length) - 1 
        
        # Link to Logic
        self.valve_open = True
        self.target_flow = 0.0 # From Solver
        
        # Physics Vectors
        rad = math.radians(angle_deg)
        self.g_trans = math.cos(rad) * 0.5 # Gravity still applies for falling/leveling
        
        # Longitudinal Drive is now controlled by the Solver!
        # We store the angle only to know if we are vertical (for drawing)
        self.angle = angle_deg

    def reset(self):
        self.states = [0] * self.lanes

    def get_boltzmann_mask(self, dE, length):
        if dE <= 0:
            base_p = MAX_MOVE_PROB
        else:
            base_p = math.exp(-dE / KT) * MAX_MOVE_PROB
            
        if base_p <= 0.01: return 0
        if base_p >= 0.99: return (1 << length) - 1
        
        r1 = random.getrandbits(length)
        return r1 if base_p > 0.5 else (r1 & random.getrandbits(length))

    def step_monte_carlo(self):
        # 1. CALCULATE BIAS FROM SOLVER
        # Solver Flow (Q) -> Energy Gradient (dE)
        # High Q = Steep Hill (Negative dE).
        # Q=0 = Flat (dE=0).
        
        # dE = -Flow * Coupling
        bias_long = -self.target_flow * COUPLING_STRENGTH
        
        dE_right = bias_long
        dE_left  = -bias_long # Uphill if flow is right

        # Transverse is fixed by gravity/geometry
        dE_down  = -abs(self.g_trans)
        dE_up    = abs(self.g_trans) # Uphill against gravity

        # Valve Logic
        valve_blocker = self.mask
        if not self.valve_open:
            # Physical blockage at midpoint
            mid = self.length // 2
            valve_blocker = ~(1 << mid) & self.mask

        # 2. PERFORM MOVES
        directions = [0, 1, 2, 3]
        random.shuffle(directions)

        for d in directions:
            if d == 0: # Right (Flow Direction)
                for i in range(self.lanes):
                    state = self.states[i]
                    candidates = (state >> 1) & (~state)
                    
                    # Neighbor Interaction (J) helps smoothing
                    has_neighbor = (state << 1) & state
                    
                    # Apply Solver Bias
                    mask_pushed = self.get_boltzmann_mask(dE_right - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_right, self.length)
                    
                    acceptance = (has_neighbor & mask_pushed) | (~has_neighbor & mask_lonely)
                    
                    valid = candidates & acceptance & valve_blocker & self.mask
                    self.states[i] = state ^ valid ^ (valid << 1)

            elif d == 1: # Left (Back Diffusion)
                for i in range(self.lanes):
                    state = self.states[i]
                    candidates = (state << 1) & (~state)
                    
                    has_neighbor = (state >> 1) & state
                    
                    mask_pushed = self.get_boltzmann_mask(dE_left - INTERACTION_J, self.length)
                    mask_lonely = self.get_boltzmann_mask(dE_left, self.length)
                    
                    acceptance = (has_neighbor & mask_pushed) | (~has_neighbor & mask_lonely)
                    
                    valid = candidates & acceptance & valve_blocker & self.mask
                    self.states[i] = state ^ valid ^ (valid >> 1)

            elif d == 2: # Down (Gravity)
                # Gravity pulls to bottom lane (channel flow)
                for i in range(self.lanes - 2, -1, -1):
                    src = self.states[i]
                    tgt = self.states[i+1]
                    candidates = src & (~tgt)
                    
                    mask = self.get_boltzmann_mask(dE_down, self.length)
                    moves = candidates & mask
                    self.states[i] ^= moves
                    self.states[i+1] |= moves

            elif d == 3: # Up (Leveling)
                # Allows fluid to climb out of pile
                for i in range(self.lanes - 1):
                    src = self.states[i+1]
                    tgt = self.states[i]
                    candidates = src & (~tgt)
                    
                    mask = self.get_boltzmann_mask(dE_up, self.length) # High dE cost
                    moves = candidates & mask
                    self.states[i+1] ^= moves
                    self.states[i] |= moves

# ==========================================
# APP INFRASTRUCTURE
# ==========================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Hybrid Engineering Engine")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 14)
    bold_font = pygame.font.SysFont("monospace", 20, bold=True)

    # --- SETUP SOLVER ---
    solver = CircuitSolver()
    # Topology: Source -> J1 -> J2 -> Sink
    n_source = solver.add_node("Source", pressure=SOURCE_PRESSURE)
    n_j1     = solver.add_node("J1") # Junction 1
    n_j2     = solver.add_node("J2") # Junction 2
    n_sink   = solver.add_node("Sink", pressure=SINK_PRESSURE)

    # Edges match our visuals
    e_main   = solver.add_edge("Main", n_source, n_j1)
    e_branch = solver.add_edge("Branch", n_j1, n_j2)
    e_bottom = solver.add_edge("Bottom", n_j2, n_sink)

    # --- SETUP MC VISUALS ---
    main_pipe   = BitwisePipe(200, NUM_LANES, angle_deg=0)
    branch_pipe = BitwisePipe(120, NUM_LANES, angle_deg=45)
    bottom_pipe = BitwisePipe(150, NUM_LANES, angle_deg=0)

    # World Layout
    w_main_x, w_main_y = 100, 300
    w_junc_x = w_main_x + (150 * 5) # Connect 3/4 way down
    w_junc_y = w_main_y + (16 * 5)
    
    rad_45 = math.radians(45)
    diag_len = 120 * 5
    w_bot_x = w_junc_x + (math.cos(rad_45) * diag_len)
    w_bot_y = w_junc_y + (math.sin(rad_45) * diag_len)

    # Camera
    cam_x, cam_y, cam_zoom = 0, 0, 1.0

    pumping = True
    running = True
    
    while running:
        # --- INPUT ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: pumping = not pumping
                if event.key == pygame.K_r: 
                    main_pipe.reset(); branch_pipe.reset(); bottom_pipe.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Valve Logic
                    # Valve 1: On Main Pipe
                    mx, my = pygame.mouse.get_pos()
                    # (Simplified hit test for demo speed)
                    if mx > 400 and mx < 450 and my > 200 and my < 400:
                        main_pipe.valve_open = not main_pipe.valve_open

        # --- STEP 1: SOLVE MATH ---
        # Update Resistances based on Valves
        # Base resistance is length-dependent? Let's say R=1.
        e_main.current_resistance = RESISTANCE_BASE if main_pipe.valve_open else RESISTANCE_VALVE
        e_branch.current_resistance = RESISTANCE_BASE 
        e_bottom.current_resistance = RESISTANCE_BASE 
        
        # Source Pressure Control
        n_source.pressure = SOURCE_PRESSURE if pumping else 0.0
        
        solver.solve() # Calculate Q for all edges

        # --- STEP 2: UPDATE VISUALS ---
        # Feed the calculated Q into the MC engines
        main_pipe.target_flow = e_main.flow
        branch_pipe.target_flow = e_branch.flow
        bottom_pipe.target_flow = e_bottom.flow

        # Run MC Ticks
        for _ in range(PHYSICS_STEPS_PER_FRAME):
            # Injection (Source boundary)
            # The solver says flow is X. If X > 0, we must provide particles.
            # We inject if Flow > 0.
            if e_main.flow > 0.1:
                # Injection rate proportional to flow demand?
                # Or just saturate inlet and let bias handle speed?
                # Saturation is safer for incompressible look.
                bit_in = 1 << (main_pipe.length - 1)
                for i in range(NUM_LANES):
                    if random.random() < 0.8: main_pipe.states[i] |= bit_in

            main_pipe.step_monte_carlo()
            branch_pipe.step_monte_carlo()
            bottom_pipe.step_monte_carlo()
            
            # Manual Topology Transfer (MC still handles continuity)
            # Main -> Branch
            # We tap main pipe at 3/4 length (bit 50 from right)
            exit_bit = 50
            entry_bit = branch_pipe.length - 1
            for i in range(NUM_LANES):
                if (main_pipe.states[i] >> exit_bit) & 1:
                    # Only transfer if Branch has space
                    if not ((branch_pipe.states[i] >> entry_bit) & 1):
                        main_pipe.states[i] &= ~(1 << exit_bit)
                        branch_pipe.states[i] |= (1 << entry_bit)
            
            # Branch -> Bottom
            for i in range(NUM_LANES):
                if branch_pipe.states[i] & 1: # End of branch
                    if not (bottom_pipe.states[i] & (1 << (bottom_pipe.length-1))):
                        branch_pipe.states[i] &= ~1
                        bottom_pipe.states[i] |= (1 << (bottom_pipe.length-1))
            
            # Sink (Drain)
            # If solver says flow > 0 at bottom, we drain.
            if e_bottom.flow > 0.1:
                for i in range(NUM_LANES):
                    bottom_pipe.states[i] &= ~1

        # --- RENDER ---
        screen.fill(COLOR_BG)
        
        # Helper to draw pipes
        def draw_p(pipe, wx, wy):
            rad = math.radians(pipe.angle)
            len_px = pipe.length * CELL_SIZE
            ex = wx + math.cos(rad)*len_px
            ey = wy + math.sin(rad)*len_px
            # Draw Line background
            pygame.draw.line(screen, COLOR_PIPE_BG, (wx, wy), (ex, ey), NUM_LANES*CELL_SIZE)
            
            # Draw Particles
            for lane in range(pipe.lanes):
                state = pipe.states[lane]
                if state == 0: continue
                
                # Screen offsets for lane
                lx = -math.sin(rad) * lane * CELL_SIZE
                ly = math.cos(rad) * lane * CELL_SIZE
                
                for b in range(pipe.length):
                    if (state >> b) & 1:
                        # Dist from end (Bit 0 is end/right)
                        dist = pipe.length - 1 - b
                        dx = math.cos(rad) * dist * CELL_SIZE
                        dy = math.sin(rad) * dist * CELL_SIZE
                        
                        px = int(wx + dx + lx)
                        py = int(wy + dy + ly)
                        pygame.draw.rect(screen, COLOR_FLUID, (px, py, 4, 4))

        # Render Pipeline
        draw_p(main_pipe, w_main_x, w_main_y)
        draw_p(branch_pipe, w_junc_x, w_junc_y)
        draw_p(bottom_pipe, w_bot_x, w_bot_y)

        # Draw Valve
        vx = w_main_x + (100 * 5)
        vy = w_main_y
        col = COLOR_SOURCE if main_pipe.valve_open else COLOR_WALL
        pygame.draw.rect(screen, col, (vx-5, vy-40, 10, 100))

        # --- UI OVERLAY (Engineering Data) ---
        ui_surf = pygame.Surface((300, 200))
        ui_surf.fill(COLOR_UI_BG)
        screen.blit(ui_surf, (10, 10))
        
        def txt(s, y, c=COLOR_TEXT):
            screen.blit(font.render(s, True, c), (20, y))

        txt("HYBRID SOLVER ENGINE", 20, COLOR_SOURCE)
        txt(f"Source P: {n_source.pressure:.1f}", 50)
        txt(f"Sink P:   {n_sink.pressure:.1f}", 70)
        
        txt(f"Node J1 P: {n_j1.pressure:.2f}", 100)
        txt(f"Node J2 P: {n_j2.pressure:.2f}", 120)
        
        txt(f"Flow Main:   {e_main.flow:.2f}", 150, COLOR_FLUID)
        txt(f"Flow Branch: {e_branch.flow:.2f}", 170, COLOR_FLUID)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
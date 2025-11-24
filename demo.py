import pygame
import config
import math
from simulation import Simulation
from renderer import Renderer
from camera import Camera 

# --- CONFIGURATION ---
GRAPH_RECT = pygame.Rect(50, 50, 1180, 300)
SIM_Y_OFFSET = 500 # Where the pipe is drawn
START_X = 100
END_X = 1180
VALVE_X = (START_X + END_X) // 2

def setup_demo_scene():
    """
    Constructs a specific test bench: Source -> Pipe -> Valve -> Pipe -> Sink
    Using the new Junction/Pipe architecture.
    """
    sim = Simulation()
    
    # Clear default setup
    sim.junctions = []
    sim.pipes = []
    
    # 1. Create Junctions
    source = sim.create_node(START_X, SIM_Y_OFFSET, kind='source', material_type='Red')
    sim.source_node = source # Track for main loop
    
    valve = sim.create_node(VALVE_X, SIM_Y_OFFSET, kind='valve')
    valve.setting = 0.0 # Start Closed
    
    sink = sim.create_node(END_X, SIM_Y_OFFSET, kind='sink')
    
    # 2. Connect with Pipes (Edges)
    # Keep track of them in order for the graph
    pipe1 = sim.create_pipe(source, valve)
    pipe2 = sim.create_pipe(valve, sink)
    
    ordered_pipes = [pipe1, pipe2]
    
    return sim, valve, ordered_pipes

def draw_graph(surface, sim, ordered_pipes):
    """
    Draws the engineering plots by sampling Pipe internals.
    """
    # Background
    pygame.draw.rect(surface, (20, 25, 30), GRAPH_RECT)
    pygame.draw.rect(surface, (100, 100, 100), GRAPH_RECT, 2)
    
    data_points = []
    
    # Iterate through the known path to build the X-axis profile
    current_x = START_X
    
    for pipe in ordered_pipes:
        # Ensure direction matches graph (Left to Right)
        # If pipe is defined Right-to-Left, we'd need to flip logic, 
        # but setup_demo_scene creates them Left-to-Right.
        
        # Metrics for this pipe section
        # Pressure: Interpolate linearly from Start Node to End Node
        p_start = pipe.start_node.pressure
        p_end = pipe.end_node.pressure
        
        # Velocity: Constant for the whole pipe edge
        # Q = vA => v = Q/A
        vel = pipe.flow_rate / config.PIPE_AREA_M2
        
        # Sample the cells (The fluid packets)
        num_cells = len(pipe.cells)
        step_x = pipe.length_px / num_cells
        
        for i, cell in enumerate(pipe.cells):
            # X Position on Graph
            # pipe.cells[0] is usually the entrance (depending on flow direction logic)
            # In simulation.py, flow direction determines insert/pop end.
            # Visual representation maps index 0 to start_node.
            sample_x = current_x + (i * step_x)
            
            # Normalize X to graph width
            norm_x = (sample_x - START_X) / (END_X - START_X)
            screen_x = GRAPH_RECT.left + norm_x * GRAPH_RECT.width
            
            # 1. Pressure Interpolation
            # Linear gradient along the pipe
            alpha = i / num_cells
            local_p = p_start + (p_end - p_start) * alpha
            p_norm = min(1.0, local_p / 600.0)
            
            # 2. Fill Ratio (Volume)
            # Estimate volume from mass (assuming water density for simplicity of graph)
            # Real calc would use weighted density
            vol_m3 = cell.volume() # Uses 1000 kg/m3 default
            capacity_m3 = pipe.cell_volume
            fill = vol_m3 / capacity_m3
            vol_norm = min(1.0, fill)
            
            # 3. Velocity
            vel_norm = min(1.0, abs(vel) / 5.0)
            
            data_points.append({
                'x': screen_x,
                'p': p_norm,
                'vol': vol_norm,
                'vel': vel_norm
            })
            
        current_x += pipe.length_px

    # Helper to map normalized Y (0-1) to screen Y
    def get_y(norm_val):
        return GRAPH_RECT.bottom - (norm_val * GRAPH_RECT.height)

    if not data_points: return

    # DRAW GRAPHS
    
    # 1. Volume (Filled Area - Blue)
    if len(data_points) > 1:
        poly_points = [(p['x'], get_y(p['vol'])) for p in data_points]
        poly_points.append((data_points[-1]['x'], GRAPH_RECT.bottom))
        poly_points.append((data_points[0]['x'], GRAPH_RECT.bottom))
        
        s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (0, 100, 255, 50), poly_points) 
        surface.blit(s, (0,0))
        pygame.draw.lines(surface, (0, 200, 255), False, [(p['x'], get_y(p['vol'])) for p in data_points], 2)

    # 2. Velocity (Green Line)
    if len(data_points) > 1:
        pygame.draw.lines(surface, (50, 255, 50), False, [(p['x'], get_y(p['vel'])) for p in data_points], 2)

    # 3. Pressure (Red Line)
    if len(data_points) > 1:
        pygame.draw.lines(surface, (255, 50, 50), False, [(p['x'], get_y(p['p'])) for p in data_points], 2)

    # DRAW LEGEND & LABELS
    font = pygame.font.SysFont("Consolas", 12)
    
    legend_items = [
        ("PRESSURE (Red)", (255, 50, 50), "0 - 600 kPa"),
        ("VELOCITY (Green)", (50, 255, 50), "0 - 5 m/s"),
        ("FILL (Blue)", (0, 200, 255), "0 - 100%")
    ]
    
    lx, ly = GRAPH_RECT.left + 10, GRAPH_RECT.top + 10
    for text, color, range_txt in legend_items:
        surface.blit(font.render(f"{text}: {range_txt}", True, color), (lx, ly))
        ly += 20

    # Draw Valve Marker
    valve_scr_x = GRAPH_RECT.left + ((VALVE_X - START_X) / (END_X - START_X)) * GRAPH_RECT.width
    pygame.draw.line(surface, (150, 150, 150), (valve_scr_x, GRAPH_RECT.top), (valve_scr_x, GRAPH_RECT.bottom), 1)
    surface.blit(font.render("VALVE", True, (150, 150, 150)), (valve_scr_x + 5, GRAPH_RECT.bottom - 20))

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Pipe Dream - Graph Dashboard")
    clock = pygame.time.Clock()

    # Setup
    sim, valve_node, ordered_pipes = setup_demo_scene()
    
    camera = Camera() 
    renderer = Renderer(screen, camera)

    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    sim.toggle_valve(valve_node)
                elif event.key == pygame.K_1:
                    sim.cycle_source_material(sim.source_node)

        sim.update(dt)

        screen.fill(config.C_BACKGROUND)
        
        # Draw Simulation World
        renderer.draw_grid()
        renderer.draw_simulation(sim)
        
        # Draw Graph Overlay
        draw_graph(screen, sim, ordered_pipes)
        
        font = pygame.font.SysFont("Consolas", 16)
        msg = font.render("SPACE: Toggle Valve | 1: Cycle Fluid", True, config.C_TEXT)
        screen.blit(msg, (50, config.SCREEN_HEIGHT - 40))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
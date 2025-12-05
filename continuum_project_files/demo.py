import pygame
import config
import math
from simulation import Simulation
from renderer import Renderer
from camera import Camera # Added missing import

# --- CONFIGURATION ---
GRAPH_RECT = pygame.Rect(50, 50, 1180, 300)
SIM_Y_OFFSET = 500 # Where the pipe is drawn
START_X = 100
END_X = 1180
VALVE_X = (START_X + END_X) // 2

def setup_demo_scene():
    """
    Constructs a specific test bench: Source -> Pipe -> Valve -> Pipe -> Sink
    """
    sim = Simulation()
    
    # 1. Move default source to start position
    sim.source_node.x = START_X
    sim.source_node.y = SIM_Y_OFFSET
    sim.source_node.material_type = 'Red'
    
    # 2. Create Valve and Sink Nodes
    valve_node = sim.create_node(VALVE_X, SIM_Y_OFFSET, kind='valve')
    valve_node.setting = 0.0 # Start Closed
    
    sink_node = sim.create_node(END_X, SIM_Y_OFFSET, kind='sink')
    
    # 3. Connect them with pipes
    # Note: add_pipe creates intermediate nodes automatically
    sim.add_pipe(sim.source_node, valve_node.x, valve_node.y, connect_to_end_node=valve_node)
    sim.add_pipe(valve_node, sink_node.x, sink_node.y, connect_to_end_node=sink_node)
    
    return sim, valve_node

def draw_graph(surface, sim):
    """
    Draws the engineering plots: Pressure, Volume, Velocity.
    """
    # Background
    pygame.draw.rect(surface, (20, 25, 30), GRAPH_RECT)
    pygame.draw.rect(surface, (100, 100, 100), GRAPH_RECT, 2)
    
    # Collect Data sorted by X position
    # We filter for nodes approximately on the pipe line to ignore any noise
    nodes = [n for n in sim.nodes if abs(n.y - SIM_Y_OFFSET) < 5]
    nodes.sort(key=lambda n: n.x)
    
    if not nodes: return

    data_points = []
    for n in nodes:
        # Normalized X coordinate (0.0 to 1.0 within graph width)
        norm_x = (n.x - START_X) / (END_X - START_X)
        screen_x = GRAPH_RECT.left + norm_x * GRAPH_RECT.width
        
        # Extract Metrics
        # Pressure (Crowding): Scale 0-100% -> 0-100% height
        p = n.pressure
        p_norm = min(1.0, p / 100.0) 
        
        # Volume: Fill Ratio 0.0-1.0
        vol = n.current_volume / n.volume_capacity
        vol_norm = min(1.0, vol)
        
        # Velocity: Scale 0-10 m/s -> 0-100% height
        # Note: We use absolute velocity for graph
        vel = n.last_velocity
        vel_norm = min(1.0, abs(vel) / 5.0) # 5 m/s max visual
        
        data_points.append({
            'x': screen_x,
            'p': p_norm,
            'vol': vol_norm,
            'vel': vel_norm,
            'kind': n.kind
        })

    # Helper to map normalized Y (0-1) to screen Y
    def get_y(norm_val):
        return GRAPH_RECT.bottom - (norm_val * GRAPH_RECT.height)

    # DRAW GRAPHS
    
    # 1. Volume (Filled Area - Blue)
    if len(data_points) > 1:
        poly_points = [(p['x'], get_y(p['vol'])) for p in data_points]
        # Close polygon to bottom axis
        poly_points.append((data_points[-1]['x'], GRAPH_RECT.bottom))
        poly_points.append((data_points[0]['x'], GRAPH_RECT.bottom))
        
        s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(s, (0, 100, 255, 50), poly_points) # Transparent Blue
        surface.blit(s, (0,0))
        
        pygame.draw.lines(surface, (0, 200, 255), False, [(p['x'], get_y(p['vol'])) for p in data_points], 2)

    # 2. Velocity (Green Line)
    if len(data_points) > 1:
        pygame.draw.lines(surface, (50, 255, 50), False, [(p['x'], get_y(p['vel'])) for p in data_points], 2)

    # 3. Pressure/Crowding (Red Line) - Draw last so it's on top
    if len(data_points) > 1:
        pygame.draw.lines(surface, (255, 50, 50), False, [(p['x'], get_y(p['p'])) for p in data_points], 2)

    # DRAW LEGEND & LABELS
    font = pygame.font.SysFont("Consolas", 12)
    
    legend_items = [
        ("CROWDING (Red)", (255, 50, 50), "0 - 100%"),
        ("VELOCITY (Green)", (50, 255, 50), "0 - 5 m/s"),
        ("FILL (Blue)", (0, 200, 255), "0 - 100%")
    ]
    
    lx, ly = GRAPH_RECT.left + 10, GRAPH_RECT.top + 10
    for text, color, range_txt in legend_items:
        surface.blit(font.render(f"{text}: {range_txt}", True, color), (lx, ly))
        ly += 20

    # Draw markers for Valve location
    valve_scr_x = GRAPH_RECT.left + ((VALVE_X - START_X) / (END_X - START_X)) * GRAPH_RECT.width
    pygame.draw.line(surface, (150, 150, 150), (valve_scr_x, GRAPH_RECT.top), (valve_scr_x, GRAPH_RECT.bottom), 1)
    surface.blit(font.render("VALVE", True, (150, 150, 150)), (valve_scr_x + 5, GRAPH_RECT.bottom - 20))

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Pipe Dream - Physics Dashboard")
    clock = pygame.time.Clock()

    # Setup
    sim, valve_node = setup_demo_scene()
    
    # We need a camera for the Renderer (even though we manipulate simulation directly)
    camera = Camera() # Default camera 0,0
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

        # Update Physics
        sim.update(dt)

        # Render
        screen.fill(config.C_BACKGROUND)
        
        # Draw the physical pipe representation below
        renderer.draw_grid()
        renderer.draw_simulation(sim)
        
        # Draw the Data Dashboard above
        draw_graph(screen, sim)
        
        # Controls Text
        font = pygame.font.SysFont("Consolas", 16)
        msg = font.render("SPACE: Toggle Valve | 1: Cycle Fluid | Sinking Crowding: 0 %", True, config.C_TEXT)
        screen.blit(msg, (50, config.SCREEN_HEIGHT - 40))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
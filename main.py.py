import pygame
import numpy as np
import math

# --- CONFIGURATION ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 40  # Pixels per grid cell
GRID_WIDTH = 50
GRID_HEIGHT = 50

# --- COLORS (WPA Palette) ---
C_BACKGROUND = (30, 35, 40)     # Dark Slate
C_GRID = (50, 55, 60)           # Faint Lines
C_FLOOR = (45, 50, 55)          # Factory Floor
C_HIGHLIGHT = (255, 180, 60)    # Amber/Bakelite
C_FLUID = (0, 200, 220)         # Blueprint Cyan
C_TEXT = (220, 230, 240)        # Off-white

class Camera:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.zoom = 1.0
        self.drag_start = None

    def world_to_screen(self, wx, wy):
        sx = (wx * TILE_SIZE * self.zoom) + self.offset_x
        sy = (wy * TILE_SIZE * self.zoom) + self.offset_y
        return sx, sy

    def screen_to_world(self, sx, sy):
        # Returns float grid coordinates (e.g., 5.5, 3.2)
        wx = (sx - self.offset_x) / (TILE_SIZE * self.zoom)
        wy = (sy - self.offset_y) / (TILE_SIZE * self.zoom)
        return wx, wy

class Simulation:
    """
    The 'Model'. This holds the math.
    Eventually, this will hold your P&ID Graph and Fluid Logic.
    """
    def __init__(self):
        # 0 = Empty, 1 = Pipe, 2 = Tank
        self.grid_structure = np.zeros((GRID_WIDTH, GRID_HEIGHT), dtype=int)
        
        # Pressure Grid (Float)
        self.grid_pressure = np.zeros((GRID_WIDTH, GRID_HEIGHT), dtype=float)
        
        # Let's place a fake tank in the middle
        self.grid_structure[25, 25] = 2
        self.grid_pressure[25, 25] = 100.0 # High pressure source

    def update(self, dt):
        """
        The Physics Step.
        Run simple diffusion for now to test visual feedback.
        """
        # Simple visualization hack: Decay pressure everywhere except the source
        source_pressure = self.grid_pressure[25, 25]
        self.grid_pressure *= 0.95 # Decay
        self.grid_pressure[25, 25] = source_pressure # Keep source constant

    def toggle_wall(self, x, y):
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            current = self.grid_structure[x, y]
            self.grid_structure[x, y] = 1 if current == 0 else 0

class Renderer:
    """
    The 'View'. Handles drawing shapes, lines, and WPA aesthetics.
    """
    def __init__(self, surface, cam):
        self.surface = surface
        self.cam = cam
        self.font = pygame.font.SysFont("Consolas", 14)

    def draw_grid(self):
        # Calculate visible range to avoid drawing off-screen tiles
        start_col = int(-self.cam.offset_x / (TILE_SIZE * self.cam.zoom))
        end_col = start_col + int(SCREEN_WIDTH / (TILE_SIZE * self.cam.zoom)) + 1
        start_row = int(-self.cam.offset_y / (TILE_SIZE * self.cam.zoom))
        end_row = start_row + int(SCREEN_HEIGHT / (TILE_SIZE * self.cam.zoom)) + 1

        # Clamp to grid bounds
        start_col = max(0, start_col)
        end_col = min(GRID_WIDTH, end_col)
        start_row = max(0, start_row)
        end_row = min(GRID_HEIGHT, end_row)

        scaled_size = TILE_SIZE * self.cam.zoom

        for x in range(start_col, end_col):
            for y in range(start_row, end_row):
                screen_x, screen_y = self.cam.world_to_screen(x, y)
                
                # Draw Cell Border
                rect = (screen_x, screen_y, scaled_size, scaled_size)
                pygame.draw.rect(self.surface, C_GRID, rect, 1)
                
                # Draw Coordinate Text (Debug)
                if self.cam.zoom > 0.8:
                    # Only draw text if zoomed in enough
                    lbl = f"{x},{y}"
                    # Using a small circle instead of text for perf if needed
                    # pygame.draw.circle(self.surface, C_GRID, (screen_x + 2, screen_y + 2), 1)

    def draw_simulation(self, sim):
        scaled_size = TILE_SIZE * self.cam.zoom
        
        # Iterate over active cells (Optimization: In real game, keep a list of active entities)
        rows, cols = np.where(sim.grid_structure > 0)
        for r, c in zip(rows, cols):
            screen_x, screen_y = self.cam.world_to_screen(r, c)
            rect = (screen_x, screen_y, scaled_size + 1, scaled_size + 1)
            
            if sim.grid_structure[r, c] == 2: # Tank
                pygame.draw.rect(self.surface, C_HIGHLIGHT, rect)
            else: # Wall/Pipe
                pygame.draw.rect(self.surface, (100, 100, 110), rect)

    def draw_ui(self, mouse_world_pos):
        # Draw mouse coordinates
        txt = self.font.render(f"GRID: {int(mouse_world_pos[0])}, {int(mouse_world_pos[1])}", True, C_HIGHLIGHT)
        self.surface.blit(txt, (10, 10))
        
        instr = self.font.render("L-CLICK: Place Wall | M-CLICK: Pan | SCROLL: Zoom", True, C_TEXT)
        self.surface.blit(instr, (10, SCREEN_HEIGHT - 30))

# --- MAIN HARNESS ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("The Synthetic Era - Proto 0.1")
    clock = pygame.time.Clock()

    camera = Camera()
    sim = Simulation()
    renderer = Renderer(screen, camera)
    
    # Center camera
    camera.offset_x = (SCREEN_WIDTH / 2) - (GRID_WIDTH * TILE_SIZE / 2)
    camera.offset_y = (SCREEN_HEIGHT / 2) - (GRID_HEIGHT * TILE_SIZE / 2)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0 # Delta time in seconds
        
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.VIDEORESIZE:
                renderer.surface = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    mx, my = pygame.mouse.get_pos()
                    wx, wy = camera.screen_to_world(mx, my)
                    sim.toggle_wall(int(wx), int(wy))
                elif event.button == 2: # Middle Click
                    camera.drag_start = pygame.mouse.get_pos()
                elif event.button == 4: # Scroll Up
                    camera.zoom = min(camera.zoom * 1.1, 5.0)
                elif event.button == 5: # Scroll Down
                    camera.zoom = max(camera.zoom * 0.9, 0.2)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    camera.drag_start = None

            elif event.type == pygame.MOUSEMOTION:
                if camera.drag_start:
                    mx, my = pygame.mouse.get_pos()
                    dx = mx - camera.drag_start[0]
                    dy = my - camera.drag_start[1]
                    camera.offset_x += dx
                    camera.offset_y += dy
                    camera.drag_start = (mx, my)

        # 2. Simulation Update
        sim.update(dt)

        # 3. Rendering
        screen.fill(C_BACKGROUND)
        
        renderer.draw_grid()
        renderer.draw_simulation(sim)
        
        mx, my = pygame.mouse.get_pos()
        renderer.draw_ui(camera.screen_to_world(mx, my))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
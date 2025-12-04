import pygame
import math
import random

# --- Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
FPS = 60

# Colors
COLOR_BG = (30, 30, 30)
COLOR_PIPE = (100, 100, 100)
COLOR_FLUID_A = (0, 200, 255)  # Cyan for "Gas/Diffusive"
COLOR_FLUID_B = (0, 100, 255)  # Deep Blue for "Liquid/Slug"

# Physics Constants
FLOW_VELOCITY = 4.0      # Pixels per frame
SPREAD_RATE = 1.0        # How fast the Gaussian packet widens
INITIAL_PACKET_SIZE = 40 # Width of the Gaussian packet at spawn
PARTICLE_RADIUS = 15     # Radius of liquid blobs

# --- Setup Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Fluid Vis: Diffusive Packet vs. Cohesive Slug")
clock = pygame.time.Clock()

def create_gaussian_surface(radius):
    """
    Pre-renders a Gaussian glow texture to use as a wave packet.
    This is much faster than calculating per-pixel math every frame.
    """
    size = radius * 2
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Draw a gradient circle to simulate Gaussian falloff
    # We layer circles with decreasing alpha
    steps = 20
    for i in range(steps):
        r = int(radius * (1 - i/steps))
        alpha = int(255 * (math.exp(-i/5))) # Decay
        # Ensure alpha doesn't vanish too fast for visibility
        alpha = max(alpha, 5)
        pygame.draw.circle(surface, (*COLOR_FLUID_A, 50), (radius, radius), r)
    
    return surface

# Pre-generate the Gaussian texture
base_gaussian = create_gaussian_surface(50) 

class DiffusivePacket:
    """
    Represents your idea: A discrete packet that spreads out over time.
    Models Advection-Diffusion.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = INITIAL_PACKET_SIZE
        self.age = 0
        
    def update(self):
        # Advection: Move forward
        self.x += FLOW_VELOCITY
        # Diffusion: Spread out
        self.width += SPREAD_RATE
        self.age += 1

    def draw(self, surface):
        # Calculate alpha based on spread (conservation of mass illusion)
        # As it gets wider, it gets dimmer
        intensity = max(50, 255 - self.width * 1.5)
        
        # Scale the pre-rendered Gaussian to current width
        current_height = 80 # Constrained by pipe height
        scaled_surf = pygame.transform.smoothscale(base_gaussian, (int(self.width), int(current_height)))
        
        # Set transparency
        scaled_surf.set_alpha(intensity)
        
        # Draw centered
        rect = scaled_surf.get_rect(center=(self.x, self.y))
        surface.blit(scaled_surf, rect)

class CohesiveParticle:
    """
    Represents the recommendation: A hard particle that stays tight.
    Models Plug Flow (Advection only).
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Slight random jitter to make it look organic, not robotic
        self.vx = FLOW_VELOCITY + random.uniform(-0.1, 0.1) 
        
    def update(self):
        self.x += self.vx

    def draw(self, surface):
        # Draw a simple solid circle
        # When many overlap, they form a "bar" or "slug"
        pygame.draw.circle(surface, COLOR_FLUID_B, (int(self.x), int(self.y)), PARTICLE_RADIUS)

# --- Main Loop ---
running = True
packets_a = [] # Top pipe (Diffusive)
particles_b = [] # Bottom pipe (Cohesive)

# Timer for particle emission frequency
emission_timer = 0 

while running:
    # 1. Input Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    is_injecting = keys[pygame.K_SPACE]

    # 2. Physics & Logic
    
    # Emission logic
    if is_injecting:
        # Pipe A: Emit distinct "packets" less frequently (Wave approach)
        if emission_timer % 15 == 0:
            packets_a.append(DiffusivePacket(50, 100))
        
        # Pipe B: Emit "particles" frequently (Stream approach)
        if emission_timer % 2 == 0:
            particles_b.append(CohesiveParticle(50, 300))
            
        emission_timer += 1
    else:
        emission_timer = 0 # Reset phase so bursts are consistent

    # Update Entities
    for p in packets_a:
        p.update()
    for p in particles_b:
        p.update()

    # Cleanup off-screen entities
    packets_a = [p for p in packets_a if p.x < SCREEN_WIDTH + 200]
    particles_b = [p for p in particles_b if p.x < SCREEN_WIDTH + 50]

    # 3. Rendering
    screen.fill(COLOR_BG)

    # Draw Pipe Outlines
    pipe_rect_a = pygame.Rect(50, 60, SCREEN_WIDTH - 100, 80)
    pipe_rect_b = pygame.Rect(50, 260, SCREEN_WIDTH - 100, 80)
    
    pygame.draw.rect(screen, COLOR_PIPE, pipe_rect_a, 2)
    pygame.draw.rect(screen, COLOR_PIPE, pipe_rect_b, 2)

    # Render Method A (Additive Blending for "Glow")
    # We create a temporary surface to handle the additive blending cleanly
    surf_a = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for p in packets_a:
        p.draw(surf_a)
    screen.blit(surf_a, (0, 0))

    # Render Method B (Painter's Algorithm for "Solidity")
    # Since they are solid circles, overlapping them naturally creates the "Union" shape
    for p in particles_b:
        p.draw(screen)

    # UI Labels
    font = pygame.font.SysFont("Arial", 18)
    label_a = font.render("Method A: Spreading Wave Packets (Gas-like)", True, (200, 200, 200))
    label_b = font.render("Method B: Cohesive Particle Stream (Liquid-like)", True, (200, 200, 200))
    label_hint = font.render("[HOLD SPACEBAR TO INJECT FLUID]", True, (255, 255, 0))
    
    screen.blit(label_a, (50, 30))
    screen.blit(label_b, (50, 230))
    screen.blit(label_hint, (SCREEN_WIDTH//2 - 150, 360))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
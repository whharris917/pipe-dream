import pygame
import sys
import subprocess
import config

class MenuButton:
    def __init__(self, x, y, w, h, text, action_code):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action_code = action_code
        self.color = (60, 60, 60)
        self.hover_color = (80, 80, 90)
    
    def draw(self, screen, font):
        mouse_pos = pygame.mouse.get_pos()
        col = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, col, self.rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 1, border_radius=8)
        
        txt_surf = font.render(self.text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class Launcher:
    def __init__(self):
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Flow State - Dashboard")
        
        self.font = pygame.font.SysFont("segoeui", 24)
        self.title_font = pygame.font.SysFont("segoeui", 48, bold=True)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Layout
        cx = self.width // 2
        cy = self.height // 2
        
        self.buttons = [
            MenuButton(cx - 150, cy - 60, 300, 50, "New Simulation", "NEW_SIM"),
            MenuButton(cx - 150, cy + 10, 300, 50, "New Model Builder", "NEW_MODEL"),
            MenuButton(cx - 150, cy + 80, 300, 50, "Open File...", "OPEN"),
            MenuButton(cx - 150, cy + 150, 300, 50, "Exit", "EXIT"),
        ]

    def run(self):
        while self.running:
            self.screen.fill((30, 30, 35))
            
            title = self.title_font.render("Flow State", True, (0, 122, 204))
            sub = self.font.render("Engineering Sandbox", True, (150, 150, 150))
            self.screen.blit(title, (self.width//2 - title.get_width()//2, 100))
            self.screen.blit(sub, (self.width//2 - sub.get_width()//2, 160))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                for btn in self.buttons:
                    if btn.is_clicked(event):
                        self.handle_action(btn.action_code)

            for btn in self.buttons:
                btn.draw(self.screen, self.font)
                
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

    def handle_action(self, code):
        if code == "EXIT":
            self.running = False
        elif code == "NEW_SIM":
            self.launch_app("sim")
        elif code == "NEW_MODEL":
            self.launch_app("editor")
        elif code == "OPEN":
            self.launch_app("sim") 

    def launch_app(self, mode):
        try:
            # Spawn the new independent instance
            subprocess.Popen([sys.executable, "run_instance.py", mode])
            # We keep the launcher open to allow launching multiple instances
        except Exception as e:
            print(f"Failed to launch: {e}")

if __name__ == "__main__":
    Launcher().run()
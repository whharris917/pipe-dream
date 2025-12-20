import pygame
import math
from folly_assets import AssetManager
from folly_ui import JuicyButton, C_BG

# Setup
pygame.init()
WIDTH, HEIGHT = 1100, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flow State // Sound Lab")
font = pygame.font.SysFont("consolas", 14)
header_font = pygame.font.SysFont("segoeui", 20, bold=True)
clock = pygame.time.Clock()

assets = AssetManager.get()

# --- TAB SYSTEM ---
current_tab = "SFX" # "SFX" or "MUSIC"

# Tab Buttons
btn_tab_sfx = JuicyButton(20, 20, 160, 40, text="Soundboard", icon_name="tab_sfx")
btn_tab_music = JuicyButton(190, 20, 160, 40, text="Jukebox", icon_name="tab_music")
btn_tab_sfx.active = True

# --- SFX VIEW COMPONENTS ---
sfx_buttons = []
sfx_categories = {
    "Beeps": [],
    "Bloops": [],
    "Clicks": [],
    "Other": []
}

for name in sorted(assets.sounds.keys()):
    if "beep" in name: sfx_categories["Beeps"].append(name)
    elif "bloop" in name: sfx_categories["Bloops"].append(name)
    elif "click" in name: sfx_categories["Clicks"].append(name)
    else: sfx_categories["Other"].append(name)

grid_x, grid_y = 50, 100
col_width = 150
row_height = 40
cat_gap = 20
curr_y = grid_y

for cat, sound_names in sfx_categories.items():
    if not sound_names: continue
    # Category Header
    header_btn = JuicyButton(grid_x, curr_y, 200, 30, text=f"--- {cat} ---")
    header_btn.target_color = (60, 60, 70)
    sfx_buttons.append(header_btn)
    curr_y += 40
    
    # Grid
    cols = 6
    for i, name in enumerate(sound_names):
        r = i // cols
        c = i % cols
        bx = grid_x + c * (col_width + 10)
        by = curr_y + r * (row_height + 10)
        
        # Clean label
        label = name.replace("bloop_", "").replace("beep_", "").replace("click_", "")
        btn = JuicyButton(bx, by, col_width, row_height, text=label, sound_name=name)
        sfx_buttons.append(btn)
        
    rows = (len(sound_names) // cols) + 1
    curr_y += rows * (row_height + 10) + cat_gap

# --- MUSIC VIEW COMPONENTS ---
music_buttons = []
jukebox_x = 100
jukebox_y = 100

track_names = list(assets.tracks.keys())
for i, t_name in enumerate(track_names):
    y_pos = jukebox_y + (i * 70)
    
    # Track Label
    lbl = JuicyButton(jukebox_x, y_pos, 300, 50, text=t_name)
    lbl.target_color = (40, 40, 50) # Darker
    music_buttons.append(lbl)
    
    # Play
    btn_play = JuicyButton(jukebox_x + 320, y_pos, 50, 50, icon_name="play")
    btn_play.track_to_play = t_name 
    music_buttons.append(btn_play)
    
    # Stop
    btn_stop = JuicyButton(jukebox_x + 380, y_pos, 50, 50, icon_name="stop")
    btn_stop.is_stop_btn = True
    music_buttons.append(btn_stop)

    btn_real = JuicyButton(jukebox_x, jukebox_y + 300, 300, 50, text="Load 'jungle_track.mp3'")
    btn_real.is_external_track = "jungle_track.mp3" # Custom property
    music_buttons.append(btn_real)

# --- MAIN LOOP ---
running = True
while running:
    dt = clock.tick(60) / 1000.0
    
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 1. Handle Tabs
        btn_tab_sfx.handle_event(event)
        btn_tab_music.handle_event(event)
        
        if btn_tab_sfx.clicked:
            current_tab = "SFX"
            btn_tab_sfx.active = True
            btn_tab_music.active = False
        elif btn_tab_music.clicked:
            current_tab = "MUSIC"
            btn_tab_sfx.active = False
            btn_tab_music.active = True
            
        # 2. Handle Views
        active_list = sfx_buttons if current_tab == "SFX" else music_buttons
        for btn in active_list:
            btn.handle_event(event)
            if btn.clicked:
                # Music Logic
                if hasattr(btn, 'track_to_play'):
                    assets.play_music(btn.track_to_play)
                elif hasattr(btn, 'is_stop_btn'):
                    assets.stop_music()
                elif hasattr(btn, 'is_external_track'):
                    # Call our new method!
                    assets.play_external_music(btn.is_external_track)

    # Updates
    btn_tab_sfx.update()
    btn_tab_music.update()
    
    active_list = sfx_buttons if current_tab == "SFX" else music_buttons
    for btn in active_list:
        btn.update()
        
    # Drawing
    screen.fill(C_BG)
    
    # Draw Tab Bar Background
    pygame.draw.rect(screen, (40, 40, 40), (0, 0, WIDTH, 80))
    pygame.draw.line(screen, (80, 80, 80), (0, 80), (WIDTH, 80))
    
    # Draw Tabs
    btn_tab_sfx.draw(screen, font)
    btn_tab_music.draw(screen, font)
    
    # Draw Content
    for btn in active_list:
        btn.draw(screen, font)
        
    pygame.display.flip()

pygame.quit()
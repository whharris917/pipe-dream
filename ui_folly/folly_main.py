import pygame
import math
import random
from folly_assets import AssetManager
from folly_ui import JuicyButton, Dropdown, Checkbox, Slider, Knob, TextInput, ProgressBar, C_BG, C_ACCENT, AnimVar

# --- SETUP ---
pygame.init()
WIDTH, HEIGHT = 1200, 850
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flow State // Studio")

# Fonts
try:
    font_path = pygame.font.match_font("segoeui") 
    font = pygame.font.Font(font_path, 15) if font_path else pygame.font.SysFont("arial", 15)
    title_path = pygame.font.match_font("segoeuibold")
    title_font = pygame.font.Font(title_path, 24) if title_path else pygame.font.SysFont("arial", 24, bold=True)
except:
    font = pygame.font.SysFont("arial", 14)
    title_font = pygame.font.SysFont("arial", 24, bold=True)

clock = pygame.time.Clock()
assets = AssetManager.get()

# --- BACKGROUND ---
class Background:
    def draw(self, surf):
        surf.fill(C_BG)
        grid_sz = 60
        grid_col = (30, 30, 35)
        for x in range(0, WIDTH + grid_sz, grid_sz):
            pygame.draw.line(surf, grid_col, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT + grid_sz, grid_sz):
            pygame.draw.line(surf, grid_col, (0, y), (WIDTH, y))

bg_sys = Background()

# --- UI BUILDER ---
sidebar_w = 200
btn_tab_sfx = JuicyButton(10, 80, 180, 45, text="Soundboard", icon_name="tab_sfx")
btn_tab_music = JuicyButton(10, 135, 180, 45, text="Jukebox", icon_name="tab_music")
btn_tab_kit = JuicyButton(10, 190, 180, 45, text="UI Kit", icon_name="settings") 
btn_tab_sfx.active = True

content_rect = pygame.Rect(210, 80, WIDTH - 220, HEIGHT - 100)
anim_tab_offset = AnimVar(0.0, speed=10.0) 

# -- SFX CONTENT --
sfx_buttons = []
sfx_categories = { "Beeps": [], "Bloops": [], "Clicks": [], "Other": [] }
for name in sorted(assets.sounds.keys()):
    if "bg_" in name: continue 
    if "beep" in name: sfx_categories["Beeps"].append(name)
    elif "bloop" in name: sfx_categories["Bloops"].append(name)
    elif "click" in name: sfx_categories["Clicks"].append(name)
    else: sfx_categories["Other"].append(name)

curr_y = content_rect.y + 10
for cat, names in sfx_categories.items():
    if not names: continue
    sfx_buttons.append(JuicyButton(content_rect.x, curr_y, content_rect.width, 30, text=f"// {cat.upper()}"))
    sfx_buttons[-1].disabled = True 
    curr_y += 40
    cols = 5
    gap = 10
    bw = (content_rect.width - (cols-1)*gap) // cols
    bh = 45
    for i, name in enumerate(names):
        r = i // cols
        c = i % cols
        bx = content_rect.x + c * (bw + gap)
        by = curr_y + r * (bh + gap)
        label = name.replace("bloop_", "").replace("beep_", "").replace("click_", "")
        btn = JuicyButton(bx, by, bw, bh, text=label, sound_name=name)
        sfx_buttons.append(btn)
    rows = (len(names) // cols) + 1
    curr_y += rows * (bh + gap) + 20

# -- MUSIC CONTENT --
music_buttons = []
track_names = sorted(list(assets.tracks.keys()))
curr_y = content_rect.y + 10
music_buttons.append(JuicyButton(content_rect.x, curr_y, content_rect.width, 30, text="// AVAILABLE TRACKS"))
music_buttons[-1].disabled = True
curr_y += 40
for t_name in track_names:
    lbl = JuicyButton(content_rect.x, curr_y, content_rect.width - 120, 50, text=t_name)
    lbl.disabled = True 
    music_buttons.append(lbl)
    btn_play = JuicyButton(content_rect.right - 110, curr_y, 50, 50, icon_name="play")
    btn_play.track_to_play = t_name 
    music_buttons.append(btn_play)
    btn_stop = JuicyButton(content_rect.right - 50, curr_y, 50, 50, icon_name="stop")
    btn_stop.is_stop_btn = True
    music_buttons.append(btn_stop)
    curr_y += 60

# -- UI KIT CONTENT (SHOWCASE) --
kit_widgets = []
cx, cy = content_rect.x + 20, content_rect.y + 20

# 1. Colors & Buttons
kit_widgets.append(JuicyButton(cx, cy, 200, 30, text="// ACTION BUTTONS"))
kit_widgets[-1].disabled = True
cy += 40
kit_widgets.append(JuicyButton(cx, cy, 140, 45, text="Default"))
kit_widgets.append(JuicyButton(cx+150, cy, 140, 45, text="Primary", style="primary"))
kit_widgets.append(JuicyButton(cx+300, cy, 140, 45, text="Danger", style="danger"))
kit_widgets.append(JuicyButton(cx+450, cy, 140, 45, text="Success", style="success"))
cy += 60

# 2. Toggles & Checkboxes
kit_widgets.append(JuicyButton(cx, cy, 200, 30, text="// BOOLEAN INPUTS"))
kit_widgets[-1].disabled = True
cy += 40
kit_widgets.append(JuicyButton(cx, cy, 140, 40, text="Toggle Me", style="toggle"))
kit_widgets.append(Checkbox(cx+160, cy+5, 30, "Show Grid", True))
kit_widgets.append(Checkbox(cx+300, cy+5, 30, "Enable Physics", False))
kit_widgets.append(Checkbox(cx+460, cy+5, 30, "Debug Mode", False))
cy += 60

# 3. Sliders & Progress
kit_widgets.append(JuicyButton(cx, cy, 200, 30, text="// ANALOG INPUTS"))
kit_widgets[-1].disabled = True
cy += 40
kit_widgets.append(Slider(cx, cy+10, 200, val=0.3))
kit_widgets.append(Slider(cx+220, cy+10, 200, val=0.7))
kit_widgets.append(Knob(cx+480, cy+20, 25, val=0.2))
kit_widgets.append(Knob(cx+550, cy+20, 25, val=0.8))
cy += 60

# 4. Text & Dropdowns
kit_widgets.append(JuicyButton(cx, cy, 200, 30, text="// TEXT & SELECTION"))
kit_widgets[-1].disabled = True
cy += 40
kit_widgets.append(TextInput(cx, cy, 250, 40, "Enter project name..."))
kit_widgets.append(Dropdown(cx+270, cy, 200, 40, ["Low Quality", "Medium Quality", "High Quality"]))
cy += 60

# 5. Progress
kit_widgets.append(JuicyButton(cx, cy, 200, 30, text="// SYSTEM STATUS"))
kit_widgets[-1].disabled = True
cy += 40
kit_widgets.append(ProgressBar(cx, cy, 400, 20, val=0.4))


# --- MAIN LOOP ---
running = True
current_tab = "SFX"
target_tab = "SFX"

while running:
    dt = clock.tick(60) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        
        btn_tab_sfx.handle_event(event, assets)
        btn_tab_music.handle_event(event, assets)
        btn_tab_kit.handle_event(event, assets)
        
        if btn_tab_sfx.clicked: target_tab = "SFX"
        elif btn_tab_music.clicked: target_tab = "MUSIC"
        elif btn_tab_kit.clicked: target_tab = "KIT"

        if target_tab != current_tab:
            anim_tab_offset.value = 50.0 
            current_tab = target_tab
            btn_tab_sfx.active = (current_tab == "SFX")
            btn_tab_music.active = (current_tab == "MUSIC")
            btn_tab_kit.active = (current_tab == "KIT")

        active_list = []
        if current_tab == "SFX": active_list = sfx_buttons
        elif current_tab == "MUSIC": active_list = music_buttons
        elif current_tab == "KIT": active_list = kit_widgets
        
        for w in active_list:
            if hasattr(w, 'handle_event'):
                try: w.handle_event(event, assets)
                except: pass # some widgets dont need assets
                
                # Logic Hooks
                if hasattr(w, 'clicked') and w.clicked:
                    if hasattr(w, 'track_to_play') and w.track_to_play: assets.play_music(w.track_to_play)
                    elif hasattr(w, 'is_stop_btn') and w.is_stop_btn: assets.stop_music()
                    elif hasattr(w, 'is_external_track') and w.is_external_track: assets.play_external_music(w.is_external_track)

    # Updates
    anim_tab_offset.update(dt)
    btn_tab_sfx.update(dt)
    btn_tab_music.update(dt)
    btn_tab_kit.update(dt)
    
    active_list = []
    if current_tab == "SFX": active_list = sfx_buttons
    elif current_tab == "MUSIC": active_list = music_buttons
    elif current_tab == "KIT": active_list = kit_widgets

    for w in active_list:
        if hasattr(w, 'update'): w.update(dt)

    # Draw
    bg_sys.draw(screen)
    
    # Sidebar
    s = pygame.Surface((200, HEIGHT), pygame.SRCALPHA)
    s.fill((25, 25, 28, 230)) 
    screen.blit(s, (0,0))
    pygame.draw.line(screen, (50,50,55), (200, 0), (200, HEIGHT))
    
    title_surf = title_font.render("FLOW STATE", True, C_ACCENT)
    screen.blit(title_surf, (20, 30))
    sub_surf = font.render("AUDIO STUDIO", True, (150, 150, 150))
    screen.blit(sub_surf, (20, 55))
    
    btn_tab_sfx.draw(screen, font, assets)
    btn_tab_music.draw(screen, font, assets)
    btn_tab_kit.draw(screen, font, assets)
    
    offset = anim_tab_offset.value
    
    # Standard Draw
    for w in active_list:
        if not isinstance(w, Dropdown) or not w.is_open:
            orig_x = w.rect.x
            w.rect.x += offset
            if isinstance(w, JuicyButton): w.draw(screen, font, assets)
            else: w.draw(screen, font)
            w.rect.x = orig_x
            
    # Overlay Draw (Dropdowns)
    for w in active_list:
        if isinstance(w, Dropdown):
            orig_x = w.rect.x
            w.rect.x += offset
            if w.is_open: w.draw_overlay(screen, font) # Draw overlay
            else: w.draw(screen, font) # Draw closed state if not handled above
            w.rect.x = orig_x
    
    pygame.display.flip()

pygame.quit()
import pygame
import os
import math
import array
import random

# Import local track generators if available
try:
    import track_whimsical
    import track_jungle
except ImportError:
    pass

ASSET_DIR = "folly_assets"
IMG_DIR = os.path.join(ASSET_DIR, "images")
SND_DIR = os.path.join(ASSET_DIR, "sounds")

class AssetManager:
    _instance = None
    
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.tracks = {} 
        self.snd_dir = SND_DIR
        
        self._ensure_dirs()
        self._generate_default_icons()
        self._synthesize_sounds()
        self._generate_sound_library()
        self._load_tracks() 

    @staticmethod
    def get():
        if AssetManager._instance is None:
            AssetManager._instance = AssetManager()
        return AssetManager._instance

    def _ensure_dirs(self):
        os.makedirs(IMG_DIR, exist_ok=True)
        os.makedirs(self.snd_dir, exist_ok=True)

    def _generate_default_icons(self):
        # Basic shapes for UI buttons
        tools = [
            ("play", (100, 255, 100), "play"),
            ("stop", (255, 100, 100), "stop"),
            ("tab_sfx", (80, 200, 255), "grid"),
            ("tab_music", (255, 200, 80), "note"),
            ("settings", (180, 180, 180), "gear"),
            ("gear", (150, 150, 150), "gear")
        ]
        for name, color, shape in tools:
            s = pygame.Surface((32, 32), pygame.SRCALPHA)
            if shape == "play": pygame.draw.polygon(s, color, [(10, 8), (24, 16), (10, 24)])
            elif shape == "stop": pygame.draw.rect(s, color, (10, 10, 12, 12))
            elif shape == "grid": 
                pygame.draw.rect(s, color, (8, 8, 7, 7)); pygame.draw.rect(s, color, (17, 8, 7, 7))
                pygame.draw.rect(s, color, (8, 17, 7, 7)); pygame.draw.rect(s, color, (17, 17, 7, 7))
            elif shape == "note":
                pygame.draw.circle(s, color, (12, 24), 5)
                pygame.draw.line(s, color, (16, 24), (16, 8), 3); pygame.draw.line(s, color, (16, 8), (26, 8), 3); pygame.draw.line(s, color, (26, 8), (26, 16), 3)
            elif shape == "gear":
                pygame.draw.circle(s, color, (16, 16), 10, 4)
            self.images[name] = s

    def _synthesize_sounds(self):
        # Note: Actual mix pre-init happens in main.py to be safe
        pass

    def _make_beep(self, freq, duration, amp=3000):
        rate = 44100
        n = int(rate * duration)
        buf = array.array('h', [0]*n)
        for i in range(n):
            t = i/rate
            val = math.sin(2*math.pi*freq*t) * ((1.0 - t/duration)**2)
            buf[i] = int(val * amp)
        return pygame.mixer.Sound(buffer=buf)

    def _make_bloop(self, start_freq, end_freq, duration, amp=2500):
        rate = 44100
        n = int(rate * duration)
        buf = array.array('h', [0]*n)
        k = (end_freq - start_freq) / duration
        for i in range(n):
            t = i/rate
            phase = 2 * math.pi * (start_freq * t + 0.5 * k * t * t)
            val = math.sin(phase)
            env = math.sin(math.pi * (t / duration)) 
            buf[i] = int(val * amp * env)
        return pygame.mixer.Sound(buffer=buf)

    def _generate_sound_library(self):
        print("Synthesizing Sound Library...")
        
        self.sounds['hover'] = self._make_beep(450, 0.05, 1500)
        self.sounds['click'] = self._make_beep(1200, 0.05, 2000)
        self.sounds['snap'] = self._make_bloop(220, 280, 0.1, 2000)

        # 1. Beeps
        for freq in [100, 220, 440, 660, 880, 1200, 1500, 2000]:
            self.sounds[f"beep_{freq}Hz"] = self._make_beep(freq, 0.15)
            
        # 2. Clicks (Materials)
        self.sounds['click_wood_low'] = self._make_beep(250, 0.05, 4000)
        self.sounds['click_wood_hi'] = self._make_beep(550, 0.04, 4000)
        self.sounds['click_plastic'] = self._make_beep(1600, 0.02, 3500)
        self.sounds['click_metal'] = self._make_beep(2800, 0.02, 3500)
        self.sounds['click_deep'] = self._make_beep(80, 0.1, 4000)

        # 3. Bloops (Sweeps)
        self.sounds['bloop_bub_1'] = self._make_bloop(400, 600, 0.1)
        self.sounds['bloop_bub_2'] = self._make_bloop(500, 700, 0.1)
        self.sounds['bloop_bub_3'] = self._make_bloop(600, 800, 0.1)
        self.sounds['bloop_rise_slow'] = self._make_bloop(200, 500, 0.3)
        self.sounds['bloop_rise_fast'] = self._make_bloop(300, 800, 0.15)
        self.sounds['bloop_fall_slow'] = self._make_bloop(500, 200, 0.3)
        self.sounds['bloop_fall_fast'] = self._make_bloop(800, 300, 0.15)
        self.sounds['bloop_error'] = self._make_bloop(150, 100, 0.4)

    def _load_tracks(self):
        try:
            self.tracks["Whimsical Flow"] = track_whimsical.generate(44100)
            self.tracks["Jungle Explorer"] = track_jungle.generate(44100)
        except: pass
        
        if os.path.exists(self.snd_dir):
            for f in os.listdir(self.snd_dir):
                if f.lower().endswith(('.mp3', '.ogg', '.wav')):
                    self.tracks[f] = os.path.join(self.snd_dir, f)

    def get_icon(self, name): return self.images.get(name)

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].set_volume(0.5)
            self.sounds[name].play()
            
    def play_music(self, track_name):
        pygame.mixer.Channel(0).stop()
        pygame.mixer.music.stop()
        if track_name in self.tracks:
            data = self.tracks[track_name]
            if isinstance(data, str):
                try:
                    pygame.mixer.music.load(data)
                    pygame.mixer.music.play(-1, fade_ms=500)
                except: pass
            else:
                pygame.mixer.Channel(0).play(data, loops=-1, fade_ms=500)

    def play_external_music(self, filename):
        path = os.path.join(self.snd_dir, filename)
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1, fade_ms=500)
            except: pass

    def stop_music(self):
        pygame.mixer.Channel(0).fadeout(500)
        pygame.mixer.music.fadeout(500)
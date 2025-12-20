import pygame
import os
import math
import array
import random

# Import the local track files
import track_whimsical
import track_jungle

# Settings
ASSET_DIR = "folly_assets"
IMG_DIR = os.path.join(ASSET_DIR, "images")

class AssetManager:
    _instance = None
    
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.tracks = {} 
        
        # --- FIX: Define the sounds directory explicitly ---
        self.snd_dir = os.path.join(ASSET_DIR, "sounds")
        
        self._ensure_dirs()
        self._generate_default_icons()
        self._synthesize_sounds()
        self._generate_sound_library()
        self._load_tracks() # Scans both generated AND external files

    @staticmethod
    def get():
        if AssetManager._instance is None:
            AssetManager._instance = AssetManager()
        return AssetManager._instance

    def _ensure_dirs(self):
        if not os.path.exists(IMG_DIR):
            os.makedirs(IMG_DIR)
        # Create the sounds folder so you have somewhere to drop your MP3s
        if not os.path.exists(self.snd_dir):
            os.makedirs(self.snd_dir)

    def _generate_default_icons(self):
        # (Standard icon generation)
        tools = [
            ("select", (200, 200, 255), "cursor"),
            ("brush", (100, 255, 100), "circle"),
            ("line", (255, 200, 100), "line"),
            ("rect", (255, 100, 100), "rect"),
            ("circle", (100, 200, 255), "hollow_circle"),
            ("eraser", (255, 150, 150), "x"),
            ("settings", (150, 150, 150), "gear"),
            ("play", (100, 255, 100), "play"),
            ("stop", (255, 100, 100), "stop"),
            ("tab_sfx", (80, 200, 255), "grid"),
            ("tab_music", (255, 200, 80), "note")
        ]
        for name, color, shape in tools:
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            if shape == "cursor":
                pygame.draw.polygon(surf, color, [(8, 4), (24, 16), (14, 16), (12, 26), (8, 24)])
            elif shape == "play":
                 pygame.draw.polygon(surf, color, [(10, 8), (24, 16), (10, 24)])
            elif shape == "stop":
                 pygame.draw.rect(surf, color, (10, 10, 12, 12))
            elif shape == "grid":
                 pygame.draw.rect(surf, color, (8, 8, 7, 7))
                 pygame.draw.rect(surf, color, (17, 8, 7, 7))
                 pygame.draw.rect(surf, color, (8, 17, 7, 7))
                 pygame.draw.rect(surf, color, (17, 17, 7, 7))
            elif shape == "note":
                 pygame.draw.circle(surf, color, (12, 24), 5)
                 pygame.draw.line(surf, color, (16, 24), (16, 8), 3)
                 pygame.draw.line(surf, color, (16, 8), (26, 8), 3)
                 pygame.draw.line(surf, color, (26, 8), (26, 16), 3)
            elif shape == "circle":
                pygame.draw.circle(surf, color, (16, 16), 12)
            elif shape == "hollow_circle":
                pygame.draw.circle(surf, color, (16, 16), 12, 3)
            elif shape == "line":
                pygame.draw.line(surf, color, (6, 26), (26, 6), 4)
            elif shape == "rect":
                pygame.draw.rect(surf, color, (6, 8, 20, 16), 3)
            elif shape == "x":
                pygame.draw.line(surf, color, (8, 8), (24, 24), 4)
                pygame.draw.line(surf, color, (24, 8), (8, 24), 4)
            elif shape == "gear":
                pygame.draw.circle(surf, color, (16, 16), 10, 4)
            self.images[name] = surf

    def _synthesize_sounds(self):
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(44100, -16, 1, 1024)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
        
        # --- GENERATORS ---
        def make_beep(freq, duration, amp=3000):
            rate = 44100
            n = int(rate * duration)
            buf = array.array('h', [0]*n)
            for i in range(n):
                t = i/rate
                val = math.sin(2*math.pi*freq*t) * ((1-t/duration)**2)
                buf[i] = int(val * amp)
            return pygame.mixer.Sound(buffer=buf)

        def make_bloop(start_freq, end_freq, duration, amp=2500):
            sample_rate = 44100
            total_duration = duration + 0.20
            total_samples = int(sample_rate * total_duration)
            buf = array.array('h', [0] * total_samples)
            
            def add_wave(offset_samples, f_start, f_end, vol):
                dur_samples = int(sample_rate * duration)
                k = (f_end - f_start) / duration
                for i in range(dur_samples):
                    idx = offset_samples + i
                    if idx >= total_samples: break
                    t = float(i) / sample_rate
                    phase = 2 * math.pi * (f_start * t + 0.5 * k * t * t)
                    val = math.sin(phase)
                    env = math.sin(math.pi * (t / duration)) 
                    buf[idx] = max(-32767, min(32767, buf[idx] + int(val * vol * env)))

            add_wave(0, start_freq, end_freq, amp)
            delay_samples = int(sample_rate * 0.08) 
            add_wave(delay_samples, start_freq * 0.8, end_freq * 0.8, amp * 0.4)
            return pygame.mixer.Sound(buffer=buf)

        self._make_beep = make_beep
        self._make_bloop = make_bloop

        self.sounds['hover'] = make_beep(450, 0.05, 2000)
        self.sounds['click'] = make_beep(1200, 0.1, 3000)
        self.sounds['snap'] = make_bloop(220, 280, 0.12, 2500)

    def _generate_sound_library(self):
        for freq in [100, 220, 440, 660, 880, 1200]:
            self.sounds[f"beep_{freq}Hz"] = self._make_beep(freq, 0.08)
            
        self.sounds['click_wood_low'] = self._make_beep(400, 0.03, 4000)
        self.sounds['click_wood_hi'] = self._make_beep(800, 0.02, 4000)
        self.sounds['click_plastic'] = self._make_beep(1500, 0.015, 3500)
        self.sounds['click_metal'] = self._make_beep(2500, 0.01, 3500)
        self.sounds['click_deep'] = self._make_beep(100, 0.05, 4000)

        self.sounds['bloop_bub_1'] = self._make_bloop(800, 900, 0.04)
        self.sounds['bloop_bub_2'] = self._make_bloop(900, 1000, 0.04)
        self.sounds['bloop_bub_3'] = self._make_bloop(1000, 1200, 0.04)
        self.sounds['bloop_rise_slow'] = self._make_bloop(200, 400, 0.15)
        self.sounds['bloop_rise_fast'] = self._make_bloop(300, 500, 0.08)
        self.sounds['bloop_rise_bass'] = self._make_bloop(100, 200, 0.20)
        self.sounds['bloop_fall_slow'] = self._make_bloop(400, 200, 0.15)
        self.sounds['bloop_fall_fast'] = self._make_bloop(500, 300, 0.08)
        self.sounds['bloop_fall_deep'] = self._make_bloop(200, 50, 0.15)
        self.sounds['bloop_snap_soft'] = self._make_bloop(220, 260, 0.06)
        self.sounds['bloop_snap_hard'] = self._make_bloop(220, 350, 0.06)
        self.sounds['bloop_snap_hi']   = self._make_bloop(600, 700, 0.05)
        self.sounds['bloop_error_1'] = self._make_bloop(400, 200, 0.15)

    def _load_tracks(self):
        print("Generating Tracks...")
        
        # 1. Internal Generated Tracks
        self.tracks["Whimsical Flow"] = track_whimsical.generate(44100)
        self.tracks["Jungle Explorer"] = track_jungle.generate(44100)
        
        # 2. External File Scanner
        # This looks into folly_assets/sounds/ and finds ANY supported file
        if os.path.exists(self.snd_dir):
            files = os.listdir(self.snd_dir)
            for f in files:
                if f.lower().endswith(('.mp3', '.ogg', '.wav')):
                    # We store the FULL PATH as the value, and the filename as the key
                    full_path = os.path.join(self.snd_dir, f)
                    self.tracks[f] = full_path
                    print(f"Loaded external track: {f}")
        
        print("Tracks Ready.")

    def get_icon(self, name):
        return self.images.get(name)

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].stop()
            self.sounds[name].play()
            
    def play_music(self, track_name):
        """Intelligently handles both generated Sounds and external Files."""
        # Stop everything first to prevent overlap
        pygame.mixer.Channel(0).stop()
        pygame.mixer.music.stop()
        
        if track_name in self.tracks:
            data = self.tracks[track_name]
            
            # Check: Is this a file path (String) or a generated Object (Sound)?
            if isinstance(data, str):
                try:
                    pygame.mixer.music.load(data)
                    pygame.mixer.music.play(loops=-1, fade_ms=500)
                    pygame.mixer.music.set_volume(0.5)
                    print(f"Streaming: {track_name}")
                except Exception as e:
                    print(f"Error loading file {track_name}: {e}")
            else:
                # It's a generated Sound object
                pygame.mixer.Channel(0).play(data, loops=-1, fade_ms=500)
                pygame.mixer.Channel(0).set_volume(0.5)
                print(f"Playing generated: {track_name}")

    def stop_music(self):
        pygame.mixer.Channel(0).fadeout(500)
        pygame.mixer.music.fadeout(500)
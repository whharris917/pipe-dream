import pygame
import random
from folly_synth import Synth, NOTES

def generate(sample_rate):
    bpm = 105 # Slower, groovy
    beat_len = 60.0 / bpm
    bar_len = beat_len * 4
    total_bars = 24
    duration = bar_len * total_bars
    
    synth = Synth(sample_rate, duration)
    
    # --- PATTERNS ---
    def pat_percussion(bar):
        base_t = bar * bar_len
        # "Four on the floor" Kick
        for i in range(4):
            synth.add_drum(base_t + i * beat_len, "kick")
            
        # Shaker (16th notes, steady)
        for i in range(16):
            synth.add_drum(base_t + i * (beat_len/4), "shaker")
            
        # Bongos (Syncopated)
        # Beats: 1.5, 2.5, 3.75
        synth.add_drum(base_t + 1.5 * beat_len, "bongo_hi")
        synth.add_drum(base_t + 2.5 * beat_len, "bongo_lo")
        synth.add_drum(base_t + 3.75 * beat_len, "bongo_lo")

    def pat_bass(bar):
        base_t = bar * bar_len
        # Root notes (F Major: F, Bb, C)
        prog = ['F2', 'F2', 'C2', 'C2']
        root = NOTES[prog[bar % 4]]
        
        # Reggae/Dub feel: heavy on beat 1, pause, then pickup
        synth.add_tone(base_t + 0.0, root, 0.6, 2800, "bass")
        synth.add_tone(base_t + 2.5 * beat_len, root, 0.3, 2500, "bass")
        synth.add_tone(base_t + 3.0 * beat_len, root * 1.5, 0.2, 2000, "bass") # Fifth

    def pat_marimba(bar):
        base_t = bar * bar_len
        # Pentatonic F: F, G, A, C, D
        scale = [NOTES['F3'], NOTES['G3'], NOTES['A3'], NOTES['C4'], NOTES['D4'], NOTES['F4']]
        
        # Playful random arpeggios
        random.seed(bar) # Consistent random per bar
        for i in range(8): # 8th notes
            if random.random() > 0.3: # 70% chance to play note
                note = random.choice(scale)
                t = base_t + i * (beat_len/2)
                synth.add_tone(t, note, 0.15, 1800, "marimba")
                
    def pat_flute(bar):
        base_t = bar * bar_len
        if bar % 4 == 0:
            # Long sustained note
            synth.add_tone(base_t, NOTES['A4'], 2.0, 1000, "flute")
        elif bar % 4 == 2:
            synth.add_tone(base_t, NOTES['G4'], 1.5, 1000, "flute")

    def pat_birds(bar):
        base_t = bar * bar_len
        if random.random() > 0.5:
            t = base_t + random.uniform(0, 3)
            # High pitch chirp (Simulated with high freq sine)
            synth.add_tone(t, 2000, 0.1, 500, "sine")
            synth.add_tone(t+0.1, 1500, 0.1, 300, "sine")

    # --- ARRANGEMENT ---
    # Intro: Jungle Ambience + Percussion
    for b in range(0, 4):
        pat_percussion(b)
        pat_birds(b)
        
    # A Section: Bass + Marimba enters
    for b in range(4, 12):
        pat_percussion(b)
        pat_bass(b)
        pat_marimba(b)
        pat_birds(b)
        
    # B Section: Full "Zoo" (Flute melody)
    for b in range(12, 20):
        pat_percussion(b)
        pat_bass(b)
        pat_marimba(b)
        pat_flute(b)
        
    # Outro
    for b in range(20, 24):
        pat_percussion(b)
        pat_marimba(b)

    return pygame.mixer.Sound(buffer=synth.get_buffer())
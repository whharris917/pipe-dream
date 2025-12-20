import pygame
from folly_synth import Synth, NOTES

def generate(sample_rate):
    bpm = 120
    beat_len = 60.0 / bpm
    bar_len = beat_len * 4
    total_bars = 32
    duration = bar_len * total_bars
    
    synth = Synth(sample_rate, duration)
    
    # --- PATTERNS ---
    def pat_bass(bar): 
        base_t = bar * bar_len
        prog = ['C2', 'G2', 'A2', 'F2']
        root = NOTES[prog[bar % 4]]
        synth.add_tone(base_t + 0.0, root, 0.4, 2500, "bass")
        synth.add_tone(base_t + 1.0, root, 0.2, 2000, "bass")
        synth.add_tone(base_t + 1.5, root, 0.4, 2500, "bass")

    def pat_keys(bar):
        base_t = bar * bar_len
        chords = [
            (NOTES['E3'], NOTES['G3'], NOTES['C4']), # C
            (NOTES['B3'], NOTES['D4'], NOTES['G4']), # G
            (NOTES['C4'], NOTES['E4'], NOTES['A4']), # Am
            (NOTES['A3'], NOTES['C4'], NOTES['F4'])  # F
        ]
        c = chords[bar % 4]
        for beat in [0.5, 1.5, 2.5, 3.5]:
            for freq in c:
                synth.add_tone(base_t + beat * beat_len, freq, 0.15, 600, "sine")

    def pat_drums(bar):
        base_t = bar * bar_len
        synth.add_drum(base_t + 0 * beat_len, "kick")
        synth.add_drum(base_t + 1 * beat_len, "snare")
        synth.add_drum(base_t + 2 * beat_len, "kick")
        synth.add_drum(base_t + 2.5 * beat_len, "kick")
        synth.add_drum(base_t + 3 * beat_len, "snare")

    def pat_melody(bar):
        base_t = bar * bar_len
        scale = [NOTES['C4'], NOTES['D4'], NOTES['E4'], NOTES['G4'], NOTES['A4'], NOTES['C5']]
        if bar % 2 == 0:
            synth.add_tone(base_t + 0.0, scale[0], 0.2, 1500, "pluck")
            synth.add_tone(base_t + 0.5, scale[1], 0.2, 1500, "pluck")
            synth.add_tone(base_t + 1.0, scale[2], 0.2, 1500, "pluck")
            synth.add_tone(base_t + 1.5, scale[4], 0.4, 1500, "pluck")
        else:
            synth.add_tone(base_t + 0.0, scale[5], 0.2, 1500, "pluck")
            synth.add_tone(base_t + 0.75, scale[3], 0.2, 1500, "pluck")
            synth.add_tone(base_t + 1.5, scale[2], 0.2, 1500, "pluck")
            synth.add_tone(base_t + 2.5, scale[0], 0.4, 1500, "pluck")

    # --- ARRANGEMENT ---
    # Intro
    for b in range(0, 4):
        pat_bass(b)
        pat_keys(b)
        
    # Main
    for b in range(4, 12):
        pat_bass(b)
        pat_keys(b)
        pat_drums(b)
        pat_melody(b)
        
    # Bridge
    for b in range(12, 20):
        base_t = b * bar_len
        synth.add_drum(base_t, "kick")
        synth.add_drum(base_t + 2 * beat_len, "kick")
        f = NOTES['C4'] if b%2==0 else NOTES['A3']
        synth.add_tone(base_t, f, 0.1, 1200, "pluck")
        synth.add_tone(base_t+0.25, f*1.5, 0.1, 1200, "pluck")
        
    # Outro
    for b in range(20, 32):
        pat_bass(b)
        pat_keys(b)
        pat_drums(b)
        pat_melody(b)
        # Hats
        t = b * bar_len
        for i in range(8):
            synth.add_drum(t + i * (beat_len/2), "snare") # soft snare as hat

    return pygame.mixer.Sound(buffer=synth.get_buffer())
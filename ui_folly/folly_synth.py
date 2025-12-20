import math
import array
import random

# Common Note Frequencies
NOTES = {
    'C2': 65.41, 'G2': 98.00, 'A2': 110.00, 'F2': 87.31,
    'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99
}

class Synth:
    def __init__(self, sample_rate, duration_sec):
        self.sample_rate = sample_rate
        self.total_samples = int(sample_rate * duration_sec)
        self.buf = array.array('h', [0] * self.total_samples)

    def add_tone(self, start_time, freq, duration, vol, inst_type="sine", pan=0.5):
        start_idx = int(start_time * self.sample_rate)
        dur_samples = int(duration * self.sample_rate)
        
        for i in range(dur_samples):
            idx = start_idx + i
            if idx >= self.total_samples: break
            
            t = float(i) / self.sample_rate
            
            # --- OSCILLATORS ---
            val = 0.0
            if inst_type == "sine":
                val = math.sin(2 * math.pi * freq * t)
            elif inst_type == "tri" or inst_type == "bass":
                val = 2 * abs(2 * ((freq * t) % 1) - 1) - 1
            elif inst_type == "saw":
                val = 2 * ((freq * t) % 1) - 1
            elif inst_type == "square":
                val = 1.0 if (freq * t) % 1 < 0.5 else -1.0
            elif inst_type == "pluck" or inst_type == "marimba":
                val = math.sin(2 * math.pi * freq * t)
                # Add a bit of 2nd harmonic for wood texture
                val += 0.3 * math.sin(2 * math.pi * (freq*2) * t)

            # --- ENVELOPES ---
            env = 1.0
            if inst_type == "pluck": 
                env = math.exp(-7.0 * t)
            elif inst_type == "marimba":
                env = math.exp(-12.0 * t) # Very short decay
            elif inst_type == "flute":
                # Slow attack, vibrato
                if t < 0.1: env = t/0.1
                elif t > duration - 0.1: env = (duration - t)/0.1
                # Vibrato
                val *= (1.0 + 0.1 * math.sin(2 * math.pi * 5.0 * t))
            elif inst_type == "bass":
                if t < 0.05: env = t/0.05
                else: env = max(0, 1.0 - (t-0.05)*3.0)
            else: 
                if t < 0.05: env = t/0.05
                elif t > duration - 0.05: env = (duration - t)/0.05
            
            # Mix
            current = self.buf[idx]
            self.buf[idx] = max(-32767, min(32767, current + int(val * vol * env)))

    def add_drum(self, start_time, type="kick"):
        start_idx = int(start_time * self.sample_rate)
        dur = 0.2 if type in ["kick", "bongo_lo"] else 0.1
        dur_samples = int(dur * self.sample_rate)
        
        vol = 3000
        
        for i in range(dur_samples):
            idx = start_idx + i
            if idx >= self.total_samples: break
            t = float(i) / self.sample_rate
            
            val = 0.0
            if type == "kick":
                f = 120 * math.exp(-15 * t)
                val = math.sin(2 * math.pi * f * t)
                if val > 0.6: val = 0.6 # Clip
            elif type == "snare":
                val = random.uniform(-1, 1) * math.exp(-10 * t)
            elif type == "shaker":
                val = random.uniform(-1, 1) * math.exp(-30 * t) # Very short
                vol = 1500
            elif type == "bongo_lo":
                f = 180 * math.exp(-5 * t) # Pitch bend
                val = math.sin(2 * math.pi * f * t)
            elif type == "bongo_hi":
                f = 350 * math.exp(-5 * t)
                val = math.sin(2 * math.pi * f * t)
                
            env = 1.0 - (t / dur)
            self.buf[idx] = max(-32767, min(32767, self.buf[idx] + int(val * vol * env)))

    def get_buffer(self):
        return self.buf
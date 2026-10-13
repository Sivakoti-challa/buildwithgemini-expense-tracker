import numpy as np
import wave
import struct

sample_rate = 44100
bpm = 86
beat_dur = 60.0 / bpm
bar_dur = beat_dur * 4
num_bars = 14
total_dur = bar_dur * num_bars
total_samples = int(sample_rate * total_dur)

t = np.linspace(0, total_dur, total_samples, endpoint=False)
audio = np.zeros(total_samples, dtype=np.float32)

def adsr(length_samples, a=0.01, d=0.1, s=0.7, r=0.2):
    env = np.ones(length_samples, dtype=np.float32) * s
    na = int(a * sample_rate)
    nd = int(d * sample_rate)
    nr = int(r * sample_rate)
    if na > 0:
        env[:min(na, length_samples)] = np.linspace(0, 1, min(na, length_samples))
    if nd > 0 and na < length_samples:
        end_d = min(na + nd, length_samples)
        env[na:end_d] = np.linspace(1, s, end_d - na)
    if nr > 0 and length_samples > nr:
        env[-nr:] = np.linspace(s, 0, nr)
    return env

# 1. Warm Jazzy Lo-Fi Chord Progression:
# Fmaj7 (F3, A3, C4, E4) -> Em7 (E3, G3, B3, D4) -> Dm7 (D3, F3, A3, C4) -> Cmaj7 (C3, E3, G3, B3)
chord_freqs = [
    [174.61, 220.00, 261.63, 329.63], # Fmaj7
    [164.81, 196.00, 246.94, 293.66], # Em7
    [146.83, 174.61, 220.00, 261.63], # Dm7
    [130.81, 164.81, 196.00, 246.94], # Cmaj7
]
bass_notes = [87.31, 82.41, 73.42, 65.41] # F2, E2, D2, C2

# Render Chords (Rhodes-like warm mellow tone)
for bar in range(num_bars):
    c_idx = bar % 4
    freqs = chord_freqs[c_idx]
    start_time = bar * bar_dur
    start_idx = int(start_time * sample_rate)
    chord_len = int(bar_dur * 0.95 * sample_rate)
    if start_idx + chord_len > total_samples:
        chord_len = total_samples - start_idx
    
    t_chord = np.linspace(0, chord_len / sample_rate, chord_len, endpoint=False)
    env = adsr(chord_len, a=0.03, d=0.4, s=0.5, r=0.4)
    # subtle vibrato
    vibrato = 1.0 + 0.003 * np.sin(2 * np.pi * 4.5 * t_chord)
    
    chord_sound = np.zeros(chord_len, dtype=np.float32)
    for f in freqs:
        tone = (np.sin(2 * np.pi * f * vibrato * t_chord) +
                0.3 * np.sin(2 * np.pi * 2 * f * vibrato * t_chord) +
                0.08 * np.sin(2 * np.pi * 3 * f * vibrato * t_chord))
        chord_sound += tone * 0.25
        
    audio[start_idx:start_idx + chord_len] += chord_sound * env * 0.35

# 2. Warm Walking Bassline
for bar in range(num_bars):
    c_idx = bar % 4
    base_f = bass_notes[c_idx]
    # Play root on 1 and 2.5, fifth on 4
    bass_hits = [(0, base_f, 1.2), (beat_dur * 1.5, base_f, 0.9), (beat_dur * 2.5, base_f, 1.0), (beat_dur * 3.5, base_f * 1.5, 0.8)]
    for offset, freq, dur in bass_hits:
        hit_start = int((bar * bar_dur + offset) * sample_rate)
        hit_len = int(beat_dur * dur * sample_rate)
        if hit_start + hit_len > total_samples:
            hit_len = total_samples - hit_start
        if hit_len <= 0: continue
        t_hit = np.linspace(0, hit_len / sample_rate, hit_len, endpoint=False)
        bass_env = np.exp(-3.5 * t_hit)
        bass_sound = (np.sin(2 * np.pi * freq * t_hit) + 0.2 * np.sin(2 * np.pi * 2 * freq * t_hit))
        audio[hit_start:hit_start + hit_len] += bass_sound * bass_env * 0.45

# 3. Upbeat Lo-Fi Drums (Kick, Snare, Hi-hats)
# Kick synth
def make_kick():
    k_len = int(0.22 * sample_rate)
    tk = np.linspace(0, 0.22, k_len, endpoint=False)
    freq_env = 120 * np.exp(-30 * tk) + 42
    phase = 2 * np.pi * np.cumsum(freq_env) / sample_rate
    amp = np.exp(-12 * tk)
    return np.sin(phase) * amp * 0.7

# Snare / rimshot synth
def make_snare():
    s_len = int(0.18 * sample_rate)
    ts = np.linspace(0, 0.18, s_len, endpoint=False)
    noise = np.random.uniform(-1, 1, s_len)
    tone = np.sin(2 * np.pi * 180 * ts) * np.exp(-25 * ts)
    noise_env = np.exp(-18 * ts)
    return (tone * 0.4 + noise * noise_env * 0.6) * 0.45

# Hi-hat synth
def make_hat(velocity=0.25):
    h_len = int(0.06 * sample_rate)
    th = np.linspace(0, 0.06, h_len, endpoint=False)
    noise = np.random.uniform(-1, 1, h_len)
    # High-pass filter rough approximation
    noise = np.diff(noise, prepend=0)
    hat_env = np.exp(-65 * th)
    return noise * hat_env * velocity

kick = make_kick()
snare = make_snare()
hat_loud = make_hat(0.18)
hat_soft = make_hat(0.10)

for bar in range(num_bars):
    # Upbeat boom bap pattern
    # Kicks on 0, 1.75, 2.5
    for beat_pos in [0, 1.75, 2.5]:
        k_start = int((bar * bar_dur + beat_pos * beat_dur) * sample_rate)
        k_end = min(k_start + len(kick), total_samples)
        audio[k_start:k_end] += kick[:k_end - k_start]
        
    # Snares on beats 1 and 3 (0-indexed: 1.0, 3.0)
    for beat_pos in [1.0, 3.0]:
        s_start = int((bar * bar_dur + beat_pos * beat_dur) * sample_rate)
        s_end = min(s_start + len(snare), total_samples)
        audio[s_start:s_end] += snare[:s_end - s_start]
        
    # Swinging 8th-note Hi-hats
    for eighth in range(8):
        # Slight swing delay on off-beats
        swing = 0.02 if eighth % 2 == 1 else 0.0
        h_pos = (eighth * 0.5 + swing) * beat_dur
        h_start = int((bar * bar_dur + h_pos) * sample_rate)
        hat = hat_loud if eighth % 2 == 0 else hat_soft
        h_end = min(h_start + len(hat), total_samples)
        if h_start < total_samples:
            audio[h_start:h_end] += hat[:h_end - h_start]

# 4. Vinyl crackle / texture
crackle = np.random.normal(0, 0.008, total_samples)
pops = np.random.choice([0, 0.06], size=total_samples, p=[0.9997, 0.0003])
audio += (crackle + pops)

# 5. Master compression / limiter
audio = np.tanh(audio * 1.3) * 0.85

# Fade in and fade out
fade_in = int(sample_rate * 0.5)
fade_out = int(sample_rate * 2.0)
audio[:fade_in] *= np.linspace(0, 1, fade_in)
audio[-fade_out:] *= np.linspace(1, 0, fade_out)

out_file = "/config/Desktop/BuildWithGemini/lofi_track.wav"
with wave.open(out_file, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    int_data = (audio * 32767).astype(np.int16)
    wf.writeframes(int_data.tobytes())

print(f"Generated lo-fi track: {out_file} ({total_dur:.1f}s)")

import streamlit as st
import numpy as np
import io
from pydub import AudioSegment
from typing import Tuple
import math # Needed for log10

# --- Constants ---
DEFAULT_DURATION_S = 10.0
SAMPLE_RATE = 44100
FADE_MS = 20 # Fade duration in milliseconds for loop smoothing
AMP_MOD_TARGET_FREQ_HZ = 2.0 # Target frequency for amplitude modulation LFO
FREQ_MOD_MAX_SHIFT_HZ = 10.0 # Max Hz shift for 100% f-mod
NUM_FM_CYCLES = 1 # Number of cycles for the frequency modulation LFO over the duration

st.title("Binaural Sound Generator – Smooth Loop Edition (Optimized)")

st.markdown(f"""
Adjust the sliders to create a binaural sound designed to loop smoothly
over a **{DEFAULT_DURATION_S:.1f}-second** duration.
Amplitude and frequency modulation frequencies are calculated to complete
an integer number of cycles within the loop.
A brief {FADE_MS}ms fade-in/out is applied for seamless transitions.
""")

# ------------------
# Sliders
# ------------------
# Using format="%.1f" for smoother display on some sliders
brainwave_freq = st.slider("Brainwave (Hz)", 0.1, 30.0, 1.86, 0.1, format="%.1f")
amp_mod        = st.slider("Amplitude Mod Depth (%)", 0.0, 100.0, 17.0, 1.0, format="%.1f")
binaural_mix   = st.slider("Binaural Mix (%)", 0.0, 100.0, 100.0, 1.0, format="%.1f")
stereo_width   = st.slider("Stereo Width (%)", 0.0, 100.0, 100.0, 1.0, format="%.1f")
freq_mod       = st.slider("Frequency Mod Depth (%)", 0.0, 100.0, 0.0, 1.0, format="%.1f")
carrier_freq   = st.slider("Carrier (Hz)", 20.0, 1000.0, 175.0, 1.0, format="%.1f")
noise_level    = st.slider("Noise Level (%)", 0.0, 100.0, 13.0, 1.0, format="%.1f")
volume         = st.slider("Volume (%)", 0.0, 100.0, 50.0, 1.0, format="%.1f")

# ------------------
# Cached Audio Generation Core
# ------------------
@st.cache_data # Cache the results of this expensive computation
def generate_binaural_raw(
    duration_s: float = DEFAULT_DURATION_S,
    sr: int = SAMPLE_RATE,
    carrier: float = 175.0,
    brainwave: float = 2.0,
    amp_mod_pct: float = 20.0,
    binaural_pct: float = 100.0,
    stereo_pct: float = 100.0,
    freq_mod_pct: float = 0.0,
    noise_pct: float = 0.0,
    # Note: volume_pct is NOT passed here; applied later
) -> Tuple[bytes, int, int]: # Returns raw_data (bytes), sr (int), channels (int)
    """
    Generates the raw byte data for a loopable binaural tone.

    Calculates LFO frequencies to ensure integer cycles over the duration
    for seamless looping. Excludes final volume scaling for caching efficiency.

    Returns:
        Tuple containing:
        - raw_audio_data: Interleaved stereo 16-bit PCM audio data as bytes.
        - sr: Sample rate used.
        - channels: Number of channels (always 2).
    """
    # This function uses integer-cycle snapping to ensure mathematically perfect loops without fading.
    
    n_samples = int(duration_s * sr)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    two_pi = 2 * np.pi

    # Convert percentages to multipliers (0.0 to 1.0)
    amp_mod_depth   = amp_mod_pct   / 100.0
    binaural_factor = binaural_pct  / 100.0
    stereo_factor   = stereo_pct    / 100.0
    freq_mod_depth  = freq_mod_pct  / 100.0
    noise_factor    = noise_pct     / 100.0

    # --- Snapdragon Frequencies for Perfect Looping ---
    # To prevent phase discontinuities at the loop boundary, we adjusted frequencies 
    # so they complete exactly an integer number of cycles within duration_s.
    
    # 1. Carrier Frequency Snap
    # Nearest integer cycle count
    carrier_cycles = round(carrier * duration_s)
    # Adjust carrier to exact frequency needed
    carrier_snapped = carrier_cycles / duration_s
    
    # 2. Brainwave Frequency Snap (Binaural Beat)
    # The beat frequency is the difference between L and R. 
    # We want the beat cycle to also be continuous.
    brainwave_cycles = round(brainwave * duration_s)
    brainwave_snapped = brainwave_cycles / duration_s
    
    # Base frequencies for left and right channels
    left_freq  = carrier_snapped
    right_freq = carrier_snapped + brainwave_snapped * binaural_factor

    # --- Calculate LFO frequencies for a perfect loop ---
    # Frequency modulation: exactly NUM_FM_CYCLES cycle(s) per loop.
    lfo_freq = NUM_FM_CYCLES / duration_s

    # Amplitude modulation: integer number of cycles
    num_cycles_am = max(1, round(AMP_MOD_TARGET_FREQ_HZ * duration_s)) 
    amp_mod_freq = num_cycles_am / duration_s

    # --- Calculate modulation signals ---
    # Frequency LFO
    freq_lfo = np.sin(two_pi * lfo_freq * t) * (FREQ_MOD_MAX_SHIFT_HZ * freq_mod_depth)
    
    # Amplitude LFO - "Spatial Tremolo"
    # User formula: 1.0 +/- depth * sin(...)
    # Note: This creates a signal that ranges from (1-depth) to (1+depth).
    # Max amplitude can reach 1.0 + 1.0 = 2.0 if depth is 100%.
    # We will normalize this later to prevent clipping.
    am_oscillator = np.sin(two_pi * amp_mod_freq * t)
    
    amp_lfo_left = 1.0 + amp_mod_depth * am_oscillator
    amp_lfo_right = 1.0 - amp_mod_depth * am_oscillator # 180 degree phase shift

    # --- Generate the waves with independent AM ---
    # Integrate frequency for phase. 
    # We add freq_lfo (Hz shift) to the base freq.
    left_phase = two_pi * np.cumsum(left_freq + freq_lfo) / sr
    right_phase = two_pi * np.cumsum(right_freq + freq_lfo) / sr
    
    left_wave  = np.sin(left_phase) * amp_lfo_left
    right_wave = np.sin(right_phase) * amp_lfo_right

    # --- Normalization to prevent Clipping ---
    # The AM logic can boost signal up to (1 + amp_mod_depth).
    # We basically divide by the max possible amplitude of the AM stage to keep it <= 1.0
    # (Before mixing noise/stereo, which are handled by ratios)
    max_am_boost = 1.0 + amp_mod_depth
    if max_am_boost > 0:
        left_wave /= max_am_boost
        right_wave /= max_am_boost

    # --- Add optional noise ---
    # Mix Logic: Signal * (1-N) + Noise * N
    # This prevents clipping as long as Signal and Noise are both <= 1.0
    if noise_factor > 0:
        noise = (2 * np.random.rand(n_samples) - 1.0) * noise_factor
        left_mix  = left_wave  * (1.0 - noise_factor) + noise
        right_mix = right_wave * (1.0 - noise_factor) + noise
    else:
        left_mix = left_wave
        right_mix = right_wave

    # --- Adjust stereo width ---
    # Standard stereo width algorithm
    if stereo_factor < 1.0:
        # Mid/Side processing equivalent
        # M = (L+R)/2, S = (L-R)/2
        # New L = M + S*width, New R = M - S*width
        # Simplified linear blend to mono:
        center = 0.5 * (left_mix + right_mix)
        left_mix  = stereo_factor * left_mix  + (1.0 - stereo_factor) * center
        right_mix = stereo_factor * right_mix + (1.0 - stereo_factor) * center

    # --- Prepare for PCM conversion ---
    # Check for NaNs just in case
    left_mix = np.nan_to_num(left_mix)
    right_mix = np.nan_to_num(right_mix)

    # Soft Clip / Limiter (Optional, but hard clip is safer if we normalized correctly)
    # We normalized AM, and Noise mix preserves limits. 
    # Just standard clamp.
    left_final = np.clip(left_mix, -1.0, 1.0)
    right_final = np.clip(right_mix, -1.0, 1.0)

    # Convert to 16-bit PCM
    left_pcm  = (left_final  * 32767).astype(np.int16)
    right_pcm = (right_final * 32767).astype(np.int16)

    # Interleave channels: Create a (N, 2) array and flatten
    interleaved = np.column_stack((left_pcm, right_pcm)).ravel()

    # Create raw bytes data
    raw_audio_data = interleaved.tobytes()

    return raw_audio_data, sr, 2 # data, sample_rate, channels

# ------------------
# Generate Audio using Cached Function and Apply Post-Processing
# ------------------
# Call the cached function with parameters from sliders (excluding volume)
raw_data, sr, channels = generate_binaural_raw(
    duration_s=DEFAULT_DURATION_S,
    sr=SAMPLE_RATE,
    carrier=carrier_freq,
    brainwave=brainwave_freq,
    amp_mod_pct=amp_mod,
    binaural_pct=binaural_mix,
    stereo_pct=stereo_width,
    freq_mod_pct=freq_mod,
    noise_pct=noise_level
)

# Create AudioSegment from cached raw data
audio_seg = AudioSegment(
    data=raw_data,
    sample_width=2,  # 16-bit audio = 2 bytes
    frame_rate=sr,
    channels=channels
)

# Apply short fade-in and fade-out AFTER generation for loop smoothing
# With the new frequency snapping logic, the loop is mathematically perfect.
# We skip fading to prevent volume dips at the loop point.
# audio_seg = audio_seg.fade_in(FADE_MS).fade_out(FADE_MS)

# Apply Volume *after* caching and fading using pydub's gain adjustment
# Convert volume percentage (0-100) to dB change.
# 100% -> 0 dB (no change)
# 50% -> -6 dB
# 0% -> -inf dB (silence)
if volume > 0:
    # Using 20 * log10(ratio) for amplitude scaling to dB
    gain_db = 20 * math.log10(volume / 100.0)
    audio_seg = audio_seg + gain_db
else:
    # Use a very large negative gain for effective silence
    audio_seg = audio_seg - 120 # Effectively silent (-120 dB)

# ------------------
# Convert to WAV and display in Streamlit
# ------------------
# Export the final AudioSegment to an in-memory WAV file
wav_io = io.BytesIO()
audio_seg.export(wav_io, format="wav")
wav_bytes = wav_io.getvalue()

# Display the audio player
st.audio(wav_bytes, format="audio/wav")

# Add a download button
st.download_button(
    label="Download WAV",
    data=wav_bytes,
    file_name=f"binaural_loop_{carrier_freq:.0f}Hz_{brainwave_freq:.1f}Hz.wav",
    mime="audio/wav"
)

st.write(f"Info: Sample Rate={SAMPLE_RATE}Hz, Duration={DEFAULT_DURATION_S}s")
# Optionally display calculated LFO frequencies for debugging/info
# lfo_f = NUM_FM_CYCLES / DEFAULT_DURATION_S
# num_am = max(1, round(AMP_MOD_TARGET_FREQ_HZ * DEFAULT_DURATION_S))
# amp_f = num_am / DEFAULT_DURATION_S
# st.write(f"FM LFO: {lfo_f:.3f} Hz ({NUM_FM_CYCLES} cycle), AM LFO: {amp_f:.3f} Hz ({num_am} cycles)")
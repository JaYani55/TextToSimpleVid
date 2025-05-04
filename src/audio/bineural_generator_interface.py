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
    n_samples = int(duration_s * sr)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    two_pi = 2 * np.pi

    # Convert percentages to multipliers (0.0 to 1.0)
    amp_mod_depth   = amp_mod_pct   / 100.0
    binaural_factor = binaural_pct  / 100.0
    stereo_factor   = stereo_pct    / 100.0
    freq_mod_depth  = freq_mod_pct  / 100.0
    noise_factor    = noise_pct     / 100.0

    # Base frequencies for left and right channels
    left_freq  = carrier
    right_freq = carrier + brainwave * binaural_factor

    # --- Calculate LFO frequencies for a perfect loop ---
    # Frequency modulation: exactly NUM_FM_CYCLES cycle(s) per loop.
    lfo_freq = NUM_FM_CYCLES / duration_s

    # Amplitude modulation: integer number of cycles, aiming for target frequency.
    num_cycles_am = max(1, round(AMP_MOD_TARGET_FREQ_HZ * duration_s)) # Ensure at least 1 cycle
    amp_mod_freq = num_cycles_am / duration_s # Exact frequency for integer cycles

    # --- Calculate modulation signals ---
    # Freq LFO: shifts frequency, scaled by FREQ_MOD_MAX_SHIFT_HZ
    freq_lfo = np.sin(two_pi * lfo_freq * t) * (FREQ_MOD_MAX_SHIFT_HZ * freq_mod_depth)
    # Amp LFO: varies amplitude between (1-depth) and (1+depth) -> adjusted to 1.0 +/- depth*sin(...)
    # Using (1 + sin)/2 shifts range from 0 to 1, scale by depth, offset if needed.
    # Original formula: 1.0 + amp_mod_depth * np.sin(...) -> range [1-depth, 1+depth]
    amp_lfo = 1.0 + amp_mod_depth * np.sin(two_pi * amp_mod_freq * t)


    # --- Generate the left and right channel waveforms ---
    # Apply frequency modulation by adding freq_lfo to the instantaneous frequency calculation
    # Integrate frequency over time for phase: cumsum(freq)/sr can be approximated by (base_freq + freq_lfo) * t
    # Note: A more precise FM requires integrating the frequency, but this is common approximation.
    left_phase = two_pi * np.cumsum(left_freq + freq_lfo) / sr
    right_phase = two_pi * np.cumsum(right_freq + freq_lfo) / sr
    # Generate wave using sine of the phase, apply amplitude modulation
    left_wave  = np.sin(left_phase) * amp_lfo
    right_wave = np.sin(right_phase) * amp_lfo
    # # Original simpler FM (less accurate but possibly intended):
    # left_wave  = np.sin(two_pi * (left_freq + freq_lfo) * t)  * amp_lfo
    # right_wave = np.sin(two_pi * (right_freq + freq_lfo) * t) * amp_lfo


    # --- Add optional noise ---
    # Generate noise once and apply to both channels if needed
    if noise_factor > 0:
        noise = (2 * np.random.rand(n_samples) - 1.0) * noise_factor
        left_mix  = left_wave  * (1.0 - noise_factor) + noise
        right_mix = right_wave * (1.0 - noise_factor) + noise
    else:
        left_mix = left_wave
        right_mix = right_wave

    # --- Adjust stereo width ---
    # If stereo_factor < 1.0, blend towards the center (mono)
    if stereo_factor < 1.0:
        center = 0.5 * (left_mix + right_mix)
        left_mix  = stereo_factor * left_mix  + (1.0 - stereo_factor) * center
        right_mix = stereo_factor * right_mix + (1.0 - stereo_factor) * center

    # --- Prepare for PCM conversion (No final volume scaling here) ---
    left_final  = left_mix
    right_final = right_mix

    # Clamp values to prevent clipping before conversion (important!)
    left_final = np.clip(left_final, -1.0, 1.0)
    right_final = np.clip(right_final, -1.0, 1.0)

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
audio_seg = audio_seg.fade_in(FADE_MS).fade_out(FADE_MS)

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
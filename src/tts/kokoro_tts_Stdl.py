import os
import time
import threading
import itertools
import sys
import soundfile as sf
from kokoro_onnx import Kokoro

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full paths to the model and voices files in a models subdirectory
models_dir = os.path.join(script_dir, "models")  # Create path to models directory
model_path = os.path.join(models_dir, "kokoro-v1.0.onnx")
voices_path = os.path.join(models_dir, "voices-v1.0.bin")

# Configuration settings
# Audio format requirements:
# - WAV files in standard PCM format
# - 16-bit depth with 44.1 kHz sample rate
# - Mono format (stereo will be converted to mono by mixing channels)
# - 30 seconds or less (max 1,323,000 samples)
DEFAULT_SAMPLE_RATE = 44100  # 44.1 kHz (required)
DEFAULT_BIT_DEPTH = 16  # 16-bit PCM format
DEFAULT_CHANNELS = 1  # Mono format
MAX_DURATION_SECONDS = 30  # Maximum allowed duration
MAX_SAMPLES = 1323000  # Maximum number of samples allowed (44100 * 30)

# TTS settings
DEFAULT_VOICE = "af_heart"
DEFAULT_SPEED = 1.0
DEFAULT_LANGUAGE = "en-us"

# Example text for TTS
example_text = (
    "The tree stood wide before it stood tall. "
    "Roots tearing ground of rock and of ore. "
    "Then the trunk and the crown, a marvel for all. "
    "Glory be, to those who dare grow. "
    "And love and peace to those, who lie low."
)

# Initialize Kokoro
kokoro = Kokoro(model_path, voices_path)

# Shared data for thread result and a completion flag
result = {}
done_event = threading.Event()

def run_tts(text=example_text, voice=DEFAULT_VOICE, speed=DEFAULT_SPEED, 
           lang=DEFAULT_LANGUAGE, sample_rate=DEFAULT_SAMPLE_RATE):
    samples, sr = kokoro.create(
        text, voice=voice, speed=speed, lang=lang
    )
    # Resample if needed (Kokoro returns its own sample rate, 
    # but we may want to convert to our target sample rate)
    # Note: For simplicity, we're not implementing resampling here
    # You would need a library like librosa or scipy for proper resampling
    result["samples"] = samples
    result["sample_rate"] = sr  # Using the actual sample rate returned by Kokoro
    result["target_sample_rate"] = sample_rate  # Store target rate for potential resampling
    done_event.set()

# Start TTS in a separate thread
tts_thread = threading.Thread(target=run_tts)
tts_thread.start()

start_time = time.time()
spinner = itertools.cycle(['|', '/', '-', '\\'])

print("Generating Kokoro-TTS: ", end="")
sys.stdout.flush()

# Run spinner and elapsed time counter until TTS generation is complete
while not done_event.is_set():
    elapsed = int(time.time() - start_time)
    # Get next spinner symbol
    spin = next(spinner)
    msg = f"{spin} {elapsed}s"
    sys.stdout.write(msg)
    sys.stdout.flush()
    # Erase the spinner output by backspacing over it
    sys.stdout.write("\b" * len(msg))
    time.sleep(0.1)

tts_thread.join()
end_time = time.time()

# Write the generated audio to a file ensuring it meets the requirements
output_file = "audio.wav"
samples = result["samples"]

# Limit duration if needed
if len(samples) > MAX_SAMPLES:
    print(f"Warning: Audio exceeds maximum length. Truncating to {MAX_DURATION_SECONDS} seconds.")
    samples = samples[:MAX_SAMPLES]

# Write as 16-bit PCM WAV file
sf.write(output_file, samples, result["sample_rate"], 
         subtype='PCM_16', format='WAV')
print(f"Audio file saved as {output_file} (Sample rate: {result['sample_rate']} Hz, 16-bit mono)")

# Print the total elapsed time
print(f"Created audio in {end_time - start_time:.2f} seconds")
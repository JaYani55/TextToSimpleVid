import os
import time
import threading
import itertools
import sys
import soundfile as sf
from kokoro_onnx import Kokoro

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full paths to the model and voices files
model_path = os.path.join(script_dir, "kokoro-v1.0.onnx")
voices_path = os.path.join(script_dir, "voices-v1.0.bin")

# Example text for TTS
example_text = (
    "In a world where technology and creativity intertwine, "
    "there exists a powerful tool that can transform written words into spoken art. "
    "This tool, known as Kokoro, harnesses the capabilities of advanced neural networks "
    "to generate lifelike voices that can narrate stories, convey emotions, and bring characters to life. "
    "Imagine a future where your favorite books are read to you by voices that sound as real as any human, "
    "where virtual assistants speak with warmth and personality, and where the boundaries between reality and imagination blur. "
    "Welcome to the future of text-to-speech, where the only limit is your imagination. "
    "As the sun sets over the horizon, casting a golden glow across the landscape, "
    "the voices of Kokoro come alive, telling tales of adventure and wonder. "
    "From the bustling streets of a futuristic city to the serene tranquility of a hidden forest, "
    "these voices transport you to worlds beyond your wildest dreams. "
    "Each word is imbued with emotion, each sentence crafted with care, "
    "creating an immersive experience that captivates the mind and stirs the soul. "
    "Whether you're listening to a gripping thriller, a heartwarming romance, or an inspiring speech, "
    "Kokoro's voices make every story unforgettable. "
    "In this new era of text-to-speech technology, the possibilities are endless. "
    "Educators can bring lessons to life with engaging narratives, "
    "authors can give their characters a voice that resonates with readers, "
    "and businesses can create personalized customer interactions that leave a lasting impression. "
    "With Kokoro, the power of the spoken word is at your fingertips, ready to transform the way you communicate and connect with the world."
)

# Initialize Kokoro
kokoro = Kokoro(model_path, voices_path)

# Shared data for thread result and a completion flag
result = {}
done_event = threading.Event()

def run_tts():
    samples, sample_rate = kokoro.create(
        example_text, voice="af_heart", speed=1.0, lang="en-us"
    )
    result["samples"] = samples
    result["sample_rate"] = sample_rate
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

# Write the generated audio to a file
sf.write("audio.wav", result["samples"], result["sample_rate"])
print("Audio file saved as audio.wav")

# Print the total elapsed time
#print(f"\nCreated audio.wav in {end_time - start_time:.2f} seconds")
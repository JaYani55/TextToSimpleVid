import os
import time
import threading
import itertools
import sys
import soundfile as sf
from kokoro_onnx import Kokoro

def generate_speech(text, output_file="tts_audio.mp3", voice="af_nicole", speed=1.0, lang="en-us"):
    # Set up paths and initialize Kokoro
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, "models")  # Go up one level and into models
    model_path = os.path.join(models_dir, "kokoro-v1.0.onnx")
    voices_path = os.path.join(models_dir, "voices-v1.0.bin")
    kokoro = Kokoro(model_path, voices_path)

    result = {}
    done_event = threading.Event()

    def run_tts():
        samples, sample_rate = kokoro.create(text, voice=voice, speed=speed, lang=lang)
        result["samples"] = samples
        result["sample_rate"] = sample_rate
        done_event.set()

    # Run TTS in a separate thread
    tts_thread = threading.Thread(target=run_tts)
    tts_thread.start()

    start_time = time.time()
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    print("Generating Kokoro-TTS: ", end="")
    sys.stdout.flush()

    # Spinner for status indication
    while not done_event.is_set():
        elapsed = int(time.time() - start_time)
        spin = next(spinner)
        msg = f"{spin} {elapsed}s"
        sys.stdout.write(msg)
        sys.stdout.flush()
        sys.stdout.write("\b" * len(msg))
        time.sleep(0.1)

    tts_thread.join()
    end_time = time.time()

    # Write the audio file
    sf.write(output_file, result["samples"], result["sample_rate"])
    audio_duration = len(result["samples"]) / result["sample_rate"]
    print(f"Audio file saved as {output_file}")
    print(f"Total TTS generation time: {end_time - start_time:.2f}s")
    return output_file, audio_duration
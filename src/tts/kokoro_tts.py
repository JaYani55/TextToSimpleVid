import os
import time
import threading
import itertools
import sys
import re
import soundfile as sf
import numpy as np
from kokoro_onnx import Kokoro

def split_text_smart(text, max_length=200):
    # Split by sentence endings (.!?) or newlines
    # The regex keeps the delimiters if possible, or we can just split and rejoin.
    # Here we split by delimiters that usually end a thought.
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If a single sentence is too long, split it further by commas or spaces
        if len(sentence) > max_length:
            sub_parts = re.split(r'[,;]\s+', sentence)
            for part in sub_parts:
                if len(current_chunk) + len(part) + 1 < max_length:
                    current_chunk += part + ", "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip(", "))
                    current_chunk = part + ", "
                    # If still too long, just hard split (unlikely with 200 chars but possible)
                    if len(current_chunk) > max_length:
                         chunks.append(current_chunk.strip(", "))
                         current_chunk = ""
            continue

        if len(current_chunk) + len(sentence) + 1 < max_length:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
            
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Fallback if no chunks (empty text)
    if not chunks and text:
        chunks = [text]
        
    return chunks

def generate_speech(text, output_file="tts_audio.mp3", voice="af_nicole", speed=1.0, lang="en-us"):
    # Set up paths and initialize Kokoro
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, "models")  # Go up one level and into models
    model_path = os.path.join(models_dir, "kokoro-v1.0.onnx")
    voices_path = os.path.join(models_dir, "voices-v1.0.bin")
    kokoro = Kokoro(model_path, voices_path)

    # Split text into chunks to avoid token limit
    chunks = split_text_smart(text)
    print(f"Splitting text into {len(chunks)} chunks for generation...")

    all_samples = []
    final_sample_rate = 24000

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
            
        print(f"Generating chunk {i+1}/{len(chunks)}...", end=" ")
        sys.stdout.flush()
        
        result = {}
        done_event = threading.Event()

        def run_tts():
            try:
                samples, sample_rate = kokoro.create(chunk, voice=voice, speed=speed, lang=lang)
                result["samples"] = samples
                result["sample_rate"] = sample_rate
            except Exception as e:
                result["error"] = e
            finally:
                done_event.set()

        tts_thread = threading.Thread(target=run_tts)
        tts_thread.start()

        spinner = itertools.cycle(['|', '/', '-', '\\'])
        while not done_event.is_set():
            sys.stdout.write(next(spinner))
            sys.stdout.flush()
            sys.stdout.write('\b')
            time.sleep(0.1)
            
        tts_thread.join()
        
        if "error" in result:
            print(f"\nError generating chunk {i+1}: {result['error']}")
        elif "samples" in result:
            all_samples.append(result["samples"])
            final_sample_rate = result["sample_rate"]
            print("Done.")
        else:
            print("Failed.")

    if not all_samples:
        print("Error: No audio generated.")
        return None, 0

    # Concatenate all samples
    combined_samples = np.concatenate(all_samples)

    # Write the audio file
    sf.write(output_file, combined_samples, final_sample_rate)
    audio_duration = len(combined_samples) / final_sample_rate
    
    return output_file, audio_duration
    print(f"Audio file saved as {output_file}")
    print(f"Total TTS generation time: {end_time - start_time:.2f}s")
    return output_file, audio_duration
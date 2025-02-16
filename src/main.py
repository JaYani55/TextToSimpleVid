import argparse
import os
import re
import sys

from moviepy import (
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips
)
from tts.kokoro_tts import generate_speech
from parser.markdown_parser import MarkdownParser
from media.video_processor import VideoProcessor

def main():
    parser = argparse.ArgumentParser(description="Simple Text-to-Video converter")
    parser.add_argument('--md', type=str, default='input/sample.md', help='Path to markdown file')
    parser.add_argument('--output', type=str, default='output', help='Output folder path')
    args = parser.parse_args()

    # Validate input file and ensure the output directory exists.
    if not os.path.exists(args.md): 
        print("Markdown file not found.")
        sys.exit(1)
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 1. Parse the markdown file
    print("Parsing markdown file...")
    parser = MarkdownParser(base_input_path="input")
    result = parser.parse(args.md)
    plain_text = result['text']
    markers = result['markers']
    print(f"Extracted text length: {len(plain_text)} characters")
    print(f"Found {len(markers)} media marker(s)")

    # 2. Generate TTS audio and output it in the output folder
    tts_audio_path = os.path.join(args.output, "tts_audio.mp3")
    print("Generating TTS audio...")
    audio_file, audio_duration = generate_speech(plain_text, output_file=tts_audio_path)
    print(f"Audio generated: {audio_file} (Duration: {audio_duration:.2f}s)")

    # 3. Create video from markers
    print("Creating video...")
    processor = VideoProcessor()
    final_clip = processor.create_video(markers, audio_file, audio_duration)

    # Ensure dimensions are even for h264 encoding
    even_width = final_clip.w - (final_clip.w % 2)
    even_height = final_clip.h - (final_clip.h % 2)
    final_clip = final_clip.resized((even_width, even_height))

    # Write the final video file
    output_video_path = os.path.join(args.output, "output_video.mp4")
    print("Exporting final video...")
    final_clip.write_videofile(
        output_video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )
    print(f"Video generated: {output_video_path}")

    # Clean up
    final_clip.close()

if __name__ == "__main__":
    main()
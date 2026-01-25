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
from subtitles.subtitle_renderer import SubtitleRenderer, add_text_overlays_to_video
from audio.audio_mixer import AudioMixer

def main():
    parser = argparse.ArgumentParser(description="Text-to-Video converter with multi-channel support")
    parser.add_argument('--md', type=str, default='input/sample.md', help='Path to markdown file')
    parser.add_argument('--output', type=str, default='output', help='Output folder path')
    parser.add_argument('--audio-only', action='store_true', help='Generate only audio file')
    parser.add_argument('--no-tts', action='store_true', help='Skip TTS generation')
    parser.add_argument('--subtitles', action='store_true', help='Generate subtitles from TTS text')
    parser.add_argument('--library', type=str, default='library', help='Path to media library folder')
    parser.add_argument('--width', type=int, default=1920, help='Video width')
    parser.add_argument('--height', type=int, default=1080, help='Video height')
    args = parser.parse_args()

    # Validate input file and ensure the output directory exists.
    if not os.path.exists(args.md): 
        print(f"Error: Markdown file not found: {args.md}")
        sys.exit(1)
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 1. Parse the markdown file
    print("Parsing markdown file...")
    md_parser = MarkdownParser(base_input_path="input", library_path=args.library)
    result = md_parser.parse(args.md)
    
    plain_text = result['text']
    video_markers = result['video_markers']
    audio_markers = result['audio_markers']
    text_markers = result['text_markers']
    explicit_duration = result['video_duration']
    
    print(f"Extracted text length: {len(plain_text)} characters")
    print(f"Found {len(video_markers)} video/image marker(s)")
    print(f"Found {len(audio_markers)} audio marker(s)")
    print(f"Found {len(text_markers)} text marker(s)")
    if explicit_duration:
        print(f"Explicit video duration: {explicit_duration}s")

    # 2. Generate TTS audio (if not disabled and there's text)
    tts_audio_path = None
    audio_duration = None
    
    if not args.no_tts and plain_text.strip():
        tts_audio_path = os.path.join(args.output, "tts_audio.mp3")
        print("Generating TTS audio...")
        audio_file, audio_duration = generate_speech(plain_text, output_file=tts_audio_path)
        print(f"Audio generated: {audio_file} (Duration: {audio_duration:.2f}s)")
    else:
        print("TTS generation skipped.")

    if args.audio_only:
        print("Audio-only mode selected. Skipping video generation.")
        return

    # 3. Determine final video duration
    # Priority: explicit duration > audio duration > calculated from markers
    if explicit_duration:
        target_duration = explicit_duration
    elif audio_duration:
        target_duration = audio_duration
    else:
        # Calculate from markers
        max_end = 0.0
        all_markers = video_markers + audio_markers + text_markers
        for m in all_markers:
            timestamp = float(m.get('timestamp', 0))
            duration = m.get('duration', 3.0)
            if duration != 'loop':
                max_end = max(max_end, timestamp + float(duration))
        target_duration = max(max_end, 10.0)
        
    print(f"Final video duration: {target_duration}s")

    # 4. Create video with multi-channel support
    print("Creating video...")
    processor = VideoProcessor(width=args.width, height=args.height)
    final_clip = processor.create_video(
        markers=result['markers'],  # Legacy support
        audio_file=tts_audio_path,
        audio_duration=audio_duration,
        video_duration=target_duration,
        video_markers=video_markers,
        audio_markers=audio_markers,
        text_markers=text_markers
    )

    # 5. Add text overlays (text markers and optional subtitles)
    if text_markers or (args.subtitles and plain_text):
        print("Adding text overlays...")
        subtitle_renderer = SubtitleRenderer(
            video_width=args.width,
            video_height=args.height
        )
        
        text_clips = []
        
        # Add text markers
        if text_markers:
            text_clips.extend(subtitle_renderer.create_text_clips_from_markers(text_markers))
            
        # Add auto-generated subtitles
        if args.subtitles and plain_text:
            text_clips.extend(subtitle_renderer.generate_subtitles_from_text(
                plain_text,
                target_duration
            ))
            
        if text_clips:
            # Compose text clips on top of video
            all_clips = [final_clip] + text_clips
            final_clip = CompositeVideoClip(all_clips, size=(args.width, args.height))
            print(f"Added {len(text_clips)} text overlay(s)")

    # Ensure dimensions are even for h264 encoding
    even_width = final_clip.w - (final_clip.w % 2)
    even_height = final_clip.h - (final_clip.h % 2)
    final_clip = final_clip.resized((even_width, even_height))

    # 6. Write the final video file
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
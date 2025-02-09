import argparse
from pathlib import Path
import sys
import os
from moviepy import *
from utils.font_manager import FontManager
from media.file_validator import MediaValidator
from subtitles.subtitle_renderer import generate_srt_file, render_subtitles
from parser.markdown_parser import MarkdownParser

class VideoGenerationError(Exception):
    """Custom exception for video generation errors"""
    pass

def main():
    print("\n=== Starting Text to Video Conversion ===")
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Convert markdown to video or output TTS audio')
        parser.add_argument('--input', type=str, required=True, help='Input markdown file')
        parser.add_argument('--output', type=str, required=True, help='Output file path (video or TTS audio)')
        parser.add_argument('--tts_output', type=str, default='',
                            help='Optional output directory for TTS audio file when generating video')
        parser.add_argument('--tts_only', action='store_true', help='Only generate TTS audio and exit')
        parser.add_argument('--audio_input', type=str, default='',
                            help='Optional external audio file to use instead of TTS generation')
        parser.add_argument('--subtitles_off', action='store_true', help='Disable subtitle display')
        parser.add_argument('--srt', type=str, default='', help='Optional SRT file for subtitles')
        args = parser.parse_args()

        # Validate input/output paths
        validator = MediaValidator()
        validator.validate_input_file(args.input)
        print(f"\nInput file: {args.input}")

        # Parse Markdown file
        print("\n[1] Parsing Markdown file...")
        md_parser = MarkdownParser()
        try:
            parsed = md_parser.parse(args.input)
        except Exception as e:
            raise VideoGenerationError(f"Failed to parse Markdown file: {str(e)}")
        plain_text = parsed.get('text', '')
        markers = parsed.get('markers', [])
        if not plain_text:
            raise VideoGenerationError("No text content found in Markdown file")
        print(f"Extracted text length: {len(plain_text)} characters")
        print(f"Number of media markers found: {len(markers)}")

        # --tts_only branch: generate only TTS audio and exit
        if args.tts_only:
            print("\n[2] Generating TTS audio only...")
            from tts.kokoro_tts import generate_speech
            try:
                audio_file, audio_duration = generate_speech(plain_text, output_file=args.output)
            except Exception as e:
                raise VideoGenerationError(f"TTS generation failed: {str(e)}")
            if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
                raise VideoGenerationError("Generated TTS audio is empty or missing.")
            print(f"TTS audio file generated: {audio_file}")
            print(f"Audio duration: {audio_duration:.2f} seconds")
            sys.exit(0)

        # Branch: if external audio file is provided, skip TTS generation.
        if args.audio_input:
            print("\n[2] Using external audio file for video...")
            if not os.path.exists(args.audio_input):
                raise VideoGenerationError(f"Provided audio file not found: {args.audio_input}")
            from moviepy import ColorClip, CompositeVideoClip, AudioFileClip
            audio_clip = AudioFileClip(args.audio_input)
            audio_duration = audio_clip.duration
            audio_file = args.audio_input
            print(f"External audio file: {audio_file}")
            print(f"Audio duration: {audio_duration:.2f} seconds")
        else:
            # Otherwise generate TTS audio for video.
            validator.validate_output_path(args.output)
            print(f"\nOutput file: {args.output}")
            tts_output_dir = args.tts_output if args.tts_output else os.path.dirname(args.output)
            tts_audio_file = os.path.join(tts_output_dir, "tts_audio.mp3")
            print("\n[2] Generating TTS audio for video...")
            from tts.kokoro_tts import generate_speech
            try:
                audio_file, audio_duration = generate_speech(plain_text, output_file=tts_audio_file)
            except Exception as e:
                raise VideoGenerationError(f"TTS generation failed: {str(e)}")
            if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
                raise VideoGenerationError("Generated TTS audio is empty or missing.")
            print(f"Audio file generated: {audio_file}")
            print(f"Audio duration: {audio_duration:.2f} seconds")

        # Before video composition, if subtitles are enabled and no SRT is provided, auto-generate one.
        if not args.subtitles_off and not args.srt:
            out_dir = os.path.dirname(args.output) if os.path.dirname(args.output) else "."
            auto_srt = os.path.join(out_dir, "temp_subtitles.srt")
            print(f"\n[pre-video] Generating subtitles SRT file: {auto_srt}")
            generate_srt_file(plain_text, audio_duration, auto_srt)
            args.srt = auto_srt

        # Create video composition
        print("\n[3] Creating video composition...")
        try:
            from moviepy import ColorClip, CompositeVideoClip, AudioFileClip
        except ImportError as e:
            raise VideoGenerationError(f"Failed to import required moviepy modules: {str(e)}")

        video_duration = audio_duration
        print(f"Setting video duration to: {video_duration:.2f} seconds")

        # Create base video composition
        base_clip = ColorClip(size=(640, 480), color=(50, 50, 50), duration=video_duration)
        composite_clip = CompositeVideoClip([base_clip])

        if not args.subtitles_off and args.srt:
            sub_clip = render_subtitles(args.srt, main_video_size=(1024,1024))
            if sub_clip is not None:
                composite_clip = CompositeVideoClip([composite_clip, sub_clip])
            else:
                print("Warning: Subtitle rendering failed, continuing without subtitles")
            
        # Process media markers
        print("\n[4] Processing media markers...")
        for i, marker in enumerate(markers, 1):
            print(f"\nProcessing marker {i}/{len(markers)}")
            try:
                if "imagepath:" in marker:
                    print(f"Processing image marker: {marker}")
                    parts = marker.split(',')
                    params = {k.strip(): v.strip() for k, v in (p.split(':', 1) for p in parts)}
                    
                    # Get image path and validate
                    image_path = params.get('imagepath', '').strip()
                    validator.validate_media_file(image_path, "image")
                    
                    # Load and process image
                    try:
                        duration = float(params.get('duration', video_duration))
                        image_clip = ImageClip(image_path).with_duration(duration)
                        
                        # Resize to match video dimensions if needed
                        if image_clip.size != (640, 480):
                            image_clip = image_clip.resize((640, 480))
                        
                        # Apply any specified effects
                        if params.get('effect') == 'edge':
                            # Add edge detection effect here if implemented
                            pass
                            
                        # Add image to composition at specified time
                        composite_clip = CompositeVideoClip([
                            composite_clip,
                            image_clip.with_start(0)  # Calculate start time if needed
                        ])
                        
                    except Exception as e:
                        raise VideoGenerationError(f"Failed to process image {image_path}: {str(e)}")
                        
                elif "videopath:" in marker:
                    print(f"Processing video marker: {marker}")
                    parts = marker.split(',')
                    params = {k.strip(): v.strip() for k, v in (p.split(':', 1) for p in parts)}
                    
                    # Get video path and validate
                    video_path = params.get('videopath', '').strip()
                    validator.validate_media_file(video_path, "video")
                    
                    # Load and process video
                    try:
                        video_clip = VideoFileClip(video_path)
                        
                        # Resize if needed
                        if video_clip.size != (640, 480):
                            video_clip = video_clip.resize((640, 480))
                        
                        # Apply transition if specified
                        if params.get('transition') == 'fade':
                            video_clip = video_clip.crossfadein(1.0)
                            
                        # Add video to composition
                        composite_clip = CompositeVideoClip([
                            composite_clip,
                            video_clip.with_start(0)  # Calculate start time if needed
                        ])
                        
                    except Exception as e:
                        raise VideoGenerationError(f"Failed to process video {video_path}: {str(e)}")
                        
                elif "audio:" in marker:
                    # For background audio marker; this demo does not mix additional audio.
                    pass
                    
            except Exception as e:
                print(f"Warning: Failed to process marker {i}: {str(e)}")
                continue

        # Final export
        print("\n[5] Exporting final video...")
        try:
            composite_clip = composite_clip.with_audio(AudioFileClip(audio_file))
            composite_clip.write_videofile(args.output, fps=24)
        except Exception as e:
            raise VideoGenerationError(f"Failed to export final video: {str(e)}")

        print("\n=== Video conversion completed successfully ===")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
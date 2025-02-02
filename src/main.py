import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Convert markdown to video')
    parser.add_argument('--input', type=str, required=True, help='Input markdown file')
    parser.add_argument('--output', type=str, required=True, help='Output video file path')
    args = parser.parse_args()

    # Parse Markdown file
    from parser.markdown_parser import MarkdownParser
    md_parser = MarkdownParser()
    parsed = md_parser.parse(args.input)
    plain_text = parsed.get('text', '')
    markers = parsed.get('markers', [])

    # Generate TTS audio (placeholder)
    from tts.elevenlabs_tts import ElevenLabsTTS
    tts = ElevenLabsTTS(api_key="YOUR_API_KEY_HERE")
    audio_file, audio_duration = tts.generate_speech(plain_text)
    
    # Check if generated TTS audio is empty (invalid API key)
    import os, sys
    if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
        sys.exit("Error: Generated TTS audio is empty. Please provide a valid API key.")

    # Create a basic visualizer clip using moviepy
    from moviepy import ColorClip, TextClip, CompositeVideoClip, AudioFileClip
    from pathlib import Path
    import sys
    
    # Get font path (ensure the font file exists)
    font_path = str(Path("assets/fonts/DejaVuSans.ttf").resolve())
    if not Path(font_path).exists():
        sys.exit(f"Error: Font file not found at {font_path}. Please download DejaVuSans.ttf")
    
    # Check TTS audio validity (this error is unrelated to font issues)
    if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
        sys.exit("Error: Generated TTS audio is empty. Please provide a valid API key and valid TTS output.")
    
    video_duration = audio_duration
    base_clip = ColorClip(size=(640, 480), color=(50, 50, 50), duration=video_duration)
    
    # Using MoviePy v2 chainable methods and updated parameter names:
    viz_label = TextClip(
                    font=font_path,
                    text="Audio Visualizer",
                    font_size=24,  # changed from fontsize to font_size
                    color='white'
                ).with_duration(video_duration).with_position('center')  # use with_position instead of set_position
    composite_clip = CompositeVideoClip([base_clip, viz_label])
    
    subtitle = TextClip(
                    font=font_path,
                    text=plain_text,
                    font_size=20,   # changed from fontsize to font_size
                    color='white',
                    bg_color='black'
                ).with_duration(video_duration).with_position(('center','bottom'))
    composite_clip = CompositeVideoClip([composite_clip, subtitle])

    # Process media markers (e.g., image and video)
    # Markers expected like: "imagepath: placeholder_image.svg, duration: 5, effect: edge"
    for marker in markers:
        if "imagepath:" in marker:
            parts = marker.split(',')
            params = {k.strip(): v.strip() for k, v in (p.split(':', 1) for p in parts)}
            duration = float(params.get('duration', video_duration))
            # Create a placeholder image clip (using a colored clip with label)
            from moviepy import ColorClip
            image_clip = ColorClip(size=(640,480), color=(100,100,200), duration=duration)
            img_label = TextClip(
                            font=font_path,
                            text="Image: " + params.get('imagepath', 'unknown'),
                            font_size=20,  # changed parameter name
                            color='white'
                        ).with_duration(duration).with_position('center')  # use with_position
            image_overlay = CompositeVideoClip([image_clip, img_label])
            # Overlay starting at t=0 (for demo purposes)
            composite_clip = CompositeVideoClip([composite_clip, image_overlay.with_start(0)])
        elif "videopath:" in marker:
            parts = marker.split(',')
            params = {k.strip(): v.strip() for k, v in (p.split(':', 1) for p in parts)}
            duration = float(params.get('duration', video_duration))
            # Create a placeholder video clip (using a differently colored clip)
            from moviepy import ColorClip
            video_clip = ColorClip(size=(640,480), color=(200,100,100), duration=duration)
            vid_label = TextClip(
                            font=font_path,
                            text="Video: " + params.get('videopath', 'unknown'),
                            font_size=20,  # changed parameter name
                            color='white'
                        ).with_duration(duration).with_position('center')  # use with_position
            video_overlay = CompositeVideoClip([video_clip, vid_label])
            composite_clip = CompositeVideoClip([composite_clip, video_overlay.with_start(0)])
        elif "audio:" in marker:
            # For background audio marker; this demo does not mix additional audio.
            pass

    # Attach the generated TTS audio
    composite_clip = composite_clip.with_audio(AudioFileClip(audio_file))
    
    # Write out the final video
    composite_clip.write_videofile(args.output, fps=24)

if __name__ == "__main__":
    main()

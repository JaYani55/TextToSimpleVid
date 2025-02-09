from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy import TextClip
import os

def format_timestamp(seconds):
    """Format seconds into SRT timestamp format."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    millis = int(round((secs - int(secs)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{int(secs):02d},{millis:03d}"

def generate_srt_file(text, duration, srt_path):
    """Generate a single-entry SRT file with the entire text spanning [0, duration]."""
    start_ts = format_timestamp(0)
    end_ts = format_timestamp(duration)
    srt_content = f"1\n{start_ts} --> {end_ts}\n{text}\n\n"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    return srt_path

from moviepy import *
from moviepy.video.tools.subtitles import SubtitlesClip
import os

def render_subtitles(srt_file, main_video_size):
    """Create a SubtitlesClip from an SRT file."""
    try:
        def generator(txt):
            return TextClip(
                txt, 
                size=main_video_size,
                method='caption',
                color='white',
                font='Arial',
                fontsize=30,
                align='center',  # Add alignment
                bg_color='black',  # Add background
                stroke_color='black',  # Add stroke
                stroke_width=2  # Add stroke width
            ).set_position(('center', 'bottom'))  # Position at bottom center
        
        subtitles = SubtitlesClip(srt_file, generator)
        return subtitles.set_duration(subtitles.duration)  # Ensure duration is set
        
    except Exception as e:
        print(f"Warning: Subtitle rendering failed: {str(e)}")
        return None

from moviepy import (
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    ImageSequenceClip
)
import os
import imageio
from PIL import Image

class VideoProcessor:
    def __init__(self, width=1920, height=1080, bg_color=(50, 50, 50)):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        
    def create_clip_from_marker(self, marker):
        """Create a video clip from a marker definition."""
        duration = float(marker.get('duration', marker.get('wait', 3.0)))
        start_time = float(marker.get('start_time', 0.0))
        target_width = int(self.width * 0.8)  # 80% of screen width
        
        try:
            if 'imagepath' in marker:
                if os.path.exists(marker['imagepath']):
                    # Check if the image is a GIF
                    if marker['imagepath'].lower().endswith('.gif'):
                        # Handle animated GIF using imageio
                        return self._create_animated_gif_clip(marker['imagepath'], duration, start_time, target_width)
                    else:
                        # Handle standard image
                        clip = (ImageClip(marker['imagepath'])
                              .with_duration(duration)
                              .with_start(start_time)
                              .with_position('center')
                              .resized(width=target_width))
                        return clip
                    
            elif 'videopath' in marker:
                if os.path.exists(marker['videopath']):
                    clip = (VideoFileClip(marker['videopath'])
                           .with_duration(duration)
                           .with_start(start_time)
                           .with_position('center')
                           .resized(width=target_width))
                    return clip
        except Exception as e:
            print(f"Warning: Failed to create clip from marker: {e}")
            
        return None
    
    def _create_animated_gif_clip(self, gif_path, duration, start_time, target_width):
        """Create an animated clip from a GIF using imageio, ensuring animation plays for full duration."""
        try:
            # Define the desired fixed fps
            fixed_fps = 20  # You can change this to the original GIF's intended fps
            
            # Read all frames from the GIF
            frames = imageio.mimread(gif_path)
            if not frames:
                raise ValueError("No frames extracted from GIF.")
            
            # Convert frames to RGB if they have an alpha channel
            processed_frames = []
            for frame in frames:
                if frame.shape[-1] == 4:
                    frame = frame[..., :3]
                processed_frames.append(frame)
            
            # Create an ImageSequenceClip using the fixed fps
            sequence_clip = ImageSequenceClip(processed_frames, fps=fixed_fps)
            
            # Calculate how many times we need to loop to fill the duration
            original_duration = len(processed_frames) / fixed_fps
            loop_count = int(duration / original_duration) + 1  # +1 to ensure we exceed the requested duration
            
            # Create a list of repeated frames to cover the full duration
            extended_frames = []
            for _ in range(loop_count):
                extended_frames.extend(processed_frames)
            
            # Create the final clip with the extended frames
            clip = (ImageSequenceClip(extended_frames, fps=fixed_fps)
                    .with_duration(duration)  # Trim to exact duration
                    .with_start(start_time)
                    .with_position('center')
                    .resized(width=target_width))
            return clip
        except Exception as e:
            print(f"Error processing animated GIF: {e}")
            # Fallback to a static image clip
            return (ImageClip(gif_path)
                    .with_duration(duration)
                    .with_start(start_time)
                    .with_position('center')
                    .resized(width=target_width))

    def create_video(self, markers, audio_file=None, audio_duration=None):
        """Create a video from markers and optional audio"""
        # Calculate timing and scaling
        original_total = sum(float(m.get('duration', m.get('wait', 3.0))) for m in markers)
        
        # Use audio duration if available, otherwise use markers total
        target_duration = audio_duration if audio_duration else original_total
        scaling = target_duration / original_total if original_total > 0 else 1.0
        
        # Update marker timings
        current_time = 0.0
        for marker in markers:
            duration = float(marker.get('duration', marker.get('wait', 3.0))) * scaling
            marker['duration'] = duration
            marker['start_time'] = current_time
            current_time += duration

        # Create clips
        clips = []
        
        # Base background clip
        base_clip = ColorClip(
            size=(self.width, self.height),
            color=self.bg_color,
            duration=target_duration
        )
        clips.append(base_clip)
        
        # Media clips
        for marker in markers:
            clip = self.create_clip_from_marker(marker)
            if clip:
                clips.append(clip)
        
        # Create composite
        print(f"Creating composite video with {len(clips)} clips...")
        final_clip = CompositeVideoClip(clips, size=(self.width, self.height))
        
        # Add audio if provided
        if audio_file and os.path.exists(audio_file):
            print("Adding audio track...")
            final_clip = final_clip.with_audio(AudioFileClip(audio_file))
        
        # Ensure dimensions are even
        even_width = final_clip.w - (final_clip.w % 2)
        even_height = final_clip.h - (final_clip.h % 2)
        final_clip = final_clip.resized((even_width, even_height))
            
        return final_clip
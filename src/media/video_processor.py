from moviepy import (
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    ImageSequenceClip,
    concatenate_videoclips,
    CompositeAudioClip
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
import os
import imageio
from PIL import Image
from typing import Dict, List, Any, Optional, Tuple

class VideoProcessor:
    """
    Video processor that supports multi-channel layered composition with looping media.
    
    Features:
    - Multi-channel video/image composition (higher channel = on top)
    - Multi-channel audio mixing
    - Loop support for video/audio/image clips
    - Opacity and transitions between channels
    """
    
    def __init__(self, width: int = 1920, height: int = 1080, bg_color: Tuple[int, int, int] = (0, 0, 0)):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        
    def _loop_clip(self, clip, target_duration: float):
        """
        Loop a clip to fill the target duration.
        
        Args:
            clip: The MoviePy clip to loop
            target_duration: The duration to fill
            
        Returns:
            A new clip that loops to fill the target duration
        """
        if clip.duration is None or clip.duration <= 0:
            return clip.with_duration(target_duration)
            
        if clip.duration >= target_duration:
            return clip.subclipped(0, target_duration)
            
        # Calculate number of loops needed
        num_loops = int(target_duration / clip.duration) + 1
        
        # Create looped clip by concatenating
        clips = [clip] * num_loops
        looped = concatenate_videoclips(clips)
        
        # Trim to exact duration
        return looped.subclipped(0, target_duration)
        
    def _loop_audio_clip(self, clip, target_duration: float):
        """
        Loop an audio clip to fill the target duration.
        
        Args:
            clip: The MoviePy audio clip to loop
            target_duration: The duration to fill
            
        Returns:
            A new audio clip that loops to fill the target duration
        """
        if clip.duration is None or clip.duration <= 0:
            return clip.with_duration(target_duration)
            
        if clip.duration >= target_duration:
            return clip.subclipped(0, target_duration)
            
        from moviepy import concatenate_audioclips
        
        # Calculate number of loops needed
        num_loops = int(target_duration / clip.duration) + 1
        
        # Create looped clip by concatenating
        clips = [clip] * num_loops
        looped = concatenate_audioclips(clips)
        
        # Trim to exact duration
        return looped.subclipped(0, target_duration)
        
    def create_clip_from_marker(self, marker: Dict[str, Any], total_duration: float) -> Optional[Any]:
        """
        Create a video clip from a marker definition with loop support.
        
        Args:
            marker: The parsed marker dictionary
            total_duration: The total video duration (for loop calculations)
            
        Returns:
            A MoviePy clip or None if creation fails
        """
        duration = marker.get('duration', 3.0)
        start_time = float(marker.get('timestamp', 0.0))
        opacity = float(marker.get('opacity', 1.0))
        position = marker.get('position', 'center')
        volume = float(marker.get('volume', 1.0))  # Volume for video audio
        target_width = int(self.width * 0.8)  # 80% of screen width
        
        # Handle loop duration
        is_loop = duration == 'loop'
        if is_loop:
            # Loop until end of video from start_time
            duration = total_duration - start_time
        else:
            duration = float(duration)
        
        try:
            clip = None
            
            if 'imagepath' in marker:
                path = marker['imagepath']
                if not os.path.exists(path):
                    print(f"Warning: Image not found: {path}")
                    return None
                    
                # Check if the image is a GIF
                if path.lower().endswith('.gif'):
                    clip = self._create_animated_gif_clip(path, duration, target_width)
                else:
                    clip = (ImageClip(path)
                          .with_duration(duration)
                          .resized(width=target_width))
                    
            elif 'videopath' in marker:
                path = marker['videopath']
                if not os.path.exists(path):
                    print(f"Warning: Video not found: {path}")
                    return None
                    
                video_clip = VideoFileClip(path)
                
                if is_loop:
                    clip = self._loop_clip(video_clip, duration)
                else:
                    # If requested duration is longer than clip, loop it
                    if video_clip.duration < duration:
                        clip = self._loop_clip(video_clip, duration)
                    else:
                        clip = video_clip.subclipped(0, min(duration, video_clip.duration))
                        
                clip = clip.resized(width=target_width)
                
            if clip is not None:
                # Apply start time and position
                clip = clip.with_start(start_time).with_position(position)
                
                # Apply opacity if not 1.0
                if opacity < 1.0:
                    clip = clip.with_opacity(opacity)
                
                # Apply volume to video's audio track
                if 'videopath' in marker and clip.audio is not None and volume != 1.0:
                    clip = clip.with_volume_scaled(volume)
                    
                # Apply transition effects
                transition = marker.get('transition', '')
                if transition == 'fade':
                    fade_duration = min(0.5, duration / 4)
                    clip = clip.with_effects([
                        CrossFadeIn(fade_duration),
                        CrossFadeOut(fade_duration)
                    ])
                    
                return clip
                
        except Exception as e:
            print(f"Warning: Failed to create clip from marker: {e}")
            import traceback
            traceback.print_exc()
            
        return None
    
    def _create_animated_gif_clip(self, gif_path: str, duration: float, target_width: int):
        """
        Create an animated clip from a GIF using imageio, ensuring animation plays for full duration.
        
        Args:
            gif_path: Path to the GIF file
            duration: Target duration in seconds
            target_width: Target width for resizing
            
        Returns:
            An ImageSequenceClip that loops to fill the duration
        """
        try:
            fixed_fps = 20
            
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
            
            # Calculate how many times we need to loop to fill the duration
            original_duration = len(processed_frames) / fixed_fps
            loop_count = int(duration / original_duration) + 1
            
            # Create extended frames
            extended_frames = []
            for _ in range(loop_count):
                extended_frames.extend(processed_frames)
            
            # Create the final clip
            clip = (ImageSequenceClip(extended_frames, fps=fixed_fps)
                    .with_duration(duration)
                    .resized(width=target_width))
            return clip
            
        except Exception as e:
            print(f"Error processing animated GIF: {e}")
            # Fallback to a static image clip
            return (ImageClip(gif_path)
                    .with_duration(duration)
                    .resized(width=target_width))
                    
    def create_audio_from_marker(self, marker: Dict[str, Any], total_duration: float) -> Optional[Any]:
        """
        Create an audio clip from a marker definition with loop support.
        
        Args:
            marker: The parsed marker dictionary
            total_duration: The total video duration (for loop calculations)
            
        Returns:
            A MoviePy AudioFileClip or None if creation fails
        """
        duration = marker.get('duration')
        start_time = float(marker.get('timestamp', 0.0))
        volume = float(marker.get('volume', 1.0))
        
        # Get path from either audiopath or sfxpath
        path = marker.get('audiopath') or marker.get('sfxpath')
        if not path:
            return None
            
        if not os.path.exists(path):
            print(f"Warning: Audio file not found: {path}")
            return None
            
        try:
            # Try loading audio directly
            try:
                audio_clip = AudioFileClip(path)
            except KeyError as ke:
                # Handle missing metadata like 'audio_bitrate'
                # Fall back to loading via video clip if it's a video file with audio
                if path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                    print(f"Note: Loading audio from video file: {path}")
                    video_clip = VideoFileClip(path)
                    audio_clip = video_clip.audio
                    if audio_clip is None:
                        print(f"Warning: No audio track in video: {path}")
                        return None
                else:
                    # Try alternative loading method using ffmpeg directly
                    print(f"Warning: Could not load audio metadata for {path}, trying alternative method")
                    from moviepy.audio.io.readers import FFMPEG_AudioReader
                    # Re-raise if we can't handle it
                    raise
            
            # Handle duration
            is_loop = duration == 'loop'
            if is_loop:
                target_duration = total_duration - start_time
                audio_clip = self._loop_audio_clip(audio_clip, target_duration)
            elif duration is not None:
                target_duration = float(duration)
                if audio_clip.duration and audio_clip.duration < target_duration:
                    audio_clip = self._loop_audio_clip(audio_clip, target_duration)
                elif audio_clip.duration:
                    audio_clip = audio_clip.subclipped(0, min(target_duration, audio_clip.duration))
            # If duration is None (SFX), play once
            
            # Apply start time
            audio_clip = audio_clip.with_start(start_time)
            
            # Apply volume
            if volume != 1.0:
                audio_clip = audio_clip.with_volume_scaled(volume)
                
            return audio_clip
            
        except Exception as e:
            print(f"Warning: Failed to create audio clip from {path}: {e}")
            import traceback
            traceback.print_exc()
            
        return None

    def create_video(
        self, 
        markers: List[Dict[str, Any]], 
        audio_file: Optional[str] = None, 
        audio_duration: Optional[float] = None,
        video_duration: Optional[float] = None,
        video_markers: Optional[List[Dict[str, Any]]] = None,
        audio_markers: Optional[List[Dict[str, Any]]] = None,
        text_markers: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Create a layered video from markers with multi-channel support.
        
        Channels work as follows:
        - Higher channel numbers are rendered on top of lower channels
        - Channel 0 is the background
        - Audio channels are mixed together
        
        Args:
            markers: Legacy list of all markers (for backward compatibility)
            audio_file: Path to TTS audio file
            audio_duration: Duration of TTS audio
            video_duration: Explicit video duration override
            video_markers: Parsed video/image markers
            audio_markers: Parsed audio/sfx markers
            text_markers: Parsed text overlay markers
            
        Returns:
            A CompositeVideoClip ready for export
        """
        # Use new marker lists if provided, else fall back to legacy markers
        if video_markers is None:
            video_markers = [m for m in markers if 'imagepath' in m or 'videopath' in m]
        if audio_markers is None:
            audio_markers = [m for m in markers if 'audiopath' in m or 'sfxpath' in m]
        if text_markers is None:
            text_markers = [m for m in markers if 'text' in m]
            
        # Determine total duration
        if video_duration:
            target_duration = video_duration
        elif audio_duration:
            target_duration = audio_duration
        else:
            # Calculate from markers
            max_end_time = 0.0
            for m in video_markers + audio_markers + text_markers:
                timestamp = float(m.get('timestamp', 0))
                duration = m.get('duration', 3.0)
                if duration != 'loop':
                    max_end_time = max(max_end_time, timestamp + float(duration))
                else:
                    max_end_time = max(max_end_time, timestamp + 10.0)  # Default loop extension
            target_duration = max(max_end_time, 10.0)
            
        print(f"Target video duration: {target_duration}s")

        # Create base background clip
        base_clip = ColorClip(
            size=(self.width, self.height),
            color=self.bg_color,
            duration=target_duration
        )
        
        # Organize video clips by channel
        channel_clips: Dict[int, List[Any]] = {}
        
        for marker in video_markers:
            clip = self.create_clip_from_marker(marker, target_duration)
            if clip:
                channel = marker.get('channel', 1)
                if channel not in channel_clips:
                    channel_clips[channel] = []
                channel_clips[channel].append(clip)
                
        # Build final clip list sorted by channel (lower channels first = rendered behind)
        all_video_clips = [base_clip]
        for channel in sorted(channel_clips.keys()):
            all_video_clips.extend(channel_clips[channel])
            
        # Create composite video
        print(f"Creating composite video with {len(all_video_clips)} clips across {len(channel_clips)} channels...")
        final_clip = CompositeVideoClip(all_video_clips, size=(self.width, self.height))
        
        # Process audio markers and mix with TTS audio
        audio_clips = []
        
        # Add TTS audio if provided
        if audio_file and os.path.exists(audio_file):
            print("Adding TTS audio track...")
            tts_audio = AudioFileClip(audio_file)
            audio_clips.append(tts_audio)
            
        # Add audio from markers
        for marker in audio_markers:
            audio_clip = self.create_audio_from_marker(marker, target_duration)
            if audio_clip:
                audio_clips.append(audio_clip)
                
        # Compose all audio
        if audio_clips:
            if len(audio_clips) == 1:
                final_audio = audio_clips[0]
            else:
                final_audio = CompositeAudioClip(audio_clips)
            final_clip = final_clip.with_audio(final_audio)
            print(f"Mixed {len(audio_clips)} audio tracks")
        
        # Ensure dimensions are even for h264 encoding
        even_width = final_clip.w - (final_clip.w % 2)
        even_height = final_clip.h - (final_clip.h % 2)
        final_clip = final_clip.resized((even_width, even_height))
            
        return final_clip
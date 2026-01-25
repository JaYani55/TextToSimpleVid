"""
Audio Mixer for TextToSimpleVid.

This module provides functionality for mixing multiple audio tracks,
including TTS audio, background music, binaural beats, and sound effects.
"""

from moviepy import AudioFileClip, CompositeAudioClip, concatenate_audioclips
from typing import List, Dict, Any, Optional, Tuple
import os
import numpy as np


class AudioMixer:
    """
    Mixes multiple audio tracks with support for:
    - Volume control per track
    - Looping audio to fill duration
    - Fade in/out effects
    - Channel-based organization
    """
    
    def __init__(self, sample_rate: int = 44100):
        """
        Initialize the AudioMixer.
        
        Args:
            sample_rate: Sample rate for audio processing
        """
        self.sample_rate = sample_rate
        
    def load_audio(self, path: str) -> Optional[AudioFileClip]:
        """
        Load an audio file.
        
        Args:
            path: Path to the audio file
            
        Returns:
            AudioFileClip or None if loading fails
        """
        if not os.path.exists(path):
            print(f"Warning: Audio file not found: {path}")
            return None
            
        try:
            return AudioFileClip(path)
        except Exception as e:
            print(f"Error loading audio file {path}: {e}")
            return None
            
    def loop_audio(self, clip: AudioFileClip, target_duration: float) -> AudioFileClip:
        """
        Loop an audio clip to fill the target duration.
        
        Args:
            clip: The audio clip to loop
            target_duration: Duration to fill
            
        Returns:
            Looped audio clip
        """
        if clip.duration is None or clip.duration <= 0:
            return clip.with_duration(target_duration)
            
        if clip.duration >= target_duration:
            return clip.subclipped(0, target_duration)
            
        # Calculate loops needed
        num_loops = int(target_duration / clip.duration) + 1
        
        # Concatenate loops
        clips = [clip] * num_loops
        looped = concatenate_audioclips(clips)
        
        # Trim to exact duration
        return looped.subclipped(0, target_duration)
        
    def apply_fade(
        self, 
        clip: AudioFileClip, 
        fade_in: float = 0.0, 
        fade_out: float = 0.0
    ) -> AudioFileClip:
        """
        Apply fade in and/or fade out to an audio clip.
        
        Args:
            clip: The audio clip
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            
        Returns:
            Audio clip with fades applied
        """
        if fade_in > 0:
            clip = clip.with_effects([lambda c: c.audio_fadein(fade_in)])
        if fade_out > 0:
            clip = clip.with_effects([lambda c: c.audio_fadeout(fade_out)])
        return clip
        
    def create_audio_from_markers(
        self,
        audio_markers: List[Dict[str, Any]],
        total_duration: float
    ) -> List[AudioFileClip]:
        """
        Create audio clips from parsed markers.
        
        Args:
            audio_markers: List of audio marker dictionaries
            total_duration: Total video/audio duration
            
        Returns:
            List of configured AudioFileClips
        """
        clips = []
        
        for marker in audio_markers:
            path = marker.get('audiopath') or marker.get('sfxpath')
            if not path:
                continue
                
            clip = self.load_audio(path)
            if not clip:
                continue
                
            # Get timing parameters
            start_time = float(marker.get('timestamp', 0.0))
            duration = marker.get('duration')
            volume = float(marker.get('volume', 1.0))
            
            # Handle duration/looping
            if duration == 'loop':
                target_duration = total_duration - start_time
                clip = self.loop_audio(clip, target_duration)
            elif duration is not None:
                target_duration = float(duration)
                if clip.duration < target_duration:
                    clip = self.loop_audio(clip, target_duration)
                else:
                    clip = clip.subclipped(0, min(target_duration, clip.duration))
            # SFX (duration=None) plays once
            
            # Apply start time
            clip = clip.with_start(start_time)
            
            # Apply volume
            if volume != 1.0:
                clip = clip.with_volume_scaled(volume)
                
            clips.append(clip)
            
        return clips
        
    def mix_tracks(
        self,
        tracks: List[AudioFileClip],
        master_volume: float = 1.0
    ) -> Optional[CompositeAudioClip]:
        """
        Mix multiple audio tracks into a single composite.
        
        Args:
            tracks: List of audio clips to mix
            master_volume: Master volume multiplier
            
        Returns:
            CompositeAudioClip or None if no tracks
        """
        if not tracks:
            return None
            
        if len(tracks) == 1:
            mixed = tracks[0]
        else:
            mixed = CompositeAudioClip(tracks)
            
        if master_volume != 1.0:
            mixed = mixed.with_volume_scaled(master_volume)
            
        return mixed
        
    def create_final_audio(
        self,
        tts_audio_path: Optional[str],
        audio_markers: List[Dict[str, Any]],
        total_duration: float,
        tts_volume: float = 1.0,
        background_volume: float = 0.3,
        sfx_volume: float = 0.8
    ) -> Optional[CompositeAudioClip]:
        """
        Create the final mixed audio for the video.
        
        Organizes audio by type:
        - TTS audio (speech) at tts_volume
        - Background audio (music, binaural) at background_volume
        - SFX at sfx_volume
        
        Args:
            tts_audio_path: Path to TTS audio file
            audio_markers: Parsed audio markers
            total_duration: Total video duration
            tts_volume: Volume for TTS
            background_volume: Volume for background audio
            sfx_volume: Volume for sound effects
            
        Returns:
            Mixed audio clip or None
        """
        all_tracks = []
        
        # Load TTS audio
        if tts_audio_path:
            tts_clip = self.load_audio(tts_audio_path)
            if tts_clip:
                if tts_volume != 1.0:
                    tts_clip = tts_clip.with_volume_scaled(tts_volume)
                all_tracks.append(tts_clip)
                
        # Process markers
        for marker in audio_markers:
            path = marker.get('audiopath') or marker.get('sfxpath')
            if not path:
                continue
                
            clip = self.load_audio(path)
            if not clip:
                continue
                
            start_time = float(marker.get('timestamp', 0.0))
            duration = marker.get('duration')
            
            # Determine if this is background or SFX
            is_sfx = 'sfxpath' in marker
            base_volume = sfx_volume if is_sfx else background_volume
            
            # Apply marker-specific volume on top of base
            marker_volume = float(marker.get('volume', 1.0))
            final_volume = base_volume * marker_volume
            
            # Handle duration
            if duration == 'loop':
                target_duration = total_duration - start_time
                clip = self.loop_audio(clip, target_duration)
            elif duration is not None:
                target_duration = float(duration)
                if clip.duration < target_duration:
                    clip = self.loop_audio(clip, target_duration)
                else:
                    clip = clip.subclipped(0, min(target_duration, clip.duration))
                    
            # Apply timing and volume
            clip = clip.with_start(start_time)
            if final_volume != 1.0:
                clip = clip.with_volume_scaled(final_volume)
                
            all_tracks.append(clip)
            
        return self.mix_tracks(all_tracks)


def mix_audio_for_video(
    tts_audio_path: Optional[str],
    audio_markers: List[Dict[str, Any]],
    total_duration: float
) -> Optional[CompositeAudioClip]:
    """
    Convenience function to create mixed audio for video.
    
    Args:
        tts_audio_path: Path to TTS audio
        audio_markers: Audio markers from parser
        total_duration: Video duration
        
    Returns:
        Mixed audio clip
    """
    mixer = AudioMixer()
    return mixer.create_final_audio(
        tts_audio_path,
        audio_markers,
        total_duration
    )

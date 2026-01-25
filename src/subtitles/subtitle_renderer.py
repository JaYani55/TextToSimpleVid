"""
Subtitle and Text-on-Screen Renderer for TextToSimpleVid.

This module provides functionality for rendering text overlays on video,
including subtitles synced to TTS audio and custom text markers from markdown.
"""

from moviepy import TextClip, CompositeVideoClip
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from typing import Dict, List, Any, Optional, Tuple
import os


class SubtitleRenderer:
    """
    Renders text overlays for video including subtitles and custom text markers.
    
    Supports:
    - Auto-synced subtitles from TTS text
    - Custom text markers with positioning and styling
    - Multiple text styles (title, subtitle, caption, custom)
    """
    
    # Windows system font paths
    WINDOWS_FONTS = {
        'arial': 'C:/Windows/Fonts/arial.ttf',
        'arial-bold': 'C:/Windows/Fonts/arialbd.ttf',
        'arial-italic': 'C:/Windows/Fonts/ariali.ttf',
        'times': 'C:/Windows/Fonts/times.ttf',
        'times-bold': 'C:/Windows/Fonts/timesbd.ttf',
        'verdana': 'C:/Windows/Fonts/verdana.ttf',
        'verdana-bold': 'C:/Windows/Fonts/verdanab.ttf',
        'georgia': 'C:/Windows/Fonts/georgia.ttf',
        'impact': 'C:/Windows/Fonts/impact.ttf',
        'comic': 'C:/Windows/Fonts/comic.ttf',
    }
    
    # Predefined text styles
    STYLES = {
        'title': {
            'font': 'arial-bold',
            'fontsize': 72,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 3,
            'method': 'caption',
        },
        'subtitle': {
            'font': 'arial',
            'fontsize': 48,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'method': 'caption',
        },
        'caption': {
            'font': 'arial',
            'fontsize': 36,
            'color': 'yellow',
            'stroke_color': 'black',
            'stroke_width': 1,
            'method': 'caption',
        },
        'heading': {
            'font': 'arial-bold',
            'fontsize': 64,
            'color': 'white',
            'stroke_color': None,
            'stroke_width': 0,
            'method': 'label',
        },
        'default': {
            'font': 'arial',
            'fontsize': 48,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'method': 'caption',
        }
    }
    
    def __init__(
        self, 
        video_width: int = 1920, 
        video_height: int = 1080,
        default_font: str = 'Arial',
        fonts_dir: Optional[str] = None
    ):
        """
        Initialize the SubtitleRenderer.
        
        Args:
            video_width: Width of the output video
            video_height: Height of the output video
            default_font: Default font to use for text
            fonts_dir: Optional path to custom fonts directory
        """
        self.video_width = video_width
        self.video_height = video_height
        self.default_font = default_font
        self.fonts_dir = fonts_dir or "assets/fonts"
        
    def _get_font_path(self, font_name: str) -> str:
        """
        Get the font path, checking custom fonts directory first, then Windows system fonts.
        
        Args:
            font_name: Name of the font
            
        Returns:
            Path to font file
        """
        font_name_lower = font_name.lower()
        
        # Check for custom font file in fonts directory
        if self.fonts_dir:
            for ext in ['.ttf', '.otf', '.TTF', '.OTF']:
                font_path = os.path.join(self.fonts_dir, f"{font_name}{ext}")
                if os.path.exists(font_path):
                    return font_path
        
        # Check Windows system fonts mapping
        if font_name_lower in self.WINDOWS_FONTS:
            system_path = self.WINDOWS_FONTS[font_name_lower]
            if os.path.exists(system_path):
                return system_path
                
        # Try common Windows font directory directly
        windows_font_path = f"C:/Windows/Fonts/{font_name_lower}.ttf"
        if os.path.exists(windows_font_path):
            return windows_font_path
            
        # Fallback to arial which is almost always available
        fallback = 'C:/Windows/Fonts/arial.ttf'
        if os.path.exists(fallback):
            return fallback
                    
        # Return original name as last resort
        return font_name
        
    def _parse_color(self, color: str) -> str:
        """
        Parse color string to MoviePy compatible format.
        
        Args:
            color: Color string (name, hex, or rgb)
            
        Returns:
            Color in MoviePy compatible format
        """
        if not color:
            return 'white'
            
        color = color.strip().lower()
        
        # Handle hex colors
        if color.startswith('#'):
            return color
            
        # Handle rgb format
        if color.startswith('rgb'):
            # Extract numbers from rgb(r,g,b)
            import re
            match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
                
        # Return as named color
        return color
        
    def _calculate_position(
        self, 
        position: Any, 
        text_width: int = 0, 
        text_height: int = 0
    ) -> Tuple[Any, Any]:
        """
        Calculate the actual position for text placement.
        
        Args:
            position: Position specification (string, tuple, or coordinates)
            text_width: Width of the text clip
            text_height: Height of the text clip
            
        Returns:
            Position tuple for MoviePy
        """
        if position == 'center':
            return 'center'
            
        if isinstance(position, tuple):
            if len(position) == 2:
                # Check if it's a named position tuple like ('center', 'bottom')
                if isinstance(position[0], str) and isinstance(position[1], str):
                    return position
                # Numeric coordinates
                return position
                
        # Default to bottom center for subtitles
        return ('center', self.video_height - 100)
        
    def create_text_clip(
        self,
        text: str,
        duration: float,
        start_time: float = 0.0,
        position: Any = 'center',
        style: str = 'default',
        fontsize: Optional[int] = None,
        color: Optional[str] = None,
        font: Optional[str] = None,
        stroke_color: Optional[str] = None,
        stroke_width: Optional[int] = None,
        bg_color: Optional[str] = None,
        opacity: float = 1.0,
        fade_duration: float = 0.0
    ):
        """
        Create a text clip with the specified parameters.
        
        Args:
            text: The text content to display
            duration: Duration to show the text
            start_time: When to start showing the text
            position: Position on screen
            style: Predefined style name
            fontsize: Override font size
            color: Override text color
            font: Override font
            stroke_color: Override stroke/outline color
            stroke_width: Override stroke width
            bg_color: Background color for text box
            opacity: Text opacity (0.0 to 1.0)
            fade_duration: Duration for fade in/out effects
            
        Returns:
            A TextClip configured with the specified parameters
        """
        # Get base style
        style_config = self.STYLES.get(style, self.STYLES['default']).copy()
        
        # Apply overrides
        if fontsize is not None:
            style_config['fontsize'] = fontsize
        if color is not None:
            style_config['color'] = self._parse_color(color)
        if font is not None:
            style_config['font'] = font
        if stroke_color is not None:
            style_config['stroke_color'] = self._parse_color(stroke_color)
        if stroke_width is not None:
            style_config['stroke_width'] = stroke_width
            
        # Get font path
        font_to_use = self._get_font_path(style_config.get('font', self.default_font))
        
        # Calculate max width for text wrapping (80% of video width)
        max_width = int(self.video_width * 0.8)
        
        try:
            # Create the text clip - use different parameters based on method
            method = style_config.get('method', 'label')
            
            # Build common parameters
            clip_params = {
                'text': text,
                'font': font_to_use,
                'font_size': style_config['fontsize'],
                'color': style_config['color'],
                'stroke_width': style_config.get('stroke_width', 0),
                'text_align': 'center'
            }
            
            # Add stroke color only if specified
            if style_config.get('stroke_color'):
                clip_params['stroke_color'] = style_config['stroke_color']
                
            # Add background color only if specified
            if bg_color:
                clip_params['bg_color'] = bg_color
            
            # For caption method, set size for text wrapping
            if method == 'caption':
                clip_params['method'] = 'caption'
                clip_params['size'] = (max_width, None)
            else:
                clip_params['method'] = 'label'
            
            clip = TextClip(**clip_params)
            
            # Set timing
            clip = clip.with_duration(duration).with_start(start_time)
            
            # Set position
            pos = self._calculate_position(position)
            clip = clip.with_position(pos)
            
            # Apply opacity
            if opacity < 1.0:
                clip = clip.with_opacity(opacity)
                
            # Apply fade effects
            if fade_duration > 0:
                clip = clip.with_effects([
                    CrossFadeIn(fade_duration),
                    CrossFadeOut(fade_duration)
                ])
                
            return clip
            
        except Exception as e:
            print(f"Warning: Failed to create text clip: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def create_text_clips_from_markers(
        self, 
        text_markers: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Create text clips from a list of parsed text markers.
        
        Args:
            text_markers: List of parsed text marker dictionaries
            
        Returns:
            List of TextClip objects
        """
        clips = []
        
        for marker in text_markers:
            text = marker.get('text', '')
            if not text:
                continue
                
            duration = marker.get('duration', 3.0)
            if duration == 'loop':
                duration = 10.0  # Default for looping text
            else:
                duration = float(duration)
                
            clip = self.create_text_clip(
                text=text,
                duration=duration,
                start_time=float(marker.get('timestamp', 0.0)),
                position=marker.get('position', ('center', 'bottom')),
                style=marker.get('style', 'default'),
                fontsize=marker.get('fontsize'),
                color=marker.get('color'),
                font=marker.get('font'),
                opacity=float(marker.get('opacity', 1.0)),
                fade_duration=0.3  # Default subtle fade
            )
            
            if clip:
                clips.append(clip)
                
        return clips
        
    def generate_subtitles_from_text(
        self,
        text: str,
        total_duration: float,
        words_per_subtitle: int = 8,
        position: Any = ('center', 'bottom'),
        style: str = 'subtitle'
    ) -> List[Any]:
        """
        Generate auto-timed subtitles from plain text.
        
        This creates evenly-timed subtitle clips based on word count.
        For more accurate timing, use with word-level timestamps from TTS.
        
        Args:
            text: The full text to convert to subtitles
            total_duration: Total duration to spread subtitles across
            words_per_subtitle: Approximate words per subtitle segment
            position: Position for all subtitles
            style: Style to apply to all subtitles
            
        Returns:
            List of TextClip objects for subtitles
        """
        # Split text into words
        words = text.split()
        if not words:
            return []
            
        # Group words into subtitle segments
        segments = []
        current_segment = []
        
        for word in words:
            current_segment.append(word)
            if len(current_segment) >= words_per_subtitle:
                segments.append(' '.join(current_segment))
                current_segment = []
                
        if current_segment:
            segments.append(' '.join(current_segment))
            
        if not segments:
            return []
            
        # Calculate timing
        duration_per_segment = total_duration / len(segments)
        
        # Create clips
        clips = []
        current_time = 0.0
        
        for segment in segments:
            clip = self.create_text_clip(
                text=segment,
                duration=duration_per_segment,
                start_time=current_time,
                position=position,
                style=style,
                fade_duration=0.2
            )
            
            if clip:
                clips.append(clip)
                
            current_time += duration_per_segment
            
        return clips


def add_text_overlays_to_video(
    video_clip,
    text_markers: List[Dict[str, Any]],
    subtitle_text: Optional[str] = None,
    video_duration: Optional[float] = None
):
    """
    Convenience function to add text overlays to an existing video clip.
    
    Args:
        video_clip: The base video clip
        text_markers: List of text markers from parser
        subtitle_text: Optional plain text for auto-generated subtitles
        video_duration: Duration of the video
        
    Returns:
        CompositeVideoClip with text overlays added
    """
    renderer = SubtitleRenderer(
        video_width=video_clip.w,
        video_height=video_clip.h
    )
    
    clips = [video_clip]
    
    # Add text marker clips
    text_clips = renderer.create_text_clips_from_markers(text_markers)
    clips.extend(text_clips)
    
    # Add auto-generated subtitles if text provided
    if subtitle_text and video_duration:
        subtitle_clips = renderer.generate_subtitles_from_text(
            subtitle_text,
            video_duration
        )
        clips.extend(subtitle_clips)
        
    if len(clips) > 1:
        return CompositeVideoClip(clips)
    return video_clip

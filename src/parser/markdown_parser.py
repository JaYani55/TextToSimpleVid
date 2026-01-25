import re
import os
from typing import Dict, List, Any, Optional

class MarkdownParser:
    """
    Parses markdown files with embedded media markers for video generation.
    
    Supports the following marker types:
    - [[video_duration: <seconds>]] - Total video duration
    - [[imagepath: <path>, timestamp: <t>, duration: <d|loop>, channel: <n>]]
    - [[videopath: <path>, timestamp: <t>, duration: <d|loop>, channel: <n>]]
    - [[audiopath: <path>, timestamp: <t>, duration: <d|loop>, channel: <n>]]
    - [[sfxpath: <path>, timestamp: <t>, channel: <n>]]
    - [[text: <content>, timestamp: <t>, duration: <d>, position: <pos>, style: <s>]]
    """
    
    # Supported media path keys and their library folder mappings
    MEDIA_PATH_KEYS = {
        'imagepath': 'images',
        'videopath': 'video',
        'audiopath': 'audio',
        'sfxpath': 'sfx'
    }
    
    def __init__(self, base_input_path: str = "input", library_path: str = "library"):
        self.base_input_path = base_input_path
        self.library_path = library_path
        self.video_duration: Optional[float] = None
        
    def _resolve_media_path(self, path: str, media_type: str) -> str:
        """
        Resolve media path by checking input folder first, then library folder.
        
        Args:
            path: The file path or name specified in the marker
            media_type: One of 'imagepath', 'videopath', 'audiopath', 'sfxpath'
            
        Returns:
            The resolved absolute or relative path to the media file
        """
        # Check if it's already an absolute path
        if os.path.isabs(path) and os.path.exists(path):
            return path
            
        # Check in input folder first
        input_path = os.path.join(self.base_input_path, path)
        if os.path.exists(input_path):
            return input_path
            
        # Check in library folder
        library_subfolder = self.MEDIA_PATH_KEYS.get(media_type, '')
        if library_subfolder:
            library_media_path = os.path.join(self.library_path, library_subfolder, path)
            if os.path.exists(library_media_path):
                return library_media_path
                
        # Return the input path as fallback (will fail later with appropriate error)
        return input_path
        
    def _parse_duration(self, value: str) -> Any:
        """
        Parse duration value which can be a number or 'loop'.
        
        Args:
            value: Duration string (e.g., "10", "5.5", "loop")
            
        Returns:
            Float for numeric duration, or the string "loop"
        """
        value = value.strip().lower()
        if value == 'loop':
            return 'loop'
        try:
            return float(value)
        except ValueError:
            print(f"Warning: Invalid duration value '{value}', defaulting to 3.0")
            return 3.0
            
    def _parse_position(self, value: str) -> tuple:
        """
        Parse position value for text/image placement.
        
        Args:
            value: Position string (e.g., "center", "top", "bottom", "100,200")
            
        Returns:
            Position tuple or string for MoviePy
        """
        value = value.strip().lower()
        
        # Named positions
        named_positions = {
            'center': 'center',
            'top': ('center', 'top'),
            'bottom': ('center', 'bottom'),
            'left': ('left', 'center'),
            'right': ('right', 'center'),
            'top-left': ('left', 'top'),
            'top-right': ('right', 'top'),
            'bottom-left': ('left', 'bottom'),
            'bottom-right': ('right', 'bottom')
        }
        
        if value in named_positions:
            return named_positions[value]
            
        # Try parsing as x,y coordinates
        if ',' in value:
            try:
                parts = value.split(',')
                return (int(parts[0].strip()), int(parts[1].strip()))
            except (ValueError, IndexError):
                pass
                
        return 'center'
        
    def parse_marker(self, marker_text: str) -> Dict[str, Any]:
        """
        Parse a single marker into a dictionary with normalized paths and values.
        
        Args:
            marker_text: The text content inside [[ ]] brackets
            
        Returns:
            Dictionary containing parsed marker properties
        """
        parts = marker_text.split(',')
        marker_dict: Dict[str, Any] = {}
        
        for part in parts:
            if ':' not in part:
                continue
                
            # Split only on first colon to allow colons in values
            colon_idx = part.find(':')
            key = part[:colon_idx].strip().lower()
            value = part[colon_idx + 1:].strip()
            
            # Handle video_duration specially (global setting)
            if key == 'video_duration':
                try:
                    self.video_duration = float(value)
                except ValueError:
                    print(f"Warning: Invalid video_duration value: {value}")
                continue
            
            # Handle media paths - resolve to actual file locations
            if key in self.MEDIA_PATH_KEYS:
                value = self._resolve_media_path(value, key)
                marker_dict[key] = value
                marker_dict['type'] = key.replace('path', '')  # 'image', 'video', 'audio', 'sfx'
                
            # Handle timing values
            elif key == 'timestamp':
                try:
                    marker_dict['timestamp'] = float(value)
                except ValueError:
                    print(f"Warning: Invalid timestamp value: {value}")
                    marker_dict['timestamp'] = 0.0
                    
            elif key == 'duration':
                marker_dict['duration'] = self._parse_duration(value)
                
            elif key == 'wait':
                # Legacy support for 'wait' as duration
                marker_dict['duration'] = self._parse_duration(value)
                
            # Handle channel (layer) specification
            elif key == 'channel':
                try:
                    marker_dict['channel'] = int(value)
                except ValueError:
                    print(f"Warning: Invalid channel value: {value}")
                    marker_dict['channel'] = 1
                    
            # Handle text content and styling
            elif key == 'text':
                marker_dict['text'] = value
                marker_dict['type'] = 'text'
                
            elif key == 'position':
                marker_dict['position'] = self._parse_position(value)
                
            elif key == 'style':
                marker_dict['style'] = value.strip()
                
            elif key == 'fontsize':
                try:
                    marker_dict['fontsize'] = int(value)
                except ValueError:
                    marker_dict['fontsize'] = 48
                    
            elif key == 'color':
                marker_dict['color'] = value.strip()
                
            elif key == 'effect':
                marker_dict['effect'] = value.strip()
                
            elif key == 'transition':
                marker_dict['transition'] = value.strip()
                
            elif key == 'opacity':
                try:
                    marker_dict['opacity'] = float(value)
                except ValueError:
                    marker_dict['opacity'] = 1.0
                    
            elif key == 'volume':
                try:
                    marker_dict['volume'] = float(value)
                except ValueError:
                    marker_dict['volume'] = 1.0
                    
            else:
                # Store any other key-value pairs
                marker_dict[key] = value
        
        # Set defaults for required fields
        if 'timestamp' not in marker_dict:
            marker_dict['timestamp'] = 0.0
            
        if 'duration' not in marker_dict:
            # SFX defaults to playing once (no duration needed)
            if marker_dict.get('type') == 'sfx':
                marker_dict['duration'] = None
            else:
                marker_dict['duration'] = 3.0
                
        if 'channel' not in marker_dict:
            marker_dict['channel'] = 1
            
        return marker_dict

    def parse(self, markdown_file: str) -> Dict[str, Any]:
        """
        Parse markdown file and return structured data for video generation.
        
        Args:
            markdown_file: Path to the markdown file to parse
            
        Returns:
            Dictionary containing:
            - text: Plain text content (for TTS)
            - markers: List of parsed media/text markers
            - video_duration: Explicit video duration if specified
            - video_markers: Markers for video/image clips
            - audio_markers: Markers for audio/sfx clips
            - text_markers: Markers for on-screen text
        """
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Reset video_duration for fresh parse
        self.video_duration = None
            
        # Extract markers within double square brackets
        marker_texts = re.findall(r'\[\[(.*?)\]\]', content, re.DOTALL)
        
        # Parse each marker
        all_markers: List[Dict[str, Any]] = []
        video_markers: List[Dict[str, Any]] = []
        audio_markers: List[Dict[str, Any]] = []
        text_markers: List[Dict[str, Any]] = []
        
        for m in marker_texts:
            marker = self.parse_marker(m)
            
            # Skip if it was just a video_duration setting
            if not marker.get('type') and not marker.get('text'):
                continue
                
            all_markers.append(marker)
            
            # Categorize by type
            marker_type = marker.get('type', '')
            if marker_type in ('image', 'video'):
                video_markers.append(marker)
            elif marker_type in ('audio', 'sfx'):
                audio_markers.append(marker)
            elif marker_type == 'text' or 'text' in marker:
                text_markers.append(marker)
        
        # Sort markers by timestamp within each category
        video_markers.sort(key=lambda x: (x.get('channel', 1), x.get('timestamp', 0)))
        audio_markers.sort(key=lambda x: (x.get('channel', 1), x.get('timestamp', 0)))
        text_markers.sort(key=lambda x: x.get('timestamp', 0))
        
        # Remove markers to get plain text for TTS
        plain_text = re.sub(r'\[\[.*?\]\]', '', content, flags=re.DOTALL).strip()
        # Clean up multiple newlines
        plain_text = re.sub(r'\n{3,}', '\n\n', plain_text)
        
        return {
            'text': plain_text,
            'markers': all_markers,
            'video_markers': video_markers,
            'audio_markers': audio_markers,
            'text_markers': text_markers,
            'video_duration': self.video_duration
        }
import re
import os

class MarkdownParser:
    def __init__(self, base_input_path="input"):
        self.base_input_path = base_input_path
        self.video_duration = None
        
    def parse_marker(self, marker_text):
        """Parse a single marker into a dictionary with normalized paths"""
        parts = marker_text.split(',')
        marker_dict = {}
        
        for part in parts:
            if ':' not in part:
                continue
            key, value = part.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Handle special cases
            if key in ['imagepath', 'videopath']:
                # Normalize file paths
                value = os.path.join(self.base_input_path, value)
            elif key in ['wait', 'duration', 'timestamp', 'video_duration']:
                # Convert time values to float
                try:
                    value = float(value)
                except ValueError:
                    print(f"Warning: Invalid time value for {key}: {value}")
                    value = 3.0
            
            marker_dict[key] = value
            
            # Handle video_duration specially
            if key == 'video_duration':
                self.video_duration = value
                continue
            
        # Set default values if not specified
        if 'timestamp' not in marker_dict:
            marker_dict['timestamp'] = 0.0
            
        if 'wait' in marker_dict and 'duration' not in marker_dict:
            marker_dict['duration'] = marker_dict['wait']
        elif 'duration' not in marker_dict:
            marker_dict['duration'] = 3.0
            
        return marker_dict

    def parse(self, markdown_file):
        """Parse markdown file and return plain text, media markers and video duration"""
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract markers within double square brackets
        marker_texts = re.findall(r'\[\[(.*?)\]\]', content)
        
        # Parse each marker
        markers = []
        for m in marker_texts:
            marker = self.parse_marker(m)
            # Only add media markers to the list
            if 'imagepath' in marker or 'videopath' in marker:
                markers.append(marker)
        
        # Sort markers by timestamp
        markers.sort(key=lambda x: x['timestamp'])
        
        # Remove markers to get plain text
        plain_text = re.sub(r'\[\[.*?\]\]', '', content).strip()
        
        return {
            'text': plain_text,
            'markers': markers,
            'video_duration': self.video_duration
        }
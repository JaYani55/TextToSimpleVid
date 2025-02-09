import os
from pathlib import Path

class FontManager:
    @staticmethod
    def get_default_font():
        """Get a default system font that works with MoviePy's TextClip."""
        # Try Windows fonts first
        windows_fonts = [
            "C:/Windows/Fonts/Arial.ttf",
            "C:/Windows/Fonts/Calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf"
        ]
        
        for font in windows_fonts:
            if os.path.exists(font):
                return font
                
        # Fallback to a basic font name that should work on most systems
        return "Arial"

    @staticmethod
    def validate_font(font_path):
        """Validate that the font file exists and return its resolved path."""
        path = Path(font_path).resolve()
        if not path.exists():
            raise ValueError(f"Required font file not found: {font_path}")
        return str(path)

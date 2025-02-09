import os

class MediaValidator:
    @staticmethod
    def validate_input_file(input_path):
        """Validate markdown input file."""
        if not os.path.exists(input_path):
            raise ValueError(f"Input file not found: {input_path}")
        if not input_path.endswith('.md'):
            raise ValueError(f"Input file must be a Markdown file: {input_path}")

    @staticmethod
    def validate_output_path(output_path):
        """Validate video output path."""
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            raise ValueError(f"Output directory does not exist: {output_dir}")
        if not output_path.endswith(('.mp4', '.avi', '.mov')):
            raise ValueError("Output file must have a valid video extension (.mp4, .avi, .mov)")

    @staticmethod
    def validate_media_file(filepath, media_type):
        """Validate that media file exists and is of correct type."""
        if not os.path.exists(filepath):
            raise ValueError(f"{media_type} file not found: {filepath}")
        
        if media_type == "image":
            valid_extensions = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
            if not filepath.lower().endswith(valid_extensions):
                raise ValueError(f"Invalid image format for {filepath}. Must be one of {valid_extensions}")
        elif media_type == "video":
            valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
            if not filepath.lower().endswith(valid_extensions):
                raise ValueError(f"Invalid video format for {filepath}. Must be one of {valid_extensions}")

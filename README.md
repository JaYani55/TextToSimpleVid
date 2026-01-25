# Text-to-Simple-Video Converter

## Overview

This project converts markdown text files into narrated videos with multi-channel audio/video support. It uses Kokoro TTS (Text-to-Speech) to generate natural-sounding narration and allows you to layer images, video clips, audio tracks, and text overlays through simple markdown syntax.

## Features

- **Text-to-Speech** narration using Kokoro ONNX
- **Multi-channel video composition** - Layer multiple video/image tracks
- **Multi-channel audio mixing** - Background music, SFX, and TTS combined
- **Loop support** - Loop video/audio clips for any duration
- **Text overlays** - Titles, subtitles, and custom text with styling
- **Media library** - Organize reusable assets in the library folder
- **Flexible timing** - Precise control with timestamps and durations

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/TextToSimpleVid.git
   cd TextToSimpleVid
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Kokoro model files:**
   Create the models directory:
   ```bash
   mkdir src\tts\models
   ```
   
   Download the required model files:
   ```bash
   # Download ONNX model
   curl -L -o src/tts/models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx

   # Download voices file
   curl -L -o src/tts/models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
   ```

## Usage

1. **Create a markdown file with media markers:**
   ```markdown
   [[video_duration: 120]]

   [[audiopath: background_music.mp3, timestamp: 0, duration: loop, channel: 3, volume: 0.3]]
   [[videopath: background.mp4, timestamp: 0, duration: loop, channel: 3]]

   Welcome to our demonstration.

   [[text: Welcome!, timestamp: 0, duration: 5, position: center, style: title]]

   Here's an image overlay:
   [[imagepath: logo.png, timestamp: 5, duration: 10, channel: 1]]

   And a sound effect:
   [[sfxpath: whoosh.wav, timestamp: 5]]

   Check out this video clip:
   [[videopath: demo.mp4, timestamp: 15, duration: 20, channel: 2, transition: fade]]
   ```

2. **Run the converter:**
   ```bash
   python src/main.py --md input/sample.md --output output
   ```

3. **Additional options:**
   ```bash
   # Skip TTS generation
   python src/main.py --md input/sample.md --no-tts

   # Generate with subtitles
   python src/main.py --md input/sample.md --subtitles

   # Custom video dimensions
   python src/main.py --md input/sample.md --width 1280 --height 720

   # Use custom library path
   python src/main.py --md input/sample.md --library path/to/library
   ```

## Markdown Syntax

### Global Settings
```markdown
[[video_duration: 120]]  # Set explicit video duration in seconds
```

### Video/Image Markers
```markdown
# Basic image
[[imagepath: image.jpg, timestamp: 0, duration: 5]]

# Image with channel and opacity
[[imagepath: overlay.png, timestamp: 10, duration: 15, channel: 2, opacity: 0.8]]

# Looping video background
[[videopath: background.mp4, timestamp: 0, duration: loop, channel: 1]]

# Video with transition
[[videopath: clip.mp4, timestamp: 20, duration: 10, transition: fade]]
```

### Audio Markers
```markdown
# Background music (looping)
[[audiopath: music.mp3, timestamp: 0, duration: loop, volume: 0.5]]

# Sound effect (plays once)
[[sfxpath: explosion.wav, timestamp: 15]]

# Audio with specific duration
[[audiopath: ambient.mp3, timestamp: 0, duration: 60, channel: 2]]
```

### Text Overlays
```markdown
# Title text
[[text: Welcome to the Show, timestamp: 0, duration: 5, style: title]]

# Positioned subtitle
[[text: Episode 1, timestamp: 5, duration: 3, position: bottom, style: subtitle]]

# Custom styled text
[[text: Important!, timestamp: 10, duration: 5, position: top, fontsize: 64, color: red]]
```

### Marker Properties Reference

| Property | Values | Description |
|----------|--------|-------------|
| `timestamp` | seconds (float) | When to start showing the element |
| `duration` | seconds or `loop` | How long to show, or loop until video ends |
| `channel` | integer | Layer order (higher = on top) |
| `opacity` | 0.0 - 1.0 | Transparency level |
| `volume` | 0.0 - 1.0 | Audio volume |
| `position` | center, top, bottom, left, right, x,y | Placement on screen |
| `style` | title, subtitle, caption, heading | Predefined text styles |
| `transition` | fade | Transition effect |
| `color` | name or #hex | Text/element color |
| `fontsize` | integer | Text size in pixels |

## Directory Structure

```
TextToSimpleVid/
├── src/
│   ├── main.py              # Main orchestrator
│   ├── parser/              # Markdown parsing
│   ├── media/               # Video/image processing
│   ├── audio/               # Audio mixing
│   ├── subtitles/           # Text rendering
│   ├── tts/                 # Text-to-speech
│   │   └── models/          # Kokoro model files
│   └── utils/               # Utilities
├── library/                 # Reusable media assets
│   ├── video/               # Video clips
│   ├── audio/               # Music, ambient sounds
│   ├── images/              # Images, logos
│   └── sfx/                 # Sound effects
├── input/                   # Your markdown and project files
├── output/                  # Generated videos
└── config/                  # Configuration files
```

## Media Library

Place reusable assets in the `library/` folder. The parser will automatically search for files in:
1. The `input/` folder (project-specific files)
2. The `library/` folder (reusable assets by type)

## Multi-Channel System

Channels determine the layering order:
- **Video/Images**: Higher channel numbers render on top
- **Audio**: All channels are mixed together
- Use channel 3+ for background elements
- Use channel 1-2 for foreground overlays

## Requirements

- Python 3.8 or higher
- FFmpeg (for video processing)
- Kokoro ONNX model files
- MoviePy dependencies

## License

This project is licensed under the MIT License - see the LICENSE file for details.
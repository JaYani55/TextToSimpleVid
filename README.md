# Text-to-Simple-Video Converter

## Overview

This project converts markdown text files into narrated videos. It uses Kokoro TTS (Text-to-Speech) to generate natural-sounding narration and allows you to synchronize images and video clips with the spoken content through simple markdown syntax.

## Features

- Text-to-Speech narration using Kokoro ONNX
- Image and video integration with timing control
- Automatic duration scaling to match narration
- Simple markdown syntax for media placement

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
   [[video_duration: 15]]

   Welcome to our demonstration.

   Here's an image:
   [[imagepath: image.jpg, timestamp: 0, duration: 5]]

   And a video clip:
   [[videopath: video.mp4, timestamp: 5, duration: 10]]
   ```

2. **Run the converter:**
   ```bash
   python src/main.py --md input/sample.md --output output
   ```

## Markdown Syntax

- **Set video duration:**
  ```markdown
  [[video_duration: seconds]]
  ```

- **Add image:**
  ```markdown
  [[imagepath: path/to/image.jpg, timestamp: seconds, duration: seconds]]
  ```

- **Add video:**
  ```markdown
  [[videopath: path/to/video.mp4, timestamp: seconds, duration: seconds]]
  ```

## Directory Structure

```
TextToSimpleVid/
├── src/
│   ├── tts/
│   │   ├── models/          # Place Kokoro model files here
│   │   │   ├── kokoro-v1.0.onnx
│   │   │   └── voices-v1.0.bin
│   │   └── kokoro_tts.py
│   └── main.py
├── input/                   # Your markdown and media files
└── output/                  # Generated videos
```

## Requirements

- Python 3.8 or higher
- FFmpeg (for video processing)
- Kokoro ONNX model files
- MoviePy dependencies

## License

This project is licensed under the MIT License - see the LICENSE file for details.
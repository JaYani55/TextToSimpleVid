# Text-to-Video System v1.0

## Overview

Text-to-Video System v1.0 converts Markdown files into dynamic video content. It generates natural-sounding narration using the ElevenLabs API, visualized through an audio-reactive visualizer. Users can embed images, videos, and background audio through special Markdown markers, applying configurable effects such as edge detection or rotoscoping. The original text is also displayed as synchronized subtitles.

## Features

- **Text-to-Speech (TTS)**: Converts text into high-quality speech.
- **Audio Visualizer**: Dynamically reacts to generated speech.
- **Media Integration**: Supports images, videos, and background audio with configurable effects.
- **Subtitles**: Automatically syncs the original text to the narration.
- **Extensible & Modular**: Easily swap or extend components such as TTS providers and visual effects.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your_username/text-to-video.git
   ```
2. **Install dependencies:**
   ```bash
   cd text-to-video
   pip install -r requirements.txt
   ```
3. **Configure settings:**  
   Edit the configuration files in the `config/` directory (e.g., set API keys and effect parameters).

## Usage

Run the main script to generate a video from a Markdown file:
```bash
python src/main.py --input input/sample.md --output output/final_video.mp4
```

### Markdown Formatting for Media

- **Images:** `[[imagepath: path/to/image.svg, duration: 5, effect: edge]]`
- **Videos:** `[[videopath: path/to/video.mp4, transition: fade]]`
- **Audio:** `[[audio: path/to/background.mp3, volume: 0.8]]`

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
Below is the revised documentation tutorial with an added section on encoding and ensuring even dimensions:

---

# MoviePy Comprehensive Tutorial

MoviePy is a Python library that lets you programmatically edit videos. It uses FFmpeg for media processing and NumPy for frame‐by‐frame manipulations. In MoviePy v2 and later, all imports are done directly from the top-level package. This guide covers the core classes, chainable transformation methods, compositing techniques, and encoding options—including how to ensure that your video dimensions are compatible with your chosen encoder.

---

## 1. Importing the Library

All core classes and functions are available directly from MoviePy. For example:

```python
from moviepy import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
```

This unified import approach ensures a clean, consistent API.

---

## 2. Loading and Creating Clips

Clips are the building blocks of MoviePy. They represent media elements over time.

### Video and Audio Clips

- **VideoFileClip:** Loads a video (with audio).  
  ```python
  video_clip = VideoFileClip("input/sample_video.mp4")
  ```

- **AudioFileClip:** Loads an audio file or extracts audio from a video.
  ```python
  audio_clip = AudioFileClip("input/sample_audio.mp3")
  ```

### Image and Text Clips

- **ImageClip:** Creates a video clip from an image or a NumPy array.  
  ```python
  image_clip = ImageClip("input/placeholder_image.jpg", duration=10)
  ```

- **TextClip:** Generates an image clip from text with customizable fonts, sizes, and colors.
  ```python
  title_clip = TextClip("Welcome to MoviePy", font="Arial.ttf",
                          font_size=70, color="white").with_duration(5).with_position("center")
  ```

---

## 3. Transformations with Chainable Methods

MoviePy methods that change clip properties all start with `with_` and return a modified copy. This functional style makes it easy to build transformation pipelines.

### Examples of Transformation Methods

- **Subclipping:** Extract a portion of a clip.
  ```python
  clip_segment = video_clip.subclipped(10, 20)
  ```

- **Duration and Timing:** Specify when a clip should start or how long it should last.
  ```python
  timed_clip = clip_segment.with_duration(10).with_start(5)
  ```

- **Audio Volume Scaling:** Adjust audio volume.
  ```python
  quieter_clip = video_clip.with_volume_scaled(0.8)
  ```

- **Resizing and Cropping:** Change clip dimensions.
  ```python
  resized_clip = image_clip.resized(width=640)  # Resizes while keeping aspect ratio
  cropped_clip = video_clip.cropped(x1=50, y1=50, x2=590, y2=430)
  ```

- **Applying Effects:** Use built-in effects from the `vfx` (video effects) or `afx` (audio effects) modules.
  ```python
  from moviepy import vfx, afx

  effected_clip = video_clip.with_effects([
      vfx.FadeIn(1),
      vfx.FadeOut(1),
      afx.AudioFadeIn(1),
      afx.AudioFadeOut(1)
  ])
  ```

- **Custom Frame Transformation:** Modify frames using your own function.
  ```python
  def invert_colors(frame):
      # Swap the red and blue channels of the frame.
      return frame[:, :, [2, 1, 0]]

  transformed_clip = video_clip.image_transform(invert_colors)
  ```

---

## 4. Compositing and Sequencing Clips

MoviePy makes it easy to combine multiple clips either by overlaying them or by placing them sequentially.

### Overlaying Clips with CompositeVideoClip

To overlay clips (for example, placing text or images over a video), use `CompositeVideoClip`:
```python
background = VideoFileClip("input/background.mp4")
overlay = TextClip("Overlay Text", font="Arial.ttf", font_size=50, color="yellow") \
          .with_duration(background.duration).with_position("center")

final_composite = CompositeVideoClip([background, overlay])
```

### Concatenating Clips Sequentially

For sequential playback—showing one clip after another—use `concatenate_videoclips`:
```python
# Show an image for 10 seconds then play a video.
image_clip = ImageClip("input/placeholder_image.jpg", duration=10)
video_clip = VideoFileClip("input/placeholder_video.mp4")

final_sequence = concatenate_videoclips([image_clip, video_clip])
```

---

## 5. Rendering, Encoding, and Ensuring Compatibility

Once your clips are assembled, render the final video using the `write_videofile` method. MoviePy uses FFmpeg under the hood, and you can control encoding parameters by passing options such as `codec` (for video) and `audio_codec` (for audio).

### Specifying Encoding Options

You can explicitly set:
- **Video codec:** For example, `"libx264"` is widely supported.
- **Audio codec:** For example, `"aac"` is common for MP4 files.
- **Additional FFmpeg parameters:** For example, setting the pixel format to `"yuv420p"` improves compatibility with many players.

Example:
```python
final_clip.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac",
                           ffmpeg_params=["-pix_fmt", "yuv420p"],
                           temp_audiofile="temp-audio.m4a", remove_temp=True)
```

### Ensuring Even Dimensions

Many encoders (such as libx264) require that the width and height of the video are divisible by 2. If your clip dimensions are odd, you may encounter errors such as "height not divisible by 2." To avoid this, adjust the dimensions before writing the file:

```python
# Calculate even dimensions
even_width = final_clip.w - (final_clip.w % 2)
even_height = final_clip.h - (final_clip.h % 2)
final_clip = final_clip.resized((even_width, even_height))
```

Adding these steps ensures that the output video adheres to codec requirements.

---

## 6. Putting It All Together: A Test Script Example

Below is an example script that creates a video by first showing an image for 10 seconds and then playing a video. It includes steps to force even dimensions and to set encoding options for compatibility.

```python
from moviepy import ImageClip, VideoFileClip, concatenate_videoclips

# Create an image clip that lasts 10 seconds.
image_clip = ImageClip("input/placeholder_image.jpg", duration=10)

# Load the video clip.
video_clip = VideoFileClip("input/placeholder_video.mp4")

# Concatenate the image clip and the video clip.
final_clip = concatenate_videoclips([image_clip, video_clip])

# Ensure the width and height are even numbers (required by libx264).
even_width = final_clip.w - (final_clip.w % 2)
even_height = final_clip.h - (final_clip.h % 2)
final_clip = final_clip.resized((even_width, even_height))

# Render the final video to an MP4 file with explicit encoding settings.
final_clip.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac",
                           ffmpeg_params=["-pix_fmt", "yuv420p"],
                           temp_audiofile="temp-audio.m4a", remove_temp=True)
```

This script demonstrates the key syntax structures:
- **Unified Imports**
- **Loading Different Clip Types**
- **Using Chainable Transformations**
- **Compositing and Concatenation**
- **Enforcing Even Dimensions and Specifying Encoding Options**

---

## 7. Conclusion

In MoviePy:
- **Imports:** Use the unified, top-level syntax.
- **Clips:** Work with VideoFileClip, ImageClip, TextClip, etc., to represent media elements over time.
- **Chainable Methods:** Transform clips with methods like `with_duration`, `with_start`, and `with_effects`.
- **Compositing:** Overlay clips with CompositeVideoClip or concatenate them sequentially.
- **Encoding:** Export videos with controlled encoding by specifying codecs and ensuring even dimensions (a requirement for certain encoders such as libx264).

By understanding these core concepts and syntax structures, you’re well on your way to leveraging MoviePy for a wide range of video editing tasks. For further details, consult the official [MoviePy documentation](https://zulko.github.io/moviepy/).
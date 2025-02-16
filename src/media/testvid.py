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
final_clip.write_videofile(
    "output.mp4",
    fps=24,
    codec="libx264",
    audio_codec="aac",
    ffmpeg_params=["-pix_fmt", "yuv420p"],
    temp_audiofile="temp-audio.m4a",
    remove_temp=True
)

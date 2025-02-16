# moviepy API Reference
Imports everything that you need from the MoviePy submodules so that every thing can be directly imported with from moviepy import *.

Modules

moviepy.Clip

Implements the central object of MoviePy, the Clip, and all the methods that are common to the two subclasses of Clip, VideoClip and AudioClip.

moviepy.Effect()

Base abstract class for all effects in MoviePy.

moviepy.audio

Everything about audio manipulation.

moviepy.config

Third party programs configuration for MoviePy.

moviepy.decorators

Decorators used by moviepy.

moviepy.tools

Misc.

moviepy.video

Everything about video manipulation.

moviepy.Clip.Clip
class moviepy.Clip.Clip[source]
Base class of all clips (VideoClips and AudioClips).

start
When the clip is included in a composition, time of the composition at which the clip starts playing (in seconds).

Type
:
float

end
When the clip is included in a composition, time of the composition at which the clip stops playing (in seconds).

Type
:
float

duration
Duration of the clip (in seconds). Some clips are infinite, in this case their duration will be None.

Type
:
float

close()[source]
Release any resources that are in use.

copy()[source]
Allows the usage of .copy() in clips as chained methods invocation.

get_frame(t)[source]
Gets a numpy array representing the RGB picture of the clip, or (mono or stereo) value for a sound clip, at time t.

Parameters
:
t (float or tuple or str) – Moment of the clip whose frame will be returned.

is_playing(t)[source]
If t is a time, returns true if t is between the start and the end of the clip. t can be expressed in seconds (15.35), in (min, sec), in (hour, min, sec), or as a string: ‘01:03:05.35’. If t is a numpy array, returns False if none of the t is in the clip, else returns a vector [b_1, b_2, b_3…] where b_i is true if tti is in the clip.

iter_frames(fps=None, with_times=False, logger=None, dtype=None)[source]
Iterates over all the frames of the clip.

Returns each frame of the clip as a HxWxN Numpy array, where N=1 for mask clips and N=3 for RGB clips.

This function is not really meant for video editing. It provides an easy way to do frame-by-frame treatment of a video, for fields like science, computer vision…

Parameters
:
fps (int, optional) – Frames per second for clip iteration. Is optional if the clip already has a fps attribute.

with_times (bool, optional) – Ff True yield tuples of (t, frame) where t is the current time for the frame, otherwise only a frame object.

logger (str, optional) – Either "bar" for progress bar or None or any Proglog logger.

dtype (type, optional) – Type to cast Numpy array frames. Use dtype="uint8" when using the pictures to write video, images..

Examples

# prints the maximum of red that is contained
# on the first line of each frame of the clip.
from moviepy import VideoFileClip
myclip = VideoFileClip('myvideo.mp4')
print([frame[0,:,0].max()
      for frame in myclip.iter_frames()])
subclipped(start_time=0, end_time=None)[source]
Returns a clip playing the content of the current clip between times start_time and end_time, which can be expressed in seconds (15.35), in (min, sec), in (hour, min, sec), or as a string: ‘01:03:05.35’.

The mask and audio of the resulting subclip will be subclips of mask and audio the original clip, if they exist.

It’s equivalent to slice the clip as a sequence, like clip[t_start:t_end].

Parameters
:
start_time (float or tuple or str, optional) – Moment that will be chosen as the beginning of the produced clip. If is negative, it is reset to clip.duration + start_time.

end_time (float or tuple or str, optional) –

Moment that will be chosen as the end of the produced clip. If not provided, it is assumed to be the duration of the clip (potentially infinite). If is negative, it is reset to clip.duration + end_time. For instance:

# cut the last two seconds of the clip:
new_clip = clip.subclipped(0, -2)
If end_time is provided or if the clip has a duration attribute, the duration of the returned clip is set automatically.

time_transform(time_func, apply_to=None, keep_duration=False)[source]
Returns a Clip instance playing the content of the current clip but with a modified timeline, time t being replaced by the return of time_func(t).

Parameters
:
time_func (function) – A function t -> new_t.

apply_to ({"mask", "audio", ["mask", "audio"]}, optional) – Can be either ‘mask’, or ‘audio’, or [‘mask’,’audio’]. Specifies if the filter transform should also be applied to the audio or the mask of the clip, if any.

keep_duration (bool, optional) – False (default) if the transformation modifies the duration of the clip.

Examples

# plays the clip (and its mask and sound) twice faster
new_clip = clip.time_transform(lambda t: 2*t, apply_to=['mask', 'audio'])

# plays the clip starting at t=3, and backwards:
new_clip = clip.time_transform(lambda t: 3-t)
transform(func, apply_to=None, keep_duration=True)[source]
General processing of a clip.

Returns a new Clip whose frames are a transformation (through function func) of the frames of the current clip.

Parameters
:
func (function) – A function with signature (gf,t -> frame) where gf will represent the current clip’s get_frame method, i.e. gf is a function (t->image). Parameter t is a time in seconds, frame is a picture (=Numpy array) which will be returned by the transformed clip (see examples below).

apply_to ({"mask", "audio", ["mask", "audio"]}, optional) – Can be either 'mask', or 'audio', or ['mask','audio']. Specifies if the filter should also be applied to the audio or the mask of the clip, if any.

keep_duration (bool, optional) – Set to True if the transformation does not change the duration of the clip.

Examples

In the following new_clip a 100 pixels-high clip whose video content scrolls from the top to the bottom of the frames of clip at 50 pixels per second.

filter = lambda get_frame,t : get_frame(t)[int(t):int(t)+50, :]
new_clip = clip.transform(filter, apply_to='mask')
with_duration(duration, change_end=True)[source]
Returns a copy of the clip, with the duration attribute set to t, which can be expressed in seconds (15.35), in (min, sec), in (hour, min, sec), or as a string: ‘01:03:05.35’. Also sets the duration of the mask and audio, if any, of the returned clip.

If change_end is False, the start attribute of the clip will be modified in function of the duration and the preset end of the clip.

Parameters
:
duration (float) – New duration attribute value for the clip.

change_end (bool, optional) – If True, the end attribute value of the clip will be adjusted accordingly to the new duration using clip.start + duration.

with_effects(effects: List[Effect])[source]
Return a copy of the current clip with the effects applied

new_clip = clip.with_effects([vfx.Resize(0.2, method="bilinear")])
You can also pass multiple effect as a list

clip.with_effects([afx.VolumeX(0.5), vfx.Resize(0.3), vfx.Mirrorx()])
with_end(t)[source]
Returns a copy of the clip, with the end attribute set to t, which can be expressed in seconds (15.35), in (min, sec), in (hour, min, sec), or as a string: ‘01:03:05.35’. Also sets the duration of the mask and audio, if any, of the returned clip.

note::
The start and end attribute of a clip define when a clip will start playing when used in a composite video clip, not the start time of the clip itself.

i.e: with_start(10) mean the clip will still start at his first frame, but if used in a composite video clip it will only start to show at 10 seconds.

Parameters
:
t (float or tuple or str) – New end attribute value for the clip.

with_fps(fps, change_duration=False)[source]
Returns a copy of the clip with a new default fps for functions like write_videofile, iterframe, etc.

Parameters
:
fps (int) – New fps attribute value for the clip.

change_duration (bool, optional) – If change_duration=True, then the video speed will change to match the new fps (conserving all frames 1:1). For example, if the fps is halved in this mode, the duration will be doubled.

with_is_mask(is_mask)[source]
Says whether the clip is a mask or not.

Parameters
:
is_mask (bool) – New is_mask attribute value for the clip.

with_memoize(memoize)[source]
Sets whether the clip should keep the last frame read in memory.

Parameters
:
memoize (bool) – Indicates if the clip should keep the last frame read in memory.

with_section_cut_out(start_time, end_time)[source]
Returns a clip playing the content of the current clip but skips the extract between start_time and end_time, which can be expressed in seconds (15.35), in (min, sec), in (hour, min, sec), or as a string: ‘01:03:05.35’.

If the original clip has a duration attribute set, the duration of the returned clip is automatically computed as `` duration - (end_time - start_time)``.

The resulting clip’s audio and mask will also be cutout if they exist.

Parameters
:
start_time (float or tuple or str) – Moment from which frames will be ignored in the resulting output.

end_time (float or tuple or str) – Moment until which frames will be ignored in the resulting output.

with_speed_scaled(factor: float = None, final_duration: float = None)[source]
Returns a clip playing the current clip but at a speed multiplied by factor. For info on the parameters, please see vfx.MultiplySpeed.

with_start(t, change_end=True)[source]
Returns a copy of the clip, with the start attribute set to t, which can be expressed in seconds (15.35), in (min, sec), in (hour, min, sec), or as a string: ‘01:03:05.35’.

These changes are also applied to the audio and mask clips of the current clip, if they exist.

note::
The start and end attribute of a clip define when a clip will start playing when used in a composite video clip, not the start time of the clip itself.

i.e: with_start(10) mean the clip will still start at his first frame, but if used in a composite video clip it will only start to show at 10 seconds.

Parameters
:
t (float or tuple or str) – New start attribute value for the clip.

change_end (bool optional) – Indicates if the end attribute value must be changed accordingly, if possible. If change_end=True and the clip has a duration attribute, the end attribute of the clip will be updated to start + duration. If change_end=False and the clip has a end attribute, the duration attribute of the clip will be updated to end - start.

with_updated_frame_function(frame_function)[source]
Sets a frame_function attribute for the clip. Useful for setting arbitrary/complicated videoclips.

Parameters
:
frame_function (function) – New frame creator function for the clip.

with_volume_scaled(factor: float, start_time=None, end_time=None)[source]
Returns a new clip with audio volume multiplied by the value factor. For info on the parameters, please see afx.MultiplyVolume

moviepy.Effect
Defines the base class for all effects in MoviePy.

class moviepy.Effect.Effect[source]
Base abstract class for all effects in MoviePy. Any new effect have to extend this base class.

abstract apply(clip: Clip) → Clip[source]
Apply the current effect on a clip

Parameters
:
clip – The target clip to apply the effect on. (Internally, MoviePy will always pass a copy of the original clip)

copy()[source]
Return a shallow copy of an Effect.

You must always copy an Effect before applying, because some of them will modify their own attributes when applied. For example, setting a previously unset property by using target clip property.

If we was to use the original effect, calling the same effect multiple times could lead to different properties, and different results for equivalent clips.

By using copy, we ensure we can use the same effect object multiple times while maintaining the same behavior/result.

In a way, copy makes the effect himself being kind of idempotent.

moviepy.audio.AudioClip
Implements AudioClip (base class for audio clips) and its main subclasses:

Audio clips: AudioClip, AudioFileClip, AudioArrayClip

Composition: CompositeAudioClip

Classes

AudioArrayClip(array, fps)

An audio clip made from a sound array.

AudioClip([frame_function, duration, fps])

Base class for audio clips.

CompositeAudioClip(clips)

Clip made by composing several AudioClips.

Functions

concatenate_audioclips(clips)

Concatenates one AudioClip after another, in the order that are passed to clips parameter.

moviepy.audio.AudioClip.AudioArrayClip
class moviepy.audio.AudioClip.AudioArrayClip(array, fps)[source]
An audio clip made from a sound array.

Parameters
:
array – A Numpy array representing the sound, of size Nx1 for mono, Nx2 for stereo.

fps – Frames per second : speed at which the sound is supposed to be played.

moviepy.audio.AudioClip.AudioClip
class moviepy.audio.AudioClip.AudioClip(frame_function=None, duration=None, fps=None)[source]
Base class for audio clips.

See AudioFileClip and CompositeAudioClip for usable classes.

An AudioClip is a Clip with a frame_function attribute of the form `` t -> [ f_t ]`` for mono sound and t-> [ f1_t, f2_t ] for stereo sound (the arrays are Numpy arrays). The f_t are floats between -1 and 1. These bounds can be trespassed without problems (the program will put the sound back into the bounds at conversion time, without much impact).

Parameters
:
frame_function – A function t-> frame at time t. The frame does not mean much for a sound, it is just a float. What ‘makes’ the sound are the variations of that float in the time.

duration – Duration of the clip (in seconds). Some clips are infinite, in this case their duration will be None.

nchannels – Number of channels (one or two for mono or stereo).

Examples

# Plays the note A in mono (a sine wave of frequency 440 Hz)
import numpy as np
frame_function = lambda t: np.sin(440 * 2 * np.pi * t)
clip = AudioClip(frame_function, duration=5, fps=44100)
clip.preview()

# Plays the note A in stereo (two sine waves of frequencies 440 and 880 Hz)
frame_function = lambda t: np.array([
    np.sin(440 * 2 * np.pi * t),
    np.sin(880 * 2 * np.pi * t)
]).T.copy(order="C")
clip = AudioClip(frame_function, duration=3, fps=44100)
clip.preview()
audiopreview(fps=None, buffersize=2000, nbytes=2, audio_flag=None, video_flag=None)[source]
Preview an AudioClip using ffplay

Parameters
:
fps – Frame rate of the sound. 44100 gives top quality, but may cause problems if your computer is not fast enough and your clip is complicated. If the sound jumps during the preview, lower it (11025 is still fine, 5000 is tolerable).

buffersize – The sound is not generated all at once, but rather made by bunches of frames (chunks). buffersize is the size of such a chunk. Try varying it if you meet audio problems (but you shouldn’t have to).

nbytes – Number of bytes to encode the sound: 1 for 8bit sound, 2 for 16bit, 4 for 32bit sound. 2 bytes is fine.

audio_flag – Instances of class threading events that are used to synchronize video and audio during VideoClip.preview().

video_flag – Instances of class threading events that are used to synchronize video and audio during VideoClip.preview().

display_in_notebook(filetype=None, maxduration=60, t=None, fps=None, rd_kwargs=None, center=True, **html_kwargs)
Displays clip content in an Jupyter Notebook.

Remarks: If your browser doesn’t support HTML5, this should warn you. If nothing is displayed, maybe your file or filename is wrong. Important: The media will be physically embedded in the notebook.

Parameters
:
clip (moviepy.Clip.Clip) – Either the name of a file, or a clip to preview. The clip will actually be written to a file and embedded as if a filename was provided.

filetype (str, optional) – One of "video", "image" or "audio". If None is given, it is determined based on the extension of filename, but this can bug.

maxduration (float, optional) – An error will be raised if the clip’s duration is more than the indicated value (in seconds), to avoid spoiling the browser’s cache and the RAM.

t (float, optional) – If not None, only the frame at time t will be displayed in the notebook, instead of a video of the clip.

fps (int, optional) – Enables to specify an fps, as required for clips whose fps is unknown.

rd_kwargs (dict, optional) – Keyword arguments for the rendering, like dict(fps=15, bitrate="50k"). Allow you to give some options to the render process. You can, for example, disable the logger bar passing dict(logger=None).

center (bool, optional) – If true (default), the content will be wrapped in a <div align=middle> HTML container, so the content will be displayed at the center.

kwargs – Allow you to give some options, like width=260, etc. When editing looping gifs, a good choice is loop=1, autoplay=1.

Examples

from moviepy import *
# later ...
clip.display_in_notebook(width=360)
clip.audio.display_in_notebook()

clip.write_gif("test.gif")
display_in_notebook('test.gif')

clip.save_frame("first_frame.jpeg")
display_in_notebook("first_frame.jpeg")
iter_chunks(chunksize=None, chunk_duration=None, fps=None, quantize=False, nbytes=2, logger=None)[source]
Iterator that returns the whole sound array of the clip by chunks

max_volume(stereo=False, chunksize=50000, logger=None)[source]
Returns the maximum volume level of the clip.

to_soundarray(tt=None, fps=None, quantize=False, nbytes=2, buffersize=50000)[source]
Transforms the sound into an array that can be played by pygame or written in a wav file. See AudioClip.preview.

Parameters
:
fps – Frame rate of the sound for the conversion. 44100 for top quality.

nbytes – Number of bytes to encode the sound: 1 for 8bit sound, 2 for 16bit, 4 for 32bit sound.

write_audiofile(filename, fps=None, nbytes=2, buffersize=2000, codec=None, bitrate=None, ffmpeg_params=None, write_logfile=False, logger='bar')[source]
Writes an audio file from the AudioClip.

Parameters
:
filename – Name of the output file, as a string or a path-like object.

fps – Frames per second. If not set, it will try default to self.fps if already set, otherwise it will default to 44100.

nbytes – Sample width (set to 2 for 16-bit sound, 4 for 32-bit sound)

buffersize – The sound is not generated all at once, but rather made by bunches of frames (chunks). buffersize is the size of such a chunk. Try varying it if you meet audio problems (but you shouldn’t have to). Default to 2000

codec – Which audio codec should be used. If None provided, the codec is determined based on the extension of the filename. Choose ‘pcm_s16le’ for 16-bit wav and ‘pcm_s32le’ for 32-bit wav.

bitrate – Audio bitrate, given as a string like ‘50k’, ‘500k’, ‘3000k’. Will determine the size and quality of the output file. Note that it mainly an indicative goal, the bitrate won’t necessarily be the this in the output file.

ffmpeg_params – Any additional parameters you would like to pass, as a list of terms, like [‘-option1’, ‘value1’, ‘-option2’, ‘value2’]

write_logfile – If true, produces a detailed logfile named filename + ‘.log’ when writing the file

logger – Either "bar" for progress bar or None or any Proglog logger.

moviepy.audio.AudioClip.CompositeAudioClip
class moviepy.audio.AudioClip.CompositeAudioClip(clips)[source]
Clip made by composing several AudioClips.

An audio clip made by putting together several audio clips.

Parameters
:
clips – List of audio clips, which may start playing at different times or together, depends on their start attributes. If all have their duration attribute set, the duration of the composite clip is computed automatically.

property ends
Returns ending times for all clips in the composition.

frame_function(t)[source]
Renders a frame for the composition for the time t.

property starts
Returns starting times for all clips in the composition.

moviepy.audio.AudioClip.concatenate_audioclips
moviepy.audio.AudioClip.concatenate_audioclips(clips)[source]
Concatenates one AudioClip after another, in the order that are passed to clips parameter.

Parameters
:
clips – List of audio clips, which will be played one after other.

moviepy.audio.fx
All the audio effects that can be applied to AudioClip and VideoClip.

Modules

moviepy.audio.fx.AudioDelay([offset, ...])

Repeats audio certain number of times at constant intervals multiplying their volume levels using a linear space in the range 1 to decay argument value.

moviepy.audio.fx.AudioFadeIn(duration)

Return an audio (or video) clip that is first mute, then the sound arrives progressively over duration seconds.

moviepy.audio.fx.AudioFadeOut(duration)

Return a sound clip where the sound fades out progressively over duration seconds at the end of the clip.

moviepy.audio.fx.AudioLoop([n_loops, duration])

Loops over an audio clip.

moviepy.audio.fx.AudioNormalize()

Return a clip whose volume is normalized to 0db.

moviepy.audio.fx.MultiplyStereoVolume([...])

For a stereo audioclip, this function enables to change the volume of the left and right channel separately (with the factors left and right).

moviepy.audio.fx.MultiplyVolume(factor[, ...])

Returns a clip with audio volume multiplied by the value factor.

moviepy.audio.io
Class and methods to read, write, preview audiofiles.

Modules

moviepy.audio.io.AudioFileClip

Implements AudioFileClip, a class for audio clips creation using audio files.

moviepy.audio.io.ffmpeg_audiowriter

MoviePy audio writing with ffmpeg.

moviepy.audio.io.ffplay_audiopreviewer

MoviePy audio writing with ffmpeg.

moviepy.audio.io.readers

MoviePy audio reading with ffmpeg.

moviepy.config
Third party programs configuration for MoviePy.

Functions

check()

Check if moviepy has found the binaries for FFmpeg.

try_cmd(cmd)

Verify if the OS support command invocation as expected by moviepy

moviepy.decorators
Decorators used by moviepy.

Functions

add_mask_if_none(func, clip, *args, **kwargs)

Add a mask to the clip if there is none.

apply_to_audio(func, clip, *args, **kwargs)

Applies the function func to the audio of the clip created with func.

apply_to_mask(func, clip, *args, **kwargs)

Applies the same function func to the mask of the clip created with func.

audio_video_effect(func, effect, clip, ...)

Use an audio function on a video/audio clip.

convert_masks_to_RGB(func, clip, *args, **kwargs)

If the clip is a mask, convert it to RGB before running the function.

convert_parameter_to_seconds(varnames)

Converts the specified variables to seconds.

convert_path_to_string(varnames)

Converts the specified variables to a path string.

outplace(func, clip, *args, **kwargs)

Applies func(clip.copy(), *args, **kwargs) and returns clip.copy().

preprocess_args(preprocess_func, varnames)

Applies preprocess_func to variables in varnames before launching the function.

requires_duration(func, clip, *args, **kwargs)

Raises an error if the clip has no duration.

requires_fps(func, clip, *args, **kwargs)

Raises an error if the clip has no fps.

use_clip_fps_by_default(func)

Will use clip.fps if no fps=... is provided in kwargs.

moviepy.tools
Misc. useful functions that can be used at many places in the program.

Functions

close_all_clips([objects, types])

Closes all clips in a context.

compute_position(clip1_size, clip2_size, pos)

Return the position to put clip 1 on clip 2 based on both clip size and the position of clip 1, as return by clip1.pos() method

convert_to_seconds(time)

Will convert any time into seconds.

cross_platform_popen_params(popen_params)

Wrap with this function a dictionary of subprocess.Popen kwargs and will be ready to work without unexpected behaviours in any platform.

deprecated_version_of(func, old_name)

Indicates that a function is deprecated and has a new name.

ffmpeg_escape_filename(filename)

Escape a filename that we want to pass to the ffmpeg command line

find_extension(codec)

Returns the correspondent file extension for a codec.

no_display_available()

Return True if we determine the host system has no graphical environment.

subprocess_call(cmd[, logger])

Executes the given subprocess command.

moviepy.video
Everything about video manipulation.

Modules

moviepy.video.VideoClip

Implements VideoClip (base class for video clips) and its main subclasses:

moviepy.video.compositing

All for compositing video clips.

moviepy.video.fx

All the visual effects that can be applied to VideoClip.

moviepy.video.io

Classes and methods for reading, writing and previewing video files.

moviepy.video.tools


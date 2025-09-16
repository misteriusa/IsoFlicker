import sys
import os
import math
import numpy as np
import librosa
import soundfile as sf
import tempfile
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

# MoviePy imports with safe fallback
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
except Exception:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.audio.AudioClip import CompositeAudioClip
    except Exception as _mp_err:
        raise _mp_err
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip


def generate_isochronic_tone(frequency, duration, sample_rate=44100, volume=0.5, carrier_frequency=100.0):
    """Generate an isochronic tone at the specified frequency and duration.
    
    An isochronic tone is a type of brainwave entrainment audio that uses 
    evenly spaced pulses of a carrier frequency to stimulate specific brainwave states.
    
    Args:
        frequency (float): The entrainment frequency in Hz (pulses per second)
        duration (float): The duration of the tone in seconds
        sample_rate (int, optional): The sample rate of the audio. Defaults to 44100.
        volume (float, optional): The volume of the tone (0.0 to 1.0). Defaults to 0.5.
        carrier_frequency (float, optional): The carrier frequency in Hz. Defaults to 100.0.
        
    Returns:
        tuple: A tuple containing:
            - numpy.ndarray: The audio data as a numpy array
            - int: The sample rate of the audio
            
    Example:
        >>> tone_data, sr = generate_isochronic_tone(10.0, 5.0, 44100, 0.5, 100.0)
        >>> len(tone_data)
        220500
    """
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Create sine wave at the specified carrier frequency
    sine_wave = np.sin(2 * np.pi * carrier_frequency * t)
    
    # Create amplitude modulation envelope for isochronic effect (square wave)
    mod_freq = frequency  # Use entrainment frequency for modulation
    envelope = 0.5 * (1 + np.sign(np.sin(2 * np.pi * mod_freq * t)))
    
    # Apply envelope to sine wave
    isochronic_tone = sine_wave * envelope * volume
    
    return isochronic_tone, sample_rate


def detect_isochronic_frequency(audio_path):
    """Detect the isochronic frequency from an audio file using beat tracking.
    
    This function attempts to detect the natural rhythm or beat of an audio file
    and converts it to an appropriate isochronic frequency for brainwave entrainment.
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        float: Detected frequency in Hz, or 10.0 if detection fails
        
    Example:
        >>> freq = detect_isochronic_frequency("audio.wav")
        >>> print(freq)
        8.5
    """
    try:
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        tempo_bpm, _ = librosa.beat.beat_track(y=y, sr=sr)
        if tempo_bpm <= 0:
            return 10.0
        return tempo_bpm / 60.0
    except Exception as e:
        print(f"Error detecting frequency: {e}")
        return 10.0


class BaseVideoProcessor(QThread):
    """Base class for video processing with isochronic entrainment effects.
    
    This class provides the core functionality for processing videos with 
    isochronic audio and visual entrainment effects. It handles:
    - Loading and processing video files
    - Generating isochronic audio tones
    - Applying visual flicker effects to video frames
    - Mixing audio tracks
    - Exporting the final processed video
    
    The class inherits from QThread to allow processing to run in a separate thread,
    preventing the UI from freezing during long operations.
    
    Signals:
        progress_signal (pyqtSignal[int]): Emitted to update progress (0-100)
        finished_signal (pyqtSignal[str]): Emitted when processing is complete with output file path
        error_signal (pyqtSignal[str]): Emitted when an error occurs with error message
    """
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, video_path, output_path, mode, config):
        """Initialize the BaseVideoProcessor.
        
        Args:
            video_path (str): Path to the input video file
            output_path (str): Path for the output video file
            mode (str): Encoding mode ('h264' or 'ffv1')
            config (dict): Configuration dictionary containing processing options
        
        The config dictionary should contain the following keys:
            - use_audio_entrainment (bool): Whether to apply audio entrainment
            - tone_frequency (float): Audio entrainment frequency in Hz
            - tone_volume (float): Audio entrainment volume (0.0 to 1.0)
            - carrier_frequency (float): Carrier frequency for audio entrainment
            - mix_with_original (bool): Whether to mix entrainment audio with original audio
            - original_volume (float): Volume of original audio when mixing
            - use_visual_entrainment (bool): Whether to apply visual entrainment
            - flicker_amplitude (float): Strength of visual flicker effect
            - visual_frequency (float): Visual entrainment frequency in Hz
        """
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.mode = mode
        self.config = config

    def run(self):
        try:
            self.process_video()
        except Exception as e:
            self.error_signal.emit(f"Error: {str(e)}\n{traceback.format_exc()}")

    def process_video(self):
        """Process the video with isochronic entrainment effects.
        This method should be overridden by subclasses to implement specific processing logic.
        """
        video_clip = None
        final_clip = None
        temp_dir = None
        try:
            # Create temporary directory for intermediate files
            temp_dir = tempfile.mkdtemp()
            temp_audio_path = os.path.join(temp_dir, "temp_audio.wav")
            
            # Load the original video
            video_clip = VideoFileClip(self.video_path)
            if not video_clip:
                raise Exception("Failed to load video file")
            
            # Generate the isochronic tone if required
            if self.config["use_audio_entrainment"]:
                # Generate isochronic tone
                self.progress_signal.emit(10)
                duration = video_clip.duration
                sample_rate = 44100  # Standard audio sample rate
                
                # Generate main tone
                tone_data, sr = generate_isochronic_tone(
                    self.config["tone_frequency"], 
                    duration, 
                    sample_rate, 
                    self.config["tone_volume"],
                    self.config.get("carrier_frequency", 100.0)  # Pass carrier frequency
                )
                
                # Write the tone to a temporary file
                sf.write(temp_audio_path, tone_data, sr)
                
                # Load the tone as an audio clip
                tone_clip = AudioFileClip(temp_audio_path)
                
                # Mix with original audio if requested
                if self.config["mix_with_original"] and video_clip.audio is not None:
                    original_audio = video_clip.audio
                    mixed_audio = CompositeAudioClip([
                        original_audio.volumex(self.config["original_volume"]),
                        tone_clip.volumex(self.config["tone_volume"])
                    ])
                    final_audio = mixed_audio
                else:
                    final_audio = tone_clip
            else:
                # Use original audio
                final_audio = video_clip.audio if video_clip.audio else None
            
            self.progress_signal.emit(20)
            
            # Process video frames with flicker effect if enabled
            if self.config["use_visual_entrainment"]:
                fps = video_clip.fps
                frame_count = int(video_clip.duration * fps)
                # Pre-allocate list for better memory management
                frames = [None] * frame_count
                
                # Pre-calculate constants
                flicker_amp = self.config["flicker_amplitude"]
                flicker_freq = self.config["visual_frequency"]
                
                # Process each frame with the flicker effect
                for i in range(frame_count):
                    if i % 10 == 0:  # Update progress every 10 frames
                        progress = 20 + int((i / frame_count) * 60)
                        self.progress_signal.emit(progress)
                    
                    t = i / fps
                    frame = video_clip.get_frame(t)
                    
                    # Apply flicker effect using sine wave at the specified frequency
                    factor = 1.0 + flicker_amp * math.sin(2.0 * math.pi * flicker_freq * t)
                    factor = max(0, factor)
                    
                    # Apply the brightness factor to the frame
                    # Use more efficient data type conversion
                    modified_frame = np.clip(frame.astype(np.float32, copy=False) * factor, 0, 255).astype(np.uint8)
                    frames[i] = modified_frame
                
                # Create a clip from the modified frames
                flicker_video = ImageSequenceClip(frames, fps=fps)
                final_clip = flicker_video.set_audio(final_audio) if final_audio else flicker_video
            else:
                # Use original video with potentially modified audio
                final_clip = video_clip.set_audio(final_audio) if final_audio else video_clip
            
            self.progress_signal.emit(80)
            
            # Determine output format
            codec = "ffv1" if self.mode == "ffv1" else "libx264"
            ext = ".mkv" if self.mode == "ffv1" else ".mp4"
            
            base, _ = os.path.splitext(self.output_path)
            output_file = base + ext
            
            # Write the final video
            if final_clip:
                final_clip.write_videofile(
                    output_file,
                    codec=codec,
                    audio_codec="pcm_s16le" if self.mode == "ffv1" else "aac",
                    threads=4,
                    ffmpeg_params=["-crf", "0", "-preset", 
                                  "ultrafast" if self.mode == "ffv1" else "medium"]
                )
            else:
                raise Exception("Failed to create output video clip")
            
            # Clean up resources
            if video_clip and video_clip.audio:
                video_clip.audio.close()
            if video_clip:
                video_clip.close()
            if final_clip:
                final_clip.close()
            
            # Clean up temporary files
            if temp_dir:
                try:
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    os.rmdir(temp_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean up temporary files: {e}")
            
            self.progress_signal.emit(100)
            self.finished_signal.emit(output_file)
        except Exception as e:
            # Clean up resources in case of error
            if video_clip and video_clip.audio:
                try:
                    video_clip.audio.close()
                except:
                    pass
            if video_clip:
                try:
                    video_clip.close()
                except:
                    pass
            if final_clip:
                try:
                    final_clip.close()
                except:
                    pass
            
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    os.rmdir(temp_dir)
                except:
                    pass
            
            raise Exception(f"Error processing video: {str(e)}")
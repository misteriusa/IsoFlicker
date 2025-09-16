import sys
import os
import math
import numpy as np
import librosa
import soundfile as sf
import tempfile
import traceback
import cv2
import multiprocessing as mp
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

# Import the advanced generator modules
from advanced_isochronic_generator import (
    IsochronicToneGenerator, 
    WaveformType, 
    ModulationType,
    generate_isochronic_tone
)

from core.ffmpeg_utils import ensure_ffmpeg_available

class EnhancedVideoProcessor(QThread):
    """Enhanced video processor with SINE presets, custom audio, and advanced visual effects.
    
    This class extends the BaseVideoProcessor to provide enhanced functionality including:
    - Support for SINE presets with complex frequency curves
    - Custom audio file input
    - Advanced visual effects (pulse, fade, strobe)
    - Text overlay support
    - Better integration with preset timelines
    
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

    def __init__(self, video_path, output_path, mode, config, isochronic_audio=None):
        """Initialize the EnhancedVideoProcessor.
        
        Args:
            video_path (str): Path to the input video file
            output_path (str): Path for the output video file
            mode (str): Encoding mode ('h264' or 'ffv1')
            config (dict): Configuration dictionary containing processing options
            isochronic_audio (str, optional): Path to a pre-generated isochronic tone file
        
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
            - visual_type (str): Type of visual effect ('pulse', 'fade', 'strobe')
            - preset (object, optional): SINE preset object with timeline information
        """
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.mode = mode
        self.config = config
        self.isochronic_audio = isochronic_audio

    @staticmethod
    def _ensure_ffmpeg_path():
        """Compatibility shim that delegates to the shared helper."""
        return ensure_ffmpeg_available()

    def run(self):
        try:
            self.process_video()
        except Exception as e:
            self.error_signal.emit(f"Error: {str(e)}\n{traceback.format_exc()}")

    def _apply_text_overlays(self, frame, t, overlays):
        """Draw text overlays onto a frame for a given time t.
        
        This method applies text overlays to video frames using OpenCV text drawing
        with alpha blending for smooth transitions. It handles positioning, timing,
        and styling of text overlays.
        
        Args:
            frame (numpy.ndarray): The video frame to apply overlays to
            t (float): Current time in seconds
            overlays (list): List of overlay objects with text, timing, and styling properties
        
        Returns:
            numpy.ndarray: The frame with text overlays applied
            
        Each overlay object should have the following attributes:
            - text (str): The text to display
            - start_time (float): When to start displaying the text
            - duration (float): How long to display the text
            - opacity (float): Text opacity (0.0 to 1.0)
            - font_size (int): Text font size
            - position (str): Text position ('center', 'top', 'bottom', 'left', 'right')
            - color (tuple): Text color as RGB tuple
        """
        if not overlays:
            return frame

        img = frame.copy()
        try:
            h, w = img.shape[:2]
            for ov in overlays:
                try:
                    start = float(getattr(ov, 'start_time', 0.0))
                    duration = float(getattr(ov, 'duration', 0.0))
                    if duration <= 0:
                        continue
                    end = start + duration
                    if not (start <= t <= end):
                        continue

                    text = getattr(ov, 'text', '') or ''
                    opacity = max(0.0, min(1.0, float(getattr(ov, 'opacity', 1.0))))
                    font_size = int(getattr(ov, 'font_size', 24))
                    position = (getattr(ov, 'position', 'center') or 'center').lower()
                    color = getattr(ov, 'color', (255, 255, 255))
                    if hasattr(color, 'red'):
                        color = (color.red(), color.green(), color.blue())

                    # Map font size to OpenCV scale.
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    scale = max(0.4, font_size / 32.0)
                    thickness = max(1, int(scale * 2))

                    # Calculate text size to position it.
                    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
                    x = (w - tw) // 2
                    y = (h + th) // 2
                    if 'top' in position:
                        y = 20 + th
                    if 'bottom' in position:
                        y = h - 20
                    if 'left' in position:
                        x = 20
                    if 'right' in position:
                        x = max(20, w - tw - 20)

                    # Create overlay image and draw text on it
                    overlay_img = img.copy()
                    cv2.putText(overlay_img, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)

                    # Alpha blend
                    img = cv2.addWeighted(overlay_img, opacity, img, 1 - opacity, 0)
                except Exception:
                    continue
            return img
        except Exception:
            return img

    def _process_frame_batch(self, args):
        """Process a batch of frames in parallel.
        
        This method is designed to be run in a separate process for parallel processing.
        
        Args:
            args (tuple): A tuple containing:
                - frames_data: List of tuples (frame_index, frame_data, time)
                - config: Configuration dictionary
                - text_overlays: Text overlays to apply
                - preset: SINE preset with timeline information
                - visual_type: Type of visual effect to apply
                
        Returns:
            list: List of tuples (frame_index, modified_frame)
        """
        frames_data, config, text_overlays, preset, visual_type = args
        results = []
        
        for frame_index, frame, t in frames_data:
            # Apply text overlays
            frame = self._apply_text_overlays(frame, t, text_overlays)
            
            # Get current frequency from preset timeline if available
            if preset and hasattr(preset, 'entrainment_curve'):
                current_freq = preset.entrainment_curve.get_value_at_time(t)
            else:
                current_freq = config["visual_frequency"]
            
            # Apply different visual effects based on type
            if visual_type == "pulse":
                # Classic pulse effect
                flicker_amp = config["flicker_amplitude"]
                factor = 1.0 + flicker_amp * math.sin(2.0 * math.pi * current_freq * t)
                factor = max(0, factor)
                modified_frame = np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)
            elif visual_type == "fade":
                # Smooth fade effect
                flicker_amp = config["flicker_amplitude"]
                factor = 1.0 + flicker_amp * (0.5 + 0.5 * math.sin(2.0 * math.pi * current_freq * t))
                factor = max(0, min(1.0, factor))
                modified_frame = np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)
            elif visual_type == "strobe":
                # Strobe effect (more intense)
                strobe_value = math.sin(2.0 * math.pi * current_freq * t)
                if strobe_value > 0.5:
                    modified_frame = np.clip(frame.astype(np.float32) * (1.0 + config["flicker_amplitude"]), 0, 255).astype(np.uint8)
                elif strobe_value < -0.5:
                    modified_frame = np.clip(frame.astype(np.float32) * (1.0 - config["flicker_amplitude"]), 0, 255).astype(np.uint8)
                else:
                    modified_frame = frame
            else:
                # Default to pulse
                flicker_amp = config["flicker_amplitude"]
                factor = 1.0 + flicker_amp * math.sin(2.0 * math.pi * current_freq * t)
                factor = max(0, factor)
                modified_frame = np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)
            
            results.append((frame_index, modified_frame))
        
        return results

    def process_video(self):
        """Process the video with enhanced features.
        
        This method performs the main video processing workflow:
        1. Loads the input video
        2. Generates or loads isochronic audio
        3. Mixes audio tracks if requested
        4. Applies visual effects to video frames (with parallel processing)
        5. Applies text overlays
        6. Exports the final processed video
        
        The method handles all resource management and cleanup, including:
        - Temporary file creation and deletion
        - Video and audio clip resource management
        - Error handling and cleanup on failure
        """
        video_clip = None
        final_clip = None
        temp_dir = None
        try:
            # Make sure ffmpeg is available before touching MoviePy
            if not self._ensure_ffmpeg_path():
                raise Exception(
                    "FFmpeg not found. Install FFmpeg or launch via startEnhancedIsoFlicker.bat "
                    "which wires the bundled ffmpeg into PATH."
                )
            # Create temporary directory for intermediate files
            temp_dir = tempfile.mkdtemp()
            temp_audio_path = self.isochronic_audio or os.path.join(temp_dir, "temp_audio.wav")
            
            # Load the original video
            video_clip = VideoFileClip(self.video_path)
            if not video_clip:
                raise Exception("Failed to load video file")
            
            # Generate the isochronic tone if required and not provided externally
            if self.config["use_audio_entrainment"] and not self.isochronic_audio:
                # Generate isochronic tone
                self.progress_signal.emit(10)
                duration = video_clip.duration
                sample_rate = 44100  # Standard audio sample rate
                
                # Check if we have a preset with a timeline
                preset = self.config.get("preset")
                if preset and hasattr(preset, 'generate_looped_audio'):
                    # Generate audio using the preset
                    tone_data, sr = preset.generate_looped_audio(duration, sample_rate)
                else:
                    # Generate using basic tone generator
                    tone_data, sr = generate_isochronic_tone(
                        self.config["tone_frequency"], 
                        duration, 
                        sample_rate, 
                        self.config["tone_volume"],
                        self.config.get("carrier_frequency", 100.0)
                    )
                
                # Write the tone to a temporary file if not already provided
                if not self.isochronic_audio:
                    sf.write(temp_audio_path, tone_data, sr)
            
            # Load the audio for the output
            if self.config["use_audio_entrainment"]:
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
                frames = [None] * frame_count  # Pre-allocate list
                
                # Get visual effect type
                visual_type = self.config.get("visual_type", "pulse").lower()
                
                # Get text overlays from preset if available
                text_overlays = []
                preset_for_overlays = self.config.get("preset")
                if preset_for_overlays is not None and hasattr(preset_for_overlays, 'text_overlays'):
                    text_overlays = preset_for_overlays.text_overlays or []

                # Determine batch size based on CPU count
                cpu_count = mp.cpu_count()
                batch_size = max(1, frame_count // (cpu_count * 4))  # Process in smaller batches
                
                # Create a pool of worker processes
                with mp.Pool(processes=cpu_count) as pool:
                    # Prepare batches of frames
                    batches = []
                    for i in range(0, frame_count, batch_size):
                        batch_end = min(i + batch_size, frame_count)
                        batch_frames = []
                        
                        # Collect frames for this batch
                        for j in range(i, batch_end):
                            if j % 10 == 0:  # Update progress every 10 frames
                                progress = 20 + int((j / frame_count) * 60)
                                self.progress_signal.emit(progress)
                            
                            t = j / fps
                            frame = video_clip.get_frame(t)
                            batch_frames.append((j, frame, t))
                        
                        # Add batch to processing queue
                        batch_args = (batch_frames, self.config, text_overlays, self.config.get("preset"), visual_type)
                        batches.append(batch_args)
                    
                    # Process batches in parallel
                    batch_results = pool.map(self._process_frame_batch, batches)
                    
                    # Collect results
                    for batch_result in batch_results:
                        for frame_index, modified_frame in batch_result:
                            frames[frame_index] = modified_frame
                
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
                    if os.path.exists(temp_audio_path) and temp_audio_path != self.isochronic_audio:
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
                    if os.path.exists(temp_audio_path) and temp_audio_path != self.isochronic_audio:
                        os.remove(temp_audio_path)
                    os.rmdir(temp_dir)
                except:
                    pass
            
            raise Exception(f"Error processing video: {str(e)}")

import sys
import os
import time
import threading
import json
import numpy as np
import tempfile
import math
import cv2  # Move it here with other imports

# Import moviepy components with fallback for environments missing editor module
try:
    from moviepy.editor import (
        VideoFileClip,
        AudioFileClip,
        ImageSequenceClip,
        CompositeAudioClip,
    )
except Exception:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
        from moviepy.audio.AudioClip import CompositeAudioClip
    except Exception as _moviepy_import_error:  # re-raise with context
        raise _moviepy_import_error

# Import soundfile for audio processing
import soundfile as sf

# Check if PyQt5 is available or any other checks you have...

import xml.etree.ElementTree as ET
from preset_converter import validate_preset_file, xml_to_sine_preset, sine_preset_to_xml
from file_optimizer import VideoOptimizer, CompressionDialog
# Import the advanced generator modules
from advanced_isochronic_generator import (
    IsochronicToneGenerator, 
    WaveformType, 
    ModulationType,
    generate_isochronic_tone
)

# Import our refactored video processor
from core.enhanced_video_processor import EnhancedVideoProcessor

from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThread
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QApplication, QMainWindow, 
    QTabWidget, QWidget, QVBoxLayout, QDialog, QDialogButtonBox,
    QPushButton, QHBoxLayout, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox, QRadioButton, QSlider, QFormLayout, QFrame, QListWidget
)
from ui.modern_ui import ModernMainWindow


# Import the TextOverlay classes and UI
from text_overlay import TextOverlay, TextOverlayDialog, TextOverlayManager
from ui.pro_layout import ProEditorWidget

# We already import QDialog in the widget list above

# Protocol presets library
PROTOCOL_PRESETS = {
    "ADHD/Beta": {
        "name": "ADHD Focus/Beta",
        "entrainment_points": [
            {"time": 0, "value": 12.0},
            {"time": 60, "value": 15.0},
            {"time": 180, "value": 18.0},
            {"time": 300, "value": 16.0},
            {"time": 420, "value": 14.0}
        ],
        "carrier_type": "sine",
        "modulation_type": "square"
    },
    "Anxiety/Alpha": {
        "name": "Anxiety Relief/Alpha",
        "entrainment_points": [
            {"time": 0, "value": 12.0},
            {"time": 120, "value": 10.0},
            {"time": 240, "value": 8.5},
            {"time": 420, "value": 8.0}
        ],
        "carrier_type": "sine",
        "modulation_type": "sine"
    },
    "Insomnia/Theta-Delta": {
        "name": "Insomnia/Theta-Delta",
        "entrainment_points": [
            {"time": 0, "value": 7.0},
            {"time": 180, "value": 5.0},
            {"time": 300, "value": 3.5},
            {"time": 480, "value": 2.5},
            {"time": 600, "value": 1.5}
        ],
        "carrier_type": "sine",
        "modulation_type": "sine"
    }
}

from core.ffmpeg_utils import ensure_ffmpeg_available as _ensure_ffmpeg_path
###############################################################################
# Original FlickerWorker and related classes
###############################################################################
class FlickerWorker(EnhancedVideoProcessor):
    """Base worker class for flicker processing (now inherits from EnhancedVideoProcessor)."""
    pass


###############################################################################
# EnhancedFlickerWorker with Compression Support
###############################################################################
class EnhancedFlickerWorker(FlickerWorker):
    """Enhanced worker that supports SINE presets, custom audio, and advanced visual effects"""
    error_signal = pyqtSignal(str)
    
    def __init__(self, video_path, output_path, mode, config, isochronic_audio=None):
        """
        Initialize the worker
        
        Args:
            video_path (str): Path to the input video
            output_path (str): Path for the output video
            mode (str): Encoding mode ('h264' or 'ffv1')
            config (dict): Configuration options
            isochronic_audio (str, optional): Path to a pre-generated isochronic tone file
        """
        super().__init__(video_path, output_path, mode, config)
        self.isochronic_audio = isochronic_audio
    
    def _apply_text_overlays(self, frame, t, overlays):
        """Draw text overlays onto a frame for a given time t.
        Uses OpenCV text drawing with alpha blending; falls back gracefully.
        """
        if not overlays:
            return frame

        img = frame.copy()
        try:
            import cv2
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

    def process_video(self):
        """Process the video with enhanced features"""
        video_clip = None
        final_clip = None
        temp_dir = None
        try:
            # Ensure ffmpeg is available before creating any MoviePy clips
            if not _ensure_ffmpeg_path():
                raise Exception(
                    "FFmpeg not found. Install FFmpeg or run startEnhancedIsoFlicker.bat "
                    "to use the bundled ffmpeg."
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
                frames = []
                
                # Get visual effect type
                visual_type = self.config.get("visual_type", "pulse").lower()
                
                # Process each frame with the selected effect
                # Get text overlays from preset if available
                text_overlays = []
                preset_for_overlays = self.config.get("preset")
                if preset_for_overlays is not None and hasattr(preset_for_overlays, 'text_overlays'):
                    text_overlays = preset_for_overlays.text_overlays or []

                for i in range(frame_count):
                    if i % 10 == 0:  # Update progress every 10 frames
                        progress = 20 + int((i / frame_count) * 60)
                        self.progress_signal.emit(progress)
                    
                    t = i / fps
                    frame = video_clip.get_frame(t)
                    
                    # Get current frequency from preset timeline if available
                    preset = self.config.get("preset")
                    if preset and hasattr(preset, 'entrainment_curve'):
                        current_freq = preset.entrainment_curve.get_value_at_time(t)
                    else:
                        current_freq = self.config["visual_frequency"]
                    
                    # Apply different visual effects based on type
                    if visual_type == "flash":
                        # Simple brightness flash
                        flicker_amp = self.config.get("flicker_amplitude", 0.5)
                        factor = 1.0 + flicker_amp * math.sin(2.0 * math.pi * current_freq * t)
                        factor = max(0, min(2.0, factor))  # Limit range to avoid extreme values
                        modified_frame = np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)
                        
                    elif visual_type == "color_cycle" or visual_type == "color cycle":
                        # Color cycling effect
                        phase = (current_freq * t) % 1.0
                        hue_shift = int(phase * 360)
                        
                        # Convert to HSV, shift hue, convert back to RGB
                        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
                        hsv_frame[:, :, 0] = (hsv_frame[:, :, 0] + hue_shift) % 180
                        modified_frame = cv2.cvtColor(hsv_frame, cv2.COLOR_HSV2RGB)
                        
                    elif visual_type == "blur":
                        # Pulsing blur effect
                        pulse = 0.5 * (1 + math.sin(2.0 * math.pi * current_freq * t))
                        blur_amount = int(1 + 10 * pulse)
                        if blur_amount % 2 == 0:  # Blur requires odd kernel size
                            blur_amount += 1
                        modified_frame = cv2.GaussianBlur(frame, (blur_amount, blur_amount), 0)
                        
                    else:  # Default "pulse" effect
                        # On/off pulse effect based on square wave
                        pulse = 0.5 * (1 + np.sign(math.sin(2.0 * math.pi * current_freq * t)))
                        factor = 1.0 if pulse > 0.5 else max(0.5, 1.0 - self.config.get("flicker_amplitude", 0.5))
                        modified_frame = np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)
                    
                    # Apply text overlays (if any) on the modified frame
                    if text_overlays:
                        modified_frame = self._apply_text_overlays(modified_frame, t, text_overlays)

                    frames.append(modified_frame)
                
                # Create a clip from the modified frames
                flicker_video = ImageSequenceClip(frames, fps=fps)
                final_clip = flicker_video.set_audio(final_audio) if final_audio else flicker_video
            else:
                # Use original video with potentially modified audio
                final_clip = video_clip.set_audio(final_audio) if final_audio else video_clip
            
            self.progress_signal.emit(80)
            
            # Determine output format
            codec = "ffv1" if self.mode == "ffv1" else "libx264"
            
            # Get extension from output path or default to the mode
            ext = os.path.splitext(self.output_path)[1]
            if not ext:
                ext = ".mkv" if self.mode == "ffv1" else ".mp4"
                self.output_path += ext
            
            # Write the final video
            if final_clip:
                final_clip.write_videofile(
                    self.output_path,
                    codec=codec,
                    audio_codec="pcm_s16le" if self.mode == "ffv1" else "aac",
                    threads=4,
                    ffmpeg_params=["-crf", "0" if self.mode == "ffv1" else "23", 
                                  "-preset", "ultrafast" if self.mode == "ffv1" else "medium"]
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
            
            # Clean up temporary files (but not the provided isochronic audio)
            if temp_dir:
                try:
                    # Only delete temp_audio_path if we created it
                    if not self.isochronic_audio and os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    os.rmdir(temp_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean up temporary files: {e}")
            
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
            
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
                    # Only delete temp_audio_path if we created it
                    if not self.isochronic_audio and os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    os.rmdir(temp_dir)
                except:
                    pass
            
            self.error_signal.emit(f"Error processing video: {str(e)}")
            raise



###############################################################################
# SinePreset class with full implementation
###############################################################################
class ControlPoint:
    """Represents a control point on a curve"""
    def __init__(self, time=0, value=0):
        self.time = time
        self.value = value
        self.selected = False

class Curve:
    """Represents a curve with control points for frequency or volume"""
    def __init__(self, min_value=0, max_value=1, default_value=0.5):
        self.control_points = []
        self.min_value = min_value
        self.max_value = max_value
        self.default_value = default_value
        self.selected_point = None
        
        # Add default points at start and end
        self.add_point(0, default_value)
        self.add_point(180, default_value)  # 3 minutes default
    
    def add_point(self, time, value):
        """Add a control point at the specified time and value"""
        # Check if there's already a point at this time
        for point in self.control_points:
            if abs(point.time - time) < 0.01:
                point.value = value
                return point
        
        # Add new point and sort
        new_point = ControlPoint(time, value)
        self.control_points.append(new_point)
        self.control_points.sort(key=lambda p: p.time)
        return new_point
    
    def get_value_at_time(self, time):
        """Get the interpolated value at a specific time"""
        if not self.control_points:
            return self.default_value
        
        # If time is before first point or after last point
        if time <= self.control_points[0].time:
            return self.control_points[0].value
        if time >= self.control_points[-1].time:
            return self.control_points[-1].value
        
        # Find the two points to interpolate between
        for i in range(len(self.control_points) - 1):
            if self.control_points[i].time <= time <= self.control_points[i + 1].time:
                p1 = self.control_points[i]
                p2 = self.control_points[i + 1]
                
                # Linear interpolation
                t = (time - p1.time) / (p2.time - p1.time)
                return p1.value + t * (p2.value - p1.value)
        
        return self.default_value
    
    def get_duration(self):
        """Get the duration of the curve (time of last point)"""
        if not self.control_points:
            return 180  # Default 3 minutes
        return self.control_points[-1].time
        
    def get_point_near(self, x, y, width, height, duration):
        """Find a control point near the given screen coordinates"""
        if not self.control_points:
            return None
            
        # Calculate threshold for proximity (in pixels)
        threshold = 10
        
        for point in self.control_points:
            # Convert point time/value to screen coordinates
            point_x = point.time * width / duration
            point_y = height - ((point.value - self.min_value) * height / (self.max_value - self.min_value))
            
            # Check if within threshold
            if abs(point_x - x) <= threshold and abs(point_y - y) <= threshold:
                return point
                
        return None
        
    def clear_selection(self):
        """Clear the selection state of all points"""
        for point in self.control_points:
            point.selected = False
        self.selected_point = None
        
    def point_on_line_segment(self, x, y, width, height, duration, tolerance=5):
        """Check if a point is on or near any line segment between control points"""
        for i in range(len(self.control_points) - 1):
            p1 = self.control_points[i]
            p2 = self.control_points[i+1]
            
            # Convert to screen coordinates
            p1x = int(p1.time / duration * width)
            p1y_factor = 1.0 - (p1.value - self.min_value) / (self.max_value - self.min_value)
            p1y = int(p1y_factor * height)
            
            p2x = int(p2.time / duration * width)
            p2y_factor = 1.0 - (p2.value - self.min_value) / (self.max_value - self.min_value)
            p2y = int(p2y_factor * height)
            
            # Check if point is near the line segment
            # First calculate the distance from point to line
            if p1x == p2x:  # Vertical line
                dist = abs(x - p1x)
                # Check if y is within range
                in_range = min(p1y, p2y) <= y <= max(p1y, p2y)
            else:
                # Calculate slope and y-intercept
                m = (p2y - p1y) / (p2x - p1x)
                b = p1y - m * p1x
                
                # Distance from point to line: |Ax + By + C|/sqrt(A^2 + B^2)
                # Line equation: y = mx + b -> -mx + y - b = 0
                # So A = -m, B = 1, C = -b
                dist = abs(-m * x + y - b) / math.sqrt(m * m + 1)
                
                # Check if point is within the line segment range
                # Project the point onto the line
                t = ((x - p1x) * (p2x - p1x) + (y - p1y) * (p2y - p1y)) / ((p2x - p1x)**2 + (p2y - p1y)**2)
                in_range = 0 <= t <= 1
                
            if dist <= tolerance and in_range:
                # Return the time and value at the point on the line
                if p1x == p2x:  # Vertical line
                    time = p1.time
                    t = (y - p1y) / (p2y - p1y) if p2y != p1y else 0
                    value = p1.value + t * (p2.value - p1.value)
                else:
                    t = (x - p1x) / (p2x - p1x)
                    time = p1.time + t * (p2.time - p1.time)
                    value = p1.value + t * (p2.value - p1.value)
                
                return True, time, value
                
        return False, 0, 0


class SinePreset:
    """Represents a SINE-based preset with entrainment, volume, and base frequency curves."""
    MIN_ENTRAINMENT_FREQ = 0.5
    MAX_ENTRAINMENT_FREQ = 40.0
    MIN_BASE_FREQ = 20.0
    MAX_BASE_FREQ = 1000.0
    DEFAULT_ENTRAINMENT_FREQ = 10.0
    DEFAULT_BASE_FREQ = 100.0

    def __init__(self, name="Default Preset"):
        self.name = name
        self.entrainment_curve = Curve(self.MIN_ENTRAINMENT_FREQ, self.MAX_ENTRAINMENT_FREQ, self.DEFAULT_ENTRAINMENT_FREQ)
        self.volume_curve = Curve(0.0, 1.0, 0.5)
        self.base_freq_curve = Curve(self.MIN_BASE_FREQ, self.MAX_BASE_FREQ, self.DEFAULT_BASE_FREQ)
        
        # Add modulation settings
        self.carrier_type = WaveformType.SINE  # Default carrier wave type
        self.modulation_type = ModulationType.SQUARE  # Default modulation type (on/off)
        
        # Visual and UX settings
        self.visual_effect_type = "pulse"
        self.visual_intensity = 0.5
        self.sync_audio_visual = True
        self.selected_format = "mp4"
        # Subsonic optional tone for masking/grounding
        self.enable_subsonic = False
        self.subsonic_frequency = 7.83
        self.subsonic_volume = 0.3
        # Master tone volume used in some UIs
        self.tone_volume = 0.8

        # Add text overlays attribute to fix the error
        self.text_overlays = []
    
    def get_duration(self):
        """Get the maximum duration of all curves"""
        return max(
            self.entrainment_curve.get_duration(),
            self.volume_curve.get_duration(),
            self.base_freq_curve.get_duration(),
            180  # Minimum 3 minutes
        )
    
    def set_duration(self, duration):
        """Set the duration of all curves by adjusting the last control point"""
        # Ensure we have at least two points in each curve
        for curve in [self.entrainment_curve, self.volume_curve, self.base_freq_curve]:
            if len(curve.control_points) < 2:
                # Add default points if needed
                if len(curve.control_points) == 0:
                    curve.add_point(0, curve.default_value)
                curve.add_point(duration, curve.default_value)
            else:
                # Move the last point to the new duration
                last_point = curve.control_points[-1]
                last_point.time = duration
                
        # Sort all points to ensure they're in order
        for curve in [self.entrainment_curve, self.volume_curve, self.base_freq_curve]:
            curve.control_points.sort(key=lambda p: p.time)
    
    def get_avg_entrainment_freq(self):
        """Calculate the average entrainment frequency"""
        if not self.entrainment_curve.control_points:
            return self.DEFAULT_ENTRAINMENT_FREQ
        
        total = sum(p.value for p in self.entrainment_curve.control_points)
        return total / len(self.entrainment_curve.control_points)
    
    def generate_audio(self, sample_rate=44100):
        """Generate the audio for this preset"""
        duration = self.get_duration()
        if duration <= 0:
            return np.array([]), sample_rate
        
        # Generate time array
        num_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        # Create output array
        output = np.zeros(num_samples)
        
        # Create tone generator
        tone_generator = IsochronicToneGenerator()
        
        # Process in small chunks to handle varying parameters
        chunk_size = int(0.01 * sample_rate)  # 10ms chunks
        for i in range(0, num_samples, chunk_size):
            end_idx = min(i + chunk_size, num_samples)
            chunk_t = t[i:end_idx]
            
            # Get current time in seconds
            current_time = chunk_t[0]
            
            # Look up parameters at this time
            entrainment_freq = self.entrainment_curve.get_value_at_time(current_time)
            volume = self.volume_curve.get_value_at_time(current_time)
            base_freq = self.base_freq_curve.get_value_at_time(current_time)
            
            # Generate chunk using advanced tone generator with modulation options
            chunk_output = tone_generator.generate_tone_segment(
                duration=len(chunk_t)/sample_rate,
                carrier_freq=base_freq,
                entrainment_freq=entrainment_freq,
                volume=volume,
                sample_rate=sample_rate,
                carrier_type=self.carrier_type,
                modulation_type=self.modulation_type
            )

            # Optionally add subsonic component (sine at low frequency)
            if getattr(self, 'enable_subsonic', False):
                sub_freq = float(getattr(self, 'subsonic_frequency', 7.83))
                sub_vol = float(getattr(self, 'subsonic_volume', 0.3))
                if sub_vol > 0:
                    sub_wave = np.sin(2 * np.pi * sub_freq * chunk_t) * sub_vol
                    # Mix: simple additive with soft clip safeguard
                    chunk_output = chunk_output + sub_wave
            
            # Add to output (make sure lengths match)
            if len(chunk_output) == len(chunk_t):
                output[i:end_idx] = chunk_output
            else:
                # Resample if needed
                output[i:end_idx] = chunk_output[:len(chunk_t)]
        
        # Apply fade in/out (10ms fade)
        fade_samples = min(int(0.01 * sample_rate), num_samples // 10)
        if fade_samples > 0:
            # Fade in
            output[:fade_samples] *= np.linspace(0, 1, fade_samples)
            # Fade out
            output[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
        # Normalize to prevent clipping
        max_amp = np.max(np.abs(output))
        if max_amp > 0.9:  # If close to clipping
            output = output * (0.9 / max_amp)
        
        return output, sample_rate
    
    def generate_looped_audio(self, target_duration, sample_rate=44100):
        """Generate audio that loops to match the target duration"""
        # Generate the base audio
        audio_data, sr = self.generate_audio(sample_rate)
        
        # Calculate current audio duration
        audio_duration = len(audio_data) / sr
        
        # If audio is already longer than target, just return it
        if audio_duration >= target_duration:
            return audio_data, sr
        
        # Calculate how many times to repeat
        repeats = int(math.ceil(target_duration / audio_duration))
        
        # Create looped audio
        looped_audio = np.tile(audio_data, repeats)
        
        # Trim to exact duration
        samples_needed = int(target_duration * sr)
        if len(looped_audio) > samples_needed:
            looped_audio = looped_audio[:samples_needed]
        
        return looped_audio, sr
    
    def save_to_file(self, filepath):
        """Save preset to a .sin file"""
        data = {
            "name": self.name,
            "entrainment_points": [{"time": p.time, "value": p.value} for p in self.entrainment_curve.control_points],
            "volume_points": [{"time": p.time, "value": p.value} for p in self.volume_curve.control_points],
            "base_freq_points": [{"time": p.time, "value": p.value} for p in self.base_freq_curve.control_points],
            "carrier_type": self.carrier_type.value if hasattr(self.carrier_type, 'value') else str(self.carrier_type),
            "modulation_type": self.modulation_type.value if hasattr(self.modulation_type, 'value') else str(self.modulation_type),
            # Extras for UI/persistence
            "visual_effect_type": getattr(self, 'visual_effect_type', 'pulse'),
            "visual_intensity": float(getattr(self, 'visual_intensity', 0.5)),
            "sync_audio_visual": bool(getattr(self, 'sync_audio_visual', True)),
            "selected_format": getattr(self, 'selected_format', 'mp4'),
            "enable_subsonic": bool(getattr(self, 'enable_subsonic', False)),
            "subsonic_frequency": float(getattr(self, 'subsonic_frequency', 7.83)),
            "subsonic_volume": float(getattr(self, 'subsonic_volume', 0.3)),
            "tone_volume": float(getattr(self, 'tone_volume', 0.8)),
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath):
        """
        Load preset from a file (.sin or .xml).
        Using preset_converter.validate_preset_file() to detect file type,
        and preset_converter.xml_to_sine_preset() to convert XML if needed.
        """
        try:
            # Check the file type
            is_valid, format_type = validate_preset_file(filepath)
            if not is_valid:
                raise ValueError(f"Invalid preset file: {filepath}")

            if format_type == "xml":
                # Convert XML preset to SINE format
                preset_data = xml_to_sine_preset(filepath)
                
                # Create a new preset
                preset = cls(name=preset_data.get("name", "Imported Preset"))
                
                # Clear default points
                preset.entrainment_curve.control_points = []
                preset.volume_curve.control_points = []
                preset.base_freq_curve.control_points = []
                
                # Add points from XML
                for point_data in preset_data.get("entrainment_points", []):
                    preset.entrainment_curve.add_point(point_data["time"], point_data["value"])
                
                for point_data in preset_data.get("volume_points", []):
                    preset.volume_curve.add_point(point_data["time"], point_data["value"])
                
                for point_data in preset_data.get("base_freq_points", []):
                    preset.base_freq_curve.add_point(point_data["time"], point_data["value"])
                
                return preset

            elif format_type == "sin":
                # Load as normal JSON file
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                preset = cls(name=data.get("name", "Imported Preset"))
                
                # Clear default points
                preset.entrainment_curve.control_points = []
                preset.volume_curve.control_points = []
                preset.base_freq_curve.control_points = []
                
                # Load entrainment points
                for point_data in data.get("entrainment_points", []):
                    preset.entrainment_curve.add_point(point_data["time"], point_data["value"])
                
                # Load volume points
                for point_data in data.get("volume_points", []):
                    preset.volume_curve.add_point(point_data["time"], point_data["value"])
                
                # Load base frequency points
                for point_data in data.get("base_freq_points", []):
                    preset.base_freq_curve.add_point(point_data["time"], point_data["value"])
                
                # Load modulation settings if available
                carrier_type_str = data.get("carrier_type", "sine")
                modulation_type_str = data.get("modulation_type", "square")
                
                # Parse carrier type
                try:
                    preset.carrier_type = WaveformType(carrier_type_str)
                except (ValueError, TypeError):
                    preset.carrier_type = WaveformType.SINE
                
                # Parse modulation type
                try:
                    preset.modulation_type = ModulationType(modulation_type_str)
                except (ValueError, TypeError):
                    preset.modulation_type = ModulationType.SQUARE
                
                # Load extra UI fields
                preset.visual_effect_type = data.get("visual_effect_type", "pulse")
                preset.visual_intensity = float(data.get("visual_intensity", 0.5))
                preset.sync_audio_visual = bool(data.get("sync_audio_visual", True))
                preset.selected_format = data.get("selected_format", "mp4")
                preset.enable_subsonic = bool(data.get("enable_subsonic", False))
                preset.subsonic_frequency = float(data.get("subsonic_frequency", 7.83))
                preset.subsonic_volume = float(data.get("subsonic_volume", 0.3))
                preset.tone_volume = float(data.get("tone_volume", 0.8))

                return preset
            else:
                raise ValueError(f"Unsupported preset file format: {format_type}")

        except Exception as e:
            print(f"Error loading preset file: {e}")
            raise


###############################################################################
# SineEditorWidget interface class for integration with main app
###############################################################################
class SineEditorWidget(QObject):
    """Interface for the SINE Editor widget."""
    
    preset_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset = SinePreset()
        self.current_file_path = None
    
    def open_preset(self):
        """
        Opens a file dialog to load a preset (.sin or .xml).
        """
        filepath, _ = QFileDialog.getOpenFileName(
            self.parent(),
            "Open Preset",
            "",
            "All Preset Files (*.sin *.xml);;SINE Preset Files (*.sin);;XML Preset Files (*.xml);;All Files (*)"
        )
        
        if filepath:
            try:
                self.preset = SinePreset.load_from_file(filepath)
                self.current_file_path = filepath
                self.preset_changed.emit()
                return True
            except Exception as e:
                QMessageBox.critical(self.parent(), "Error", f"Failed to open preset: {str(e)}")
                return False
        return False
    
    def save_preset(self, filepath=None):
        """
        Save preset to a file.
        
        Args:
            filepath: Path to save to. If None, will use current_file_path or prompt for location.
        """
        if filepath is None:
            if self.current_file_path:
                filepath = self.current_file_path
            else:
                filepath, _ = QFileDialog.getSaveFileName(
                    self.parent(),
                    "Save Preset As",
                    self.preset.name,
                    "SINE Preset Files (*.sin)"
                )
                
                if not filepath:
                    return False
        
        try:
            # Add extension if missing
            if not filepath.lower().endswith('.sin'):
                filepath += '.sin'
                
            self.preset.save_to_file(filepath)
            self.current_file_path = filepath
            return True
        except Exception as e:
            QMessageBox.critical(self.parent(), "Error", f"Failed to save preset: {str(e)}")
            return False
    
    def export_as_xml(self, filepath=None):
        """
        Export the preset as an XML file.
        
        Args:
            filepath: Path to save to. If None, will prompt for location.
        """
        if filepath is None:
            filepath, _ = QFileDialog.getSaveFileName(
                self.parent(),
                "Export as XML",
                self.preset.name,
                "XML Files (*.xml)"
            )
            
            if not filepath:
                return False
        
        try:
            # Add .xml extension if missing
            if not filepath.lower().endswith('.xml'):
                filepath += '.xml'
            
            # First create preset data dict
            preset_data = {
                "name": self.preset.name,
                "entrainment_points": [{"time": p.time, "value": p.value} 
                                      for p in self.preset.entrainment_curve.control_points],
                "volume_points": [{"time": p.time, "value": p.value} 
                                 for p in self.preset.volume_curve.control_points],
                "base_freq_points": [{"time": p.time, "value": p.value} 
                                    for p in self.preset.base_freq_curve.control_points]
            }
            
            # Convert and save as XML
            result = sine_preset_to_xml(preset_data, filepath)
            
            return result
        except Exception as e:
            QMessageBox.critical(self.parent(), "Error", f"Failed to export preset as XML: {str(e)}")
            return False
    
    def get_current_audio(self, sample_rate=44100):
        """
        Get the current audio data for preview or use in the main application.
        
        Returns:
            tuple: (audio_data, sample_rate)
        """
        return self.preset.generate_audio(sample_rate)


###############################################################################
# Integrated IsoFlicker Pro Application with SINE and Timeline Editors
###############################################################################
class IntegratedIsoFlickerApp(QMainWindow):
    """Main application that integrates both editors and the basic mode"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IsoFlicker Pro - Entrainment Toolkit")
        self.setGeometry(100, 100, 1000, 800)
        self.worker_threads = []  # Keep track of worker threads
        self.setup_ui()
        
    def setup_ui(self):
        # Import needed widgets here to ensure they're available
        from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        from PyQt5.QtWidgets import QGroupBox, QComboBox, QSlider, QCheckBox
        
        # Create main tab widget
        self.tabs = QTabWidget()
        
        try:
            # Import the basic GUI
            from isoFlickerGUI import MainWindow as BasicModeWindow
            
            # Import the SINE editor
            from sine_widget import SineEditorWidget
            
            # Create the basic mode tab
            self.basic_mode = BasicModeWindow()
            self.basic_mode.original_window = self  # Set reference to main window
            # Auto-attach video to SINE editor when selected in Basic Mode
            try:
                self.basic_mode.video_selected.connect(self.on_basic_mode_video_selected)
            except Exception:
                pass
            
            # Create the SINE editor tab
            sine_container = QWidget()
            sine_layout = QVBoxLayout()
            self.sine_editor = SineEditorWidget()
            self.sine_editor.original_window = self  # Set reference to this window instead of basic_mode
            # Wrap editor in a scroll area to prevent oversized UI from hiding bottom controls
            from PyQt5.QtWidgets import QScrollArea
            sine_scroll = QScrollArea()
            sine_scroll.setWidgetResizable(True)
            sine_scroll.setWidget(self.sine_editor)
            sine_layout.addWidget(sine_scroll)
            sine_container.setLayout(sine_layout)
            
            # Add text overlay button
            overlay_btn = QPushButton("Manage Text Overlays")
            overlay_btn.clicked.connect(self.open_text_overlay_manager)
            sine_layout.addWidget(overlay_btn)
            
            # Add visual flicker settings
            visual_group = QGroupBox("Visual Flicker Settings")
            visual_layout = QVBoxLayout()
            
            # Flicker shape
            shape_layout = QHBoxLayout()
            shape_layout.addWidget(QLabel("Flicker Shape:"))
            self.flicker_shape_combo = QComboBox()
            self.flicker_shape_combo.addItems(["sine", "square"])
            shape_layout.addWidget(self.flicker_shape_combo)
            visual_layout.addLayout(shape_layout)
            
            # Duty cycle
            duty_layout = QHBoxLayout()
            duty_layout.addWidget(QLabel("Duty Cycle:"))
            self.duty_cycle_slider = QSlider(Qt.Horizontal)
            self.duty_cycle_slider.setRange(10, 90)
            self.duty_cycle_slider.setValue(50)
            self.duty_label = QLabel("50%")
            self.duty_cycle_slider.valueChanged.connect(lambda v: self.duty_label.setText(f"{v}%"))
            duty_layout.addWidget(self.duty_cycle_slider)
            duty_layout.addWidget(self.duty_label)
            visual_layout.addLayout(duty_layout)
            
            # Color cycling
            self.color_cycling_check = QCheckBox("Enable Color Cycling")
            visual_layout.addWidget(self.color_cycling_check)
            
            # Pattern overlay
            self.pattern_overlay_check = QCheckBox("Enable Pattern Overlay")
            visual_layout.addWidget(self.pattern_overlay_check)
            
            visual_group.setLayout(visual_layout)
            sine_layout.addWidget(visual_group)

            # Pro Editor tab (dark layout)
            self.pro_editor = ProEditorWidget()
            self.pro_editor.request_process.connect(self.on_pro_layout_process)

            # Add tabs
            self.tabs.addTab(self.basic_mode, "Basic Mode")
            self.tabs.addTab(sine_container, "SINE Editor")
            self.tabs.addTab(self.pro_editor, "Editor")
            
            # Add process buttons for each editor type (can be implemented in their respective widgets too)
            
            # Set the central widget
            self.setCentralWidget(self.tabs)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error setting up UI: {e}\n{error_details}")
            # Show error in UI
            from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_layout.addWidget(QLabel(f"Error initializing application:\n{str(e)}"))
            error_widget.setLayout(error_layout)
            self.setCentralWidget(error_widget)

    def on_basic_mode_video_selected(self, path):
        """Receive video selection from Basic Mode and attach to SINE editor preview."""
        try:
            if hasattr(self, 'sine_editor') and self.sine_editor and hasattr(self.sine_editor, 'set_attached_video'):
                # Mark origin as 'basic' to update link status
                try:
                    self.sine_editor.set_attached_video(path, origin='basic')
                except TypeError:
                    # Backward compatibility if method signature differs
                    self.sine_editor.set_attached_video(path)
        except Exception:
            pass

    def on_pro_layout_process(self, settings: dict):
        """Start processing from the Pro Editor layout."""
        try:
            video_path = settings.get('video_path') or ''
            if not video_path:
                video_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.mov *.mkv *.avi)")
                if not video_path:
                    return

            fmt_text = (settings.get('format') or 'mp4').lower()
            mode = 'h264' if 'mp4' in fmt_text else 'ffv1'

            # Ask output if not supplied
            output_path = settings.get('output_path') or ''
            if not output_path:
                base = os.path.splitext(os.path.basename(video_path))[0]
                ext = '.mp4' if mode == 'h264' else '.mkv'
                output_path, _ = QFileDialog.getSaveFileName(self, "Save Output", f"{base}_processed{ext}", "Video Files (*.mp4 *.mkv)")
                if not output_path:
                    return

            # Gather preset if editor loaded
            preset = None
            try:
                if hasattr(self, 'sine_editor') and self.sine_editor and hasattr(self.sine_editor, 'preset'):
                    preset = self.sine_editor.preset
            except Exception:
                preset = None

            # Build config for worker
            config = {
                "use_visual_entrainment": True,
                "visual_frequency": getattr(preset.entrainment_curve, 'get_value_at_time', lambda t: 10.0)(0) if preset else 10.0,
                "flicker_amplitude": max(0.05, min(1.0, float(settings.get('volume', 0.9)))) * 0.6,
                "use_audio_entrainment": True,
                "tone_frequency": getattr(preset.entrainment_curve, 'get_value_at_time', lambda t: 10.0)(0) if preset else 10.0,
                "tone_volume": max(0.05, min(1.0, float(settings.get('volume', 0.9)))),
                "carrier_frequency": getattr(preset.base_freq_curve, 'get_value_at_time', lambda t: 100.0)(0) if preset and hasattr(preset, 'base_freq_curve') else 100.0,
                "mix_with_original": True,
                "original_volume": 0.5,
                "preset": preset,
                "visual_type": "pulse",
            }

            worker = EnhancedFlickerWorker(
                video_path=video_path,
                output_path=output_path,
                mode=mode,
                config=config,
                isochronic_audio=None,
            )

            # Track and connect
            self.worker_threads.append(worker)
            worker.finished_signal.connect(lambda out: self.on_pro_process_complete(out, worker))
            worker.error_signal.connect(self.on_process_error)
            worker.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start processing: {str(e)}")

    def on_pro_process_complete(self, output_file, worker):
        if worker in self.worker_threads:
            self.worker_threads.remove(worker)
        QMessageBox.information(self, "Success", f"Video processed successfully.\nSaved to: {output_file}")
    
    def open_text_overlay_manager(self):
        """Open the text overlay manager dialog"""
        try:
            # Ensure the TextOverlayManager class is imported
            from text_overlay import TextOverlayManager, TextOverlay
            
            # Create a dialog to hold the manager
            dialog = QDialog(self)
            dialog.setWindowTitle("Text Overlay Manager")
            dialog.setMinimumSize(600, 400)
            
            # Create the manager widget
            layout = QVBoxLayout()
            manager = TextOverlayManager(dialog)
            layout.addWidget(manager)
            
            # If we have a SINE editor with a preset, load its overlays
            if hasattr(self, 'sine_editor') and hasattr(self.sine_editor, 'preset'):
                manager.set_overlays(self.sine_editor.preset.text_overlays)
            
            # Add buttons
            button_layout = QHBoxLayout()
            ok_btn = QPushButton("Apply")
            cancel_btn = QPushButton("Cancel")
            
            # Connect buttons
            ok_btn.clicked.connect(lambda: self.apply_text_overlays(manager.get_overlays(), dialog))
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec_()
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "Error", f"Failed to open text overlay manager: {str(e)}\n\n{error_details}")
    
    def apply_text_overlays(self, overlays, dialog):
        """Apply the text overlays to the current preset"""
        try:
            if hasattr(self, 'sine_editor') and hasattr(self.sine_editor, 'preset'):
                self.sine_editor.preset.text_overlays = overlays
                dialog.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply text overlays: {str(e)}")
            
    def process_with_timeline(self, options):
        """Process video with a SINE preset timeline.
        This method is called from the SINE editor tab.
        
        Args:
            options: Dictionary containing processing options
        """
        try:
            # Create default output filename based on preset name
            preset = options.get("preset")
            preset_name = preset.name if preset else "Timeline"
            
            # Get frequency from preset
            freq = None
            if preset and hasattr(preset, 'entrainment_curve') and preset.entrainment_curve.control_points:
                # Get the starting frequency from the preset
                freq = preset.entrainment_curve.control_points[0].value
            
            prefix = self.basic_mode.prefix_edit.text() if hasattr(self.basic_mode, 'prefix_edit') else "IsoFlicker"
            if not prefix:
                prefix = "IsoFlicker"
                
            default_name = f"{prefix}_{preset_name}_{freq:.1f}Hz" if freq else f"{prefix}_{preset_name}"
            
            # Get format from options or use default
            format_ext = options.get("format", "mp4").lower()
            if not format_ext.startswith('.'):
                format_ext = f".{format_ext}"
            
            # Get save location
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Processed Video", default_name, f"Video Files (*{format_ext})")
            
            if not output_path:
                return
                
            if hasattr(self.basic_mode, 'progress_bar'):
                self.basic_mode.progress_bar.setVisible(True)
                self.basic_mode.progress_bar.setValue(0)
            
            if hasattr(self.basic_mode, 'process_btn'):
                self.basic_mode.process_btn.setEnabled(False)
            
            # Configure processing options from SINE preset
            config = {
                "use_visual_entrainment": options.get("visual_entrainment", True),
                "visual_frequency": freq if freq else 10.0,
                "flicker_amplitude": options.get("visual_intensity", 0.5),
                
                "use_audio_entrainment": options.get("audio_entrainment", True),
                "tone_frequency": freq if freq else 10.0,
                "tone_volume": options.get("tone_volume", 0.8),
                
                "carrier_frequency": preset.base_freq_curve.get_value_at_time(0) if preset and hasattr(preset, 'base_freq_curve') else 100.0,
                "mix_with_original": True,
                "original_volume": options.get("audio_volume", 0.5),
                
                "external_audio": None,
                
                # Pass the full preset for advanced processing
                "preset": preset,
                "visual_type": options.get("visual_type", "pulse")
            }
            
            # Use enhanced processing worker
            worker_class = EnhancedFlickerWorker
            
            # Generate the isochronic audio for the preset
            audio_path = None
            
            # Generate the preset audio if the preset has audio generation capability
            if preset and hasattr(preset, 'generate_audio'):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    audio_path = tmp.name
                
                try:
                    # Generate audio from preset
                    audio_data, sample_rate = preset.generate_audio()
                    
                    # Write to temporary file
                    sf.write(audio_path, audio_data, sample_rate)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Audio Generation Warning",
                        f"Failed to generate audio from preset: {str(e)}\n"
                        "Processing will continue without custom audio."
                    )
                    if audio_path and os.path.exists(audio_path):
                        try:
                            os.unlink(audio_path)
                        except:
                            pass
                    audio_path = None
            
            # Create worker
            worker = worker_class(
                video_path=self.basic_mode.video_path,
                output_path=output_path,
                mode=self.basic_mode.format_combo.currentData() if hasattr(self.basic_mode, 'format_combo') else "h264",
                config=config,
                isochronic_audio=audio_path
            )
            
            # Keep track of the worker
            self.worker_threads.append(worker)
            
            # Connect signals
            if hasattr(self.basic_mode, 'progress_bar'):
                worker.progress_signal.connect(self.basic_mode.progress_bar.setValue)
            
            worker.finished_signal.connect(lambda output_file: self.on_timeline_process_complete(output_file, worker))
            worker.error_signal.connect(self.on_process_error)
            
            # Start the worker
            worker.start()
            
        except Exception as e:
            import traceback
            print(f"Error in process_with_timeline: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to start processing: {str(e)}")
            
            # Re-enable the process buttons
            if hasattr(self, 'basic_mode') and self.basic_mode:
                self.basic_mode.process_btn.setEnabled(True)
    
    def on_timeline_process_complete(self, output_file, worker):
        """Handle completion of timeline processing"""
        try:
            # Remove the worker from our tracked threads
            if worker in self.worker_threads:
                self.worker_threads.remove(worker)
                
            self.basic_mode.progress_bar.setVisible(False)
            self.basic_mode.process_btn.setEnabled(True)
            
            # Ask for optional compression
            compressed_msg = ""
            try:
                settings = CompressionDialog.show_dialog(self)
                if settings:
                    # Build target path
                    base, ext = os.path.splitext(output_file)
                    out_path = f"{base}_opt{ext}"

                    if settings.get('method') == 'quality':
                        ok = VideoOptimizer.optimize_file_size(
                            output_file, out_path,
                            target_size_mb=None,
                            quality=settings.get('quality', 'medium'),
                            audio_bitrate=settings.get('audio_bitrate', '192k')
                        )
                    else:
                        ok = VideoOptimizer.optimize_file_size(
                            output_file, out_path,
                            target_size_mb=settings.get('target_size_mb'),
                            quality='medium',
                            audio_bitrate=settings.get('audio_bitrate', '192k')
                        )
                    if ok:
                        compressed_msg = f"\nOptimized copy saved to: {out_path}"
            except Exception as ce:
                print(f"Compression step skipped due to error: {ce}")

            QMessageBox.information(
                self,
                "Success",
                f"Video processed successfully with timeline preset!\nSaved to: {output_file}{compressed_msg}"
            )
        except Exception as e:
            print(f"Error in on_timeline_process_complete: {e}")
            
    def on_process_error(self, error_msg):
        """Handle processing errors"""
        # Re-enable the process buttons
        if hasattr(self, 'basic_mode') and self.basic_mode:
            self.basic_mode.progress_bar.setVisible(False)
            self.basic_mode.process_btn.setEnabled(True)
            
        QMessageBox.critical(self, "Error", error_msg)

    def process_video_with_sine_preset(self, video_path, preset_path=None):
        """Process video with SINE preset"""
        if not preset_path:
            preset_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select SINE Preset",
                "",
                "SINE Presets (*.sin);;XML Presets (*.xml);;All Files (*)"
            )
            if not preset_path:
                return
        
        try:
            # Validate preset file
            is_valid, _fmt = validate_preset_file(preset_path)
            if not is_valid:
                raise ValueError("Selected preset file is not valid.")
            
            # Load preset
            if preset_path.lower().endswith('.xml'):
                preset = xml_to_sine_preset(preset_path)
            else:
                preset = SinePreset.load_from_file(preset_path)
            
            # Generate audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio_path = tmp.name
            try:
                audio_data, sr = preset.generate_audio()
                sf.write(audio_path, audio_data, sr)
            except Exception as ge:
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass
                raise ge
            
            # Ask for output location
            default_name = os.path.splitext(os.path.basename(video_path))[0] + "_sine.mp4"
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Processed Video", default_name, "Video Files (*.mp4 *.mkv *.mov)"
            )
            if not output_path:
                return

            # Process video
            worker = EnhancedFlickerWorker(
                video_path=video_path,
                output_path=output_path,
                mode="sine",
                config={
                    "preset": preset,
                    "use_visual_entrainment": True,
                    "visual_frequency": preset.entrainment_curve.get_value_at_time(0) if hasattr(preset, 'entrainment_curve') else 10.0,
                    "flicker_amplitude": 0.5,
                    "use_audio_entrainment": True,
                    "tone_frequency": preset.entrainment_curve.get_value_at_time(0) if hasattr(preset, 'entrainment_curve') else 10.0,
                    "tone_volume": 0.8,
                    "carrier_frequency": preset.base_freq_curve.get_value_at_time(0) if hasattr(preset, 'base_freq_curve') else 100.0,
                    "mix_with_original": True,
                    "original_volume": 0.5,
                    "visual_type": getattr(preset, 'visual_effect_type', 'pulse') or 'pulse'
                },
                isochronic_audio=audio_path
            )
            worker.start()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process video: {str(e)}")

###############################################################################
# Main function or entry point if running this file directly
###############################################################################
def main():
    """Main entry point for IsoFlicker Pro."""
    try:
        print("[+] Starting Integrated IsoFlicker Pro...")
        
        # Check for required files
        required_files = [
            "sine_widget.py",
            "sine_editor_with_xml.py",
            "text_overlay.py",
            "file_optimizer.py",
            "preset_converter.py",
            "isoFlickerGUI.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"Error: The following required files are missing: {', '.join(missing_files)}")
            return 1
        
        # Create the application
        app = QApplication(sys.argv)
        
        # Create the main window
        window = ModernMainWindow()
        window.show()

        # Run the event loop
        exec_method = getattr(app, 'exec', None)
        if callable(exec_method):
            return exec_method()
        return app.exec_()
        
    except ImportError as e:
        print(f"[!] Import Error: {e}")
        print("[!] Make sure all required libraries are installed")
        input("Press Enter to exit...")
        return 1
    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())


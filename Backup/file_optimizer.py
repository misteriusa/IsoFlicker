"""
File optimization utilities for IsoFlicker Pro
"""

import os
import sys
import tempfile
import subprocess
import math

class VideoOptimizer:
    """Helper class for optimizing video file sizes"""
    
    @staticmethod
    def estimate_bitrate(width, height, fps, target_quality="medium"):
        """
        Estimate an appropriate bitrate based on video dimensions and frame rate.
        
        Args:
            width (int): Video width in pixels
            height (int): Video height in pixels
            fps (float): Frames per second
            target_quality (str): Quality target ("low", "medium", "high", "very_high")
            
        Returns:
            int: Recommended bitrate in kbps
        """
        # Base bitrate factors for different quality targets
        quality_factors = {
            "low": 0.04,      # ~0.04 bits per pixel
            "medium": 0.08,   # ~0.08 bits per pixel
            "high": 0.12,     # ~0.12 bits per pixel
            "very_high": 0.20 # ~0.20 bits per pixel
        }
        
        # Default to medium if target_quality is not recognized
        factor = quality_factors.get(target_quality, quality_factors["medium"])
        
        # Calculate bits per pixel based on resolution and factor
        pixels_per_frame = width * height
        bits_per_pixel = factor
        
        # Calculate bitrate: pixels * bits_per_pixel * fps / 1000 (to get kbps)
        bitrate = int((pixels_per_frame * bits_per_pixel * fps) / 1000)
        
        # Ensure minimum and maximum sensible bitrates
        bitrate = max(500, min(bitrate, 20000))
        
        return bitrate
    
    @staticmethod
    def optimize_file_size(input_file, output_file, target_size_mb=None, quality="medium", audio_bitrate="192k"):
        """
        Optimize a video file to target a specific file size or quality level.
        
        Args:
            input_file (str): Path to input video file
            output_file (str): Path to save optimized output
            target_size_mb (float, optional): Target size in MB, or None to use quality-based approach
            quality (str): Quality target when not using target_size_mb ("low", "medium", "high", "very_high")
            audio_bitrate (str): Audio bitrate to use (e.g. "128k", "192k", "256k")
            
        Returns:
            bool: True if optimization was successful, False otherwise
        """
        try:
            # First, get video information from ffprobe
            probe_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0", 
                "-show_entries", "stream=width,height,r_frame_rate,duration", 
                "-of", "csv=p=0:s=,", input_file
            ]
            
            probe_output = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT)
            width, height, frame_rate, duration = probe_output.decode().strip().split(",")
            
            # Parse frame rate fraction (e.g. "30000/1001" -> ~29.97)
            if "/" in frame_rate:
                num, den = map(int, frame_rate.split("/"))
                fps = num / den
            else:
                fps = float(frame_rate)
            
            width = int(width)
            height = int(height)
            duration = float(duration)
            
            # Check if we need to target a specific file size
            if target_size_mb is not None:
                # Calculate available bits after accounting for audio
                audio_bits_per_second = int(audio_bitrate.rstrip("k")) * 1000
                total_bits = target_size_mb * 8 * 1024 * 1024  # Convert MB to bits
                audio_bits = audio_bits_per_second * duration
                available_bits = total_bits - audio_bits
                
                # Calculate required video bitrate
                video_bitrate = int(available_bits / duration)
                
                # Ensure minimum reasonable bitrate (500 kbps)
                video_bitrate = max(500 * 1000, video_bitrate)
                
                # Convert to kbps for ffmpeg
                video_bitrate_str = f"{video_bitrate // 1000}k"
            else:
                # Quality-based approach
                bitrate = VideoOptimizer.estimate_bitrate(width, height, fps, quality)
                video_bitrate_str = f"{bitrate}k"
            
            # Determine CRF value based on quality
            crf_values = {
                "low": 28,
                "medium": 23,
                "high": 18,
                "very_high": 14
            }
            crf = crf_values.get(quality, 23)
            
            # Determine preset based on quality
            presets = {
                "low": "fast",
                "medium": "medium",
                "high": "slow",
                "very_high": "slower"
            }
            preset = presets.get(quality, "medium")
            
            # Build the ffmpeg command
            out_cmd = [
                "ffmpeg", "-i", input_file,
                "-c:v", "libx264", "-crf", str(crf),
                "-preset", preset, "-b:v", video_bitrate_str,
                "-maxrate", f"{int(int(video_bitrate_str.rstrip('k')) * 1.5)}k",
                "-bufsize", f"{int(int(video_bitrate_str.rstrip('k')) * 2)}k",
                "-c:a", "aac", "-b:a", audio_bitrate,
                "-movflags", "+faststart",  # Optimize for web streaming
                "-y", output_file
            ]
            
            # Run the ffmpeg command
            subprocess.run(out_cmd, check=True)
            
            return True
        
        except Exception as e:
            print(f"Error in optimize_file_size: {e}")
            return False
    
    @staticmethod
    def replace_with_optimized(original_file, target_size_mb=None, quality="medium"):
        """
        Replace the original file with an optimized version.
        
        Args:
            original_file (str): Path to the file to optimize
            target_size_mb (float, optional): Target size in MB, or None to use quality-based approach
            quality (str): Quality target when not using target_size_mb
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create temporary directory for the optimized file
            temp_dir = tempfile.mkdtemp()
            base_name = os.path.basename(original_file)
            temp_output = os.path.join(temp_dir, f"opt_{base_name}")
            
            # Optimize the file
            success = VideoOptimizer.optimize_file_size(
                original_file, temp_output, target_size_mb, quality
            )
            
            if success:
                # Replace the original file
                os.unlink(original_file)
                os.rename(temp_output, original_file)
                os.rmdir(temp_dir)
                return True
            else:
                # Clean up if optimization failed
                if os.path.exists(temp_output):
                    os.unlink(temp_output)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                return False
                
        except Exception as e:
            print(f"Error in replace_with_optimized: {e}")
            return False

class CompressionDialog:
    """
    Helper class to show a compression dialog using PyQt5.
    This must be instantiated after the application is created.
    """
    
    @staticmethod
    def show_dialog(parent_widget):
        """
        Show a dialog to get compression settings.
        
        Args:
            parent_widget: Parent widget for the dialog
            
        Returns:
            dict: Compression settings or None if canceled
        """
        try:
            from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                       QLabel, QComboBox, QSpinBox, QCheckBox, 
                                       QDialogButtonBox, QGroupBox, QRadioButton)
            from PyQt5.QtCore import Qt
            
            dialog = QDialog(parent_widget)
            dialog.setWindowTitle("Video Compression Settings")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout()
            
            # Compression method
            method_group = QGroupBox("Compression Method")
            method_layout = QVBoxLayout()
            
            quality_radio = QRadioButton("Quality-based (recommended)")
            quality_radio.setChecked(True)
            method_layout.addWidget(quality_radio)
            
            size_radio = QRadioButton("Target specific file size")
            method_layout.addWidget(size_radio)
            
            method_group.setLayout(method_layout)
            layout.addWidget(method_group)
            
            # Quality settings
            quality_group = QGroupBox("Quality Settings")
            quality_layout = QHBoxLayout()
            
            quality_layout.addWidget(QLabel("Quality Level:"))
            quality_combo = QComboBox()
            quality_combo.addItems(["Low", "Medium", "High", "Very High"])
            quality_combo.setCurrentIndex(1)  # Default to Medium
            quality_layout.addWidget(quality_combo)
            
            quality_group.setLayout(quality_layout)
            layout.addWidget(quality_group)
            
            # Target size settings
            size_group = QGroupBox("Target Size")
            size_layout = QHBoxLayout()
            
            size_layout.addWidget(QLabel("Target File Size:"))
            size_spin = QSpinBox()
            size_spin.setRange(10, 10000)  # 10MB to 10GB
            size_spin.setValue(100)  # Default 100MB
            size_spin.setSuffix(" MB")
            size_layout.addWidget(size_spin)
            
            size_group.setLayout(size_layout)
            size_group.setEnabled(False)  # Disabled initially
            layout.addWidget(size_group)
            
            # Audio settings
            audio_group = QGroupBox("Audio Settings")
            audio_layout = QHBoxLayout()
            
            audio_layout.addWidget(QLabel("Audio Quality:"))
            audio_combo = QComboBox()
            audio_combo.addItems(["Low (128 kbps)", "Medium (192 kbps)", "High (256 kbps)"])
            audio_combo.setCurrentIndex(1)  # Default to Medium
            audio_layout.addWidget(audio_combo)
            
            audio_group.setLayout(audio_layout)
            layout.addWidget(audio_group)
            
            # Add option to apply to all future exports
            remember_check = QCheckBox("Remember these settings for this session")
            remember_check.setChecked(False)
            layout.addWidget(remember_check)
            
            # Connect radio buttons to enable/disable appropriate groups
            quality_radio.toggled.connect(lambda checked: quality_group.setEnabled(checked))
            size_radio.toggled.connect(lambda checked: size_group.setEnabled(checked))
            
            # Buttons
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            # Show dialog and get result
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Return settings based on selected options
                if quality_radio.isChecked():
                    # Quality-based compression
                    quality_map = {
                        0: "low",
                        1: "medium",
                        2: "high", 
                        3: "very_high"
                    }
                    
                    audio_bitrate_map = {
                        0: "128k",
                        1: "192k",
                        2: "256k"
                    }
                    
                    return {
                        "method": "quality",
                        "quality": quality_map[quality_combo.currentIndex()],
                        "audio_bitrate": audio_bitrate_map[audio_combo.currentIndex()],
                        "remember": remember_check.isChecked()
                    }
                else:
                    # Size-based compression
                    audio_bitrate_map = {
                        0: "128k",
                        1: "192k",
                        2: "256k"
                    }
                    
                    return {
                        "method": "size",
                        "target_size_mb": size_spin.value(),
                        "audio_bitrate": audio_bitrate_map[audio_combo.currentIndex()],
                        "remember": remember_check.isChecked()
                    }
            else:
                return None
                
        except Exception as e:
            print(f"Error in CompressionDialog.show_dialog: {e}")
            return None

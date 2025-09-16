import sys
import os
import math
import numpy as np
import librosa
import soundfile as sf
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QProgressBar, QMessageBox, QTabWidget,
    QGroupBox, QLineEdit, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
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
import traceback

# Import our refactored video processor
from core.video_processor import generate_isochronic_tone, detect_isochronic_frequency, BaseVideoProcessor


class FlickerWorker(BaseVideoProcessor):
    """Worker class for flicker processing (now inherits from BaseVideoProcessor)"""
    pass

class MainWindow(QMainWindow):
    # Emit when a user selects a video in Basic Mode
    video_selected = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.video_path = ""
        self.audio_path = ""
        self.detected_freq = 0.0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("IsoFlicker Pro - Video & Audio Entrainment Generator")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        
        # File selection tab
        file_tab = QWidget()
        file_layout = QVBoxLayout()
        
        # Video controls
        video_group = QGroupBox("Video Selection")
        video_layout = QHBoxLayout()
        
        self.video_label = QLabel("No video file selected")
        self.video_btn = QPushButton("Select Video File")
        self.video_btn.clicked.connect(self.choose_video)
        
        video_layout.addWidget(self.video_label)
        video_layout.addWidget(self.video_btn)
        video_group.setLayout(video_layout)
        file_layout.addWidget(video_group)
        
        # Optional audio input
        audio_group = QGroupBox("External Audio (Optional)")
        audio_layout = QHBoxLayout()
        
        self.audio_label = QLabel("No audio file selected")
        self.audio_btn = QPushButton("Select Audio File")
        self.audio_btn.clicked.connect(self.choose_audio)
        self.clear_audio_btn = QPushButton("Clear")
        self.clear_audio_btn.clicked.connect(self.clear_audio)
        
        audio_layout.addWidget(self.audio_label)
        audio_layout.addWidget(self.audio_btn)
        audio_layout.addWidget(self.clear_audio_btn)
        audio_group.setLayout(audio_layout)
        file_layout.addWidget(audio_group)
        
        file_tab.setLayout(file_layout)
        
        # Entrainment settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        
        # Visual entrainment settings
        visual_group = QGroupBox("Visual Entrainment")
        visual_layout = QVBoxLayout()
        
        self.use_visual_check = QCheckBox("Enable Visual Entrainment")
        self.use_visual_check.setChecked(True)
        
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency (Hz):"))
        self.visual_freq_spin = QDoubleSpinBox()
        self.visual_freq_spin.setRange(0.5, 40.0)
        self.visual_freq_spin.setValue(10.0)
        self.visual_freq_spin.setSingleStep(0.5)
        freq_layout.addWidget(self.visual_freq_spin)
        
        amp_layout = QHBoxLayout()
        amp_layout.addWidget(QLabel("Flicker Strength:"))
        self.flicker_amp_slider = QSlider(Qt.Horizontal)
        self.flicker_amp_slider.setRange(1, 50)
        self.flicker_amp_slider.setValue(10)
        self.flicker_amp_value = QLabel("0.10")
        self.flicker_amp_slider.valueChanged.connect(self.update_flicker_amp_label)
        amp_layout.addWidget(self.flicker_amp_slider)
        amp_layout.addWidget(self.flicker_amp_value)
        
        visual_layout.addWidget(self.use_visual_check)
        visual_layout.addLayout(freq_layout)
        visual_layout.addLayout(amp_layout)
        visual_group.setLayout(visual_layout)
        settings_layout.addWidget(visual_group)
        
        # Audio entrainment settings
        audio_group = QGroupBox("Audio Entrainment")
        audio_layout = QVBoxLayout()
        
        self.use_audio_check = QCheckBox("Enable Audio Entrainment")
        self.use_audio_check.setChecked(True)
        
        tone_freq_layout = QHBoxLayout()
        tone_freq_layout.addWidget(QLabel("Tone Frequency (Hz):"))
        self.tone_freq_spin = QDoubleSpinBox()
        self.tone_freq_spin.setRange(0.5, 40.0)
        self.tone_freq_spin.setValue(10.0)
        self.tone_freq_spin.setSingleStep(0.5)
        tone_freq_layout.addWidget(self.tone_freq_spin)
        
        carrier_freq_layout = QHBoxLayout()
        carrier_freq_layout.addWidget(QLabel("Carrier Frequency (Hz):"))
        self.carrier_freq_spin = QDoubleSpinBox()
        self.carrier_freq_spin.setRange(20.0, 1000.0)
        self.carrier_freq_spin.setValue(100.0)  # Default to 100Hz
        self.carrier_freq_spin.setSingleStep(10.0)
        carrier_freq_layout.addWidget(self.carrier_freq_spin)
        
        # Sync frequencies checkbox
        self.sync_freq_check = QCheckBox("Synchronize Audio and Visual Frequencies")
        self.sync_freq_check.setChecked(True)
        self.sync_freq_check.stateChanged.connect(self.sync_frequencies)
        
        # Volume controls
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Tone Volume:"))
        self.tone_volume_slider = QSlider(Qt.Horizontal)
        self.tone_volume_slider.setRange(1, 100)
        self.tone_volume_slider.setValue(50)
        self.tone_volume_value = QLabel("0.50")
        self.tone_volume_slider.valueChanged.connect(self.update_tone_volume_label)
        volume_layout.addWidget(self.tone_volume_slider)
        volume_layout.addWidget(self.tone_volume_value)
        
        # Original audio mixing options
        self.mix_original_check = QCheckBox("Mix with Original Audio")
        self.mix_original_check.setChecked(True)
        
        orig_volume_layout = QHBoxLayout()
        orig_volume_layout.addWidget(QLabel("Original Audio Volume:"))
        self.orig_volume_slider = QSlider(Qt.Horizontal)
        self.orig_volume_slider.setRange(1, 100)
        self.orig_volume_slider.setValue(30)
        self.orig_volume_value = QLabel("0.30")
        self.orig_volume_slider.valueChanged.connect(self.update_orig_volume_label)
        orig_volume_layout.addWidget(self.orig_volume_slider)
        orig_volume_layout.addWidget(self.orig_volume_value)
        
        audio_layout.addWidget(self.use_audio_check)
        audio_layout.addLayout(tone_freq_layout)
        audio_layout.addLayout(carrier_freq_layout)
        audio_layout.addWidget(self.sync_freq_check)
        audio_layout.addLayout(volume_layout)
        audio_layout.addWidget(self.mix_original_check)
        audio_layout.addLayout(orig_volume_layout)
        audio_group.setLayout(audio_layout)
        settings_layout.addWidget(audio_group)
        
        settings_tab.setLayout(settings_layout)
        
        # Add tabs to tab widget
        tabs.addTab(file_tab, "Files")
        tabs.addTab(settings_tab, "Entrainment Settings")
        
        main_layout.addWidget(tabs)
        
        # Output format and processing
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("H.264 MP4 (Compatible)", "h264")
        self.format_combo.addItem("FFV1 MKV (Lossless)", "ffv1")
        format_layout.addWidget(self.format_combo)
        
        # Filename prefix
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Filename Prefix:"))
        self.prefix_edit = QLineEdit("IsoFlicker")
        prefix_layout.addWidget(self.prefix_edit)
        
        output_layout.addLayout(format_layout)
        output_layout.addLayout(prefix_layout)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Process button and progress bar
        process_layout = QHBoxLayout()
        self.process_btn = QPushButton("Process Video")
        self.process_btn.clicked.connect(self.process_video)
        self.process_btn.setEnabled(False)
        process_layout.addWidget(self.process_btn)
        
        main_layout.addLayout(process_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def update_flicker_amp_label(self):
        value = self.flicker_amp_slider.value() / 100
        self.flicker_amp_value.setText(f"{value:.2f}")
        
    def update_tone_volume_label(self):
        value = self.tone_volume_slider.value() / 100
        self.tone_volume_value.setText(f"{value:.2f}")
        if self.sync_freq_check.isChecked():
            self.visual_freq_spin.setValue(self.tone_freq_spin.value())
        
    def update_orig_volume_label(self):
        value = self.orig_volume_slider.value() / 100
        self.orig_volume_value.setText(f"{value:.2f}")
        
    def sync_frequencies(self, state):
        if state == Qt.Checked:
            self.visual_freq_spin.setValue(self.tone_freq_spin.value())
            
    def choose_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File",
            "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        
        if file_path:
            self.video_path = file_path
            self.video_label.setText(f"Video: {os.path.basename(file_path)}")
            self.update_process_button()
            # Notify listeners (e.g., SINE Editor) about the selected video
            try:
                self.video_selected.emit(file_path)
            except Exception:
                pass

    def choose_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File",
            "", "Audio Files (*.wav *.mp3 *.flac *.ogg)")
        
        if file_path:
            self.audio_path = file_path
            self.audio_label.setText(f"Audio: {os.path.basename(file_path)}")
            
            self.detected_freq = detect_isochronic_frequency(file_path)
            
            # Ask user if they want to use detected frequency
            if self.detected_freq > 0:
                reply = QMessageBox.question(
                    self, 
                    "Detected Frequency", 
                    f"Detected frequency: {self.detected_freq:.2f} Hz\nUse this frequency for entrainment?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.tone_freq_spin.setValue(self.detected_freq)
                    if self.sync_freq_check.isChecked():
                        self.visual_freq_spin.setValue(self.detected_freq)
    
    def clear_audio(self):
        self.audio_path = ""
        self.audio_label.setText("No audio file selected")

    def update_process_button(self):
        self.process_btn.setEnabled(bool(self.video_path))

    def get_config(self):
        """Get the current configuration settings"""
        config = {
            "use_visual_entrainment": self.use_visual_check.isChecked(),
            "visual_frequency": self.visual_freq_spin.value(),
            "flicker_amplitude": self.flicker_amp_slider.value() / 100,
            
            "use_audio_entrainment": self.use_audio_check.isChecked(),
            "tone_frequency": self.tone_freq_spin.value(),
            "tone_volume": self.tone_volume_slider.value() / 100,
            
            "carrier_frequency": self.carrier_freq_spin.value(),
            "mix_with_original": self.mix_original_check.isChecked(),
            "original_volume": self.orig_volume_slider.value() / 100,
            
            "external_audio": self.audio_path if self.audio_path else None
        }
        return config

    def process_video(self):
        # Create default output filename based on settings
        prefix = self.prefix_edit.text() or "IsoFlicker"
        freq = self.tone_freq_spin.value() if self.use_audio_check.isChecked() else self.visual_freq_spin.value()
        default_name = f"{prefix}_{freq:.1f}Hz"
        
        # Get save location
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output Video", default_name, "Video Files (*.mp4 *.mkv)")
        
        if not output_path:
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        
        config = self.get_config()
        
        self.worker = FlickerWorker(
            self.video_path,
            output_path,
            self.format_combo.currentData(),
            config
        )
        
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_process_complete)
        self.worker.error_signal.connect(self.on_process_error)
        self.worker.start()

    def on_process_complete(self, output_file):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        QMessageBox.information(self, "Success",
                              f"Video processed successfully!\nSaved to: {output_file}")

    def on_process_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", error_msg)
        
        # Add this method to the MainWindow class in your isoFlickerGUI.py file
# This should be placed inside the MainWindow class definition, 
# alongside other methods like process_video, choose_video, etc.

def process_with_timeline(self, options):
    """
    Process video with a SINE preset timeline.
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
        
        prefix = self.prefix_edit.text() if hasattr(self, 'prefix_edit') else "IsoFlicker"
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
            
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
        
        if hasattr(self, 'process_btn'):
            self.process_btn.setEnabled(False)
        
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
        
        # Use enhanced processing worker if available
        worker_class = None
        
        # Try to import EnhancedFlickerWorker (but fallback to regular FlickerWorker)
        try:
            from integrated_isoflicker import EnhancedFlickerWorker
            worker_class = EnhancedFlickerWorker
        except ImportError:
            worker_class = FlickerWorker
        
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
                import soundfile as sf
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
        self.worker = worker_class(
            video_path=self.video_path,
            output_path=output_path,
            mode=self.format_combo.currentData() if hasattr(self, 'format_combo') else "h264",
            config=config,
            isochronic_audio=audio_path
        )
        
        # Connect signals
        if hasattr(self, 'progress_bar'):
            self.worker.progress_signal.connect(self.progress_bar.setValue)
        
        self.worker.finished_signal.connect(lambda output_file: self.on_timeline_process_complete(output_file, audio_path))
        self.worker.error_signal.connect(self.on_process_error)
        
        # Start the worker
        self.worker.start()
        
    except Exception as e:
        import traceback
        QMessageBox.critical(
            self,
            "Processing Error",
            f"Error starting processing: {str(e)}\n\n{traceback.format_exc()}"
        )
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        if hasattr(self, 'process_btn'):
            self.process_btn.setEnabled(True)

def on_timeline_process_complete(self, output_file, temp_audio_path=None):
    """Handle completion of timeline processing"""
    # Clean up temporary audio file
    if temp_audio_path and os.path.exists(temp_audio_path):
        try:
            os.unlink(temp_audio_path)
        except Exception as e:
            print(f"Warning: Failed to clean up temporary audio file: {e}")
    
    # Show completion message and reset UI
    if hasattr(self, 'progress_bar'):
        self.progress_bar.setVisible(False)
    if hasattr(self, 'process_btn'):
        self.process_btn.setEnabled(True)
    
    QMessageBox.information(
        self,
        "Success",
        f"Video processed successfully!\nSaved to: {output_file}"
    )

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == '__main__':
    main()

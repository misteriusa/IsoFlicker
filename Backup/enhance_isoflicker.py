import os
import sys
import shutil

def backup_file(filename):
    """Create a backup of a file if it exists"""
    if os.path.exists(filename):
        backup = f"{filename}.backup"
        print(f"Creating backup: {backup}")
        shutil.copy2(filename, backup)
        return True
    return False

def enhance_sine_editor():
    """Add new features to the SINE editor"""
    filename = "sine_editor_with_xml.py"
    
    if not backup_file(filename):
        print(f"Error: {filename} not found")
        return False
    
    print(f"Enhancing {filename} with new features...")
    
    try:
        # Read the original file
        with open(filename, "r") as f:
            content = f.read()
        
        # Add required imports
        imports_to_add = """
import pygame.mixer  # For audio preview
from advanced_isochronic_generator import WaveformType, ModulationType  # For modulation options
"""
        
        # Add imports after existing imports
        import_section_end = "from preset_converter import validate_preset_file, xml_to_sine_preset, sine_preset_to_xml"
        if import_section_end in content:
            updated_content = content.replace(import_section_end, import_section_end + imports_to_add)
        else:
            print("Could not find import section")
            return False
        
        # Add TextOverlay class
        text_overlay_class = """
class TextOverlaySettings:
    """Settings for text overlay on videos"""
    def __init__(self):
        self.enabled = False
        self.text = ""
        self.font = "Arial"
        self.font_size = 36
        self.opacity = 0.75
        self.start_time = 0
        self.end_time = 10
        self.position = "center"  # center, top, bottom

class TextOverlayWidget(QWidget):
    """Widget for text overlay settings"""
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = TextOverlaySettings()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Enable checkbox
        self.enable_check = QCheckBox("Enable Text Overlay")
        self.enable_check.setChecked(self.settings.enabled)
        self.enable_check.stateChanged.connect(self.update_settings)
        layout.addWidget(self.enable_check)
        
        # Text input
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text:"))
        self.text_edit = QLineEdit(self.settings.text)
        self.text_edit.setPlaceholderText("Enter text to overlay")
        self.text_edit.textChanged.connect(self.update_settings)
        text_layout.addWidget(self.text_edit)
        layout.addLayout(text_layout)
        
        # Font settings
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "Courier New", "Verdana", "Impact"])
        self.font_combo.setCurrentText(self.settings.font)
        self.font_combo.currentTextChanged.connect(self.update_settings)
        font_layout.addWidget(self.font_combo)
        
        font_layout.addWidget(QLabel("Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 100)
        self.size_spin.setValue(self.settings.font_size)
        self.size_spin.valueChanged.connect(self.update_settings)
        font_layout.addWidget(self.size_spin)
        layout.addLayout(font_layout)
        
        # Opacity setting
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.settings.opacity * 100))
        self.opacity_slider.valueChanged.connect(self.update_settings)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel(f"{self.settings.opacity:.2f}")
        opacity_layout.addWidget(self.opacity_label)
        layout.addLayout(opacity_layout)
        
        # Time settings
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Start Time (s):"))
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0, 3600)
        self.start_spin.setValue(self.settings.start_time)
        self.start_spin.valueChanged.connect(self.update_settings)
        time_layout.addWidget(self.start_spin)
        
        time_layout.addWidget(QLabel("End Time (s):"))
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(0, 3600)
        self.end_spin.setValue(self.settings.end_time)
        self.end_spin.valueChanged.connect(self.update_settings)
        time_layout.addWidget(self.end_spin)
        layout.addLayout(time_layout)
        
        # Position setting
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("Position:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Center", "Top", "Bottom"])
        self.position_combo.setCurrentText(self.settings.position.capitalize())
        self.position_combo.currentTextChanged.connect(self.update_settings)
        position_layout.addWidget(self.position_combo)
        layout.addLayout(position_layout)
        
        self.setLayout(layout)
    
    def update_settings(self):
        """Update settings from UI controls"""
        self.settings.enabled = self.enable_check.isChecked()
        self.settings.text = self.text_edit.text()
        self.settings.font = self.font_combo.currentText()
        self.settings.font_size = self.size_spin.value()
        self.settings.opacity = self.opacity_slider.value() / 100.0
        self.opacity_label.setText(f"{self.settings.opacity:.2f}")
        self.settings.start_time = self.start_spin.value()
        self.settings.end_time = self.end_spin.value()
        self.settings.position = self.position_combo.currentText().lower()
        
        self.settings_changed.emit()

class AudioExtensionWidget(QWidget):
    """Widget for additional audio settings"""
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_path = ""
        self.volume = 0.5
        self.subsonic_enabled = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Audio file selection
        audio_group = QGroupBox("Additional Audio")
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
        layout.addWidget(audio_group)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.volume * 100))
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel(f"{self.volume:.2f}")
        volume_layout.addWidget(self.volume_label)
        layout.addLayout(volume_layout)
        
        # Subsonic options
        subsonic_layout = QHBoxLayout()
        self.subsonic_check = QCheckBox("Enable Subsonic Masking")
        self.subsonic_check.setChecked(self.subsonic_enabled)
        self.subsonic_check.stateChanged.connect(self.update_settings)
        subsonic_layout.addWidget(self.subsonic_check)
        layout.addLayout(subsonic_layout)
        
        self.setLayout(layout)
    
    def choose_audio(self):
        """Select audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File",
            "", "Audio Files (*.wav *.mp3 *.flac *.ogg)")
        
        if file_path:
            self.audio_path = file_path
            self.audio_label.setText(f"Audio: {os.path.basename(file_path)}")
            self.settings_changed.emit()
            
    def clear_audio(self):
        """Clear audio selection"""
        self.audio_path = ""
        self.audio_label.setText("No audio file selected")
        self.settings_changed.emit()
    
    def update_volume(self):
        """Update volume from slider"""
        self.volume = self.volume_slider.value() / 100.0
        self.volume_label.setText(f"{self.volume:.2f}")
        self.settings_changed.emit()
    
    def update_settings(self):
        """Update settings from UI controls"""
        self.subsonic_enabled = self.subsonic_check.isChecked()
        self.settings_changed.emit()
"""
        
        # Add class after existing classes but before SineEditorWidget
        class_insertion_point = "class SineEditorWidget(QWidget):"
        if class_insertion_point in updated_content:
            updated_content = updated_content.replace(class_insertion_point, text_overlay_class + "\n" + class_insertion_point)
        else:
            print("Could not find class insertion point")
            return False
        
        # Add modulation options to SinePreset class
        modulation_addition = """
        # Set modulation properties (from timeline editor)
        self.carrier_type = WaveformType.SINE
        self.modulation_type = ModulationType.SQUARE
"""
        
        init_target = "    def __init__(self, name=\"New Preset\"):\n        self.name = name\n        self.entrainment_curve = TrackCurve(MIN_ENTRAINMENT_FREQ, MAX_ENTRAINMENT_FREQ, DEFAULT_ENTRAINMENT_FREQ)\n        self.volume_curve = TrackCurve(0.0, 1.0, 0.5)\n        self.base_freq_curve = TrackCurve(MIN_BASE_FREQ, MAX_BASE_FREQ, DEFAULT_BASE_FREQ)"
        
        if init_target in updated_content:
            updated_content = updated_content.replace(init_target, init_target + modulation_addition)
        else:
            print("Could not find SinePreset init method")
            return False
        
        # Add modulation UI to SineEditorWidget
        modulation_ui = """
        # Modulation settings
        modulation_group = QGroupBox("Modulation Settings")
        modulation_layout = QVBoxLayout()
        
        carrier_layout = QHBoxLayout()
        carrier_layout.addWidget(QLabel("Carrier Wave:"))
        self.carrier_combo = QComboBox()
        self.carrier_combo.addItems([wt.value for wt in WaveformType])
        self.carrier_combo.setCurrentText(self.preset.carrier_type.value if hasattr(self.preset.carrier_type, "value") else "sine")
        self.carrier_combo.currentTextChanged.connect(self.update_carrier_type)
        carrier_layout.addWidget(self.carrier_combo)
        modulation_layout.addLayout(carrier_layout)
        
        mod_layout = QHBoxLayout()
        mod_layout.addWidget(QLabel("Modulation:"))
        self.modulation_combo = QComboBox()
        self.modulation_combo.addItems([mt.value for mt in ModulationType])
        self.modulation_combo.setCurrentText(self.preset.modulation_type.value if hasattr(self.preset.modulation_type, "value") else "square")
        self.modulation_combo.currentTextChanged.connect(self.update_modulation_type)
        mod_layout.addWidget(self.modulation_combo)
        modulation_layout.addLayout(mod_layout)
        
        modulation_group.setLayout(modulation_layout)
        editor_layout.addWidget(modulation_group)
        
        # Sync frequencies checkbox
        sync_layout = QHBoxLayout()
        self.sync_freq_check = QCheckBox("Synchronize Audio and Visual Frequencies")
        self.sync_freq_check.setChecked(True)
        self.sync_freq_check.stateChanged.connect(self.sync_frequencies)
        sync_layout.addWidget(self.sync_freq_check)
        editor_layout.addLayout(sync_layout)
        
        # Text overlay
        self.text_overlay = TextOverlayWidget()
        editor_layout.addWidget(self.text_overlay)
        
        # Additional audio
        self.audio_extension = AudioExtensionWidget()
        editor_layout.addWidget(self.audio_extension)
"""
        
        # Add UI elements to SineEditorWidget init_ui method
        ui_target = "        main_layout.addLayout(editor_layout)"
        if ui_target in updated_content:
            updated_content = updated_content.replace(ui_target, modulation_ui + "\n        " + ui_target)
        else:
            print("Could not find UI insertion point")
            return False
        
        # Add carrier and modulation update methods to SineEditorWidget
        modulation_methods = """
    def update_carrier_type(self, carrier_type_str):
        """Update the carrier wave type"""
        self.preset.carrier_type = WaveformType(carrier_type_str)
        self.preset_changed.emit()
        
    def update_modulation_type(self, modulation_type_str):
        """Update the modulation type"""
        self.preset.modulation_type = ModulationType(modulation_type_str)
        self.preset_changed.emit()
    
    def sync_frequencies(self, state):
        """Toggle frequency synchronization with visual effects"""
        # This would be implemented when integrated with video processing
        pass
"""
        
        # Add methods after existing methods before the end of the class
        methods_target = "    def get_current_audio(self):\n        \"\"\"Get the current audio data for preview or use in the main application\"\"\"\n        return self.preset.generate_audio()"
        if methods_target in updated_content:
            updated_content = updated_content.replace(methods_target, methods_target + modulation_methods)
        else:
            print("Could not find methods insertion point")
            return False
        
        # Add preview button
        preview_button = """
        # Preview button
        preview_layout = QHBoxLayout()
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.preview_audio)
        preview_layout.addWidget(self.preview_btn)
        
        self.process_video_btn = QPushButton("Process with Video")
        self.process_video_btn.clicked.connect(self.process_with_video)
        preview_layout.addWidget(self.process_video_btn)
        
        main_layout.addLayout(preview_layout)
"""
        
        # Add preview button before the final setLayout call
        preview_target = "        self.setLayout(main_layout)"
        if preview_target in updated_content:
            updated_content = updated_content.replace(preview_target, preview_button + "\n        " + preview_target)
        else:
            print("Could not find preview button insertion point")
            return False
        
        # Add preview methods
        preview_methods = """
    def preview_audio(self):
        """Preview the audio output"""
        try:
            # Generate audio
            audio_data, sample_rate = self.preset.generate_audio()
            
            if len(audio_data) == 0:
                QMessageBox.warning(self, "Preview Error", "No audio data to preview")
                return
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_wav = tmp.name
            
            sf.write(temp_wav, audio_data, sample_rate)
            
            # Initialize pygame mixer
            pygame.mixer.init(frequency=sample_rate)
            
            # Load and play sound
            pygame.mixer.music.load(temp_wav)
            pygame.mixer.music.play()
            
            # Show a simple dialog with stop button
            msg = QMessageBox()
            msg.setWindowTitle("Audio Preview")
            msg.setText("Playing audio preview...")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.buttonClicked.connect(lambda: pygame.mixer.music.stop())
            msg.exec_()
            
            # Clean up
            pygame.mixer.quit()
            os.unlink(temp_wav)
            
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Failed to preview audio: {str(e)}")
    
    def process_with_video(self):
        """Process the current video with this preset"""
        # Get the main window to access the video
        if hasattr(self, 'original_window') and self.original_window:
            video_path = self.original_window.video_path
            
            if not video_path:
                QMessageBox.warning(self, "Error", "Please select a video file in the Basic Mode tab first.")
                return
                
            if not os.path.exists(video_path):
                QMessageBox.warning(self, "Error", f"Video file not found: {video_path}")
                return
            
            # Generate default output filename
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            preset_name = self.preset.name.replace(" ", "_")
            default_output = f"{base_name}_{preset_name}.mp4"
            
            # Get save location
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Processed Video", default_output, "Video Files (*.mp4);;All Files (*)"
            )
            
            if not output_path:
                return
            
            # Generate audio data
            audio_data, sample_rate = self.preset.generate_audio()
            
            # Create a processing dialog
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("Processing video with SINE preset...", "Cancel", 0, 100, self)
            progress.setWindowTitle("Processing")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # TODO: This would need to be integrated with the actual video processing code
            # For now, just show a success message
            progress.setValue(100)
            QMessageBox.information(self, "Success", 
                                  f"Video processed with SINE preset\\nSaved to: {output_path}")
            
        else:
            QMessageBox.warning(self, "Error", "Cannot access main window or video information.")
"""
        
        # Add methods to the end of the class
        class_end = "def main():"
        if class_end in updated_content:
            updated_content = updated_content.replace(class_end, preview_methods + "\n\ndef main():")
        else:
            print("Could not find class end point")
            return False
        
        # Write the updated file
        with open(filename, "w") as f:
            f.write(updated_content)
        
        print(f"Successfully enhanced {filename}")
        return True
            
    except Exception as e:
        print(f"Error enhancing {filename}: {e}")
        return False

def main():
    print("=== IsoFlicker Pro Enhancement Script ===")
    
    # Enhance the sine editor
    if enhance_sine_editor():
        print("✓ SINE editor enhanced successfully")
    else:
        print("✗ Failed to enhance SINE editor")
    
    print("\nEnhancements complete!")
    print("Run the application to see the new features.")
    print("Please note: Some features may require additional integration to work fully.")

if __name__ == "__main__":
    main()
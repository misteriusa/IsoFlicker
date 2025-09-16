from PyQt5.QtCore import Qt, QPoint, QRect, QSize, QEvent, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QGroupBox, QListWidget, QFrame,
    QMenu, QAction, QMessageBox, QLineEdit, QDialog, QDialogButtonBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QRadioButton, QComboBox, QTabWidget
)
import numpy as np
import math
import soundfile as sf
import tempfile
import os
import threading

# Safe MoviePy import for local duration lookups
try:
    from moviepy.editor import VideoFileClip  # type: ignore
except Exception:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip  # type: ignore
    except Exception:
        VideoFileClip = None  # Will be checked at call sites

# Import from integrated_isoflicker instead of sine_editor_with_xml
from integrated_isoflicker import SinePreset, ControlPoint, Curve
from sine_editor_with_xml import CurveEditor, NameDialog, ExportSettingsDialog
from preset_converter import sine_preset_to_xml

# Define QPlaybackFinishedEvent since we're not importing it anymore
class QPlaybackFinishedEvent(QEvent):
    def __init__(self):
        super().__init__(QEvent.Type(QEvent.User + 1))

# Try to import visual preview or create a placeholder
try:
    from visual_preview import VisualPreviewWidget
except ImportError:
    # Create a placeholder if not available
    class VisualPreviewWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(100)
            self.setMinimumWidth(200)
            self.setStyleSheet("background-color: black;")
            self.label = QLabel("Visual Preview")
            self.label.setStyleSheet("color: white;")
            self.label.setAlignment(Qt.AlignCenter)
            layout = QVBoxLayout()
            layout.addWidget(self.label)
            self.setLayout(layout)
            
        def show_static_preview(self, frequency):
            self.label.setText(f"Preview: {frequency:.1f} Hz")
            self.update()
            
        def start_preview(self, frequency=10.0, effect_type="pulse"):
            self.label.setText(f"Preview: {frequency:.1f} Hz - {effect_type}")
            self.update()
            
        def stop_preview(self):
            self.label.setText("Visual Preview")
            self.update()
            
        def update_frequency(self, frequency):
            self.label.setText(f"Preview: {frequency:.1f} Hz")
            self.update()

# Constants - ensure these are defined if they aren't imported
MIN_ENTRAINMENT_FREQ = 0.5
MAX_ENTRAINMENT_FREQ = 40.0
MIN_BASE_FREQ = 20.0
MAX_BASE_FREQ = 1000.0
DEFAULT_ENTRAINMENT_FREQ = 10.0
DEFAULT_BASE_FREQ = 100.0

# Import enum types if available
try:
    from advanced_isochronic_generator import WaveformType, ModulationType
    HAVE_ADVANCED_TYPES = True
except ImportError:
    HAVE_ADVANCED_TYPES = False
    # Create simple enum replacements
    class WaveformType:
        SINE = "sine"
        SQUARE = "square"
        TRIANGLE = "triangle"
        SAWTOOTH = "sawtooth"
        
    class ModulationType:
        SQUARE = "square"
        SINE = "sine"
        TRIANGLE = "triangle"

# Define the SineEditorWidget in the new file
class SineEditorWidget(QWidget):
    """Widget for editing SINE presets with entrainment, volume, and frequency curves."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset = SinePreset()
        self.current_file_path = None
        
        # Set the modern dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #202020;
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QPushButton {
                background-color: #3D6185;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4A76A8;
            }
            QPushButton:pressed {
                background-color: #2C4A6D;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #303030;
                color: #E0E0E0;
                border: 1px solid #505050;
                padding: 3px;
                border-radius: 2px;
            }
            QTabWidget::pane {
                border: 1px solid #505050;
                background-color: #252525;
            }
            QTabBar::tab {
                background-color: #353535;
                color: #C0C0C0;
                padding: 5px 10px;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
            }
            QTabBar::tab:selected {
                background-color: #454545;
                color: white;
            }
            QGroupBox {
                border: 1px solid #505050;
                border-radius: 3px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #353535;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3D6185;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:checked {
                background-color: #3D6185;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #353535;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
            }
        """)
        
        self.setup_ui()
        
        # Initialize audio preview variables
        self.stream = None
        self.p = None
        self.play_thread = None
        self._preview_backend = None  # 'pyaudio' | 'simpleaudio' | 'sounddevice'
        self._sa_obj = None  # simpleaudio.PlayObject
        
        # Initialize the original window reference (will be set by the main app)
        self.original_window = None
        self.attached_video_path = None
        self.video_linked_to_basic = False
    
    def setup_ui(self):
        """Set up the UI components"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create toolbar with buttons
        toolbar_layout = QHBoxLayout()
        
        # New preset button
        new_btn = QPushButton("New")
        try:
            new_btn.setIcon(QIcon.fromTheme("document-new"))
        except:
            pass  # Ignore if icon not available
        new_btn.clicked.connect(self.new_preset)
        toolbar_layout.addWidget(new_btn)
        
        # Open button
        open_btn = QPushButton("Open")
        try:
            open_btn.setIcon(QIcon.fromTheme("document-open"))
        except:
            pass  # Ignore if icon not available
        open_btn.clicked.connect(self.open_preset)
        toolbar_layout.addWidget(open_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        try:
            save_btn.setIcon(QIcon.fromTheme("document-save"))
        except:
            pass  # Ignore if icon not available
        save_btn.clicked.connect(self.save_preset)
        toolbar_layout.addWidget(save_btn)

        # Attach video button (always visible on toolbar)
        attach_btn_tb = QPushButton("Attach Video…")
        try:
            attach_btn_tb.setIcon(QIcon.fromTheme("video-x-generic"))
        except:
            pass
        attach_btn_tb.clicked.connect(self.attach_video)
        toolbar_layout.addWidget(attach_btn_tb)
        
        # Export button (with menu)
        export_btn = QPushButton("Export")
        try:
            export_btn.setIcon(QIcon.fromTheme("document-export"))
        except:
            pass  # Ignore if icon not available
        export_menu = QMenu(self)
        export_audio_action = QAction("Export Audio...", self)
        export_audio_action.triggered.connect(self.export_audio)
        export_xml_action = QAction("Export as XML...", self)
        export_xml_action.triggered.connect(self.export_as_xml)
        export_menu.addAction(export_audio_action)
        export_menu.addAction(export_xml_action)
        export_btn.setMenu(export_menu)
        toolbar_layout.addWidget(export_btn)
        
        # Add spacer
        toolbar_layout.addStretch()
        
        # Preset name display
        self.name_label = QLabel(self.preset.name)
        self.name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.name_label.setStyleSheet("color: #FFFFFF;")
        toolbar_layout.addWidget(self.name_label)
        
        # Edit name button
        edit_name_btn = QPushButton("Edit Name")
        edit_name_btn.clicked.connect(self.edit_name)
        toolbar_layout.addWidget(edit_name_btn)
        
        # Add spacer
        toolbar_layout.addStretch()
        
        # Play/Stop audio preview
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.play_preview)
        toolbar_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_preview)
        self.stop_btn.setEnabled(False)  # Disabled by default
        toolbar_layout.addWidget(self.stop_btn)
        
        # Process with video button
        process_btn = QPushButton("Process Video")
        process_btn.clicked.connect(self.process_with_video)
        toolbar_layout.addWidget(process_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Add horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #505050;")
        main_layout.addWidget(separator)
        
        # Create a second row for additional controls
        controls_layout = QHBoxLayout()

        # Video attachment
        video_group = QGroupBox("Video")
        video_vlayout = QVBoxLayout()
        self.video_label = QLabel("No video attached")
        attach_btn = QPushButton("Attach Video…")
        attach_btn.clicked.connect(self.attach_video)
        video_vlayout.addWidget(self.video_label)
        video_vlayout.addWidget(attach_btn)
        video_group.setLayout(video_vlayout)
        controls_layout.addWidget(video_group)
        
        # Duration controls
        duration_group = QGroupBox("Duration")
        duration_layout = QHBoxLayout()
        
        # Duration spinner (minutes and seconds)
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 120)  # 0-120 minutes
        self.min_spin.setValue(3)  # Default 3 minutes
        self.min_spin.setSuffix(" min")
        duration_layout.addWidget(self.min_spin)
        
        self.sec_spin = QSpinBox()
        self.sec_spin.setRange(0, 59)  # 0-59 seconds
        self.sec_spin.setValue(0)  # Default 0 seconds
        self.sec_spin.setSuffix(" sec")
        duration_layout.addWidget(self.sec_spin)
        
        # Connect duration controls
        self.min_spin.valueChanged.connect(self.update_duration)
        self.sec_spin.valueChanged.connect(self.update_duration)
        
        duration_group.setLayout(duration_layout)
        controls_layout.addWidget(duration_group)
        
        # Protocol presets
        protocol_group = QGroupBox("Protocol")
        protocol_layout = QHBoxLayout()
        
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItem("Custom")
        self.protocol_combo.addItem("ADHD/Beta")
        self.protocol_combo.addItem("Anxiety/Alpha")
        self.protocol_combo.addItem("Insomnia/Theta-Delta")
        self.protocol_combo.currentTextChanged.connect(self.apply_protocol_preset)
        protocol_layout.addWidget(self.protocol_combo)
        
        protocol_group.setLayout(protocol_layout)
        controls_layout.addWidget(protocol_group)
        
        # Audio-Visual Sync checkbox
        sync_group = QGroupBox("Synchronization")
        sync_layout = QVBoxLayout()
        
        self.sync_check = QCheckBox("Synchronize Audio & Visual")
        self.sync_check.setChecked(self.preset.sync_audio_visual if hasattr(self.preset, 'sync_audio_visual') else True)
        self.sync_check.stateChanged.connect(self.update_sync_setting)
        sync_layout.addWidget(self.sync_check)
        
        sync_group.setLayout(sync_layout)
        controls_layout.addWidget(sync_group)
        
        # Add Subsonic control
        subsonic_group = QGroupBox("Subsonic")
        subsonic_layout = QGridLayout()
        
        self.subsonic_check = QCheckBox("Enable Subsonic")
        self.subsonic_check.setChecked(self.preset.enable_subsonic if hasattr(self.preset, 'enable_subsonic') else False)
        self.subsonic_check.stateChanged.connect(self.update_subsonic_setting)
        subsonic_layout.addWidget(self.subsonic_check, 0, 0, 1, 2)
        
        subsonic_layout.addWidget(QLabel("Frequency:"), 1, 0)
        self.subsonic_freq_spin = QDoubleSpinBox()
        self.subsonic_freq_spin.setRange(0.1, 20.0)
        self.subsonic_freq_spin.setValue(self.preset.subsonic_frequency if hasattr(self.preset, 'subsonic_frequency') else 7.83)
        self.subsonic_freq_spin.setSuffix(" Hz")
        self.subsonic_freq_spin.setSingleStep(0.1)
        self.subsonic_freq_spin.setDecimals(2)
        self.subsonic_freq_spin.valueChanged.connect(self.update_subsonic_frequency)
        subsonic_layout.addWidget(self.subsonic_freq_spin, 1, 1)
        
        subsonic_layout.addWidget(QLabel("Volume:"), 2, 0)
        self.subsonic_vol_slider = QSlider(Qt.Horizontal)
        self.subsonic_vol_slider.setRange(0, 100)
        self.subsonic_vol_slider.setValue(int((self.preset.subsonic_volume if hasattr(self.preset, 'subsonic_volume') else 0.3) * 100))
        self.subsonic_vol_slider.valueChanged.connect(self.update_subsonic_volume)
        subsonic_layout.addWidget(self.subsonic_vol_slider, 2, 1)

        # Link subsonic frequency to entrainment option
        self.link_subsonic_check = QCheckBox("Link to Entrainment")
        self.link_subsonic_check.setChecked(False)
        self.link_subsonic_check.stateChanged.connect(self.update_visual_preview)
        # Also update enabled state when toggled
        self.link_subsonic_check.stateChanged.connect(lambda _: self.update_subsonic_setting(Qt.Checked if self.subsonic_check.isChecked() else Qt.Unchecked))
        subsonic_layout.addWidget(self.link_subsonic_check, 3, 0, 1, 2)

        subsonic_group.setLayout(subsonic_layout)
        controls_layout.addWidget(subsonic_group)
        
        # Add export format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MKV", "MOV", "WebM"])
        self.format_combo.setCurrentText((self.preset.selected_format if hasattr(self.preset, 'selected_format') else "mp4").upper())
        self.format_combo.currentTextChanged.connect(self.update_format_setting)
        format_layout.addWidget(self.format_combo)
        
        format_group.setLayout(format_layout)
        controls_layout.addWidget(format_group)
        
        main_layout.addLayout(controls_layout)
        
        # Add horizontal separator 
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #505050;")
        main_layout.addWidget(separator2)
        
        # Add Audio Settings row
        audio_layout = QHBoxLayout()
        
        # Tone volume control
        tone_group = QGroupBox("Tone Volume")
        tone_layout = QHBoxLayout()
        
        self.tone_vol_slider = QSlider(Qt.Horizontal)
        self.tone_vol_slider.setRange(0, 100)
        self.tone_vol_slider.setValue(int((self.preset.tone_volume if hasattr(self.preset, 'tone_volume') else 0.8) * 100))
        
        self.tone_vol_label = QLabel(f"{(self.preset.tone_volume if hasattr(self.preset, 'tone_volume') else 0.8) * 100:.0f}%")
        self.tone_vol_slider.valueChanged.connect(self.update_tone_volume)
        
        tone_layout.addWidget(self.tone_vol_slider)
        tone_layout.addWidget(self.tone_vol_label)
        
        tone_group.setLayout(tone_layout)
        audio_layout.addWidget(tone_group)
        
        # Waveform settings
        wave_group = QGroupBox("Waveform Settings")
        wave_layout = QGridLayout()
        
        wave_layout.addWidget(QLabel("Carrier:"), 0, 0)
        self.carrier_combo = QComboBox()
        self.carrier_combo.addItems(["Sine", "Square", "Triangle", "Sawtooth"])
        
        # Set the current carrier type
        current_carrier = str(self.preset.carrier_type) if hasattr(self.preset, 'carrier_type') else "sine"
        if hasattr(self.preset.carrier_type, 'value') if hasattr(self.preset, 'carrier_type') else False:
            current_carrier = str(self.preset.carrier_type.value)
        
        carrier_index = 0  # Default to sine
        if "square" in current_carrier.lower():
            carrier_index = 1
        elif "triangle" in current_carrier.lower():
            carrier_index = 2
        elif "saw" in current_carrier.lower():
            carrier_index = 3
            
        self.carrier_combo.setCurrentIndex(carrier_index)
        self.carrier_combo.currentIndexChanged.connect(self.update_carrier_type)
        wave_layout.addWidget(self.carrier_combo, 0, 1)
        
        wave_layout.addWidget(QLabel("Modulation:"), 1, 0)
        self.modulation_combo = QComboBox()
        self.modulation_combo.addItems(["Square", "Sine", "Triangle"])
        
        # Set the current modulation type
        current_mod = str(self.preset.modulation_type) if hasattr(self.preset, 'modulation_type') else "square"
        if hasattr(self.preset.modulation_type, 'value') if hasattr(self.preset, 'modulation_type') else False:
            current_mod = str(self.preset.modulation_type.value)
            
        mod_index = 0  # Default to square
        if "sine" in current_mod.lower():
            mod_index = 1
        elif "triangle" in current_mod.lower():
            mod_index = 2
            
        self.modulation_combo.setCurrentIndex(mod_index)
        self.modulation_combo.currentIndexChanged.connect(self.update_modulation_type)
        wave_layout.addWidget(self.modulation_combo, 1, 1)
        
        wave_group.setLayout(wave_layout)
        audio_layout.addWidget(wave_group)
        
        # Visual effect settings
        visual_group = QGroupBox("Visual Effect")
        visual_layout = QGridLayout()
        
        visual_layout.addWidget(QLabel("Effect Type:"), 0, 0)
        self.visual_combo = QComboBox()
        self.visual_combo.addItems(["Pulse", "Flash", "Color Cycle", "Blur"])
        
        # Set current visual effect
        visual_index = 0  # Default to pulse
        current_effect = (self.preset.visual_effect_type if hasattr(self.preset, 'visual_effect_type') else "pulse").lower()
        if "flash" in current_effect:
            visual_index = 1
        elif "color" in current_effect:
            visual_index = 2
        elif "blur" in current_effect:
            visual_index = 3
            
        self.visual_combo.setCurrentIndex(visual_index)
        self.visual_combo.currentIndexChanged.connect(self.update_visual_effect)
        visual_layout.addWidget(self.visual_combo, 0, 1)
        
        visual_layout.addWidget(QLabel("Intensity:"), 1, 0)
        self.visual_intensity_slider = QSlider(Qt.Horizontal)
        self.visual_intensity_slider.setRange(0, 100)
        self.visual_intensity_slider.setValue(int((self.preset.visual_intensity if hasattr(self.preset, 'visual_intensity') else 0.5) * 100))
        self.visual_intensity_slider.valueChanged.connect(self.update_visual_intensity)
        visual_layout.addWidget(self.visual_intensity_slider, 1, 1)
        
        visual_group.setLayout(visual_layout)
        audio_layout.addWidget(visual_group)
        
        main_layout.addLayout(audio_layout)
        
        # Add horizontal separator 
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        separator3.setStyleSheet("background-color: #505050;")
        main_layout.addWidget(separator3)
        
        # Add tabs for different curve editors
        self.tabs = QTabWidget()
        
        # Entrainment frequency tab
        entrainment_tab = QWidget()
        entrainment_layout = QVBoxLayout()
        self.entrainment_editor = CurveEditor(
            "Entrainment Frequency", 
            self.preset.entrainment_curve,
            value_unit="Hz",
            min_value=MIN_ENTRAINMENT_FREQ,
            max_value=MAX_ENTRAINMENT_FREQ
        )
        self.entrainment_editor.point_changed.connect(self.update_visual_preview)
        entrainment_layout.addWidget(self.entrainment_editor)
        entrainment_tab.setLayout(entrainment_layout)
        self.tabs.addTab(entrainment_tab, "Entrainment Frequency")
        
        # Volume tab
        volume_tab = QWidget()
        volume_layout = QVBoxLayout()
        self.volume_editor = CurveEditor(
            "Volume", 
            self.preset.volume_curve,
            value_unit="%",
            min_value=0,
            max_value=1
        )
        volume_layout.addWidget(self.volume_editor)
        volume_tab.setLayout(volume_layout)
        self.tabs.addTab(volume_tab, "Volume")
        
        # Base frequency tab
        base_freq_tab = QWidget()
        base_freq_layout = QVBoxLayout()
        self.base_freq_editor = CurveEditor(
            "Base Frequency", 
            self.preset.base_freq_curve,
            value_unit="Hz",
            min_value=MIN_BASE_FREQ,
            max_value=MAX_BASE_FREQ
        )
        base_freq_layout.addWidget(self.base_freq_editor)
        base_freq_tab.setLayout(base_freq_layout)
        self.tabs.addTab(base_freq_tab, "Base Frequency")
        
        main_layout.addWidget(self.tabs, 1)  # Give tabs a stretch factor of 1
        
        # Add visual preview widget below the tabs
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Visual Preview:"))
        
        try:
            self.visual_preview = VisualPreviewWidget()
            preview_layout.addWidget(self.visual_preview, 1)  # Give it a stretch factor
        except Exception as e:
            print(f"Error creating visual preview: {e}")
            self.visual_preview = QLabel("Visual Preview Not Available")
            self.visual_preview.setAlignment(Qt.AlignCenter)
            self.visual_preview.setStyleSheet("background-color: #000000; color: #FFFFFF; padding: 20px;")
            preview_layout.addWidget(self.visual_preview, 1)
        
        main_layout.addLayout(preview_layout)
        
        self.setLayout(main_layout)
    
    def update_tone_volume(self, value):
        """Update the tone volume setting"""
        volume = value / 100.0
        if hasattr(self.preset, 'tone_volume'):
            self.preset.tone_volume = volume
        self.tone_vol_label.setText(f"{value}%")
    
    def update_carrier_type(self, index):
        """Update the carrier waveform type"""
        carrier_types = ["sine", "square", "triangle", "sawtooth"]
        if index < len(carrier_types):
            carrier_type = carrier_types[index]
            
            # Update the preset
            if hasattr(self.preset, 'carrier_type'):
                if HAVE_ADVANCED_TYPES:
                    try:
                        self.preset.carrier_type = WaveformType(carrier_type)
                    except:
                        self.preset.carrier_type = carrier_type
                else:
                    self.preset.carrier_type = carrier_type
    
    def update_modulation_type(self, index):
        """Update the modulation type"""
        mod_types = ["square", "sine", "triangle"]
        if index < len(mod_types):
            mod_type = mod_types[index]
            
            # Update the preset
            if hasattr(self.preset, 'modulation_type'):
                if HAVE_ADVANCED_TYPES:
                    try:
                        self.preset.modulation_type = ModulationType(mod_type)
                    except:
                        self.preset.modulation_type = mod_type
                else:
                    self.preset.modulation_type = mod_type
    
    def update_visual_effect(self, index):
        """Update the visual effect type"""
        effect_types = ["pulse", "flash", "color_cycle", "blur"]
        if index < len(effect_types) and hasattr(self.preset, 'visual_effect_type'):
            self.preset.visual_effect_type = effect_types[index]
            self.update_visual_preview()
    
    def update_visual_intensity(self, value):
        """Update the visual effect intensity"""
        if hasattr(self.preset, 'visual_intensity'):
            self.preset.visual_intensity = value / 100.0
        # Update on-screen preview overlay intensity if available
        try:
            if hasattr(self, 'visual_preview') and hasattr(self.visual_preview, 'set_intensity'):
                self.visual_preview.set_intensity(self.preset.visual_intensity)
        except Exception:
            pass
    
    def update_sync_setting(self, state):
        """Update audio-visual synchronization setting"""
        if hasattr(self.preset, 'sync_audio_visual'):
            self.preset.sync_audio_visual = (state == Qt.Checked)
    
    def update_subsonic_setting(self, state):
        """Update subsonic enable state"""
        if hasattr(self.preset, 'enable_subsonic'):
            self.preset.enable_subsonic = (state == Qt.Checked)
            
            # Enable/disable the related controls
            enable = self.preset.enable_subsonic
            # Frequency spin disabled when linked
            link_on = getattr(self, 'link_subsonic_check', None)
            link_on = (link_on.isChecked() if link_on else False)
            self.subsonic_freq_spin.setEnabled(enable and not link_on)
            self.subsonic_vol_slider.setEnabled(enable)
    
    def update_subsonic_frequency(self, value):
        """Update subsonic frequency"""
        if hasattr(self.preset, 'subsonic_frequency'):
            self.preset.subsonic_frequency = value
    
    def update_subsonic_volume(self, value):
        """Update subsonic volume"""
        if hasattr(self.preset, 'subsonic_volume'):
            self.preset.subsonic_volume = value / 100.0
    
    def update_format_setting(self, text):
        """Update the selected video export format"""
        if hasattr(self.preset, 'selected_format'):
            self.preset.selected_format = text.lower()
    
    def new_preset(self):
        """Create a new preset"""
        # Prompt for confirmation if current preset is modified
        # (would need tracking of whether preset is modified)
        
        dialog = NameDialog("New Preset", self)
        if dialog.exec_():
            preset_name = dialog.get_name()
            self.preset = SinePreset(name=preset_name)
            self.name_label.setText(preset_name)
            self.current_file_path = None
            
            # Update UI components with new preset data
            self.entrainment_editor.curve = self.preset.entrainment_curve
            self.volume_editor.curve = self.preset.volume_curve
            self.base_freq_editor.curve = self.preset.base_freq_curve
            
            # Update duration controls
            mins = int(self.preset.get_duration()) // 60
            secs = int(self.preset.get_duration()) % 60
            self.min_spin.setValue(mins)
            self.sec_spin.setValue(secs)
            
            # Reset protocol dropdown
            self.protocol_combo.setCurrentIndex(0)  # Custom
            
            # Update checkboxes and sliders
            if hasattr(self.preset, 'sync_audio_visual'):
                self.sync_check.setChecked(self.preset.sync_audio_visual)
            if hasattr(self.preset, 'enable_subsonic'):
                self.subsonic_check.setChecked(self.preset.enable_subsonic)
            if hasattr(self.preset, 'subsonic_frequency'):
                self.subsonic_freq_spin.setValue(self.preset.subsonic_frequency)
            if hasattr(self.preset, 'subsonic_volume'):
                self.subsonic_vol_slider.setValue(int(self.preset.subsonic_volume * 100))
            if hasattr(self.preset, 'tone_volume'):
                self.tone_vol_slider.setValue(int(self.preset.tone_volume * 100))
            if hasattr(self.preset, 'visual_intensity'):
                self.visual_intensity_slider.setValue(int(self.preset.visual_intensity * 100))
            
            # Update the preview
            self.update_visual_preview()
            
            # Force redraw
            self.entrainment_editor.update()
            self.volume_editor.update()
            self.base_freq_editor.update()
    
    def edit_name(self):
        """Edit the name of the current preset"""
        dialog = NameDialog(self.preset.name, self)
        if dialog.exec_():
            new_name = dialog.get_name()
            self.preset.name = new_name
            self.name_label.setText(new_name)
    
    def update_duration(self):
        """Update the duration of the preset based on spinbox values"""
        # Calculate total seconds
        mins = self.min_spin.value()
        secs = self.sec_spin.value()
        total_seconds = mins * 60 + secs
        
        # Update preset duration
        if total_seconds > 0:
            self.preset.set_duration(total_seconds)
            
            # Force redraw of editors
            self.entrainment_editor.update()
            self.volume_editor.update()
            self.base_freq_editor.update()
    
    def apply_protocol_preset(self, protocol_name):
        """Apply a predefined protocol preset"""
        if protocol_name == "Custom":
            return  # Keep current settings
        
        try:
            # Import protocols dictionary if available, otherwise use defaults
            try:
                from integrated_isoflicker import PROTOCOL_PRESETS
            except ImportError:
                # Define basic presets if not imported
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
            
            if protocol_name in PROTOCOL_PRESETS:
                protocol = PROTOCOL_PRESETS[protocol_name]
                
                # Clear existing points
                self.preset.entrainment_curve.control_points = []
                
                # Add new points from the protocol
                for point in protocol["entrainment_points"]:
                    self.preset.entrainment_curve.add_point(point["time"], point["value"])
                
                # Update carrier and modulation types if specified
                if "carrier_type" in protocol and hasattr(self.preset, 'carrier_type'):
                    self.preset.carrier_type = protocol["carrier_type"]
                    # Update the UI
                    carrier_index = 0  # Default to sine
                    carrier_type = protocol["carrier_type"].lower()
                    if "square" in carrier_type:
                        carrier_index = 1
                    elif "triangle" in carrier_type:
                        carrier_index = 2
                    elif "saw" in carrier_type:
                        carrier_index = 3
                    self.carrier_combo.setCurrentIndex(carrier_index)
                
                if "modulation_type" in protocol and hasattr(self.preset, 'modulation_type'):
                    self.preset.modulation_type = protocol["modulation_type"]
                    # Update the UI
                    mod_index = 0  # Default to square
                    mod_type = protocol["modulation_type"].lower()
                    if "sine" in mod_type:
                        mod_index = 1
                    elif "triangle" in mod_type:
                        mod_index = 2
                    self.modulation_combo.setCurrentIndex(mod_index)
                
                # Update UI
                self.entrainment_editor.update()
                self.update_visual_preview()
                
                # Set name
                self.preset.name = protocol["name"]
                self.name_label.setText(self.preset.name)
                
                # Update duration to match the protocol
                max_time = max(point["time"] for point in protocol["entrainment_points"])
                self.min_spin.setValue(max_time // 60)
                self.sec_spin.setValue(max_time % 60)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply protocol preset: {str(e)}")
    
    def update_visual_preview(self):
        """Update the visual preview based on the current settings"""
        try:
            # Current entrainment frequency (at time 0)
            entrainment_freq = self.preset.entrainment_curve.get_value_at_time(0)

            # Determine preview frequency (linked to entrainment or manual)
            if hasattr(self, 'preview_link_check') and self.preview_link_check.isChecked():
                preview_freq = entrainment_freq
                if hasattr(self, 'preview_freq_spin'):
                    self.preview_freq_spin.blockSignals(True)
                    self.preview_freq_spin.setValue(preview_freq)
                    self.preview_freq_spin.blockSignals(False)
            else:
                preview_freq = getattr(self, 'preview_freq_spin', None).value() if hasattr(self, 'preview_freq_spin') else entrainment_freq

            # Optionally link subsonic to entrainment
            if hasattr(self, 'link_subsonic_check') and self.link_subsonic_check.isChecked():
                linked = max(0.1, min(20.0, entrainment_freq))
                if hasattr(self, 'subsonic_freq_spin'):
                    self.subsonic_freq_spin.blockSignals(True)
                    self.subsonic_freq_spin.setValue(linked)
                    self.subsonic_freq_spin.blockSignals(False)
                if hasattr(self.preset, 'subsonic_frequency'):
                    self.preset.subsonic_frequency = linked

            # Update the visual preview
            if hasattr(self, 'visual_preview'):
                # Sync intensity to preview if supported
                try:
                    if hasattr(self.visual_preview, 'set_intensity') and hasattr(self.preset, 'visual_intensity'):
                        self.visual_preview.set_intensity(self.preset.visual_intensity)
                except Exception:
                    pass
                if self.stop_btn.isEnabled():  # If playback is active
                    if hasattr(self.visual_preview, 'update_frequency'):
                        self.visual_preview.update_frequency(preview_freq)
                else:
                    if hasattr(self.visual_preview, 'show_static_preview'):
                        self.visual_preview.show_static_preview(preview_freq)
        except Exception as e:
            print(f"Error updating visual preview: {e}")
    
    def export_audio(self):
        """Export the current preset as an audio file"""
        try:
            # Show export settings dialog
            dialog = ExportSettingsDialog(self)
            if not dialog.exec_():
                return
            
            settings = dialog.get_settings()
            
            # Get file path
            default_name = self.preset.name.replace(" ", "_") + "." + settings["format"]
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Export Audio",
                default_name,
                f"Audio Files (*.{settings['format']})"
            )
            
            if not filepath:
                return
            
            # Generate audio with the specified settings
            audio_data, sample_rate = self.preset.generate_audio(sample_rate=settings["sample_rate"])
            
            # Apply normalization if requested
            if settings["normalize"]:
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = audio_data * (0.95 / max_val)
            
            # Apply fade in/out if requested
            if settings["fade_in"] > 0:
                fade_samples = int(settings["fade_in"] * sample_rate)
                if fade_samples > 0 and fade_samples < len(audio_data):
                    audio_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
            
            if settings["fade_out"] > 0:
                fade_samples = int(settings["fade_out"] * sample_rate)
                if fade_samples > 0 and fade_samples < len(audio_data):
                    audio_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            # Save audio file
            sf.write(filepath, audio_data, sample_rate, format=settings["format"])
            
            QMessageBox.information(self, "Export Complete", f"Audio exported to:\n{filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export audio: {str(e)}")
    
    def export_as_xml(self, filepath=None):
        """
        Export the preset as an XML file.
        
        Args:
            filepath: Path to save to. If None, will prompt for location.
        """
        if filepath is None:
            filepath, _ = QFileDialog.getSaveFileName(
                self,
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
            
            if result:
                QMessageBox.information(self, "Export Complete", f"Preset exported to XML:\n{filepath}")
            
            return result
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export preset as XML: {str(e)}")
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
                    self,
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
            QMessageBox.information(self, "Save Complete", f"Preset saved to:\n{filepath}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preset: {str(e)}")
            return False
    
    def open_preset(self):
        """
        Opens a file dialog to load a preset (.sin or .xml).
        """
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Preset",
            "",
            "All Preset Files (*.sin *.xml);;SINE Preset Files (*.sin);;XML Preset Files (*.xml);;All Files (*)"
        )
        
        if filepath:
            try:
                self.preset = SinePreset.load_from_file(filepath)
                self.current_file_path = filepath
                
                # Update UI
                self.name_label.setText(self.preset.name)
                
                # Update editors with new curves
                self.entrainment_editor.curve = self.preset.entrainment_curve
                self.volume_editor.curve = self.preset.volume_curve
                self.base_freq_editor.curve = self.preset.base_freq_curve
                
                # Update duration spinners
                duration = self.preset.get_duration()
                self.min_spin.setValue(int(duration) // 60)
                self.sec_spin.setValue(int(duration) % 60)
                
                # Update checkboxes and sliders
                if hasattr(self.preset, 'sync_audio_visual'):
                    self.sync_check.setChecked(self.preset.sync_audio_visual)
                if hasattr(self.preset, 'enable_subsonic'):
                    self.subsonic_check.setChecked(self.preset.enable_subsonic)
                if hasattr(self.preset, 'subsonic_frequency'):
                    self.subsonic_freq_spin.setValue(self.preset.subsonic_frequency)
                if hasattr(self.preset, 'subsonic_volume'):
                    self.subsonic_vol_slider.setValue(int(self.preset.subsonic_volume * 100))
                if hasattr(self.preset, 'tone_volume'):
                    self.tone_vol_slider.setValue(int(self.preset.tone_volume * 100))
                if hasattr(self.preset, 'visual_intensity'):
                    self.visual_intensity_slider.setValue(int(self.preset.visual_intensity * 100))
                
                # Reset protocol to custom (since we loaded a file)
                self.protocol_combo.setCurrentIndex(0)
                
                # Update carrier and modulation UI
                if hasattr(self.preset, 'carrier_type'):
                    current_carrier = str(self.preset.carrier_type)
                    if hasattr(self.preset.carrier_type, 'value'):
                        current_carrier = str(self.preset.carrier_type.value)
                        
                    carrier_index = 0  # Default to sine
                    if "square" in current_carrier.lower():
                        carrier_index = 1
                    elif "triangle" in current_carrier.lower():
                        carrier_index = 2
                    elif "saw" in current_carrier.lower():
                        carrier_index = 3
                    
                    self.carrier_combo.setCurrentIndex(carrier_index)
                
                if hasattr(self.preset, 'modulation_type'):
                    current_mod = str(self.preset.modulation_type)
                    if hasattr(self.preset.modulation_type, 'value'):
                        current_mod = str(self.preset.modulation_type.value)
                        
                    mod_index = 0  # Default to square
                    if "sine" in current_mod.lower():
                        mod_index = 1
                    elif "triangle" in current_mod.lower():
                        mod_index = 2
                        
                    self.modulation_combo.setCurrentIndex(mod_index)
                
                # Update visual effect UI
                if hasattr(self.preset, 'visual_effect_type'):
                    effect_index = 0  # Default to pulse
                    effect = self.preset.visual_effect_type.lower()
                    if "flash" in effect:
                        effect_index = 1
                    elif "color" in effect:
                        effect_index = 2
                    elif "blur" in effect:
                        effect_index = 3
                    
                    self.visual_combo.setCurrentIndex(effect_index)
                
                # Update visual preview
                self.update_visual_preview()
                
                # Force redraw
                self.entrainment_editor.update()
                self.volume_editor.update()
                self.base_freq_editor.update()
                
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open preset: {str(e)}")
                return False
        return False
    
    def get_current_audio(self, sample_rate=44100):
        """
        Get the current audio data for preview or use in the main application.
        
        Returns:
            tuple: (audio_data, sample_rate)
        """
        return self.preset.generate_audio(sample_rate)
    
    def play_preview(self):
        """Play a preview of the current tone settings"""
        try:
            import numpy as np
            import threading

            # Generate audio data
            audio_data, sample_rate = self.preset.generate_audio()

            # Limit preview to 10 seconds
            preview_length = min(10 * sample_rate, len(audio_data))
            preview_data = audio_data[:preview_length]
            # Apply tone volume as master preview gain if available
            try:
                gain = float(getattr(self.preset, 'tone_volume', 0.8))
            except Exception:
                gain = 0.8
            preview_data = preview_data * gain

            # Try PyAudio first
            try:
                import pyaudio

                self.p = pyaudio.PyAudio()
                self.stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=sample_rate,
                    output=True
                )

                audio_bytes = (preview_data.astype(np.float32)).tobytes()

                def play_audio_pa():
                    try:
                        self.stream.write(audio_bytes)
                        QApplication.postEvent(self, QPlaybackFinishedEvent())
                    except Exception as e:
                        print(f"Error during playback (PyAudio): {e}")

                self.play_thread = threading.Thread(target=play_audio_pa)
                self.play_thread.daemon = True
                self.play_thread.start()
                self._preview_backend = 'pyaudio'

            except Exception:
                # Fallback to simpleaudio
                try:
                    import simpleaudio as sa
                    audio_int16 = np.clip(preview_data, -1.0, 1.0)
                    audio_int16 = (audio_int16 * 32767).astype(np.int16)
                    self._sa_obj = sa.play_buffer(audio_int16.tobytes(), 1, 2, sample_rate)

                    def monitor_sa():
                        try:
                            self._sa_obj.wait_done()
                        except Exception as e:
                            print(f"Error during playback (simpleaudio): {e}")
                        QApplication.postEvent(self, QPlaybackFinishedEvent())

                    self.play_thread = threading.Thread(target=monitor_sa)
                    self.play_thread.daemon = True
                    self.play_thread.start()
                    self._preview_backend = 'simpleaudio'

                except Exception:
                    # Fallback to sounddevice
                    try:
                        import sounddevice as sd

                        sd.play(preview_data.astype(np.float32), samplerate=sample_rate, blocking=False)

                        def monitor_sd():
                            import time as _t
                            _t.sleep(preview_length / float(sample_rate))
                            QApplication.postEvent(self, QPlaybackFinishedEvent())

                        self.play_thread = threading.Thread(target=monitor_sd)
                        self.play_thread.daemon = True
                        self.play_thread.start()
                        self._preview_backend = 'sounddevice'
                    except Exception as e:
                        raise RuntimeError(
                            "Audio backend not available. Install one of: pyaudio, simpleaudio, or sounddevice"
                        ) from e
            
            # Update UI
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # Ensure visual preview has a video source if available
            try:
                candidate_video = None
                if getattr(self, 'attached_video_path', None):
                    candidate_video = self.attached_video_path
                elif getattr(self, 'original_window', None):
                    ow = self.original_window
                    if hasattr(ow, 'video_path') and ow.video_path:
                        candidate_video = ow.video_path
                    elif hasattr(ow, 'basic_mode') and hasattr(ow.basic_mode, 'video_path') and ow.basic_mode.video_path:
                        candidate_video = ow.basic_mode.video_path
                if candidate_video and hasattr(self, 'visual_preview') and hasattr(self.visual_preview, 'set_video_source'):
                    try:
                        self.visual_preview.set_video_source(candidate_video)
                    except Exception:
                        pass
            except Exception:
                pass

            # Start visual preview
            base_freq = self.preset.entrainment_curve.get_value_at_time(0)
            preview_freq = base_freq
            if hasattr(self, 'preview_link_check') and not self.preview_link_check.isChecked():
                if hasattr(self, 'preview_freq_spin'):
                    preview_freq = self.preview_freq_spin.value()
            if hasattr(self.visual_preview, 'start_preview'):
                effect_type = self.preset.visual_effect_type if hasattr(self.preset, 'visual_effect_type') else "pulse"
                self.visual_preview.start_preview(
                    frequency=preview_freq, 
                    effect_type=effect_type
                )
            
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Could not play preview: {str(e)}")

    def stop_preview(self):
        """Stop the currently playing preview"""
        try:
            if self._preview_backend == 'pyaudio':
                if getattr(self, "stream", None):
                    try:
                        self.stream.stop_stream()
                    except Exception as e:
                        print(f"Error stopping stream: {e}")
                    try:
                        self.stream.close()
                    except Exception as e:
                        print(f"Error closing stream: {e}")
                    self.stream = None
                if getattr(self, "p", None):
                    try:
                        self.p.terminate()
                    except Exception as e:
                        print(f"Error terminating PyAudio: {e}")
                    self.p = None
            elif self._preview_backend == 'simpleaudio':
                if getattr(self, "_sa_obj", None):
                    try:
                        self._sa_obj.stop()
                    except Exception:
                        pass
                    self._sa_obj = None
            elif self._preview_backend == 'sounddevice':
                try:
                    import sounddevice as sd
                    sd.stop()
                except Exception:
                    pass
            self._preview_backend = None
        except Exception as e:
            print(f"Error during playback cleanup: {e}")
            
        # Update UI
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Stop visual preview
        if hasattr(self.visual_preview, 'stop_preview'):
            try:
                self.visual_preview.stop_preview()
            except Exception as e:
                print(f"Error stopping visual preview: {e}")

    def attach_video(self):
        """Attach a video file for SINE processing and preview aspect."""
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.mkv *.avi *.mov *.webm);;All Files (*)")
            if not path:
                return
            self.set_attached_video(path, origin='local')
        except Exception as e:
            QMessageBox.warning(self, "Attach Video", f"Could not attach video: {str(e)}")

    def set_attached_video(self, path, origin='local'):
        """Attach a video path programmatically.
        origin: 'basic' when coming from Basic Mode, else 'local'.
        """
        self.attached_video_path = path
        self.video_linked_to_basic = (origin == 'basic')
        try:
            import os
            if hasattr(self, 'video_label'):
                self.video_label.setText(os.path.basename(path))
        except Exception:
            if hasattr(self, 'video_label'):
                self.video_label.setText(path)

        # Update preview aspect and propose duration
        if VideoFileClip is not None:
            try:
                clip = VideoFileClip(path)
                duration = clip.duration
                width = getattr(clip, 'w', None)
                height = getattr(clip, 'h', None)
                try:
                    if (width is None or height is None) and hasattr(clip, 'size'):
                        width, height = clip.size
                except Exception:
                    width, height = None, None
                clip.close()
                # Apply aspect
                if hasattr(self.visual_preview, 'set_video_dimensions') and width and height:
                    self.visual_preview.set_video_dimensions(width, height)
                # Also grab a representative frame to show under the flicker
                if hasattr(self.visual_preview, 'set_video_source'):
                    try:
                        self.visual_preview.set_video_source(path)
                    except Exception:
                        pass
                # Align duration
                if duration and duration > 0:
                    mins = int(duration) // 60
                    secs = int(duration) % 60
                    self.min_spin.setValue(mins)
                    self.sec_spin.setValue(secs)
                    self.preset.set_duration(duration)
            except Exception as e:
                print(f"set_attached_video: could not read info: {e}")
        else:
            # Even if MoviePy dimension probe failed, try to set a frame if preview supports OpenCV path
            try:
                if hasattr(self.visual_preview, 'set_video_source'):
                    self.visual_preview.set_video_source(path)
            except Exception:
                pass

        # Also propagate to main window if available (so processing works)
        if hasattr(self, 'original_window') and self.original_window:
            try:
                self.original_window.video_path = path
            except Exception:
                pass

        # Update link status label
        self.update_link_status()

    def update_link_status(self):
        """Update the toolbar link status indicator."""
        try:
            if getattr(self, 'video_linked_to_basic', False):
                self.link_status_label.setText("Linked to Basic Mode")
                self.link_status_label.setStyleSheet("color: #2ECC71; font-weight: bold;")
            else:
                if self.attached_video_path:
                    self.link_status_label.setText("Local Video")
                    self.link_status_label.setStyleSheet("color: #F1C40F; font-weight: bold;")
                else:
                    self.link_status_label.setText("Not Linked")
                    self.link_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
        except Exception:
            pass

    def match_video_duration(self):
        """Match the duration to the selected video"""
        # Check if we have a direct reference to the original window
        if hasattr(self, 'original_window') and self.original_window:
            original_window = self.original_window
        else:
            # Try to get it from the main window
            main_window = self.window()
            if not hasattr(main_window, 'original_window') or not main_window.original_window:
                QMessageBox.warning(self, "Error", "Cannot access main window or video information.")
                return
            original_window = main_window.original_window
            
        # Check if a video is selected - try multiple ways to find the video path
        video_path = None
        
        # Try direct access to video_path
        if hasattr(original_window, 'video_path') and original_window.video_path:
            video_path = original_window.video_path
        # Try accessing through basic_mode if available
        elif hasattr(original_window, 'basic_mode') and hasattr(original_window.basic_mode, 'video_path') and original_window.basic_mode.video_path:
            video_path = original_window.basic_mode.video_path
        # Fallback to locally attached video
        elif hasattr(self, 'attached_video_path') and self.attached_video_path:
            video_path = self.attached_video_path
        
        if not video_path:
            QMessageBox.warning(self, "Error", "Please select a video file in the Basic Mode tab first.")
            return
            
        try:
            # Get video duration and resolution using MoviePy
            if VideoFileClip is None:
                raise ImportError("MoviePy VideoFileClip not available")
            video_clip = VideoFileClip(video_path)
            video_duration = video_clip.duration
            # Determine resolution if available
            width = getattr(video_clip, 'w', None)
            height = getattr(video_clip, 'h', None)
            try:
                if (width is None or height is None) and hasattr(video_clip, 'size'):
                    width, height = video_clip.size
            except Exception:
                width, height = None, None
            video_clip.close()
            
            # Update the duration in the UI
            mins = int(video_duration) // 60
            secs = int(video_duration) % 60
            self.min_spin.setValue(mins)
            self.sec_spin.setValue(secs)
            
            # Update the preset duration
            self.preset.set_duration(video_duration)
            # Update visual preview aspect, if possible
            if hasattr(self.visual_preview, 'set_video_dimensions') and width and height:
                try:
                    self.visual_preview.set_video_dimensions(width, height)
                except Exception:
                    pass
            
            # Force redraw of editors
            self.entrainment_editor.update()
            self.volume_editor.update()
            self.base_freq_editor.update()
            
            QMessageBox.information(self, "Duration Updated", 
                                   f"Preset duration set to match video: {mins} min {secs} sec")
            
        except ImportError:
            QMessageBox.warning(self, "Error", "Could not import moviepy. Please install it with 'pip install moviepy'")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not get video duration: {str(e)}")

            
    def process_with_video(self):
        """Process a video with the current sine editor settings"""
        # First check if we have access to the parent window
        if hasattr(self, 'original_window') and self.original_window:
            main_window = self.original_window
        else:
            main_window = self.window()
            if not hasattr(main_window, 'original_window') or not main_window.original_window:
                QMessageBox.warning(self, "Error", "Cannot access main window or video processing functions.")
                return
            main_window = main_window.original_window
            
        # Check if a video is selected - try multiple ways to find the video path
        video_path = None
        
        # Try direct access to video_path
        if hasattr(main_window, 'video_path') and main_window.video_path:
            video_path = main_window.video_path
        # Try accessing through basic_mode if available
        elif hasattr(main_window, 'basic_mode') and hasattr(main_window.basic_mode, 'video_path') and main_window.basic_mode.video_path:
            video_path = main_window.basic_mode.video_path
        # Fallback to locally attached video
        elif hasattr(self, 'attached_video_path') and self.attached_video_path:
            video_path = self.attached_video_path
        
        if not video_path:
            QMessageBox.warning(self, "Error", "Please select a video file in the Basic Mode tab first.")
            return
            
        # Create processing options dialog
        try:
            process_dialog = QDialog(self)
            process_dialog.setWindowTitle("Process Video with Timeline Settings")
            process_dialog.setStyleSheet(self.styleSheet())  # Apply same style
            layout = QVBoxLayout()
            
            # Add processing options
            options_group = QGroupBox("Processing Options")
            options_layout = QVBoxLayout()
            
            # Visual entrainment options
            visual_check = QCheckBox("Include visual entrainment")
            visual_check.setChecked(True)
            options_layout.addWidget(visual_check)
            
            # Visual entrainment type
            visual_type_layout = QHBoxLayout()
            visual_type_layout.addWidget(QLabel("Visual effect:"))
            visual_type_combo = QComboBox()
            visual_type_combo.addItems(["Pulse", "Flash", "Color Cycle", "Blur"])
            
            # Set current visual effect
            current_effect = (self.preset.visual_effect_type if hasattr(self.preset, 'visual_effect_type') else "pulse").lower()
            effect_index = 0
            if "flash" in current_effect:
                effect_index = 1
            elif "color" in current_effect:
                effect_index = 2
            elif "blur" in current_effect:
                effect_index = 3
            visual_type_combo.setCurrentIndex(effect_index)
            
            visual_type_layout.addWidget(visual_type_combo)
            options_layout.addLayout(visual_type_layout)
            
            # Audio options
            audio_check = QCheckBox("Include audio entrainment")
            audio_check.setChecked(True)
            options_layout.addWidget(audio_check)
            
            # Audio volume
            audio_volume_layout = QHBoxLayout()
            audio_volume_layout.addWidget(QLabel("Audio volume:"))
            audio_volume_slider = QSlider(Qt.Horizontal)
            audio_volume_slider.setRange(0, 100)
            audio_volume_slider.setValue(80)
            audio_volume_layout.addWidget(audio_volume_slider)
            volume_label = QLabel("80%")
            audio_volume_layout.addWidget(volume_label)
            options_layout.addLayout(audio_volume_layout)
            
            # Tone volume (separate from main audio)
            tone_volume_layout = QHBoxLayout()
            tone_volume_layout.addWidget(QLabel("Tone volume:"))
            tone_volume_slider = QSlider(Qt.Horizontal)
            tone_volume_slider.setRange(0, 100)
            tone_volume_slider.setValue(int((self.preset.tone_volume if hasattr(self.preset, 'tone_volume') else 0.8) * 100))
            tone_volume_layout.addWidget(tone_volume_slider)
            tone_volume_label = QLabel(f"{int((self.preset.tone_volume if hasattr(self.preset, 'tone_volume') else 0.8) * 100)}%")
            tone_volume_layout.addWidget(tone_volume_label)
            options_layout.addLayout(tone_volume_layout)
            
            # Connect volume sliders to labels
            def update_volume_label(value):
                volume_label.setText(f"{value}%")
            audio_volume_slider.valueChanged.connect(update_volume_label)
            
            def update_tone_volume_label(value):
                tone_volume_label.setText(f"{value}%")
            tone_volume_slider.valueChanged.connect(update_tone_volume_label)
            
            # Add format options
            format_layout = QHBoxLayout()
            format_layout.addWidget(QLabel("Output format:"))
            format_combo = QComboBox()
            format_combo.addItems(["MP4", "AVI", "MKV", "MOV", "WebM"])
            format_combo.setCurrentText((self.preset.selected_format if hasattr(self.preset, 'selected_format') else "mp4").upper())
            format_layout.addWidget(format_combo)
            options_layout.addLayout(format_layout)
            
            options_group.setLayout(options_layout)
            layout.addWidget(options_group)
            
            # Add buttons
            button_layout = QHBoxLayout()
            process_btn = QPushButton("Process Video")
            cancel_btn = QPushButton("Cancel")
            button_layout.addWidget(process_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            process_dialog.setLayout(layout)
            
            # Connect buttons
            cancel_btn.clicked.connect(process_dialog.reject)
            
            # Connect process button to main window's processing function
            def start_processing():
                # Get processing options
                options = {
                    "visual_entrainment": visual_check.isChecked(),
                    "visual_type": visual_type_combo.currentText().lower(),
                    "audio_entrainment": audio_check.isChecked(),
                    "audio_volume": audio_volume_slider.value() / 100.0,
                    "tone_volume": tone_volume_slider.value() / 100.0,
                    "preset": self.preset,
                    "format": format_combo.currentText().lower()
                }
                
                process_dialog.accept()
                
                # Call the main window's process_with_timeline function
                if hasattr(main_window, 'process_with_timeline'):
                    main_window.process_with_timeline(options)
                else:
                    QMessageBox.warning(self, "Error", "Processing function not available. Please add the process_with_timeline method to your main window class.")
            
            process_btn.clicked.connect(start_processing)
            
            # Show dialog
            process_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def event(self, event):
        """Handle custom events"""
        if isinstance(event, QPlaybackFinishedEvent):
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            return True
        return super().event(event)

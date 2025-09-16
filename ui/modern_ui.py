import sys
import os
from core.video_processor import detect_isochronic_frequency
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QGroupBox, QFrame,
    QScrollArea, QComboBox, QDoubleSpinBox, QCheckBox, QLineEdit, QProgressBar,
    QMessageBox, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette
from sine_widget import SineEditorWidget


class ModernMainWindow(QMainWindow):
    """Modern main window with improved UI/UX design"""
    
    def __init__(self):
        super().__init__()
        self.video_path = ""
        self.audio_path = ""
        self.detected_freq = 0.0
        self.init_ui()
    
    def init_ui(self):
        """Initialize the modern user interface"""
        self.setWindowTitle("IsoFlicker Pro - Brainwave Entrainment Generator")
        self.setGeometry(100, 100, 1000, 700)

        # Initialize workflow enhancement features
        self.undo_stack = []
        self.redo_stack = []
        self.batch_files = []

        # Section configuration for navigation
        self.section_config = [
            ("media", "Media & Batching", self.create_file_section),
            ("entrainment", "Audio & Visual Entrainment", self.create_settings_section),
            ("export", "Export & Delivery", self.create_export_section),
        ]
        self.section_widgets = {}
        self.nav_buttons = {}

        # Set application style
        self.setStyleSheet(self.get_stylesheet())

        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create header
        header = self.create_header()
        main_layout.addWidget(header)

        # Build workspace with navigation, content, and utilities
        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(20)

        nav_panel = self.create_navigation_panel()
        workspace_layout.addWidget(nav_panel)

        self.main_scroll_area = self.build_main_content_area()
        workspace_layout.addWidget(self.main_scroll_area, 1)

        utility_panel = self.create_utility_panel()
        workspace_layout.addWidget(utility_panel)

        main_layout.addLayout(workspace_layout)

        # Create action buttons
        action_layout = self.create_action_buttons()
        main_layout.addLayout(action_layout)

        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        main_layout.addWidget(self.progress_bar)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Highlight the first navigation item by default
        if self.section_config:
            self.highlight_nav_button(self.section_config[0][0])

        # Setup keyboard shortcuts
        self.setup_shortcuts()    
    def get_stylesheet(self):
        """Get the application stylesheet"""
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 10px;
                padding-bottom: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004a8c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #007acc;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QLineEdit:focus {
                border: 2px solid #007acc;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #999999;
                background: white;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #007acc;
                border: 1px solid #007acc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked::after {
                content: "";
                position: absolute;
                left: 6px;
                top: 2px;
                width: 5px;
                height: 10px;
                border: solid white;
                border-width: 0 2px 2px 0;
                transform: rotate(45deg);
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            #navPanel {
                border: 1px solid #cccccc;
                border-radius: 12px;
                background-color: #ffffff;
                padding: 16px;
            }
            #navPanel QLabel {
                font-weight: bold;
                color: #333333;
            }
            #navPanel QPushButton {
                border: none;
                text-align: left;
                padding: 8px 12px;
                border-radius: 6px;
                background: transparent;
                color: #444444;
            }
            #navPanel QPushButton:hover {
                background-color: #e6f1fb;
            }
            #navPanel QPushButton:checked {
                background-color: #007acc;
                color: white;
            }
            QFrame#previewPanel, QFrame#utilityPanel, QFrame#contentSection {
                background-color: #ffffff;
                border: 1px solid #dddddd;
                border-radius: 12px;
            }
            QFrame#utilityPanel QLabel:first-child {
                font-weight: bold;
            }
        """
    
    def create_header(self):
        """Create the application header"""
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 20)
        
        # Title
        title = QLabel("IsoFlicker Pro")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #007acc;")
        
        # Version
        version = QLabel("v2.0")
        version.setStyleSheet("color: #666666; font-size: 10pt;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(version)
        header_layout.addStretch()
        
        header.setLayout(header_layout)
        return header


    def create_navigation_panel(self):
        panel = QFrame()
        panel.setObjectName("navPanel")
        panel.setFixedWidth(180)

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Workflow")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        for key, label, _ in self.section_config:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(32)
            button.clicked.connect(lambda checked, k=key: self.scroll_to_section(k))
            layout.addWidget(button)
            self.nav_buttons[key] = button

        layout.addStretch()
        return panel

    def build_main_content_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(0, 0, 0, 0)

        preview_panel = self.create_preview_panel()
        container_layout.addWidget(preview_panel)

        for key, title, factory in self.section_config:
            section_widget = factory()
            wrapped = self.wrap_section(title, section_widget)
            container_layout.addWidget(wrapped)
            self.section_widgets[key] = wrapped

        container_layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def wrap_section(self, title, content_widget):
        frame = QFrame()
        frame.setObjectName("contentSection")

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel(title)
        header.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(header)
        layout.addWidget(content_widget)

        return frame

    def create_preview_panel(self):
        frame = QFrame()
        frame.setObjectName("previewPanel")

        layout = QVBoxLayout(frame)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        header_layout = QHBoxLayout()
        header_label = QLabel("Preview")
        header_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.preview_snapshot = QLabel()
        self.preview_snapshot.setAlignment(Qt.AlignCenter)
        self.preview_snapshot.setMinimumHeight(220)
        self.preview_snapshot.setStyleSheet("background-color: #1e1e1e; color: #ffffff; border-radius: 8px;")
        self.preview_snapshot.setText("Preview will appear here")
        layout.addWidget(self.preview_snapshot)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        self.preview_play_btn = QPushButton("Preview")
        self.preview_play_btn.setEnabled(False)
        controls_layout.addWidget(self.preview_play_btn)
        controls_layout.addStretch()
        self.preview_time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.preview_time_label)
        layout.addLayout(controls_layout)

        return frame

    def create_utility_panel(self):
        panel = QFrame()
        panel.setObjectName("utilityPanel")
        panel.setMinimumWidth(320)
        panel.setMaximumWidth(380)

        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Tone Designer")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        subtitle = QLabel("Adjust entrainment curves and generate custom tones.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #555555;")
        layout.addWidget(subtitle)

        self.sine_editor_widget = SineEditorWidget(panel)
        self.sine_editor_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.sine_editor_widget)

        return panel

    def scroll_to_section(self, key):
        widget = self.section_widgets.get(key)
        if not widget:
            return
        self.highlight_nav_button(key)
        if getattr(self, "main_scroll_area", None):
            self.main_scroll_area.ensureWidgetVisible(widget, 0, 60)

    def highlight_nav_button(self, key):
        for section_key, button in self.nav_buttons.items():
            button.setChecked(section_key == key)
    
    def create_file_section(self):
        """Create the file selection section"""
        section = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Video selection group
        video_group = QGroupBox("Video Selection")
        video_layout = QVBoxLayout()
        video_layout.setSpacing(10)
        
        # Video file selection
        video_file_layout = QHBoxLayout()
        self.video_label = QLabel("No video file selected")
        self.video_label.setWordWrap(True)
        self.video_btn = QPushButton("Select Video File (Ctrl+O)")
        self.video_btn.clicked.connect(self.choose_video)
        video_file_layout.addWidget(self.video_label)
        video_file_layout.addWidget(self.video_btn)
        video_layout.addLayout(video_file_layout)
        
        # Batch processing
        batch_layout = QHBoxLayout()
        self.batch_label = QLabel("Batch Files: 0 selected")
        self.batch_btn = QPushButton("Select Batch Files")
        self.batch_btn.clicked.connect(self.choose_batch_files)
        self.clear_batch_btn = QPushButton("Clear Batch")
        self.clear_batch_btn.clicked.connect(self.clear_batch_files)
        batch_layout.addWidget(self.batch_label)
        batch_layout.addWidget(self.batch_btn)
        batch_layout.addWidget(self.clear_batch_btn)
        video_layout.addLayout(batch_layout)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # Audio selection group
        audio_group = QGroupBox("Audio Selection (Optional)")
        audio_layout = QVBoxLayout()
        audio_layout.setSpacing(10)
        
        # Audio file selection
        audio_file_layout = QHBoxLayout()
        self.audio_label = QLabel("No audio file selected")
        self.audio_label.setWordWrap(True)
        self.audio_btn = QPushButton("Select Audio File (Ctrl+Shift+O)")
        self.audio_btn.clicked.connect(self.choose_audio)
        self.clear_audio_btn = QPushButton("Clear")
        self.clear_audio_btn.clicked.connect(self.clear_audio)
        audio_file_layout.addWidget(self.audio_label)
        audio_file_layout.addWidget(self.audio_btn)
        audio_file_layout.addWidget(self.clear_audio_btn)
        audio_layout.addLayout(audio_file_layout)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # File information group
        info_group = QGroupBox("File Information")
        info_layout = QGridLayout()
        info_layout.setSpacing(10)
        
        self.video_info_label = QLabel("Video: None")
        self.video_info_label.setWordWrap(True)
        self.audio_info_label = QLabel("Audio: None")
        self.audio_info_label.setWordWrap(True)
        
        info_layout.addWidget(self.video_info_label, 0, 0)
        info_layout.addWidget(self.audio_info_label, 1, 0)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        section.setLayout(layout)
        return section
    
    def create_settings_section(self):
        """Create the settings section"""
        section = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Visual entrainment group
        visual_group = QGroupBox("Visual Entrainment")
        visual_layout = QVBoxLayout()
        visual_layout.setSpacing(10)
        
        # Enable checkbox
        self.use_visual_check = QCheckBox("Enable Visual Entrainment")
        self.use_visual_check.setChecked(True)
        visual_layout.addWidget(self.use_visual_check)
        
        # Frequency control
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency (Hz):"))
        self.visual_freq_spin = QDoubleSpinBox()
        self.visual_freq_spin.setRange(0.5, 40.0)
        self.visual_freq_spin.setValue(10.0)
        self.visual_freq_spin.setSingleStep(0.5)
        freq_layout.addWidget(self.visual_freq_spin)
        freq_layout.addStretch()
        visual_layout.addLayout(freq_layout)
        
        # Flicker strength control
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("Flicker Strength:"))
        self.flicker_amp_slider = QSlider(Qt.Horizontal)
        self.flicker_amp_slider.setRange(1, 50)
        self.flicker_amp_slider.setValue(10)
        self.flicker_amp_value = QLabel("0.10")
        self.flicker_amp_slider.valueChanged.connect(self.update_flicker_amp_label)
        strength_layout.addWidget(self.flicker_amp_slider)
        strength_layout.addWidget(self.flicker_amp_value)
        visual_layout.addLayout(strength_layout)
        
        # Visual effect type
        effect_layout = QHBoxLayout()
        effect_layout.addWidget(QLabel("Effect Type:"))
        self.visual_effect_combo = QComboBox()
        self.visual_effect_combo.addItems(["Pulse", "Fade", "Strobe"])
        effect_layout.addWidget(self.visual_effect_combo)
        effect_layout.addStretch()
        visual_layout.addLayout(effect_layout)
        
        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)
        
        # Audio entrainment group
        audio_group = QGroupBox("Audio Entrainment")
        audio_layout = QVBoxLayout()
        audio_layout.setSpacing(10)
        
        # Enable checkbox
        self.use_audio_check = QCheckBox("Enable Audio Entrainment")
        self.use_audio_check.setChecked(True)
        audio_layout.addWidget(self.use_audio_check)
        
        # Tone frequency control
        tone_freq_layout = QHBoxLayout()
        tone_freq_layout.addWidget(QLabel("Tone Frequency (Hz):"))
        self.tone_freq_spin = QDoubleSpinBox()
        self.tone_freq_spin.setRange(0.5, 40.0)
        self.tone_freq_spin.setValue(10.0)
        self.tone_freq_spin.setSingleStep(0.5)
        tone_freq_layout.addWidget(self.tone_freq_spin)
        tone_freq_layout.addStretch()
        audio_layout.addLayout(tone_freq_layout)
        
        # Carrier frequency control
        carrier_freq_layout = QHBoxLayout()
        carrier_freq_layout.addWidget(QLabel("Carrier Frequency (Hz):"))
        self.carrier_freq_spin = QDoubleSpinBox()
        self.carrier_freq_spin.setRange(20.0, 1000.0)
        self.carrier_freq_spin.setValue(100.0)
        self.carrier_freq_spin.setSingleStep(10.0)
        carrier_freq_layout.addWidget(self.carrier_freq_spin)
        carrier_freq_layout.addStretch()
        audio_layout.addLayout(carrier_freq_layout)
        
        # Sync frequencies checkbox
        self.sync_freq_check = QCheckBox("Synchronize Audio and Visual Frequencies")
        self.sync_freq_check.setChecked(True)
        self.sync_freq_check.stateChanged.connect(self.sync_frequencies)
        audio_layout.addWidget(self.sync_freq_check)
        
        # Tone volume control
        tone_volume_layout = QHBoxLayout()
        tone_volume_layout.addWidget(QLabel("Tone Volume:"))
        self.tone_volume_slider = QSlider(Qt.Horizontal)
        self.tone_volume_slider.setRange(1, 100)
        self.tone_volume_slider.setValue(50)
        self.tone_volume_value = QLabel("0.50")
        self.tone_volume_slider.valueChanged.connect(self.update_tone_volume_label)
        tone_volume_layout.addWidget(self.tone_volume_slider)
        tone_volume_layout.addWidget(self.tone_volume_value)
        audio_layout.addLayout(tone_volume_layout)
        
        # Original audio mixing options
        self.mix_original_check = QCheckBox("Mix with Original Audio")
        self.mix_original_check.setChecked(True)
        audio_layout.addWidget(self.mix_original_check)
        
        orig_volume_layout = QHBoxLayout()
        orig_volume_layout.addWidget(QLabel("Original Audio Volume:"))
        self.orig_volume_slider = QSlider(Qt.Horizontal)
        self.orig_volume_slider.setRange(1, 100)
        self.orig_volume_slider.setValue(30)
        self.orig_volume_value = QLabel("0.30")
        self.orig_volume_slider.valueChanged.connect(self.update_orig_volume_label)
        orig_volume_layout.addWidget(self.orig_volume_slider)
        orig_volume_layout.addWidget(self.orig_volume_value)
        audio_layout.addLayout(orig_volume_layout)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        layout.addStretch()
        section.setLayout(layout)
        return section
    
    def create_export_section(self):
        """Create the export section"""
        section = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Export settings group
        export_group = QGroupBox("Export Settings")
        export_layout = QVBoxLayout()
        export_layout.setSpacing(10)
        
        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("H.264 MP4 (Compatible)", "h264")
        self.format_combo.addItem("H.265 MP4 (HEVC)", "h265")
        self.format_combo.addItem("FFV1 MKV (Lossless)", "ffv1")
        self.format_combo.addItem("VP9 WebM (Web Optimized)", "webm")
        self.format_combo.addItem("ProRes MOV (Professional)", "prores")
        self.format_combo.addItem("Audio Only - WAV", "wav")
        self.format_combo.addItem("Audio Only - FLAC", "flac")
        self.format_combo.addItem("Audio Only - MP3", "mp3")
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        export_layout.addLayout(format_layout)
        
        # Filename prefix
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Filename Prefix:"))
        self.prefix_edit = QLineEdit("IsoFlicker")
        prefix_layout.addWidget(self.prefix_edit)
        prefix_layout.addStretch()
        export_layout.addLayout(prefix_layout)
        
        # Resolution settings
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["Source", "4K (3840x2160)", "1080p (1920x1080)", "720p (1280x720)", "Custom"])
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addStretch()
        export_layout.addLayout(resolution_layout)
        
        # Custom resolution (hidden by default)
        self.custom_resolution_widget = QWidget()
        custom_res_layout = QHBoxLayout()
        custom_res_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 7680)
        self.width_spin.setValue(1920)
        custom_res_layout.addWidget(self.width_spin)
        custom_res_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 4320)
        self.height_spin.setValue(1080)
        custom_res_layout.addWidget(self.height_spin)
        self.custom_resolution_widget.setLayout(custom_res_layout)
        self.custom_resolution_widget.setVisible(False)
        export_layout.addWidget(self.custom_resolution_widget)
        
        # Quality settings
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Lossless", "High", "Medium", "Low", "Custom"])
        self.quality_combo.setCurrentText("High")
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        export_layout.addLayout(quality_layout)
        
        # Custom quality settings (hidden by default)
        self.custom_quality_widget = QWidget()
        custom_quality_layout = QGridLayout()
        custom_quality_layout.addWidget(QLabel("Video Bitrate (kbps):"), 0, 0)
        self.video_bitrate_spin = QSpinBox()
        self.video_bitrate_spin.setRange(100, 50000)
        self.video_bitrate_spin.setValue(5000)
        custom_quality_layout.addWidget(self.video_bitrate_spin, 0, 1)
        custom_quality_layout.addWidget(QLabel("Audio Bitrate (kbps):"), 1, 0)
        self.audio_bitrate_spin = QSpinBox()
        self.audio_bitrate_spin.setRange(32, 320)
        self.audio_bitrate_spin.setValue(256)
        custom_quality_layout.addWidget(self.audio_bitrate_spin, 1, 1)
        self.custom_quality_widget.setLayout(custom_quality_layout)
        self.custom_quality_widget.setVisible(False)
        export_layout.addWidget(self.custom_quality_widget)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # Advanced export presets group
        preset_group = QGroupBox("Export Presets")
        preset_layout = QVBoxLayout()
        preset_layout.setSpacing(10)
        
        # Preset selection
        preset_select_layout = QHBoxLayout()
        preset_select_layout.addWidget(QLabel("Select Preset:"))
        self.export_preset_combo = QComboBox()
        self.export_preset_combo.addItems([
            "Custom",
            "YouTube",
            "Vimeo",
            "Lossless Archive",
            "Web Optimized",
            "Audio Only"
        ])
        preset_select_layout.addWidget(self.export_preset_combo)
        preset_select_layout.addStretch()
        preset_layout.addLayout(preset_select_layout)
        
        # Apply preset button
        self.apply_export_preset_btn = QPushButton("Apply Export Preset")
        self.apply_export_preset_btn.clicked.connect(self.apply_export_preset)
        preset_layout.addWidget(self.apply_export_preset_btn)
        
        # Save custom preset button
        self.save_export_preset_btn = QPushButton("Save Custom Preset")
        self.save_export_preset_btn.clicked.connect(self.save_export_preset)
        preset_layout.addWidget(self.save_export_preset_btn)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        layout.addStretch()
        section.setLayout(layout)
        return section
    
    def create_action_buttons(self):
        """Create the action buttons layout"""
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        # Undo/Redo buttons
        self.undo_btn = QPushButton("Undo (Ctrl+Z)")
        self.undo_btn.clicked.connect(self.undo_action)
        self.undo_btn.setEnabled(False)
        self.undo_btn.setFixedHeight(40)
        
        self.redo_btn = QPushButton("Redo (Ctrl+Y)")
        self.redo_btn.clicked.connect(self.redo_action)
        self.redo_btn.setEnabled(False)
        self.redo_btn.setFixedHeight(40)
        
        # Process button
        self.process_btn = QPushButton("Process Video (Ctrl+P)")
        self.process_btn.clicked.connect(self.process_video)
        self.process_btn.setEnabled(False)
        self.process_btn.setFixedHeight(40)
        
        # Preview button
        self.preview_btn = QPushButton("Preview Settings (Ctrl+R)")
        self.preview_btn.clicked.connect(self.preview_settings)
        self.preview_btn.setEnabled(False)
        self.preview_btn.setFixedHeight(40)
        
        # Save preset button
        self.save_preset_btn = QPushButton("Save Preset (Ctrl+S)")
        self.save_preset_btn.clicked.connect(self.save_preset)
        self.save_preset_btn.setFixedHeight(40)
        
        layout.addWidget(self.undo_btn)
        layout.addWidget(self.redo_btn)
        layout.addWidget(self.process_btn)
        layout.addWidget(self.preview_btn)
        layout.addWidget(self.save_preset_btn)
        
        return layout
    
    def update_flicker_amp_label(self):
        """Update the flicker amplitude label"""
        value = self.flicker_amp_slider.value() / 100
        self.flicker_amp_value.setText(f"{value:.2f}")
        
    def update_tone_volume_label(self):
        """Update the tone volume label"""
        value = self.tone_volume_slider.value() / 100
        self.tone_volume_value.setText(f"{value:.2f}")
        if self.sync_freq_check.isChecked():
            self.visual_freq_spin.setValue(self.tone_freq_spin.value())
        
    def update_orig_volume_label(self):
        """Update the original volume label"""
        value = self.orig_volume_slider.value() / 100
        self.orig_volume_value.setText(f"{value:.2f}")
        
    def sync_frequencies(self, state):
        """Synchronize audio and visual frequencies"""
        if state == Qt.Checked:
            self.visual_freq_spin.setValue(self.tone_freq_spin.value())
            
    def choose_video(self):
        """Choose a video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File",
            "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        
        if file_path:
            self.video_path = file_path
            filename = os.path.basename(file_path)
            self.video_label.setText(f"Video: {filename}")
            self.video_info_label.setText(f"Video: {filename}")
            self.update_process_button()
            
    def choose_audio(self):
        """Choose an audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File",
            "", "Audio Files (*.wav *.mp3 *.flac *.ogg)")

        if file_path:
            self.audio_path = file_path
            filename = os.path.basename(file_path)
            self.audio_label.setText(f"Audio: {filename}")
            info_text = f"Audio: {filename}"
            self.detected_freq = 0.0

            QApplication.setOverrideCursor(Qt.WaitCursor)
            detection_error = None
            try:
                self.detected_freq = detect_isochronic_frequency(file_path)
            except Exception as exc:
                detection_error = str(exc)
                self.detected_freq = 0.0
            finally:
                QApplication.restoreOverrideCursor()

            if detection_error:
                QMessageBox.warning(
                    self,
                    "Frequency Detection",
                    f"Unable to detect entrainment frequency:\n{detection_error}"
                )

            if self.detected_freq > 0:
                info_text += f" ({self.detected_freq:.2f} Hz)"
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

            self.audio_info_label.setText(info_text)

    def clear_audio(self):
        """Clear the selected audio file"""
        # Save current state for undo
        self.save_state_for_undo()
        
        self.audio_path = ""
        self.detected_freq = 0.0
        self.audio_label.setText("No audio file selected")
        self.audio_info_label.setText("Audio: None")
        
    def update_process_button(self):
        """Update the process button state"""
        self.process_btn.setEnabled(bool(self.video_path) or bool(self.batch_files))
        self.preview_btn.setEnabled(bool(self.video_path))
        
    def apply_preset(self):
        """Apply a selected preset"""
        # Save current state for undo
        self.save_state_for_undo()
        
        preset = self.preset_combo.currentText()
        
        # Apply preset values based on selection
        if preset == "ADHD Focus/Beta":
            self.tone_freq_spin.setValue(15.0)
            self.visual_freq_spin.setValue(15.0)
            self.carrier_freq_spin.setValue(100.0)
        elif preset == "Anxiety Relief/Alpha":
            self.tone_freq_spin.setValue(10.0)
            self.visual_freq_spin.setValue(10.0)
            self.carrier_freq_spin.setValue(100.0)
        elif preset == "Insomnia/Theta-Delta":
            self.tone_freq_spin.setValue(3.5)
            self.visual_freq_spin.setValue(3.5)
            self.carrier_freq_spin.setValue(100.0)
        elif preset == "Deep Relaxation/Theta":
            self.tone_freq_spin.setValue(6.0)
            self.visual_freq_spin.setValue(6.0)
            self.carrier_freq_spin.setValue(100.0)
        elif preset == "Creative Flow/Alpha-Theta":
            self.tone_freq_spin.setValue(8.0)
            self.visual_freq_spin.setValue(8.0)
            self.carrier_freq_spin.setValue(100.0)
        
        # Sync frequencies if enabled
        if self.sync_freq_check.isChecked():
            self.visual_freq_spin.setValue(self.tone_freq_spin.value())
            
        QMessageBox.information(self, "Preset Applied", f"Preset '{preset}' has been applied.")
    
    def apply_export_preset(self):
        """Apply a selected export preset"""
        # Save current state for undo
        self.save_state_for_undo()
        
        preset = self.export_preset_combo.currentText()
        
        # Apply export preset values based on selection
        if preset == "YouTube":
            self.format_combo.setCurrentIndex(0)  # H.264 MP4
            self.quality_combo.setCurrentText("High")
        elif preset == "Vimeo":
            self.format_combo.setCurrentIndex(0)  # H.264 MP4
            self.quality_combo.setCurrentText("High")
        elif preset == "Lossless Archive":
            self.format_combo.setCurrentIndex(2)  # FFV1 MKV
            self.quality_combo.setCurrentText("Lossless")
        elif preset == "Web Optimized":
            self.format_combo.setCurrentIndex(3)  # VP9 WebM
            self.quality_combo.setCurrentText("Medium")
        elif preset == "Audio Only":
            self.format_combo.setCurrentIndex(5)  # WAV
            self.quality_combo.setCurrentText("Lossless")
            
        QMessageBox.information(self, "Export Preset Applied", f"Export preset '{preset}' has been applied.")
    
    def save_export_preset(self):
        """Save the current export settings as a custom preset"""
        # Save current state for undo
        self.save_state_for_undo()
        
        # TODO: Implement custom preset saving functionality
        QMessageBox.information(self, "Save Export Preset", "Custom export preset saving functionality would be implemented here.")
        
    def preview_settings(self):
        """Preview the current settings"""
        # TODO: Implement preview functionality
        QMessageBox.information(self, "Preview", "Preview functionality would be implemented here.")
        
    def save_preset(self):
        """Save the current settings as a preset"""
        # TODO: Implement preset saving functionality
        QMessageBox.information(self, "Save Preset", "Preset saving functionality would be implemented here.")
        
    def process_video(self):
        """Process the video(s) with current settings"""
        # Save current state for undo
        self.save_state_for_undo()
        
        # Check if we're doing batch processing
        if self.batch_files:
            reply = QMessageBox.question(
                self, 
                "Batch Processing", 
                f"You have {len(self.batch_files)} files selected for batch processing. "
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # TODO: Implement batch video processing functionality
                # This would integrate with our enhanced video processor
                QMessageBox.information(self, "Batch Process", 
                                      f"Batch processing {len(self.batch_files)} files would be implemented here.")
        else:
            # TODO: Implement single video processing functionality
            # This would integrate with our enhanced video processor
            QMessageBox.information(self, "Process Video", "Video processing would be implemented here.")
        
    def save_state_for_undo(self):
        """Save the current state for undo functionality"""
        state = {
            "video_path": self.video_path,
            "audio_path": self.audio_path,
            "tone_freq": self.tone_freq_spin.value(),
            "visual_freq": self.visual_freq_spin.value(),
            "carrier_freq": self.carrier_freq_spin.value(),
            "tone_volume": self.tone_volume_slider.value(),
            "flicker_amp": self.flicker_amp_slider.value(),
            "use_visual": self.use_visual_check.isChecked(),
            "use_audio": self.use_audio_check.isChecked(),
            "sync_freq": self.sync_freq_check.isChecked(),
            "mix_original": self.mix_original_check.isChecked(),
            "original_volume": self.orig_volume_slider.value(),
            "batch_files": self.batch_files.copy()
        }
        self.undo_stack.append(state)
        self.undo_btn.setEnabled(True)
        self.redo_stack.clear()
        self.redo_btn.setEnabled(False)
    
    def restore_state(self, state):
        """Restore a previously saved state"""
        if state:
            self.video_path = state["video_path"]
            self.audio_path = state["audio_path"]
            self.tone_freq_spin.setValue(state["tone_freq"])
            self.visual_freq_spin.setValue(state["visual_freq"])
            self.carrier_freq_spin.setValue(state["carrier_freq"])
            self.tone_volume_slider.setValue(state["tone_volume"])
            self.flicker_amp_slider.setValue(state["flicker_amp"])
            self.use_visual_check.setChecked(state["use_visual"])
            self.use_audio_check.setChecked(state["use_audio"])
            self.sync_freq_check.setChecked(state["sync_freq"])
            self.mix_original_check.setChecked(state["mix_original"])
            self.orig_volume_slider.setValue(state["original_volume"])
            self.batch_files = state["batch_files"].copy()
            
            # Update UI labels
            if self.video_path:
                filename = os.path.basename(self.video_path)
                self.video_label.setText(f"Video: {filename}")
                self.video_info_label.setText(f"Video: {filename}")
            else:
                self.video_label.setText("No video file selected")
                self.video_info_label.setText("Video: None")
                
            if self.audio_path:
                filename = os.path.basename(self.audio_path)
                self.audio_label.setText(f"Audio: {filename}")
                self.audio_info_label.setText(f"Audio: {filename}")
            else:
                self.audio_label.setText("No audio file selected")
                self.audio_info_label.setText("Audio: None")
                
            self.batch_label.setText(f"Batch Files: {len(self.batch_files)} selected")
            self.update_process_button()
    
    def undo_action(self):
        """Undo the last action"""
        if self.undo_stack:
            # Save current state for redo
            current_state = {
                "video_path": self.video_path,
                "audio_path": self.audio_path,
                "tone_freq": self.tone_freq_spin.value(),
                "visual_freq": self.visual_freq_spin.value(),
                "carrier_freq": self.carrier_freq_spin.value(),
                "tone_volume": self.tone_volume_slider.value(),
                "flicker_amp": self.flicker_amp_slider.value(),
                "use_visual": self.use_visual_check.isChecked(),
                "use_audio": self.use_audio_check.isChecked(),
                "sync_freq": self.sync_freq_check.isChecked(),
                "mix_original": self.mix_original_check.isChecked(),
                "original_volume": self.orig_volume_slider.value(),
                "batch_files": self.batch_files.copy()
            }
            self.redo_stack.append(current_state)
            self.redo_btn.setEnabled(True)
            
            # Restore previous state
            previous_state = self.undo_stack.pop()
            self.restore_state(previous_state)
            
            # Update undo button state
            self.undo_btn.setEnabled(bool(self.undo_stack))
    
    def redo_action(self):
        """Redo the last undone action"""
        if self.redo_stack:
            # Save current state for undo
            current_state = {
                "video_path": self.video_path,
                "audio_path": self.audio_path,
                "tone_freq": self.tone_freq_spin.value(),
                "visual_freq": self.visual_freq_spin.value(),
                "carrier_freq": self.carrier_freq_spin.value(),
                "tone_volume": self.tone_volume_slider.value(),
                "flicker_amp": self.flicker_amp_slider.value(),
                "use_visual": self.use_visual_check.isChecked(),
                "use_audio": self.use_audio_check.isChecked(),
                "sync_freq": self.sync_freq_check.isChecked(),
                "mix_original": self.mix_original_check.isChecked(),
                "original_volume": self.orig_volume_slider.value(),
                "batch_files": self.batch_files.copy()
            }
            self.undo_stack.append(current_state)
            self.undo_btn.setEnabled(True)
            
            # Restore next state
            next_state = self.redo_stack.pop()
            self.restore_state(next_state)
            
            # Update redo button state
            self.redo_btn.setEnabled(bool(self.redo_stack))
    
    def choose_batch_files(self):
        """Choose multiple video files for batch processing"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files for Batch Processing",
            "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        
        if file_paths:
            # Save current state for undo
            self.save_state_for_undo()
            
            self.batch_files = file_paths
            self.batch_label.setText(f"Batch Files: {len(file_paths)} selected")
            self.update_process_button()
    
    def clear_batch_files(self):
        """Clear the selected batch files"""
        # Save current state for undo
        self.save_state_for_undo()
        
        self.batch_files = []
        self.batch_label.setText("Batch Files: 0 selected")
        self.update_process_button()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # We'll implement this in the full class
        pass
    
    def get_config(self):
        """Get the current configuration settings"""
        config = {
            "use_visual_entrainment": self.use_visual_check.isChecked(),
            "visual_frequency": self.visual_freq_spin.value(),
            "flicker_amplitude": self.flicker_amp_slider.value() / 100,
            "visual_type": self.visual_effect_combo.currentText().lower(),
            
            "use_audio_entrainment": self.use_audio_check.isChecked(),
            "tone_frequency": self.tone_freq_spin.value(),
            "tone_volume": self.tone_volume_slider.value() / 100,
            
            "carrier_frequency": self.carrier_freq_spin.value(),
            "mix_with_original": self.mix_original_check.isChecked(),
            "original_volume": self.orig_volume_slider.value() / 100,
            
            "external_audio": self.audio_path if self.audio_path else None
        }
        return config


def main():
    """Main function to run the modern UI"""
    app = QApplication(sys.argv)
    window = ModernMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()



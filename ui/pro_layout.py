from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QFormLayout,
    QPushButton, QLabel, QComboBox, QDoubleSpinBox, QSlider, QCheckBox,
    QLineEdit, QFrame, QSpinBox
)


class ProEditorWidget(QWidget):
    """Dark, three-pane editor layout inspired by the provided mock.

    Emits `request_process` with a dict of settings when the Process button
    is pressed. The host app is responsible for running the pipeline.
    """

    request_process = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = ""
        self._init_ui()

    # -------------------- UI --------------------
    def _init_ui(self):
        self.setStyleSheet(self._dark_stylesheet())
        root = QVBoxLayout(self)

        # Top bar
        top_bar = QHBoxLayout()
        self.path_label = QLabel("IsoFlicker / Default Preset")
        top_bar.addWidget(self.path_label, 1)

        self.stop_btn = QPushButton("Stop")
        self.process_btn = QPushButton("Process MP4")
        self.export_btn = QPushButton("Export MP4")
        self.stop_btn.setEnabled(False)
        top_bar.addWidget(self.stop_btn)
        top_bar.addWidget(self.process_btn)
        top_bar.addWidget(self.export_btn)

        root.addLayout(top_bar)

        # Split panes
        splitter = QSplitter(Qt.Horizontal)

        # Left: Controls
        left = QWidget()
        left_layout = QVBoxLayout(left)

        video_group = QGroupBox("Video")
        vform = QFormLayout()
        self.attach_btn = QPushButton("Attach Video…")
        vform.addRow(self.attach_btn)
        self.duration_min = QSpinBox(); self.duration_min.setRange(0, 600); self.duration_min.setValue(3)
        self.duration_sec = QSpinBox(); self.duration_sec.setRange(0, 59)
        drow = QHBoxLayout(); drow.addWidget(self.duration_min); drow.addWidget(QLabel("mn")); drow.addWidget(self.duration_sec); drow.addWidget(QLabel("sec"))
        dwrap = QWidget(); dwrap.setLayout(drow)
        vform.addRow(QLabel("Duration"), dwrap)
        self.protocol_combo = QComboBox(); self.protocol_combo.addItems(["Default", "Custom"])
        vform.addRow(QLabel("Protocol"), self.protocol_combo)
        video_group.setLayout(vform)
        left_layout.addWidget(video_group)

        sync_group = QGroupBox("Synchronization")
        sl = QVBoxLayout(); self.sync_audio = QCheckBox("Syncronize Audio"); self.sync_audio.setChecked(True); sl.addWidget(self.sync_audio)
        sync_group.setLayout(sl)
        left_layout.addWidget(sync_group)

        sub_group = QGroupBox("Subsonic")
        sf = QFormLayout()
        self.sub_freq = QDoubleSpinBox(); self.sub_freq.setRange(0.5, 1000.0); self.sub_freq.setValue(733.0)
        sf.addRow(QLabel("Frequency"), self.sub_freq)
        self.volume_slider = QSlider(Qt.Horizontal); self.volume_slider.setRange(1, 100); self.volume_slider.setValue(90)
        sf.addRow(QLabel("Volume"), self.volume_slider)
        sub_group.setLayout(sf)
        left_layout.addWidget(sub_group)

        wave_group = QGroupBox("Waveform Settings")
        wf = QFormLayout()
        self.carrier_combo = QComboBox(); self.carrier_combo.addItems(["Sine", "Square"]) 
        wf.addRow(QLabel("Carrier"), self.carrier_combo)
        self.mod_combo = QComboBox(); self.mod_combo.addItems(["Square", "Sine"]) 
        wf.addRow(QLabel("Modulation"), self.mod_combo)
        wave_group.setLayout(wf)
        left_layout.addWidget(wave_group)

        left_layout.addStretch(1)

        splitter.addWidget(left)

        # Center: Graph + Preview
        center = QWidget(); cly = QVBoxLayout(center)
        ctrl_group = QGroupBox("Controls")
        cbox = QVBoxLayout()
        cbox.addWidget(QLabel("Entrainment Frequency  |  Volume  |  Base Frequency"))
        self.chart = QFrame(); self.chart.setObjectName("chart"); self.chart.setMinimumHeight(180)
        self.chart.setFrameShape(QFrame.StyledPanel)
        cbox.addWidget(self.chart)
        ctrl_group.setLayout(cbox)
        cly.addWidget(ctrl_group)

        prev_group = QGroupBox("Visual Preview")
        pv = QVBoxLayout()
        self.preview = QFrame(); self.preview.setObjectName("preview"); self.preview.setMinimumHeight(220)
        self.preview.setFrameShape(QFrame.StyledPanel)
        pv.addWidget(self.preview)
        prev_group.setLayout(pv)
        cly.addWidget(prev_group)

        splitter.addWidget(center)

        # Right: Inspect
        right = QWidget(); rly = QVBoxLayout(right)
        inspect = QGroupBox("Inspect")
        iv = QVBoxLayout()

        vis1 = QGroupBox("Visual Flicker Settings")
        f1 = QFormLayout()
        self.flicker_shape = QComboBox(); self.flicker_shape.addItems(["sine", "square"])
        f1.addRow(QLabel("Flicker Shape"), self.flicker_shape)
        self.duty_slider = QSlider(Qt.Horizontal); self.duty_slider.setRange(10, 90); self.duty_slider.setValue(50)
        f1.addRow(QLabel("Duty Cycle"), self.duty_slider)
        self.enable_color_cycle = QCheckBox("Enable Color Cycling")
        self.enable_pattern_overlay = QCheckBox("Enable Pattern Overlay")
        f1.addRow(self.enable_color_cycle)
        f1.addRow(self.enable_pattern_overlay)
        vis1.setLayout(f1)
        iv.addWidget(vis1)

        inspect.setLayout(iv)
        rly.addWidget(inspect)
        rly.addStretch(1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setStretchFactor(2, 3)

        root.addWidget(splitter)

        # Bottom status bar-like row
        bottom = QHBoxLayout()
        self.export_path = QLineEdit()
        self.export_path.setPlaceholderText("File export")
        self.format_combo = QComboBox(); self.format_combo.addItems(["MP4", "MKV"])
        bottom.addWidget(self.export_path, 1)
        bottom.addWidget(self.format_combo)
        root.addLayout(bottom)

        # Signals
        self.attach_btn.clicked.connect(self._on_attach_video)
        self.process_btn.clicked.connect(self._emit_process)

    # -------------------- Behavior --------------------
    def _on_attach_video(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Attach Video", "", "Video Files (*.mp4 *.mov *.mkv *.avi)")
        if path:
            self.video_path = path
            self.path_label.setText(f"IsoFlicker / {path.split('/')[-1]}")

    def _emit_process(self):
        settings = {
            "video_path": self.video_path,
            "format": self.format_combo.currentText().lower(),
            "sync_audio": self.sync_audio.isChecked(),
            "volume": self.volume_slider.value() / 100.0,
            "flicker_shape": self.flicker_shape.currentText(),
            "duty": self.duty_slider.value(),
            "carrier": self.carrier_combo.currentText().lower(),
            "modulation": self.mod_combo.currentText().lower(),
            "sub_freq": self.sub_freq.value(),
            "color_cycle": self.enable_color_cycle.isChecked(),
            "pattern_overlay": self.enable_pattern_overlay.isChecked(),
            "output_path": self.export_path.text().strip(),
        }
        self.request_process.emit(settings)

    # -------------------- Styles --------------------
    def _dark_stylesheet(self) -> str:
        return """
        QWidget { background-color: #0f1722; color: #e5ecf5; }
        QGroupBox { border: 1px solid #2a3443; border-radius: 8px; margin-top: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #9fb4cf; }
        QPushButton { background-color: #1f2a38; border: 1px solid #2a3443; border-radius: 6px; padding: 6px 12px; }
        QPushButton:hover { background-color: #273447; }
        QPushButton:disabled { color: #73839b; border-color: #2a3443; }
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { background-color: #111a27; border: 1px solid #2a3443; border-radius: 6px; padding: 4px 6px; }
        QSlider::groove:horizontal { height: 6px; background: #1a2432; border-radius: 3px; }
        QSlider::handle:horizontal { background: #5bb0ff; width: 14px; margin: -4px 0; border-radius: 7px; }
        QCheckBox { spacing: 6px; }
        QFrame#preview { background-color: #0a0f16; border: 1px solid #2a3443; border-radius: 8px; }
        QFrame#chart { background-color: #0a0f16; border: 1px solid #2a3443; border-radius: 8px; }
        """


import numpy as np
import soundfile as sf
import os
import json
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QDoubleSpinBox, QComboBox, QSlider, QGroupBox,
    QScrollArea, QFileDialog, QMessageBox, QFrame, QLineEdit,
    QCheckBox, QDialog, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient

# Import the advanced generator
from advanced_isochronic_generator import IsochronicPresetGenerator, IsochronicToneGenerator, WaveformType, ModulationType

class TimelineSegment:
    """Represents a single segment in the isochronic timeline"""
    def __init__(self, 
                 start_freq=10.0,
                 end_freq=10.0, 
                 base_freq=100.0,
                 duration=60, 
                 volume=0.5, 
                 transition_type="linear"):
        self.start_freq = start_freq  # Hz - starting entrainment frequency
        self.end_freq = end_freq      # Hz - ending entrainment frequency
        self.base_freq = base_freq    # Hz - carrier wave frequency
        self.duration = duration      # seconds
        self.volume = volume          # 0.0 to 1.0
        self.transition_type = transition_type  # "none", "linear", "exponential"
    
    def to_dict(self):
        """Convert segment to dictionary for serialization"""
        return {
            "start_freq": self.start_freq,
            "end_freq": self.end_freq,
            "base_freq": self.base_freq,
            "duration": self.duration,
            "volume": self.volume,
            "transition_type": self.transition_type
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create segment from dictionary"""
        return cls(
            start_freq=data.get("start_freq", 10.0),
            end_freq=data.get("end_freq", 10.0),
            base_freq=data.get("base_freq", 100.0),
            duration=data.get("duration", 60),
            volume=data.get("volume", 0.5),
            transition_type=data.get("transition_type", "linear")
        )


class IsochronicPreset:
    """Manages a full isochronic tone preset with multiple segments"""
    def __init__(self, name="New Preset"):
        self.name = name
        self.segments = []
        self.loop = False
        self.carrier_type = WaveformType.SINE
        self.modulation_type = ModulationType.SQUARE
    
    def add_segment(self, segment):
        """Add a segment to the preset"""
        self.segments.append(segment)
    
    def remove_segment(self, index):
        """Remove a segment at the given index"""
        if 0 <= index < len(self.segments):
            self.segments.pop(index)
    
    def get_total_duration(self):
        """Calculate total duration of all segments"""
        return sum(segment.duration for segment in self.segments)
    
    def to_dict(self):
        """Convert preset to dictionary for serialization"""
        return {
            "name": self.name,
            "loop": self.loop,
            "carrier_type": self.carrier_type.value if hasattr(self.carrier_type, 'value') else str(self.carrier_type),
            "modulation_type": self.modulation_type.value if hasattr(self.modulation_type, 'value') else str(self.modulation_type),
            "segments": [segment.to_dict() for segment in self.segments]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create preset from dictionary"""
        preset = cls(name=data.get("name", "Imported Preset"))
        preset.loop = data.get("loop", False)
        
        # Parse carrier and modulation types
        carrier_type_str = data.get("carrier_type", "sine")
        try:
            preset.carrier_type = WaveformType(carrier_type_str)
        except (ValueError, TypeError):
            preset.carrier_type = WaveformType.SINE
        
        modulation_type_str = data.get("modulation_type", "square")
        try:
            preset.modulation_type = ModulationType(modulation_type_str)
        except (ValueError, TypeError):
            preset.modulation_type = ModulationType.SQUARE
        
        for segment_data in data.get("segments", []):
            preset.add_segment(TimelineSegment.from_dict(segment_data))
        
        return preset
    
    def save_to_file(self, filepath):
        """Save preset to a .sin file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath):
        """Load preset from a .sin file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def generate_audio(self, sample_rate=44100):
        """Generate the complete isochronic tone audio for this preset"""
        # Use the advanced generator
        preset_generator = IsochronicPresetGenerator(sample_rate)
        return preset_generator.generate_from_preset(self)


class TimelineSegmentWidget(QFrame):
    """Widget for displaying and editing a single timeline segment"""
    changed = pyqtSignal()
    deleted = pyqtSignal(object)
    
    def __init__(self, segment=None, index=0, parent=None):
        super().__init__(parent)
        self.segment = segment or TimelineSegment()
        self.index = index
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumHeight(120)
        self.setMaximumHeight(120)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header with title and delete button
        header = QHBoxLayout()
        title = QLabel(f"Segment {self.index + 1}")
        title.setStyleSheet("font-weight: bold;")
        header.addWidget(title)
        
        delete_btn = QPushButton("✖")
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(lambda: self.deleted.emit(self))
        header.addWidget(delete_btn)
        
        layout.addLayout(header)
        
        # Controls grid
        controls = QHBoxLayout()
        
        # First column - frequencies
        freq_group = QVBoxLayout()
        
        start_freq_layout = QHBoxLayout()
        start_freq_layout.addWidget(QLabel("Start Freq (Hz):"))
        self.start_freq_spin = QDoubleSpinBox()
        self.start_freq_spin.setRange(0.1, 40.0)
        self.start_freq_spin.setValue(self.segment.start_freq)
        self.start_freq_spin.setSingleStep(0.1)
        self.start_freq_spin.valueChanged.connect(self.update_segment)
        start_freq_layout.addWidget(self.start_freq_spin)
        freq_group.addLayout(start_freq_layout)
        
        end_freq_layout = QHBoxLayout()
        end_freq_layout.addWidget(QLabel("End Freq (Hz):"))
        self.end_freq_spin = QDoubleSpinBox()
        self.end_freq_spin.setRange(0.1, 40.0)
        self.end_freq_spin.setValue(self.segment.end_freq)
        self.end_freq_spin.setSingleStep(0.1)
        self.end_freq_spin.valueChanged.connect(self.update_segment)
        end_freq_layout.addWidget(self.end_freq_spin)
        freq_group.addLayout(end_freq_layout)
        
        base_freq_layout = QHBoxLayout()
        base_freq_layout.addWidget(QLabel("Base Freq (Hz):"))
        self.base_freq_spin = QDoubleSpinBox()
        self.base_freq_spin.setRange(20.0, 1000.0)
        self.base_freq_spin.setValue(self.segment.base_freq)
        self.base_freq_spin.setSingleStep(10.0)
        self.base_freq_spin.valueChanged.connect(self.update_segment)
        base_freq_layout.addWidget(self.base_freq_spin)
        freq_group.addLayout(base_freq_layout)
        
        controls.addLayout(freq_group)
        
        # Second column - duration and volume
        params_group = QVBoxLayout()
        
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (sec):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(self.segment.duration)
        self.duration_spin.valueChanged.connect(self.update_segment)
        duration_layout.addWidget(self.duration_spin)
        params_group.addLayout(duration_layout)
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.segment.volume * 100))
        self.volume_slider.valueChanged.connect(self.update_segment)
        volume_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel(f"{self.segment.volume:.2f}")
        volume_layout.addWidget(self.volume_label)
        params_group.addLayout(volume_layout)
        
        transition_layout = QHBoxLayout()
        transition_layout.addWidget(QLabel("Transition:"))
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["none", "linear", "exponential"])
        self.transition_combo.setCurrentText(self.segment.transition_type)
        self.transition_combo.currentTextChanged.connect(self.update_segment)
        transition_layout.addWidget(self.transition_combo)
        params_group.addLayout(transition_layout)
        
        controls.addLayout(params_group)
        
        layout.addLayout(controls)
        self.setLayout(layout)
    
    def update_segment(self):
        """Update segment data from UI controls"""
        self.segment.start_freq = self.start_freq_spin.value()
        self.segment.end_freq = self.end_freq_spin.value()
        self.segment.base_freq = self.base_freq_spin.value()
        self.segment.duration = self.duration_spin.value()
        self.segment.volume = self.volume_slider.value() / 100.0
        self.segment.transition_type = self.transition_combo.currentText()
        
        self.volume_label.setText(f"{self.segment.volume:.2f}")
        self.changed.emit()


class TimelineVisualizer(QWidget):
    """Widget for visualizing the timeline graphically"""
    segment_selected = pyqtSignal(int)
    
    def __init__(self, preset=None, parent=None):
        super().__init__(parent)
        self.preset = preset or IsochronicPreset()
        self.selected_segment = -1
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)
        
        # Color scheme
        self.colors = [
            QColor(52, 152, 219),    # Blue
            QColor(46, 204, 113),    # Green
            QColor(155, 89, 182),    # Purple
            QColor(241, 196, 15),    # Yellow
            QColor(231, 76, 60),     # Red
            QColor(26, 188, 156),    # Turquoise
            QColor(243, 156, 18)     # Orange
        ]
    
    def paintEvent(self, event):
        if not self.preset.segments:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate total duration and time scale
        total_duration = self.preset.get_total_duration()
        width = self.width() - 2  # Leave 1px border on each side
        
        # Draw timeline background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawRect(0, 0, self.width(), self.height())
        
        # Draw time markers (every minute)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # Draw minute markers
        minutes = int(total_duration / 60) + 1
        for i in range(minutes + 1):
            time_pos = i * 60
            if time_pos > total_duration:
                break
                
            x_pos = int(time_pos / total_duration * width) + 1
            painter.drawLine(x_pos, 0, x_pos, self.height())
            
            # Draw time label
            if i > 0:  # Skip 0:00 label which would be at the edge
                time_str = f"{i}:00"
                painter.drawText(x_pos - 10, self.height() - 5, time_str)
        
        # Draw segments
        current_x = 1  # Start at left edge with 1px offset
        
        for i, segment in enumerate(self.preset.segments):
            # Calculate segment width based on duration
            segment_width = int((segment.duration / total_duration) * width)
            if segment_width < 2:
                segment_width = 2  # Ensure minimum visibility
            
            # Define segment rectangle
            rect = QRectF(current_x, 5, segment_width, self.height() - 25)
            
            # Get color based on index (cycling through available colors)
            color = self.colors[i % len(self.colors)]
            
            # Create gradient for transition visualization
            if segment.start_freq != segment.end_freq:
                gradient = QLinearGradient(rect.topLeft(), rect.topRight())
                start_color = color
                end_color = color.lighter(130) if segment.end_freq > segment.start_freq else color.darker(130)
                gradient.setColorAt(0, start_color)
                gradient.setColorAt(1, end_color)
                painter.setBrush(QBrush(gradient))
            else:
                painter.setBrush(QBrush(color))
            
            # Highlight selected segment
            if i == self.selected_segment:
                painter.setPen(QPen(QColor(0, 0, 0), 2))
            else:
                painter.setPen(QPen(color.darker(), 1))
            
            # Draw segment rectangle
            painter.drawRect(rect)
            
            # Draw frequency label
            painter.setPen(Qt.white)
            if segment.start_freq == segment.end_freq:
                freq_text = f"{segment.start_freq:.1f}Hz"
            else:
                freq_text = f"{segment.start_freq:.1f}→{segment.end_freq:.1f}Hz"
                
            # Draw centered text if there's enough space
            if segment_width > 60:
                painter.drawText(rect, Qt.AlignCenter, freq_text)
            
            # Update current position
            current_x += segment_width
    
    def mousePressEvent(self, event):
        if not self.preset.segments:
            return
            
        # Calculate which segment was clicked
        total_duration = self.preset.get_total_duration()
        width = self.width() - 2
        
        current_x = 1
        for i, segment in enumerate(self.preset.segments):
            segment_width = int((segment.duration / total_duration) * width)
            if segment_width < 2:
                segment_width = 2
                
            # Check if click is within this segment
            if current_x <= event.x() <= current_x + segment_width:
                self.selected_segment = i
                self.segment_selected.emit(i)
                self.update()
                break
                
            current_x += segment_width


class IsochronicEditorWidget(QWidget):
    """Main widget for editing isochronic presets with timeline visualization"""
    preset_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset = IsochronicPreset()
        self.segment_widgets = []
        self.background_audio_path = ""
        self.background_volume = 0.3
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Preset name and control buttons
        header_layout = QHBoxLayout()
        
        preset_name_layout = QHBoxLayout()
        preset_name_layout.addWidget(QLabel("Preset Name:"))
        self.preset_name_edit = QLineEdit(self.preset.name)
        self.preset_name_edit.setMinimumWidth(200)
        self.preset_name_edit.textChanged.connect(self.update_preset_name)
        preset_name_layout.addWidget(self.preset_name_edit)
        header_layout.addLayout(preset_name_layout)
        
        # Loop checkbox
        self.loop_checkbox = QCheckBox("Loop Preset")
        self.loop_checkbox.setChecked(self.preset.loop)
        self.loop_checkbox.stateChanged.connect(self.update_loop_setting)
        header_layout.addWidget(self.loop_checkbox)
        
        # Advanced settings
        advanced_layout = QHBoxLayout()
        advanced_layout.addWidget(QLabel("Carrier:"))
        self.carrier_combo = QComboBox()
        self.carrier_combo.addItems([wt.value for wt in WaveformType])
        self.carrier_combo.setCurrentText(self.preset.carrier_type.value)
        self.carrier_combo.currentTextChanged.connect(self.update_carrier_type)
        advanced_layout.addWidget(self.carrier_combo)
        
        advanced_layout.addWidget(QLabel("Modulation:"))
        self.modulation_combo = QComboBox()
        self.modulation_combo.addItems([mt.value for mt in ModulationType])
        self.modulation_combo.setCurrentText(self.preset.modulation_type.value)
        self.modulation_combo.currentTextChanged.connect(self.update_modulation_type)
        advanced_layout.addWidget(self.modulation_combo)
        
        header_layout.addLayout(advanced_layout)
        header_layout.addStretch()
        
        # Control buttons
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self.new_preset)
        header_layout.addWidget(self.new_btn)
        
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self.load_preset)
        header_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_preset)
        header_layout.addWidget(self.save_btn)
        
        self.export_btn = QPushButton("Export Audio")
        self.export_btn.clicked.connect(self.export_audio)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Timeline visualization
        timeline_group = QGroupBox("Timeline Visualization")
        timeline_layout = QVBoxLayout()
        
        self.visualizer = TimelineVisualizer(self.preset)
        self.visualizer.segment_selected.connect(self.select_segment)
        timeline_layout.addWidget(self.visualizer)
        
        # Total duration display
        self.duration_label = QLabel("Total Duration: 0:00")
        timeline_layout.addWidget(self.duration_label)
        
        timeline_group.setLayout(timeline_layout)
        layout.addWidget(timeline_group)
        
        # Segments section
        segments_group = QGroupBox("Segments")
        segments_layout = QVBoxLayout()
        
        # Add segment button
        add_btn = QPushButton("+ Add Segment")
        add_btn.clicked.connect(self.add_segment)
        segments_layout.addWidget(add_btn)
        
        # Scrollable area for segments
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        
        self.segments_container = QWidget()
        self.segments_layout = QVBoxLayout(self.segments_container)
        self.segments_layout.addStretch()
        
        scroll.setWidget(self.segments_container)
        segments_layout.addWidget(scroll)
        
        segments_group.setLayout(segments_layout)
        layout.addWidget(segments_group)
        
        # Background audio options
        bg_group = QGroupBox("Background Audio (Optional)")
        bg_layout = QHBoxLayout()
        
        self.bg_label = QLabel("No background audio selected")
        self.bg_btn = QPushButton("Select Background")
        self.bg_btn.clicked.connect(self.choose_background)
        self.clear_bg_btn = QPushButton("Clear")
        self.clear_bg_btn.clicked.connect(self.clear_background)
        
        bg_layout.addWidget(self.bg_label)
        bg_layout.addWidget(self.bg_btn)
        bg_layout.addWidget(self.clear_bg_btn)
        
        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)
        
        self.setLayout(layout)
        
        # Add initial segment if preset is empty
        if not self.preset.segments:
            self.add_segment()
            
    def choose_background(self):
        """Select background audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Audio",
            "", "Audio Files (*.wav *.mp3 *.flac *.ogg)")
        
        if file_path:
            self.background_audio_path = file_path
            self.bg_label.setText(f"Background: {os.path.basename(file_path)}")
            
    def clear_background(self):
        """Clear background audio selection"""
        self.background_audio_path = ""
        self.bg_label.setText("No background audio selected")
    
    def update_preset_name(self, name):
        """Update the preset name"""
        self.preset.name = name
        self.preset_changed.emit()
    
    def update_loop_setting(self, state):
        """Update the loop setting"""
        self.preset.loop = state == Qt.Checked
        self.preset_changed.emit()
        
    def update_carrier_type(self, carrier_type_str):
        """Update the carrier wave type"""
        self.preset.carrier_type = WaveformType(carrier_type_str)
        self.preset_changed.emit()
        
    def update_modulation_type(self, modulation_type_str):
        """Update the modulation type"""
        self.preset.modulation_type = ModulationType(modulation_type_str)
        self.preset_changed.emit()
    
    def update_duration_label(self):
        """Update the total duration display"""
        total_seconds = self.preset.get_total_duration()
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        self.duration_label.setText(f"Total Duration: {minutes}:{seconds:02d}")
    
    def add_segment(self):
        """Add a new segment to the preset"""
        # Create a default segment (using previous segment's end frequency as the start if possible)
        if self.preset.segments:
            prev_segment = self.preset.segments[-1]
            segment = TimelineSegment(
                start_freq=prev_segment.end_freq,
                end_freq=prev_segment.end_freq,
                base_freq=prev_segment.base_freq,
                duration=60,
                volume=prev_segment.volume
            )
        else:
            segment = TimelineSegment()
            
        self.preset.add_segment(segment)
        
        # Create and add the widget
        segment_widget = TimelineSegmentWidget(segment, len(self.preset.segments) - 1)
        segment_widget.changed.connect(self.update_preset)
        segment_widget.deleted.connect(self.remove_segment_widget)
        
        # Add widget before the stretch
        self.segments_layout.insertWidget(self.segments_layout.count() - 1, segment_widget)
        self.segment_widgets.append(segment_widget)
        
        # Update the UI
        self.update_preset()
    
    def remove_segment_widget(self, widget):
        """Remove a segment widget and its corresponding segment"""
        if widget in self.segment_widgets:
            index = self.segment_widgets.index(widget)
            
            # Remove from preset
            self.preset.remove_segment(index)
            
            # Remove widget
            self.segments_layout.removeWidget(widget)
            widget.deleteLater()
            self.segment_widgets.remove(widget)
            
            # Update indices for remaining widgets
            for i, w in enumerate(self.segment_widgets):
                w.index = i
            
            # Update UI
            self.update_preset()
    
    def update_preset(self):
        """Update the preset and UI after changes"""
        # Update the visualizer
        self.visualizer.update()
        
        # Update duration label
        self.update_duration_label()
        
        # Emit change signal
        self.preset_changed.emit()
    
    def select_segment(self, index):
        """Select a segment in the editor"""
        if 0 <= index < len(self.segment_widgets):
            # Scroll to the selected segment
            widget = self.segment_widgets[index]
            # Add code here to scroll to widget if needed
    
    def new_preset(self):
        """Create a new preset"""
        # Confirm with user if there are existing segments
        if self.preset.segments:
            reply = QMessageBox.question(
                self, "New Preset", 
                "This will clear the current preset. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
                
        # Clear existing segments
        for widget in self.segment_widgets:
            self.segments_layout.removeWidget(widget)
            widget.deleteLater()
        
        self.segment_widgets.clear()
        
        # Create new preset
        self.preset = IsochronicPreset()
        self.preset_name_edit.setText(self.preset.name)
        self.loop_checkbox.setChecked(self.preset.loop)
        
        # Add initial segment
        self.add_segment()
        
        # Update UI
        self.visualizer.preset = self.preset
        self.update_preset()
    
    def load_preset(self):
        """Load a preset from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Preset", "", "SINE Preset Files (*.sin);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Load the preset
            preset = IsochronicPreset.load_from_file(file_path)
            
            # Clear existing segments
            for widget in self.segment_widgets:
                self.segments_layout.removeWidget(widget)
                widget.deleteLater()
            
            self.segment_widgets.clear()
            
            # Set the new preset
            self.preset = preset
            self.preset_name_edit.setText(self.preset.name)
            self.loop_checkbox.setChecked(self.preset.loop)
            
            # Create widgets for each segment
            for i, segment in enumerate(self.preset.segments):
                segment_widget = TimelineSegmentWidget(segment, i)
                segment_widget.changed.connect(self.update_preset)
                segment_widget.deleted.connect(self.remove_segment_widget)
                
                # Add widget before the stretch
                self.segments_layout.insertWidget(self.segments_layout.count() - 1, segment_widget)
                self.segment_widgets.append(segment_widget)
            
            # Update the visualizer
            self.visualizer.preset = self.preset
            self.update_preset()
            
            QMessageBox.information(self, "Load Preset", "Preset loaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preset: {str(e)}")
    
    def save_preset(self):
        """Save the preset to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", self.preset.name, "SINE Preset Files (*.sin)"
        )
        
        if not file_path:
            return
            
        # Add .sin extension if not present
        if not file_path.lower().endswith('.sin'):
            file_path += '.sin'
            
        try:
            self.preset.save_to_file(file_path)
            QMessageBox.information(self, "Save Preset", "Preset saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preset: {str(e)}")
    
    def export_audio(self):
        """Export the preset to an audio file"""
        if not self.preset.segments:
            QMessageBox.warning(self, "Export", "Cannot export an empty preset.")
            return
            
        file_path, filter_used = QFileDialog.getSaveFileName(
            self, "Export Audio", self.preset.name, 
            "WAV Files (*.wav);;FLAC Files (*.flac);;MP3 Files (*.mp3)"
        )
        
        if not file_path:
            return
            
        try:
            # Determine format from filter or extension
            if "WAV" in filter_used:
                file_format = "wav"
            elif "FLAC" in filter_used:
                file_format = "flac"
            elif "MP3" in filter_used:
                file_format = "mp3"
            else:
                # Detect from extension
                _, ext = os.path.splitext(file_path)
                file_format = ext.lower().lstrip('.')
            
            # Add appropriate extension if missing
            if not file_path.lower().endswith(f".{file_format}"):
                file_path += f".{file_format}"
            
            # Handle background audio if selected
            background_data = None
            if self.background_audio_path and os.path.exists(self.background_audio_path):
                try:
                    background_data, background_sr = sf.read(self.background_audio_path)
                    # Convert to mono if stereo
                    if len(background_data.shape) > 1 and background_data.shape[1] > 1:
                        background_data = np.mean(background_data, axis=1)
                except Exception as e:
                    print(f"Warning: Failed to load background audio: {e}")
            
            # Export using the preset generator
            preset_generator = IsochronicPresetGenerator()
            preset_generator.export_to_file(
                self.preset,
                file_path,
                file_format,
                background_data,
                self.background_volume
            )
            
            QMessageBox.information(
                self, "Export Audio", 
                f"Audio exported successfully to:\n{file_path}"
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "Error", f"Failed to export audio: {str(e)}\n\n{error_details}")
    
    def get_current_audio(self):
        """Get the current audio data for preview or use in the main application"""
        if not self.preset.segments:
            return np.array([]), 44100
        
        # Handle background audio if selected
        background_data = None
        if self.background_audio_path and os.path.exists(self.background_audio_path):
            try:
                background_data, background_sr = sf.read(self.background_audio_path)
                # Convert to mono if stereo
                if len(background_data.shape) > 1 and background_data.shape[1] > 1:
                    background_data = np.mean(background_data, axis=1)
            except Exception as e:
                print(f"Warning: Failed to load background audio: {e}")
        
        # Get audio from preset generator
        preset_generator = IsochronicPresetGenerator()
        return preset_generator.generate_from_preset(
            self.preset, 
            background_data, 
            self.background_volume
        )
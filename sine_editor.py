import sys
import os
import time
import numpy as np
import soundfile as sf
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFileDialog, QSlider, QGroupBox, QListWidget, QFrame,
    QMenu, QAction, QMessageBox, QLineEdit, QDialog, QDialogButtonBox, QCheckBox
)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject, QSize, QTimer

# Constants for the application
DEFAULT_BASE_FREQ = 100.0
DEFAULT_ENTRAINMENT_FREQ = 10.0
MIN_ENTRAINMENT_FREQ = 0.5
MAX_ENTRAINMENT_FREQ = 40.0
MIN_BASE_FREQ = 20.0
MAX_BASE_FREQ = 1000.0

class ControlPoint:
    """Represents a control point on the curve"""
    def __init__(self, time=0, value=0):
        self.time = time  # Time in seconds
        self.value = value  # Value (frequency or volume)
        self.selected = False
    
    def is_near(self, x, y, time_scale, value_scale, tolerance=10):
        """Check if a point is near this control point with given tolerance"""
        px = self.time * time_scale
        py = (1.0 - (self.value - value_scale[0]) / (value_scale[1] - value_scale[0])) * 100
        return abs(x - px) < tolerance and abs(y - py) < tolerance

class TrackCurve:
    """Manages a curve with control points for frequency or volume"""
    def __init__(self, min_value=0, max_value=1, default_value=0.5):
        self.control_points = []
        self.min_value = min_value
        self.max_value = max_value
        self.default_value = default_value
        self.selected_point = None
        # Add default points at start and end
        self.add_point(0, default_value)
        
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
    
    def remove_point(self, point):
        """Remove a control point"""
        if point in self.control_points and len(self.control_points) > 1:
            self.control_points.remove(point)
            return True
        return False
    
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
    
    def get_point_near(self, x, y, time_scale, value_scale):
        """Find a control point near the given coordinates"""
        for point in self.control_points:
            if point.is_near(x, y, time_scale, value_scale):
                return point
        return None
    
    def get_duration(self):
        """Get the duration of the curve (time of last point)"""
        if not self.control_points:
            return 0
        return self.control_points[-1].time

class CurveEditor(QWidget):
    """Widget for editing a curve with control points"""
    point_changed = pyqtSignal()
    
    def __init__(self, title, curve, parent=None, time_unit="sec", value_unit="Hz", min_value=0, max_value=100):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.title = title
        self.curve = curve
        self.time_unit = time_unit
        self.value_unit = value_unit
        self.min_value = min_value
        self.max_value = max_value
        self.dragging = False
        self.selected_point = None
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(0, 0, 0))
        self.setPalette(palette)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the grid
        self.draw_grid(painter)
        
        # Draw the curve
        self.draw_curve(painter)
    
    def draw_grid(self, painter):
        width = self.width()
        height = self.height()
        
        # Draw grid lines
        painter.setPen(QPen(QColor(50, 50, 50)))
        
        # Horizontal grid lines (10% intervals)
        for i in range(11):
            y = int(height * i / 10)
            painter.drawLine(0, y, width, y)
        
        # Vertical grid lines (10% intervals)
        for i in range(11):
            x = int(width * i / 10)
            painter.drawLine(x, 0, x, height)
    
    def draw_curve(self, painter):
        if not self.curve.control_points:
            return
            
        width = self.width()
        height = self.height()
        duration = max(180, self.curve.get_duration())  # Minimum 3 minute view
        
        # Draw connecting lines between points
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        
        points = []
        for point in self.curve.control_points:
            x = int(point.time / duration * width)
            y_factor = 1.0 - (point.value - self.min_value) / (self.max_value - self.min_value)
            y = int(y_factor * height)
            points.append(QPoint(x, y))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])
        
        # Draw control points
        for i, point in enumerate(self.curve.control_points):
            if point.selected or point == self.selected_point:
                painter.setBrush(QBrush(QColor(255, 255, 0)))
                painter.setPen(QPen(QColor(255, 255, 0), 2))
            else:
                painter.setBrush(QBrush(QColor(0, 255, 0)))
                painter.setPen(QPen(QColor(0, 255, 0), 2))
            
            x = int(point.time / duration * width)
            y_factor = 1.0 - (point.value - self.min_value) / (self.max_value - self.min_value)
            y = int(y_factor * height)
            
            # Draw point
            painter.drawRect(x-4, y-4, 8, 8)
            
            # Draw time and value for selected point
            if point.selected or point == self.selected_point:
                minutes = int(point.time) // 60
                seconds = int(point.time) % 60
                time_str = f"{minutes:02d}:{seconds:02d}:{int((point.time - int(point.time)) * 100):02d}"
                value_str = f"{point.value:.1f}{self.value_unit}"
                text = f"{time_str} , {value_str}"
                
                text_width = painter.fontMetrics().width(text)
                text_x = max(10, min(x - text_width // 2, width - text_width - 10))
                text_y = max(15, min(y - 15, height - 10))
                
                # Draw background for text
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
                painter.drawRect(text_x - 5, text_y - 15, text_width + 10, 20)
                
                # Draw text
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.drawText(text_x, text_y, text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            width = self.width()
            height = self.height()
            duration = max(180, self.curve.get_duration())
            
            # Calculate value scale
            value_scale = (self.min_value, self.max_value)
            
            # Check if we're clicking on an existing point
            point = self.curve.get_point_near(event.x(), event.x() / width * duration, value_scale)
            
            if point:
                self.selected_point = point
                point.selected = True
                self.dragging = True
            else:
                # Add a new point
                time = duration * event.x() / width
                value_factor = 1.0 - event.y() / height
                value = self.min_value + value_factor * (self.max_value - self.min_value)
                
                # Clamp values
                time = max(0, time)
                value = max(self.min_value, min(self.max_value, value))
                
                new_point = self.curve.add_point(time, value)
                self.selected_point = new_point
                self.dragging = True
            
            self.update()
            self.point_changed.emit()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
    
    def mouseMoveEvent(self, event):
        if self.dragging and self.selected_point:
            width = self.width()
            height = self.height()
            duration = max(180, self.curve.get_duration())
            
            # Update point position
            time = duration * event.x() / width
            value_factor = 1.0 - event.y() / height
            value = self.min_value + value_factor * (self.max_value - self.min_value)
            
            # Clamp values
            time = max(0, time)
            value = max(self.min_value, min(self.max_value, value))
            
            self.selected_point.time = time
            self.selected_point.value = value
            
            # Re-sort points
            self.curve.control_points.sort(key=lambda p: p.time)
            
            self.update()
            self.point_changed.emit()
    
    def show_context_menu(self, position):
        if self.selected_point:
            menu = QMenu(self)
            delete_action = QAction("Delete Point", self)
            delete_action.triggered.connect(self.delete_selected_point)
            menu.addAction(delete_action)
            menu.exec_(self.mapToGlobal(position))
    
    def delete_selected_point(self):
        if self.selected_point and len(self.curve.control_points) > 1:
            self.curve.remove_point(self.selected_point)
            self.selected_point = None
            self.update()
            self.point_changed.emit()

class SinePreset:
    """Represents a full preset with multiple curves for entrainment, volume, and base frequency"""
    def __init__(self, name="New Preset"):
        self.name = name
        self.entrainment_curve = TrackCurve(MIN_ENTRAINMENT_FREQ, MAX_ENTRAINMENT_FREQ, DEFAULT_ENTRAINMENT_FREQ)
        self.volume_curve = TrackCurve(0.0, 1.0, 0.5)
        self.base_freq_curve = TrackCurve(MIN_BASE_FREQ, MAX_BASE_FREQ, DEFAULT_BASE_FREQ)
    
    def get_duration(self):
        """Get the total duration of the preset"""
        return max(
            self.entrainment_curve.get_duration(),
            self.volume_curve.get_duration(),
            self.base_freq_curve.get_duration()
        )
    
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
        
        # Process in small chunks to handle varying parameters
        chunk_size = int(0.01 * sample_rate)  # 10ms chunks
        for i in range(0, num_samples, chunk_size):
            end_idx = min(i + chunk_size, num_samples)
            chunk_t = t[i:end_idx]
            chunk_size_actual = len(chunk_t)
            
            # Get current time in seconds
            current_time = chunk_t[0]
            
            # Look up parameters at this time
            entrainment_freq = self.entrainment_curve.get_value_at_time(current_time)
            volume = self.volume_curve.get_value_at_time(current_time)
            base_freq = self.base_freq_curve.get_value_at_time(current_time)
            
            # Generate carrier wave
            carrier = np.sin(2 * np.pi * base_freq * chunk_t)
            
            # Generate modulation envelope (on/off isochronic pulses)
            envelope = 0.5 * (1 + np.sign(np.sin(2 * np.pi * entrainment_freq * chunk_t)))
            
            # Apply envelope to carrier with volume adjustment
            chunk_output = carrier * envelope * volume
            
            # Add to output
            output[i:end_idx] = chunk_output
        
        # Apply fade in/out (10ms fade)
        fade_samples = min(int(0.01 * sample_rate), num_samples // 10)
        if fade_samples > 0:
            # Fade in
            output[:fade_samples] *= np.linspace(0, 1, fade_samples)
            # Fade out
            output[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return output, sample_rate
    
    def save_to_file(self, filepath):
        """Save preset to a .sin file"""
        import json
        
        data = {
            "name": self.name,
            "entrainment_points": [{"time": p.time, "value": p.value} for p in self.entrainment_curve.control_points],
            "volume_points": [{"time": p.time, "value": p.value} for p in self.volume_curve.control_points],
            "base_freq_points": [{"time": p.time, "value": p.value} for p in self.base_freq_curve.control_points]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath):
        """Load preset from a .sin file"""
        import json
        
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
        
        return preset

class NameDialog(QDialog):
    """Dialog for entering a preset name"""
    def __init__(self, current_name="New Preset", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preset Name")
        layout = QVBoxLayout()
        
        self.name_edit = QLineEdit(current_name)
        layout.addWidget(QLabel("Enter preset name:"))
        layout.addWidget(self.name_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_name(self):
        return self.name_edit.text()

class SineEditorWindow(QMainWindow):
    """Main window for the SINE Editor application"""
    def __init__(self):
        super().__init__()
        self.preset = SinePreset()
        self.current_time = 0.0
        self.total_duration = self.preset.get_duration()
        self.playing = False
        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(100)
        self.playback_timer.timeout.connect(self.update_playback_time)
        self.play_obj = None
        self._playback_duration = 0.0
        self._playback_start_time = None
        self.init_ui()
        self.update_time_display()
    
    def init_ui(self):
        self.setWindowTitle("SINE Editor")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create menu bar
        self.create_menu()
        
        # Create track list section
        tracks_layout = QVBoxLayout()
        
        # List view for track selection
        self.track_list = QListWidget()
        self.track_list.addItem("Preset details")
        self.track_list.addItem("Background noise")
        self.track_list.addItem("Entrainment Track 1")
        self.track_list.setFixedWidth(200)
        self.track_list.setCurrentRow(2)  # Select Entrainment Track 1 by default
        
        # Editor section
        editor_layout = QVBoxLayout()
        
        # Entrainment frequency editor
        entrainment_label = QLabel("Entrainment frequency (Isochronic pulses)")
        self.entrainment_editor = CurveEditor(
            "", 
            self.preset.entrainment_curve,
            min_value=MIN_ENTRAINMENT_FREQ,
            max_value=MAX_ENTRAINMENT_FREQ,
            value_unit="Hz"
        )
        self.entrainment_editor.point_changed.connect(self.update_duration)
        
        # Volume editor
        volume_label = QLabel("Volume")
        self.volume_editor = CurveEditor(
            "",
            self.preset.volume_curve,
            min_value=0,
            max_value=1,
            value_unit=""
        )
        self.volume_editor.point_changed.connect(self.update_duration)
        
        # Base frequency editor
        base_freq_label = QLabel("Base frequency")
        self.base_freq_editor = CurveEditor(
            "",
            self.preset.base_freq_curve,
            min_value=MIN_BASE_FREQ,
            max_value=MAX_BASE_FREQ,
            value_unit="Hz"
        )
        self.base_freq_editor.point_changed.connect(self.update_duration)
        
        # Add editors to layout
        editor_layout.addWidget(entrainment_label)
        editor_layout.addWidget(self.entrainment_editor)
        editor_layout.addWidget(volume_label)
        editor_layout.addWidget(self.volume_editor)
        editor_layout.addWidget(base_freq_label)
        editor_layout.addWidget(self.base_freq_editor)
        
        # Track volume control
        track_volume_layout = QHBoxLayout()
        track_volume_layout.addWidget(QLabel("Track volume"))
        self.track_volume_slider = QSlider(Qt.Horizontal)
        self.track_volume_slider.setRange(0, 100)
        self.track_volume_slider.setValue(100)
        track_volume_layout.addWidget(self.track_volume_slider)
        track_volume_layout.addWidget(QLabel("100%"))
        
        editor_layout.addLayout(track_volume_layout)
        
        # Playback controls
        playback_layout = QHBoxLayout()
        
        # Time display
        self.time_label = QLabel("00:00:00")
        
        # Transport controls
        self.rew_button = QPushButton("<<")
        self.play_button = QPushButton(">")
        
        # Volume display text
        volume_text = QLabel("Volume")
        
        playback_layout.addWidget(self.rew_button)
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(volume_text)
        
        # Combine layouts
        main_split = QHBoxLayout()
        main_split.addWidget(self.track_list)
        main_split.addLayout(editor_layout)
        
        main_layout.addLayout(main_split)
        main_layout.addWidget(self.time_label)
        main_layout.addLayout(playback_layout)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Connect signals
        self.play_button.clicked.connect(self.toggle_playback)
        self.rew_button.clicked.connect(self.rewind)
    
    def create_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.triggered.connect(self.new_preset)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open...', self)
        open_action.triggered.connect(self.open_preset)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_preset)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.triggered.connect(self.save_preset_as)
        file_menu.addAction(save_as_action)
        
        export_action = QAction('Export Audio...', self)
        export_action.triggered.connect(self.export_audio)
        file_menu.addAction(export_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        add_point_action = QAction('Add Point', self)
        edit_menu.addAction(add_point_action)
        
        remove_point_action = QAction('Remove Selected Point', self)
        edit_menu.addAction(remove_point_action)
        
        # Preset menu
        preset_menu = menubar.addMenu('Preset')
        
        rename_action = QAction('Rename Preset...', self)
        rename_action.triggered.connect(self.rename_preset)
        preset_menu.addAction(rename_action)
        
        # Help menu
        help_menu = menubar.addMenu('?')
        
        about_action = QAction('About SINE Editor', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def new_preset(self):
        dialog = NameDialog(parent=self)
        if dialog.exec_():
            name = dialog.get_name()
            self.preset = SinePreset(name)
            self.update_editors()
            self.update_duration()
    
    def open_preset(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Preset", "", "SINE Preset Files (*.sin);;All Files (*)"
        )
        
        if filepath:
            try:
                self.preset = SinePreset.load_from_file(filepath)
                self.update_editors()
                self.update_duration()
                self.setWindowTitle(f"SINE Editor - {self.preset.name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open preset: {str(e)}")
    
    def save_preset(self):
        # If we haven't saved before, do Save As
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", self.preset.name, "SINE Preset Files (*.sin)"
        )
        
        if filepath:
            try:
                # Add extension if missing
                if not filepath.lower().endswith('.sin'):
                    filepath += '.sin'
                    
                self.preset.save_to_file(filepath)
                QMessageBox.information(self, "Save Preset", "Preset saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save preset: {str(e)}")
    
    def save_preset_as(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Preset As", self.preset.name, "SINE Preset Files (*.sin)"
        )
        
        if filepath:
            try:
                # Add extension if missing
                if not filepath.lower().endswith('.sin'):
                    filepath += '.sin'
                    
                self.preset.save_to_file(filepath)
                QMessageBox.information(self, "Save Preset", "Preset saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save preset: {str(e)}")
    
    def export_audio(self):
        filepath, filter_used = QFileDialog.getSaveFileName(
            self, "Export Audio", self.preset.name, 
            "WAV Files (*.wav);;FLAC Files (*.flac);;MP3 Files (*.mp3)"
        )
        
        if filepath:
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
                    _, ext = os.path.splitext(filepath)
                    file_format = ext.lower().lstrip('.')
                
                # Add appropriate extension if missing
                if not filepath.lower().endswith(f".{file_format}"):
                    filepath += f".{file_format}"
                
                # Generate audio
                audio_data, sample_rate = self.preset.generate_audio()
                
                # Save audio
                if file_format.lower() == "wav":
                    sf.write(filepath, audio_data, sample_rate)
                elif file_format.lower() == "flac":
                    sf.write(filepath, audio_data, sample_rate, format="FLAC")
                elif file_format.lower() == "mp3":
                    try:
                        # First write to temporary WAV
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                            temp_wav = tmp.name
                        
                        sf.write(temp_wav, audio_data, sample_rate)
                        
                        # Convert to MP3 using pydub
                        from pydub import AudioSegment
                        sound = AudioSegment.from_wav(temp_wav)
                        sound.export(filepath, format="mp3", bitrate="192k")
                        
                        # Remove temporary file
                        os.unlink(temp_wav)
                    except Exception as e:
                        raise Exception(f"Failed to export as MP3: {str(e)}")
                
                QMessageBox.information(
                    self, "Export Audio", 
                    f"Audio exported successfully to:\n{filepath}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export audio: {str(e)}")
    
    def rename_preset(self):
        dialog = NameDialog(self.preset.name, parent=self)
        if dialog.exec_():
            name = dialog.get_name()
            self.preset.name = name
            self.setWindowTitle(f"SINE Editor - {name}")
    
    def update_editors(self):
        """Update the editors with the current preset data"""
        self.entrainment_editor.curve = self.preset.entrainment_curve
        self.volume_editor.curve = self.preset.volume_curve
        self.base_freq_editor.curve = self.preset.base_freq_curve
        
        self.entrainment_editor.update()
        self.volume_editor.update()
        self.base_freq_editor.update()
    
    def update_duration(self):
        """Update duration display based on current preset"""
        self.total_duration = self.preset.get_duration()
        if self.current_time > self.total_duration:
            self.current_time = self.total_duration
        self.update_time_display()

    def format_time(self, value):
        """Format seconds as mm:ss:cc text."""
        value = float(value)
        if not np.isfinite(value):
            value = 0.0
        value = max(0.0, value)
        minutes = int(value) // 60
        seconds = int(value) % 60
        centiseconds = int((value - int(value)) * 100)
        return f"{minutes:02d}:{seconds:02d}:{centiseconds:02d}"

    def update_time_display(self):
        """Update the time label with current and total duration."""
        self.time_label.setText(f"{self.format_time(self.current_time)} / {self.format_time(self.total_duration)}")

    def update_playback_time(self):
        """Update playback position while audio is playing."""
        if not self.playing or self._playback_start_time is None:
            return
        elapsed = time.time() - self._playback_start_time
        if self.play_obj and not self.play_obj.is_playing():
            self.stop_playback(reset_position=True)
            return
        self.current_time = min(elapsed, self._playback_duration)
        self.update_time_display()
        if elapsed >= self._playback_duration:
            self.stop_playback(reset_position=True)

    def toggle_playback(self):
        """Toggle playback of the preset"""
        if self.playing:
            self.stop_playback(reset_position=True)
        else:
            self.start_playback()

    def start_playback(self):
        """Start playback of the preset"""
        self.total_duration = self.preset.get_duration()
        audio_data, sample_rate = self.preset.generate_audio()
        if audio_data.size == 0:
            QMessageBox.warning(self, "Playback", "Preset does not contain any audio to play.")
            return
        audio_data = np.nan_to_num(audio_data, nan=0.0)
        peak = np.max(np.abs(audio_data))
        if peak > 1.0:
            audio_data = audio_data / peak
        audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
        try:
            import simpleaudio as sa
        except ImportError:
            QMessageBox.critical(self, "Playback Error", "simpleaudio is required for playback preview.")
            return
        self.stop_playback(reset_position=True)
        try:
            self.play_obj = sa.play_buffer(audio_int16.tobytes(), 1, 2, sample_rate)
        except Exception as exc:
            self.play_obj = None
            QMessageBox.critical(self, "Playback Error", f"Failed to start playback: {exc}")
            return
        self.playing = True
        self.current_time = 0.0
        self._playback_duration = max(audio_data.size / float(sample_rate) if sample_rate else 0.0, self.total_duration)
        self._playback_start_time = time.time()
        self.play_button.setText("||")
        self.update_time_display()
        self.playback_timer.start()

    def stop_playback(self, reset_position=False):
        """Stop playback of the preset"""
        if self.play_obj is not None:
            try:
                self.play_obj.stop()
            except Exception:
                pass
            self.play_obj = None
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        self.playing = False
        self.play_button.setText(">")
        self._playback_start_time = None
        self._playback_duration = 0.0
        if reset_position:
            self.current_time = 0.0
        self.update_time_display()

    def rewind(self):
        """Rewind to beginning of the preset"""
        self.stop_playback(reset_position=True)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About SINE Editor", 
                         "SINE Editor 1.0\n\nA tool for creating isochronic tone presets.")

def main():
    app = QApplication(sys.argv)
    window = SineEditorWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
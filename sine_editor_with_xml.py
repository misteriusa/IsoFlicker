"""



This is an extension of the existing sine_editor.py with added XML support.



"""







import sys



import os



import numpy as np



import soundfile as sf



import math



import tempfile



from PyQt5.QtWidgets import (



    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,



    QLabel, QPushButton, QFileDialog, QSlider, QGroupBox, QListWidget, QFrame,



    QMenu, QAction, QMessageBox, QLineEdit, QDialog, QDialogButtonBox, QCheckBox,



    QSpinBox, QRadioButton, QComboBox, QTabWidget



)



from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor



from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject, QSize, QEvent, QTimer







# Import the preset converter



# Import visual preview widget
from visual_preview import VisualPreviewWidget
from preset_converter import validate_preset_file, xml_to_sine_preset, sine_preset_to_xml







# Constants for the application



DEFAULT_BASE_FREQ = 100.0



DEFAULT_ENTRAINMENT_FREQ = 10.0



MIN_ENTRAINMENT_FREQ = 0.5



MAX_ENTRAINMENT_FREQ = 40.0



MIN_BASE_FREQ = 20.0



MAX_BASE_FREQ = 1000.0



DEFAULT_DURATION = 180  # Default duration of 3 minutes (180 seconds)







class ControlPoint:



    """Represents a control point on the curve"""



    def __init__(self, time=0, value=0):



        self.time = time  # Time in seconds



        self.value = value  # Value (frequency or volume)



        self.selected = False



    



    def is_near(self, x, y, width, height, duration, value_min, value_max, tolerance=20):



        """Check if a point is near this control point with given tolerance"""



        # Convert time and value to screen coordinates



        px = int(self.time / duration * width)



        y_factor = 1.0 - (self.value - value_min) / (value_max - value_min)



        py = int(y_factor * height)



        



        # Check if the mouse coordinates are within the tolerance of this point



        return abs(x - px) < tolerance and abs(y - py) < tolerance







class FrequencyDialog(QDialog):



    """Dialog for entering an exact frequency value"""



    def __init__(self, current_value, min_value, max_value, parent=None):



        super().__init__(parent)



        self.current_value = current_value



        self.min_value = min_value



        self.max_value = max_value



        self.init_ui()



        



    def init_ui(self):



        from PyQt5.QtWidgets import QVBoxLayout, QLabel, QDoubleSpinBox, QDialogButtonBox



        



        self.setWindowTitle("Set Exact Value")



        self.setFixedWidth(250)



        layout = QVBoxLayout()



        



        # Create spinner for value input



        self.spinner = QDoubleSpinBox()



        self.spinner.setRange(self.min_value, self.max_value)



        self.spinner.setValue(self.current_value)



        self.spinner.setDecimals(2)  # Two decimal places



        self.spinner.setSingleStep(0.1)  # Small step for fine control



        



        # Add to layout



        layout.addWidget(QLabel("Enter exact value:"))



        layout.addWidget(self.spinner)



        



        # Add buttons



        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)



        buttons.accepted.connect(self.accept)



        buttons.rejected.connect(self.reject)



        layout.addWidget(buttons)



        



        self.setLayout(layout)



    



    def get_value(self):



        return self.spinner.value()







class TrackCurve:



    """Manages a curve with control points for frequency or volume"""



    def __init__(self, min_value=0, max_value=1, default_value=0.5):



        self.control_points = []



        self.min_value = min_value



        self.max_value = max_value



        self.default_value = default_value



        self.selected_point = None



        



        # Add default points at start and end for a straight line



        self.add_point(0, default_value)



        self.add_point(DEFAULT_DURATION, default_value)  # Add point at 3 minutes by default



        



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



        if point in self.control_points and len(self.control_points) > 2:  # Keep at least 2 points for start and end



            # Don't allow removing the first or last point



            if point == self.control_points[0] or point == self.control_points[-1]:



                return False



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



    



    def get_point_near(self, x, y, width, height, duration, tolerance=20):



        """Find a control point near the given coordinates"""



        for point in self.control_points:



            if point.is_near(x, y, width, height, duration, self.min_value, self.max_value, tolerance):



                return point



        return None



        



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



    



    def get_duration(self):



        """Get the duration of the curve (time of last point)"""



        if not self.control_points:



            return DEFAULT_DURATION



        return self.control_points[-1].time



        



    def clear_selection(self):



        """Clear selection for all points"""



        for point in self.control_points:



            point.selected = False



        self.selected_point = None







    def extend_duration(self, new_duration):



        """Extend the duration of the curve to the new duration"""



        if not self.control_points:



            # If no points, add default points



            self.add_point(0, self.default_value)



            self.add_point(new_duration, self.default_value)



            return



            



        # Get the current last point



        last_point = self.control_points[-1]



        



        # If new duration is longer than current duration



        if new_duration > last_point.time:



            # Add a new point at the end with the same value as the current last point



            self.add_point(new_duration, last_point.value)



        



        # If new duration is shorter than current duration



        elif new_duration < last_point.time:



            # Remove all points beyond the new duration



            self.control_points = [p for p in self.control_points if p.time <= new_duration]



            



            # Add a point at exactly the new duration if needed



            if not any(abs(p.time - new_duration) < 0.01 for p in self.control_points):



                # Interpolate value at the new duration



                value = self.get_value_at_time(new_duration)



                self.add_point(new_duration, value)







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



        self.hover_point = None



        self.setMouseTracking(True)  # Enable mouse tracking for hover effects



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



        point_size = 20  # Size for control points



        for i, point in enumerate(self.curve.control_points):



            # First and last points are shown in yellow to indicate they're fixed



            if i == 0 or i == len(self.curve.control_points) - 1:



                painter.setBrush(QBrush(QColor(255, 255, 0)))  # Yellow for end points



                painter.setPen(QPen(QColor(255, 255, 0), 2))



            elif point.selected or point == self.selected_point or point == self.hover_point:



                painter.setBrush(QBrush(QColor(255, 165, 0)))  # Orange for selected/hover



                painter.setPen(QPen(QColor(255, 165, 0), 2))



            else:



                painter.setBrush(QBrush(QColor(0, 255, 0)))



                painter.setPen(QPen(QColor(0, 255, 0), 2))



            



            x = int(point.time / duration * width)



            y_factor = 1.0 - (point.value - self.min_value) / (self.max_value - self.min_value)



            y = int(y_factor * height)



            



            # Draw point - larger rectangle using integer values for all parameters



            half_size = point_size // 2  # Use integer division instead of float division



            painter.drawRect(x - half_size, y - half_size, point_size, point_size)



            



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



            



            # First check if we're clicking on an existing point



            point = self.curve.get_point_near(event.x(), event.y(), width, height, duration)



            



            if point:



                # Clear previous selection



                self.curve.clear_selection()



                



                # Select new point



                self.selected_point = point



                point.selected = True



                self.dragging = True



                self.update()



            else:



                # Check if we're clicking on a line segment



                on_line, time, value = self.curve.point_on_line_segment(



                    event.x(), event.y(), width, height, duration)



                



                if on_line:



                    # Clear previous selection



                    self.curve.clear_selection()



                    



                    # Add and select new point



                    new_point = self.curve.add_point(time, value)



                    self.selected_point = new_point



                    new_point.selected = True



                    self.dragging = True



                    self.update()



                    self.point_changed.emit()



                else:



                    # If not on point or line, just clear selection



                    self.curve.clear_selection()



                    self.selected_point = None



                    self.update()



    



    def mouseDoubleClickEvent(self, event):



        """Handle double click to set exact value"""



        width = self.width()



        height = self.height()



        duration = max(180, self.curve.get_duration())



        



        # Check if we're double-clicking on an existing point



        point = self.curve.get_point_near(event.x(), event.y(), width, height, duration)



        



        if point:



            # Show dialog to set exact value



            dialog = FrequencyDialog(



                point.value, 



                self.min_value, 



                self.max_value, 



                parent=self



            )



            



            if dialog.exec_():



                # Update point value



                point.value = dialog.get_value()



                self.update()



                self.point_changed.emit()



    



    def mouseReleaseEvent(self, event):



        self.dragging = False



    



    def mouseMoveEvent(self, event):



        width = self.width()



        height = self.height()



        duration = max(180, self.curve.get_duration())



        



        # Check for hover effects



        hover_point = self.curve.get_point_near(event.x(), event.y(), width, height, duration)



        if hover_point != self.hover_point:



            self.hover_point = hover_point



            self.update()



        



        # Handle dragging of selected point



        if self.dragging and self.selected_point:



            # Don't allow dragging the first or last point horizontally



            if self.selected_point == self.curve.control_points[0] or self.selected_point == self.curve.control_points[-1]:



                # Only allow vertical movement for first and last points



                value_factor = 1.0 - event.y() / height



                value = self.min_value + value_factor * (self.max_value - self.min_value)



                value = max(self.min_value, min(self.max_value, value))



                self.selected_point.value = value



            else:



                # Normal point movement (horizontal and vertical)



                time = duration * event.x() / width



                value_factor = 1.0 - event.y() / height



                value = self.min_value + value_factor * (self.max_value - self.min_value)



                



                # Clamp values



                time = max(0, min(time, duration))



                value = max(self.min_value, min(self.max_value, value))



                



                self.selected_point.time = time



                self.selected_point.value = value



            



            # Re-sort points



            self.curve.control_points.sort(key=lambda p: p.time)



            



            self.update()



            self.point_changed.emit()



    



    def show_context_menu(self, position):



        """Show context menu with options for the selected point"""



        width = self.width()



        height = self.height()



        duration = max(180, self.curve.get_duration())



        



        # Check if right-clicking on a point



        point = self.curve.get_point_near(position.x(), position.y(), width, height, duration)



        



        if point:



            # Update selection



            self.curve.clear_selection()



            self.selected_point = point



            point.selected = True



            self.update()



            



            # Create context menu



            menu = QMenu(self)



            



            # Don't allow deleting end points



            if point != self.curve.control_points[0] and point != self.curve.control_points[-1]:



                delete_action = QAction("Delete Point", self)



                delete_action.triggered.connect(self.delete_selected_point)



                menu.addAction(delete_action)



            



            set_value_action = QAction("Set Exact Value...", self)



            set_value_action.triggered.connect(self.set_exact_value)



            menu.addAction(set_value_action)



            



            menu.exec_(self.mapToGlobal(position))



    



    def set_exact_value(self):



        """Show dialog to set exact value for selected point"""



        if self.selected_point:



            dialog = FrequencyDialog(



                self.selected_point.value, 



                self.min_value, 



                self.max_value, 



                parent=self



            )



            



            if dialog.exec_():



                # Update point value



                self.selected_point.value = dialog.get_value()



                self.update()



                self.point_changed.emit()



    



    def delete_selected_point(self):



        """Delete the currently selected control point"""



        if self.selected_point:



            # Don't allow deleting end points



            if self.selected_point != self.curve.control_points[0] and self.selected_point != self.curve.control_points[-1]:



                if self.curve.remove_point(self.selected_point):



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
        
        # Add carrier and modulation type settings
        self.carrier_type = WaveformType.SINE if 'WaveformType' in globals() else "sine"
        self.modulation_type = ModulationType.SQUARE if 'ModulationType' in globals() else "square"
        
        # Add text overlays support
        self.text_overlays = []
        
        # Add advanced settings
        self.sync_audio_visual = True
        self.tone_volume = 0.8  # Separate from main volume curve
        self.enable_subsonic = False
        self.subsonic_frequency = 7.83  # Default Schumann resonance
        self.subsonic_volume = 0.3
        self.selected_format = "mp4"  # Default format
        self.visual_effect_type = "pulse"  # Default visual effect
        self.visual_intensity = 0.5  # Default visual intensity
    
    def get_duration(self):
        """Get the total duration of the preset"""
        return max(
            self.entrainment_curve.get_duration(),
            self.volume_curve.get_duration(),
            self.base_freq_curve.get_duration(),
            DEFAULT_DURATION  # Ensure minimum duration
        )
    
    def set_duration(self, duration):
        """Set the duration for all curves in the preset"""
        self.entrainment_curve.extend_duration(duration)
        self.volume_curve.extend_duration(duration)
        self.base_freq_curve.extend_duration(duration)

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
            
            # Generate carrier wave with appropriate waveform type
            if hasattr(self, 'carrier_type') and hasattr(self.carrier_type, 'value'):
                carrier_type = self.carrier_type.value
            else:
                carrier_type = getattr(self, 'carrier_type', "sine")
                
            if carrier_type == "sine" or carrier_type == WaveformType.SINE if 'WaveformType' in globals() else None:
                carrier = np.sin(2 * np.pi * base_freq * chunk_t)
            elif carrier_type == "square" or carrier_type == WaveformType.SQUARE if 'WaveformType' in globals() else None:
                carrier = np.sign(np.sin(2 * np.pi * base_freq * chunk_t))
            elif carrier_type == "triangle" or carrier_type == WaveformType.TRIANGLE if 'WaveformType' in globals() else None:
                carrier = 2 * np.abs(2 * (base_freq * chunk_t - np.floor(base_freq * chunk_t + 0.5))) - 1
            elif carrier_type == "sawtooth" or carrier_type == WaveformType.SAWTOOTH if 'WaveformType' in globals() else None:
                carrier = 2 * (base_freq * chunk_t - np.floor(base_freq * chunk_t + 0.5))
            else:
                # Default to sine wave
                carrier = np.sin(2 * np.pi * base_freq * chunk_t)
            
            # Generate modulation envelope
            if hasattr(self, 'modulation_type') and hasattr(self.modulation_type, 'value'):
                modulation_type = self.modulation_type.value
            else:
                modulation_type = getattr(self, 'modulation_type', "square")
                
            if modulation_type == "square" or modulation_type == ModulationType.SQUARE if 'ModulationType' in globals() else None:
                # Sharp on/off isochronic pulses
                envelope = 0.5 * (1 + np.sign(np.sin(2 * np.pi * entrainment_freq * chunk_t)))
            elif modulation_type == "sine" or modulation_type == ModulationType.SINE if 'ModulationType' in globals() else None:
                # Smooth sinusoidal modulation (pure monaural beats)
                envelope = 0.5 * (1 + np.sin(2 * np.pi * entrainment_freq * chunk_t))
            elif modulation_type == "triangle" or modulation_type == ModulationType.TRIANGLE if 'ModulationType' in globals() else None:
                # Triangle wave modulation
                mod_wave = 2 * np.abs(2 * (entrainment_freq * chunk_t - np.floor(entrainment_freq * chunk_t + 0.5))) - 1
                envelope = 0.5 * (1 + mod_wave)
            else:
                # Default to square wave
                envelope = 0.5 * (1 + np.sign(np.sin(2 * np.pi * entrainment_freq * chunk_t)))
            
            # Apply envelope to carrier with volume adjustment and tone volume
            chunk_output = carrier * envelope * volume * self.tone_volume
            
            # Add subsonic frequency if enabled
            if hasattr(self, 'enable_subsonic') and self.enable_subsonic:
                subsonic = np.sin(2 * np.pi * self.subsonic_frequency * chunk_t) * self.subsonic_volume
                chunk_output += subsonic
                
            # Add to output
            output[i:end_idx] = chunk_output
        
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
        import json
        
        data = {
            "name": self.name,
            "entrainment_points": [{"time": p.time, "value": p.value} for p in self.entrainment_curve.control_points],
            "volume_points": [{"time": p.time, "value": p.value} for p in self.volume_curve.control_points],
            "base_freq_points": [{"time": p.time, "value": p.value} for p in self.base_freq_curve.control_points],
            "carrier_type": str(self.carrier_type.value if hasattr(self.carrier_type, 'value') else self.carrier_type),
            "modulation_type": str(self.modulation_type.value if hasattr(self.modulation_type, 'value') else self.modulation_type),
            "sync_audio_visual": self.sync_audio_visual,
            "tone_volume": self.tone_volume,
            "enable_subsonic": self.enable_subsonic,
            "subsonic_frequency": self.subsonic_frequency,
            "subsonic_volume": self.subsonic_volume,
            "visual_effect_type": self.visual_effect_type,
            "visual_intensity": self.visual_intensity,
            "text_overlays": self.text_overlays
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath):
        """Load preset from a file (.sin or .xml)"""
        # This part is already well-implemented in your code, just add
        # support for the new attributes when loading
        
        preset = None
        
        try:
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
                
                # Add points from the XML data
                for point_data in preset_data.get("entrainment_points", []):
                    preset.entrainment_curve.add_point(point_data["time"], point_data["value"])
                
                for point_data in preset_data.get("volume_points", []):
                    preset.volume_curve.add_point(point_data["time"], point_data["value"])
                
                for point_data in preset_data.get("base_freq_points", []):
                    preset.base_freq_curve.add_point(point_data["time"], point_data["value"])
                    
                return preset
                
            elif format_type == "json":
                # Load as normal JSON file
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
                
                # Load carrier and modulation types
                if "carrier_type" in data:
                    if 'WaveformType' in globals():
                        try:
                            preset.carrier_type = WaveformType(data["carrier_type"])
                        except:
                            preset.carrier_type = data["carrier_type"]
                    else:
                        preset.carrier_type = data["carrier_type"]
                
                if "modulation_type" in data:
                    if 'ModulationType' in globals():
                        try:
                            preset.modulation_type = ModulationType(data["modulation_type"])
                        except:
                            preset.modulation_type = data["modulation_type"]
                    else:
                        preset.modulation_type = data["modulation_type"]
                
                # Load new attributes with defaults if not present
                preset.sync_audio_visual = data.get("sync_audio_visual", True)
                preset.tone_volume = data.get("tone_volume", 0.8)
                preset.enable_subsonic = data.get("enable_subsonic", False)
                preset.subsonic_frequency = data.get("subsonic_frequency", 7.83)
                preset.subsonic_volume = data.get("subsonic_volume", 0.3)
                preset.visual_effect_type = data.get("visual_effect_type", "pulse")
                preset.visual_intensity = data.get("visual_intensity", 0.5)
                preset.text_overlays = data.get("text_overlays", [])
                
                return preset
            else:
                raise ValueError(f"Unsupported preset format: {format_type}")
                
        except Exception as e:
            print(f"Error loading preset file: {e}")
            if preset is None:
                # Return a default preset if loading failed
                preset = cls(name="Error Preset")
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







class ExportSettingsDialog(QDialog):



    """Dialog for configuring export settings"""



    def __init__(self, parent=None):



        super().__init__(parent)



        self.setWindowTitle("Export Settings")



        self.setMinimumWidth(400)



        layout = QVBoxLayout()



        



        # File format selection



        format_group = QGroupBox("File Format")



        format_layout = QVBoxLayout()



        



        self.wav_radio = QRadioButton("WAV (Uncompressed)")



        self.wav_radio.setChecked(True)



        format_layout.addWidget(self.wav_radio)



        



        self.flac_radio = QRadioButton("FLAC (Lossless Compressed)")



        format_layout.addWidget(self.flac_radio)



        



        self.mp3_radio = QRadioButton("MP3 (Lossy Compressed)")



        format_layout.addWidget(self.mp3_radio)



        



        format_group.setLayout(format_layout)



        layout.addWidget(format_group)



        



        # MP3 quality settings (only enabled when MP3 is selected)



        self.mp3_settings = QGroupBox("MP3 Quality")



        mp3_layout = QHBoxLayout()



        



        mp3_layout.addWidget(QLabel("Bitrate:"))



        self.bitrate_combo = QComboBox()



        self.bitrate_combo.addItems(["128 kbps", "192 kbps", "256 kbps", "320 kbps"])



        self.bitrate_combo.setCurrentIndex(1)  # Default to 192 kbps



        mp3_layout.addWidget(self.bitrate_combo)



        



        self.mp3_settings.setLayout(mp3_layout)



        self.mp3_settings.setEnabled(False)



        layout.addWidget(self.mp3_settings)



        



        # Sample rate settings



        sample_group = QGroupBox("Sample Rate")



        sample_layout = QHBoxLayout()



        



        sample_layout.addWidget(QLabel("Sample Rate:"))



        self.sample_combo = QComboBox()



        self.sample_combo.addItems(["44100 Hz (CD Quality)", "48000 Hz (DVD Quality)", "96000 Hz (Hi-Res)"])



        sample_layout.addWidget(self.sample_combo)



        



        sample_group.setLayout(sample_layout)



        layout.addWidget(sample_group)



        



        # Normalization option



        self.normalize_check = QCheckBox("Normalize audio (prevents clipping)")



        self.normalize_check.setChecked(True)



        layout.addWidget(self.normalize_check)



        



        # Fade in/out options



        fade_group = QGroupBox("Fade In/Out")



        fade_layout = QGridLayout()



        



        fade_layout.addWidget(QLabel("Fade In:"), 0, 0)



        self.fade_in_spin = QSpinBox()



        self.fade_in_spin.setRange(0, 10000)  # 0-10 seconds in ms



        self.fade_in_spin.setValue(100)  # Default 100ms



        self.fade_in_spin.setSuffix(" ms")



        fade_layout.addWidget(self.fade_in_spin, 0, 1)



        



        fade_layout.addWidget(QLabel("Fade Out:"), 1, 0)



        self.fade_out_spin = QSpinBox()



        self.fade_out_spin.setRange(0, 10000)  # 0-10 seconds in ms



        self.fade_out_spin.setValue(100)  # Default 100ms



        self.fade_out_spin.setSuffix(" ms")



        fade_layout.addWidget(self.fade_out_spin, 1, 1)



        



        fade_group.setLayout(fade_layout)



        layout.addWidget(fade_group)



        



        # Buttons



        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)



        buttons.accepted.connect(self.accept)



        buttons.rejected.connect(self.reject)



        layout.addWidget(buttons)



        



        self.setLayout(layout)



        



        # Connect signals



        self.mp3_radio.toggled.connect(self.mp3_settings.setEnabled)



    



    def get_settings(self):



        """Get the selected export settings"""



        # Determine file format



        if self.wav_radio.isChecked():



            file_format = "wav"



        elif self.flac_radio.isChecked():



            file_format = "flac"



        else:



            file_format = "mp3"



        



        # Get MP3 bitrate if applicable



        bitrate = "192k"  # Default



        if file_format == "mp3":



            bitrate = self.bitrate_combo.currentText().split()[0] + "k"



        



        # Get sample rate



        sample_rate = 44100  # Default



        if self.sample_combo.currentIndex() == 1:



            sample_rate = 48000



        elif self.sample_combo.currentIndex() == 2:



            sample_rate = 96000



        



        return {



            "format": file_format,



            "bitrate": bitrate,



            "sample_rate": sample_rate,



            "normalize": self.normalize_check.isChecked(),



            "fade_in": self.fade_in_spin.value() / 1000.0,  # Convert to seconds



            "fade_out": self.fade_out_spin.value() / 1000.0  # Convert to seconds



        }








# Custom event to handle playback completion
class QPlaybackFinishedEvent(QEvent):
    def __init__(self):
        super().__init__(QEvent.Type(QEvent.User + 1))

class SineEditorWidget(QWidget):
    """Widget for editing SINE presets with entrainment, volume, and frequency curves."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preset = SinePreset()
        self.current_file_path = None
        self.setup_ui()
        
        # Initialize audio preview variables
        self.stream = None
        self.p = None
        self.play_thread = None
        
        # Initialize the original window reference (will be set by the main app)
        self.original_window = None
    
    def setup_ui(self):
        """Set up the UI components"""
        main_layout = QVBoxLayout()
        
        # Create toolbar with buttons
        toolbar_layout = QHBoxLayout()
        
        # New preset button
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_preset)
        toolbar_layout.addWidget(new_btn)
        
        # Open button
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_preset)
        toolbar_layout.addWidget(open_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_preset)
        toolbar_layout.addWidget(save_btn)
        
        # Export button (with menu)
        export_btn = QPushButton("Export")
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
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))
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
        main_layout.addWidget(separator)
        
        # Duration controls
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration:"))
        
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
        
        # Match video duration button
        match_video_btn = QPushButton("Match Video Length")
        match_video_btn.setToolTip("Set duration to match the selected video")
        match_video_btn.clicked.connect(self.match_video_duration)
        duration_layout.addWidget(match_video_btn)
        
        # Connect duration controls
        self.min_spin.valueChanged.connect(self.update_duration)
        self.sec_spin.valueChanged.connect(self.update_duration)
        
        duration_layout.addStretch()
        
        # Protocol presets
        duration_layout.addWidget(QLabel("Protocol:"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItem("Custom")
        self.protocol_combo.addItem("ADHD/Beta")
        self.protocol_combo.addItem("Anxiety/Alpha")
        self.protocol_combo.addItem("Insomnia/Theta-Delta")
        self.protocol_combo.currentTextChanged.connect(self.apply_protocol_preset)
        duration_layout.addWidget(self.protocol_combo)
        
        main_layout.addLayout(duration_layout)
        
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
        
        self.visual_preview = VisualPreviewWidget()
        preview_layout.addWidget(self.visual_preview, 1)  # Give it a stretch factor
        
        main_layout.addLayout(preview_layout)
        
        self.setLayout(main_layout)
    
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
            from integrated_isoflicker import PROTOCOL_PRESETS
            
            if protocol_name in PROTOCOL_PRESETS:
                protocol = PROTOCOL_PRESETS[protocol_name]
                
                # Clear existing points
                self.preset.entrainment_curve.control_points = []
                
                # Check if we should scale to video duration
                video_duration = None
                
                # Try to get video duration if available
                if hasattr(self, 'original_window') and self.original_window:
                    original_window = self.original_window
                    if hasattr(original_window, 'video_path') and original_window.video_path:
                        try:
                            try:
                                from moviepy.editor import VideoFileClip  # type: ignore
                            except Exception:
                                from moviepy.video.io.VideoFileClip import VideoFileClip  # type: ignore
                            video_clip = VideoFileClip(original_window.video_path)
                            video_duration = video_clip.duration
                            video_clip.close()
                        except Exception as e:
                            print(f"Could not get video duration: {e}")
                
                # Calculate scaling factor if video is available
                scaling_factor = 1.0
                original_max_time = max(point["time"] for point in protocol["entrainment_points"])
                
                if video_duration and video_duration > 0 and original_max_time > 0:
                    scaling_factor = video_duration / original_max_time
                    print(f"Scaling protocol by factor: {scaling_factor}")
                
                # Add new points from the protocol, scaled if needed
                for point in protocol["entrainment_points"]:
                    scaled_time = point["time"] * scaling_factor
                    self.preset.entrainment_curve.add_point(scaled_time, point["value"])
                
                # Update UI
                self.entrainment_editor.update()
                self.update_visual_preview()
                
                # Set name
                self.preset.name = protocol["name"]
                if video_duration and scaling_factor != 1.0:
                    self.preset.name += " (Video-Adjusted)"
                self.name_label.setText(self.preset.name)
                
                # Update duration based on scaling
                if video_duration:
                    mins = int(video_duration) // 60
                    secs = int(video_duration) % 60
                else:
                    max_time = max(point.time for point in self.preset.entrainment_curve.control_points)
                    mins = int(max_time) // 60
                    secs = int(max_time) % 60
                
                self.min_spin.setValue(mins)
                self.sec_spin.setValue(secs)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply protocol preset: {str(e)}")
    
    def update_visual_preview(self):
        """Update the visual preview based on the current settings"""
        try:
            # Get the current entrainment frequency (at time 0)
            entrainment_freq = self.preset.entrainment_curve.get_value_at_time(0)
            
            # Update the visual preview
            if self.visual_preview:
                if self.stop_btn.isEnabled():  # If playback is active
                    # When playing, leave preview running but update frequency
                    self.visual_preview.update_frequency(entrainment_freq)
                else:
                    # When not playing, show a static preview
                    self.visual_preview.show_static_preview(entrainment_freq)
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
                
                # Reset protocol to custom (since we loaded a file)
                self.protocol_combo.setCurrentIndex(0)
                
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
            backend = None
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

                self.play_thread = threading.Thread(target=play_audio_pa, daemon=True)
                self.play_thread.start()
                backend = 'pyaudio'
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

                    self.play_thread = threading.Thread(target=monitor_sa, daemon=True)
                    self.play_thread.start()
                    backend = 'simpleaudio'
                except Exception:
                    # Fallback to sounddevice
                    try:
                        import sounddevice as sd
                        sd.play(preview_data.astype(np.float32), samplerate=sample_rate, blocking=False)

                        def monitor_sd():
                            import time as _t
                            _t.sleep(preview_length / float(sample_rate))
                            QApplication.postEvent(self, QPlaybackFinishedEvent())

                        self.play_thread = threading.Thread(target=monitor_sd, daemon=True)
                        self.play_thread.start()
                        backend = 'sounddevice'
                    except Exception as e:
                        raise RuntimeError(
                            "Audio backend not available. Install one of: pyaudio, simpleaudio, or sounddevice"
                        ) from e

            # Update UI
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            # Start visual preview
            entrainment_freq = self.preset.entrainment_curve.get_value_at_time(0)  # Get starting frequency
            if hasattr(self, 'visual_preview') and self.visual_preview:
                self.visual_preview.start_preview(effect_type="color_cycle", frequency=entrainment_freq)

            # Remember backend for stop
            self._preview_backend = backend
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Could not play preview: {str(e)}")
    
    def stop_preview(self):
        """Stop the currently playing preview"""
        try:
            if getattr(self, '_preview_backend', None) == 'pyaudio':
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
            elif getattr(self, '_preview_backend', None) == 'simpleaudio':
                if getattr(self, "_sa_obj", None):
                    try:
                        self._sa_obj.stop()
                    except Exception:
                        pass
                    self._sa_obj = None
            elif getattr(self, '_preview_backend', None) == 'sounddevice':
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
        if hasattr(self, "visual_preview") and self.visual_preview:
            try:
                self.visual_preview.stop_preview()
            except Exception as e:
                print(f"Error stopping visual preview: {e}")
    
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
        
        if not video_path:
            QMessageBox.warning(self, "Error", "Please select a video file in the Basic Mode tab first.")
            return
            
        try:
            # Get video duration using MoviePy
            try:
                from moviepy.editor import VideoFileClip  # type: ignore
            except Exception:
                from moviepy.video.io.VideoFileClip import VideoFileClip  # type: ignore
            video_clip = VideoFileClip(video_path)
            video_duration = video_clip.duration
            video_clip.close()
            
            # Update the duration controls
            mins = int(video_duration) // 60
            secs = int(video_duration) % 60
            self.min_spin.setValue(mins)
            self.sec_spin.setValue(secs)
            
            # Update preset duration
            self.preset.set_duration(video_duration)
            
            # Force redraw of editors
            self.entrainment_editor.update()
            self.volume_editor.update()
            self.base_freq_editor.update()
            
            QMessageBox.information(self, "Duration Updated", 
                                  f"Preset duration set to match video: {mins} minutes and {secs} seconds.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get video duration: {str(e)}")
    
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
        
        if not video_path:
            QMessageBox.warning(self, "Error", "Please select a video file in the Basic Mode tab first.")
            return
            
        # Create processing options dialog
        try:
            process_dialog = QDialog(self)
            process_dialog.setWindowTitle("Process Video with Timeline Settings")
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
            visual_type_combo.addItems(["Flash", "Pulse", "Color Cycle", "Blur"])
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
            
            # Connect volume slider to label
            def update_volume_label(value):
                volume_label.setText(f"{value}%")
            audio_volume_slider.valueChanged.connect(update_volume_label)
            
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
                    "preset": self.preset
                }
                
                process_dialog.accept()
                
                # Call the main window's process_with_timeline function
                if hasattr(main_window, 'process_with_timeline'):
                    main_window.process_with_timeline(options)
                else:
                    QMessageBox.warning(self, "Error", "Processing function not available.")
            
            process_btn.clicked.connect(start_processing)
            
            # Show dialog
            process_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def event(self, event):
        if isinstance(event, QPlaybackFinishedEvent):
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            return True
        return super(SineEditorWidget, self).event(event)
    
    def event(self, event):
        if isinstance(event, QPlaybackFinishedEvent):
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            return True
        return super(SineEditorWidget, self).event(event)

# Test class to verify indentation
class TestWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("Test widget initialized")


from PyQt5.QtWidgets import (QDialog, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout, 
                           QLineEdit, QDoubleSpinBox, QSlider, QLabel, QComboBox,
                           QSpinBox, QPushButton, QDialogButtonBox, QListWidget, QColorDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class TextOverlay:
    """Class for storing text overlay settings"""
    def __init__(self, text="", start_time=0.0, duration=5.0, 
                 opacity=1.0, font_family="Arial", font_size=24, 
                 color=(255, 255, 255), position="center"):
        self.text = text
        self.start_time = start_time  # in seconds with microsecond precision
        self.duration = duration  # in seconds
        self.opacity = opacity  # 0.0 to 1.0
        self.font_family = font_family
        self.font_size = font_size
        self.color = color
        self.position = position  # "center", "top", "bottom", etc.
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "text": self.text,
            "start_time": self.start_time,
            "duration": self.duration,
            "opacity": self.opacity,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "position": self.position
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            text=data.get("text", ""),
            start_time=data.get("start_time", 0.0),
            duration=data.get("duration", 5.0),
            opacity=data.get("opacity", 1.0),
            font_family=data.get("font_family", "Arial"),
            font_size=data.get("font_size", 24),
            color=data.get("color", (255, 255, 255)),
            position=data.get("position", "center")
        )
    
    def __str__(self):
        """String representation for display in list widget"""
        minutes = int(self.start_time // 60)
        seconds = int(self.start_time % 60)
        milliseconds = int((self.start_time % 1) * 1000)
        
        time_str = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        
        return f"{time_str} - {self.text[:20]}{'...' if len(self.text) > 20 else ''}"


class TextOverlayDialog(QDialog):
    """Dialog for editing text overlays"""
    def __init__(self, overlay=None, parent=None):
        super().__init__(parent)
        self.overlay = overlay or TextOverlay()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Text Overlay Settings")
        layout = QFormLayout()
        
        # Text content
        self.text_edit = QLineEdit(self.overlay.text)
        layout.addRow("Text:", self.text_edit)
        
        # Time controls with separate hour, minute, second fields
        start_time_layout = QHBoxLayout()
        
        # Hours
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(int(self.overlay.start_time // 3600))
        self.hours_spin.valueChanged.connect(self.update_start_time)
        start_time_layout.addWidget(self.hours_spin)
        start_time_layout.addWidget(QLabel("h"))
        
        # Minutes
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(int((self.overlay.start_time % 3600) // 60))
        self.minutes_spin.valueChanged.connect(self.update_start_time)
        start_time_layout.addWidget(self.minutes_spin)
        start_time_layout.addWidget(QLabel("m"))
        
        # Seconds
        self.seconds_spin = QDoubleSpinBox()
        self.seconds_spin.setRange(0, 59.999)
        self.seconds_spin.setValue(self.overlay.start_time % 60)
        self.seconds_spin.setDecimals(3)  # Millisecond precision
        self.seconds_spin.setSingleStep(0.1)
        self.seconds_spin.valueChanged.connect(self.update_start_time)
        start_time_layout.addWidget(self.seconds_spin)
        start_time_layout.addWidget(QLabel("s"))
        
        layout.addRow("Start Time:", start_time_layout)
        
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 3600)
        self.duration_spin.setValue(self.overlay.duration)
        self.duration_spin.setDecimals(3)
        self.duration_spin.setSingleStep(0.5)
        layout.addRow("Duration (seconds):", self.duration_spin)
        
        # Opacity control
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.overlay.opacity * 100))
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel(f"{self.overlay.opacity:.2f}")
        opacity_layout.addWidget(self.opacity_label)
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        layout.addRow("Opacity:", opacity_layout)
        
        # Font settings
        self.font_combo = QComboBox()
        available_fonts = ["Arial", "Times New Roman", "Courier New", "Verdana", "Tahoma"]
        self.font_combo.addItems(available_fonts)
        
        # Set current font if it's in the list, otherwise default to first font
        current_font_idx = self.font_combo.findText(self.overlay.font_family)
        if current_font_idx >= 0:
            self.font_combo.setCurrentIndex(current_font_idx)
        layout.addRow("Font Family:", self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.overlay.font_size)
        layout.addRow("Font Size:", self.font_size_spin)
        
        # Color picker button
        self.color_btn = QPushButton("Set Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.update_color_preview()
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_btn)
        color_layout.addWidget(self.color_preview)
        layout.addRow("Text Color:", color_layout)
        
        # Position options
        self.position_combo = QComboBox()
        positions = ["center", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"]
        self.position_combo.addItems(positions)
        current_pos_idx = self.position_combo.findText(self.overlay.position)
        if current_pos_idx >= 0:
            self.position_combo.setCurrentIndex(current_pos_idx)
        layout.addRow("Position:", self.position_combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def update_opacity_label(self):
        value = self.opacity_slider.value() / 100.0
        self.opacity_label.setText(f"{value:.2f}")
    
    def choose_color(self):
        # Use built-in color picker
        if isinstance(self.overlay.color, tuple):
            # Convert tuple to QColor for the dialog
            r, g, b = self.overlay.color
            initial_color = QColor(r, g, b)
        else:
            initial_color = self.overlay.color
            
        color = QColorDialog.getColor(initial_color, self, "Choose Text Color")
        if color.isValid():
            self.overlay.color = color
            self.update_color_preview()
    
    def update_color_preview(self):
        # Set background color of the preview label
        if isinstance(self.overlay.color, tuple):
            # Handle tuple color format (r, g, b)
            r, g, b = self.overlay.color
            self.color_preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")
        else:
            # Handle QColor object
            self.color_preview.setStyleSheet(f"background-color: rgb({self.overlay.color.red()}, {self.overlay.color.green()}, {self.overlay.color.blue()})")

    def update_start_time(self):
        """Calculate the start time from hours, minutes, and seconds"""
        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        seconds = self.seconds_spin.value()
        
        # Calculate total time in seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds
        self.overlay.start_time = total_seconds
    
    def get_overlay(self):
        """Get the updated text overlay settings"""
        self.overlay.text = self.text_edit.text()
        self.update_start_time()  # Make sure we have the latest start time
        self.overlay.duration = self.duration_spin.value()
        self.overlay.opacity = self.opacity_slider.value() / 100.0
        self.overlay.font_family = self.font_combo.currentText()
        self.overlay.font_size = self.font_size_spin.value()
        self.overlay.position = self.position_combo.currentText()
        return self.overlay


class TextOverlayManager(QWidget):
    """Widget for managing multiple text overlays"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlays = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Overlay list
        self.overlay_list = QListWidget()
        self.overlay_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(QLabel("Text Overlays:"))
        layout.addWidget(self.overlay_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_overlay)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_overlay)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_overlay)
        btn_layout.addWidget(self.delete_btn)
        
        # Move buttons
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.clicked.connect(self.move_overlay_up)
        btn_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.clicked.connect(self.move_overlay_down)
        btn_layout.addWidget(self.move_down_btn)
        
        layout.addLayout(btn_layout)
        
        # Update button states
        self.update_button_states()
        self.overlay_list.itemSelectionChanged.connect(self.update_button_states)
        
        self.setLayout(layout)
    
    def update_overlay_list(self):
        """Update the list widget with current overlays"""
        self.overlay_list.clear()
        for overlay in self.overlays:
            self.overlay_list.addItem(str(overlay))
    
    def update_button_states(self):
        """Enable/disable buttons based on selection"""
        has_selection = len(self.overlay_list.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        # Move buttons
        selected_row = self.overlay_list.currentRow()
        self.move_up_btn.setEnabled(has_selection and selected_row > 0)
        self.move_down_btn.setEnabled(has_selection and 
                                     selected_row < len(self.overlays) - 1)
    
    def add_overlay(self):
        """Add a new text overlay"""
        dialog = TextOverlayDialog(parent=self)
        if dialog.exec_():
            overlay = dialog.get_overlay()
            self.overlays.append(overlay)
            self.update_overlay_list()
            # Select the new item
            self.overlay_list.setCurrentRow(len(self.overlays) - 1)
    
    def edit_overlay(self):
        """Edit the selected overlay"""
        selected_row = self.overlay_list.currentRow()
        if selected_row >= 0:
            dialog = TextOverlayDialog(self.overlays[selected_row], parent=self)
            if dialog.exec_():
                self.overlays[selected_row] = dialog.get_overlay()
                self.update_overlay_list()
                # Reselect the edited item
                self.overlay_list.setCurrentRow(selected_row)
    
    def delete_overlay(self):
        """Delete the selected overlay"""
        selected_row = self.overlay_list.currentRow()
        if selected_row >= 0:
            del self.overlays[selected_row]
            self.update_overlay_list()
            # Update selection
            if self.overlays:
                new_row = min(selected_row, len(self.overlays) - 1)
                self.overlay_list.setCurrentRow(new_row)
            self.update_button_states()
    
    def move_overlay_up(self):
        """Move the selected overlay up in the list"""
        selected_row = self.overlay_list.currentRow()
        if selected_row > 0:
            self.overlays[selected_row], self.overlays[selected_row - 1] = \
                self.overlays[selected_row - 1], self.overlays[selected_row]
            self.update_overlay_list()
            self.overlay_list.setCurrentRow(selected_row - 1)
    
    def move_overlay_down(self):
        """Move the selected overlay down in the list"""
        selected_row = self.overlay_list.currentRow()
        if selected_row < len(self.overlays) - 1:
            self.overlays[selected_row], self.overlays[selected_row + 1] = \
                self.overlays[selected_row + 1], self.overlays[selected_row]
            self.update_overlay_list()
            self.overlay_list.setCurrentRow(selected_row + 1)
    
    def get_overlays(self):
        """Get all the current overlays"""
        return self.overlays
    
    def set_overlays(self, overlays):
        """Set the list of overlays"""
        self.overlays = overlays
        self.update_overlay_list()


"""
IsoFlicker Pro Improvement Installer

This script installs all improvements to the IsoFlicker Pro software:
- Carrier frequency control
- XML preset support
- File size optimization
- Enhanced SINE editor
"""

import os
import sys
import shutil
import tempfile
import re

def update_isoflickergui():
    """Update the isoFlickerGUI.py file to add carrier frequency control"""
    print("Updating isoFlickerGUI.py...")
    
    # Backup the original file
    if os.path.exists("isoFlickerGUI.py"):
        backup_file = "isoFlickerGUI.py.bak"
        shutil.copy2("isoFlickerGUI.py", backup_file)
        print(f"Backup created: {backup_file}")
    else:
        print("Error: isoFlickerGUI.py not found")
        return False
    
    try:
        # Read the original file
        with open("isoFlickerGUI.py", "r") as f:
            original_code = f.read()
        
        # Add carrier frequency control after tone frequency
        pattern = r"(tone_freq_layout\.addWidget\(self\.tone_freq_spin\)\s+)"
        replacement = r"""\1
        carrier_freq_layout = QHBoxLayout()
        carrier_freq_layout.addWidget(QLabel("Carrier Frequency (Hz):"))
        self.carrier_freq_spin = QDoubleSpinBox()
        self.carrier_freq_spin.setRange(20.0, 1000.0)
        self.carrier_freq_spin.setValue(100.0)  # Default to 100Hz
        self.carrier_freq_spin.setSingleStep(10.0)
        carrier_freq_layout.addWidget(self.carrier_freq_spin)
        
        """
        
        updated_code = re.sub(pattern, replacement, original_code)
        
        # Add carrier frequency layout to audio layout
        pattern = r"(audio_layout\.addWidget\(self\.use_audio_check\)\s+audio_layout\.addLayout\(tone_freq_layout\)\s+)"
        replacement = r"""\1audio_layout.addLayout(carrier_freq_layout)
        """
        
        updated_code = re.sub(pattern, replacement, updated_code)
        
        # Update get_config to include carrier frequency
        pattern = r"(\"tone_frequency\": self\.tone_freq_spin\.value\(\),\s+\"tone_volume\": self\.tone_volume_slider\.value\(\) \/ 100,\s+)"
        replacement = r"""\1"carrier_frequency": self.carrier_freq_spin.value(),
            """
        
        updated_code = re.sub(pattern, replacement, updated_code)
        
        # Update generate_isochronic_tone function to use carrier frequency
        pattern = r"(def generate_isochronic_tone\(frequency, duration, sample_rate=44100, volume=0\.5\):)"
        replacement = r"def generate_isochronic_tone(frequency, duration, sample_rate=44100, volume=0.5, carrier_frequency=100.0):"
        
        updated_code = re.sub(pattern, replacement, updated_code)
        
        # Update sine wave generation to use carrier frequency
        pattern = r"(# Create sine wave at the specified frequency\s+sine_wave = np\.sin\(2 \* np\.pi \* frequency \* t\))"
        replacement = r"# Create sine wave at the specified carrier frequency\n    sine_wave = np.sin(2 * np.pi * carrier_frequency * t)"
        
        updated_code = re.sub(pattern, replacement, updated_code)
        
        # Update modulation envelope to use entrainment frequency
        pattern = r"(# Create amplitude modulation envelope for isochronic effect \(square wave\)\s+mod_freq = frequency)"
        replacement = r"# Create amplitude modulation envelope for isochronic effect (square wave)\n    mod_freq = frequency  # Use entrainment frequency for modulation"
        
        updated_code = re.sub(pattern, replacement, updated_code)
        
        # Update FlickerWorker.process_video to pass carrier frequency
        pattern = r"(tone_data, sr = generate_isochronic_tone\(\s+self\.config\[\"tone_frequency\"\],\s+duration,\s+sample_rate,\s+self\.config\[\"tone_volume\"\]\s+\))"
        replacement = r"""tone_data, sr = generate_isochronic_tone(
                    self.config["tone_frequency"], 
                    duration, 
                    sample_rate, 
                    self.config["tone_volume"],
                    self.config.get("carrier_frequency", 100.0)  # Pass carrier frequency
                )"""
        
        updated_code = re.sub(pattern, replacement, updated_code)
        
        # Write the updated code to the file
        with open("isoFlickerGUI.py", "w") as f:
            f.write(updated_code)
        
        print("Successfully updated isoFlickerGUI.py")
        return True
        
    except Exception as e:
        print(f"Error updating isoFlickerGUI.py: {e}")
        # Restore the backup if an error occurred
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, "isoFlickerGUI.py")
            print("Restored original file from backup")
        return False

def update_integrated_file():
    """Update the integrated_isoflicker.py file using the updater"""
    try:
        # Check if the updater module exists
        if not os.path.exists("integrated_isoflicker_updater.py"):
            print("Error: integrated_isoflicker_updater.py not found")
            return False
        
        # Import and run the updater
        sys.path.append(os.getcwd())
        from integrated_isoflicker_updater import update_integrated_isoflicker
        
        result = update_integrated_isoflicker()
        return result
    
    except Exception as e:
        print(f"Error running integrated_isoflicker_updater: {e}")
        return False

def update_sine_editor():
    """Update the sine_editor.py file with improved version"""
    print("Updating sine_editor.py...")
    
    # Backup the original file if it exists
    if os.path.exists("sine_editor.py"):
        backup_file = "sine_editor.py.bak"
        shutil.copy2("sine_editor.py", backup_file)
        print(f"Backup created: {backup_file}")
    
    try:
        # Check if the new editor file exists
        if not os.path.exists("sine_editor_with_xml.py"):
            print("Error: sine_editor_with_xml.py not found")
            return False
        
        # Replace the original with the improved version
        shutil.copy2("sine_editor_with_xml.py", "sine_editor.py")
        print("Successfully updated sine_editor.py")
        return True
    
    except Exception as e:
        print(f"Error updating sine_editor.py: {e}")
        # Restore the backup if an error occurred
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, "sine_editor.py")
            print("Restored original file from backup")
        return False

def main():
    """Main function to install all improvements"""
    print("=== IsoFlicker Pro Improvement Installer ===")
    print("This script will update your IsoFlicker Pro installation with:")
    print("  - Carrier frequency control in Basic Mode")
    print("  - XML preset support")
    print("  - File size optimization")
    print("  - Enhanced SINE editor")
    print()
    
    # Check for required files
    missing_files = []
    for file in ["isoFlickerGUI.py", "integrated_isoflicker.py", "sine_editor.py"]:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"Error: Missing required files: {', '.join(missing_files)}")
        print("Please run this script in the IsoFlicker Pro directory.")
        return False
    
    # Check for new files
    missing_new_files = []
    for file in ["preset_converter.py", "file_optimizer.py", "integrated_isoflicker_updater.py", "sine_editor_with_xml.py"]:
        if not os.path.exists(file):
            missing_new_files.append(file)
    
    if missing_new_files:
        print(f"Error: Missing new improvement files: {', '.join(missing_new_files)}")
        print("Please make sure all required files are in the current directory.")
        return False
    
    # Apply updates
    print("\nApplying updates...")
    
    # Update isoFlickerGUI.py
    if not update_isoflickergui():
        print("Failed to update isoFlickerGUI.py. Installation aborted.")
        return False
    
    # Update integrated_isoflicker.py
    if not update_integrated_file():
        print("Failed to update integrated_isoflicker.py. Installation aborted.")
        return False
    
    # Update sine_editor.py
    if not update_sine_editor():
        print("Failed to update sine_editor.py. Installation aborted.")
        return False
    
    print("\n=== Installation Complete! ===")
    print("All improvements have been installed successfully.")
    print("Restart IsoFlicker Pro to apply the changes.")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\nInstallation failed. Please check the error messages above.")
    
    input("\nPress Enter to exit...")
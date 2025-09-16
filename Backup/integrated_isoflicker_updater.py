"""
This script updates the integrated_isoflicker.py file by adding file format support
and file size optimization.

Run this script to update the IsoFlicker Pro software with the new features.
"""

import os
import sys
import shutil
import tempfile
import re

def update_integrated_isoflicker():
    """Update the integrated_isoflicker.py file with new features"""
    print("Updating integrated_isoflicker.py with new features...")
    
    # Backup the original file
    if os.path.exists("integrated_isoflicker.py"):
        backup_file = "integrated_isoflicker.py.bak"
        shutil.copy2("integrated_isoflicker.py", backup_file)
        print(f"Backup created: {backup_file}")
    else:
        print("Error: integrated_isoflicker.py not found")
        return False
    
    try:
        # Read the original file
        with open("integrated_isoflicker.py", "r") as f:
            original_code = f.read()
        
        # Update the imports section to include preset_converter and file_optimizer
        import_pattern = re.compile(r"(import sys\s+import os.*?import threading.*?)(\s+# Check if)", re.DOTALL)
        new_imports = r"""\1
import xml.etree.ElementTree as ET
try:
    from preset_converter import validate_preset_file, xml_to_sine_preset
    from file_optimizer import VideoOptimizer, CompressionDialog
except ImportError:
    print("Warning: Some modules not found. File optimization disabled.")

\2"""
        updated_code = import_pattern.sub(new_imports, original_code)
        
        # Update the EnhancedFlickerWorker class to include compression
        worker_pattern = re.compile(r"(class EnhancedFlickerWorker\(FlickerWorker\):.*?)(\s+def __init__\s*\(self, video_path, output_path, mode, config, isochronic_audio=None\):.*?)(\s+def process_video\(self\):)", re.DOTALL)
        new_worker_init = r"""\1\2
        self.compression_settings = None  # Optional compression settings
\3"""
        updated_code = worker_pattern.sub(new_worker_init, updated_code)
        
        # Update the process_video method to include compression
        process_end_pattern = re.compile(r"(self.progress_signal.emit\(100\)\s+self.finished_signal.emit\(output_file\))", re.DOTALL)
        new_process_end = r"""            # Apply compression if requested
            if hasattr(self, 'compression_settings') and self.compression_settings:
                self.progress_signal.emit(90)
                print(f"Applying compression to output file: {output_file}")
                try:
                    if self.compression_settings['method'] == 'quality':
                        success = VideoOptimizer.replace_with_optimized(
                            output_file,
                            quality=self.compression_settings['quality'],
                        )
                    else:
                        success = VideoOptimizer.replace_with_optimized(
                            output_file,
                            target_size_mb=self.compression_settings['target_size_mb'],
                        )
                    
                    if success:
                        print(f"Successfully compressed output file")
                    else:
                        print(f"Warning: Compression failed, using original file")
                except Exception as e:
                    print(f"Error during compression: {e}")
            
            \1"""
        updated_code = process_end_pattern.sub(new_process_end, updated_code)
        
        # Update the process_video_with_preset method to include compression dialog
        preset_process_pattern = re.compile(r"(# Create and start worker thread with preset audio.*?)(\s+worker = EnhancedFlickerWorker\(.*?\))", re.DOTALL)
        new_preset_process = r"""\1
            # Show compression options dialog
            compression_settings = None
            try:
                compression_settings = CompressionDialog.show_dialog(self)
            except Exception as e:
                print(f"Error showing compression dialog: {e}")
\2
            
            # Apply compression settings if selected
            if compression_settings:
                worker.compression_settings = compression_settings"""
        updated_code = preset_process_pattern.sub(new_preset_process, updated_code)
        
        # Add direct XML loading support
        xml_support_code = """
# Add support for loading XML presets
def load_preset_file(filepath):
    '''Load a preset from a file, handling both .sin and .xml formats'''
    try:
        # Check if we have the validator function
        if 'validate_preset_file' in globals():
            is_valid, format_type = validate_preset_file(filepath)
            
            if format_type == "xml":
                # Convert XML to SIN format
                return xml_to_sine_preset(filepath)
        
        # Default JSON loading
        import json
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading preset file: {e}")
        raise
"""
        
        # Add the XML support code near the end of the file
        end_of_file_pattern = re.compile(r"(if __name__ == \"__main__\":\s+sys\.exit\(main\(\)\))", re.DOTALL)
        updated_code = end_of_file_pattern.sub(xml_support_code + "\n\n\\1", updated_code)
        
        # Write the updated code to the file
        with open("integrated_isoflicker.py", "w") as f:
            f.write(updated_code)
        
        print("Successfully updated integrated_isoflicker.py")
        return True
        
    except Exception as e:
        print(f"Error updating integrated_isoflicker.py: {e}")
        # Restore the backup if an error occurred
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, "integrated_isoflicker.py")
            print("Restored original file from backup")
        return False

if __name__ == "__main__":
    update_integrated_isoflicker()
import os
import sys
import shutil

def backup_file(filename):
    """Create a backup of a file if it exists"""
    if os.path.exists(filename):
        backup = f"{filename}.bak"
        print(f"Creating backup: {backup}")
        shutil.copy2(filename, backup)
        return True
    return False

def fix_integrated_file():
    """Fix the integrated_isoflicker.py file"""
    filename = "integrated_isoflicker.py"
    
    if not backup_file(filename):
        print(f"Error: {filename} not found")
        return False
    
    print(f"Updating {filename}...")
    
    try:
        # Read the original file
        with open(filename, "r") as f:
            content = f.read()
        
        # Find the section where we need to add the original_window reference
        target = "            # Create the SINE editor tab\n            sine_container = QWidget()\n            sine_layout = QVBoxLayout()\n            self.sine_editor = SineEditorWidget()"
        replacement = "            # Create the SINE editor tab\n            sine_container = QWidget()\n            sine_layout = QVBoxLayout()\n            self.sine_editor = SineEditorWidget()\n            self.sine_editor.original_window = self.basic_mode  # Add reference to basic mode"
        
        if target in content:
            new_content = content.replace(target, replacement)
            
            # Write the updated content back to the file
            with open(filename, "w") as f:
                f.write(new_content)
            
            print(f"Successfully updated {filename}")
            return True
        else:
            print(f"Could not find target section in {filename}")
            return False
            
    except Exception as e:
        print(f"Error updating {filename}: {e}")
        return False

def fix_sine_editor():
    """Fix the sine_editor_with_xml.py file"""
    filename = "sine_editor_with_xml.py"
    
    if not backup_file(filename):
        print(f"Error: {filename} not found")
        return False
    
    print(f"Updating {filename}...")
    
    try:
        # Read the original file
        with open(filename, "r") as f:
            content = f.read()
        
        # Update the match_video_duration method
        target = "    def match_video_duration(self):\n        \"\"\"Match the duration to the selected video\"\"\"\n        # Get the main window to access the video duration\n        main_window = self.window()\n        if not hasattr(main_window, 'original_window') or not main_window.original_window:"
        replacement = "    def match_video_duration(self):\n        \"\"\"Match the duration to the selected video\"\"\"\n        # Check if we have a direct reference to the original window\n        if hasattr(self, 'original_window') and self.original_window:\n            original_window = self.original_window\n        else:\n            # Try to get it from the main window\n            main_window = self.window()\n            if not hasattr(main_window, 'original_window') or not main_window.original_window:"
        
        if target in content:
            new_content = content.replace(target, replacement)
            
            # Write the updated content back to the file
            with open(filename, "w") as f:
                f.write(new_content)
            
            print(f"Successfully updated {filename}")
            return True
        else:
            print(f"Could not find target section in {filename}")
            return False
            
    except Exception as e:
        print(f"Error updating {filename}: {e}")
        return False

def clean_integration_files():
    """Clean up duplicate integration files"""
    # Keep only the main integration file
    if os.path.exists("integrated_isoflicker.py"):
        # Backup old versions if they don't exist
        for old_file in ["isoflicker_integration.py.bak", "isoflicker_integration.py.old"]:
            if os.path.exists(old_file):
                print(f"Removing old integration file: {old_file}")
                os.remove(old_file)
    
    # Update starter.py to use correct file
    with open("starter.py", "r") as f:
        content = f.read()
    
    if "import isoflicker_integration" in content:
        new_content = content.replace(
            "import isoflicker_integration",
            "import integrated_isoflicker"
        )
        with open("starter.py", "w") as f:
            f.write(new_content)

def main():
    print("=== IsoFlicker Pro Fix Script ===")
    
    # First fix the integrated_isoflicker.py file
    if fix_integrated_file():
        print("✓ Integrated file fixed successfully")
    else:
        print("✗ Failed to fix integrated file")
    
    # Then fix the sine_editor_with_xml.py file
    if fix_sine_editor():
        print("✓ SINE editor fixed successfully")
    else:
        print("✗ Failed to fix SINE editor")
    
    # Clean up integration files
    clean_integration_files()
    
    print("\nFixes complete! Run the application to see if the error is resolved.")
    print("Next, we'll implement the additional features you requested.")

if __name__ == "__main__":
    main()
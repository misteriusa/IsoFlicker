"""
IsoFlicker Pro Launcher
This script provides a more robust startup sequence for IsoFlicker
with better error handling and debugging information.
"""

import os
import sys
import traceback
import importlib
import subprocess

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        "PyQt5", "moviepy", "librosa", "numpy", "scipy", 
        "ffmpeg_python", "soundfile", "pydub"
    ]
    
    missing = []
    for package in required_packages:
        try:
            # Handle ffmpeg-python special case (uses underscore in import)
            if package == "ffmpeg_python":
                try:
                    import ffmpeg
                    continue
                except ImportError:
                    missing.append("ffmpeg-python")
            else:
                importlib.import_module(package)
        except ImportError:
            missing.append(package)
    
    return missing

def check_ffmpeg_installed():
    """Check if ffmpeg is installed on the system"""
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.check_call(['ffmpeg', '-version'], stdout=devnull, stderr=devnull)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    print("\n===== IsoFlicker Pro Launcher =====\n")
    
    # Check if we're running in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("WARNING: Not running in a virtual environment.")
        print("It's recommended to use the provided startup scripts to ensure all dependencies are properly loaded.\n")
    
    # Check for required Python packages
    missing_packages = check_dependencies()
    if missing_packages:
        print(f"ERROR: Missing required packages: {', '.join(missing_packages)}")
        print("Please run the startup script (startEnhancedIsoFlicker.bat) to install all dependencies.")
        input("Press Enter to exit...")
        return 1
    
    # Check for ffmpeg installation
    if not check_ffmpeg_installed():
        print("WARNING: FFMPEG is not installed or not found in your system PATH")
        print("This may cause issues with video processing. Please install FFMPEG:")
        print("Download: https://ffmpeg.org/download.html")
        print("After installing, make sure to add it to your system PATH")
        
        # Ask user if they want to continue anyway
        response = input("Do you want to continue without FFMPEG? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    # Check for required files
    required_files = [
        "isoFlickerGUI.py",
        "advanced_isochronic_generator.py",
        "isochronic_timeline.py",
        "sine_editor.py",
        "sine_editor_with_xml.py",  # Updated sine editor with XML support
        "integrated_isoflicker.py",
        "preset_converter.py"  # Required for converting between formats
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"ERROR: Missing required files: {', '.join(missing_files)}")
        print("Please ensure all program files are in the current directory.")
        input("Press Enter to exit...")
        return 1
    
    # Try to run the application
    try:
        print("Starting IsoFlicker Pro...")
        # Import the main module
        import integrated_isoflicker
        # Run the main function
        integrated_isoflicker.main()
        return 0
    except Exception as e:
        print("\n===== ERROR: Application failed to start =====")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nDetailed traceback:")
        traceback.print_exc()
        
        print("\nPlease report this error with the above details.")
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
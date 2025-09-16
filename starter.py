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
from core.ffmpeg_utils import ensure_ffmpeg_available
from PyQt5.QtWidgets import QApplication

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        # Core GUI and media
        "PyQt5", "moviepy", "moviepy.editor", "librosa", "numpy", "scipy",
        "ffmpeg_python", "soundfile", "pydub", "cv2", "PIL"
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == "ffmpeg_python":
                try:
                    import ffmpeg  # noqa: F401
                    continue
                except ImportError:
                    missing.append("ffmpeg-python")
                    continue

            if package == "moviepy.editor":
                # Try the editor import first; if it raises, attempt known submodule fallbacks
                try:
                    importlib.import_module("moviepy.editor")
                except ImportError:
                    try:
                        # Fallback: import core classes directly; if this works, editor is effectively usable
                        from moviepy.video.io.VideoFileClip import VideoFileClip  # noqa: F401
                        from moviepy.audio.io.AudioFileClip import AudioFileClip  # noqa: F401
                        from moviepy.video.io.ImageSequenceClip import ImageSequenceClip  # noqa: F401
                        from moviepy.audio.AudioClip import CompositeAudioClip  # noqa: F401
                    except Exception:
                        missing.append("moviepy.editor")
                continue

            # Default path: import the package/module
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
    
    # Initialize QApplication first
    app = QApplication(sys.argv)
    
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
    
    # Ensure ffmpeg is available (prefer bundled binary)
    ensured = ensure_ffmpeg_available()
    if not ensured and not check_ffmpeg_installed():
        print("WARNING: FFmpeg not found. Some features may fail.")
        print("Tip: Run startEnhancedIsoFlicker.bat or place ffmpeg in PATH.")
    
    # Try to run the application
    try:
        print("Starting IsoFlicker Pro...")
        import integrated_isoflicker
        return integrated_isoflicker.main()
    except Exception as e:
        print("\n===== ERROR: Application failed to start =====")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nDetailed traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

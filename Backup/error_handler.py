import sys
import os
import traceback

def check_required_files():
    """Check if all required files exist in the current directory."""
    required_files = [
        "isoFlickerGUI.py",
        "isochronic_timeline.py",
        "advanced_isochronic_generator.py",
        "isoflicker_integration.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def main():
    """Main function that catches exceptions and provides detailed error messages."""
    try:
        # Check for required files
        missing_files = check_required_files()
        if missing_files:
            print(f"ERROR: The following required files are missing: {', '.join(missing_files)}")
            return 1

        # Import the main application module
        try:
            import isoflicker_integration
        except ImportError as e:
            print(f"ERROR: Failed to import isoflicker_integration: {e}")
            traceback.print_exc()
            return 1

        # Run the application
        print("Starting IsoFlicker application...")
        isoflicker_integration.main()
        return 0
        
    except Exception as e:
        print(f"ERROR: Unhandled exception: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

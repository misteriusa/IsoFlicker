import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_modern_ui_import():
    """Test that the modern UI module can be imported without errors"""
    try:
        from ui.modern_ui import ModernMainWindow
        assert ModernMainWindow is not None
    except ImportError as e:
        pytest.fail(f"Failed to import ModernMainWindow: {e}")


def test_modern_ui_creation():
    """Test that the ModernMainWindow class can be instantiated"""
    try:
        from ui.modern_ui import ModernMainWindow
        # We won't actually show the window in tests to avoid GUI issues
        window = ModernMainWindow()
        assert window is not None
    except Exception as e:
        pytest.fail(f"Failed to create ModernMainWindow instance: {e}")
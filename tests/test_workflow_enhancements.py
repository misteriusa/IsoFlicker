import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_undo_redo_functionality():
    """Test the undo/redo functionality"""
    try:
        from ui.modern_ui import ModernMainWindow
        window = ModernMainWindow()
        
        # Test initial state
        assert len(window.undo_stack) == 0
        assert len(window.redo_stack) == 0
        assert not window.undo_btn.isEnabled()
        assert not window.redo_btn.isEnabled()
        
        # Simulate an action that should be saved for undo
        window.save_state_for_undo()
        
        # Check that state was saved
        assert len(window.undo_stack) == 1
        assert len(window.redo_stack) == 0
        assert window.undo_btn.isEnabled()
        assert not window.redo_btn.isEnabled()
        
    except Exception as e:
        pytest.fail(f"Failed to test undo/redo functionality: {e}")


def test_batch_processing_setup():
    """Test that batch processing variables are initialized"""
    try:
        from ui.modern_ui import ModernMainWindow
        window = ModernMainWindow()
        
        # Check that batch processing variables are initialized
        assert hasattr(window, 'batch_files')
        assert isinstance(window.batch_files, list)
        assert len(window.batch_files) == 0
        
        # Check that UI elements exist
        assert hasattr(window, 'batch_label')
        assert hasattr(window, 'batch_btn')
        assert hasattr(window, 'clear_batch_btn')
        
    except Exception as e:
        pytest.fail(f"Failed to test batch processing setup: {e}")


def test_state_saving_and_restoration():
    """Test saving and restoring application state"""
    try:
        from ui.modern_ui import ModernMainWindow
        window = ModernMainWindow()
        
        # Set some values
        window.video_path = "/test/video.mp4"
        window.audio_path = "/test/audio.wav"
        window.tone_freq_spin.setValue(15.0)
        window.visual_freq_spin.setValue(10.0)
        window.batch_files = ["/test/video1.mp4", "/test/video2.mp4"]
        
        # Save state
        window.save_state_for_undo()
        
        # Check that state was saved
        assert len(window.undo_stack) == 1
        
        # Modify values
        window.video_path = "/test/other.mp4"
        window.tone_freq_spin.setValue(20.0)
        
        # Restore previous state
        previous_state = window.undo_stack.pop()
        window.restore_state(previous_state)
        
        # Check that values were restored
        assert window.video_path == "/test/video.mp4"
        assert window.audio_path == "/test/audio.wav"
        assert window.tone_freq_spin.value() == 15.0
        assert window.visual_freq_spin.value() == 10.0
        assert len(window.batch_files) == 2
        
    except Exception as e:
        pytest.fail(f"Failed to test state saving and restoration: {e}")
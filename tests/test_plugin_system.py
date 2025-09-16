import pytest
import sys
import os
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_plugin_base_class():
    """Test the base Plugin class"""
    try:
        from plugins.plugin_manager import Plugin
        
        # Try to instantiate the abstract base class (should fail)
        try:
            plugin = Plugin("Test", "1.0", "Test plugin")
            pytest.fail("Should not be able to instantiate abstract Plugin class")
        except TypeError:
            # This is expected
            pass
            
    except Exception as e:
        pytest.fail(f"Failed to test Plugin base class: {e}")


def test_plugin_manager_creation():
    """Test creating a PluginManager"""
    try:
        from plugins.plugin_manager import PluginManager
        
        # Create plugin manager
        plugin_manager = PluginManager()
        
        # Check attributes
        assert hasattr(plugin_manager, 'plugins_directory')
        assert hasattr(plugin_manager, 'plugins')
        assert hasattr(plugin_manager, 'plugin_modules')
        
    except Exception as e:
        pytest.fail(f"Failed to test PluginManager creation: {e}")


def test_plugin_discovery():
    """Test discovering plugins"""
    try:
        from plugins.plugin_manager import PluginManager
        
        # Create plugin manager
        plugin_manager = PluginManager("plugins")
        
        # Discover plugins
        plugin_modules = plugin_manager.discover_plugins()
        
        # Check that we found our sample plugins
        assert isinstance(plugin_modules, list)
        
    except Exception as e:
        pytest.fail(f"Failed to test plugin discovery: {e}")


def test_sample_video_plugin():
    """Test the sample video effect plugin"""
    try:
        from plugins.sample_video_effect import SampleVideoEffectPlugin
        import numpy as np
        
        # Create plugin instance
        plugin = SampleVideoEffectPlugin()
        
        # Check attributes
        assert plugin.name == "Sample Video Effect Plugin"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Adds a simple watermark effect to video frames"
        
        # Test initialization
        app_context = {"app_name": "Test"}
        result = plugin.initialize(app_context)
        assert result is True
        
        # Test frame processing
        # Create a simple test frame (100x100 RGB image)
        test_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        config = {"watermark_text": "Test"}
        
        processed_frame = plugin.process_frame(test_frame, 0.0, config)
        
        # Check that we got a processed frame
        assert processed_frame is not None
        assert isinstance(processed_frame, np.ndarray)
        assert processed_frame.shape == test_frame.shape
        
        # Test cleanup
        plugin.cleanup()
        
    except Exception as e:
        pytest.fail(f"Failed to test sample video plugin: {e}")


def test_sample_audio_plugin():
    """Test the sample audio effect plugin"""
    try:
        from plugins.sample_audio_effect import SampleAudioEffectPlugin
        import numpy as np
        
        # Create plugin instance
        plugin = SampleAudioEffectPlugin()
        
        # Check attributes
        assert plugin.name == "Sample Audio Effect Plugin"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Adds a subtle echo effect to audio"
        
        # Test initialization
        app_context = {"app_name": "Test"}
        result = plugin.initialize(app_context)
        assert result is True
        
        # Test audio processing
        # Create a simple test audio signal
        test_audio = np.random.random(4410)  # 0.1 seconds at 44100 Hz
        config = {"echo_delay": 0.05, "echo_strength": 0.2}
        
        processed_audio = plugin.process_audio(test_audio, config)
        
        # Check that we got a processed audio signal
        assert processed_audio is not None
        assert isinstance(processed_audio, np.ndarray)
        assert processed_audio.shape == test_audio.shape
        
        # Test cleanup
        plugin.cleanup()
        
    except Exception as e:
        pytest.fail(f"Failed to test sample audio plugin: {e}")
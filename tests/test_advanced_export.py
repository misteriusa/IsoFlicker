import pytest
import sys
import os
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_export_preset_creation():
    """Test creating export presets"""
    try:
        from export.advanced_export import ExportPreset, ExportFormat, QualityPreset
        
        # Create a preset
        preset = ExportPreset(
            "Test Preset",
            ExportFormat.MP4_H264,
            QualityPreset.HIGH,
            {"crf": 20}
        )
        
        # Check attributes
        assert preset.name == "Test Preset"
        assert preset.format == ExportFormat.MP4_H264
        assert preset.quality == QualityPreset.HIGH
        assert preset.custom_settings == {"crf": 20}
        
    except Exception as e:
        pytest.fail(f"Failed to create export preset: {e}")


def test_export_preset_serialization():
    """Test serializing and deserializing export presets"""
    try:
        from export.advanced_export import ExportPreset, ExportFormat, QualityPreset
        
        # Create a preset
        original_preset = ExportPreset(
            "Test Preset",
            ExportFormat.MP4_H264,
            QualityPreset.HIGH,
            {"crf": 20}
        )
        
        # Serialize to dict
        data = original_preset.to_dict()
        assert isinstance(data, dict)
        assert data["name"] == "Test Preset"
        assert data["format"] == "mp4_h264"
        assert data["quality"] == "high"
        assert data["custom_settings"] == {"crf": 20}
        
        # Deserialize from dict
        restored_preset = ExportPreset.from_dict(data)
        assert restored_preset.name == original_preset.name
        assert restored_preset.format == original_preset.format
        assert restored_preset.quality == original_preset.quality
        assert restored_preset.custom_settings == original_preset.custom_settings
        
    except Exception as e:
        pytest.fail(f"Failed to test export preset serialization: {e}")


def test_advanced_export_manager():
    """Test the advanced export manager"""
    try:
        from export.advanced_export import AdvancedExportManager, ExportFormat, QualityPreset
        
        # Create export manager
        export_manager = AdvancedExportManager()
        
        # Check that default presets are loaded
        presets = export_manager.list_presets()
        assert len(presets) > 0
        assert "YouTube" in presets
        assert "Lossless Archive" in presets
        
        # Get a preset
        preset = export_manager.get_preset("YouTube")
        assert preset is not None
        assert preset.name == "YouTube"
        
        # Create a custom preset
        custom_preset = export_manager.create_custom_preset(
            "My Custom Preset",
            ExportFormat.MP4_H264,
            QualityPreset.CUSTOM,
            video_bitrate="3000k",
            audio_bitrate="320k"
        )
        
        # Check that custom preset is added
        assert "My Custom Preset" in export_manager.list_presets()
        
        # Get format options
        format_options = export_manager.get_format_options(ExportFormat.MP4_H264)
        assert format_options["extension"] == ".mp4"
        assert format_options["codec"] == "libx264"
        
        # Get quality settings
        quality_settings = export_manager.get_quality_settings(QualityPreset.HIGH)
        assert "video_bitrate" in quality_settings
        assert "audio_bitrate" in quality_settings
        
    except Exception as e:
        pytest.fail(f"Failed to test advanced export manager: {e}")


def test_ffmpeg_parameters():
    """Test generating FFmpeg parameters"""
    try:
        from export.advanced_export import AdvancedExportManager, ExportFormat, QualityPreset
        
        # Create export manager
        export_manager = AdvancedExportManager()
        
        # Get a preset
        preset = export_manager.get_preset("YouTube")
        assert preset is not None
        
        # Get FFmpeg parameters
        ffmpeg_params = export_manager.get_ffmpeg_params(preset)
        assert isinstance(ffmpeg_params, list)
        assert "-c:v" in ffmpeg_params
        assert "-c:a" in ffmpeg_params
        
    except Exception as e:
        pytest.fail(f"Failed to test FFmpeg parameters: {e}")


def test_preset_save_load():
    """Test saving and loading presets"""
    try:
        from export.advanced_export import AdvancedExportManager, ExportFormat, QualityPreset
        import os
        
        # Create export manager
        export_manager = AdvancedExportManager()
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            filepath = tmp.name
        
        try:
            # Save presets
            export_manager.save_presets(filepath)
            
            # Check that file was created
            assert os.path.exists(filepath)
            
            # Create a new export manager and load presets
            new_export_manager = AdvancedExportManager()
            new_export_manager.load_presets(filepath)
            
            # Check that presets were loaded
            assert len(new_export_manager.list_presets()) > 0
            
        finally:
            # Clean up temporary file
            if os.path.exists(filepath):
                os.unlink(filepath)
                
    except Exception as e:
        pytest.fail(f"Failed to test preset save/load: {e}")
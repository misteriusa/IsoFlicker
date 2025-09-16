import os
import json
from enum import Enum
from typing import Dict, Any, Optional


class ExportFormat(Enum):
    """Supported export formats"""
    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    MKV_FFV1 = "mkv_ffv1"
    MKV_H264 = "mkv_h264"
    AVI_DV = "avi_dv"
    WEBM_VP9 = "webm_vp9"
    MOV_PRORES = "mov_prores"
    WAV = "wav"
    FLAC = "flac"
    MP3 = "mp3"


class QualityPreset(Enum):
    """Quality presets for export"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LOSSLESS = "lossless"
    CUSTOM = "custom"


class ExportPreset:
    """Export preset with configuration options"""
    
    def __init__(self, name: str, format: ExportFormat, quality: QualityPreset, 
                 custom_settings: Optional[Dict[str, Any]] = None):
        self.name = name
        self.format = format
        self.quality = quality
        self.custom_settings = custom_settings or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary for serialization"""
        return {
            "name": self.name,
            "format": self.format.value,
            "quality": self.quality.value,
            "custom_settings": self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportPreset':
        """Create preset from dictionary"""
        return cls(
            name=data["name"],
            format=ExportFormat(data["format"]),
            quality=QualityPreset(data["quality"]),
            custom_settings=data.get("custom_settings", {})
        )


class AdvancedExportManager:
    """Advanced export manager with multiple format and quality options"""
    
    def __init__(self):
        self.presets = {}
        self.default_presets = {
            "YouTube": ExportPreset(
                "YouTube",
                ExportFormat.MP4_H264,
                QualityPreset.HIGH,
                {"crf": 23, "preset": "medium"}
            ),
            "Vimeo": ExportPreset(
                "Vimeo",
                ExportFormat.MP4_H264,
                QualityPreset.HIGH,
                {"crf": 22, "preset": "slow"}
            ),
            "Lossless Archive": ExportPreset(
                "Lossless Archive",
                ExportFormat.MKV_FFV1,
                QualityPreset.LOSSLESS,
                {"crf": 0, "preset": "veryslow"}
            ),
            "Web Optimized": ExportPreset(
                "Web Optimized",
                ExportFormat.WEBM_VP9,
                QualityPreset.MEDIUM,
                {"crf": 30, "preset": "fast"}
            ),
            "Audio Only": ExportPreset(
                "Audio Only",
                ExportFormat.FLAC,
                QualityPreset.LOSSLESS,
                {}
            )
        }
        # Load default presets
        self.presets.update(self.default_presets)
    
    def get_format_options(self, format: ExportFormat) -> Dict[str, Any]:
        """Get format-specific options"""
        format_options = {
            ExportFormat.MP4_H264: {
                "extension": ".mp4",
                "codec": "libx264",
                "audio_codec": "aac",
                "container": "mp4"
            },
            ExportFormat.MP4_H265: {
                "extension": ".mp4",
                "codec": "libx265",
                "audio_codec": "aac",
                "container": "mp4"
            },
            ExportFormat.MKV_FFV1: {
                "extension": ".mkv",
                "codec": "ffv1",
                "audio_codec": "pcm_s16le",
                "container": "matroska"
            },
            ExportFormat.MKV_H264: {
                "extension": ".mkv",
                "codec": "libx264",
                "audio_codec": "aac",
                "container": "matroska"
            },
            ExportFormat.AVI_DV: {
                "extension": ".avi",
                "codec": "dvvideo",
                "audio_codec": "pcm_s16le",
                "container": "avi"
            },
            ExportFormat.WEBM_VP9: {
                "extension": ".webm",
                "codec": "libvpx-vp9",
                "audio_codec": "libopus",
                "container": "webm"
            },
            ExportFormat.MOV_PRORES: {
                "extension": ".mov",
                "codec": "prores",
                "audio_codec": "aac",
                "container": "mov"
            },
            ExportFormat.WAV: {
                "extension": ".wav",
                "codec": None,
                "audio_codec": "pcm_s16le",
                "container": None
            },
            ExportFormat.FLAC: {
                "extension": ".flac",
                "codec": None,
                "audio_codec": "flac",
                "container": None
            },
            ExportFormat.MP3: {
                "extension": ".mp3",
                "codec": None,
                "audio_codec": "libmp3lame",
                "container": None
            }
        }
        return format_options.get(format, {})
    
    def get_quality_settings(self, quality: QualityPreset) -> Dict[str, Any]:
        """Get quality-specific settings"""
        quality_settings = {
            QualityPreset.LOW: {
                "video_bitrate": "1000k",
                "audio_bitrate": "128k",
                "crf": 30,
                "preset": "fast"
            },
            QualityPreset.MEDIUM: {
                "video_bitrate": "2500k",
                "audio_bitrate": "192k",
                "crf": 25,
                "preset": "medium"
            },
            QualityPreset.HIGH: {
                "video_bitrate": "5000k",
                "audio_bitrate": "256k",
                "crf": 20,
                "preset": "slow"
            },
            QualityPreset.LOSSLESS: {
                "video_bitrate": None,
                "audio_bitrate": None,
                "crf": 0,
                "preset": "veryslow"
            },
            QualityPreset.CUSTOM: {
                "video_bitrate": None,
                "audio_bitrate": None,
                "crf": None,
                "preset": "medium"
            }
        }
        return quality_settings.get(quality, {})
    
    def create_custom_preset(self, name: str, format: ExportFormat, quality: QualityPreset,
                           video_bitrate: Optional[str] = None, audio_bitrate: Optional[str] = None,
                           crf: Optional[int] = None, preset: Optional[str] = None) -> ExportPreset:
        """Create a custom export preset"""
        custom_settings = {}
        if video_bitrate:
            custom_settings["video_bitrate"] = video_bitrate
        if audio_bitrate:
            custom_settings["audio_bitrate"] = audio_bitrate
        if crf is not None:
            custom_settings["crf"] = crf
        if preset:
            custom_settings["preset"] = preset
            
        preset_obj = ExportPreset(name, format, quality, custom_settings)
        self.presets[name] = preset_obj
        return preset_obj
    
    def get_preset(self, name: str) -> Optional[ExportPreset]:
        """Get a preset by name"""
        return self.presets.get(name)
    
    def list_presets(self) -> list:
        """List all available presets"""
        return list(self.presets.keys())
    
    def save_presets(self, filepath: str):
        """Save presets to a JSON file"""
        preset_data = {name: preset.to_dict() for name, preset in self.presets.items()}
        with open(filepath, 'w') as f:
            json.dump(preset_data, f, indent=2)
    
    def load_presets(self, filepath: str):
        """Load presets from a JSON file"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                preset_data = json.load(f)
            for name, data in preset_data.items():
                self.presets[name] = ExportPreset.from_dict(data)
    
    def get_ffmpeg_params(self, preset: ExportPreset) -> list:
        """Get FFmpeg parameters for a given preset"""
        params = []
        
        # Get format options
        format_options = self.get_format_options(preset.format)
        
        # Get quality settings
        quality_settings = self.get_quality_settings(preset.quality)
        
        # Combine with custom settings
        settings = {**quality_settings, **preset.custom_settings}
        
        # Add codec parameters
        if format_options.get("codec"):
            params.extend(["-c:v", format_options["codec"]])
            
        if format_options.get("audio_codec"):
            params.extend(["-c:a", format_options["audio_codec"]])
        
        # Add quality parameters
        if "crf" in settings and settings["crf"] is not None:
            params.extend(["-crf", str(settings["crf"])])
            
        if "preset" in settings:
            params.extend(["-preset", settings["preset"]])
            
        if "video_bitrate" in settings and settings["video_bitrate"]:
            params.extend(["-b:v", settings["video_bitrate"]])
            
        if "audio_bitrate" in settings and settings["audio_bitrate"]:
            params.extend(["-b:a", settings["audio_bitrate"]])
        
        # Add format-specific parameters
        if preset.format == ExportFormat.MOV_PRORES:
            params.extend(["-profile:v", "3"])  # Proxy, LT, Standard, HQ, 4444, 4444XQ
        
        return params


def main():
    """Example usage of the advanced export manager"""
    # Create export manager
    export_manager = AdvancedExportManager()
    
    # List available presets
    print("Available presets:")
    for preset_name in export_manager.list_presets():
        print(f"  - {preset_name}")
    
    # Get a preset
    preset = export_manager.get_preset("YouTube")
    if preset:
        print(f"\nPreset: {preset.name}")
        print(f"Format: {preset.format.value}")
        print(f"Quality: {preset.quality.value}")
        
        # Get FFmpeg parameters
        ffmpeg_params = export_manager.get_ffmpeg_params(preset)
        print(f"FFmpeg params: {' '.join(ffmpeg_params)}")
    
    # Create a custom preset
    custom_preset = export_manager.create_custom_preset(
        "My Custom Preset",
        ExportFormat.MP4_H264,
        QualityPreset.CUSTOM,
        video_bitrate="3000k",
        audio_bitrate="320k",
        crf=18,
        preset="veryslow"
    )
    
    print(f"\nCustom preset created: {custom_preset.name}")
    ffmpeg_params = export_manager.get_ffmpeg_params(custom_preset)
    print(f"FFmpeg params: {' '.join(ffmpeg_params)}")
    
    # Save presets to file
    export_manager.save_presets("export_presets.json")
    print("\nPresets saved to export_presets.json")


if __name__ == "__main__":
    main()
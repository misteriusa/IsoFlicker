from plugins.plugin_manager import Plugin, AudioProcessorPlugin
import numpy as np


class SampleAudioEffectPlugin(AudioProcessorPlugin):
    """Sample audio effect plugin that adds a subtle echo effect"""
    
    def __init__(self):
        super().__init__()
        self.name = "Sample Audio Effect Plugin"
        self.version = "1.0.0"
        self.description = "Adds a subtle echo effect to audio"
    
    def initialize(self, app_context) -> bool:
        """Initialize the plugin"""
        print(f"Initializing {self.name} v{self.version}")
        print(f"Description: {self.description}")
        return True
    
    def cleanup(self):
        """Clean up plugin resources"""
        print(f"Cleaning up {self.name}")
    
    def process_audio(self, audio_data, config):
        """Process audio data by adding a subtle echo effect
        
        Args:
            audio_data: Audio data to process (numpy array)
            config: Configuration dictionary
            
        Returns:
            Processed audio data with echo effect
        """
        # Make a copy of the audio data to avoid modifying the original
        processed_audio = audio_data.copy()
        
        # Get echo parameters from config or use defaults
        echo_delay = config.get("echo_delay", 0.1)  # seconds
        echo_strength = config.get("echo_strength", 0.3)  # 0.0 to 1.0
        
        # Calculate delay in samples (assuming 44100 Hz sample rate)
        sample_rate = 44100
        delay_samples = int(echo_delay * sample_rate)
        
        # Apply echo effect
        if delay_samples < len(processed_audio):
            # Add delayed version of the audio to itself
            processed_audio[delay_samples:] += echo_strength * processed_audio[:-delay_samples]
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(processed_audio))
            if max_val > 1.0:
                processed_audio = processed_audio / max_val
                
        return processed_audio


# This is needed for the plugin manager to find the plugin class
def get_plugin_class():
    """Return the plugin class"""
    return SampleAudioEffectPlugin
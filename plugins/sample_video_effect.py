from plugins.plugin_manager import Plugin, VideoProcessorPlugin
import numpy as np


class SampleVideoEffectPlugin(VideoProcessorPlugin):
    """Sample video effect plugin that adds a watermark to frames"""
    
    def __init__(self):
        super().__init__()
        self.name = "Sample Video Effect Plugin"
        self.version = "1.0.0"
        self.description = "Adds a simple watermark effect to video frames"
    
    def initialize(self, app_context) -> bool:
        """Initialize the plugin"""
        print(f"Initializing {self.name} v{self.version}")
        print(f"Description: {self.description}")
        return True
    
    def cleanup(self):
        """Clean up plugin resources"""
        print(f"Cleaning up {self.name}")
    
    def process_frame(self, frame, time, config):
        """Process a video frame by adding a simple watermark
        
        Args:
            frame: Video frame to process (numpy array)
            time: Current time in seconds
            config: Configuration dictionary
            
        Returns:
            Processed frame with watermark
        """
        # Make a copy of the frame to avoid modifying the original
        processed_frame = frame.copy()
        
        # Get watermark text from config or use default
        watermark_text = config.get("watermark_text", "IsoFlicker Pro")
        
        # Add a simple text-like effect (in a real implementation, you would use OpenCV)
        height, width = processed_frame.shape[:2]
        
        # Add a semi-transparent rectangle as a "watermark area"
        if height > 50 and width > 200:
            # Create a simple watermark effect using numpy operations
            # This is a simplified example - in practice, you'd use OpenCV's text drawing functions
            watermark_area = processed_frame[height-50:height, width-200:width]
            # Reduce brightness to create a semi-transparent effect
            watermark_area = (watermark_area * 0.7).astype(np.uint8)
            processed_frame[height-50:height, width-200:width] = watermark_area
            
            # Add some text-like pixels
            # This is just a simple pattern to simulate text
            for i in range(0, min(20, height-30)):
                for j in range(0, min(100, width-100)):
                    if (i + j) % 10 < 5:  # Simple pattern
                        if height-40+i < height and width-180+j < width:
                            processed_frame[height-40+i, width-180+j] = [255, 255, 255]
        
        return processed_frame


# This is needed for the plugin manager to find the plugin class
def get_plugin_class():
    """Return the plugin class"""
    return SampleVideoEffectPlugin
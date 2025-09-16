import pytest
import numpy as np
import os
import tempfile
from core.video_processor import generate_isochronic_tone, detect_isochronic_frequency


def test_generate_isochronic_tone():
    """Test that the isochronic tone generator produces the correct output shape and type"""
    frequency = 10.0
    duration = 1.0
    sample_rate = 44100
    volume = 0.5
    carrier_frequency = 100.0
    
    tone_data, sr = generate_isochronic_tone(
        frequency, duration, sample_rate, volume, carrier_frequency
    )
    
    # Check that we get the right sample rate back
    assert sr == sample_rate
    
    # Check that we get the right number of samples
    expected_samples = int(sample_rate * duration)
    assert len(tone_data) == expected_samples
    
    # Check that the data is in the right range
    assert np.max(np.abs(tone_data)) <= volume


def test_detect_isochronic_frequency_with_invalid_file():
    """Test that frequency detection handles invalid files gracefully"""
    # Create a temporary file that doesn't contain valid audio
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"This is not an audio file")
        tmp_path = tmp.name
    
    try:
        # Should return default frequency when file is invalid
        freq = detect_isochronic_frequency(tmp_path)
        assert freq == 10.0  # Default frequency
    finally:
        # Clean up
        os.unlink(tmp_path)


def test_detect_isochronic_frequency_with_nonexistent_file():
    """Test that frequency detection handles missing files gracefully"""
    # Should return default frequency when file doesn't exist
    freq = detect_isochronic_frequency("/nonexistent/file.wav")
    assert freq == 10.0  # Default frequency
import pytest
import numpy as np
from advanced_isochronic_generator import (
    IsochronicToneGenerator, 
    WaveformType, 
    ModulationType,
    generate_isochronic_tone
)


def test_generate_isochronic_tone_function():
    """Test the generate_isochronic_tone function"""
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


def test_isochronic_tone_generator_sine_carrier():
    """Test the IsochronicToneGenerator with sine carrier wave"""
    generator = IsochronicToneGenerator(sample_rate=44100)
    
    # Generate a sine carrier wave
    frequency = 100.0
    duration = 0.1  # 100ms
    carrier = generator.generate_carrier(WaveformType.SINE, frequency, duration)
    
    # Check that we get the right number of samples
    expected_samples = int(generator.sample_rate * duration)
    assert len(carrier) == expected_samples
    
    # For a sine wave, the max amplitude should be close to 1.0
    assert np.max(np.abs(carrier)) <= 1.0


def test_isochronic_tone_generator_square_carrier():
    """Test the IsochronicToneGenerator with square carrier wave"""
    generator = IsochronicToneGenerator(sample_rate=44100)
    
    # Generate a square carrier wave
    frequency = 100.0
    duration = 0.1  # 100ms
    carrier = generator.generate_carrier(WaveformType.SQUARE, frequency, duration)
    
    # Check that we get the right number of samples
    expected_samples = int(generator.sample_rate * duration)
    assert len(carrier) == expected_samples
    
    # For a square wave, values should be either +1 or -1
    unique_values = np.unique(np.round(carrier, decimals=6))
    assert len(unique_values) <= 2
    assert all(abs(val) == 1.0 or val == 0.0 for val in unique_values)


def test_isochronic_tone_generator_modulation():
    """Test the IsochronicToneGenerator modulation generation"""
    generator = IsochronicToneGenerator(sample_rate=44100)
    
    # Generate square modulation
    frequency = 10.0
    duration = 1.0
    modulation = generator.generate_modulation(ModulationType.SQUARE, frequency, duration)
    
    # Check that we get the right number of samples
    expected_samples = int(generator.sample_rate * duration)
    assert len(modulation) == expected_samples
    
    # For square modulation, values should be between 0 and 1
    assert np.min(modulation) >= 0.0
    assert np.max(modulation) <= 1.0


def test_isochronic_tone_generator_tone_segment():
    """Test the IsochronicToneGenerator tone segment generation"""
    generator = IsochronicToneGenerator(sample_rate=44100)
    
    # Generate a tone segment
    duration = 0.5
    carrier_freq = 100.0
    entrainment_freq = 10.0
    volume = 0.5
    
    tone_segment = generator.generate_tone_segment(
        duration=duration,
        carrier_freq=carrier_freq,
        entrainment_freq=entrainment_freq,
        volume=volume,
        sample_rate=44100,
        carrier_type=WaveformType.SINE,
        modulation_type=ModulationType.SQUARE
    )
    
    # Check that we get the right number of samples
    expected_samples = int(generator.sample_rate * duration)
    assert len(tone_segment) == expected_samples
    
    # Check that the data is in the right range
    assert np.max(np.abs(tone_segment)) <= volume
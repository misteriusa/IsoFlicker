import pytest
import numpy as np
from advanced_isochronic_generator import IsochronicToneGenerator, WaveformType, ModulationType


def test_tone_generator_caching():
    """Test that the tone generator caches generated segments"""
    generator = IsochronicToneGenerator(sample_rate=44100)
    
    # Generate a tone segment
    duration = 0.5
    carrier_freq = 100.0
    entrainment_freq = 10.0
    volume = 0.5
    
    # Generate the same segment twice
    tone1 = generator.generate_tone_segment(
        duration=duration,
        carrier_freq=carrier_freq,
        entrainment_freq=entrainment_freq,
        volume=volume,
        sample_rate=44100,
        carrier_type=WaveformType.SINE,
        modulation_type=ModulationType.SQUARE
    )
    
    tone2 = generator.generate_tone_segment(
        duration=duration,
        carrier_freq=carrier_freq,
        entrainment_freq=entrainment_freq,
        volume=volume,
        sample_rate=44100,
        carrier_type=WaveformType.SINE,
        modulation_type=ModulationType.SQUARE
    )
    
    # Check that both segments are identical
    assert np.array_equal(tone1, tone2)
    
    # Check that the cache has one entry
    assert len(generator._cache) == 1


def test_tone_generator_cache_different_parameters():
    """Test that the tone generator caches different segments for different parameters"""
    generator = IsochronicToneGenerator(sample_rate=44100)
    
    # Generate two tone segments with different parameters
    duration = 0.5
    carrier_freq = 100.0
    entrainment_freq = 10.0
    volume = 0.5
    
    # Generate first segment
    tone1 = generator.generate_tone_segment(
        duration=duration,
        carrier_freq=carrier_freq,
        entrainment_freq=entrainment_freq,
        volume=volume,
        sample_rate=44100,
        carrier_type=WaveformType.SINE,
        modulation_type=ModulationType.SQUARE
    )
    
    # Generate second segment with different frequency
    tone2 = generator.generate_tone_segment(
        duration=duration,
        carrier_freq=carrier_freq,
        entrainment_freq=15.0,  # Different frequency
        volume=volume,
        sample_rate=44100,
        carrier_type=WaveformType.SINE,
        modulation_type=ModulationType.SQUARE
    )
    
    # Check that segments are different
    assert not np.array_equal(tone1, tone2)
    
    # Check that the cache has two entries
    assert len(generator._cache) == 2


def test_tone_generator_cache_clear():
    """Test that we can clear the cache"""
    generator = IsochronicToneGenerator(sample_rate=44100)
    
    # Generate a tone segment
    duration = 0.5
    carrier_freq = 100.0
    entrainment_freq = 10.0
    volume = 0.5
    
    tone = generator.generate_tone_segment(
        duration=duration,
        carrier_freq=carrier_freq,
        entrainment_freq=entrainment_freq,
        volume=volume,
        sample_rate=44100,
        carrier_type=WaveformType.SINE,
        modulation_type=ModulationType.SQUARE
    )
    
    # Check that the cache has one entry
    assert len(generator._cache) == 1
    
    # Clear the cache
    generator._cache.clear()
    
    # Check that the cache is empty
    assert len(generator._cache) == 0
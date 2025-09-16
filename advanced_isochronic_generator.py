import numpy as np
import soundfile as sf
import scipy.signal
from enum import Enum


class WaveformType(Enum):
    """Enumeration of supported waveform types for carrier waves.
    
    Carrier waves are the base audio signals that are modulated to create 
    isochronic tones. Different waveforms produce different sound characteristics.
    
    Attributes:
        SINE: Smooth sine wave, clean and pure sound
        SQUARE: Sharp square wave, rich in harmonics
        TRIANGLE: Triangle wave, milder than square but more complex than sine
        SAWTOOTH: Sawtooth wave, bright and buzzy sound
        NOISE: Filtered white noise, textured sound
    """
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    NOISE = "noise"


class ModulationType(Enum):
    """Enumeration of supported modulation types for isochronic tones.
    
    Modulation types determine how the carrier wave is pulsed to create 
    the isochronic effect. Different modulation types produce different 
    entrainment experiences.
    
    Attributes:
        SQUARE: Classic on/off isochronic pulsing with sharp transitions
        SINE: Smooth sine wave modulation with gradual transitions
        TRAPEZOID: Trapezoidal modulation with adjustable ramp time
        GAUSSIAN: Gaussian pulse shape with smooth bell-curve transitions
    """
    SQUARE = "square"         # Classic on/off isochronic
    SINE = "sine"             # Smoother sine wave modulation
    TRAPEZOID = "trapezoid"   # Trapezoidal with adjustable ramp
    GAUSSIAN = "gaussian"     # Gaussian pulse shape


# Add the missing generate_isochronic_tone function
def generate_isochronic_tone(frequency, duration, sample_rate=44100, volume=0.5, carrier_frequency=100.0):
    """Generate a simple isochronic tone with the specified parameters.
    
    This is a convenience function that creates an isochronic tone using 
    default settings (sine carrier wave with square modulation).
    
    Args:
        frequency (float): The entrainment frequency in Hz (pulses per second)
        duration (float): The duration of the tone in seconds
        sample_rate (int, optional): The sample rate of the audio. Defaults to 44100.
        volume (float, optional): The volume of the tone (0.0 to 1.0). Defaults to 0.5.
        carrier_frequency (float, optional): The carrier frequency in Hz. Defaults to 100.0.
        
    Returns:
        tuple: A tuple containing:
            - numpy.ndarray: The audio data as a numpy array
            - int: The sample rate of the audio
            
    Example:
        >>> tone_data, sr = generate_isochronic_tone(10.0, 5.0)
        >>> len(tone_data)
        220500
    """
    # Create a tone generator instance
    generator = IsochronicToneGenerator(sample_rate=sample_rate)
    
    # Generate the tone using the default settings
    audio_data = generator.generate_tone_segment(
        duration=duration,
        carrier_freq=carrier_frequency,
        entrainment_freq=frequency,
        volume=volume,
        sample_rate=sample_rate,
        carrier_type=WaveformType.SINE,
        modulation_type=ModulationType.SQUARE
    )
    
    return audio_data, sample_rate


class IsochronicToneGenerator:
    """Advanced generator for isochronic tones with various carrier and modulation options.
    
    This class provides advanced functionality for generating isochronic tones 
    with customizable carrier waves and modulation patterns. It supports multiple 
    waveform types and modulation shapes for creating diverse entrainment experiences.
    
    The generator works by:
    1. Creating a carrier wave of the specified frequency and waveform type
    2. Generating a modulation envelope of the specified pattern
    3. Applying the modulation to the carrier wave
    4. Adjusting the volume to the specified level
    
    Features caching for improved performance when generating repeated segments.
    """
    
    def __init__(self, sample_rate=44100):
        """Initialize the IsochronicToneGenerator.
        
        Args:
            sample_rate (int, optional): The sample rate for audio generation. Defaults to 44100.
        """
        self.sample_rate = sample_rate
        # Initialize cache for generated segments
        self._cache = {}
    
    def generate_carrier(self, waveform_type, frequency, duration, amplitude=1.0):
        """Generate carrier wave with specified waveform type.
        
        Creates a continuous waveform of the specified type and frequency to 
        serve as the base signal for isochronic tone generation.
        
        Args:
            waveform_type (WaveformType): The type of waveform to generate
            frequency (float): The frequency of the carrier wave in Hz
            duration (float): The duration of the carrier wave in seconds
            amplitude (float, optional): The amplitude of the carrier wave. Defaults to 1.0.
            
        Returns:
            numpy.ndarray: The generated carrier wave as a numpy array
            
        Raises:
            ValueError: If an unsupported waveform type is specified
        """
        # Create time array
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        # Generate waveform based on type
        if waveform_type == WaveformType.SINE:
            return amplitude * np.sin(2 * np.pi * frequency * t)
            
        elif waveform_type == WaveformType.SQUARE:
            return amplitude * scipy.signal.square(2 * np.pi * frequency * t)
            
        elif waveform_type == WaveformType.TRIANGLE:
            return amplitude * scipy.signal.sawtooth(2 * np.pi * frequency * t, width=0.5)
            
        elif waveform_type == WaveformType.SAWTOOTH:
            return amplitude * scipy.signal.sawtooth(2 * np.pi * frequency * t)
            
        elif waveform_type == WaveformType.NOISE:
            # White noise filtered to emphasize the frequency
            noise = np.random.normal(0, 1, num_samples)
            # Apply bandpass filter around the frequency
            b, a = scipy.signal.butter(4, [max(0.01, (frequency - 20) / (self.sample_rate/2)), 
                                           min(0.99, (frequency + 20) / (self.sample_rate/2))], 
                                       btype='band')
            filtered_noise = scipy.signal.filtfilt(b, a, noise)
            return amplitude * filtered_noise / np.max(np.abs(filtered_noise))
        
        # Default to sine wave if type is unknown
        return amplitude * np.sin(2 * np.pi * frequency * t)
    
    def generate_modulation(self, mod_type, frequency, duration, duty_cycle=0.5, ramp_percent=10):
        """Generate modulation envelope with specified type.
        
        Creates a modulation envelope that controls when the carrier wave 
        is audible, creating the characteristic pulsing effect of isochronic tones.
        
        Args:
            mod_type (ModulationType): The type of modulation to generate
            frequency (float): The frequency of the modulation in Hz
            duration (float): The duration of the modulation in seconds
            duty_cycle (float, optional): The duty cycle for square/trapezoid modulation. Defaults to 0.5.
            ramp_percent (int, optional): The ramp percentage for trapezoid modulation. Defaults to 10.
            
        Returns:
            numpy.ndarray: The generated modulation envelope as a numpy array
        """
        # Create time array
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        # Generate modulation based on type
        if mod_type == ModulationType.SQUARE:
            # Classic on/off isochronic pulsing
            return 0.5 * (1 + scipy.signal.square(2 * np.pi * frequency * t, duty=duty_cycle))
            
        elif mod_type == ModulationType.SINE:
            # Sine wave modulation (smoother)
            return 0.5 * (1 + np.sin(2 * np.pi * frequency * t))
            
        elif mod_type == ModulationType.TRAPEZOID:
            # Trapezoidal modulation with adjustable ramp
            # Calculate number of samples for ramp
            period_samples = int(self.sample_rate / frequency)
            ramp_samples = int(period_samples * ramp_percent / 100)
            
            # Generate modulation for each period
            envelope = np.zeros(num_samples)
            
            # Create a single period
            for i in range(0, num_samples, period_samples):
                end_idx = min(i + period_samples, num_samples)
                period_len = end_idx - i
                
                if period_len <= ramp_samples * 2:
                    # Period too short for trapezoid, use triangle
                    period = np.concatenate([
                        np.linspace(0, 1, period_len // 2),
                        np.linspace(1, 0, period_len - period_len // 2)
                    ])
                else:
                    # Create trapezoid pattern
                    ramp_up = np.linspace(0, 1, ramp_samples)
                    hold = np.ones(period_len - 2 * ramp_samples)
                    ramp_down = np.linspace(1, 0, ramp_samples)
                    period = np.concatenate([ramp_up, hold, ramp_down])
                
                # Add to envelope
                envelope[i:end_idx] = period[:period_len]
            
            return envelope
            
        elif mod_type == ModulationType.GAUSSIAN:
            # Gaussian pulse modulation
            envelope = np.zeros(num_samples)
            
            # Calculate period in samples
            period_samples = int(self.sample_rate / frequency)
            
            # Create gaussian pulses at each period
            for i in range(0, num_samples, period_samples):
                # Center of gaussian
                center = i + period_samples // 2
                
                # Width of gaussian (adjust for desired duty cycle)
                sigma = period_samples * duty_cycle / 6  # 6-sigma covers most of the gaussian
                
                # Generate gaussian around center
                for j in range(max(0, i), min(num_samples, i + period_samples)):
                    envelope[j] = np.exp(-0.5 * ((j - center) / sigma) ** 2)
            
            return envelope
        
        # Default to square wave modulation
        return 0.5 * (1 + scipy.signal.square(2 * np.pi * frequency * t))
    
    def _get_cache_key(self, duration, carrier_freq, entrainment_freq, volume, 
                      sample_rate, carrier_type, modulation_type, duty_cycle):
        """Generate a cache key for the given parameters.
        
        Args:
            duration (float): The duration of the tone segment in seconds
            carrier_freq (float): The frequency of the carrier wave in Hz
            entrainment_freq (float): The frequency of the entrainment effect in Hz
            volume (float): The volume of the tone (0.0 to 1.0)
            sample_rate (int): The sample rate for audio generation
            carrier_type (WaveformType): The type of carrier wave
            modulation_type (ModulationType): The type of modulation
            duty_cycle (float): The duty cycle for certain modulation types
            
        Returns:
            tuple: A hashable tuple representing the parameters
        """
        return (duration, carrier_freq, entrainment_freq, volume, 
                sample_rate, carrier_type, modulation_type, duty_cycle)
    
    def generate_tone_segment(self, duration, carrier_freq, entrainment_freq, volume=0.5, 
                             sample_rate=44100, carrier_type=WaveformType.SINE, 
                             modulation_type=ModulationType.SQUARE, duty_cycle=0.5):
        """Generate a segment of isochronic tone with the specified parameters.
        
        This is the main method for generating isochronic tones. It combines 
        a carrier wave with a modulation envelope to create the final audio.
        
        Uses caching to improve performance when generating repeated segments.
        
        Args:
            duration (float): The duration of the tone segment in seconds
            carrier_freq (float): The frequency of the carrier wave in Hz
            entrainment_freq (float): The frequency of the entrainment effect in Hz
            volume (float, optional): The volume of the tone (0.0 to 1.0). Defaults to 0.5.
            sample_rate (int, optional): The sample rate for audio generation. Defaults to 44100.
            carrier_type (WaveformType, optional): The type of carrier wave. Defaults to WaveformType.SINE.
            modulation_type (ModulationType, optional): The type of modulation. Defaults to ModulationType.SQUARE.
            duty_cycle (float, optional): The duty cycle for certain modulation types. Defaults to 0.5.
            
        Returns:
            numpy.ndarray: The generated isochronic tone segment as a numpy array
        """
        # Create cache key
        cache_key = self._get_cache_key(duration, carrier_freq, entrainment_freq, volume, 
                                       sample_rate, carrier_type, modulation_type, duty_cycle)
        
        # Check if result is in cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Ensure we're using the correct sample rate
        self.sample_rate = sample_rate
        
        # Generate carrier wave
        carrier = self.generate_carrier(carrier_type, carrier_freq, duration, amplitude=0.8)
        
        # Generate modulation envelope
        modulation = self.generate_modulation(modulation_type, entrainment_freq, duration, duty_cycle)
        
        # Apply modulation to carrier
        output = carrier * modulation * volume
        
        # Cache the result
        self._cache[cache_key] = output
        
        return output


class IsochronicPresetGenerator:
    """Generator for full isochronic presets with multiple segments and transitions"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.tone_generator = IsochronicToneGenerator(sample_rate)
    
    def generate_from_preset(self, preset, add_background=None, background_volume=0.3):
        """Generate complete audio from a preset with multiple segments"""
        if not preset.segments:
            return np.array([]), self.sample_rate
        
        # Calculate total number of samples
        total_duration = preset.get_total_duration()
        total_samples = int(self.sample_rate * total_duration)
        audio_data = np.zeros(total_samples)
        
        # Current position in samples
        current_pos = 0
        
        # Process each segment
        for segment in preset.segments:
            # Generate audio for this segment
            segment_audio, _ = self.tone_generator.generate_advanced_isochronic(
                carrier_type=preset.carrier_type,
                modulation_type=preset.modulation_type,
                start_freq=segment.start_freq,
                end_freq=segment.end_freq,
                base_freq=segment.base_freq,
                duration=segment.duration,
                volume=segment.volume,
                transition_type=segment.transition_type
            )
            
            # Calculate segment position and length
            segment_length = len(segment_audio)
            end_pos = current_pos + segment_length
            
            # Add to main audio buffer
            if end_pos <= total_samples:
                audio_data[current_pos:end_pos] = segment_audio
                current_pos = end_pos
        
        # Add background if provided
        if add_background is not None:
            audio_data = self.tone_generator.mix_with_background(
                audio_data, add_background, background_volume
            )
        
        return audio_data, self.sample_rate
    
    def export_to_file(self, preset, output_file, file_format="wav", add_background=None, background_volume=0.3):
        """Generate and export preset to audio file"""
        audio_data, sample_rate = self.generate_from_preset(preset, add_background, background_volume)
        
        if file_format.lower() == "wav":
            sf.write(output_file, audio_data, sample_rate)
        elif file_format.lower() == "flac":
            sf.write(output_file, audio_data, sample_rate, format="FLAC")
        elif file_format.lower() == "mp3":
            try:
                import soundfile as sf
                # Write to temporary WAV first
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    temp_wav = tmp.name
                
                sf.write(temp_wav, audio_data, sample_rate)
                
                # Convert to MP3 using ffmpeg or pydub if available
                try:
                    from pydub import AudioSegment
                    sound = AudioSegment.from_wav(temp_wav)
                    sound.export(output_file, format="mp3", bitrate="192k")
                except ImportError:
                    import subprocess
                    subprocess.call(['ffmpeg', '-i', temp_wav, '-b:a', '192k', output_file])
                
                # Remove temporary file
                os.unlink(temp_wav)
            except Exception as e:
                raise Exception(f"Failed to export as MP3: {str(e)}")
        else:
            # Default to WAV
            sf.write(output_file, audio_data, sample_rate)
        
        return output_file
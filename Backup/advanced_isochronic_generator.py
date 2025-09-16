import numpy as np
import soundfile as sf
import scipy.signal
from enum import Enum


class WaveformType(Enum):
    """Enumeration of supported waveform types for carrier waves"""
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    NOISE = "noise"


class ModulationType(Enum):
    """Enumeration of supported modulation types for isochronic tones"""
    SQUARE = "square"         # Classic on/off isochronic
    SINE = "sine"             # Smoother sine wave modulation
    TRAPEZOID = "trapezoid"   # Trapezoidal with adjustable ramp
    GAUSSIAN = "gaussian"     # Gaussian pulse shape


class IsochronicToneGenerator:
    """Advanced generator for isochronic tones with various carrier and modulation options"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
    
    def generate_carrier(self, waveform_type, frequency, duration, amplitude=1.0):
        """Generate carrier wave with specified waveform type"""
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
        """Generate modulation envelope with specified type"""
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
            
            # Determine width of Gaussian pulse (in samples)
            period_samples = int(self.sample_rate / frequency)
            sigma = period_samples / 6  # Standard deviation
            
            # Generate Gaussian pulses at each cycle
            for i in range(0, num_samples, period_samples):
                pulse_center = i + period_samples // 2
                x = np.arange(num_samples)
                gauss_pulse = np.exp(-0.5 * ((x - pulse_center) / sigma)**2)
                envelope = np.maximum(envelope, gauss_pulse)
            
            # Normalize to [0, 1]
            if np.max(envelope) > 0:
                envelope /= np.max(envelope)
            
            return envelope
        
        # Default to square wave if type is unknown
        return 0.5 * (1 + scipy.signal.square(2 * np.pi * frequency * t))
    
    def generate_frequency_transition(self, start_freq, end_freq, duration, transition_type="linear"):
        """Generate a frequency array for smooth transitions"""
        num_samples = int(self.sample_rate * duration)
        
        if transition_type == "linear":
            # Linear transition
            return np.linspace(start_freq, end_freq, num_samples)
            
        elif transition_type == "exponential":
            # Exponential transition
            return np.logspace(
                np.log10(max(0.1, start_freq)),  # Avoid log(0)
                np.log10(end_freq),
                num_samples
            )
            
        elif transition_type == "logarithmic":
            # Logarithmic transition
            log_start = np.log(max(1.0, start_freq))
            log_end = np.log(max(1.0, end_freq))
            log_values = np.linspace(log_start, log_end, num_samples)
            return np.exp(log_values)
            
        elif transition_type == "quadratic":
            # Quadratic easing
            t = np.linspace(0, 1, num_samples)
            if start_freq < end_freq:
                # Ease in
                factor = t ** 2
            else:
                # Ease out
                factor = 1 - (1 - t) ** 2
            return start_freq + (end_freq - start_freq) * factor
            
        elif transition_type == "sigmoid":
            # Sigmoid (logistic) transition
            t = np.linspace(-6, 6, num_samples)  # -6 to 6 gives good sigmoid range
            sigmoid = 1 / (1 + np.exp(-t))
            # Scale to frequency range
            return start_freq + (end_freq - start_freq) * sigmoid
        
        # Default to linear if type is unknown
        return np.linspace(start_freq, end_freq, num_samples)
    
    def generate_advanced_isochronic(self, 
                               carrier_type=WaveformType.SINE,
                               modulation_type=ModulationType.SQUARE,
                               start_freq=10.0,
                               end_freq=10.0,
                               base_freq=100.0,
                               duration=60,
                               volume=0.5,
                               transition_type="linear",
                               duty_cycle=0.5,
                               ramp_percent=10):
        """Generate an advanced isochronic tone with specified parameters"""
        # Create time array
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        # Generate carrier wave
        if start_freq == end_freq:
            # Constant frequency
            carrier = self.generate_carrier(carrier_type, base_freq, duration)
            
            # Generate modulation for constant frequency
            modulation = self.generate_modulation(
                modulation_type, start_freq, duration, duty_cycle, ramp_percent
            )
        else:
            # Frequency transition
            carrier = self.generate_carrier(carrier_type, base_freq, duration)
            
            # Generate frequency array for transition
            freq_array = self.generate_frequency_transition(
                start_freq, end_freq, duration, transition_type
            )
            
            # For modulation with changing frequency, we need to calculate phase accumulation
            phase = np.zeros(num_samples)
            for i in range(1, num_samples):
                phase[i] = phase[i-1] + 2 * np.pi * freq_array[i-1] / self.sample_rate
            
            # Generate modulation envelope using accumulated phase
            if modulation_type == ModulationType.SQUARE:
                modulation = 0.5 * (1 + np.sign(np.sin(phase)))
            elif modulation_type == ModulationType.SINE:
                modulation = 0.5 * (1 + np.sin(phase))
            elif modulation_type == ModulationType.TRAPEZOID:
                # Complex for varying frequency - use square wave modified with envelope
                sq_mod = 0.5 * (1 + np.sign(np.sin(phase)))
                # Add trapezoidal shape by convolving with a triangle window
                window_size = int(ramp_percent / 100 * self.sample_rate / np.mean(freq_array))
                if window_size > 1:
                    window = np.bartlett(window_size * 2)
                    modulation = np.convolve(sq_mod, window, mode='same')
                    modulation = modulation / np.max(modulation)
                else:
                    modulation = sq_mod
            elif modulation_type == ModulationType.GAUSSIAN:
                # Use square wave as basis and convolve with Gaussian
                sq_mod = 0.5 * (1 + np.sign(np.sin(phase)))
                # Add Gaussian shape by convolving with a Gaussian window
                window_size = int(self.sample_rate / np.mean(freq_array))
                if window_size > 1:
                    sigma = window_size / 6
                    x = np.linspace(-3, 3, window_size)
                    window = np.exp(-0.5 * (x ** 2))
                    modulation = np.convolve(sq_mod, window, mode='same')
                    modulation = modulation / np.max(modulation)
                else:
                    modulation = sq_mod
            else:
                # Default to square wave
                modulation = 0.5 * (1 + np.sign(np.sin(phase)))
        
        # Apply modulation to carrier wave with volume adjustment
        isochronic_tone = carrier * modulation * volume
        
        # Apply fade in/out (10ms fade)
        fade_samples = min(int(0.01 * self.sample_rate), num_samples // 10)
        if fade_samples > 0:
            # Fade in
            isochronic_tone[:fade_samples] *= np.linspace(0, 1, fade_samples)
            # Fade out
            isochronic_tone[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return isochronic_tone, self.sample_rate
    
    def mix_with_background(self, isochronic_tone, background, background_volume=0.3):
        """Mix isochronic tone with background audio"""
        # Ensure background is same length as tone
        tone_length = len(isochronic_tone)
        background_length = len(background)
        
        if background_length < tone_length:
            # Repeat background if needed
            repeats = int(np.ceil(tone_length / background_length))
            background_extended = np.tile(background, repeats)
            # Trim to match tone length
            background = background_extended[:tone_length]
        elif background_length > tone_length:
            # Trim background if longer
            background = background[:tone_length]
        
        # Mix with volume adjustment
        mixed_audio = isochronic_tone + background * background_volume
        
        # Normalize to avoid clipping
        max_amplitude = np.max(np.abs(mixed_audio))
        if max_amplitude > 1.0:
            mixed_audio = mixed_audio / max_amplitude
        
        return mixed_audio


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
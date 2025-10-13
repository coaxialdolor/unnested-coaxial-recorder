"""
Audio processing utilities for Voice Dataset Manager
"""
import os
from pathlib import Path
from pydub import AudioSegment
# Import for compression - handle different pydub versions
try:
    from pydub.effects import compress_dynamic_range
    COMPRESS_FUNC = compress_dynamic_range
except ImportError:
    try:
        from pydub.effects import compress_dyn
        COMPRESS_FUNC = compress_dyn
    except ImportError:
        # Fallback for older pydub versions
        COMPRESS_FUNC = None
import numpy as np
import shutil # Added for reliable file copying

def apply_compression(audio_segment: AudioSegment) -> AudioSegment:
    """
    Apply dynamic range compression to an AudioSegment.

    This reduces the difference between the loud and quiet parts of the speech.

    Args:
        audio_segment: AudioSegment to process

    Returns:
        Compressed AudioSegment
    """
    if COMPRESS_FUNC is None:
        print("Warning: No compression function available, using simple normalization")
        # Fallback: use simple peak normalization
        return audio_segment.normalize()

    # Compressor settings common for speech:
    threshold = -20.0  # Start compressing signals above -20 dBFS
    ratio = 4.0        # 4:1 ratio (for every 4dB over the threshold, only 1dB is allowed)
    attack = 5.0       # 5 ms attack time (fast to catch peaks)
    release = 50.0     # 50 ms release time (medium speed)

    # Use the available compression function
    compressed_audio = COMPRESS_FUNC(
        audio_segment,
        threshold=threshold,
        ratio=ratio,
        attack=attack,
        release=release
    )
    return compressed_audio


def process_audio(file_path: Path):
    """
    Process audio file:
    - Convert to WAV if needed
    - Normalize volume (using PEAK normalization)
    - Trim silence

    Args:
        file_path: Path to the audio file
    """
    try:
        # Load audio file
        audio = AudioSegment.from_file(file_path)

        # Convert to WAV if not already (and ensure standard format for voice)
        audio = audio.set_frame_rate(22050)  # Standard for Piper
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_sample_width(2)  # 16-bit

        # Normalize audio (adjust volume using PEAK normalization to avoid clipping)
        target_peak_dBFS = -1.0 # Target peak at -1 dBFS
        current_peak_dBFS = audio.max_dBFS
        
        # Calculate gain, ensuring we don't apply massive gain to silent files
        if current_peak_dBFS > -90.0:
            change_in_dBFS = target_peak_dBFS - current_peak_dBFS
        else:
            # For near-silent files, apply a default gain (e.g., from -15 dBFS to -1 dBFS)
            change_in_dBFS = target_peak_dBFS - (-15.0) 
            
        normalized_audio = audio.apply_gain(change_in_dBFS)

        # Trim silence
        silence_threshold = -40  # dB
        trimmed_audio = trim_silence(normalized_audio, silence_threshold)

        # Export processed audio
        trimmed_audio.export(file_path, format="wav")
        return True
    except Exception as e:
        print(f"Error processing audio: {e}")
        return False

def trim_silence(audio: AudioSegment, silence_threshold=-40, min_silence_len=100, silence_padding=200) -> AudioSegment:
    """
    Trim silence from the beginning and end of an audio segment and add consistent padding

    Args:
        audio: AudioSegment to process
        silence_threshold: silence threshold in dB
        min_silence_len: minimum silence length in ms (not used in current detect_leading_silence, but kept for signature)
        silence_padding: padding to add at start and end in ms

    Returns:
        Trimmed AudioSegment with consistent padding
    """
    def detect_leading_silence(sound: AudioSegment, silence_threshold: int, chunk_size=10) -> int:
        """
        Detect silence at the beginning of a sound file
        """
        trim_ms = 0
        while trim_ms < len(sound):
            # Check the average volume (dBFS) of a small chunk
            if sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold:
                trim_ms += chunk_size
            else:
                break
        return trim_ms

    start_trim = detect_leading_silence(audio, silence_threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold)

    # Ensure we don't trim too much
    if start_trim + end_trim >= len(audio):
        # If the entire audio would be trimmed, return a small portion or the original
        if len(audio) > 100:
            trimmed_audio = audio[len(audio)//3:2*len(audio)//3]
        else:
            trimmed_audio = audio
    else:
        trimmed_audio = audio[start_trim:len(audio)-end_trim]

    # Add consistent silence padding at the beginning and end
    silence_segment = AudioSegment.silent(duration=silence_padding)
    final_audio = silence_segment + trimmed_audio + silence_segment

    return final_audio

def get_audio_duration(file_path: Path) -> float:
    """
    Get the duration of an audio file in seconds
    """
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # Convert ms to seconds
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0

def process_audio_enhanced(file_path: Path, silence_threshold=-40, target_peak_volume=-1, silence_padding=200, create_backup=True, apply_comp=True) -> tuple[bool, float, float]:
    """
    Enhanced audio processing with configurable parameters (uses Peak Normalization).
    
    Args:
        file_path: Path to the audio file
        silence_threshold: Silence threshold in dB
        target_peak_volume: Target peak volume in dBFS (e.g., -1 to avoid clipping) <--- CHANGED
        silence_padding: Padding to add at start and end in ms
        create_backup: Whether to create a backup of the original file
        apply_comp: Whether to apply dynamic range compression

    Returns:
        Tuple of (success: bool, original_duration: float, new_duration: float)
    """
    try:
        # Create backup if requested
        if create_backup:
            backup_path = file_path.with_suffix('.wav.backup')
            if not backup_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)

        # Load audio file and standardize format
        audio = AudioSegment.from_file(file_path)
        original_duration = len(audio) / 1000.0
        
        audio = audio.set_frame_rate(22050)  # Standard for Piper
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_sample_width(2)  # 16-bit

        # 1. Apply Compression (to make the lows louder)
        if apply_comp:
            audio = apply_compression(audio)

        # 2. Peak Normalization (to set the final maximum volume and apply makeup gain)
        current_peak_dBFS = audio.max_dBFS
        
        if current_peak_dBFS > -90.0:
            change_in_dBFS = target_peak_volume - current_peak_dBFS
        else:
            change_in_dBFS = target_peak_volume - (-15.0) 
        
        normalized_audio = audio.apply_gain(change_in_dBFS)

        # 3. Trim silence and add padding
        processed_audio = trim_silence(normalized_audio, silence_threshold, silence_padding=silence_padding)

        # Export processed audio
        processed_audio.export(file_path, format="wav")
        new_duration = len(processed_audio) / 1000.0

        return True, original_duration, new_duration
    except Exception as e:
        print(f"Error processing audio {file_path}: {e}")
        return False, 0, 0

def process_audio_enhanced_with_sample_rate(file_path: Path, output_path: Path = None, silence_threshold=-40, target_peak_volume=-1, target_sample_rate=44100, silence_padding=200, create_backup=True, apply_comp=True) -> tuple[bool, float, float]:
    """
    Enhanced audio processing with configurable parameters including sample rate conversion.
    
    MODIFICATION: Uses Compression + Peak Normalization to make lows louder without clipping peaks.

    Args:
        file_path: Path to the input audio file
        output_path: Path to save the processed file (if None, overwrites input file)
        silence_threshold: Silence threshold in dB
        target_peak_volume: Target peak volume in dBFS (e.g., -1 to avoid clipping) <--- CHANGED
        target_sample_rate: Target sample rate in Hz
        silence_padding: Padding to add at start and end in ms
        create_backup: Whether to create a backup of the original file
        apply_comp: Whether to apply dynamic range compression <--- NEW

    Returns:
        Tuple of (success: bool, original_duration: float, new_duration: float)
    """
    try:
        # If no output path specified, use input path (overwrite)
        if output_path is None:
            output_path = file_path
        
        # Create backup if requested and overwriting
        if create_backup and output_path == file_path:
            backup_path = file_path.with_suffix('.wav.backup')
            if not backup_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)

        # Load audio file and standardize format
        audio = AudioSegment.from_file(file_path)
        original_duration = len(audio) / 1000.0

        # Convert to target sample rate and format
        audio = audio.set_frame_rate(target_sample_rate)
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_sample_width(2)  # 16-bit
        
        # 1. Apply Compression (to make the lows louder)
        if apply_comp:
            audio = apply_compression(audio)

        # 2. Peak Normalization (to set the final maximum volume and apply makeup gain)
        current_peak_dBFS = audio.max_dBFS
        
        if current_peak_dBFS > -90.0:
            change_in_dBFS = target_peak_volume - current_peak_dBFS
        else:
            # For near-silent files, apply a default gain (e.g., from -15 dBFS to -1 dBFS)
            change_in_dBFS = target_peak_volume - (-15.0) 
            
        normalized_audio = audio.apply_gain(change_in_dBFS)

        # 3. Trim silence and add padding
        processed_audio = trim_silence(normalized_audio, silence_threshold, silence_padding=silence_padding)

        # Export processed audio to output path
        processed_audio.export(output_path, format="wav")
        new_duration = len(processed_audio) / 1000.0

        return True, original_duration, new_duration
    except Exception as e:
        print(f"Error processing audio {file_path}: {e}")
        return False, 0, 0

def get_audio_info(file_path: Path):
    """
    Get comprehensive audio file information
    """
    try:
        audio = AudioSegment.from_file(file_path)
        return {
            'duration': len(audio) / 1000.0,  # seconds
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'sample_width': audio.sample_width,
            'frame_count': audio.frame_count(),
            'max_possible_amplitude': audio.max_possible_amplitude,
            'dBFS': audio.dBFS,
            'max_dBFS': audio.max_dBFS,
            'rms': audio.rms,
            'file_size': file_path.stat().st_size
        }
    except Exception as e:
        print(f"Error getting audio info for {file_path}: {e}")
        return None

def batch_process_audio(directory: Path, silence_threshold=-40, target_peak_volume=-1, silence_padding=200, create_backup=True, progress_callback=None):
    """
    Process multiple audio files in a directory (Updated for Peak Normalization)
    """
    audio_files = list(directory.glob("*.wav"))
    total_files = len(audio_files)
    processed_files = 0
    failed_files = []
    total_original_duration = 0
    total_new_duration = 0

    for i, file_path in enumerate(audio_files):
        if progress_callback:
            progress_callback(i, total_files, file_path.name)

        # Calls the enhanced function which now uses Peak Normalization
        success, original_duration, new_duration = process_audio_enhanced(
            file_path, silence_threshold, target_peak_volume, silence_padding, create_backup
        )

        if success:
            processed_files += 1
            total_original_duration += original_duration
            total_new_duration += new_duration
        else:
            failed_files.append(file_path.name)

    return {
        'total_files': total_files,
        'processed_files': processed_files,
        'failed_files': failed_files,
        'total_original_duration': total_original_duration,
        'total_new_duration': total_new_duration,
        'success_rate': (processed_files / total_files * 100) if total_files > 0 else 0
    }

def export_audio_file(input_path: Path, output_dir: Path, format="wav", sample_rate=44100, bit_depth=16, channels=1, mp3_bitrate="192"):
    """
    Export an audio file in the specified format and settings (No change needed here)
    """
    try:
        # Load audio file
        audio = AudioSegment.from_file(input_path)

        # Convert to specified format
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_channels(channels)

        # Set bit depth (sample width)
        if bit_depth == 16:
            audio = audio.set_sample_width(2)
        elif bit_depth == 24:
            audio = audio.set_sample_width(3)
        elif bit_depth == 32:
            audio = audio.set_sample_width(4)
        else:
            audio = audio.set_sample_width(2)  # Default to 16-bit

        # Generate output filename
        output_filename = input_path.stem + f".{format}"
        output_path = output_dir / output_filename

        # Export with format-specific parameters
        if format.lower() == "mp3":
            audio.export(output_path, format="mp3", bitrate=f"{mp3_bitrate}k")
        elif format.lower() == "flac":
            audio.export(output_path, format="flac")
        elif format.lower() == "ogg":
            audio.export(output_path, format="ogg", codec="libvorbis")
        else:  # WAV
            audio.export(output_path, format="wav")

        return True, output_path
    except Exception as e:
        print(f"Error exporting audio {input_path}: {e}")
        return False, None
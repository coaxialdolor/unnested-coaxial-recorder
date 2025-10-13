"""
Audio processing utilities for Voice Dataset Manager
"""
import os
from pathlib import Path
from pydub import AudioSegment
import numpy as np

def process_audio(file_path: Path):
    """
    Process audio file:
    - Convert to WAV if needed
    - Normalize volume
    - Trim silence

    Args:
        file_path: Path to the audio file
    """
    try:
        # Load audio file
        audio = AudioSegment.from_file(file_path)

        # Convert to WAV if not already
        if file_path.suffix.lower() != '.wav':
            audio = audio.set_frame_rate(22050)  # Standard for Piper
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_sample_width(2)  # 16-bit

        # Normalize audio (adjust volume)
        target_dBFS = -20.0
        change_in_dBFS = target_dBFS - audio.dBFS
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

def trim_silence(audio, silence_threshold=-40, min_silence_len=100, silence_padding=200):
    """
    Trim silence from the beginning and end of an audio segment and add consistent padding

    Args:
        audio: AudioSegment to process
        silence_threshold: silence threshold in dB
        min_silence_len: minimum silence length in ms
        silence_padding: padding to add at start and end in ms

    Returns:
        Trimmed AudioSegment with consistent padding
    """
    def detect_leading_silence(sound, silence_threshold, chunk_size=10):
        """
        Detect silence at the beginning of a sound file
        """
        trim_ms = 0
        while trim_ms < len(sound):
            if sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold:
                trim_ms += chunk_size
            else:
                break
        return trim_ms

    start_trim = detect_leading_silence(audio, silence_threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold)

    # Ensure we don't trim too much
    if start_trim + end_trim >= len(audio):
        # If the entire audio would be trimmed, return a small portion
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

def get_audio_duration(file_path):
    """
    Get the duration of an audio file in seconds

    Args:
        file_path: Path to the audio file

    Returns:
        Duration in seconds
    """
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # Convert ms to seconds
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0

def process_audio_enhanced(file_path: Path, silence_threshold=-40, target_volume=-20, silence_padding=200, create_backup=True):
    """
    Enhanced audio processing with configurable parameters

    Args:
        file_path: Path to the audio file
        silence_threshold: Silence threshold in dB
        target_volume: Target volume in dB
        silence_padding: Padding to add at start and end in ms
        create_backup: Whether to create a backup of the original file

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

        # Load audio file
        audio = AudioSegment.from_file(file_path)
        original_duration = len(audio) / 1000.0

        # Convert to WAV if not already
        if file_path.suffix.lower() != '.wav':
            audio = audio.set_frame_rate(22050)  # Standard for Piper
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_sample_width(2)  # 16-bit

        # Normalize audio (adjust volume)
        change_in_dBFS = target_volume - audio.dBFS
        normalized_audio = audio.apply_gain(change_in_dBFS)

        # Trim silence and add padding
        processed_audio = trim_silence(normalized_audio, silence_threshold, silence_padding=silence_padding)

        # Export processed audio
        processed_audio.export(file_path, format="wav")
        new_duration = len(processed_audio) / 1000.0

        return True, original_duration, new_duration
    except Exception as e:
        print(f"Error processing audio {file_path}: {e}")
        return False, 0, 0

def process_audio_enhanced_with_sample_rate(file_path: Path, output_path: Path = None, silence_threshold=-40, target_volume=-6, target_sample_rate=44100, silence_padding=200, create_backup=True):
    """
    Enhanced audio processing with configurable parameters including sample rate conversion

    Args:
        file_path: Path to the input audio file
        output_path: Path to save the processed file (if None, overwrites input file)
        silence_threshold: Silence threshold in dB
        target_volume: Target volume in dB
        target_sample_rate: Target sample rate in Hz
        silence_padding: Padding to add at start and end in ms
        create_backup: Whether to create a backup of the original file

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

        # Load audio file
        audio = AudioSegment.from_file(file_path)
        original_duration = len(audio) / 1000.0

        # Convert to target sample rate and format
        audio = audio.set_frame_rate(target_sample_rate)
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_sample_width(2)  # 16-bit

        # Normalize audio (adjust volume)
        change_in_dBFS = target_volume - audio.dBFS
        normalized_audio = audio.apply_gain(change_in_dBFS)

        # Trim silence and add padding
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

    Args:
        file_path: Path to the audio file

    Returns:
        Dictionary with audio information
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

def batch_process_audio(directory: Path, silence_threshold=-40, target_volume=-20, silence_padding=200, create_backup=True, progress_callback=None):
    """
    Process multiple audio files in a directory

    Args:
        directory: Directory containing audio files
        silence_threshold: Silence threshold in dB
        target_volume: Target volume in dB
        silence_padding: Padding to add at start and end in ms
        create_backup: Whether to create backups
        progress_callback: Function to call with progress updates (current, total, current_file)

    Returns:
        Dictionary with processing results
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

        success, original_duration, new_duration = process_audio_enhanced(
            file_path, silence_threshold, target_volume, silence_padding, create_backup
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
    Export an audio file in the specified format and settings

    Args:
        input_path: Path to the input audio file
        output_dir: Directory to save the exported file
        format: Output format (wav, mp3, flac, ogg)
        sample_rate: Sample rate in Hz
        bit_depth: Bit depth (16, 24, 32)
        channels: Number of channels (1 for mono, 2 for stereo)
        mp3_bitrate: MP3 bitrate in kbps (only used for MP3 format)

    Returns:
        Tuple of (success: bool, output_path: Path)
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
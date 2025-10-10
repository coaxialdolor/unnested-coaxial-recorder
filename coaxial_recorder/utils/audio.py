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

def trim_silence(audio, silence_threshold=-40, min_silence_len=100):
    """
    Trim silence from the beginning and end of an audio segment
    
    Args:
        audio: AudioSegment to process
        silence_threshold: silence threshold in dB
        min_silence_len: minimum silence length in ms
        
    Returns:
        Trimmed AudioSegment
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
            return audio[len(audio)//3:2*len(audio)//3]
        return audio
    
    trimmed_audio = audio[start_trim:len(audio)-end_trim]
    return trimmed_audio

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
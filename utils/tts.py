"""
Text-to-Speech synthesis utilities using Piper TTS
"""
import os
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PiperTTS:
    """Piper TTS synthesis engine"""

    def __init__(self):
        self.available_models = {}
        self.load_available_models()

    def load_available_models(self):
        """Load available Piper models from checkpoints directory"""
        checkpoints_dir = Path("checkpoints")
        if not checkpoints_dir.exists():
            logger.warning("Checkpoints directory not found")
            return

        for lang_dir in checkpoints_dir.iterdir():
            if lang_dir.is_dir():
                language = lang_dir.name
                self.available_models[language] = {}

                for voice_dir in lang_dir.iterdir():
                    if voice_dir.is_dir():
                        voice_id = voice_dir.name

                        # Look for .onnx model files
                        onnx_files = list(voice_dir.glob("*.onnx"))
                        config_files = list(voice_dir.glob("*.json"))

                        if onnx_files and config_files:
                            self.available_models[language][voice_id] = {
                                "model_path": onnx_files[0],
                                "config_path": config_files[0],
                                "voice_dir": voice_dir
                            }

    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return list(self.available_models.keys())

    def get_available_voices(self, language: str) -> list:
        """Get list of available voices for a language"""
        return list(self.available_models.get(language, {}).keys())

    def synthesize(self, text: str, language: str, voice_id: str, output_path: Path,
                   speech_rate: float = 1.0, speech_pitch: float = 1.0) -> bool:
        """
        Synthesize speech from text using Piper TTS

        Args:
            text: Text to synthesize
            language: Language code (e.g., 'en-US')
            voice_id: Voice identifier (e.g., 'amy')
            output_path: Path to save the generated audio
            speech_rate: Speech rate multiplier (0.5-2.0)
            speech_pitch: Speech pitch multiplier (0.5-2.0)

        Returns:
            bool: True if synthesis was successful
        """
        try:
            if language not in self.available_models:
                logger.error(f"Language {language} not available")
                return False

            if voice_id not in self.available_models[language]:
                logger.error(f"Voice {voice_id} not available for language {language}")
                return False

            model_info = self.available_models[language][voice_id]
            model_path = model_info["model_path"]
            config_path = model_info["config_path"]

            # Create temporary text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(text)
                temp_text_path = temp_file.name

            try:
                # Use Piper TTS command line tool
                cmd = [
                    "piper",
                    "--model", str(model_path),
                    "--config", str(config_path),
                    "--output_file", str(output_path),
                    "--text_file", temp_text_path
                ]

                # Add speech rate and pitch if supported
                if speech_rate != 1.0:
                    cmd.extend(["--speaker_id", "0"])  # Default speaker

                logger.info(f"Running Piper TTS: {' '.join(cmd)}")

                # Run Piper TTS
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    logger.info(f"Successfully synthesized audio to {output_path}")
                    return True
                else:
                    logger.error(f"Piper TTS failed: {result.stderr}")
                    return False

            finally:
                # Clean up temporary file
                os.unlink(temp_text_path)

        except subprocess.TimeoutExpired:
            logger.error("Piper TTS synthesis timed out")
            return False
        except Exception as e:
            logger.error(f"Error during synthesis: {e}")
            return False

    def synthesize_with_espeak(self, text: str, language: str, voice_id: str,
                              output_path: Path, speech_rate: float = 1.0,
                              speech_pitch: float = 1.0) -> bool:
        """
        Alternative synthesis method using espeak-ng + Piper
        This method converts text to phonemes first, then synthesizes
        """
        try:
            if language not in self.available_models:
                logger.error(f"Language {language} not available")
                return False

            if voice_id not in self.available_models[language]:
                logger.error(f"Voice {voice_id} not available for language {language}")
                return False

            model_info = self.available_models[language][voice_id]
            model_path = model_info["model_path"]
            config_path = model_info["config_path"]

            # Convert text to phonemes using espeak-ng
            phonemes = self.text_to_phonemes(text, language)
            if not phonemes:
                logger.error("Failed to convert text to phonemes")
                return False

            # Create temporary phoneme file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(phonemes)
                temp_phoneme_path = temp_file.name

            try:
                # Use Piper TTS with phonemes
                cmd = [
                    "piper",
                    "--model", str(model_path),
                    "--config", str(config_path),
                    "--output_file", str(output_path),
                    "--phoneme_file", temp_phoneme_path
                ]

                logger.info(f"Running Piper TTS with phonemes: {' '.join(cmd)}")

                # Run Piper TTS
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    logger.info(f"Successfully synthesized audio to {output_path}")
                    return True
                else:
                    logger.error(f"Piper TTS failed: {result.stderr}")
                    return False

            finally:
                # Clean up temporary file
                os.unlink(temp_phoneme_path)

        except subprocess.TimeoutExpired:
            logger.error("Piper TTS synthesis timed out")
            return False
        except Exception as e:
            logger.error(f"Error during synthesis: {e}")
            return False

    def text_to_phonemes(self, text: str, language: str) -> Optional[str]:
        """
        Convert text to phonemes using espeak-ng

        Args:
            text: Text to convert
            language: Language code

        Returns:
            str: Phoneme sequence or None if failed
        """
        try:
            # Map language codes to espeak-ng language codes
            espeak_lang_map = {
                'en-US': 'en-us',
                'en-GB': 'en-gb',
                'sv-SE': 'sv',
                'it-IT': 'it',
                'fr-FR': 'fr',
                'de-DE': 'de',
                'es-ES': 'es',
                'pt-BR': 'pt',
                'nl-NL': 'nl'
            }

            espeak_lang = espeak_lang_map.get(language, 'en-us')

            # Use espeak-ng to convert text to phonemes
            cmd = [
                "espeak-ng",
                "-q",  # Quiet mode
                "-x",  # Output phonemes
                "-v", espeak_lang,  # Voice/language
                text
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                phonemes = result.stdout.strip()
                logger.info(f"Converted '{text}' to phonemes: {phonemes}")
                return phonemes
            else:
                logger.error(f"espeak-ng failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("espeak-ng conversion timed out")
            return None
        except Exception as e:
            logger.error(f"Error converting text to phonemes: {e}")
            return None

    def get_model_info(self, language: str, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        if language not in self.available_models:
            return None

        if voice_id not in self.available_models[language]:
            return None

        model_info = self.available_models[language][voice_id]

        # Try to read config file for additional info
        config_info = {}
        try:
            with open(model_info["config_path"], 'r') as f:
                config_data = json.load(f)
                config_info = {
                    "sample_rate": config_data.get("audio", {}).get("sample_rate", 22050),
                    "channels": config_data.get("audio", {}).get("channels", 1),
                    "phoneme_type": config_data.get("phoneme_type", "unknown"),
                    "speaker_id": config_data.get("speaker_id", 0)
                }
        except Exception as e:
            logger.warning(f"Could not read config file: {e}")

        return {
            "language": language,
            "voice_id": voice_id,
            "model_path": str(model_info["model_path"]),
            "config_path": str(model_info["config_path"]),
            "voice_dir": str(model_info["voice_dir"]),
            **config_info
        }

# Global TTS instance
_tts_instance = None

def get_tts_instance() -> PiperTTS:
    """Get global TTS instance"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = PiperTTS()
    return _tts_instance

def synthesize_speech(text: str, language: str, voice_id: str, output_path: Path,
                     length_scale: float = 1.0, noise_scale: float = 0.667) -> bool:
    """
    Convenience function for speech synthesis

    Args:
        text: Text to synthesize
        language: Language code
        voice_id: Voice identifier
        output_path: Path to save audio
        length_scale: Length scale for VITS (controls speech rate)
        noise_scale: Noise scale for VITS (controls randomness)

    Returns:
        bool: True if successful
    """
    tts = get_tts_instance()

    # Map VITS parameters to Piper parameters
    # length_scale controls speech rate (inverse relationship)
    speech_rate = 1.0 / length_scale if length_scale != 0 else 1.0
    # noise_scale doesn't have a direct equivalent in Piper, so we'll use a default
    speech_pitch = 1.0

    # Try direct synthesis first
    if tts.synthesize(text, language, voice_id, output_path, speech_rate, speech_pitch):
        return True

    # Fallback to phoneme-based synthesis
    logger.info("Direct synthesis failed, trying phoneme-based synthesis")
    return tts.synthesize_with_espeak(text, language, voice_id, output_path, speech_rate, speech_pitch)


def synthesize_speech_with_checkpoint(text: str, checkpoint_path: Path, output_path: Path,
                                     length_scale: float = 1.0, noise_scale: float = 0.667) -> bool:
    """
    Synthesize speech using a custom PyTorch checkpoint (VITS model)
    
    Args:
        text: Text to synthesize
        checkpoint_path: Path to the PyTorch checkpoint
        output_path: Path to save the generated audio
        length_scale: Length scale for VITS (controls speech rate)
        noise_scale: Noise scale for VITS (controls randomness)
    
    Returns:
        bool: True if synthesis was successful
    """
    try:
        import torch
        import torchaudio
        from utils.vits_training import SimpleTTSModel
        from utils.phonemes import text_to_phonemes

        # Force CPU inference for stability on Windows
        device = torch.device('cpu')

        # Load checkpoint (CPU)
        checkpoint = torch.load(checkpoint_path, map_location=device)

        # Model config
        model_config = checkpoint.get('config', {})
        if not model_config:
            model_config = {
                'hidden_dim': 512,
                'sample_rate': 22050
            }

        sample_rate = int(model_config.get('sample_rate', 22050))
        n_mels = 80
        hop_length = 256
        n_fft = 1024
        n_stft = n_fft // 2 + 1

        # Create model on CPU
        model = SimpleTTSModel(model_config).to(device)

        # Load state dict
        if 'state_dict' in checkpoint:
            model.load_state_dict(checkpoint['state_dict'])
        else:
            model.load_state_dict(checkpoint)

        model.eval()

        # Get phonemes (required by current pipeline)
        phonemes_str = text_to_phonemes(text, 'sv-SE')
        if not phonemes_str:
            return False

        # Create a basic mel input driven by phoneme length
        mel_length = max(10, len(phonemes_str.split()) * 50)
        mel_spec = torch.randn(1, mel_length, n_mels, device=device)

        # Forward pass: model outputs mel (batch, time, features)
        with torch.no_grad():
            mel_out_bt_f = model(mel_spec)

        # Prepare for inverse mel: (batch, features, time)
        mel_out_bf_t = mel_out_bt_f.transpose(1, 2).contiguous()

        # Invert mel to linear spectrogram
        inv_mel = torchaudio.transforms.InverseMelScale(
            n_stft=n_stft,
            n_mels=n_mels,
            sample_rate=sample_rate,
        ).to(device)
        mag_spec = torch.clamp(inv_mel(mel_out_bf_t), min=0.0)

        # Griffin-Lim to waveform
        griffin = torchaudio.transforms.GriffinLim(
            n_fft=n_fft,
            hop_length=hop_length,
            n_iter=32,
        ).to(device)
        waveform = griffin(mag_spec)

        # Ensure mono [1, T]
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)

        # Normalize to prevent clipping
        peak = waveform.abs().max().item() if waveform.numel() > 0 else 1.0
        if peak > 0:
            waveform = waveform / peak * 0.95

        # Save WAV
        torchaudio.save(str(output_path), waveform.cpu(), sample_rate)
        return True

    except Exception:
        return False

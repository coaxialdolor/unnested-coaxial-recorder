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
                     speech_rate: float = 1.0, speech_pitch: float = 1.0) -> bool:
    """
    Convenience function for speech synthesis

    Args:
        text: Text to synthesize
        language: Language code
        voice_id: Voice identifier
        output_path: Path to save audio
        speech_rate: Speech rate multiplier
        speech_pitch: Speech pitch multiplier

    Returns:
        bool: True if successful
    """
    tts = get_tts_instance()

    # Try direct synthesis first
    if tts.synthesize(text, language, voice_id, output_path, speech_rate, speech_pitch):
        return True

    # Fallback to phoneme-based synthesis
    logger.info("Direct synthesis failed, trying phoneme-based synthesis")
    return tts.synthesize_with_espeak(text, language, voice_id, output_path, speech_rate, speech_pitch)

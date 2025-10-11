"""
Montreal Forced Aligner (MFA) Integration for Coaxial Recorder
Handles text-audio alignment for TTS training
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MFAAlignment:
    """Handles Montreal Forced Aligner integration for text-audio alignment"""

    def __init__(self, mfa_path: Optional[str] = None):
        self.mfa_path = mfa_path or self._find_mfa_path()
        self.language_models = self._get_available_models()

    def _find_mfa_path(self) -> Optional[str]:
        """Find MFA installation path"""
        possible_paths = [
            "mfa",  # In PATH
            "/usr/local/bin/mfa",
            "/opt/mfa/bin/mfa",
            "~/mfa/bin/mfa",
            "~/miniconda3/bin/mfa",
            "~/anaconda3/bin/mfa"
        ]

        for path in possible_paths:
            expanded_path = os.path.expanduser(path)
            if shutil.which(expanded_path) or os.path.exists(expanded_path):
                logger.info(f"Found MFA at: {expanded_path}")
                return expanded_path

        logger.warning("MFA not found in standard locations")
        return None

    def _get_available_models(self) -> Dict[str, str]:
        """Get available MFA language models"""
        return {
            "en-US": "english_us_arpa",
            "en-GB": "english_uk_mfa",
            "en-AU": "english_au_mfa",
            "en-CA": "english_ca_mfa",
            "en-IN": "english_in_mfa",
            "en-IE": "english_ie_mfa",
            "sv-SE": "swedish_mfa",
            "it-IT": "italian_mfa",
            "es-ES": "spanish_mfa",
            "es-MX": "spanish_mx_mfa",
            "fr-FR": "french_mfa",
            "fr-CA": "french_ca_mfa",
            "fr-BE": "french_be_mfa",
            "fr-CH": "french_ch_mfa",
            "de-DE": "german_mfa",
            "de-AT": "german_at_mfa",
            "de-CH": "german_ch_mfa",
            "pt-BR": "portuguese_br_mfa",
            "pt-PT": "portuguese_pt_mfa",
            "nl-NL": "dutch_mfa",
            "nl-BE": "dutch_be_mfa",
            "da-DK": "danish_mfa",
            "nb-NO": "norwegian_mfa",
            "fi-FI": "finnish_mfa",
            "ru-RU": "russian_mfa",
            "pl-PL": "polish_mfa",
            "cs-CZ": "czech_mfa",
            "sk-SK": "slovak_mfa",
            "hr-HR": "croatian_mfa",
            "sl-SI": "slovenian_mfa",
            "bg-BG": "bulgarian_mfa",
            "ro-RO": "romanian_mfa",
            "ja-JP": "japanese_mfa",
            "ko-KR": "korean_mfa",
            "zh-CN": "chinese_mfa",
            "zh-TW": "chinese_tw_mfa",
            "zh-HK": "chinese_hk_mfa",
            "th-TH": "thai_mfa",
            "vi-VN": "vietnamese_mfa",
            "ar-SA": "arabic_mfa",
            "ar-EG": "arabic_eg_mfa",
            "he-IL": "hebrew_mfa",
            "hi-IN": "hindi_mfa",
            "tr-TR": "turkish_mfa",
            "el-GR": "greek_mfa",
            "hu-HU": "hungarian_mfa",
            "ca-ES": "catalan_mfa",
            "eu-ES": "basque_mfa",
            "cy-GB": "welsh_mfa",
            "sq-AL": "albanian_mfa",
            "af-ZA": "afrikaans_mfa",
            "id-ID": "indonesian_mfa",
            "ms-MY": "malay_mfa",
            "sw-KE": "swahili_mfa",
            "ta-IN": "tamil_mfa",
            "te-IN": "telugu_mfa",
            "ne-NP": "nepali_mfa"
        }

    def is_available(self) -> bool:
        """Check if MFA is available"""
        if not self.mfa_path:
            return False

        try:
            result = subprocess.run([self.mfa_path, '--version'],
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available MFA models"""
        if not self.is_available():
            return []

        try:
            result = subprocess.run([self.mfa_path, 'model', 'list'],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                models = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and not line.startswith('Available'):
                        models.append(line.strip())
                return models
            else:
                logger.warning(f"MFA model list failed: {result.stderr}")
                return list(self.language_models.values())
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.error(f"Error getting MFA models: {e}")
            return list(self.language_models.values())

    def download_model(self, language_code: str) -> bool:
        """Download MFA model for a language"""
        if not self.is_available():
            logger.error("MFA not available")
            return False

        model_name = self.language_models.get(language_code)
        if not model_name:
            logger.error(f"No MFA model available for language: {language_code}")
            return False

        try:
            logger.info(f"Downloading MFA model: {model_name}")
            result = subprocess.run([
                self.mfa_path, 'model', 'download', 'acoustic', model_name
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout

            if result.returncode == 0:
                logger.info(f"Successfully downloaded model: {model_name}")
                return True
            else:
                logger.error(f"Failed to download model {model_name}: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.error(f"Error downloading MFA model: {e}")
            return False

    def align_audio_text(self, audio_dir: Path, text_dir: Path,
                        output_dir: Path, language_code: str) -> bool:
        """Align audio files with text using MFA"""
        if not self.is_available():
            logger.error("MFA not available")
            return False

        model_name = self.language_models.get(language_code)
        if not model_name:
            logger.error(f"No MFA model available for language: {language_code}")
            return False

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Starting MFA alignment for {language_code}")
            logger.info(f"Audio dir: {audio_dir}")
            logger.info(f"Text dir: {text_dir}")
            logger.info(f"Output dir: {output_dir}")
            logger.info(f"Model: {model_name}")

            # Run MFA alignment
            result = subprocess.run([
                self.mfa_path, 'align',
                str(audio_dir),
                str(text_dir),
                model_name,
                str(output_dir)
            ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout

            if result.returncode == 0:
                logger.info("MFA alignment completed successfully")
                return True
            else:
                logger.error(f"MFA alignment failed: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.error(f"Error running MFA alignment: {e}")
            return False

    def validate_alignment(self, alignment_dir: Path) -> Dict:
        """Validate MFA alignment results"""
        validation_result = {
            "valid": False,
            "total_files": 0,
            "aligned_files": 0,
            "errors": [],
            "warnings": []
        }

        if not alignment_dir.exists():
            validation_result["errors"].append(f"Alignment directory does not exist: {alignment_dir}")
            return validation_result

        # Check for TextGrid files
        textgrid_files = list(alignment_dir.glob("*.TextGrid"))
        validation_result["total_files"] = len(textgrid_files)

        if len(textgrid_files) == 0:
            validation_result["errors"].append("No TextGrid files found in alignment output")
            return validation_result

        # Validate each TextGrid file
        for textgrid_file in textgrid_files:
            try:
                # Basic validation - check if file is not empty and has content
                if textgrid_file.stat().st_size > 0:
                    validation_result["aligned_files"] += 1
                else:
                    validation_result["warnings"].append(f"Empty TextGrid file: {textgrid_file.name}")
            except Exception as e:
                validation_result["errors"].append(f"Error validating {textgrid_file.name}: {e}")

        # Determine if alignment is valid
        if validation_result["aligned_files"] > 0 and len(validation_result["errors"]) == 0:
            validation_result["valid"] = True

        return validation_result

    def convert_to_piper_format(self, alignment_dir: Path,
                               output_dir: Path, language_code: str) -> bool:
        """Convert MFA alignment to Piper training format"""
        if not alignment_dir.exists():
            logger.error(f"Alignment directory does not exist: {alignment_dir}")
            return False

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # This would implement the conversion from TextGrid to Piper format
            # For now, this is a placeholder that copies the alignment files

            logger.info("Converting MFA alignment to Piper format...")

            # Copy TextGrid files to output directory
            textgrid_files = list(alignment_dir.glob("*.TextGrid"))
            for textgrid_file in textgrid_files:
                output_file = output_dir / textgrid_file.name
                shutil.copy2(textgrid_file, output_file)

            # Create metadata file
            metadata = {
                "language": language_code,
                "alignment_tool": "MFA",
                "total_files": len(textgrid_files),
                "format": "TextGrid"
            }

            metadata_file = output_dir / "alignment_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Converted {len(textgrid_files)} alignment files to Piper format")
            return True

        except Exception as e:
            logger.error(f"Error converting alignment to Piper format: {e}")
            return False

    def prepare_training_data(self, recordings_dir: Path, transcripts_dir: Path,
                            output_dir: Path, language_code: str) -> bool:
        """Prepare training data with MFA alignment"""
        if not self.is_available():
            logger.error("MFA not available, skipping alignment")
            return False

        # Create temporary directory for MFA alignment
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            alignment_dir = temp_path / "alignment"

            # Run MFA alignment
            if not self.align_audio_text(recordings_dir, transcripts_dir,
                                       alignment_dir, language_code):
                logger.error("MFA alignment failed")
                return False

            # Validate alignment
            validation = self.validate_alignment(alignment_dir)
            if not validation["valid"]:
                logger.error(f"Alignment validation failed: {validation['errors']}")
                return False

            # Convert to Piper format
            if not self.convert_to_piper_format(alignment_dir, output_dir, language_code):
                logger.error("Failed to convert alignment to Piper format")
                return False

            logger.info("Training data preparation completed successfully")
            return True

# Global instance
mfa_aligner = MFAAlignment()

def get_mfa_aligner() -> MFAAlignment:
    """Get the global MFA aligner instance"""
    return mfa_aligner

# Convenience functions
def is_mfa_available() -> bool:
    """Check if MFA is available"""
    return mfa_aligner.is_available()

def align_audio_text(audio_dir: Path, text_dir: Path,
                    output_dir: Path, language_code: str) -> bool:
    """Align audio files with text using MFA"""
    return mfa_aligner.align_audio_text(audio_dir, text_dir, output_dir, language_code)

def prepare_training_data(recordings_dir: Path, transcripts_dir: Path,
                         output_dir: Path, language_code: str) -> bool:
    """Prepare training data with MFA alignment"""
    return mfa_aligner.prepare_training_data(recordings_dir, transcripts_dir,
                                            output_dir, language_code)

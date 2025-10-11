"""
Phoneme and Language Support for Coaxial Recorder
Handles phoneme sets, language configuration, and eSpeak NG integration
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhonemeManager:
    """Manages phoneme sets and language configuration for TTS training"""

    def __init__(self):
        self.language_configs = self._load_language_configs()
        self.espeak_voices = self._get_espeak_voices()

    def _load_language_configs(self) -> Dict[str, Dict]:
        """Load language configurations with phoneme set mappings"""
        return {
            # English variants
            "en-US": {
                "espeak_voice": "en-us",
                "phoneme_set": "en-us",
                "description": "English (United States)",
                "supported": True,
                "mfa_language": "english_us_arpa",
                "sample_rate": 22050
            },
            "en-GB": {
                "espeak_voice": "en-gb",
                "phoneme_set": "en-gb",
                "description": "English (United Kingdom)",
                "supported": True,
                "mfa_language": "english_uk_mfa",
                "sample_rate": 22050
            },
            "en-AU": {
                "espeak_voice": "en-au",
                "phoneme_set": "en-au",
                "description": "English (Australia)",
                "supported": True,
                "mfa_language": "english_au_mfa",
                "sample_rate": 22050
            },
            "en-CA": {
                "espeak_voice": "en-ca",
                "phoneme_set": "en-ca",
                "description": "English (Canada)",
                "supported": True,
                "mfa_language": "english_ca_mfa",
                "sample_rate": 22050
            },
            "en-IN": {
                "espeak_voice": "en-in",
                "phoneme_set": "en-in",
                "description": "English (India)",
                "supported": True,
                "mfa_language": "english_in_mfa",
                "sample_rate": 22050
            },
            "en-IE": {
                "espeak_voice": "en-ie",
                "phoneme_set": "en-ie",
                "description": "English (Ireland)",
                "supported": True,
                "mfa_language": "english_ie_mfa",
                "sample_rate": 22050
            },

            # Swedish
            "sv-SE": {
                "espeak_voice": "sv",
                "phoneme_set": "sv",
                "description": "Swedish (Sweden)",
                "supported": True,
                "mfa_language": "swedish_mfa",
                "sample_rate": 22050
            },

            # Italian
            "it-IT": {
                "espeak_voice": "it",
                "phoneme_set": "it",
                "description": "Italian (Italy)",
                "supported": True,
                "mfa_language": "italian_mfa",
                "sample_rate": 22050
            },

            # Spanish variants
            "es-ES": {
                "espeak_voice": "es",
                "phoneme_set": "es",
                "description": "Spanish (Spain)",
                "supported": True,
                "mfa_language": "spanish_mfa",
                "sample_rate": 22050
            },
            "es-MX": {
                "espeak_voice": "es-mx",
                "phoneme_set": "es-mx",
                "description": "Spanish (Mexico)",
                "supported": True,
                "mfa_language": "spanish_mx_mfa",
                "sample_rate": 22050
            },

            # French variants
            "fr-FR": {
                "espeak_voice": "fr",
                "phoneme_set": "fr",
                "description": "French (France)",
                "supported": True,
                "mfa_language": "french_mfa",
                "sample_rate": 22050
            },
            "fr-CA": {
                "espeak_voice": "fr-ca",
                "phoneme_set": "fr-ca",
                "description": "French (Canada)",
                "supported": True,
                "mfa_language": "french_ca_mfa",
                "sample_rate": 22050
            },
            "fr-BE": {
                "espeak_voice": "fr-be",
                "phoneme_set": "fr-be",
                "description": "French (Belgium)",
                "supported": True,
                "mfa_language": "french_be_mfa",
                "sample_rate": 22050
            },
            "fr-CH": {
                "espeak_voice": "fr-ch",
                "phoneme_set": "fr-ch",
                "description": "French (Switzerland)",
                "supported": True,
                "mfa_language": "french_ch_mfa",
                "sample_rate": 22050
            },

            # German variants
            "de-DE": {
                "espeak_voice": "de",
                "phoneme_set": "de",
                "description": "German (Germany)",
                "supported": True,
                "mfa_language": "german_mfa",
                "sample_rate": 22050
            },
            "de-AT": {
                "espeak_voice": "de-at",
                "phoneme_set": "de-at",
                "description": "German (Austria)",
                "supported": True,
                "mfa_language": "german_at_mfa",
                "sample_rate": 22050
            },
            "de-CH": {
                "espeak_voice": "de-ch",
                "phoneme_set": "de-ch",
                "description": "German (Switzerland)",
                "supported": True,
                "mfa_language": "german_ch_mfa",
                "sample_rate": 22050
            },

            # Portuguese variants
            "pt-BR": {
                "espeak_voice": "pt-br",
                "phoneme_set": "pt-br",
                "description": "Portuguese (Brazil)",
                "supported": True,
                "mfa_language": "portuguese_br_mfa",
                "sample_rate": 22050
            },
            "pt-PT": {
                "espeak_voice": "pt",
                "phoneme_set": "pt",
                "description": "Portuguese (Portugal)",
                "supported": True,
                "mfa_language": "portuguese_pt_mfa",
                "sample_rate": 22050
            },

            # Dutch variants
            "nl-NL": {
                "espeak_voice": "nl",
                "phoneme_set": "nl",
                "description": "Dutch (Netherlands)",
                "supported": True,
                "mfa_language": "dutch_mfa",
                "sample_rate": 22050
            },
            "nl-BE": {
                "espeak_voice": "nl-be",
                "phoneme_set": "nl-be",
                "description": "Dutch (Belgium)",
                "supported": True,
                "mfa_language": "dutch_be_mfa",
                "sample_rate": 22050
            },

            # Nordic languages
            "da-DK": {
                "espeak_voice": "da",
                "phoneme_set": "da",
                "description": "Danish (Denmark)",
                "supported": True,
                "mfa_language": "danish_mfa",
                "sample_rate": 22050
            },
            "nb-NO": {
                "espeak_voice": "no",
                "phoneme_set": "no",
                "description": "Norwegian (Bokmål)",
                "supported": True,
                "mfa_language": "norwegian_mfa",
                "sample_rate": 22050
            },
            "fi-FI": {
                "espeak_voice": "fi",
                "phoneme_set": "fi",
                "description": "Finnish (Finland)",
                "supported": True,
                "mfa_language": "finnish_mfa",
                "sample_rate": 22050
            },

            # Slavic languages
            "ru-RU": {
                "espeak_voice": "ru",
                "phoneme_set": "ru",
                "description": "Russian (Russia)",
                "supported": True,
                "mfa_language": "russian_mfa",
                "sample_rate": 22050
            },
            "pl-PL": {
                "espeak_voice": "pl",
                "phoneme_set": "pl",
                "description": "Polish (Poland)",
                "supported": True,
                "mfa_language": "polish_mfa",
                "sample_rate": 22050
            },
            "cs-CZ": {
                "espeak_voice": "cs",
                "phoneme_set": "cs",
                "description": "Czech (Czech Republic)",
                "supported": True,
                "mfa_language": "czech_mfa",
                "sample_rate": 22050
            },
            "sk-SK": {
                "espeak_voice": "sk",
                "phoneme_set": "sk",
                "description": "Slovak (Slovakia)",
                "supported": True,
                "mfa_language": "slovak_mfa",
                "sample_rate": 22050
            },
            "hr-HR": {
                "espeak_voice": "hr",
                "phoneme_set": "hr",
                "description": "Croatian (Croatia)",
                "supported": True,
                "mfa_language": "croatian_mfa",
                "sample_rate": 22050
            },
            "sl-SI": {
                "espeak_voice": "sl",
                "phoneme_set": "sl",
                "description": "Slovenian (Slovenia)",
                "supported": True,
                "mfa_language": "slovenian_mfa",
                "sample_rate": 22050
            },
            "bg-BG": {
                "espeak_voice": "bg",
                "phoneme_set": "bg",
                "description": "Bulgarian (Bulgaria)",
                "supported": True,
                "mfa_language": "bulgarian_mfa",
                "sample_rate": 22050
            },
            "ro-RO": {
                "espeak_voice": "ro",
                "phoneme_set": "ro",
                "description": "Romanian (Romania)",
                "supported": True,
                "mfa_language": "romanian_mfa",
                "sample_rate": 22050
            },

            # Asian languages
            "ja-JP": {
                "espeak_voice": "ja",
                "phoneme_set": "ja",
                "description": "Japanese (Japan)",
                "supported": True,
                "mfa_language": "japanese_mfa",
                "sample_rate": 22050
            },
            "ko-KR": {
                "espeak_voice": "ko",
                "phoneme_set": "ko",
                "description": "Korean (Korea)",
                "supported": True,
                "mfa_language": "korean_mfa",
                "sample_rate": 22050
            },
            "zh-CN": {
                "espeak_voice": "zh",
                "phoneme_set": "zh",
                "description": "Chinese (Simplified)",
                "supported": True,
                "mfa_language": "chinese_mfa",
                "sample_rate": 22050
            },
            "zh-TW": {
                "espeak_voice": "zh-yue",
                "phoneme_set": "zh-yue",
                "description": "Chinese (Traditional)",
                "supported": True,
                "mfa_language": "chinese_tw_mfa",
                "sample_rate": 22050
            },
            "zh-HK": {
                "espeak_voice": "zh-yue",
                "phoneme_set": "zh-yue",
                "description": "Chinese (Cantonese)",
                "supported": True,
                "mfa_language": "chinese_hk_mfa",
                "sample_rate": 22050
            },
            "th-TH": {
                "espeak_voice": "th",
                "phoneme_set": "th",
                "description": "Thai (Thailand)",
                "supported": True,
                "mfa_language": "thai_mfa",
                "sample_rate": 22050
            },
            "vi-VN": {
                "espeak_voice": "vi",
                "phoneme_set": "vi",
                "description": "Vietnamese (Vietnam)",
                "supported": True,
                "mfa_language": "vietnamese_mfa",
                "sample_rate": 22050
            },

            # Other languages
            "ar-SA": {
                "espeak_voice": "ar",
                "phoneme_set": "ar",
                "description": "Arabic (Saudi Arabia)",
                "supported": True,
                "mfa_language": "arabic_mfa",
                "sample_rate": 22050
            },
            "ar-EG": {
                "espeak_voice": "ar-eg",
                "phoneme_set": "ar-eg",
                "description": "Arabic (Egypt)",
                "supported": True,
                "mfa_language": "arabic_eg_mfa",
                "sample_rate": 22050
            },
            "he-IL": {
                "espeak_voice": "he",
                "phoneme_set": "he",
                "description": "Hebrew (Israel)",
                "supported": True,
                "mfa_language": "hebrew_mfa",
                "sample_rate": 22050
            },
            "hi-IN": {
                "espeak_voice": "hi",
                "phoneme_set": "hi",
                "description": "Hindi (India)",
                "supported": True,
                "mfa_language": "hindi_mfa",
                "sample_rate": 22050
            },
            "tr-TR": {
                "espeak_voice": "tr",
                "phoneme_set": "tr",
                "description": "Turkish (Turkey)",
                "supported": True,
                "mfa_language": "turkish_mfa",
                "sample_rate": 22050
            },
            "el-GR": {
                "espeak_voice": "el",
                "phoneme_set": "el",
                "description": "Greek (Greece)",
                "supported": True,
                "mfa_language": "greek_mfa",
                "sample_rate": 22050
            },
            "hu-HU": {
                "espeak_voice": "hu",
                "phoneme_set": "hu",
                "description": "Hungarian (Hungary)",
                "supported": True,
                "mfa_language": "hungarian_mfa",
                "sample_rate": 22050
            },
            "ca-ES": {
                "espeak_voice": "ca",
                "phoneme_set": "ca",
                "description": "Catalan (Spain)",
                "supported": True,
                "mfa_language": "catalan_mfa",
                "sample_rate": 22050
            },
            "eu-ES": {
                "espeak_voice": "eu",
                "phoneme_set": "eu",
                "description": "Basque (Spain)",
                "supported": True,
                "mfa_language": "basque_mfa",
                "sample_rate": 22050
            },
            "cy-GB": {
                "espeak_voice": "cy",
                "phoneme_set": "cy",
                "description": "Welsh (United Kingdom)",
                "supported": True,
                "mfa_language": "welsh_mfa",
                "sample_rate": 22050
            },
            "sq-AL": {
                "espeak_voice": "sq",
                "phoneme_set": "sq",
                "description": "Albanian (Albania)",
                "supported": True,
                "mfa_language": "albanian_mfa",
                "sample_rate": 22050
            },
            "af-ZA": {
                "espeak_voice": "af",
                "phoneme_set": "af",
                "description": "Afrikaans (South Africa)",
                "supported": True,
                "mfa_language": "afrikaans_mfa",
                "sample_rate": 22050
            },
            "id-ID": {
                "espeak_voice": "id",
                "phoneme_set": "id",
                "description": "Indonesian (Indonesia)",
                "supported": True,
                "mfa_language": "indonesian_mfa",
                "sample_rate": 22050
            },
            "ms-MY": {
                "espeak_voice": "ms",
                "phoneme_set": "ms",
                "description": "Malay (Malaysia)",
                "supported": True,
                "mfa_language": "malay_mfa",
                "sample_rate": 22050
            },
            "sw-KE": {
                "espeak_voice": "sw",
                "phoneme_set": "sw",
                "description": "Swahili (Kenya)",
                "supported": True,
                "mfa_language": "swahili_mfa",
                "sample_rate": 22050
            },
            "ta-IN": {
                "espeak_voice": "ta",
                "phoneme_set": "ta",
                "description": "Tamil (India)",
                "supported": True,
                "mfa_language": "tamil_mfa",
                "sample_rate": 22050
            },
            "te-IN": {
                "espeak_voice": "te",
                "phoneme_set": "te",
                "description": "Telugu (India)",
                "supported": True,
                "mfa_language": "telugu_mfa",
                "sample_rate": 22050
            },
            "ne-NP": {
                "espeak_voice": "ne",
                "phoneme_set": "ne",
                "description": "Nepali (Nepal)",
                "supported": True,
                "mfa_language": "nepali_mfa",
                "sample_rate": 22050
            }
        }

    def _get_espeak_voices(self) -> List[str]:
        """Get list of available eSpeak NG voices"""
        try:
            result = subprocess.run(['espeak-ng', '--voices'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                voices = []
                for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            voices.append(parts[1])  # Voice code
                return voices
            else:
                logger.warning("Could not get eSpeak voices, using fallback list")
                return list(self.language_configs.keys())
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            logger.warning("eSpeak NG not available, using fallback list")
            return list(self.language_configs.keys())

    def get_language_config(self, language_code: str) -> Optional[Dict]:
        """Get configuration for a specific language"""
        return self.language_configs.get(language_code)

    def get_supported_languages(self) -> List[Dict]:
        """Get list of all supported languages"""
        return [
            {
                "code": code,
                "name": config["description"],
                "espeak_voice": config["espeak_voice"],
                "supported": config["supported"],
                "mfa_language": config.get("mfa_language"),
                "sample_rate": config.get("sample_rate", 22050)
            }
            for code, config in self.language_configs.items()
        ]

    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported"""
        config = self.get_language_config(language_code)
        return config is not None and config.get("supported", False)

    def get_espeak_voice(self, language_code: str) -> Optional[str]:
        """Get eSpeak voice for a language"""
        config = self.get_language_config(language_code)
        return config.get("espeak_voice") if config else None

    def get_mfa_language(self, language_code: str) -> Optional[str]:
        """Get MFA language model for a language"""
        config = self.get_language_config(language_code)
        return config.get("mfa_language") if config else None

    def text_to_phonemes(self, text: str, language_code: str) -> Optional[str]:
        """Convert text to phonemes using eSpeak NG"""
        espeak_voice = self.get_espeak_voice(language_code)
        if not espeak_voice:
            logger.error(f"No eSpeak voice found for language: {language_code}")
            return None

        try:
            # Use eSpeak NG to convert text to phonemes
            result = subprocess.run([
                'espeak-ng', '-v', espeak_voice, '-x', '--ipa'
            ], input=text, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                # Clean up the output
                phonemes = result.stdout.strip()
                # Remove any extra whitespace and normalize
                phonemes = re.sub(r'\s+', ' ', phonemes)
                return phonemes
            else:
                logger.error(f"eSpeak NG failed: {result.stderr}")
                return None

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.error(f"Error running eSpeak NG: {e}")
            return None

    def validate_phonemes(self, phonemes: str, language_code: str) -> bool:
        """Validate that phonemes are properly formatted for the language"""
        if not phonemes or not phonemes.strip():
            return False

        # Basic validation - check for common phoneme patterns
        # This is a simplified validation, real validation would be more complex
        valid_patterns = [
            r'[a-zA-Z]',  # Basic letters
            r'[ˈˌ]',      # Stress markers
            r'[ː]',       # Length markers
            r'[ˈˌː]',     # Various IPA markers
        ]

        for pattern in valid_patterns:
            if re.search(pattern, phonemes):
                return True

        return False

    def get_phoneme_set_info(self, language_code: str) -> Dict:
        """Get information about the phoneme set for a language"""
        config = self.get_language_config(language_code)
        if not config:
            return {"error": f"Language {language_code} not supported"}

        espeak_voice = config.get("espeak_voice")
        mfa_language = config.get("mfa_language")

        return {
            "language_code": language_code,
            "language_name": config.get("description"),
            "espeak_voice": espeak_voice,
            "mfa_language": mfa_language,
            "sample_rate": config.get("sample_rate", 22050),
            "supported": config.get("supported", False),
            "phoneme_set_type": "eSpeak NG",
            "alignment_tool": "MFA (Montreal Forced Aligner)" if mfa_language else "Manual"
        }

    def export_language_config(self, output_path: Path) -> bool:
        """Export language configuration to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.language_configs, f, indent=2, ensure_ascii=False)
            logger.info(f"Language configuration exported to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export language configuration: {e}")
            return False

    def import_language_config(self, config_path: Path) -> bool:
        """Import language configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                imported_configs = json.load(f)

            # Validate the imported configuration
            for lang_code, config in imported_configs.items():
                required_fields = ["espeak_voice", "phoneme_set", "description"]
                if not all(field in config for field in required_fields):
                    logger.error(f"Invalid configuration for {lang_code}")
                    return False

            # Update the configuration
            self.language_configs.update(imported_configs)
            logger.info(f"Language configuration imported from {config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to import language configuration: {e}")
            return False

# Global instance
phoneme_manager = PhonemeManager()

def get_phoneme_manager() -> PhonemeManager:
    """Get the global phoneme manager instance"""
    return phoneme_manager

# Convenience functions
def text_to_phonemes(text: str, language_code: str) -> Optional[str]:
    """Convert text to phonemes for a given language"""
    return phoneme_manager.text_to_phonemes(text, language_code)

def is_language_supported(language_code: str) -> bool:
    """Check if a language is supported"""
    return phoneme_manager.is_language_supported(language_code)

def get_supported_languages() -> List[Dict]:
    """Get list of all supported languages"""
    return phoneme_manager.get_supported_languages()

def get_language_config(language_code: str) -> Optional[Dict]:
    """Get configuration for a specific language"""
    return phoneme_manager.get_language_config(language_code)

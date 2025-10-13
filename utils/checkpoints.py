"""
Piper Checkpoint Management System
Handles automatic download, validation, and caching of pre-trained Piper models
"""

import os
import json
import hashlib
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import shutil
from urllib.parse import urlparse
import time

# Optional dependency for checkpoint validation
try:
    import torch  # type: ignore
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CheckpointManager:
    """Manages Piper checkpoint downloads, validation, and caching"""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("checkpoints")
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize checkpoint manifest
        self.checkpoint_manifest = self._load_checkpoint_manifest()

        # Create metadata directory
        self.metadata_dir = self.cache_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)

    def _load_checkpoint_manifest(self) -> Dict:
        """Load the curated checkpoint manifest"""
        return {
            "en-US": {
                "amy": {
                    "name": "Amy",
                    "gender": "Female",
                    "dataset": "LJSpeech",
                    "quality": "High",
                    "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/epoch%3D6679-step%3D1554200.ckpt",
                    "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/config.json",
                    "phoneme_type": "en-us-mfa",
                    "sample_rate": 22050,
                    "speaker_id": 0,
                    "description": "High-quality female voice trained on LJSpeech dataset"
                },
                "lessac": {
                    "name": "Lessac",
                    "gender": "Male",
                    "dataset": "Blizzard 2013",
                    "quality": "Medium",
                    "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/epoch%3D1000-step%3D3493434.ckpt",
                    "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/config.json",
                    "phoneme_type": "en-us-mfa",
                    "sample_rate": 22050,
                    "speaker_id": 0,
                    "description": "Male voice trained on Blizzard 2013 dataset"
                }
            },
            "en-GB": {
                "lessac": {
                    "name": "Lessac",
                    "gender": "Male",
                    "dataset": "Blizzard 2013",
                    "quality": "Medium",
                    "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/lessac/epoch%3D1000-step%3D3493434.ckpt",
                    "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/lessac/config.json",
                    "phoneme_type": "en-gb-mfa",
                    "sample_rate": 22050,
                    "speaker_id": 0,
                    "description": "British English male voice"
                },
                "cori": {
                    "name": "Cori",
                    "gender": "Female",
                    "dataset": "LibriVox",
                    "quality": "High",
                    "url": "https://brycebeattie.com/files/tts/cori-high.ckpt",
                    "config_url": None,  # No config available
                    "phoneme_type": "en-gb-mfa",
                    "sample_rate": 22050,
                    "speaker_id": 0,
                    "description": "High-quality British English female voice"
                }
            },
            "sv-SE": {
                "nst": {
                    "name": "NST (Requires Manual Download)",
                    "gender": "Female",
                    "dataset": "NST Swedish",
                    "quality": "Medium",
                    "url": None,  # Not directly downloadable - requires HuggingFace login
                    "config_url": None,
                    "phoneme_type": "sv-se-mfa",
                    "sample_rate": 22050,
                    "speaker_id": 0,
                    "description": "Swedish female voice from NST dataset",
                    "manual_download_url": "https://huggingface.co/KBLab/piper-tts-nst-swedish",
                    "manual_instructions": "1. Visit https://huggingface.co/KBLab/piper-tts-nst-swedish\n2. Download the .ckpt file\n3. Save to: checkpoints/sv-SE/nst/\n4. Or use Custom Checkpoint Path field"
                },
                "multispeaker": {
                    "name": "SubZeroAI Multi-Speaker",
                    "gender": "Multiple",
                    "dataset": "Swedish Multi-Speaker",
                    "quality": "High",
                    "url": None,
                    "config_url": None,
                    "phoneme_type": "sv-se-mfa",
                    "sample_rate": 22050,
                    "speaker_id": 0,
                    "description": "Swedish multi-speaker TTS model",
                    "manual_download_url": "https://huggingface.co/SubZeroAI/piper-swedish-tts-multispeaker",
                    "manual_instructions": "1. Visit https://huggingface.co/SubZeroAI/piper-swedish-tts-multispeaker\n2. Download the .ckpt file\n3. Save to: checkpoints/sv-SE/multispeaker/\n4. Or use Custom Checkpoint Path field"
                }
            },
            "it-IT": {
                "fallback": {
                    "name": "Fallback",
                    "gender": "Unknown",
                    "dataset": "Unknown",
                    "quality": "Low",
                    "url": None,  # No direct Italian model available
                    "config_url": None,
                    "phoneme_type": "espeak",
                    "sample_rate": 22050,
                    "speaker_id": 0,
                    "description": "Fallback to English model with espeak phonemes",
                    "fallback_to": "en-US.amy"  # Use Amy as fallback
                }
            }
        }

    def get_available_checkpoints(self, language_code: str) -> List[Dict]:
        """Get available checkpoints for a language"""
        if language_code not in self.checkpoint_manifest:
            return []

        checkpoints = []
        for voice_id, config in self.checkpoint_manifest[language_code].items():
            checkpoint_info = {
                "voice_id": voice_id,
                "language_code": language_code,
                "name": config["name"],
                "gender": config["gender"],
                "dataset": config["dataset"],
                "quality": config["quality"],
                "description": config["description"],
                "phoneme_type": config["phoneme_type"],
                "sample_rate": config["sample_rate"],
                "speaker_id": config["speaker_id"],
                "downloaded": self.is_checkpoint_downloaded(language_code, voice_id),
                "file_size": self.get_checkpoint_size(language_code, voice_id),
                "download_url": config["url"]
            }
            checkpoints.append(checkpoint_info)

        return checkpoints

    def get_all_available_checkpoints(self) -> Dict[str, List[Dict]]:
        """Get all available checkpoints across all languages"""
        result = {}
        for language_code in self.checkpoint_manifest.keys():
            result[language_code] = self.get_available_checkpoints(language_code)
        return result

    def is_checkpoint_downloaded(self, language_code: str, voice_id: str) -> bool:
        """Check if a checkpoint is already downloaded"""
        checkpoint_path = self.get_checkpoint_path(language_code, voice_id)
        return checkpoint_path.exists() and checkpoint_path.stat().st_size > 0

    def get_checkpoint_path(self, language_code: str, voice_id: str) -> Path:
        """Get the local path for a checkpoint"""
        return self.cache_dir / f"{language_code}_{voice_id}.ckpt"

    def get_config_path(self, language_code: str, voice_id: str) -> Path:
        """Get the local path for a config file"""
        return self.cache_dir / f"{language_code}_{voice_id}_config.json"

    def get_checkpoint_size(self, language_code: str, voice_id: str) -> Optional[int]:
        """Get the size of a downloaded checkpoint in bytes"""
        checkpoint_path = self.get_checkpoint_path(language_code, voice_id)
        if checkpoint_path.exists():
            return checkpoint_path.stat().st_size
        return None

    def download_checkpoint(self, language_code: str, voice_id: str,
                          progress_callback=None) -> Tuple[bool, str]:
        """Download a checkpoint with progress tracking"""
        if language_code not in self.checkpoint_manifest:
            return False, f"Language {language_code} not supported"

        if voice_id not in self.checkpoint_manifest[language_code]:
            return False, f"Voice {voice_id} not found for language {language_code}"

        config = self.checkpoint_manifest[language_code][voice_id]

        # Handle fallback cases
        if config.get("fallback_to"):
            fallback_lang, fallback_voice = config["fallback_to"].split(".")
            logger.info(f"Using fallback checkpoint: {fallback_lang}.{fallback_voice}")
            return self.download_checkpoint(fallback_lang, fallback_voice, progress_callback)

        if not config["url"]:
            # Check if manual download instructions are available
            if config.get("manual_instructions"):
                manual_msg = f"MANUAL DOWNLOAD REQUIRED:\n\n{config['manual_instructions']}\n\nURL: {config.get('manual_download_url', 'Not provided')}"
                return False, manual_msg
            return False, f"No download URL available for {language_code}.{voice_id}"

        # Check if already downloaded
        if self.is_checkpoint_downloaded(language_code, voice_id):
            logger.info(f"Checkpoint {language_code}.{voice_id} already downloaded")
            return True, "Already downloaded"

        try:
            # Download checkpoint file
            checkpoint_path = self.get_checkpoint_path(language_code, voice_id)
            success, message = self._download_file(
                config["url"], checkpoint_path, progress_callback
            )

            if not success:
                return False, f"Failed to download checkpoint: {message}"

            # Download config file if available
            if config.get("config_url"):
                config_path = self.get_config_path(language_code, voice_id)
                self._download_file(config["config_url"], config_path)

            # Validate the downloaded checkpoint
            if not self.validate_checkpoint(language_code, voice_id):
                logger.warning(f"Checkpoint validation failed for {language_code}.{voice_id}")
                # Don't fail the download, just warn

            # Save metadata
            self._save_checkpoint_metadata(language_code, voice_id, config)

            logger.info(f"Successfully downloaded checkpoint: {language_code}.{voice_id}")
            return True, "Download completed successfully"

        except Exception as e:
            logger.error(f"Error downloading checkpoint {language_code}.{voice_id}: {e}")
            return False, f"Download failed: {str(e)}"

    def _download_file(self, url: str, output_path: Path,
                      progress_callback=None) -> Tuple[bool, str]:
        """Download a file with progress tracking"""
        try:
            logger.info(f"Downloading {url} to {output_path}")

            # Create temporary file for download
            temp_path = output_path.with_suffix('.tmp')

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_callback(progress, downloaded_size, total_size)

            # Move temp file to final location
            shutil.move(str(temp_path), str(output_path))

            logger.info(f"Download completed: {output_path}")
            return True, "Download successful"

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading {url}: {e}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False, f"Download error: {str(e)}"

    def validate_checkpoint(self, language_code: str, voice_id: str) -> bool:
        """Validate a downloaded checkpoint"""
        checkpoint_path = self.get_checkpoint_path(language_code, voice_id)

        if not checkpoint_path.exists():
            return False

        try:
            # Check file size (should be reasonable for a checkpoint)
            file_size = checkpoint_path.stat().st_size
            if file_size < 1024 * 1024:  # Less than 1MB is suspicious
                logger.warning(f"Checkpoint file too small: {file_size} bytes")
                return False

            # Try to load the checkpoint (basic validation)
            if not TORCH_AVAILABLE:
                logger.warning("PyTorch not available, skipping checkpoint validation")
                return True  # Assume valid if we can't validate
            
            try:
                checkpoint = torch.load(checkpoint_path, map_location='cpu')
                if not isinstance(checkpoint, dict):
                    logger.warning("Checkpoint is not a dictionary")
                    return False

                # Check for required keys
                required_keys = ['state_dict', 'hyper_parameters']
                for key in required_keys:
                    if key not in checkpoint:
                        logger.warning(f"Missing required key in checkpoint: {key}")
                        return False

                logger.info(f"Checkpoint validation passed: {language_code}.{voice_id}")
                return True

            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
                return False

        except Exception as e:
            logger.error(f"Error validating checkpoint: {e}")
            return False

    def _save_checkpoint_metadata(self, language_code: str, voice_id: str, config: Dict):
        """Save metadata for a downloaded checkpoint"""
        metadata = {
            "language_code": language_code,
            "voice_id": voice_id,
            "downloaded_at": time.time(),
            "config": config,
            "file_path": str(self.get_checkpoint_path(language_code, voice_id)),
            "config_path": str(self.get_config_path(language_code, voice_id)) if config.get("config_url") else None
        }

        metadata_file = self.metadata_dir / f"{language_code}_{voice_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def get_checkpoint_metadata(self, language_code: str, voice_id: str) -> Optional[Dict]:
        """Get metadata for a downloaded checkpoint"""
        metadata_file = self.metadata_dir / f"{language_code}_{voice_id}_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading metadata: {e}")
        return None

    def delete_checkpoint(self, language_code: str, voice_id: str) -> bool:
        """Delete a downloaded checkpoint"""
        try:
            checkpoint_path = self.get_checkpoint_path(language_code, voice_id)
            config_path = self.get_config_path(language_code, voice_id)
            metadata_file = self.metadata_dir / f"{language_code}_{voice_id}_metadata.json"

            # Delete files
            if checkpoint_path.exists():
                checkpoint_path.unlink()
            if config_path.exists():
                config_path.unlink()
            if metadata_file.exists():
                metadata_file.unlink()

            logger.info(f"Deleted checkpoint: {language_code}.{voice_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting checkpoint: {e}")
            return False

    def get_cache_info(self) -> Dict:
        """Get information about the checkpoint cache"""
        total_size = 0
        checkpoint_count = 0

        for file_path in self.cache_dir.glob("*.ckpt"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                checkpoint_count += 1

        return {
            "cache_dir": str(self.cache_dir),
            "checkpoint_count": checkpoint_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "available_languages": list(self.checkpoint_manifest.keys())
        }

    def clear_cache(self) -> bool:
        """Clear all downloaded checkpoints"""
        try:
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()

            logger.info("Checkpoint cache cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_recommended_checkpoint(self, language_code: str, gender_preference: str = None) -> Optional[Dict]:
        """Get the recommended checkpoint for a language"""
        checkpoints = self.get_available_checkpoints(language_code)

        if not checkpoints:
            return None

        # Filter by gender preference if specified
        if gender_preference:
            gender_checkpoints = [cp for cp in checkpoints if cp["gender"].lower() == gender_preference.lower()]
            if gender_checkpoints:
                checkpoints = gender_checkpoints

        # Prefer high quality checkpoints
        high_quality = [cp for cp in checkpoints if cp["quality"].lower() == "high"]
        if high_quality:
            return high_quality[0]

        # Fall back to first available
        return checkpoints[0]

# Global instance
checkpoint_manager = CheckpointManager()

def get_checkpoint_manager() -> CheckpointManager:
    """Get the global checkpoint manager instance"""
    return checkpoint_manager

# Convenience functions
def download_checkpoint(language_code: str, voice_id: str, progress_callback=None) -> Tuple[bool, str]:
    """Download a checkpoint"""
    return checkpoint_manager.download_checkpoint(language_code, voice_id, progress_callback)

def get_available_checkpoints(language_code: str) -> List[Dict]:
    """Get available checkpoints for a language"""
    return checkpoint_manager.get_available_checkpoints(language_code)

def is_checkpoint_downloaded(language_code: str, voice_id: str) -> bool:
    """Check if a checkpoint is downloaded"""
    return checkpoint_manager.is_checkpoint_downloaded(language_code, voice_id)

def get_checkpoint_path(language_code: str, voice_id: str) -> Path:
    """Get the path to a downloaded checkpoint"""
    return checkpoint_manager.get_checkpoint_path(language_code, voice_id)

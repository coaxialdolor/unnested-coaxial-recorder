#!/usr/bin/env python3
"""
Coaxial Recorder Training Script
Trains Piper TTS models from recorded voice data
"""

import argparse
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.phonemes import get_phoneme_manager, is_language_supported
from utils.mfa import get_mfa_aligner, is_mfa_available
from utils.checkpoints import get_checkpoint_manager, download_checkpoint, get_available_checkpoints
from utils.vits_training import train_tts_model

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('training.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []

    try:
        import torch
        logging.info(f"PyTorch version: {torch.__version__}")

        # Try to import GPU compatibility utilities
        try:
            from utils.gpu_compat import check_gpu_compatibility

            # Check GPU compatibility
            gpu_status = check_gpu_compatibility()
            if gpu_status['cuda_available']:
                logging.info(f"CUDA available: {gpu_status['device_count']} device(s)")
                for device in gpu_status['devices']:
                    logging.info(f"  - {device['name']} (Compute Capability: {device['compute_capability']})")

                if not gpu_status['compatible']:
                    logging.warning("GPU compatibility issue detected!")
                    for warning in gpu_status['warnings']:
                        logging.warning(f"  {warning}")
                    if gpu_status['recommended_action']:
                        logging.warning(f"  Recommended: {gpu_status['recommended_action']}")
                else:
                    logging.info("GPU is compatible and ready for training")
            else:
                logging.info("CUDA not available, using CPU")
                if gpu_status['warnings']:
                    for warning in gpu_status['warnings']:
                        logging.warning(warning)
        except ImportError:
            # Fallback if gpu_compat module not available
            if torch.cuda.is_available():
                logging.info(f"CUDA available: {torch.cuda.device_count()} device(s)")
            else:
                logging.info("CUDA not available, using CPU")
    except ImportError:
        missing_deps.append("torch")

    try:
        import torchaudio
        logging.info(f"TorchAudio version: {torchaudio.__version__}")
    except ImportError:
        missing_deps.append("torchaudio")

    # Check phoneme system
    phoneme_manager = get_phoneme_manager()
    logging.info(f"Phoneme system: {len(phoneme_manager.get_supported_languages())} languages supported")

    # Check MFA availability
    mfa_available = is_mfa_available()
    logging.info(f"MFA (Montreal Forced Aligner): {'Available' if mfa_available else 'Not available'}")

    # Check checkpoint system
    checkpoint_manager = get_checkpoint_manager()
    cache_info = checkpoint_manager.get_cache_info()
    logging.info(f"Checkpoint system: {cache_info['checkpoint_count']} checkpoints cached, {cache_info['total_size_mb']} MB")

    if missing_deps:
        logging.error(f"Missing dependencies: {', '.join(missing_deps)}")
        logging.error("Please install training dependencies: pip install -r requirements_training.txt")
        return False

    return True

def prepare_dataset(profile_id: str, prompt_list_id: str, output_dir: str, language_code: str = "en-US", audio_source: str = "original") -> Dict:
    """Prepare dataset for training with phoneme and MFA support"""
    logging.info(f"Preparing dataset for profile: {profile_id}, prompt list: {prompt_list_id}, language: {language_code}, audio_source: {audio_source}")

    # Initialize phoneme and MFA systems
    phoneme_manager = get_phoneme_manager()
    mfa_aligner = get_mfa_aligner()

    # Check language support
    if not is_language_supported(language_code):
        logging.error(f"Language {language_code} is not supported")
        return {"error": f"Language {language_code} not supported"}

    # Get language configuration
    lang_config = phoneme_manager.get_language_config(language_code)
    logging.info(f"Language config: {lang_config['description']}")

    dataset_info = {
        "profile_id": profile_id,
        "prompt_list_id": prompt_list_id,
        "output_dir": output_dir,
        "language_code": language_code,
        "audio_source": audio_source,
        "audio_files": [],
        "transcripts": [],
        "phonemes": [],
        "train_files": [],
        "val_files": [],
        "mfa_aligned": False,
        "espeak_voice": lang_config.get("espeak_voice"),
        "mfa_language": lang_config.get("mfa_language")
    }

    # Determine which directory to use based on audio_source
    base_recordings_dir = Path("voices") / profile_id / "recordings"
    if audio_source == "preprocessed":
        recordings_dir = base_recordings_dir / "preprocessed"
        logging.info(f"Using preprocessed audio from: {recordings_dir}")
    else:
        recordings_dir = base_recordings_dir
        logging.info(f"Using original audio from: {recordings_dir}")
    
    if not recordings_dir.exists():
        logging.error(f"Recordings directory not found: {recordings_dir}")
        return dataset_info

    # Find audio files
    audio_files = list(recordings_dir.glob("*.wav"))
    logging.info(f"Found {len(audio_files)} audio files")

    # Load metadata and prepare transcripts
    metadata_file = Path("voices") / profile_id / "metadata.jsonl"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        metadata = json.loads(line.strip())
                        if metadata.get("prompt_list") == prompt_list_id:
                            dataset_info["transcripts"].append(metadata)

                            # Convert text to phonemes
                            text = metadata.get("text", "")
                            if text:
                                phonemes = phoneme_manager.text_to_phonemes(text, language_code)
                                if phonemes:
                                    dataset_info["phonemes"].append({
                                        "text": text,
                                        "phonemes": phonemes,
                                        "file_id": metadata.get("file_id")
                                    })
                                else:
                                    logging.warning(f"Failed to convert text to phonemes: {text}")
                    except json.JSONDecodeError:
                        continue

    logging.info(f"Found {len(dataset_info['transcripts'])} transcript entries")
    logging.info(f"Generated {len(dataset_info['phonemes'])} phoneme sequences")

    # Prepare MFA alignment if available
    if is_mfa_available() and lang_config.get("mfa_language"):
        logging.info("MFA available, preparing alignment...")

        # Create temporary directories for MFA
        temp_dir = Path(output_dir) / "temp_mfa"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Prepare text files for MFA
        text_dir = temp_dir / "text"
        text_dir.mkdir(exist_ok=True)

        for transcript in dataset_info["transcripts"]:
            text_file = text_dir / f"{transcript['file_id']}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(transcript.get("text", ""))

        # Run MFA alignment
        alignment_dir = temp_dir / "alignment"
        if mfa_aligner.align_audio_text(recordings_dir, text_dir, alignment_dir, language_code):
            logging.info("MFA alignment completed successfully")
            dataset_info["mfa_aligned"] = True

            # Validate alignment
            validation = mfa_aligner.validate_alignment(alignment_dir)
            if validation["valid"]:
                logging.info(f"Alignment validation passed: {validation['aligned_files']} files aligned")
            else:
                logging.warning(f"Alignment validation issues: {validation['warnings']}")
        else:
            logging.warning("MFA alignment failed, proceeding without alignment")
    else:
        logging.info("MFA not available or language not supported, skipping alignment")

    return dataset_info

def train_model(args):
    """Main training function"""
    setup_logging()

    logging.info("Starting model training...")
    logging.info(f"Arguments: {args}")

    # Check dependencies
    if not check_dependencies():
        return False

    # Handle checkpoint selection and download
    checkpoint_path = None
    if args.checkpoint:
        # Use provided checkpoint path
        checkpoint_path = Path(args.checkpoint)
        if not checkpoint_path.exists():
            logging.error(f"Checkpoint file not found: {checkpoint_path}")
            return False
        logging.info(f"Using provided checkpoint: {checkpoint_path}")
    elif args.base_voice:
        # Download and use base voice checkpoint
        checkpoint_manager = get_checkpoint_manager()

        # Parse base voice (format: language_code.voice_id)
        if '.' in args.base_voice:
            language_code, voice_id = args.base_voice.split('.', 1)
        else:
            # Use language from args and voice from base_voice
            language_code = args.language_code
            voice_id = args.base_voice

        logging.info(f"Using base voice: {language_code}.{voice_id}")

        # Check if checkpoint is available
        available_checkpoints = checkpoint_manager.get_available_checkpoints(language_code)
        checkpoint_info = None

        for cp in available_checkpoints:
            if cp["voice_id"] == voice_id:
                checkpoint_info = cp
                break

        if not checkpoint_info:
            logging.error(f"Base voice {language_code}.{voice_id} not available")
            logging.info(f"Available voices for {language_code}: {[cp['voice_id'] for cp in available_checkpoints]}")
            return False

        # Download checkpoint if not already downloaded
        if not checkpoint_manager.is_checkpoint_downloaded(language_code, voice_id):
            logging.info(f"Downloading checkpoint: {language_code}.{voice_id}")
            success, message = checkpoint_manager.download_checkpoint(language_code, voice_id)
            if not success:
                logging.error(f"Failed to download checkpoint: {message}")
                return False
            logging.info("Checkpoint downloaded successfully")

        checkpoint_path = checkpoint_manager.get_checkpoint_path(language_code, voice_id)
        logging.info(f"Using downloaded checkpoint: {checkpoint_path}")
    else:
        logging.info("Training from scratch (no base checkpoint)")

    # Prepare dataset
    dataset_info = prepare_dataset(
        args.profile_id,
        args.prompt_list_id,
        args.output_dir,
        args.language_code
    )

    if not dataset_info["audio_files"] and not dataset_info["transcripts"]:
        logging.error("No training data found!")
        return False

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Prepare training configuration
    training_config = {
        'learning_rate': args.learning_rate,
        'batch_size': args.batch_size,
        'epochs': args.epochs,
        'save_interval': args.save_interval,
        'early_stopping': args.early_stopping,
        'mixed_precision': args.mixed_precision,
        'sample_rate': 22050,
        'hidden_dim': 256 if args.model_size == 'small' else 512 if args.model_size == 'medium' else 1024
    }

    # Determine if MFA should be used
    use_mfa = dataset_info.get("mfa_aligned", False) and args.use_mfa

    # Train the model
    logging.info("Starting ACTUAL TTS model training...")
    logging.info(f"Training mode: {'MFA-aligned' if use_mfa else 'Basic (phoneme-only)'}")
    logging.info(f"GPU acceleration: {'enabled' if args.use_gpu else 'disabled'}")
    logging.info(f"Mixed precision: {'enabled' if args.mixed_precision else 'disabled'}")

    try:
        success, message = train_tts_model(
            dataset_info=dataset_info,
            output_dir=args.output_dir,
            config=training_config,
            use_mfa=use_mfa,
            checkpoint_path=checkpoint_path if checkpoint_path else None
        )

        if success:
            logging.info("Training completed successfully!")
            logging.info(message)
            return True
        else:
            logging.error(f"Training failed: {message}")
            return False

    except Exception as e:
        logging.error(f"Training failed: {e}", exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description="Train Piper TTS model")

    # Dataset arguments
    parser.add_argument("--profile-id", required=True, help="Voice profile ID")
    parser.add_argument("--prompt-list-id", required=True, help="Prompt list ID")
    parser.add_argument("--language-code", default="en-US", help="Language code (e.g., en-US, sv-SE, it-IT)")

    # Model arguments
    parser.add_argument("--model-size", choices=["small", "medium", "large"], default="medium")
    parser.add_argument("--learning-rate", type=float, default=0.0001)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--train-split", type=float, default=0.85)
    parser.add_argument("--validation-split", type=float, default=0.15)
    parser.add_argument("--save-interval", type=int, default=10)
    parser.add_argument("--early-stopping", type=int, default=20)

    # Training options
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU acceleration")
    parser.add_argument("--mixed-precision", action="store_true", help="Use mixed precision training")
    parser.add_argument("--use-mfa", action="store_true", default=True, help="Use MFA alignment if available (default: True)")
    parser.add_argument("--checkpoint", help="Path to checkpoint for fine-tuning")
    parser.add_argument("--base-voice", help="Base voice to use for fine-tuning (format: language_code.voice_id, e.g., en-US.amy)")

    # Output arguments
    parser.add_argument("--output-dir", default="./models", help="Output directory")
    parser.add_argument("--model-name", help="Model name")

    args = parser.parse_args()

    success = train_model(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

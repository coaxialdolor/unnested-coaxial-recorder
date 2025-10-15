"""
VITS Training Implementation for Piper TTS
Based on VITS architecture with PyTorch Lightning
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import torchaudio

try:
    import lightning as L
    from lightning.pytorch import Trainer
    from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping
    from lightning.pytorch.loggers import TensorBoardLogger
    LIGHTNING_AVAILABLE = True
except ImportError:
    try:
        import pytorch_lightning as L
        from pytorch_lightning import Trainer
        from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
        from pytorch_lightning.loggers import TensorBoardLogger
        LIGHTNING_AVAILABLE = True
    except ImportError:
        LIGHTNING_AVAILABLE = False
        L = None
        Trainer = None
        ModelCheckpoint = None
        EarlyStopping = None
        TensorBoardLogger = None

# Apply runtime GPU optimizations (RTX 5060 Ti compatibility)
if LIGHTNING_AVAILABLE:
    logger = logging.getLogger(__name__)

    try:
        import torch
        if torch.cuda.is_available():
            # RTX 5060 Ti optimizations based on Copilot recommendations
            torch.backends.cudnn.benchmark = True  # Auto-tune kernels
            torch.backends.cuda.matmul.allow_tf32 = True  # Use TF32 on Ampere+

            # Check for modern GPU (compute capability 8.0+)
            if hasattr(torch.cuda, 'get_device_capability'):
                cap = torch.cuda.get_device_capability(0)
                if cap[0] >= 8:  # Ampere or newer (RTX 30/40/50 series)
                    torch.set_float32_matmul_precision('high')
                    logger.info(f"GPU optimizations enabled for compute capability {cap[0]}.{cap[1]}")
    except Exception as e:
        logger.warning(f"Could not apply GPU optimizations: {e}")


class VoiceDataset(Dataset):
    """Dataset for TTS training"""

    def __init__(self, audio_files: List[Path], transcripts: List[str], phonemes: List[str],
                 sample_rate: int = 22050, max_wav_value: float = 32768.0):
        self.audio_files = audio_files
        self.transcripts = transcripts
        self.phonemes = phonemes
        self.sample_rate = sample_rate
        self.max_wav_value = max_wav_value

    def __len__(self):
        return len(self.audio_files)

    def __getitem__(self, idx):
        # Load audio
        audio_path = self.audio_files[idx]
        # Convert Path to string if needed
        if isinstance(audio_path, Path):
            audio_path = str(audio_path)
        
        # Use soundfile directly (torchaudio.load has issues with PyTorch nightly)
        import soundfile as sf
        waveform, sr = sf.read(audio_path)
        waveform = torch.from_numpy(waveform).float()
        if len(waveform.shape) == 1:
            waveform = waveform.unsqueeze(0)
        else:
            waveform = waveform.T

        # Resample if needed
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Normalize
        waveform = waveform / self.max_wav_value

        # Get phoneme sequence (convert to indices)
        # If phonemes list is empty (no MFA), use empty sequence
        if self.phonemes and idx < len(self.phonemes):
            phoneme_seq = self.phonemes[idx]
        else:
            phoneme_seq = ""

        return {
            'audio': waveform.squeeze(0),
            'audio_len': waveform.shape[1],
            'phonemes': phoneme_seq,
            'transcript': self.transcripts[idx]
        }


class SimpleTTSModel(L.LightningModule if LIGHTNING_AVAILABLE else nn.Module):
    """Simplified TTS model for training

    This is a basic implementation. For production, integrate full VITS model.
    """

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.learning_rate = config.get('learning_rate', 0.0001)

        # Simple encoder-decoder architecture (placeholder for full VITS)
        hidden_dim = config.get('hidden_dim', 256)
        self.encoder = nn.LSTM(
            input_size=80,  # Mel spectrogram features
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )

        self.decoder = nn.LSTM(
            input_size=hidden_dim * 2,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True
        )

        self.output_proj = nn.Linear(hidden_dim, 80)

    def forward(self, x):
        # Encode
        encoded, _ = self.encoder(x)
        # Decode
        decoded, _ = self.decoder(encoded)
        # Project
        output = self.output_proj(decoded)
        return output

    def training_step(self, batch, batch_idx):
        # Extract mel spectrogram from audio
        mel_spec = self._audio_to_mel(batch['audio'])

        # Forward pass
        output = self(mel_spec)

        # Loss (simplified - use actual vocoder loss in production)
        loss = F.mse_loss(output, mel_spec)

        # Log
        self.log('train_loss', loss, prog_bar=True)

        return loss

    def validation_step(self, batch, batch_idx):
        mel_spec = self._audio_to_mel(batch['audio'])
        output = self(mel_spec)
        loss = F.mse_loss(output, mel_spec)

        self.log('val_loss', loss, prog_bar=True)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5
        )
        return {
            'optimizer': optimizer,
            'lr_scheduler': {
                'scheduler': scheduler,
                'monitor': 'train_loss'
            }
        }

    def _audio_to_mel(self, audio):
        """Convert audio to mel spectrogram"""
        mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.config.get('sample_rate', 22050),
            n_fft=1024,
            hop_length=256,
            n_mels=80
        ).to(audio.device)  # Move transform to same device as audio

        if audio.dim() == 1:
            audio = audio.unsqueeze(0)

        mel = mel_transform(audio)
        mel = torch.log(torch.clamp(mel, min=1e-5))

        return mel.transpose(1, 2)  # (batch, time, features)


def train_tts_model(
    dataset_info: Dict,
    output_dir: str,
    config: Dict,
    use_mfa: bool = False,
    checkpoint_path: Optional[str] = None,
    progress_callback=None
) -> Tuple[bool, str]:
    """Train TTS model with PyTorch Lightning

    Args:
        dataset_info: Dataset information including audio files, transcripts, phonemes
        output_dir: Directory to save checkpoints and logs
        config: Training configuration
        use_mfa: Whether to use MFA alignment (if available)
        checkpoint_path: Optional checkpoint to resume from
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (success, message)
    """

    if not LIGHTNING_AVAILABLE:
        return False, "PyTorch Lightning not installed. Run: pip install lightning"

    try:
        # Create output directories
        output_path = Path(output_dir)
        checkpoint_dir = output_path / "checkpoints"
        log_dir = output_path / "logs"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Prepare dataset
        audio_files = [Path(f) for f in dataset_info.get('audio_files', [])]
        transcripts = [t.get('text', '') for t in dataset_info.get('transcripts', [])]
        phonemes = [p.get('phonemes', '') for p in dataset_info.get('phonemes', [])]

        if not audio_files:
            return False, "No audio files found in dataset"

        logger.info(f"Training with {len(audio_files)} audio files")
        logger.info(f"MFA alignment: {'enabled' if use_mfa else 'disabled'}")

        # Create datasets
        train_dataset = VoiceDataset(
            audio_files=audio_files,
            transcripts=transcripts,
            phonemes=phonemes,
            sample_rate=config.get('sample_rate', 22050)
        )

        # Data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=config.get('batch_size', 16),
            shuffle=True,
            num_workers=0,  # Disable multiprocessing to avoid torchaudio crashes
            collate_fn=collate_fn
        )

        # Initialize model
        model_config = {
            'learning_rate': config.get('learning_rate', 0.0001),
            'hidden_dim': config.get('hidden_dim', 256),
            'sample_rate': config.get('sample_rate', 22050),
            'use_mfa': use_mfa
        }

        model = SimpleTTSModel(model_config)

        # Load from checkpoint if provided
        if checkpoint_path and Path(checkpoint_path).exists():
            logger.info(f"Loading checkpoint: {checkpoint_path}")
            checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
            model.load_state_dict(checkpoint['state_dict'], strict=False)

        # Callbacks
        checkpoint_callback = ModelCheckpoint(
            dirpath=checkpoint_dir,
            filename='checkpoint-{epoch:04d}-{val_loss:.4f}',
            save_top_k=3,
            monitor='val_loss',
            mode='min',
            save_last=True,
            every_n_epochs=config.get('save_interval', 10)
        )

        early_stop_callback = EarlyStopping(
            monitor='train_loss',
            patience=config.get('early_stopping', 20),
            mode='min'
        )

        # Logger
        tb_logger = TensorBoardLogger(
            save_dir=log_dir,
            name='tts_training'
        )

        # Trainer configuration (RTX 5060 Ti optimized)
        trainer_kwargs = {
            'max_epochs': config.get('epochs', 100),
            'callbacks': [checkpoint_callback, early_stop_callback],
            'logger': tb_logger,
            'gradient_clip_val': 1.0,
            'log_every_n_steps': 10,
            'enable_progress_bar': True,
            'enable_model_summary': True
        }

        # GPU configuration (CUDA, MPS, or CPU)
        if torch.cuda.is_available():
            trainer_kwargs['accelerator'] = 'gpu'
            trainer_kwargs['devices'] = 1  # Single GPU

            # Precision: use 16 for modern GPUs (Ampere+)
            if config.get('mixed_precision', False):
                if hasattr(torch.cuda, 'get_device_capability'):
                    cap = torch.cuda.get_device_capability(0)
                    if cap[0] >= 8:  # Ampere or newer
                        trainer_kwargs['precision'] = '16-mixed'  # Modern syntax
                    else:
                        trainer_kwargs['precision'] = 16
                else:
                    trainer_kwargs['precision'] = 16
            else:
                trainer_kwargs['precision'] = 32
        elif torch.backends.mps.is_available():
            # Apple Silicon GPU (M1/M2/M3)
            trainer_kwargs['accelerator'] = 'mps'
            trainer_kwargs['precision'] = 32  # MPS doesn't support mixed precision yet
            logger.info("Using Apple Silicon GPU (MPS)")
        else:
            trainer_kwargs['accelerator'] = 'cpu'
            trainer_kwargs['precision'] = 32

        trainer = Trainer(**trainer_kwargs)

        # Train
        logger.info("Starting training...")
        trainer.fit(model, train_loader)

        # Save final model
        final_model_path = checkpoint_dir / "final_model.ckpt"
        trainer.save_checkpoint(final_model_path)

        logger.info(f"Training completed! Model saved to: {final_model_path}")

        return True, f"Training completed successfully. Model saved to {final_model_path}"

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return False, f"Training failed: {str(e)}"


def collate_fn(batch):
    """Collate function for data loader"""
    # Simple collation - pad sequences to same length
    max_audio_len = max([item['audio_len'] for item in batch])

    audios = []
    phonemes = []
    transcripts = []

    for item in batch:
        audio = item['audio']
        if len(audio) < max_audio_len:
            audio = F.pad(audio, (0, max_audio_len - len(audio)))
        audios.append(audio)
        phonemes.append(item['phonemes'])
        transcripts.append(item['transcript'])

    return {
        'audio': torch.stack(audios),
        'phonemes': phonemes,
        'transcript': transcripts
    }


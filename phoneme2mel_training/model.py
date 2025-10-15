import logging
from typing import Dict, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import lightning as L
    LIGHTNING_AVAILABLE = True
except ImportError:
    try:
        import pytorch_lightning as L  # type: ignore
        LIGHTNING_AVAILABLE = True
    except ImportError:  # pragma: no cover
        LIGHTNING_AVAILABLE = False
        L = None  # type: ignore


class PhonemeToMelModel(L.LightningModule if LIGHTNING_AVAILABLE else nn.Module):
    """Phoneme-to-mel baseline model with Transformer encoder.

    Expects integer token IDs as input with shape (batch, time).
    Produces mel-spectrogram frames with shape (batch, time, n_mels).
    """

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        # Ensure hyperparameters (including model_type) are stored in checkpoints
        if LIGHTNING_AVAILABLE:
            try:
                # save_hyperparameters stores a copy under 'hyper_parameters' in .ckpt
                self.save_hyperparameters(config)
            except Exception:
                pass

        # Optimization / training params
        self.learning_rate: float = float(config.get("learning_rate", 1e-4))

        # Audio / mel params
        self.n_mels: int = int(config.get("n_mels", 80))
        self.sample_rate: int = int(config.get("sample_rate", 22050))

        # Text encoder params
        self.vocab_size: int = int(config.get("vocab_size", 256))
        self.unk_id: int = int(config.get("unk_id", 92))
        self.embed_dim: int = int(config.get("embed_dim", 256))
        self.nhead: int = int(config.get("nhead", 4))
        self.num_layers: int = int(config.get("num_layers", 4))
        self.dropout: float = float(config.get("dropout", 0.1))

        self.embedding = nn.Embedding(self.vocab_size, self.embed_dim, padding_idx=self.unk_id)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.embed_dim,
            nhead=self.nhead,
            dropout=self.dropout,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=self.num_layers)
        self.output_proj = nn.Linear(self.embed_dim, self.n_mels)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            token_ids: Tensor of shape (batch, time) with dtype long

        Returns:
            Tensor of shape (batch, time, n_mels)
        """
        x = self.embedding(token_ids)  # (B, T, E)
        x = self.encoder(x)            # (B, T, E)
        mel = self.output_proj(x)      # (B, T, n_mels)
        return mel

    # --- Lightning only below ---
    def _audio_to_mel(self, audio: torch.Tensor) -> torch.Tensor:
        """Convert mono audio (B, T) to log-mel (B, T', n_mels)."""
        import torchaudio

        mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate,
            n_fft=int(self.config.get("n_fft", 1024)),
            hop_length=int(self.config.get("hop_length", 256)),
            n_mels=self.n_mels,
        ).to(audio.device)

        if audio.dim() == 1:
            audio = audio.unsqueeze(0)

        mel = mel_transform(audio)
        mel = torch.log(torch.clamp(mel, min=1e-5))
        return mel.transpose(1, 2)  # (B, T, n_mels)

    def training_step(self, batch: Dict, batch_idx: int):  # type: ignore[override]
        tokens: torch.Tensor = batch["phoneme_ids"]
        pred_mel = self(tokens)

        tgt_mel = self._audio_to_mel(batch["audio"])  # (B, T_audio, n_mels)
        min_len = min(pred_mel.shape[1], tgt_mel.shape[1])
        pred_mel = pred_mel[:, :min_len, :]
        tgt_mel = tgt_mel[:, :min_len, :]

        loss = F.mse_loss(pred_mel, tgt_mel)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def validation_step(self, batch: Dict, batch_idx: int):  # type: ignore[override]
        tokens: torch.Tensor = batch["phoneme_ids"]
        pred_mel = self(tokens)
        tgt_mel = self._audio_to_mel(batch["audio"])  # (B, T_audio, n_mels)
        min_len = min(pred_mel.shape[1], tgt_mel.shape[1])
        pred_mel = pred_mel[:, :min_len, :]
        tgt_mel = tgt_mel[:, :min_len, :]
        loss = F.mse_loss(pred_mel, tgt_mel)
        self.log("val_loss", loss, prog_bar=True)
        return loss

    def configure_optimizers(self):  # type: ignore[override]
        optimizer = torch.optim.Adam(self.parameters(), lr=self.learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=5
        )
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "monitor": "train_loss",
            },
        }



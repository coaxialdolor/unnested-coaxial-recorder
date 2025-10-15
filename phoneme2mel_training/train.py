import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

import torch

try:
    import lightning as L
    from lightning.pytorch import Trainer
    from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping
    from lightning.pytorch.loggers import TensorBoardLogger
    LIGHTNING_AVAILABLE = True
except ImportError:
    import pytorch_lightning as L  # type: ignore
    from pytorch_lightning import Trainer  # type: ignore
    from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping  # type: ignore
    from pytorch_lightning.loggers import TensorBoardLogger  # type: ignore
    LIGHTNING_AVAILABLE = True

from torch.utils.data import DataLoader

from .model import PhonemeToMelModel
from .dataset import MultilingualVoiceDataset
from .collate import collate_fn


def load_config(config_path: str) -> Dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Train phoneme-to-mel model")
    parser.add_argument("--config", required=True, help="Path to config.json")
    parser.add_argument("--output_dir", required=True, help="Output directory for checkpoints and logs")
    args = parser.parse_args()

    config = load_config(args.config)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("phoneme2mel")

    output_path = Path(args.output_dir)
    ckpt_dir = output_path / "checkpoints"
    log_dir = output_path / "logs"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Dataset inputs
    audio_files: List[str] = config.get("audio_files", [])
    phoneme_sequences: List[str] = config.get("phoneme_sequences", [])
    transcripts: List[str] = config.get("transcripts", [])
    phoneme_map_path: str = config["phoneme_map_path"]

    if not audio_files:
        raise ValueError("config.audio_files is empty")
    if not phoneme_sequences:
        raise ValueError("config.phoneme_sequences is empty")

    dataset = MultilingualVoiceDataset(
        audio_files=audio_files,
        phoneme_sequences=phoneme_sequences,
        transcripts=transcripts,
        sample_rate=int(config.get("sample_rate", 22050)),
        phoneme_map_path=phoneme_map_path,
    )

    train_loader = DataLoader(
        dataset,
        batch_size=int(config.get("batch_size", 16)),
        shuffle=True,
        num_workers=int(config.get("num_workers", 0)),
        collate_fn=collate_fn,
    )

    # Model
    model = PhonemeToMelModel(config)

    # Callbacks & logger
    checkpoint_callback = ModelCheckpoint(
        dirpath=ckpt_dir,
        filename="checkpoint-{epoch:04d}-{val_loss:.4f}",
        save_top_k=3,
        monitor="val_loss",
        mode="min",
        save_last=True,
        every_n_epochs=int(config.get("save_interval", 10)),
    )

    early_stop_callback = EarlyStopping(
        monitor="train_loss",
        patience=int(config.get("early_stopping", 20)),
        mode="min",
    )

    tb_logger = TensorBoardLogger(save_dir=log_dir, name="tts_training")

    trainer_kwargs = {
        "max_epochs": int(config.get("epochs", 100)),
        "callbacks": [checkpoint_callback, early_stop_callback],
        "logger": tb_logger,
        "gradient_clip_val": 1.0,
        "log_every_n_steps": 10,
        "enable_progress_bar": True,
        "enable_model_summary": True,
    }

    if torch.cuda.is_available():
        trainer_kwargs["accelerator"] = "gpu"
        trainer_kwargs["devices"] = 1
        if bool(config.get("mixed_precision", True)):
            trainer_kwargs["precision"] = "16-mixed"
        else:
            trainer_kwargs["precision"] = 32
    else:
        trainer_kwargs["accelerator"] = "cpu"
        trainer_kwargs["precision"] = 32

    trainer = Trainer(**trainer_kwargs)
    logger.info("Starting training...")
    # For simplicity, use the same dataset as both train and val here; users can split externally
    trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=train_loader)

    final_model_path = ckpt_dir / "final_model.ckpt"
    trainer.save_checkpoint(final_model_path)
    logger.info(f"Training completed. Model saved to: {final_model_path}")


if __name__ == "__main__":
    main()



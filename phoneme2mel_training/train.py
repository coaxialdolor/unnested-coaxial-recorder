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

    # Validate required keys and phoneme map
    if "phoneme_map_path" not in config:
        raise ValueError("Missing 'phoneme_map_path' in config")
    phoneme_map_path = Path(config["phoneme_map_path"]) 
    if not phoneme_map_path.exists():
        raise FileNotFoundError(f"phoneme_map_path not found: {phoneme_map_path}")
    with open(phoneme_map_path, "r", encoding="utf-8") as f:
        phoneme_map = json.load(f)
    if "UNK" not in phoneme_map:
        raise ValueError("phoneme_map.json must include 'UNK' entry")
    unk_id = int(config.get("unk_id", phoneme_map.get("UNK")))
    if unk_id != phoneme_map.get("UNK"):
        # ensure consistency
        unk_id = phoneme_map.get("UNK")
        config["unk_id"] = unk_id
    vocab_size = int(config.get("vocab_size", len(phoneme_map)))
    if vocab_size != len(phoneme_map):
        vocab_size = len(phoneme_map)
        config["vocab_size"] = vocab_size
    # Additional required keys
    for k in ["n_mels", "sample_rate"]:
        if k not in config:
            raise ValueError(f"Missing '{k}' in config")

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
        phoneme_map_path=str(phoneme_map_path),
    )

    train_loader = DataLoader(
        dataset,
        batch_size=int(config.get("batch_size", 16)),
        shuffle=True,
        num_workers=int(config.get("num_workers", 0)),
        collate_fn=collate_fn,
    )

    # Model
    # Tag model type for downstream detection
    config["model_type"] = "phoneme2mel"
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



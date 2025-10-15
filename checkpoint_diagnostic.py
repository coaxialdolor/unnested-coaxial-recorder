import sys
import argparse
import torch
from utils.vits_training import SimpleTTSModel

ckpt_path = "models/checkpoints/final_model.ckpt"


def to_cpu(x):
    try:
        return x.cpu()
    except Exception:
        return x


def main(path: str):
    print(f"Loading checkpoint: {path}")
    ckpt = torch.load(path, map_location="cpu")

    print("\u2705 Checkpoint top-level keys:")
    if isinstance(ckpt, dict):
        print(list(ckpt.keys()))
    else:
        print(type(ckpt))

    # Recover training config
    config = {}
    if isinstance(ckpt, dict):
        config = ckpt.get("hyper_parameters") or ckpt.get("config") or {}
    if not isinstance(config, dict):
        config = {}

    # Defaults expected by SimpleTTSModel
    config.setdefault("n_mels", 80)
    config.setdefault("hidden_dim", 256)
    config.setdefault("learning_rate", 1e-4)
    config.setdefault("sample_rate", 22050)

    print("\n\u2705 Training config (merged with safe defaults):")
    for k in sorted(config.keys()):
        print(f"{k}: {config[k]}")

    model = None
    load_mode = None
    error_messages = []

    # Preferred: Lightning loader with explicit config
    try:
        model = SimpleTTSModel.load_from_checkpoint(path, config=config)
        load_mode = "lightning.load_from_checkpoint"
    except Exception as e:
        error_messages.append(f"load_from_checkpoint failed: {e}")

    # Fallback: manual state_dict load
    if model is None:
        try:
            model = SimpleTTSModel(config)
            state_dict = ckpt.get("state_dict") if isinstance(ckpt, dict) else None
            if state_dict is None and isinstance(ckpt, dict):
                if any(k.startswith(("encoder.", "decoder.", "output_proj.")) for k in ckpt.keys()):
                    state_dict = ckpt
            if state_dict is None:
                raise RuntimeError("No state_dict found in checkpoint")
            missing, unexpected = model.load_state_dict(state_dict, strict=False)
            load_mode = "manual.load_state_dict(strict=False)"
            print("\n\u2139\ufe0f load_state_dict report:")
            print(f"- missing keys: {missing}")
            print(f"- unexpected keys: {unexpected}")
        except Exception as e:
            error_messages.append(f"manual load_state_dict failed: {e}")

    if model is None:
        print("\n\u274c Could not load model.")
        for msg in error_messages:
            print(f"- {msg}")
        sys.exit(1)

    model.eval()

    print("\n\u2705 Model input/output sanity check:")
    output = None
    try:
        n_mels = int(config.get("n_mels", 80))
        dummy_input = torch.randn(1, 300, n_mels)
        with torch.inference_mode():
            output = model(dummy_input)
        print(f"- Input shape:  {tuple(dummy_input.shape)}")
        print(f"- Output shape: {tuple(to_cpu(output).shape)}")
    except Exception as e:
        print(f"\u274c Error when running model forward: {e}")

    print("\n\u2705 Phoneme support (heuristic):")
    if hasattr(model, "embedding") or "vocab_size" in config:
        print("\u2705 Model includes a text/phoneme encoder.")
    else:
        print("\u2139\ufe0f No embedding/vocab found \u2014 likely mel-to-mel (no text encoder).")

    print("\n\u2705 Vocoder compatibility (heuristic):")
    if output is not None and hasattr(output, "shape"):
        if output.shape[-1] == config.get("n_mels", 80):
            print("\u2705 Output is a mel spectrogram \u2014 vocoder-ready.")
        else:
            print(f"\u274c Unexpected output feature dim: {output.shape[-1]} (expected {config.get('n_mels', 80)})")
    else:
        print("\u2139\ufe0f Skipping \u2014 forward output unavailable.")

    if load_mode:
        print(f"\n\u2705 Loaded using: {load_mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnose TTS Lightning checkpoints")
    parser.add_argument("--ckpt", dest="ckpt", default=ckpt_path, help="Path to checkpoint .ckpt file")
    args = parser.parse_args()
    main(args.ckpt)



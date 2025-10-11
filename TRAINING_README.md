# Coaxial Recorder Training Guide

## Overview
This installation includes full Piper TTS training capabilities. You can train custom voice models from your recorded data.

## Quick Start

1. **Record your voice data** using the recording interface
2. **Post-process your recordings** to ensure consistent quality
3. **Export your dataset** in the desired format
4. **Train your model** using the training interface

## Training Features

- **Train from scratch**: Start with a completely new model
- **Fine-tune**: Continue training from an existing checkpoint
- **GPU acceleration**: Automatic CUDA detection and usage
- **Mixed precision**: Faster training with lower memory usage
- **Real-time monitoring**: Watch training progress and console output

## Command Line Training

You can also train models from the command line:

```bash
# Activate the environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Train a model
python train_model.py --profile-id "YourProfile" --prompt-list-id "YourPromptList" --epochs 100
```

## System Requirements

- **Python 3.8+**
- **8GB+ RAM** (16GB+ recommended for large models)
- **GPU with CUDA support** (optional but recommended)
- **10GB+ free disk space** for models and training data

## Troubleshooting

### CUDA Issues
If you encounter CUDA-related errors:
1. Ensure you have a compatible NVIDIA GPU
2. Install the latest NVIDIA drivers
3. Reinstall PyTorch with CUDA support:
   ```bash
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

### Memory Issues
If you run out of memory:
1. Reduce batch size (try 8 or 4)
2. Use mixed precision training
3. Close other applications
4. Consider using a smaller model size

### Audio Issues
If you have audio processing problems:
1. Ensure espeak-ng is installed
2. Check that your audio files are in WAV format
3. Verify sample rates are consistent (44.1kHz recommended)

## Support

For issues and questions:
1. Check the console output for error messages
2. Review the training logs in `training/logs/`
3. Test your installation with `python test_installation.py`

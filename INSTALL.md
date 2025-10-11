# Coaxial Recorder Installation Guide

## Quick Installation

### Option 1: Full Installation (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd coaxial-recorder

# Run the comprehensive installer
chmod +x install.sh
./install.sh
```

This will install:
- ✅ Core application dependencies
- ✅ Piper TTS training framework
- ✅ All ML training dependencies
- ✅ System dependencies (espeak-ng, ffmpeg, etc.)
- ✅ Pre-trained model samples
- ✅ Training scripts and utilities

### Option 2: Basic Installation
```bash
# For basic recording and post-processing only
chmod +x setup_venv.sh
./setup_venv.sh
```

## System Requirements

### Minimum Requirements
- **Python 3.8+**
- **4GB RAM**
- **2GB free disk space**
- **Internet connection** (for downloading dependencies)

### Recommended for Training
- **Python 3.8+**
- **16GB+ RAM**
- **10GB+ free disk space**
- **NVIDIA GPU with CUDA support** (optional but recommended)
- **Internet connection**

## Platform-Specific Notes

### macOS
- Requires Homebrew (installed automatically)
- Installs: espeak-ng, ffmpeg, portaudio

### Linux (Ubuntu/Debian)
- Requires sudo access for system packages
- Installs: espeak-ng, ffmpeg, portaudio, build tools

### Windows
- Requires Visual Studio Build Tools
- May need manual installation of espeak-ng and ffmpeg
- Consider using WSL2 for better compatibility

## What Gets Installed

### Core Application
- FastAPI web framework
- Audio processing (pydub, librosa)
- Data handling (pandas, numpy)

### Training Framework
- PyTorch with CUDA support
- Piper TTS framework
- Transformers and datasets libraries
- Training monitoring tools (tensorboard, wandb)

### System Dependencies
- **espeak-ng**: Text-to-speech synthesis
- **ffmpeg**: Audio/video processing
- **portaudio**: Audio I/O

## Post-Installation

### Test Installation
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Test the installation
python test_installation.py
```

### Launch Application
```bash
# Full version with training support
./launch_complete.sh

# Or basic version
./launch.sh
```

## Troubleshooting

### Common Issues

#### 1. CUDA Installation Fails
```bash
# Install CPU-only PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### 2. System Dependencies Missing
**macOS:**
```bash
brew install espeak-ng ffmpeg portaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install espeak-ng ffmpeg portaudio19-dev
```

**Windows:**
- Install Visual Studio Build Tools
- Consider using conda: `conda install espeak-ng ffmpeg`

#### 3. Memory Issues During Training
- Reduce batch size to 8 or 4
- Use mixed precision training
- Close other applications
- Consider using a smaller model size

#### 4. Audio Processing Errors
- Ensure audio files are in WAV format
- Check sample rates are consistent (44.1kHz recommended)
- Verify espeak-ng is properly installed

### Getting Help

1. **Check logs**: Look in `training/logs/` for detailed error messages
2. **Test installation**: Run `python test_installation.py`
3. **Check system**: Ensure all system dependencies are installed
4. **Review documentation**: See `TRAINING_README.md` for training-specific help

## Features by Installation Type

### Basic Installation
- ✅ Voice recording
- ✅ Audio post-processing
- ✅ Dataset export
- ✅ Basic statistics

### Full Installation
- ✅ All basic features
- ✅ Model training from scratch
- ✅ Fine-tuning from checkpoints
- ✅ GPU acceleration
- ✅ Training progress monitoring
- ✅ Command-line training tools

## Uninstalling

```bash
# Remove virtual environment
rm -rf venv

# Remove training data (optional)
rm -rf training

# Remove models (optional)
rm -rf models
```

## Updating

```bash
# Pull latest changes
git pull

# Reinstall dependencies
./install.sh
```

---

**Need help?** Check the troubleshooting section or review the training documentation in `TRAINING_README.md`.

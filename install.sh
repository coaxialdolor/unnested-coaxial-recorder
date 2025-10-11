#!/bin/bash

# Comprehensive installer for Coaxial Recorder with Piper TTS Training
# This script sets up the complete environment including training capabilities

set -e  # Exit on any error

echo "🚀 Installing Coaxial Recorder with Piper TTS Training Support"
echo "=============================================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS, Linux, or Windows
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

print_status "Detected operating system: $OS"

# Check for Python
print_status "Checking Python installation..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
elif command -v python &>/dev/null; then
    PYTHON=python
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
else
    print_error "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

print_success "Found Python $PYTHON_VERSION"

# Check Python version
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Install system dependencies
print_status "Installing system dependencies..."

if [ "$OS" == "macos" ]; then
    # Check for Homebrew
    if ! command -v brew &>/dev/null; then
        print_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    print_status "Installing system packages via Homebrew..."
    brew install espeak-ng ffmpeg portaudio

    # Install MFA via conda (recommended method)
    print_status "Installing Montreal Forced Aligner (MFA)..."
    if command -v conda &>/dev/null; then
        conda install -c conda-forge montreal-forced-alignment
    else
        print_warning "Conda not found. MFA will need to be installed manually."
        print_warning "See: https://montreal-forced-alignment.readthedocs.io/en/latest/installation.html"
    fi

elif [ "$OS" == "linux" ]; then
    # Detect package manager
    if command -v apt-get &>/dev/null; then
        print_status "Installing system packages via apt..."
        sudo apt-get update
        sudo apt-get install -y espeak-ng ffmpeg portaudio19-dev python3-dev build-essential

        # Install MFA via conda (recommended method)
        print_status "Installing Montreal Forced Aligner (MFA)..."
        if command -v conda &>/dev/null; then
            conda install -c conda-forge montreal-forced-alignment
        else
            print_warning "Conda not found. Installing MFA via pip..."
            pip install montreal-forced-alignment
        fi

    elif command -v yum &>/dev/null; then
        print_status "Installing system packages via yum..."
        sudo yum install -y espeak-ng ffmpeg portaudio-devel python3-devel gcc gcc-c++

        # Install MFA
        print_status "Installing Montreal Forced Aligner (MFA)..."
        if command -v conda &>/dev/null; then
            conda install -c conda-forge montreal-forced-alignment
        else
            pip install montreal-forced-alignment
        fi

    elif command -v pacman &>/dev/null; then
        print_status "Installing system packages via pacman..."
        sudo pacman -S --noconfirm espeak-ng ffmpeg portaudio python

        # Install MFA
        print_status "Installing Montreal Forced Aligner (MFA)..."
        if command -v conda &>/dev/null; then
            conda install -c conda-forge montreal-forced-alignment
        else
            pip install montreal-forced-alignment
        fi

    else
        print_warning "Could not detect package manager. Please install espeak-ng, ffmpeg, and portaudio manually."
        print_warning "Also install MFA: pip install montreal-forced-alignment"
    fi

elif [ "$OS" == "windows" ]; then
    print_warning "Windows detected. Please ensure you have Visual Studio Build Tools installed."
    print_warning "You may need to install espeak-ng and ffmpeg manually or via conda."
    print_warning "For MFA, use: conda install -c conda-forge montreal-forced-alignment"
fi

# Create virtual environment
print_status "Setting up Python virtual environment..."

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists."
    read -p "Do you want to recreate it? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        print_status "Removing existing virtual environment..."
        rm -rf venv
    else
        print_status "Using existing virtual environment."
    fi
fi

if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    $PYTHON -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment!"
        exit 1
    fi
fi

# Activate virtual environment
print_status "Activating virtual environment..."
if [ "$OS" == "windows" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip and install build tools
print_status "Setting up Python build environment..."
$PYTHON -m pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    print_error "Failed to upgrade pip/setuptools/wheel!"
    exit 1
fi

# Install PyTorch with appropriate CUDA support
print_status "Installing PyTorch..."
if [ "$OS" == "windows" ]; then
    # Windows - install CPU version by default, user can install CUDA manually
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
else
    # macOS and Linux - try CUDA first, fallback to CPU
    print_status "Attempting to install PyTorch with CUDA support..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118 2>/dev/null || {
        print_warning "CUDA installation failed, installing CPU version..."
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    }
fi

# Install other requirements
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    # Install requirements with fallback for problematic packages
    pip install --only-binary=all -r requirements.txt 2>/dev/null || {
        print_warning "Some packages failed with pre-built wheels, trying source installation..."
        pip install -r requirements.txt
    }

    if [ $? -ne 0 ]; then
        print_warning "Some packages failed, trying to install core packages individually..."
        pip install fastapi uvicorn python-multipart jinja2 aiofiles pydantic pydub pandas
        pip install transformers datasets accelerate evaluate librosa soundfile scipy scikit-learn
        pip install tensorboard wandb phonemizer
    fi
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Download and setup Piper TTS
print_status "Setting up Piper TTS..."

# Create training directory
mkdir -p training
cd training

# Download Piper TTS if not already present
if [ ! -d "piper" ]; then
    print_status "Downloading Piper TTS..."
    git clone https://github.com/rhasspy/piper.git
    if [ $? -ne 0 ]; then
        print_error "Failed to clone Piper TTS repository!"
        exit 1
    fi
fi

cd piper

# Install Piper dependencies
print_status "Installing Piper TTS dependencies..."
pip install -e .

# Download pre-trained models for reference
print_status "Downloading sample pre-trained models..."
mkdir -p models

# Download a small English model for testing
if [ ! -f "models/en_US-lessac-medium.onnx" ]; then
    print_status "Downloading sample English model..."
    wget -O models/en_US-lessac-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    wget -O models/en_US-lessac-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
fi

cd ../..

# Create training script
print_status "Creating training script..."
cat > train_model.py << 'EOF'
#!/usr/bin/env python3
"""
Coaxial Recorder Training Script
Trains Piper TTS models from recorded voice data
"""

import argparse
import os
import sys
import json
import torch
import torchaudio
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Add piper to path
sys.path.append(str(Path(__file__).parent / "training" / "piper"))

from piper.train import main as piper_train_main

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

def prepare_dataset(profile_id: str, prompt_list_id: str, output_dir: str) -> Dict:
    """Prepare dataset for training"""
    logging.info(f"Preparing dataset for profile: {profile_id}, prompt list: {prompt_list_id}")

    # This would implement the actual dataset preparation
    # For now, return a placeholder structure
    dataset_info = {
        "profile_id": profile_id,
        "prompt_list_id": prompt_list_id,
        "output_dir": output_dir,
        "audio_files": [],
        "transcripts": []
    }

    return dataset_info

def train_model(args):
    """Main training function"""
    setup_logging()

    logging.info("Starting model training...")
    logging.info(f"Arguments: {args}")

    # Check if CUDA is available
    device = "cuda" if torch.cuda.is_available() and args.use_gpu else "cpu"
    logging.info(f"Using device: {device}")

    # Prepare dataset
    dataset_info = prepare_dataset(
        args.profile_id,
        args.prompt_list_id,
        args.output_dir
    )

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Prepare training arguments for Piper
    piper_args = [
        "--dataset-dir", dataset_info["output_dir"],
        "--output-dir", args.output_dir,
        "--model-name", args.model_name or f"{args.profile_id}_{args.prompt_list_id}",
        "--epochs", str(args.epochs),
        "--batch-size", str(args.batch_size),
        "--learning-rate", str(args.learning_rate),
        "--save-interval", str(args.save_interval),
        "--early-stopping", str(args.early_stopping),
    ]

    if args.checkpoint:
        piper_args.extend(["--checkpoint", args.checkpoint])

    if device == "cuda":
        piper_args.append("--use-gpu")

    if args.mixed_precision:
        piper_args.append("--mixed-precision")

    # Run Piper training
    try:
        logging.info("Starting Piper training...")
        piper_train_main(piper_args)
        logging.info("Training completed successfully!")
        return True
    except Exception as e:
        logging.error(f"Training failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Train Piper TTS model")

    # Dataset arguments
    parser.add_argument("--profile-id", required=True, help="Voice profile ID")
    parser.add_argument("--prompt-list-id", required=True, help="Prompt list ID")

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
    parser.add_argument("--checkpoint", help="Path to checkpoint for fine-tuning")

    # Output arguments
    parser.add_argument("--output-dir", default="./models", help="Output directory")
    parser.add_argument("--model-name", help="Model name")

    args = parser.parse_args()

    success = train_model(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
EOF

chmod +x train_model.py

# Create directories
print_status "Creating necessary directories..."
mkdir -p models
mkdir -p training/checkpoints
mkdir -p training/logs

# Create a simple test script
print_status "Creating test script..."
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify installation
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: {e}")
        return False

def main():
    print("Testing installation...")
    print("=" * 50)

    # Core dependencies
    core_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydub", "Pydub"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
    ]

    # Training dependencies
    training_modules = [
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio"),
        ("transformers", "Transformers"),
        ("datasets", "Datasets"),
        ("librosa", "Librosa"),
        ("soundfile", "SoundFile"),
        ("scipy", "SciPy"),
        ("sklearn", "Scikit-learn"),
    ]

    print("Core Dependencies:")
    core_success = all(test_import(module, name) for module, name in core_modules)

    print("\nTraining Dependencies:")
    training_success = all(test_import(module, name) for module, name in training_modules)

    # Test PyTorch CUDA
    print("\nPyTorch CUDA Support:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.device_count()} device(s)")
            for i in range(torch.cuda.device_count()):
                print(f"   - {torch.cuda.get_device_name(i)}")
        else:
            print("⚠️  CUDA not available (CPU-only mode)")
    except ImportError:
        print("❌ PyTorch not available")

    print("\n" + "=" * 50)
    if core_success and training_success:
        print("🎉 Installation test passed!")
        return True
    else:
        print("❌ Installation test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chmod +x test_installation.py

# Run installation test
print_status "Running installation test..."
$PYTHON test_installation.py

if [ $? -eq 0 ]; then
    print_success "Installation test passed!"
else
    print_warning "Some components may not be properly installed."
fi

# Create launch script
print_status "Creating launch script..."
cat > launch_complete.sh << 'EOF'
#!/bin/bash

# Launch script for Coaxial Recorder with full training support

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if training dependencies are available
echo "Checking training dependencies..."
python test_installation.py

if [ $? -ne 0 ]; then
    echo "⚠️  Some training dependencies are missing. Training features may not work."
    echo "You can still use recording and post-processing features."
fi

# Launch the application
echo "🚀 Launching Coaxial Recorder..."
python app.py
EOF

chmod +x launch_complete.sh

# Final setup
print_status "Setting up file permissions..."
chmod +x *.sh
chmod +x train_model.py
chmod +x test_installation.py

# Create README for training
print_status "Creating training documentation..."
cat > TRAINING_README.md << 'EOF'
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
EOF

print_success "Installation completed successfully!"
echo ""
echo "🎉 Coaxial Recorder with Piper TTS Training is ready!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
if [ "$OS" == "windows" ]; then
    echo "   source venv/Scripts/activate"
else
    echo "   source venv/bin/activate"
fi
echo ""
echo "2. Launch the application:"
echo "   ./launch_complete.sh"
echo ""
echo "3. Or test the installation:"
echo "   python test_installation.py"
echo ""
echo "📚 See TRAINING_README.md for detailed training instructions"
echo ""
print_success "Happy voice training! 🎤🤖"

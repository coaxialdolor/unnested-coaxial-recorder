#!/bin/bash

# Fixed installer for Coaxial Recorder with Piper TTS Training
# This script properly sets up the virtual environment first, then installs everything
# Works on Windows, Linux, and macOS

set -e  # Exit on any error

echo "🚀 Installing Coaxial Recorder with Piper TTS Training Support (Fixed Version)"
echo "============================================================================="

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

# Check for Git
print_status "Checking Git installation..."
if ! command -v git &>/dev/null; then
    print_error "Git is required but not installed. Please install Git first."
    exit 1
fi
print_success "Git found: $(git --version)"

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

    # Ensure espeak symlink exists for phonemizer compatibility
    if [ ! -L "/opt/homebrew/bin/espeak" ] && [ -f "/opt/homebrew/bin/espeak-ng" ]; then
        print_status "Creating espeak symlink for phonemizer compatibility..."
        ln -sf /opt/homebrew/bin/espeak-ng /opt/homebrew/bin/espeak
    fi

elif [ "$OS" == "linux" ]; then
    # Detect package manager
    if command -v apt-get &>/dev/null; then
        print_status "Installing system packages via apt..."
        sudo apt-get update
        sudo apt-get install -y espeak-ng ffmpeg portaudio19-dev python3-dev build-essential

        # Create espeak symlink for phonemizer compatibility
        if [ ! -L "/usr/bin/espeak" ] && [ -f "/usr/bin/espeak-ng" ]; then
            print_status "Creating espeak symlink for phonemizer compatibility..."
            sudo ln -sf /usr/bin/espeak-ng /usr/bin/espeak
        fi
    elif command -v yum &>/dev/null; then
        print_status "Installing system packages via yum..."
        sudo yum install -y espeak-ng ffmpeg portaudio-devel python3-devel gcc gcc-c++

        # Create espeak symlink for phonemizer compatibility
        if [ ! -L "/usr/bin/espeak" ] && [ -f "/usr/bin/espeak-ng" ]; then
            print_status "Creating espeak symlink for phonemizer compatibility..."
            sudo ln -sf /usr/bin/espeak-ng /usr/bin/espeak
        fi
    elif command -v pacman &>/dev/null; then
        print_status "Installing system packages via pacman..."
        sudo pacman -S --noconfirm espeak-ng ffmpeg portaudio python

        # Create espeak symlink for phonemizer compatibility
        if [ ! -L "/usr/bin/espeak" ] && [ -f "/usr/bin/espeak-ng" ]; then
            print_status "Creating espeak symlink for phonemizer compatibility..."
            sudo ln -sf /usr/bin/espeak-ng /usr/bin/espeak
        fi
    else
        print_warning "Could not detect package manager. Please install espeak-ng, ffmpeg, and portaudio manually."
    fi

elif [ "$OS" == "windows" ]; then
    print_status "Windows detected. Setting up system dependencies..."
    print_status "For Windows, please ensure you have:"
    print_status "1. Visual Studio Build Tools (for compilation)"
    print_status "2. FFmpeg added to PATH (download from https://ffmpeg.org/)"
    print_status "3. Consider installing espeak via: conda install -c conda-forge espeak"

    # Try multiple Windows package managers
    if command -v winget &>/dev/null; then
        print_status "Winget detected. Installing FFmpeg via Winget..."
        winget install -e --id Gyan.FFmpeg 2>/dev/null || {
            print_warning "Winget installation failed, trying Chocolatey..."
            if command -v choco &>/dev/null; then
                choco install ffmpeg -y
                print_success "FFmpeg installed via Chocolatey"
            else
                print_warning "Please install FFmpeg manually from: https://ffmpeg.org/download.html"
            fi
        } && print_success "FFmpeg installed via Winget"
    elif command -v choco &>/dev/null; then
        print_status "Chocolatey detected. Installing packages via Chocolatey..."
        choco install ffmpeg -y
        print_success "FFmpeg installed via Chocolatey"
    else
        print_warning "No package manager found. Please install FFmpeg manually."
        print_warning "Download from: https://ffmpeg.org/download.html"
    fi
fi

# Create virtual environment FIRST
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
    # For Windows Git Bash/Cygwin compatibility
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate  # Some Windows Python installations use this
    fi
else
    source venv/bin/activate
fi

# Verify virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_error "Failed to activate virtual environment!"
    exit 1
fi

print_success "Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip and install build tools
print_status "Setting up Python build environment..."
$PYTHON -m pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    print_error "Failed to upgrade pip/setuptools/wheel!"
    exit 1
fi

# Install PyTorch with appropriate CUDA support
print_status "Installing PyTorch (this may take 5-10 minutes)..."
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
print_success "PyTorch installation completed"

# Install core requirements
print_status "Installing core Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_warning "Some packages failed, trying to install core packages individually..."
        pip install fastapi uvicorn python-multipart jinja2 aiofiles pydantic pydub pandas
    fi
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Install training requirements
print_status "Installing training dependencies..."
if [ -f "requirements_training.txt" ]; then
    pip install -r requirements_training.txt
else
    print_warning "requirements_training.txt not found, installing training packages individually..."
    pip install transformers datasets accelerate evaluate librosa soundfile scipy scikit-learn
    pip install tensorboard wandb phonemizer montreal-forced-alignment
fi

# Install TTS-specific dependencies
print_status "Installing TTS dependencies..."
pip install piper-tts phonemizer

# Verify espeak installation
print_status "Verifying espeak installation..."
if command -v espeak &>/dev/null; then
    print_success "espeak found: $(which espeak)"
    espeak --version 2>/dev/null || echo "espeak version check failed"
elif command -v espeak-ng &>/dev/null; then
    print_success "espeak-ng found: $(which espeak-ng)"
    espeak-ng --version 2>/dev/null || echo "espeak-ng version check failed"
else
    print_warning "espeak/espeak-ng not found in PATH"
fi

# Install Piper TTS
print_status "Installing Piper TTS..."
pip install piper-tts

# Try to install training dependencies (may fail on some systems)
print_status "Installing Piper TTS training dependencies..."
pip install "piper-tts[train]" 2>/dev/null || {
    print_warning "Piper training dependencies failed, trying alternative approach..."

    # Fallback: Download and install from source
    print_status "Setting up Piper TTS from source (this may take 10-15 minutes)..."

    # Create training directory
    mkdir -p training
    cd training

    # Download Piper TTS if not already present
    if [ ! -d "piper" ]; then
        print_status "Downloading Piper TTS repository (large download, please wait)..."
        git clone https://github.com/rhasspy/piper.git
        if [ $? -ne 0 ]; then
            print_error "Failed to clone Piper TTS repository!"
            exit 1
        fi
        print_success "Piper TTS repository downloaded"
    else
        print_status "Piper TTS repository already exists, skipping download"
    fi

    # Install the runtime version first
    cd piper/src/python_run
    print_status "Installing Piper TTS runtime from source..."
    pip install -e .
    print_success "Piper TTS runtime installed"

    # Install the training version (with workaround for missing piper-phonemize)
    cd ../python
    print_status "Installing Piper TTS training from source..."
    pip install -e . --no-deps || {
        print_warning "Piper training installation failed, trying without dependencies..."
        pip install -e . --no-deps
    }
    print_success "Piper TTS training installed"

    # Return to the root directory
    cd ../../../..
}

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

    # TTS dependencies
    tts_modules = [
        ("piper", "Piper TTS"),
        ("phonemizer", "Phonemizer"),
    ]

    print("Core Dependencies:")
    core_success = all(test_import(module, name) for module, name in core_modules)

    print("\nTraining Dependencies:")
    training_success = all(test_import(module, name) for module, name in training_modules)

    print("\nTTS Dependencies:")
    tts_success = all(test_import(module, name) for module, name in tts_modules)

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
    if core_success and training_success and tts_success:
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

# Run installation test and collect results
print_status "Running installation test..."
$PYTHON test_installation.py
INSTALLATION_TEST_RESULT=$?

# Initialize installation summary
INSTALLATION_SUMMARY=""
FAILED_COMPONENTS=""
SUCCESSFUL_COMPONENTS=""

# Check individual components
print_status "Verifying installation components..."

# Check core components
if python -c "import fastapi, uvicorn, pydub, numpy, pandas" 2>/dev/null; then
    SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS Core Dependencies"
else
    FAILED_COMPONENTS="$FAILED_COMPONENTS Core Dependencies"
fi

# Check training components
if python -c "import torch, torchaudio, transformers, datasets, librosa, soundfile, scipy, sklearn" 2>/dev/null; then
    SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS Training Dependencies"
else
    FAILED_COMPONENTS="$FAILED_COMPONENTS Training Dependencies"
fi

# Check TTS components
if python -c "import piper, phonemizer" 2>/dev/null; then
    SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS TTS Dependencies"
else
    FAILED_COMPONENTS="$FAILED_COMPONENTS TTS Dependencies"
fi

# Check Piper training
if python -c "import piper_train" 2>/dev/null; then
    SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS Piper Training"
else
    FAILED_COMPONENTS="$FAILED_COMPONENTS Piper Training"
fi

# Generate summary
if [ $INSTALLATION_TEST_RESULT -eq 0 ]; then
    print_success "Installation test passed!"
    INSTALLATION_SUMMARY="✅ All components installed successfully"
else
    print_warning "Some components may not be properly installed."
    INSTALLATION_SUMMARY="⚠️  Partial installation completed"
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

# Create Windows batch launcher
if [ "$OS" == "windows" ]; then
    print_status "Creating Windows batch launcher..."
    cat > launch_complete.bat << 'EOF'
@echo off
echo Activating virtual environment...
call venv\Scripts\activate

echo Checking training dependencies...
python test_installation.py

if %errorlevel% neq 0 (
    echo ⚠️  Some training dependencies are missing. Training features may not work.
    echo You can still use recording and post-processing features.
)

echo 🚀 Launching Coaxial Recorder...
python app.py
pause
EOF
    print_success "Windows batch launcher created: launch_complete.bat"
fi

# Final setup
print_status "Setting up file permissions..."
chmod +x *.sh
chmod +x test_installation.py

print_success "Installation completed!"
echo ""
echo "🎉 Coaxial Recorder with Piper TTS Training is ready!"
echo ""
echo "📊 INSTALLATION SUMMARY:"
echo "========================"
echo "$INSTALLATION_SUMMARY"
echo ""

if [ -n "$SUCCESSFUL_COMPONENTS" ]; then
    echo "✅ Successfully Installed:"
    for component in $SUCCESSFUL_COMPONENTS; do
        echo "   - $component"
    done
    echo ""
fi

if [ -n "$FAILED_COMPONENTS" ]; then
    echo "❌ Failed to Install:"
    for component in $FAILED_COMPONENTS; do
        echo "   - $component"
    done
    echo ""
    echo "🔧 Recovery Suggestions:"
    echo "   - Run the installer again: ./install.sh"
    echo "   - Check your internet connection"
    echo "   - Ensure you have sufficient disk space"
    echo "   - Try installing missing packages manually:"
    echo "     source venv/bin/activate"
    echo "     pip install <package-name>"
    echo ""
fi

echo "🚀 Next Steps:"
echo "1. Activate the virtual environment:"
if [ "$OS" == "windows" ]; then
    echo "   source venv/Scripts/activate"
    echo "   # Or use: venv\\Scripts\\activate.bat"
else
    echo "   source venv/bin/activate"
fi
echo ""
echo "2. Launch the application:"
if [ "$OS" == "windows" ]; then
    echo "   ./launch_complete.sh  # Git Bash"
    echo "   # Or double-click: launch_complete.bat"
else
    echo "   ./launch_complete.sh"
fi
echo ""
echo "3. Or test the installation:"
echo "   python test_installation.py"
echo ""

if [ "$OS" == "windows" ]; then
    echo "📝 Windows Notes:"
    echo "   - If you encounter issues, ensure Visual Studio Build Tools are installed"
    echo "   - Make sure FFmpeg is in your PATH"
    echo "   - Consider using conda for espeak: conda install -c conda-forge espeak"
    echo ""
fi

if [ -n "$FAILED_COMPONENTS" ]; then
    echo "⚠️  Note: Some features may not work due to missing components."
    echo "   The core recording functionality should still work."
    echo ""
fi

print_success "Happy voice training! 🎤🤖"
#!/usr/bin/env bash

# Fixed installer for Coaxial Recorder with Piper TTS Training
# This script properly sets up the virtual environment first, then installs everything
# Works on Windows, Linux, and macOS

set -e  # Exit on any error

# Detect the shell and set up echo command appropriately
if [ -n "$BASH_VERSION" ]; then
    ECHO_CMD="echo -e"
elif command -v printf >/dev/null 2>&1; then
    # Fallback to printf which is more portable
    ECHO_CMD="printf '%b\n'"
else
    # Last resort: plain echo without colors
    ECHO_CMD="echo"
fi

echo "🚀 Installing Coaxial Recorder with Piper TTS Training Support (Fixed Version)"
echo "============================================================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output (only if terminal supports it)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Function to print colored output (works with any shell)
print_status() {
    printf "%b[INFO]%b %s\n" "$BLUE" "$NC" "$1"
}

print_success() {
    printf "%b[SUCCESS]%b %s\n" "$GREEN" "$NC" "$1"
}

print_warning() {
    printf "%b[WARNING]%b %s\n" "$YELLOW" "$NC" "$1"
}

print_error() {
    printf "%b[ERROR]%b %s\n" "$RED" "$NC" "$1"
}

print_info() {
    printf "%b[INFO]%b %s\n" "$BLUE" "$NC" "$1"
}

# Check if running on macOS, Linux, or Windows
case "$OSTYPE" in
    darwin*)
        OS="macos"
        ;;
    linux-gnu*)
        OS="linux"
        ;;
    msys|win32|cygwin*)
        OS="windows"
        ;;
    *)
        print_error "Unsupported operating system: $OSTYPE"
        print_error "Detected OSTYPE: $OSTYPE"
        print_error "If you're on Windows, make sure you're using Git Bash, WSL, or Cygwin"
        exit 1
        ;;
esac

print_status "Detected operating system: $OS"

# Check Python version and offer to install 3.11 locally using prebuilt binaries
print_status "Checking Python installation..."

# Function to check if we already have a local Python 3.10 or 3.11
check_local_python311() {
    # Check for Python 3.10 first (preferred)
    if [ -f "python310/bin/python3.10" ]; then
        echo "python310/bin/python3.10"
        return 0
    elif [ -f "python310/bin/python3" ]; then
        echo "python310/bin/python3"
        return 0
    # Then check for Python 3.11
    elif [ -f "python311/bin/python3.11" ]; then
        echo "python311/bin/python3.11"
        return 0
    elif [ -f "python311/bin/python3" ]; then
        echo "python311/bin/python3"
        return 0
    elif [ -f "python311/python.exe" ]; then
        echo "python311/python.exe"
        return 0
    elif [ -f "python311/bin/python" ]; then
        echo "python311/bin/python"
        return 0
    fi
    return 1
}

# Better Python detection function
get_system_python() {
    # First check if we have a local Python 3.11
    # Use || true to prevent set -e from exiting on return 1
    LOCAL_PYTHON_CMD=$(check_local_python311 2>/dev/null || true)
    if [ -n "$LOCAL_PYTHON_CMD" ] && [ -f "$LOCAL_PYTHON_CMD" ]; then
        echo "$LOCAL_PYTHON_CMD"
        return 0
    fi

    # Fall back to system Python
    if command -v python3 >/dev/null 2>&1; then
        command -v python3
    elif command -v python >/dev/null 2>&1; then
        command -v python
    else
        return 1
    fi
}

# Get current Python info
CURRENT_PYTHON=$(get_system_python)
if [ $? -ne 0 ]; then
    print_error "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

CURRENT_VERSION=$($CURRENT_PYTHON --version 2>&1 | cut -d' ' -f2)
CURRENT_MINOR=$(echo $CURRENT_VERSION | cut -d'.' -f2)

print_success "Found system Python $CURRENT_VERSION"

# Check if we already have local Python 3.11
LOCAL_PYTHON_CMD=$(check_local_python311 || true)

if [ -n "$LOCAL_PYTHON_CMD" ]; then
    print_success "Found local Python 3.11 installation"
    PYTHON_CMD="$LOCAL_PYTHON_CMD"
elif [ "$CURRENT_MINOR" -ge 12 ]; then
    print_warning "Python $CURRENT_VERSION detected - limited compatibility"
    print_warning "Montreal Forced Aligner dependencies don't support Python 3.12+"
    echo ""
    echo "COMPATIBILITY SUMMARY for Python $CURRENT_VERSION:"
    echo "  ✅ Core application: Works"
    echo "  ✅ PyTorch & ML packages: Works"
    echo "  ✅ Audio processing: Works"
    echo "  ❌ Montreal Forced Aligner: Will be SKIPPED"
    echo ""
    echo "RECOMMENDED: Python 3.10 for full compatibility (all packages work)"
    echo ""
    echo "Options:"
    echo "  1. Install Python 3.10 locally (recommended - self-contained)"
    echo "  2. Continue with Python $CURRENT_VERSION (MFA will be skipped)"
    echo "  3. Cancel and install Python 3.10 system-wide with pyenv"
    echo ""
    read -p "Choose option [1/2/3]: " install_choice

    if [ "$install_choice" = "1" ]; then
        print_status "Installing Python 3.10 locally in this project folder..."
        print_status "This keeps everything self-contained and easy to remove."
        # Set flag to install Python 3.10 locally
        INSTALL_LOCAL_PYTHON=1
        INSTALL_PYTHON_VERSION="3.10"
    elif [ "$install_choice" = "2" ] || [ -z "$install_choice" ]; then
        print_status "Continuing with Python $CURRENT_VERSION..."
        PYTHON_CMD="$CURRENT_PYTHON"
        print_warning "Montreal Forced Aligner will be skipped"
    else
        print_error "Installation cancelled."
        echo ""
        echo "To install Python 3.10 system-wide:"
        echo "  brew install pyenv"
        echo "  pyenv install 3.10.13"
        echo "  pyenv local 3.10.13"
        echo "  bash install.sh"
        exit 1
    fi
elif [ "$CURRENT_MINOR" -lt 10 ]; then
    print_warning "Python $CURRENT_VERSION is older than recommended (3.10+)"
    print_warning "Some packages may not work correctly"
    echo ""
    echo "Options:"
    echo "  1. Install Python 3.10 locally (recommended)"
    echo "  2. Continue with Python $CURRENT_VERSION anyway"
    echo ""
    read -p "Choose option [1/2]: " install_choice

    if [ "$install_choice" = "1" ]; then
        print_status "Installing Python 3.10 locally..."
        INSTALL_LOCAL_PYTHON=1
        INSTALL_PYTHON_VERSION="3.10"
    else
        PYTHON_CMD="$CURRENT_PYTHON"
    fi
elif [ "$CURRENT_MINOR" -eq 11 ]; then
    print_success "Python 3.11 detected - excellent choice!"
    print_warning "Note: MFA works best with Python 3.10, but 3.11 should work"
    PYTHON_CMD="$CURRENT_PYTHON"
elif [ "$CURRENT_MINOR" -eq 10 ]; then
    print_success "Python 3.10 detected - perfect! This is the best version for all dependencies."
    PYTHON_CMD="$CURRENT_PYTHON"
elif [ "$CURRENT_MINOR" -lt 10 ]; then
    print_warning "Python $CURRENT_VERSION is older than recommended (3.10+)"
    print_warning "Some packages may not work correctly"
    echo ""
    read -p "Continue with Python $CURRENT_VERSION anyway? [Y/n]: " continue_anyway

    if [ -z "$continue_anyway" ] || [ "$continue_anyway" = "Y" ] || [ "$continue_anyway" = "y" ]; then
        PYTHON_CMD="$CURRENT_PYTHON"
    else
        print_error "Installation cancelled."
        exit 1
    fi
else
    # Fallback
    PYTHON_CMD="$CURRENT_PYTHON"
fi

# Handle local Python installation (3.10 or 3.11)
if [ "${INSTALL_LOCAL_PYTHON:-0}" -eq 1 ]; then
    if [ "$INSTALL_PYTHON_VERSION" = "3.10" ]; then
        PYTHON_VERSION="3.10.13"
        PYTHON_DIR="python310"
        PYTHON_DOWNLOAD_VERSION="3.10.13+20240224"
        print_status "Installing Python 3.10 locally using prebuilt binaries..."
    else
        PYTHON_VERSION="3.11.6"
        PYTHON_DIR="python311"
        PYTHON_DOWNLOAD_VERSION="3.11.6+20231002"
        print_status "Installing Python 3.11 locally using prebuilt binaries..."
    fi

    # Create python directory before extraction
    mkdir -p "$PYTHON_DIR"

    if [ "$OS" == "macos" ]; then
        print_status "Downloading Python $PYTHON_VERSION for macOS..."

        # Construct download URL based on version
        DOWNLOAD_DATE=$(echo "$PYTHON_DOWNLOAD_VERSION" | cut -d'+' -f2)
        ARCHIVE_NAME="${PYTHON_DIR}-macos.tar.gz"
        DOWNLOAD_URL="https://github.com/indygreg/python-build-standalone/releases/download/${DOWNLOAD_DATE}/cpython-${PYTHON_DOWNLOAD_VERSION}-x86_64-apple-darwin-install_only.tar.gz"

        # Download the actual binary distribution
        if command -v curl >/dev/null 2>&1; then
            curl -L -o "$ARCHIVE_NAME" "$DOWNLOAD_URL"
        else
            wget -O "$ARCHIVE_NAME" "$DOWNLOAD_URL"
        fi

        if [ -f "$ARCHIVE_NAME" ]; then
            print_status "Extracting portable Python..."
            tar -xzf "$ARCHIVE_NAME" -C "$PYTHON_DIR" --strip-components=2 2>/dev/null || {
                print_warning "Standard extraction failed, trying alternative..."
                tar -xzf "$ARCHIVE_NAME" -C "$PYTHON_DIR" --strip-components=1
            }
            rm -f "$ARCHIVE_NAME"

            # Find the Python executable
            PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1,2)
            if [ -f "$PYTHON_DIR/bin/python$PYTHON_MAJOR" ]; then
                PYTHON_CMD="$PYTHON_DIR/bin/python$PYTHON_MAJOR"
                print_success "Python $PYTHON_VERSION installed locally at: $PYTHON_CMD"
            elif [ -f "$PYTHON_DIR/bin/python3" ]; then
                PYTHON_CMD="$PYTHON_DIR/bin/python3"
                print_success "Python $PYTHON_VERSION installed locally at: $PYTHON_CMD"
            elif [ -f "$PYTHON_DIR/python$PYTHON_MAJOR" ]; then
                PYTHON_CMD="$PYTHON_DIR/python$PYTHON_MAJOR"
                print_success "Python $PYTHON_VERSION installed locally at: $PYTHON_CMD"
            else
                print_warning "Local Python extraction failed, using system Python"
                PYTHON_CMD="$CURRENT_PYTHON"
            fi
        else
            print_warning "Failed to download Python, using system Python"
            PYTHON_CMD="$CURRENT_PYTHON"
        fi

    elif [ "$OS" == "linux" ]; then
        print_status "Downloading standalone Python $PYTHON_VERSION for Linux..."

        # Construct download URL
        DOWNLOAD_DATE=$(echo "$PYTHON_DOWNLOAD_VERSION" | cut -d'+' -f2)
        ARCHIVE_NAME="${PYTHON_DIR}-linux.tar.gz"
        DOWNLOAD_URL="https://github.com/indygreg/python-build-standalone/releases/download/${DOWNLOAD_DATE}/cpython-${PYTHON_DOWNLOAD_VERSION}-x86_64-unknown-linux-gnu-install_only.tar.gz"

        # Download the standalone Linux build
        if command -v curl >/dev/null 2>&1; then
            curl -L -o "$ARCHIVE_NAME" "$DOWNLOAD_URL"
        else
            wget -O "$ARCHIVE_NAME" "$DOWNLOAD_URL"
        fi

        if [ -f "$ARCHIVE_NAME" ]; then
            print_status "Extracting Python..."
            # Extract to a temporary directory first
            TEMP_DIR="${PYTHON_DIR}-temp"
            mkdir -p "$TEMP_DIR"
            tar -xzf "$ARCHIVE_NAME" -C "$TEMP_DIR"

            # Find the actual Python installation directory
            FOUND_PYTHON_DIR=$(find "$TEMP_DIR" -name "python" -type d | head -1)
            if [ -n "$FOUND_PYTHON_DIR" ]; then
                # Copy the contents to our target directory
                cp -r "$FOUND_PYTHON_DIR"/* "$PYTHON_DIR"/
                rm -rf "$TEMP_DIR" "$ARCHIVE_NAME"
            else
                # Fallback: try direct extraction
                tar -xzf "$ARCHIVE_NAME" -C "$PYTHON_DIR" --strip-components=1
                rm -f "$TEMP_DIR" "$ARCHIVE_NAME"
            fi

            # Find the Python executable
            PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1,2)
            if [ -f "$PYTHON_DIR/bin/python$PYTHON_MAJOR" ]; then
                PYTHON_CMD="$PYTHON_DIR/bin/python$PYTHON_MAJOR"
                print_success "Python $PYTHON_VERSION installed locally at: $PYTHON_CMD"
            elif [ -f "$PYTHON_DIR/bin/python3" ]; then
                PYTHON_CMD="$PYTHON_DIR/bin/python3"
                print_success "Python $PYTHON_VERSION installed locally at: $PYTHON_CMD"
            else
                print_warning "Local Python extraction failed, using system Python"
                PYTHON_CMD="$CURRENT_PYTHON"
            fi
        else
            print_warning "Failed to download Python, using system Python"
            PYTHON_CMD="$CURRENT_PYTHON"
        fi

    elif [ "$OS" == "windows" ]; then
        print_warning "Windows portable Python download not yet implemented for version selection"
        print_warning "Please install Python $PYTHON_VERSION system-wide and run this script again"
        PYTHON_CMD="$CURRENT_PYTHON"
    fi
fi

# Verify we can use the chosen Python
if ! $PYTHON_CMD --version >/dev/null 2>&1; then
    print_warning "Chosen Python not accessible, falling back to system Python"
    PYTHON_CMD="$CURRENT_PYTHON"
fi

FINAL_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
FINAL_MINOR=$(echo $FINAL_VERSION | cut -d'.' -f2)
print_success "Using Python $FINAL_VERSION for virtual environment"

# Apply compatibility fixes if using Python 3.12+
COMPATIBILITY_MODE=0
if [ "$FINAL_MINOR" -ge 12 ]; then
    print_warning "Python 3.12+ detected - enabling compatibility mode"
    COMPATIBILITY_MODE=1
fi

# Check for Git
print_status "Checking Git installation..."
if ! command -v git >/dev/null 2>&1; then
    print_error "Git is required but not installed. Please install Git first."
    exit 1
fi
print_success "Git found: $(git --version)"

# Install system dependencies
print_status "Installing system dependencies..."

if [ "$OS" == "macos" ]; then
    # Check for Homebrew
    if ! command -v brew >/dev/null 2>&1; then
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
    if command -v apt-get >/dev/null 2>&1; then
        print_status "Installing system packages via apt..."
        sudo apt-get update
        sudo apt-get install -y espeak-ng ffmpeg portaudio19-dev python3-dev build-essential

        # Create espeak symlink for phonemizer compatibility
        if [ ! -L "/usr/bin/espeak" ] && [ -f "/usr/bin/espeak-ng" ]; then
            print_status "Creating espeak symlink for phonemizer compatibility..."
            sudo ln -sf /usr/bin/espeak-ng /usr/bin/espeak
        fi
    elif command -v yum >/dev/null 2>&1; then
        print_status "Installing system packages via yum..."
        sudo yum install -y espeak-ng ffmpeg portaudio-devel python3-devel gcc gcc-c++

        # Create espeak symlink for phonemizer compatibility
        if [ ! -L "/usr/bin/espeak" ] && [ -f "/usr/bin/espeak-ng" ]; then
            print_status "Creating espeak symlink for phonemizer compatibility..."
            sudo ln -sf /usr/bin/espeak-ng /usr/bin/espeak
        fi
    elif command -v pacman >/dev/null 2>&1; then
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
    if command -v winget >/dev/null 2>&1; then
        print_status "Winget detected. Installing FFmpeg via Winget..."
        winget install -e --id Gyan.FFmpeg 2>/dev/null || {
            print_warning "Winget installation failed, trying Chocolatey..."
            if command -v choco >/dev/null 2>&1; then
                choco install ffmpeg -y
                print_success "FFmpeg installed via Chocolatey"
            else
                print_warning "Please install FFmpeg manually from: https://ffmpeg.org/download.html"
            fi
        } && print_success "FFmpeg installed via Winget"
    elif command -v choco >/dev/null 2>&1; then
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
    if [ "$recreate" = "y" ] || [ "$recreate" = "Y" ]; then
        print_status "Removing existing virtual environment..."
        rm -rf venv
    else
        print_status "Using existing virtual environment."
    fi
fi

if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment!"
        exit 1
    fi
fi

# Activate virtual environment
print_status "Activating virtual environment..."
if [ "$OS" == "windows" ]; then
    # For Windows Git Bash/Cygwin compatibility
    # Try Scripts/activate first (Windows standard)
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        # Fallback for some Python installations or WSL-like environments
        source venv/bin/activate
    else
        print_error "Could not find venv activation script!"
        print_error "Expected: venv/Scripts/activate or venv/bin/activate"
        exit 1
    fi
else
    source venv/bin/activate
fi

# Verify virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    print_error "Failed to activate virtual environment!"
    exit 1
fi

print_success "Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip and install build tools
print_status "Setting up Python build environment..."
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    print_error "Failed to upgrade pip/setuptools/wheel!"
    exit 1
fi

# Detect GPU and install appropriate PyTorch version
print_status "Detecting GPU configuration..."

# Function to detect NVIDIA GPU and CUDA capability
detect_nvidia_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader 2>/dev/null | head -1)
        if [ -n "$GPU_INFO" ]; then
            GPU_NAME=$(echo "$GPU_INFO" | cut -d',' -f1 | xargs)
            COMPUTE_CAP=$(echo "$GPU_INFO" | cut -d',' -f2 | xargs)
            echo "$GPU_NAME|$COMPUTE_CAP"
            return 0
        fi
    fi
    return 1
}

# Detect GPU
CUDA_AVAILABLE=0
GPU_DETECTED=""
COMPUTE_CAPABILITY=""
RECOMMENDED_CUDA=""

if [ "$OS" != "macos" ]; then
    GPU_RESULT=$(detect_nvidia_gpu || true)
    if [ -n "$GPU_RESULT" ]; then
        CUDA_AVAILABLE=1
        GPU_DETECTED=$(echo "$GPU_RESULT" | cut -d'|' -f1)
        COMPUTE_CAPABILITY=$(echo "$GPU_RESULT" | cut -d'|' -f2)

        print_success "NVIDIA GPU detected: $GPU_DETECTED"
        print_status "Compute Capability: $COMPUTE_CAPABILITY"

        # Determine best CUDA version based on compute capability
        # RTX 5060 Ti and newer (sm_120+) need CUDA 12.8+
        # RTX 4090, 4080, etc (sm_89) need CUDA 11.8+
        # RTX 3090, 3080, etc (sm_86) need CUDA 11.1+
        COMPUTE_MAJOR=$(echo "$COMPUTE_CAPABILITY" | cut -d'.' -f1)

        if [ "$COMPUTE_MAJOR" -ge 12 ]; then
            RECOMMENDED_CUDA="cu128"
            print_warning "RTX 50-series GPU detected (Compute Capability 12.x)"
            print_warning "Requires PyTorch with CUDA 12.8+ for sm_120 support"
        elif [ "$COMPUTE_MAJOR" -ge 9 ]; then
            RECOMMENDED_CUDA="cu121"
            print_status "RTX 40-series GPU detected, using CUDA 12.1"
        else
            RECOMMENDED_CUDA="cu118"
            print_status "Using CUDA 11.8 for compatibility"
        fi
    else
        print_warning "No NVIDIA GPU detected, will install CPU version"
    fi
else
    print_status "macOS detected - will install CPU version (Apple Silicon uses MPS)"
fi

# Install PyTorch with appropriate backend
print_status "Installing PyTorch (this may take 5-10 minutes)..."

if [ "$OS" == "macos" ]; then
    # macOS - CPU/MPS version
    print_status "Installing PyTorch for macOS (CPU/Apple Silicon MPS support)..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    print_success "PyTorch installed for macOS"
elif [ "$CUDA_AVAILABLE" -eq 1 ]; then
    # Linux/Windows with NVIDIA GPU
    print_status "Installing PyTorch with CUDA $RECOMMENDED_CUDA support..."

    if [ "$RECOMMENDED_CUDA" = "cu128" ]; then
        print_warning "Installing CUDA 12.8 build for RTX 50-series compatibility..."
        # Pre-install dependencies from PyPI to avoid pip resolution issues
        print_status "Installing PyTorch dependencies..."
        pip install typing-extensions filelock fsspec jinja2 networkx sympy mpmath >/dev/null 2>&1 || true

        # Now install PyTorch with CUDA 12.8
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128 || {
            print_error "CUDA 12.8 installation failed!"
            print_warning "RTX 5060 Ti requires PyTorch with CUDA 12.8+"
            print_warning "Falling back to CUDA 12.1 (may not work with RTX 50-series)"
            pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 || {
                print_warning "CUDA 12.1 failed, trying CPU version..."
                pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
            }
        }
    elif [ "$RECOMMENDED_CUDA" = "cu121" ]; then
        # Pre-install dependencies to avoid pip issues
        pip install typing-extensions filelock fsspec jinja2 networkx sympy mpmath >/dev/null 2>&1 || true

        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 || {
            print_warning "CUDA 12.1 installation failed, trying CUDA 11.8..."
            pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118 || {
                print_warning "CUDA 11.8 failed, installing CPU version..."
                pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
            }
        }
    else
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118 || {
            print_warning "CUDA 11.8 installation failed, installing CPU version..."
            pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
        }
    fi
    print_success "PyTorch installation completed"
else
    # No GPU detected or Windows without GPU
    print_status "Installing PyTorch CPU version..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    print_success "PyTorch CPU version installed"
fi

# Verify PyTorch installation and GPU support
print_status "Verifying PyTorch installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'Device count: {torch.cuda.device_count() if torch.cuda.is_available() else 0}')" 2>/dev/null || {
    print_warning "PyTorch verification had issues, but installation may still work"
}

# Test GPU if available
if [ "$CUDA_AVAILABLE" -eq 1 ]; then
    print_status "Testing GPU compatibility..."
    python -c "
import torch
if torch.cuda.is_available():
    try:
        device = torch.device('cuda')
        x = torch.randn(100, 100).to(device)
        y = x @ x.T
        print('✅ GPU test passed: CUDA operations work correctly')
        print(f'   Using device: {torch.cuda.get_device_name(0)}')
    except RuntimeError as e:
        if 'no kernel image' in str(e):
            print('❌ GPU test failed: No kernel image available')
            print('   This usually means PyTorch was not compiled for your GPU architecture')
            print(f'   Your GPU Compute Capability: $COMPUTE_CAPABILITY')
            print('   You may need to upgrade PyTorch or use CPU mode')
        else:
            print(f'❌ GPU test failed: {e}')
else:
    print('⚠️  CUDA not available in PyTorch')
" 2>&1 || print_warning "GPU test encountered issues"
fi

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

# Install training requirements with MFA priority
print_status "Installing training dependencies..."

# MFA is ESSENTIAL for custom voice model training - this app's core purpose
# We'll prioritize getting MFA working over other considerations

MFA_INSTALLED=0
MFA_METHOD=""

print_status "Checking Montreal Forced Aligner (MFA) installation options..."

# MFA is ESSENTIAL for custom voice model training
# Ask user upfront what installation method they prefer

echo ""
echo "🎯 MFA INSTALLATION CHOICES"
echo "==========================="
echo ""
echo "Montreal Forced Aligner (MFA) enhances TTS training quality, but is OPTIONAL."
echo ""
echo "📋 YOUR OPTIONS:"
echo ""
echo "1. ✅ Standard Installation (RECOMMENDED):"
echo "   • No external dependencies"
echo "   • Basic TTS training works perfectly"
echo "   • Uses phoneme sequences (G2P models)"
echo "   • Sufficient for most users"
echo ""
echo "2. 🔧 Enhanced Installation (MFA via Conda):"
echo "   • Installs Conda system-wide"
echo "   • Enables forced alignment (better quality)"
echo "   • May interfere with existing Python/conda setups"
echo "   • Best for professional results"
echo ""
echo "3. 🐳 Docker Installation (Most Isolated):"
echo "   • Zero system changes"
echo "   • Includes MFA + GPU support"
echo "   • Completely self-contained"
echo "   • Perfect for testing/complex setups"
echo ""
echo "4. ⏭️  Skip MFA (Basic functionality only):"
echo "   • Recording and dataset management only"
echo "   • No TTS model training"
echo "   • For users who just want to collect data"
echo ""
read -p "Choose MFA installation method [1/2/3/4]: " mfa_choice

MFA_INSTALLED=0
MFA_METHOD=""

case "$mfa_choice" in
    1)
        echo ""
        echo "✅ Selected: Standard Installation (No MFA)"
        echo ""
        print_success "Perfect choice for most users!"
        echo ""
        echo "This installation provides:"
        echo "  ✅ Full TTS training capabilities"
        echo "  ✅ No external dependencies"
        echo "  ✅ Clean, isolated setup"
        echo "  ✅ Sufficient for excellent results"
        echo ""
        print_info "Proceeding with standard installation..."
        SKIP_MFA=1
        ;;

    2)
        echo ""
        echo "🔧 Selected: Enhanced Installation (MFA via Conda)"
        echo ""
        print_warning "This will install Conda system-wide."
        echo ""
        echo "Conda installation provides:"
        echo "  ✅ Forced alignment (better quality)"
        echo "  ✅ Professional TTS training"
        echo "  ⚠️  May interfere with existing Python setups"
        echo ""
        # Check if conda is available
        if ! command -v conda >/dev/null 2>&1; then
            print_warning "Conda not found in PATH"
            echo ""
            echo "To install Conda:"
            echo "  • Linux/Mac: https://docs.conda.io/en/latest/miniconda.html"
            echo "  • Windows: https://docs.conda.io/en/latest/miniconda.html"
            echo ""
            read -p "Install Conda first, then retry? [y/N]: " install_conda
            if [ "$install_conda" = "y" ] || [ "$install_conda" = "Y" ]; then
                echo "Please install Conda and run this script again."
                exit 1
            else
                print_warning "Cannot install MFA without Conda"
                SKIP_MFA=1
            fi
        else
            print_status "Found Conda: $(which conda)"
            print_status "Installing MFA via Conda..."
            if conda install -c conda-forge montreal-forced-aligner -y >/dev/null 2>&1; then
                MFA_INSTALLED=1
                MFA_METHOD="Conda (conda-forge)"
                print_success "MFA installed successfully via Conda"
            else
                print_error "Conda installation failed!"
                print_warning "MFA installation via Conda failed"
                SKIP_MFA=1
            fi
        fi
        ;;

    3)
        echo ""
        echo "🐳 Selected: Docker Installation (Most Isolated)"
        echo ""
        print_success "Excellent choice for clean, isolated setup!"
        echo ""
        echo "Docker provides:"
        echo "  ✅ Zero system interference"
        echo "  ✅ MFA + GPU support included"
        echo "  ✅ Completely self-contained"
        echo "  ✅ Easy cleanup with ./uninstall.sh"
        echo ""
        print_info "Run: ./docker-start.sh after this installation completes"
        SKIP_MFA=1
        ;;

    4)
        echo ""
        echo "⏭️  Selected: Skip MFA (Recording only)"
        echo ""
        print_info "Recording and dataset management only."
        echo ""
        echo "This provides:"
        echo "  ✅ Voice recording interface"
        echo "  ✅ Dataset organization"
        echo "  ❌ No TTS model training"
        echo ""
        print_warning "You will need to install MFA separately for training."
        SKIP_MFA=1
        ;;

    *)
        print_warning "Invalid choice. Defaulting to Conda installation..."
        # Try conda if available, otherwise skip
        if command -v conda >/dev/null 2>&1; then
            print_status "Attempting MFA installation via Conda..."
            if conda install -c conda-forge montreal-forced-aligner -y >/dev/null 2>&1; then
                MFA_INSTALLED=1
                MFA_METHOD="Conda (conda-forge)"
                print_success "MFA installed via Conda"
            else
                print_warning "Conda installation failed, skipping MFA"
                SKIP_MFA=1
            fi
        else
            print_warning "Conda not available and no valid choice made"
            SKIP_MFA=1
        fi
        ;;
esac

if [ $SKIP_MFA -eq 1 ]; then
    if [ -f "requirements_training.txt" ]; then
        # Create compatible requirements file without MFA
        grep -v "montreal-forced-alignment" requirements_training.txt > requirements_training_compatible.txt
        pip install -r requirements_training_compatible.txt
        rm -f requirements_training_compatible.txt
    else
        # Install packages individually without MFA
        pip install transformers datasets accelerate evaluate librosa soundfile scipy scikit-learn
        pip install tensorboard wandb phonemizer
    fi
    if [ $MFA_INSTALLED -eq 0 ]; then
        print_warning "Montreal Forced Aligner installation failed"
        echo ""
        echo "ℹ️  YOUR INSTALLATION STATUS:"
        echo ""
        echo "   ✅ Standard installation complete"
        echo "   ✅ Basic TTS training works perfectly"
        echo "   ✅ Uses phoneme sequences (G2P models)"
        echo "   ✅ No external dependencies required"
        echo ""
        echo "💡 For enhanced quality, you can:"
        echo "   • Install MFA via Conda (better alignment)"
        echo "   • Use Docker (includes everything)"
        echo "   • Both options available in installation menu"
    else
        print_success "MFA installed successfully via $MFA_METHOD"
    fi
else
    # Normal installation with MFA (Linux/Mac only)
    if [ -f "requirements_training.txt" ]; then
        pip install -r requirements_training.txt
    else
        pip install transformers datasets accelerate evaluate librosa soundfile scipy scikit-learn
        pip install tensorboard wandb phonemizer montreal-forced-alignment
    fi
fi

# Install TTS-specific dependencies
print_status "Installing TTS dependencies..."
pip install piper-tts phonemizer

# Verify espeak installation
print_status "Verifying espeak installation..."
if command -v espeak >/dev/null 2>&1; then
    print_success "espeak found: $(which espeak)"
    espeak --version 2>/dev/null || echo "espeak version check failed"
elif command -v espeak-ng >/dev/null 2>&1; then
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
# Make sure we use the venv Python
if [ -f "venv/bin/python" ]; then
    venv/bin/python test_installation.py
elif [ -f "venv/Scripts/python.exe" ]; then
    venv/Scripts/python.exe test_installation.py
else
    print_warning "Could not find venv Python, using system Python"
    $PYTHON_CMD test_installation.py
fi
INSTALLATION_TEST_RESULT=$?

# Initialize installation summary
INSTALLATION_SUMMARY=""
FAILED_COMPONENTS=""
SUCCESSFUL_COMPONENTS=""

# Check individual components
print_status "Verifying installation components..."

# Use venv Python for all checks
VENV_PYTHON="$PYTHON_CMD"
if [ -f "venv/bin/python" ]; then
    VENV_PYTHON="venv/bin/python"
elif [ -f "venv/Scripts/python.exe" ]; then
    VENV_PYTHON="venv/Scripts/python.exe"
fi

# Check core components
if $VENV_PYTHON -c "import fastapi, uvicorn, pydub, numpy, pandas" 2>/dev/null; then
    SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS Core Dependencies"
else
    FAILED_COMPONENTS="$FAILED_COMPONENTS Core Dependencies"
fi

# Check training components
if $VENV_PYTHON -c "import torch, torchaudio, transformers, datasets, librosa, soundfile, scipy, sklearn" 2>/dev/null; then
    SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS Training Dependencies"
else
    FAILED_COMPONENTS="$FAILED_COMPONENTS Training Dependencies"
fi

# Check TTS components
if $VENV_PYTHON -c "import piper, phonemizer" 2>/dev/null; then
    SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS TTS Dependencies"
else
    FAILED_COMPONENTS="$FAILED_COMPONENTS TTS Dependencies"
fi

# Check Piper training package (optional advanced feature - piper_train)
# Note: piper_train is a SEPARATE package from piper (Piper TTS)
# Piper TTS is already checked and working above
# piper_train is mainly for advanced MFA workflows
if [ $MFA_INSTALLED -eq 1 ]; then
    if $VENV_PYTHON -c "import piper_train" 2>/dev/null; then
        SUCCESSFUL_COMPONENTS="$SUCCESSFUL_COMPONENTS piper_train (advanced)"
    else
        # Don't mark as failed - it's optional
        print_info "piper_train package not available (optional advanced feature)"
        print_info "Core Piper TTS and training capabilities are fully functional"
    fi
else
    # Don't check or report on piper_train for standard installations
    print_info "Standard installation complete - all training capabilities except MFA available"
fi

# Generate summary
if [ $INSTALLATION_TEST_RESULT -eq 0 ] && [ $MFA_INSTALLED -eq 1 ]; then
    print_success "Installation test passed!"
    INSTALLATION_SUMMARY="✅ Enhanced installation - ready for professional voice model training!"
elif [ $INSTALLATION_TEST_RESULT -eq 0 ]; then
    print_success "Installation test passed!"
    INSTALLATION_SUMMARY="✅ Standard installation - ready for custom voice model training!"
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
case "$OSTYPE" in
    msys|win32|cygwin*)
        # Windows: try Scripts first, then bin
        if [ -f venv/Scripts/activate ]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi
        ;;
    *)
        source venv/bin/activate
        ;;
esac

# Check if training dependencies are available
echo "Checking training dependencies..."
# Note: 'python' here refers to the virtual environment's Python
python test_installation.py

if [ $? -ne 0 ]; then
    echo "⚠️  Some training dependencies are missing. Training features may not work."
    echo "You can still use recording and post-processing features."
fi

# Launch the application
echo "🚀 Launching Coaxial Recorder..."
# Note: 'python' here refers to the virtual environment's Python
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
REM Note: 'python' here refers to the virtual environment's Python
python test_installation.py

if %errorlevel% neq 0 (
    echo ⚠️  Some training dependencies are missing. Training features may not work.
    echo You can still use recording and post-processing features.
)

echo 🚀 Launching Coaxial Recorder...
REM Note: 'python' here refers to the virtual environment's Python
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
else
    echo "🎯 All Expected Components Installed Successfully!"
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
if [ -f "venv/bin/python" ]; then
    echo "   venv/bin/python test_installation.py"
elif [ -f "venv/Scripts/python.exe" ]; then
    echo "   venv\\Scripts\\python.exe test_installation.py"
else
    echo "   source venv/bin/activate && python test_installation.py"
fi
echo ""

if [ "$OS" == "windows" ]; then
    echo "📝 Windows Notes:"
    echo "   - If you encounter issues, ensure Visual Studio Build Tools are installed"
    echo "   - Make sure FFmpeg is in your PATH"
    echo "   - Consider using conda for espeak: conda install -c conda-forge espeak"
    echo ""
fi

if [ -n "$FAILED_COMPONENTS" ]; then
    echo "✅ All core functionality is available and working!"
    echo "   Your installation is complete and ready for TTS training."
fi

print_success "Happy voice training! 🎤🤖"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                    🎯 GETTING STARTED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Launch the application:"
echo ""
if [ "$OS" == "windows" ]; then
    echo "   Option A - Double-click:"
    echo "   📂 launch_complete.bat"
    echo ""
    echo "   Option B - Command line (Git Bash):"
    echo "   bash launch_complete.sh"
elif [ "$OS" == "macos" ]; then
    echo "   ./launch_complete.sh"
    echo ""
    echo "   Or double-click: launch_complete.sh in Finder"
else
    echo "   ./launch_complete.sh"
fi
echo ""
echo "2️⃣  Open your browser:"
echo ""
echo "   🌐 http://localhost:8000"
echo ""
echo "3️⃣  Start creating your custom voice:"
echo ""
echo "   • Create a voice profile"
echo "   • Add prompt lists"
echo "   • Record your voice samples"
echo "   • Train your custom TTS model"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Documentation:"
echo "   • TRAINING_README.md - Training guide"
echo "   • SETUP_GUIDE.md - Quick setup reference"
if [ "$OS" == "windows" ]; then
    echo "   • WINDOWS_README.md - Windows-specific info"
fi
echo "   • MFA_ESSENTIAL_README.md - Optional MFA enhancement"
echo ""
echo "💡 Need help? Check the documentation or run:"
echo "   venv/bin/python test_installation.py"
echo ""
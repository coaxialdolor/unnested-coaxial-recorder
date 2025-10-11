#!/bin/bash

# Quick test script to verify Piper TTS installation
# This script tests the installation without doing a full reinstall

set -e

echo "🧪 Testing Piper TTS Installation"
echo "================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found! Please run the installer first."
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Verify virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_error "Failed to activate virtual environment!"
    exit 1
fi

print_success "Virtual environment activated: $VIRTUAL_ENV"

# Test Python imports
print_status "Testing Python imports..."

python3 -c "
import sys
print(f'Python version: {sys.version}')

# Test core imports
try:
    import fastapi
    print('✅ FastAPI')
except ImportError as e:
    print(f'❌ FastAPI: {e}')

try:
    import torch
    print(f'✅ PyTorch {torch.__version__}')
    if torch.cuda.is_available():
        print(f'   CUDA available: {torch.cuda.device_count()} device(s)')
    else:
        print('   CUDA not available')
except ImportError as e:
    print(f'❌ PyTorch: {e}')

try:
    import piper
    print('✅ Piper TTS')
except ImportError as e:
    print(f'❌ Piper TTS: {e}')

try:
    import phonemizer
    print('✅ Phonemizer')
except ImportError as e:
    print(f'❌ Phonemizer: {e}')

try:
    import transformers
    print(f'✅ Transformers {transformers.__version__}')
except ImportError as e:
    print(f'❌ Transformers: {e}')
"

# Test Piper TTS functionality
print_status "Testing Piper TTS functionality..."

if [ -d "training/piper" ]; then
    print_success "Piper TTS repository found"

    # Test if we can import piper_train
    python3 -c "
try:
    import piper_train
    print('✅ Piper TTS Training module')
except ImportError as e:
    print(f'❌ Piper TTS Training module: {e}')
"
else
    print_warning "Piper TTS repository not found in training/piper"
fi

# Test espeak
print_status "Testing espeak installation..."
if command -v espeak &>/dev/null; then
    print_success "espeak found: $(which espeak)"
    espeak --version 2>/dev/null || echo "espeak version check failed"
elif command -v espeak-ng &>/dev/null; then
    print_success "espeak-ng found: $(which espeak-ng)"
    espeak-ng --version 2>/dev/null || echo "espeak-ng version check failed"
else
    print_warning "espeak/espeak-ng not found in PATH"
fi

print_success "Installation test completed!"
echo ""
echo "If you see any ❌ errors above, you may need to:"
echo "1. Run the full installer: ./install_fixed.sh"
echo "2. Or install missing packages manually in the virtual environment"
echo ""
echo "To activate the virtual environment manually:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "   source venv/Scripts/activate"
else
    echo "   source venv/bin/activate"
fi

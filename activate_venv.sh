#!/bin/bash

# Virtual Environment Activation Script for Piper Recording Studio Coaxial Recorder
# This script simply activates the virtual environment

cd "$(dirname "$0")"

# Detect OS and set activation path
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    VENV_ACTIVATE="venv/Scripts/activate"
else
    VENV_ACTIVATE="venv/bin/activate"
fi

# Check if virtual environment exists
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "❌ Virtual environment not found or incomplete!"
    echo "Please run ./setup_venv.sh first to create the virtual environment."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_ACTIVATE"

# Show current Python path
echo "✅ Virtual environment activated!"
echo "Python: $(which python)"
echo ""
echo "You can now run Python commands with the venv packages."
echo "To deactivate, type: deactivate"
echo ""
echo "To launch the application, run: ./launch.sh"
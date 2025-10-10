#!/bin/bash

# Virtual Environment Activation Script for Piper Recording Studio Coaxial Recorder
# This script simply activates the virtual environment

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup_venv.sh first to create the virtual environment."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Show current Python path
echo "✅ Virtual environment activated!"
echo "Python: $(which python)"
echo ""
echo "You can now run Python commands with the venv packages."
echo "To deactivate, type: deactivate"
echo ""
echo "To launch the application, run: ./launch.sh"
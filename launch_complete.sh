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

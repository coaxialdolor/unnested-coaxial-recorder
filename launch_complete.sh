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

#!/bin/bash

# Launch script for Piper Recording Studio Coaxial Recorder
# This script activates the virtual environment and runs the application

echo "🚀 Launching Piper Recording Studio Coaxial Recorder"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup_venv.sh first to create the virtual environment."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment!"
    exit 1
fi

# Install/update requirements with better error handling
echo "Installing/updating requirements..."
pip install --upgrade pip setuptools wheel

# Install requirements with fallback options
if [ -f "requirements.txt" ]; then
    pip install --only-binary=all -r requirements.txt 2>/dev/null || {
        echo "⚠️  Some packages failed with pre-built wheels, trying source installation..."
        pip install -r requirements.txt
    }
else
    echo "⚠️  requirements.txt not found, installing core packages..."
    pip install fastapi uvicorn python-multipart jinja2 aiofiles pydantic pydub pandas
fi

if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements!"
    exit 1
fi

# Check for existing processes on port 8000
echo "Checking for existing processes on port 8000..."
EXISTING_PID=$(lsof -ti :8000 2>/dev/null)
if [ ! -z "$EXISTING_PID" ]; then
    echo "⚠️  Found existing process on port 8000 (PID: $EXISTING_PID)"
    read -p "Do you want to kill it? (y/N): " kill_process
    if [[ $kill_process =~ ^[Yy]$ ]]; then
        echo "Killing process $EXISTING_PID..."
        kill -9 $EXISTING_PID 2>/dev/null
        sleep 2
    fi
fi

# Start the Flask application
echo "Starting Flask application..."
echo "The application will be available at: http://localhost:8000/record"
echo ""
echo "Press Ctrl+C to stop the application"
echo "=================================="

# Run the Flask app
python app.py
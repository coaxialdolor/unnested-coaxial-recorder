 #!/bin/bash

# Start script for Piper Recording Studio Coaxial Recorder
# This script activates the virtual environment and starts the Flask app

echo "Starting Piper Recording Studio Coaxial Recorder..."

# Navigate to the coaxial_recorder directory
cd "$(dirname "$0")"

# Check if virtual environment exists in parent directory
if [ ! -d "../.venv" ]; then
    echo "Error: Virtual environment '../.venv' not found!"
    echo "Please run: python -m venv ../.venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source ../.venv/bin/activate

# Check if requirements are installed
echo "Checking requirements..."
if ! pip list | grep -q "Flask"; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Start the Flask app
echo "Starting Flask application..."
echo "Server will be available at: http://localhost:8000/record"
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Run the app
python app.py
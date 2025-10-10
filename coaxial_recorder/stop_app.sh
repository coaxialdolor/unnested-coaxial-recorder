#!/bin/bash

# Stop script for Piper Recording Studio Coaxial Recorder
# This script stops the Flask app

echo "Stopping Piper Recording Studio Coaxial Recorder..."

# Find and stop the Flask app process
FLASK_PID=$(pgrep -f "python.*app.py")

if [ -n "$FLASK_PID" ]; then
    echo "Found Flask app process with PID: $FLASK_PID"
    echo "Stopping process..."
    kill "$FLASK_PID"
    sleep 2s
    
    # Force kill if still running
    if pgrep -f "python.*app.py" > /dev/null; then
        echo "Force stopping process..."
        kill -9 "$FLASK_PID"
        sleep 2s
    fi
    
    echo "Flask app stopped successfully!"
else
    echo "No Flask app process found."
fi

echo "Done!"
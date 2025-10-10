#!/bin/bash

# Kill script for Piper Recording Studio Coaxial Recorder
# This script stops the Flask application and frees up ports

echo "🔪 Stopping Piper Recording Studio Coaxial Recorder and freeing ports..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Find and kill Flask/Python processes
echo "Looking for Flask/Python processes..."
FLASK_PIDS=$(pgrep -f "python.*app.py" 2>/dev/null || true)
if [ ! -z "$FLASK_PIDS" ]; then
    echo "Found Flask app processes: $FLASK_PIDS"
    echo "Killing Flask processes..."
    kill -9 $FLASK_PIDS 2>/dev/null
    /bin/sleep 2
else
    echo "No Flask app processes found."
fi

# Free up ports
echo "Freeing up ports..."
for port in 8000 8001 5000; do
    echo "Checking port $port..."
    PORT_PIDS=$(lsof -ti :$port 2>/dev/null || true)
    if [ ! -z "$PORT_PIDS" ]; then
        echo "Found processes on port $port: $PORT_PIDS"
        echo "Killing processes on port $port..."
        kill -9 $PORT_PIDS 2>/dev/null
        /bin/sleep 1
    else
        echo "✅ Port $port is now free."
    fi
done

# Additional cleanup
echo "Performing additional cleanup..."
ADDITIONAL_PIDS=$(pgrep -f "coaxial_recorder" 2>/dev/null || true)
if [ ! -z "$ADDITIONAL_PIDS" ]; then
    echo "Found additional coaxial_recorder processes: $ADDITIONAL_PIDS"
    echo "Killing additional processes..."
    kill -9 $ADDITIONAL_PIDS 2>/dev/null
fi

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "You can now:"
echo "  - Run ./launch.sh to start the application again"
echo "  - Run ./setup_venv.sh to recreate the environment"
echo "  - Check port status with: lsof -i :8000"
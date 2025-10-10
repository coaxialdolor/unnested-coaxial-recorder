#!/bin/bash

# Setup script for Piper Recording Studio Coaxial Recorder
# This script creates a virtual environment and installs requirements

echo "🚀 Setting up Piper Recording Studio Coaxial Recorder"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists."
    read -p "Do you want to recreate it? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Using existing virtual environment."
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment!"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment!"
    exit 1
fi

# Upgrade pip and install build tools
echo "Setting up build environment..."
pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    echo "❌ Failed to upgrade pip/setuptools/wheel!"
    exit 1
fi

# Install requirements with better error handling
echo "Installing requirements..."
if [ -f "requirements.txt" ]; then
    # Try to install with pre-built wheels first
    pip install --only-binary=all -r requirements.txt 2>/dev/null || {
        echo "⚠️  Some packages failed with pre-built wheels, trying source installation..."
        pip install -r requirements.txt
    }
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install requirements!"
        echo "Trying to install packages individually..."
        # Try individual package installation
        pip install fastapi uvicorn python-multipart jinja2 aiofiles pydantic pydub pandas
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install core packages!"
            exit 1
        fi
    fi
else
    echo "⚠️  requirements.txt not found, installing core packages..."
    pip install fastapi uvicorn python-multipart jinja2 aiofiles pydantic pydub pandas
fi

echo "✅ Setup completed successfully!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To launch the application, run:"
echo "  ./launch.sh"
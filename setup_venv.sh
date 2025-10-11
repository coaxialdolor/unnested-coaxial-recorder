#!/bin/bash

# Basic setup script for Coaxial Recorder
# This script creates a virtual environment and installs basic requirements
# For full training capabilities, use install.sh instead

echo "🚀 Setting up Coaxial Recorder (Basic Installation)"
echo "For full training capabilities, run: ./install.sh"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Determine Python command
if command -v python3 &>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

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
$PYTHON -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment!"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip and install build tools
echo "Setting up build environment..."
$PYTHON -m pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    echo "❌ Failed to upgrade pip/setuptools/wheel!"
    exit 1
fi

# Install requirements with fallback
echo "Installing requirements..."
if [ -f "requirements.txt" ]; then
    pip install --only-binary=all -r requirements.txt 2>/dev/null || {
        echo "⚠️  Some packages failed with pre-built wheels, trying source installation..."
        pip install -r requirements.txt
    }

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install requirements!"
        echo "Trying to install packages individually..."
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
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  source venv/Scripts/activate"
else
    echo "  source venv/bin/activate"
fi
echo ""
echo "To launch the application, run:"
echo "  ./launch.sh"
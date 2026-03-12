#!/bin/bash
# Setup script for MooAId development environment

set -e

echo "================================"
echo "MooAId Setup Script"
echo "================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -e ".[dev]"

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To start the API server:"
echo "  mooaid serve"
echo ""
echo "To use the CLI:"
echo "  mooaid --help"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""

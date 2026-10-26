#!/usr/bin/env bash
# ==============================================================================
# Awingi NLP Platform — Automated Developer Setup Script
# Works on both Computer 1 and Computer 2
# ==============================================================================
set -euo pipefail

echo "===================================================================="
echo "🚀 Initializing Awingi NLP Platform Development Environment"
echo "===================================================================="

# Check Python version (requires >= 3.10)
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed on this system."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Detected Python version: ${PY_VERSION}"

# Create virtual environment if not present
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment in ./venv ..."
    python3 -m venv venv
    echo "✓ Virtual environment created."
else
    echo "✓ Existing virtual environment detected at ./venv"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source venv/bin/activate
echo "✓ Virtual environment activated."

# Ensure pip is up to date
pip install --upgrade pip

# Install dependencies
echo "📦 Installing platform dependencies from requirements.txt ..."
pip install -r requirements.txt

# Copy .env.example to .env if not exists
if [ ! -f ".env" ]; then
    echo "📄 Creating local .env from .env.example ..."
    cp .env.example .env
fi

# Run initial test verification
echo "🧪 Running initial contract test suite ..."
pytest tests/test_contract.py -v

echo ""
echo "===================================================================="
echo "🎉 Setup complete! You are ready to start development."
echo "   To activate your environment in a new terminal:"
echo "       source venv/bin/activate"
echo "===================================================================="

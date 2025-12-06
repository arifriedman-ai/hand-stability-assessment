#!/bin/bash
# Setup script for hand-stability-assessment
# Installs all system and Python dependencies

set -e  # Exit on error

echo "=========================================="
echo "Hand Stability Assessment - Setup Script"
echo "=========================================="

# Check if running with sudo (for system packages)
if [ "$EUID" -ne 0 ]; then
   echo "Installing system dependencies requires sudo..."
   sudo bash "$0"
   exit $?
fi

echo ""
echo "[1/3] Updating package lists..."
apt-get update -qq

echo ""
echo "[2/3] Installing system dependencies..."
echo "Installing graphics and media libraries..."
apt-get install -y libgl1 libsm6 libxext6 libxrender-dev libglvnd0 libglx0 libglx-mesa0 libgl1-mesa-dri libx11-xcb1 libxcb-dri3-0 libxcb-glx0 libxcb-present0 libxcb-randr0 libxcb-sync1 libxcb-xfixes0 libxxf86vm1 mesa-libgallium mesa-vulkan-drivers libgbm1 libice6 libvulkan1 > /dev/null 2>&1

echo ""
echo "[3/3] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "To run the application:"
echo "  streamlit run app.py"
echo ""

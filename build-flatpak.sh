#!/bin/bash
# Flatpak build script for Budgie

set -e

echo "======================================"
echo "Building Budgie Flatpak"
echo "======================================"
echo ""

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo "ERROR: flatpak-builder not found!"
    echo "Install it with: sudo apt install flatpak-builder"
    exit 1
fi

# Check if KDE runtime is installed
if ! flatpak info org.palodequeso.Platform//6.8 &> /dev/null; then
    echo "KDE Platform 6.8 not found. Installing..."
    flatpak install -y flathub org.palodequeso.Platform//6.8 org.palodequeso.Sdk//6.8
fi

# Check if PyQt BaseApp is installed
if ! flatpak info com.riverbankcomputing.PyQt.BaseApp//6.8 &> /dev/null; then
    echo "PyQt BaseApp not found. Installing..."
    flatpak install -y flathub com.riverbankcomputing.PyQt.BaseApp//6.8
fi

echo ""
echo "Building Flatpak..."
echo ""

# Build and install locally (with network access for pip)
flatpak-builder --force-clean --user --install-deps-from=flathub \
    --allow-missing-runtimes --disable-rofiles-fuse \
    --repo=repo --install build-dir org.palodequeso.budgie.json

echo ""
echo "======================================"
echo "Build complete!"
echo "======================================"
echo ""
echo "Run with: flatpak run org.palodequeso.budgie"
echo ""
echo "To create a distributable bundle:"
echo "  flatpak build-bundle repo budgie.flatpak org.palodequeso.budgie"
echo ""

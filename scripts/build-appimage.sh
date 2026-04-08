#!/bin/bash
# Build Linux AppImage for Budgie Qt desktop app
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_DIR/build/appimage"
APPDIR="$BUILD_DIR/Budgie.AppDir"

echo "======================================"
echo "Building Budgie AppImage"
echo "======================================"

# Check for required tools
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Download appimagetool if not present
APPIMAGETOOL="$BUILD_DIR/appimagetool"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    mkdir -p "$BUILD_DIR"
    ARCH=$(uname -m)
    curl -fsSL "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
        -o "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# Clean previous build
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"

echo "Creating virtual environment and installing dependencies..."
python3 -m venv "$BUILD_DIR/venv"
source "$BUILD_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$PROJECT_DIR/requirements-qtapp.txt" -q
pip install pyinstaller -q

echo "Bundling application with PyInstaller..."
cd "$PROJECT_DIR"
pyinstaller --noconfirm --clean \
    --name budgie \
    --onedir \
    --windowed \
    --add-data "ui:ui" \
    --add-data "database:database" \
    --add-data "api:api" \
    --add-data "services:services" \
    --add-data "scheduler:scheduler" \
    --add-data "shedule:shedule" \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --distpath "$BUILD_DIR/pyinstaller-dist" \
    main.py

echo "Fixing executable stack flags on bundled libraries..."
# Kernel 6.19+ rejects shared libraries with executable stack (GNU_STACK with X flag).
# Clear the flag on all bundled .so files to prevent "cannot enable executable stack" errors.
if command -v patchelf &> /dev/null; then
    find "$BUILD_DIR/pyinstaller-dist/budgie/" -name '*.so*' -exec \
        sh -c 'patchelf --clear-execstack "$1" 2>/dev/null || true' _ {} \;
    echo "  Cleared execstack flags with patchelf"
else
    echo "  WARNING: patchelf not found. Install it (sudo pacman -S patchelf) to fix execstack issues."
    echo "  The AppImage may fail on kernel 6.19+ without this fix."
fi

echo "Assembling AppDir..."

# Copy PyInstaller output into AppDir
cp -r "$BUILD_DIR/pyinstaller-dist/budgie/"* "$APPDIR/usr/bin/"

# Desktop entry
cat > "$APPDIR/budgie.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=Budgie
Comment=Personal budgeting tool
Exec=budgie
Icon=budgie
Categories=Office;Finance;
Terminal=false
DESKTOP
cp "$APPDIR/budgie.desktop" "$APPDIR/usr/share/applications/"

# Icon
if [ -f "$PROJECT_DIR/org.palodequeso.budgie.svg" ]; then
    cp "$PROJECT_DIR/org.palodequeso.budgie.svg" "$APPDIR/budgie.svg"
    cp "$PROJECT_DIR/org.palodequeso.budgie.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/budgie.svg"
else
    # Generate a simple placeholder icon
    echo '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#1976d2" rx="32"/><text x="128" y="160" text-anchor="middle" font-size="140" fill="white" font-family="sans-serif">B</text></svg>' > "$APPDIR/budgie.svg"
fi

# AppRun script
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/budgie" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

echo "Building AppImage..."
ARCH=$(uname -m)
APPIMAGE_OUTPUT="$PROJECT_DIR/Budgie-${ARCH}.AppImage"

# appimagetool needs ARCH env var
export ARCH
"$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_OUTPUT"

deactivate 2>/dev/null || true

echo ""
echo "======================================"
echo "Build complete!"
echo "======================================"
echo "AppImage: $APPIMAGE_OUTPUT"
echo ""
echo "Run with: chmod +x Budgie-${ARCH}.AppImage && ./Budgie-${ARCH}.AppImage"
echo "======================================"

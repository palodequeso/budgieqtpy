#!/bin/bash
# Build Android APK for Budgie (React Native / Expo)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MOBILE_DIR="$PROJECT_DIR/mobile"

echo "======================================"
echo "Building Budgie Android APK"
echo "======================================"

# Check for required tools
if ! command -v node &> /dev/null; then
    echo "ERROR: node not found. Install Node.js first."
    exit 1
fi

if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    # Check common locations
    if [ -d "$HOME/Android/Sdk" ]; then
        export ANDROID_HOME="$HOME/Android/Sdk"
    elif [ -d "$HOME/Library/Android/sdk" ]; then
        export ANDROID_HOME="$HOME/Library/Android/sdk"
    else
        echo "WARNING: ANDROID_HOME not set. Gradle may fail if SDK is not found."
    fi
fi

cd "$MOBILE_DIR"

echo "Installing dependencies..."
npm install

# Generate native android project if it doesn't exist
if [ ! -d "$MOBILE_DIR/android" ]; then
    echo "Generating Android project with Expo prebuild..."
    npx expo prebuild --platform android --clean
fi

echo "Building APK..."
cd "$MOBILE_DIR/android"

# Try release build first, fall back to debug
if ./gradlew assembleRelease 2>/dev/null; then
    APK_PATH="app/build/outputs/apk/release/app-release.apk"
    BUILD_TYPE="release"
else
    echo "Release build failed, building debug APK..."
    ./gradlew assembleDebug
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    BUILD_TYPE="debug"
fi

if [ -f "$APK_PATH" ]; then
    cp "$APK_PATH" "$PROJECT_DIR/budgie.apk"
    echo ""
    echo "======================================"
    echo "Build complete! ($BUILD_TYPE)"
    echo "======================================"
    echo "APK: $PROJECT_DIR/budgie.apk"
    echo ""
    echo "Install on device: adb install budgie.apk"
    echo "======================================"
else
    echo "ERROR: Build failed — no APK found"
    exit 1
fi

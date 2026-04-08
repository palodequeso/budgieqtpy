#!/bin/bash
# Build and install Budgie on a connected Android device
set -e

cd "$(dirname "$0")/../mobile"

# Check for connected devices
DEVICES=$(adb devices | grep -v "List" | grep -v "^$" | awk '{print $1}')
DEVICE_COUNT=$(echo "$DEVICES" | grep -c . || true)

if [ "$DEVICE_COUNT" -eq 0 ]; then
    echo "No Android devices connected. Connect a device and enable USB debugging."
    exit 1
fi

TARGET_DEVICE=""
if [ "$DEVICE_COUNT" -gt 1 ]; then
    echo "Multiple devices found:"
    i=1
    while IFS= read -r device; do
        MODEL=$(adb -s "$device" shell getprop ro.product.model 2>/dev/null || echo "unknown")
        echo "  $i) $device ($MODEL)"
        i=$((i + 1))
    done <<< "$DEVICES"

    read -p "Select device [1-$DEVICE_COUNT]: " CHOICE
    TARGET_DEVICE=$(echo "$DEVICES" | sed -n "${CHOICE}p")
else
    TARGET_DEVICE=$(echo "$DEVICES" | head -1)
    MODEL=$(adb -s "$TARGET_DEVICE" shell getprop ro.product.model 2>/dev/null || echo "unknown")
    echo "Target device: $TARGET_DEVICE ($MODEL)"
fi

if [ -z "$TARGET_DEVICE" ]; then
    echo "Invalid device selection"
    exit 1
fi

echo "Installing dependencies..."
npm install

echo "Building APK..."
cd android
./gradlew assembleDebug

APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ ! -f "$APK_PATH" ]; then
    echo "Build failed - no APK found"
    exit 1
fi

echo "Installing on $TARGET_DEVICE..."
adb -s "$TARGET_DEVICE" install -r "$APK_PATH"

echo "Launching app..."
adb -s "$TARGET_DEVICE" shell am start -n org.palodequeso.budgie/.MainActivity 2>/dev/null || \
adb -s "$TARGET_DEVICE" shell monkey -p org.palodequeso.budgie -c android.intent.category.LAUNCHER 1 2>/dev/null || \
echo "(Could not auto-launch — open manually)"

echo "Done!"
